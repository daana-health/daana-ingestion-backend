"""
Daana-Rx Database Schema Definition
This serves as the source of truth for column mapping
"""

# Target schema for the daana-rx database
TARGET_SCHEMA = {
    "clinics": {
        "columns": [
            {"name": "clinic_id", "type": "UUID", "description": "Primary key for clinic"},
            {"name": "name", "type": "VARCHAR(255)", "description": "Clinic name"},
            {"name": "primary_color", "type": "VARCHAR(7)", "description": "Primary brand color (hex)", "nullable": True},
            {"name": "secondary_color", "type": "VARCHAR(7)", "description": "Secondary brand color (hex)", "nullable": True},
            {"name": "logo_url", "type": "TEXT", "description": "URL to clinic logo", "nullable": True},
            {"name": "require_lot_location", "type": "BOOLEAN", "description": "Whether to require L/R location specification for lots", "nullable": True},
            {"name": "created_at", "type": "TIMESTAMPTZ", "description": "Record creation timestamp"},
            {"name": "updated_at", "type": "TIMESTAMPTZ", "description": "Record last update timestamp"}
        ]
    },
    "users": {
        "columns": [
            {"name": "user_id", "type": "UUID", "description": "Primary key for user"},
            {"name": "username", "type": "VARCHAR(255)", "description": "Unique username"},
            {"name": "clinic_id", "type": "UUID", "description": "Foreign key to clinics"},
            {"name": "user_role", "type": "VARCHAR(50)", "description": "User role: superadmin, admin, or employee"},
            {"name": "email", "type": "VARCHAR(255)", "description": "User email address"},
            {"name": "created_at", "type": "TIMESTAMPTZ", "description": "Record creation timestamp"},
            {"name": "updated_at", "type": "TIMESTAMPTZ", "description": "Record last update timestamp"}
        ]
    },
    "locations": {
        "columns": [
            {"name": "location_id", "type": "UUID", "description": "Primary key for location"},
            {"name": "name", "type": "VARCHAR(255)", "description": "Location name"},
            {"name": "temp", "type": "VARCHAR(50)", "description": "Storage temperature: fridge or room temp"},
            {"name": "clinic_id", "type": "UUID", "description": "Foreign key to clinics"},
            {"name": "created_at", "type": "TIMESTAMPTZ", "description": "Record creation timestamp"},
            {"name": "updated_at", "type": "TIMESTAMPTZ", "description": "Record last update timestamp"}
        ]
    },
    "lots": {
        "columns": [
            {"name": "lot_id", "type": "UUID", "description": "Primary key for lot"},
            {"name": "source", "type": "VARCHAR(255)", "description": "Source/donation origin of the lot", "nullable": True},
            {"name": "lot_code", "type": "VARCHAR(2)", "description": "2-letter drawer code (e.g., AL, CR)", "nullable": True},
            {"name": "note", "type": "TEXT", "description": "Additional notes about the lot", "nullable": True},
            {"name": "date_created", "type": "TIMESTAMPTZ", "description": "Lot creation date"},
            {"name": "location_id", "type": "UUID", "description": "Foreign key to locations"},
            {"name": "clinic_id", "type": "UUID", "description": "Foreign key to clinics"},
            {"name": "max_capacity", "type": "INTEGER", "description": "Maximum capacity of the lot", "nullable": True}
        ]
    },
    "drugs": {
        "columns": [
            {"name": "drug_id", "type": "UUID", "description": "Primary key for drug"},
            {"name": "medication_name", "type": "VARCHAR(255)", "description": "Brand/trade name of medication"},
            {"name": "generic_name", "type": "VARCHAR(255)", "description": "Generic name of medication", "nullable": True},
            {"name": "strength", "type": "DECIMAL(10, 4)", "description": "Medication strength value"},
            {"name": "strength_unit", "type": "VARCHAR(50)", "description": "Unit of strength (mg, ml, etc.)"},
            {"name": "ndc_id", "type": "VARCHAR(50)", "description": "National Drug Code identifier", "nullable": True},
            {"name": "form", "type": "VARCHAR(100)", "description": "Medication form (tablet, capsule, etc.)"},
            {"name": "created_at", "type": "TIMESTAMPTZ", "description": "Record creation timestamp"}
        ]
    },
    "units": {
        "columns": [
            {"name": "unit_id", "type": "UUID", "description": "Primary key for unit"},
            {"name": "total_quantity", "type": "INTEGER", "description": "Total quantity in unit"},
            {"name": "available_quantity", "type": "INTEGER", "description": "Available quantity in unit"},
            {"name": "patient_reference_id", "type": "VARCHAR(255)", "description": "Reference ID for patient", "nullable": True},
            {"name": "lot_id", "type": "UUID", "description": "Foreign key to lots"},
            {"name": "expiry_date", "type": "DATE", "description": "Expiration date"},
            {"name": "date_created", "type": "TIMESTAMPTZ", "description": "Unit creation timestamp"},
            {"name": "user_id", "type": "UUID", "description": "Foreign key to users"},
            {"name": "drug_id", "type": "UUID", "description": "Foreign key to drugs"},
            {"name": "qr_code", "type": "TEXT", "description": "QR code data", "nullable": True},
            {"name": "optional_notes", "type": "TEXT", "description": "Optional notes", "nullable": True},
            {"name": "manufacturer_lot_number", "type": "VARCHAR(255)", "description": "Manufacturer's lot number", "nullable": True},
            {"name": "clinic_id", "type": "UUID", "description": "Foreign key to clinics"}
        ]
    },
    "transactions": {
        "columns": [
            {"name": "transaction_id", "type": "UUID", "description": "Primary key for transaction"},
            {"name": "timestamp", "type": "TIMESTAMPTZ", "description": "Transaction timestamp"},
            {"name": "type", "type": "VARCHAR(50)", "description": "Transaction type: adjust, check_out, or check_in"},
            {"name": "quantity", "type": "INTEGER", "description": "Quantity involved in transaction"},
            {"name": "unit_id", "type": "UUID", "description": "Foreign key to units"},
            {"name": "patient_name", "type": "VARCHAR(255)", "description": "Patient name"},
            {"name": "patient_reference_id", "type": "VARCHAR(255)", "description": "Patient reference ID"},
            {"name": "user_id", "type": "UUID", "description": "Foreign key to users"},
            {"name": "notes", "type": "TEXT", "description": "Transaction notes"},
            {"name": "clinic_id", "type": "UUID", "description": "Foreign key to clinics"}
        ]
    }
}


def get_schema_description() -> str:
    """
    Generate a formatted schema description for the AI prompt
    """
    schema_text = "Target Database Schema:\n\n"
    
    for table_name, table_info in TARGET_SCHEMA.items():
        schema_text += f"Table: {table_name}\n"
        schema_text += "Columns:\n"
        for col in table_info["columns"]:
            schema_text += f"  - {col['name']} ({col['type']}): {col['description']}\n"
        schema_text += "\n"
    
    return schema_text


def get_all_column_names() -> list:
    """
    Get a flat list of all column names across all tables
    """
    columns = []
    for table_info in TARGET_SCHEMA.values():
        for col in table_info["columns"]:
            columns.append(col["name"])
    return columns
