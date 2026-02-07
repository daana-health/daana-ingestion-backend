"""
Ingestion service with deduplication
Handles inserting cleaned CSV data into Supabase with duplicate detection.
"""
import logging
import uuid
from datetime import datetime, timezone
import pandas as pd
from utils.supabase import get_supabase_server

logger = logging.getLogger(__name__)

# Deduplication rules: columns that form the unique composite key per table
DEDUP_KEYS = {
    "drugs": ["medication_name", "strength", "strength_unit", "form"],
    "lots": ["lot_code", "clinic_id"],
    "locations": ["name", "clinic_id"],
    "units": [
        "drug_id",
        "lot_id",
        "expiry_date",
        "manufacturer_lot_number",
        "total_quantity",
    ],
    "transactions": ["timestamp", "type", "unit_id", "quantity"],
    "clinics": ["name"],
    "users": ["email"],
}

# Primary key column name per table
PK_COLUMNS = {
    "drugs": "drug_id",
    "lots": "lot_id",
    "locations": "location_id",
    "units": "unit_id",
    "transactions": "transaction_id",
    "clinics": "clinic_id",
    "users": "user_id",
}


def ingest_data(
    cleaned_df: pd.DataFrame,
    target_table: str,
    clinic_id: str,
    user_id: str,
) -> dict:
    """
    Insert cleaned DataFrame rows into Supabase with deduplication.

    Returns:
        {inserted: int, skipped: int, errors: list}
    """
    if target_table not in DEDUP_KEYS:
        raise ValueError(
            f"Unknown target table: {target_table}. "
            f"Supported: {', '.join(DEDUP_KEYS.keys())}"
        )

    supabase = get_supabase_server()
    inserted = 0
    skipped = 0
    errors = []

    for idx, row in cleaned_df.iterrows():
        try:
            record = _prepare_record(
                row, target_table, clinic_id, user_id, supabase
            )
            if record is None:
                errors.append(f"Row {idx}: Could not prepare record (missing FK)")
                continue

            if _record_exists(supabase, target_table, record):
                skipped += 1
                continue

            # Assign new UUID primary key
            pk_col = PK_COLUMNS[target_table]
            record[pk_col] = str(uuid.uuid4())

            supabase.table(target_table).insert(record).execute()
            inserted += 1

        except Exception as e:
            errors.append(f"Row {idx}: {str(e)}")

    logger.info(
        f"Ingestion complete for {target_table}: "
        f"{inserted} inserted, {skipped} skipped, {len(errors)} errors"
    )
    return {"inserted": inserted, "skipped": skipped, "errors": errors}


def _record_exists(supabase, table: str, record: dict) -> bool:
    """Check if a record with the same dedup key values already exists."""
    dedup_cols = DEDUP_KEYS[table]
    query = supabase.table(table).select(PK_COLUMNS[table])

    for col in dedup_cols:
        value = record.get(col)
        if value is None or (isinstance(value, str) and value == ""):
            query = query.is_(col, "null")
        elif isinstance(value, str) and col in _case_insensitive_cols(table):
            query = query.ilike(col, value)
        else:
            query = query.eq(col, value)

    result = query.limit(1).execute()
    return len(result.data) > 0


def _case_insensitive_cols(table: str) -> set:
    """Columns that should be matched case-insensitively for dedup."""
    return {
        "medication_name",
        "strength_unit",
        "form",
        "name",
        "email",
        "lot_code",
    }


def _prepare_record(
    row: pd.Series,
    table: str,
    clinic_id: str,
    user_id: str,
    supabase,
) -> dict | None:
    """
    Build an insert-ready dict from a DataFrame row.
    Handles FK resolution and auto-populated fields.
    """
    record = {}
    for col, value in row.items():
        if pd.isna(value) or value == "":
            continue
        record[str(col)] = value

    # Remove any PK column the CSV might have included
    pk_col = PK_COLUMNS.get(table)
    if pk_col and pk_col in record:
        del record[pk_col]

    # Set clinic_id from auth context for tables that need it
    if table in ("lots", "locations", "units", "transactions"):
        record["clinic_id"] = clinic_id

    if table == "units":
        record["user_id"] = user_id
        record["date_created"] = datetime.now(timezone.utc).isoformat()

        # Resolve drug_id from medication_name + strength
        if "drug_id" not in record and "medication_name" in record:
            drug_id = _resolve_drug_id(supabase, record)
            if drug_id:
                record["drug_id"] = drug_id
            else:
                logger.warning(
                    f"Could not resolve drug for: {record.get('medication_name')}"
                )
                return None

        # Resolve lot_id from lot_code + clinic_id
        if "lot_id" not in record and "lot_code" in record:
            lot_id = _resolve_lot_id(
                supabase, record.get("lot_code", ""), clinic_id
            )
            if lot_id:
                record["lot_id"] = lot_id
            else:
                logger.warning(
                    f"Could not resolve lot for code: {record.get('lot_code')}"
                )
                return None

        # Remove intermediate columns not in the units schema
        for extra_col in ("medication_name", "strength", "strength_unit", "form", "lot_code", "generic_name"):
            record.pop(extra_col, None)

    if table == "transactions":
        if "user_id" not in record:
            record["user_id"] = user_id

    now_iso = datetime.now(timezone.utc).isoformat()
    if table in ("drugs", "clinics", "users", "locations"):
        if "created_at" not in record:
            record["created_at"] = now_iso
    if table in ("clinics", "users", "locations"):
        if "updated_at" not in record:
            record["updated_at"] = now_iso
    if table == "lots":
        if "date_created" not in record:
            record["date_created"] = now_iso

    return record


def _resolve_drug_id(supabase, record: dict) -> str | None:
    """Look up drug by medication_name + strength, return drug_id or None."""
    med_name = record.get("medication_name", "")
    strength = record.get("strength")

    query = supabase.table("drugs").select("drug_id").ilike(
        "medication_name", med_name
    )
    if strength is not None:
        query = query.eq("strength", strength)

    result = query.limit(1).execute()
    if result.data:
        return result.data[0]["drug_id"]
    return None


def _resolve_lot_id(supabase, lot_code: str, clinic_id: str) -> str | None:
    """Look up lot by lot_code + clinic_id, return lot_id or None."""
    result = (
        supabase.table("lots")
        .select("lot_id")
        .ilike("lot_code", lot_code)
        .eq("clinic_id", clinic_id)
        .limit(1)
        .execute()
    )
    if result.data:
        return result.data[0]["lot_id"]
    return None
