"""
CSV Conversion Service
Handles intelligent mapping of messy CSV files to the Daana-Rx schema using OpenAI
"""
import json
import pandas as pd
from io import StringIO, BytesIO
from typing import Dict, Optional
from openai import OpenAI
from config import settings
from schema import get_schema_description


class CSVConverter:
    """
    Handles CSV conversion using OpenAI for intelligent column mapping
    """
    
    def __init__(self):
        self.client = OpenAI(api_key=settings.openai_api_key)
    
    def _get_column_mapping(self, csv_headers: list, target_table: Optional[str] = None) -> Dict[str, str]:
        """
        Use OpenAI to intelligently map CSV headers to target schema fields
        
        Args:
            csv_headers: List of headers from the input CSV
            target_table: Optional specific table to target (e.g., 'units', 'drugs')
        
        Returns:
            Dictionary mapping CSV headers to target schema field names
        """
        schema_description = get_schema_description()
        
        # Build the system prompt
        system_prompt = f"""You are a Data Engineer specializing in healthcare data migration.

Your task is to map input CSV column headers to our target database schema.

{schema_description}

Instructions:
1. Analyze the input CSV headers and match them to the most appropriate target schema fields
2. Consider common variations, abbreviations, and medical terminology
3. Return ONLY a valid JSON object mapping CSV headers to target schema field names
4. Use the format: {{"csv_header": "target_field_name"}}
5. If a CSV header doesn't match any target field, omit it from the mapping
6. Be flexible with matching - consider synonyms, common abbreviations, and context
7. Field names should be exact matches from the target schema (case-sensitive)

Examples of flexible matching:
- "Med Name" or "Medicine" → "medication_name"
- "NDC" or "NDC Code" → "ndc_id"
- "Exp Date" or "Expires" → "expiry_date"
- "Qty" or "Amount" → "total_quantity" or "available_quantity"
- "Patient ID" or "MRN" → "patient_reference_id"

Return ONLY the JSON mapping, no explanation or additional text."""

        user_prompt = f"""Map these CSV headers to the target schema:

CSV Headers: {json.dumps(csv_headers)}

{f"Focus on the '{target_table}' table." if target_table else "Consider all tables."}"""

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
            return column_mapping
            
        except Exception as e:
            raise Exception(f"Failed to get column mapping from OpenAI: {str(e)}")
    
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
                # Convert to ISO-8601 format
                df[col] = df[col].dt.strftime('%Y-%m-%dT%H:%M:%S%z')
            except Exception:
                pass
        
        # Integer columns
        integer_columns = [col for col in df.columns if any(
            keyword in col.lower() for keyword in ['quantity', 'count', 'amount']
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
            
            # Step B: Get intelligent mapping from OpenAI
            column_mapping = self._get_column_mapping(original_headers, target_table)
            
            # Track unmapped columns
            unmapped_columns = [
                col for col in original_headers 
                if col not in column_mapping
            ]
            
            # Step C: Rename columns based on mapping
            df_renamed = df.rename(columns=column_mapping)
            
            # Keep only mapped columns
            mapped_columns = list(column_mapping.values())
            df_cleaned = df_renamed[mapped_columns]
            
            # Step D: Enforce data types
            df_cleaned = self._enforce_data_types(df_cleaned)
            
            # Step E: Convert to CSV string
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
