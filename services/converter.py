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
        system_prompt = f"""You are a healthcare data migration specialist for DaanaRx, a pharmacy/medication dispensary inventory management system used by clinics to manage donated medication inventory.

DOMAIN CONTEXT — MASS Clinic Medication Flow:
DaanaRx manages medication inventory for free/charitable clinics that receive donated medications. Here is how the system works:

DATA MODEL RELATIONSHIPS:
  Clinics -> Locations -> Lots -> Units -> Drugs
  - A Clinic has Locations (physical storage areas like "Fridge" or "Room Temp Shelf")
  - A Location contains Lots (individual storage drawers)
  - A Lot contains Units (individual medication items)
  - Each Unit references a Drug (medication definition)

KEY CONCEPTS:
- "Lots" = physical storage DRAWERS in the clinic. Each lot/drawer has a 2-letter code following the formula XY:
    X = Drawer Letter (A, B, C, D...)
    Y = Side (L=Left, R=Right)
    Examples: "AL" = Drawer A Left, "CR" = Drawer C Right, "BL" = Drawer B Left
    This drawer code is stored in the lot's "source" field.
- "Locations" = physical storage areas that contain multiple drawers/lots. Each location has a name and temperature type ("fridge" or "room temp").
- "Drugs" = medication definitions with name, strength, strength_unit, form, and NDC code.
- "Units" = individual inventory items of a specific drug stored in a specific lot/drawer. Tracks quantity, expiry date, etc.
- Med intake form typically records: Lot number (drawer code), date of entry, medication name, and dosage.
- Barcodes follow formula: LotCode-Date-4LettersOfMed-Dosage (e.g., "BL-122225-AMLO-05" for Amlodipine 5mg in Drawer B Left on 12/22/2025).

Your task is to map input CSV column headers to our target database schema columns. You will receive the CSV headers and sample data rows to help you understand the data.

{schema_description}

CRITICAL RULES:
1. ONLY map to "Mappable columns" or "Helper columns" listed above. NEVER map to "Auto-managed columns" — those are system-generated (primary keys, timestamps, foreign keys set from auth context).
2. Return ONLY a valid JSON object mapping CSV headers to target column names: {{"csv_header": "target_column_name"}}
3. If a CSV header doesn't match any mappable or helper column, OMIT it from the mapping entirely.
4. Column names in the mapping must EXACTLY match the column names listed in the schema (case-sensitive).
5. Each CSV header should map to at most one target column.

TARGET TABLE INFERENCE (when no target_table is specified):
Look at the CSV headers AND sample data to determine which table the data belongs to:
- If data has drawer codes (2-letter like AL, CR) + medication names + dosages -> likely "units" table (medication items in drawers)
- If data has only drawer codes + location/temperature info but NO medication data -> likely "lots" table (setting up drawers)
- If data has medication name + strength + form + NDC but NO quantities/expiry -> likely "drugs" table (medication catalog)
- If data has location names + temperatures -> likely "locations" table
- If data has transaction types (check_in/check_out/adjust) + quantities -> likely "transactions" table

FLEXIBLE MATCHING GUIDELINES:
Think broadly about what each CSV column represents. ALWAYS examine the sample data values to disambiguate ambiguous headers.

Drug-related:
- "Med Name", "Medicine", "Drug", "Drug Name", "Medication", "Medication Name", "Rx" -> medication_name
- "Generic", "Generic Name" -> generic_name
- "Strength", "Dose", "Dosage" (when values are NUMERIC like 10, 500, 0.5) -> strength
- "Unit", "Dose Unit", "Strength Unit" (when values are like mg, ml, mcg) -> strength_unit
- "Form", "Dosage Form", "Type" (when values are like tablet, capsule, injection) -> form
- "NDC", "NDC Code", "National Drug Code", "NDC ID" -> ndc_id

Quantity-related:
- "Qty", "Quantity", "Amount", "Count", "Total", "Total Qty" -> total_quantity
- "Available", "Avail", "Qty Available", "Available Qty" -> available_quantity

Date-related:
- "Exp Date", "Expires", "Expiration", "Exp", "Expiry", "Expiry Date" -> expiry_date
- "Date", "Date of Entry", "Entry Date", "Date Created", "Date Added" -> date_created

Patient-related:
- "Patient ID", "MRN", "Patient Ref", "Patient #", "Patient Reference" -> patient_reference_id
- "Patient Name", "Patient" -> patient_name

Lot/Drawer-related (IMPORTANT — examine data values):
- "Lot", "Lot Number", "Lot #", "Drawer", "Drawer Code", "Lot Code" — LOOK AT THE DATA:
    - If values are 2-letter drawer codes (like "AL", "CR", "BL", "DR") -> map to "source" (lots table) or "lot_source" (units table helper)
    - If values look like manufacturer codes (like "LOT-2024-001", "MFG12345", long alphanumeric) -> map to "manufacturer_lot_number"
    - If values are UUIDs -> map to "lot_id"
- "Mfg Lot", "Manufacturer Lot", "Mfg Lot Number", "Manufacturer Lot Number" -> manufacturer_lot_number

Location-related (for lots table helpers):
- "Location", "Storage Location", "Location Name" -> location_name (lots helper, resolves location_id)
- "Temp", "Temperature", "Storage Temp", "Storage Temperature", "Storage" -> location_temp (lots helper, resolves location_id)
  Values should be normalized to "fridge" or "room temp".

Notes:
- "Notes", "Comments", "Remarks" -> optional_notes (units), note (lots), or notes (transactions) depending on table
- "Capacity", "Max Capacity", "Max" -> max_capacity
- "Source", "Donation Source", "Origin", "Donor" -> source (if NOT a drawer code)
- "Type", "Transaction Type", "Action" -> type (for transactions)

IMPORTANT DISAMBIGUATION:
- When target is "lots": "Lot"/"Lot Number"/"Drawer Code" with 2-letter values -> source. "Temp"/"Temperature"/"Storage Temp" -> location_temp (helper). "Location" -> location_name (helper).
- When target is "units": drug-related columns -> helper columns (medication_name, strength, etc.). "Lot"/"Drawer" with 2-letter values -> lot_source (helper). "Lot Number" with long codes -> manufacturer_lot_number.
- When target is "drugs": drug-related columns map directly to drugs table columns.
- A CSV column like "Dosage" might contain combined values like "10mg" or "5 mg". Map it to "strength" — the processing pipeline handles parsing.
- A CSV column like "Med Name" might contain combined info like "Lisinopril 10mg Tablet". Map it to "medication_name" — the pipeline handles parsing.

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
