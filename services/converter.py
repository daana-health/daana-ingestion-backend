"""
CSV Conversion Service
Handles intelligent mapping of messy CSV files to the Daana-Rx schema using OpenAI
"""
import json
import logging
import pandas as pd
from io import StringIO, BytesIO
from typing import Dict, Optional
from openai import OpenAI
from config import settings
from schema import get_schema_description, get_table_column_names, TARGET_SCHEMA, HELPER_COLUMNS

logger = logging.getLogger(__name__)


class CSVConverter:
    """
    Handles CSV conversion using OpenAI for intelligent column mapping
    """

    def __init__(self):
        self.client = OpenAI(api_key=settings.openai_api_key)

    def _get_column_mapping(
        self,
        csv_headers: list,
        sample_rows: list[dict],
        target_table: Optional[str] = None,
    ) -> Dict[str, str]:
        """
        Use OpenAI to intelligently map CSV headers to target schema fields.

        Args:
            csv_headers: List of headers from the input CSV
            sample_rows: First few rows of data as list of dicts for context
            target_table: Optional specific table to target (e.g., 'units', 'drugs')

        Returns:
            Dictionary mapping CSV headers to target schema field names
        """
        schema_description = get_schema_description()

        # Build the system prompt with clear categorization
        system_prompt = f"""You are a healthcare data migration specialist for DaanaRx, a pharmacy/medication dispensary inventory management system used by clinics to track donated medications.

DOMAIN CONTEXT:
DaanaRx manages medication inventory for clinics. Key concepts:
- "Lots" are physical storage drawers in the clinic. Each lot has a 2-letter drawer code following the formula XY, where X = Drawer Letter (A, B, C...) and Y = Side (L=Left, R=Right). Examples: "AL" = Drawer A Left side, "CR" = Drawer C Right side. This drawer code is stored as the lot's "source" field.
- "Units" are individual medication items stored in lots. Each unit tracks a specific drug, quantity, expiry date, and which lot (drawer) it's stored in.
- "Drugs" are medication definitions (name, strength, form, NDC code).
- The medication intake form typically records: Lot number (drawer code), today's date, medication name, and medication dosage.
- Barcodes follow the formula: LotCode-Date-4LettersOfMed-Dosage (e.g., "BL-122225-AMLO-05" for Amlodipine 5mg in Drawer B Left on 12/22/2025).
- "Locations" are physical storage areas (e.g., a fridge or a room temperature shelf) that contain multiple lots/drawers.

Your task is to map input CSV column headers to our target database schema columns. You will receive the CSV headers and sample data rows to help you understand the data.

{schema_description}

CRITICAL RULES:
1. ONLY map to "Mappable columns" or "Helper columns" listed above. NEVER map to "Auto-managed columns" — those are system-generated (primary keys, timestamps, foreign keys set from auth context).
2. Return ONLY a valid JSON object mapping CSV headers to target column names: {{"csv_header": "target_column_name"}}
3. If a CSV header doesn't match any mappable or helper column, OMIT it from the mapping entirely.
4. Column names in the mapping must EXACTLY match the column names listed in the schema (case-sensitive).
5. Each CSV header should map to at most one target column.

FLEXIBLE MATCHING GUIDELINES:
Think broadly about what each CSV column represents. Consider the sample data values to disambiguate.
- Drug names: "Med Name", "Medicine", "Drug", "Drug Name", "Medication", "Rx" -> medication_name
- Generic names: "Generic", "Generic Name" -> generic_name
- Drug strength: "Strength", "Dose", "Dosage" (when numeric, e.g., 10, 500) -> strength
- Strength unit: "Unit", "Dose Unit", "Strength Unit" (e.g., mg, ml) -> strength_unit
- Drug form: "Form", "Dosage Form", "Type" (e.g., tablet, capsule) -> form
- NDC: "NDC", "NDC Code", "National Drug Code", "NDC ID" -> ndc_id
- Quantities: "Qty", "Quantity", "Amount", "Count", "Total" -> total_quantity; "Available", "Avail", "Qty Available" -> available_quantity
- Dates: "Exp Date", "Expires", "Expiration", "Exp", "Expiry" -> expiry_date; "Date", "Date of Entry", "Entry Date", "Date Created" -> date_created
- Patient info: "Patient ID", "MRN", "Patient Ref", "Patient #", "Patient Reference" -> patient_reference_id; "Patient Name", "Patient" -> patient_name
- Lot/Drawer codes: "Lot", "Lot Number", "Lot #", "Drawer", "Drawer Code" -> source (for lots table) or lot_source (helper for units table to resolve lot_id)
- Manufacturer lot: "Mfg Lot", "Manufacturer Lot", "Mfg Lot Number", "Manufacturer Lot Number" -> manufacturer_lot_number
- Location: "Location", "Storage Location" -> name (for locations table)
- Temperature: "Temp", "Temperature", "Storage Temp" -> temp
- Notes: "Notes", "Comments", "Remarks" -> optional_notes (units), note (lots), or notes (transactions)
- Source/Donor: "Source", "Donation Source", "Origin", "Donor" -> source
- Capacity: "Capacity", "Max Capacity", "Max" -> max_capacity
- Transaction type: "Type", "Transaction Type", "Action" -> type (for transactions)

IMPORTANT DISAMBIGUATION:
- If the target table is "units" and CSV has drug-related columns (medication name, strength, NDC, form), map them to the HELPER columns (medication_name, strength, strength_unit, form, ndc_id, generic_name) — these help resolve the drug_id foreign key.
- If the target table is "drugs", map the same columns directly to the drugs table columns.
- "Lot", "Lot Number", or "Lot #" — look at the sample data values:
  - If values are 2-letter drawer codes (like "AL", "CR", "BL") -> map to "source" (lots table) or "lot_source" (units helper).
  - If values look like manufacturer codes (like "LOT-2024-001", "MFG12345") -> map to "manufacturer_lot_number".
  - If values are UUIDs -> map to "lot_id".
- "Quantity" or "Qty" usually means total_quantity. "Available" means available_quantity.
- If a CSV column contains combined info (e.g., "Lisinopril 10mg Tablet"), it should still map to medication_name — the data processing pipeline handles parsing.
- For lots table uploads: "Lot", "Lot Number", "Drawer Code" -> source (this is the drawer code like AL, CR).

Return ONLY the JSON mapping object. No explanation, no markdown, no code blocks."""

        # Build sample data string
        sample_str = ""
        if sample_rows:
            sample_str = "\n\nSample data (first few rows):\n"
            for i, row in enumerate(sample_rows[:3]):
                sample_str += f"  Row {i}: {json.dumps(row, default=str)}\n"

        user_prompt = f"""Map these CSV headers to the target schema:

CSV Headers: {json.dumps(csv_headers)}
{sample_str}
{f"Target table: '{target_table}'. Focus mapping on this table's columns and its helper columns." if target_table else "No target table specified. Determine the best table from the data and map accordingly."}"""

        try:
            response = self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.1,
                max_tokens=1000
            )

            # Extract the mapping from the response
            mapping_text = response.choices[0].message.content.strip()

            # Remove code block markers if present
            if mapping_text.startswith("```"):
                lines = mapping_text.split("\n")
                mapping_text = "\n".join(lines[1:-1]) if len(lines) > 2 else mapping_text
                mapping_text = mapping_text.replace("```json", "").replace("```", "").strip()

            column_mapping = json.loads(mapping_text)

            # Validate the mapping against known column names
            column_mapping = self._validate_mapping(column_mapping, target_table)

            return column_mapping

        except json.JSONDecodeError as e:
            raise Exception(f"Failed to parse column mapping from OpenAI (invalid JSON): {str(e)}")
        except Exception as e:
            raise Exception(f"Failed to get column mapping from OpenAI: {str(e)}")

    def _validate_mapping(
        self,
        column_mapping: Dict[str, str],
        target_table: Optional[str],
    ) -> Dict[str, str]:
        """
        Validate that mapped columns actually exist in the target schema.
        Removes any hallucinated or invalid column mappings.
        """
        if not target_table:
            # If no target table, validate against all known columns
            from schema import get_all_column_names
            all_columns = set(get_all_column_names())
            validated = {}
            for csv_header, target_col in column_mapping.items():
                if target_col in all_columns:
                    validated[csv_header] = target_col
                else:
                    logger.warning(
                        f"Removing invalid mapping: '{csv_header}' -> '{target_col}' "
                        f"(column does not exist in any table)"
                    )
            return validated

        # Validate against specific table's columns + helper columns
        valid_columns = get_table_column_names(target_table)

        validated = {}
        for csv_header, target_col in column_mapping.items():
            if target_col in valid_columns:
                validated[csv_header] = target_col
            else:
                logger.warning(
                    f"Removing invalid mapping: '{csv_header}' -> '{target_col}' "
                    f"(column does not exist in table '{target_table}')"
                )
        return validated

    def _enforce_data_types(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Enforce proper data types based on common database field patterns

        Args:
            df: DataFrame to process

        Returns:
            DataFrame with corrected data types
        """
        # Date/timestamp columns
        date_columns = [col for col in df.columns if any(
            keyword in col.lower() for keyword in ['date', 'timestamp', 'created_at', 'updated_at']
        )]

        for col in date_columns:
            try:
                df[col] = pd.to_datetime(df[col], errors='coerce')
                # Use ISO date for DATE columns, full ISO for TIMESTAMPTZ
                if col == 'expiry_date':
                    df[col] = df[col].dt.strftime('%Y-%m-%d')
                else:
                    df[col] = df[col].dt.strftime('%Y-%m-%dT%H:%M:%S%z')
            except Exception:
                pass

        # Integer columns
        integer_columns = [col for col in df.columns if any(
            keyword in col.lower() for keyword in ['quantity', 'count', 'amount', 'capacity']
        )]

        for col in integer_columns:
            try:
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0).astype(int)
            except Exception:
                pass

        # Decimal columns (for strength, etc.)
        decimal_columns = [col for col in df.columns if 'strength' in col.lower()]

        for col in decimal_columns:
            try:
                df[col] = pd.to_numeric(df[col], errors='coerce').round(4)
            except Exception:
                pass

        # Clean string columns - strip whitespace
        string_columns = df.select_dtypes(include=['object']).columns
        for col in string_columns:
            if col not in date_columns:
                df[col] = df[col].astype(str).str.strip()
                # Replace 'nan' strings with empty strings
                df[col] = df[col].replace('nan', '')

        return df

    async def smart_convert_csv(
        self,
        file_content: bytes,
        target_table: Optional[str] = None
    ) -> tuple[str, Dict[str, str], list]:
        """
        Intelligently convert a messy CSV to match the target schema

        Args:
            file_content: Raw bytes of the CSV file
            target_table: Optional specific table to target

        Returns:
            Tuple of (cleaned_csv_string, column_mapping, unmapped_columns)
        """
        try:
            # Step A: Read the CSV and get headers
            df = pd.read_csv(BytesIO(file_content))
            original_headers = df.columns.tolist()

            if len(original_headers) == 0:
                raise ValueError("CSV file has no columns")

            # Step B: Extract sample rows for LLM context
            sample_rows = df.head(3).to_dict(orient='records')

            # Step C: Get intelligent mapping from OpenAI
            column_mapping = self._get_column_mapping(
                original_headers, sample_rows, target_table
            )

            # Track unmapped columns
            unmapped_columns = [
                col for col in original_headers
                if col not in column_mapping
            ]

            # Step D: Rename columns based on mapping
            df_renamed = df.rename(columns=column_mapping)

            # Keep only mapped columns
            mapped_columns = list(column_mapping.values())
            df_cleaned = df_renamed[mapped_columns]

            # Step E: Enforce data types
            df_cleaned = self._enforce_data_types(df_cleaned)

            # Step F: Convert to CSV string
            output = StringIO()
            df_cleaned.to_csv(output, index=False)
            cleaned_csv = output.getvalue()

            return cleaned_csv, column_mapping, unmapped_columns

        except pd.errors.EmptyDataError:
            raise ValueError("CSV file is empty")
        except Exception as e:
            raise Exception(f"Error during CSV conversion: {str(e)}")


# Initialize converter instance
converter = CSVConverter()
