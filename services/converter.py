"""
CSV Conversion Service
Two-phase intelligent parsing of messy CSV files to the Daana-Rx schema using OpenAI.

Phase 1: Quick column mapping + table inference (for metadata).
Phase 2: Deep row-level parsing — the LLM examines each cell's actual value
         and extracts structured fields, splitting combined values as needed.
"""
import json
import logging
import pandas as pd
from io import StringIO, BytesIO
from typing import Dict, Optional
from openai import OpenAI
from config import settings
from schema import (
    get_schema_description,
    get_table_column_names,
    get_all_column_names,
    TARGET_SCHEMA,
    HELPER_COLUMNS,
)

logger = logging.getLogger(__name__)

ROW_PARSE_BATCH_SIZE = 25


class CSVConverter:
    """
    Handles CSV conversion using OpenAI for intelligent column mapping
    and value-level data extraction.
    """

    def __init__(self):
        self.client = OpenAI(api_key=settings.openai_api_key)

    # ------------------------------------------------------------------
    # Phase 1 — Quick column mapping (for metadata / table inference)
    # ------------------------------------------------------------------

    def _get_column_mapping(
        self,
        csv_headers: list,
        sample_rows: list[dict],
        target_table: Optional[str] = None,
    ) -> Dict[str, str]:
        """
        Quick LLM call to map CSV headers to target schema fields.
        Used primarily for frontend metadata and table inference.
        """
        schema_description = get_schema_description()

        system_prompt = f"""You are a healthcare data migration specialist for DaanaRx, a pharmacy medication inventory system for free clinics.

DOMAIN: Clinics -> Locations (storage areas) -> Lots (drawers, 2-letter code XY: X=Letter, Y=L/R) -> Units (medication items) -> Drugs.
Drawer codes: AL=Drawer A Left, CR=Drawer C Right, etc. Stored in lots.source field.

{schema_description}

RULES:
1. ONLY map to Mappable or Helper columns. NEVER map to Auto-managed columns.
2. Return ONLY valid JSON: {{"csv_header": "target_column_name"}}
3. Omit unmatchable headers. Column names must be exact case-sensitive matches.
4. One CSV column may primarily map to one field even if it contains combined data (e.g., "Acetaminophen 325mg (5)" maps to "medication_name").

KEY DISAMBIGUATIONS:
- 2-letter values (AL, CR, BL) in "Lot"/"Drawer" columns → source (lots) or lot_source (units helper)
- Long lot codes (LOT-2024-001) → manufacturer_lot_number
- "Temp"/"Temperature"/"Storage Temp" → location_temp (lots helper) or temp (locations)
- Drug columns in units context → helper columns (medication_name, strength, etc.)

Return ONLY the JSON mapping. No explanation."""

        sample_str = ""
        if sample_rows:
            sample_str = "\n\nSample data:\n"
            for i, row in enumerate(sample_rows[:3]):
                sample_str += f"  Row {i}: {json.dumps(row, default=str)}\n"

        user_prompt = f"""CSV Headers: {json.dumps(csv_headers)}
{sample_str}
{f"Target table: '{target_table}'." if target_table else "Infer the best target table from the data."}"""

        try:
            response = self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=0.1,
                max_tokens=1000,
            )

            mapping_text = response.choices[0].message.content.strip()
            mapping_text = self._clean_json_response(mapping_text)
            column_mapping = json.loads(mapping_text)
            return self._validate_mapping(column_mapping, target_table)

        except json.JSONDecodeError as e:
            raise Exception(f"Failed to parse column mapping (invalid JSON): {e}")
        except Exception as e:
            raise Exception(f"Failed to get column mapping from OpenAI: {e}")

    def _validate_mapping(
        self, column_mapping: Dict[str, str], target_table: Optional[str]
    ) -> Dict[str, str]:
        """Strip any hallucinated column names from the mapping."""
        if target_table:
            valid = get_table_column_names(target_table)
        else:
            valid = set(get_all_column_names())

        validated = {}
        for csv_h, target_col in column_mapping.items():
            if target_col in valid:
                validated[csv_h] = target_col
            else:
                logger.warning(f"Removing invalid mapping: '{csv_h}' -> '{target_col}'")
        return validated

    def _infer_target_table(self, column_mapping: Dict[str, str]) -> Optional[str]:
        """Infer the target table from a column mapping using overlap scoring."""
        mapped_cols = set(column_mapping.values())
        best_table, best_score = None, 0
        for tbl, info in TARGET_SCHEMA.items():
            tbl_cols = {c["name"] for c in info["columns"]}
            for h in HELPER_COLUMNS.get(tbl, []):
                tbl_cols.add(h["name"])
            overlap = len(mapped_cols & tbl_cols)
            if overlap > best_score:
                best_score = overlap
                best_table = tbl
        return best_table

    # ------------------------------------------------------------------
    # Phase 2 — Deep row-level parsing
    # ------------------------------------------------------------------

    def _build_target_fields_text(self, target_table: str) -> str:
        """Build a concise target fields list for the parsing prompt."""
        lines = []
        for col in TARGET_SCHEMA[target_table]["columns"]:
            if not col.get("auto"):
                opt = " [optional]" if col.get("nullable") else ""
                lines.append(f"- {col['name']} ({col['type']}): {col['description']}{opt}")
        for col in HELPER_COLUMNS.get(target_table, []):
            lines.append(
                f"- {col['name']} (HELPER -> {col['resolves']}): {col['description']}"
            )
        return "\n".join(lines)

    def _parse_rows_batch(
        self,
        headers: list[str],
        rows: list[dict],
        target_table: str,
    ) -> list[dict]:
        """
        Send a batch of raw CSV rows to the LLM for intelligent value-level
        parsing.  One CSV cell can produce multiple target fields.
        """
        target_fields = self._build_target_fields_text(target_table)

        # Format raw rows compactly
        rows_text = ""
        for i, row in enumerate(rows):
            cells = []
            for h in headers:
                v = row.get(h)
                if pd.notna(v) and str(v).strip() and str(v).strip() != "nan":
                    cells.append(f"{h}={v}")
            rows_text += f"Row {i}: {' | '.join(cells)}\n"

        system_prompt = f"""You are a healthcare data parser for DaanaRx, a pharmacy medication inventory system.

TASK: Parse each row of raw CSV data into structured records for the "{target_table}" table.
Each CSV cell may contain data for MULTIPLE target fields. Extract and separate all values.

DOMAIN CONTEXT:
- DaanaRx manages donated medication inventory for free clinics.
- "Lots" are storage drawers. 2-letter codes: XY (X=Drawer Letter A-Z, Y=L=Left/R=Right).
  Examples: AL=Drawer A Left, CR=Drawer C Right. Stored in "source" field.
- "Locations" are storage areas (fridge, room temp shelf) containing multiple drawers.
- "Units" are individual medication items in a drawer. Track drug, quantity, expiry.
- "Drugs" are medication definitions (name, strength, form, NDC).
- Barcode formula: LotCode-Date-4LettersOfMed-Dosage (e.g., BL-122225-AMLO-05).

TARGET FIELDS for "{target_table}":
{target_fields}

PARSING RULES — Extract structured data from raw cell values:

1. MEDICATION STRINGS (split into components):
   "Acetaminophen 325MG (5)" → medication_name: "Acetaminophen", strength: 325, strength_unit: "mg", total_quantity: 5, available_quantity: 5
   "Lisinopril 10mg Tablet" → medication_name: "Lisinopril", strength: 10, strength_unit: "mg", form: "Tablet"
   "Omeprazole 20mg Capsule x3" → medication_name: "Omeprazole", strength: 20, strength_unit: "mg", form: "Capsule", total_quantity: 3, available_quantity: 3
   "Metformin HCL 500mg" → medication_name: "Metformin HCL", strength: 500, strength_unit: "mg"
   "Amoxicillin 250mg/5ml Susp" → medication_name: "Amoxicillin", strength: 250, strength_unit: "mg/5ml", form: "Suspension"

2. DRAWER CODES: "AL", "CR", "BL" → source (lots) or lot_source (units helper)

3. DATES (any format → ISO):
   "12/22/2025" → "2025-12-22", "Jan 15, 2026" → "2026-01-15", "2025-12-31" → "2025-12-31"

4. QUANTITIES: "(5)", "x5", "qty: 5", "5" in quantity context → integer.
   When extracted from a medication string, set BOTH total_quantity AND available_quantity.

5. STRENGTH: "325MG" → strength: 325, strength_unit: "mg". "5 mg" → strength: 5, strength_unit: "mg".

6. FORMS (normalize): "Tab"→"Tablet", "Cap"→"Capsule", "Inj"→"Injection", "Susp"→"Suspension", "Sol"→"Solution"

7. TEMPERATURE (normalize): "Room Temp"/"RT"/"Ambient"→"room temp". "Fridge"/"Cold"/"Refrigerated"→"fridge"

8. BARCODES: If a value matches the barcode pattern (e.g., "BL-122225-AMLO-05"), extract:
   lot drawer code → source/lot_source, date → relevant date field, med abbreviation + dosage → medication hints.

IMPORTANT:
- Return ONLY a JSON array with exactly {len(rows)} objects (one per input row).
- Each object contains only the target fields that could be extracted.
- Omit fields with no extractable data. Do NOT include null values.
- Do NOT include auto-managed fields (IDs, timestamps, clinic_id, user_id).
- strength must be a number (not a string). strength_unit must be a string (e.g., "mg").
- total_quantity and available_quantity must be integers.
- All dates must be ISO format strings.

Return ONLY the JSON array. No explanation, no markdown, no code blocks."""

        user_prompt = f"""Parse these {len(rows)} rows for the "{target_table}" table:

CSV Headers: {json.dumps(headers)}

{rows_text}"""

        try:
            response = self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=0.1,
                max_tokens=max(2000, len(rows) * 150),
            )

            text = response.choices[0].message.content.strip()
            text = self._clean_json_response(text)
            parsed = json.loads(text)

            if not isinstance(parsed, list):
                raise ValueError("LLM did not return a JSON array")

            # Validate field names against schema
            valid_fields = get_table_column_names(target_table)
            cleaned = []
            for record in parsed:
                if not isinstance(record, dict):
                    cleaned.append({})
                    continue
                cleaned.append(
                    {k: v for k, v in record.items() if k in valid_fields and v is not None}
                )
            return cleaned

        except json.JSONDecodeError as e:
            logger.error(f"Row parsing batch returned invalid JSON: {e}")
            raise
        except Exception as e:
            logger.error(f"Row parsing batch failed: {e}")
            raise

    # ------------------------------------------------------------------
    # Utilities
    # ------------------------------------------------------------------

    @staticmethod
    def _clean_json_response(text: str) -> str:
        """Strip markdown code fences from an LLM response."""
        if text.startswith("```"):
            lines = text.split("\n")
            text = "\n".join(lines[1:-1]) if len(lines) > 2 else text
            text = text.replace("```json", "").replace("```", "").strip()
        return text

    def _enforce_data_types(self, df: pd.DataFrame) -> pd.DataFrame:
        """Enforce proper data types based on common field name patterns."""
        date_columns = [
            col
            for col in df.columns
            if any(kw in col.lower() for kw in ["date", "timestamp", "created_at", "updated_at"])
        ]
        for col in date_columns:
            try:
                df[col] = pd.to_datetime(df[col], errors="coerce")
                if col == "expiry_date":
                    df[col] = df[col].dt.strftime("%Y-%m-%d")
                else:
                    df[col] = df[col].dt.strftime("%Y-%m-%dT%H:%M:%S%z")
            except Exception:
                pass

        integer_columns = [
            col
            for col in df.columns
            if any(kw in col.lower() for kw in ["quantity", "count", "amount", "capacity"])
        ]
        for col in integer_columns:
            try:
                df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0).astype(int)
            except Exception:
                pass

        decimal_columns = [col for col in df.columns if "strength" in col.lower()]
        for col in decimal_columns:
            try:
                df[col] = pd.to_numeric(df[col], errors="coerce").round(4)
            except Exception:
                pass

        string_columns = df.select_dtypes(include=["object"]).columns
        for col in string_columns:
            if col not in date_columns:
                df[col] = df[col].astype(str).str.strip()
                df[col] = df[col].replace("nan", "")

        return df

    # ------------------------------------------------------------------
    # Main entry point
    # ------------------------------------------------------------------

    async def smart_convert_csv(
        self,
        file_content: bytes,
        target_table: Optional[str] = None,
    ) -> tuple[str, Dict[str, str], list, str]:
        """
        Intelligently convert a messy CSV to match the target schema.

        Phase 1: Quick column mapping (for frontend metadata + table inference).
        Phase 2: Deep row-level parsing (LLM extracts structured fields from
                 raw cell values, splitting combined data as needed).

        Returns:
            (cleaned_csv, column_mapping, unmapped_columns, effective_table)
        """
        try:
            # ---- Step A: Read CSV ----
            df = pd.read_csv(BytesIO(file_content))
            original_headers = df.columns.tolist()
            if not original_headers:
                raise ValueError("CSV file has no columns")

            sample_rows = df.head(3).to_dict(orient="records")

            # ---- Step B: Phase 1 — column mapping + table inference ----
            column_mapping = self._get_column_mapping(
                original_headers, sample_rows, target_table
            )
            unmapped_columns = [h for h in original_headers if h not in column_mapping]

            effective_table = target_table or self._infer_target_table(column_mapping)
            if not effective_table:
                raise ValueError(
                    "Could not determine target table from CSV data. "
                    "Please specify target_table."
                )

            # ---- Step C: Phase 2 — deep row parsing in batches ----
            all_rows = df.to_dict(orient="records")
            parsed_rows: list[dict] = []

            for batch_start in range(0, len(all_rows), ROW_PARSE_BATCH_SIZE):
                batch = all_rows[batch_start : batch_start + ROW_PARSE_BATCH_SIZE]
                batch_num = batch_start // ROW_PARSE_BATCH_SIZE + 1
                total_batches = (len(all_rows) + ROW_PARSE_BATCH_SIZE - 1) // ROW_PARSE_BATCH_SIZE
                logger.info(
                    f"Parsing batch {batch_num}/{total_batches} "
                    f"({len(batch)} rows) for table '{effective_table}'"
                )
                try:
                    batch_parsed = self._parse_rows_batch(
                        original_headers, batch, effective_table
                    )
                    parsed_rows.extend(batch_parsed)
                except Exception as e:
                    logger.error(f"Batch {batch_num} parsing failed, using column-mapping fallback: {e}")
                    # Fallback: simple column rename (old behaviour)
                    for row in batch:
                        fallback = {}
                        for csv_h, target_col in column_mapping.items():
                            v = row.get(csv_h)
                            if pd.notna(v) and str(v).strip() and str(v).strip() != "nan":
                                fallback[target_col] = v
                        parsed_rows.append(fallback)

            # ---- Step D: Build clean DataFrame ----
            df_cleaned = pd.DataFrame(parsed_rows) if parsed_rows else pd.DataFrame()
            df_cleaned = self._enforce_data_types(df_cleaned)

            # ---- Step E: Return ----
            output = StringIO()
            df_cleaned.to_csv(output, index=False)

            return output.getvalue(), column_mapping, unmapped_columns, effective_table

        except pd.errors.EmptyDataError:
            raise ValueError("CSV file is empty")
        except Exception as e:
            raise Exception(f"Error during CSV conversion: {str(e)}")


# Initialize converter instance
converter = CSVConverter()
