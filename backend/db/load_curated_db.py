import os
import sys
import sqlite3
import pandas as pd

# Paths
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DB_DIR = os.path.join(BASE_DIR, "backend", "db")
DB_PATH = os.path.join(DB_DIR, "sentra_fs.db")

CURATED_REFUSALS_CSV = os.path.join(BASE_DIR, "data", "curated", "fda_food_refusals_curated.csv")
CHARGE_REF_CSV = os.path.join(BASE_DIR, "data", "acquisition", "fda_charge_reference.csv")
DEFECT_LEVELS_CSV = os.path.join(BASE_DIR, "data", "acquisition", "fda_defect_levels.csv")

EXPECTED_COUNTS = {
    "refusal_events": 62937,
    "charge_crosswalk": 146,
    "defect_standards": 194
}

def init_db(conn):
    cursor = conn.cursor()

    # Drop existing tables to ensure deterministic fresh load
    cursor.execute("DROP TABLE IF EXISTS refusal_events;")
    cursor.execute("DROP TABLE IF EXISTS charge_crosswalk;")
    cursor.execute("DROP TABLE IF EXISTS defect_standards;")

    # 1. refusal_events table (id is primary key; refusal_id allows duplicates per audit)
    cursor.execute("""
        CREATE TABLE refusal_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            refusal_id TEXT,
            entry_num TEXT,
            line_num TEXT,
            refusal_date TEXT,
            product_code TEXT,
            industry_code TEXT,
            food_class TEXT,
            product_desc TEXT,
            country_code TEXT,
            country_name TEXT,
            manufacturer_name TEXT,
            manufacturer_city TEXT,
            port_of_entry TEXT,
            primary_charge_code TEXT,
            all_charge_codes TEXT,
            raw_charges TEXT,
            primary_act_section TEXT,
            primary_charge_statement TEXT,
            all_act_sections TEXT,
            all_charge_statements TEXT,
            charge_category TEXT,
            defect_standard_status TEXT,
            potential_defect_commodities TEXT
        );
    """)

    # 2. charge_crosswalk table
    cursor.execute("""
        CREATE TABLE charge_crosswalk (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            charge_code TEXT,
            occurrence_count INTEGER,
            match_status TEXT,
            act_section TEXT,
            charge_statement TEXT
        );
    """)

    # 3. defect_standards table
    cursor.execute("""
        CREATE TABLE defect_standards (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            product TEXT,
            defect TEXT,
            method TEXT,
            action_level TEXT,
            source_document TEXT,
            source_table TEXT
        );
    """)

    conn.commit()

def create_indexes(conn):
    cursor = conn.cursor()
    indexes = [
        ("idx_refusal_date", "refusal_events", "refusal_date"),
        ("idx_country_code", "refusal_events", "country_code"),
        ("idx_industry_code", "refusal_events", "industry_code"),
        ("idx_charge_category", "refusal_events", "charge_category"),
        ("idx_food_class", "refusal_events", "food_class"),
        # Additional operational indexes for search and investigation drill-downs
        ("idx_manufacturer_name", "refusal_events", "manufacturer_name"),
        ("idx_primary_charge_code", "refusal_events", "primary_charge_code"),
        ("idx_defect_standard_status", "refusal_events", "defect_standard_status"),
        ("idx_charge_crosswalk_code", "charge_crosswalk", "charge_code"),
        ("idx_defect_standards_product", "defect_standards", "product")
    ]

    for idx_name, tbl_name, col_name in indexes:
        cursor.execute(f"CREATE INDEX IF NOT EXISTS {idx_name} ON {tbl_name}({col_name});")

    conn.commit()
    return [idx[0] for idx in indexes]

def load_data(conn):
    # Verify input files exist
    for path, name in [(CURATED_REFUSALS_CSV, "Curated Refusals"), (CHARGE_REF_CSV, "Charge Reference"), (DEFECT_LEVELS_CSV, "Defect Levels")]:
        if not os.path.exists(path):
            print(f"ERROR: Required input file missing: {path}")
            sys.exit(1)

    # 1. Load Curated Refusal Events
    df_refusals = pd.read_csv(CURATED_REFUSALS_CSV, dtype=str, keep_default_na=False)
    # Map CSV column headers to SQLite table columns
    refusals_cols = [
        "REFUSAL_ID", "ENTRY_NUM", "LINE_NUM", "REFUSAL_DATE", "PRODUCT_CODE",
        "INDUSTRY_CODE", "FOOD_CLASS", "PRODUCT_DESC", "COUNTRY_CODE", "COUNTRY_NAME",
        "MANUFACTURER_NAME", "MANUFACTURER_CITY", "PORT_OF_ENTRY", "PRIMARY_CHARGE_CODE",
        "ALL_CHARGE_CODES", "RAW_CHARGES", "PRIMARY_ACT_SECTION", "PRIMARY_CHARGE_STATEMENT",
        "ALL_ACT_SECTIONS", "ALL_CHARGE_STATEMENTS", "CHARGE_CATEGORY",
        "DEFECT_STANDARD_STATUS", "POTENTIAL_DEFECT_COMMODITIES"
    ]
    df_refusals_db = df_refusals[refusals_cols].copy()
    df_refusals_db.columns = [c.lower() for c in refusals_cols]
    df_refusals_db.to_sql("refusal_events", conn, if_exists="append", index=False)

    # 2. Load Charge Reference
    df_charges = pd.read_csv(CHARGE_REF_CSV, dtype=str, keep_default_na=False)
    # Identify available columns in fda_charge_reference.csv
    charge_col_map = {
        "CHARGE_CODE": "charge_code",
        "OCCURRENCE_COUNT": "occurrence_count",
        "MATCH_STATUS": "match_status",
        "ACT_SECTION": "act_section",
        "CHARGE_STATEMENT": "charge_statement"
    }
    available_charge_cols = [c for c in charge_col_map.keys() if c in df_charges.columns]
    df_charges_db = df_charges[available_charge_cols].rename(columns=charge_col_map)
    if "occurrence_count" in df_charges_db.columns:
        df_charges_db["occurrence_count"] = pd.to_numeric(df_charges_db["occurrence_count"], errors="coerce").fillna(0).astype(int)
    df_charges_db.to_sql("charge_crosswalk", conn, if_exists="append", index=False)

    # 3. Load Defect Standards
    df_defects = pd.read_csv(DEFECT_LEVELS_CSV, dtype=str, keep_default_na=False)
    defect_col_map = {
        "PRODUCT": "product",
        "DEFECT": "defect",
        "METHOD": "method",
        "ACTION_LEVEL": "action_level",
        "SOURCE_DOCUMENT": "source_document",
        "SOURCE_TABLE": "source_table"
    }
    available_defect_cols = [c for c in defect_col_map.keys() if c in df_defects.columns]
    df_defects_db = df_defects[available_defect_cols].rename(columns=defect_col_map)
    df_defects_db.to_sql("defect_standards", conn, if_exists="append", index=False)

def validate_db(conn):
    cursor = conn.cursor()
    validation_passed = True
    actual_counts = {}

    for table, expected_cnt in EXPECTED_COUNTS.items():
        cursor.execute(f"SELECT COUNT(*) FROM {table};")
        cnt = cursor.fetchone()[0]
        actual_counts[table] = cnt
        if cnt != expected_cnt:
            validation_passed = False
            print(f"[!] Validation Failure: Table '{table}' has {cnt:,} rows, expected {expected_cnt:,}")

    # Verify column existence on refusal_events
    cursor.execute("PRAGMA table_info(refusal_events);")
    columns_info = cursor.fetchall()
    actual_cols = {col[1] for col in columns_info}
    expected_cols = {
        "id", "refusal_id", "entry_num", "line_num", "refusal_date", "product_code",
        "industry_code", "food_class", "product_desc", "country_code", "country_name",
        "manufacturer_name", "manufacturer_city", "port_of_entry", "primary_charge_code",
        "all_charge_codes", "raw_charges", "primary_act_section", "primary_charge_statement",
        "all_act_sections", "all_charge_statements", "charge_category",
        "defect_standard_status", "potential_defect_commodities"
    }

    if not expected_cols.issubset(actual_cols):
        validation_passed = False
        missing = expected_cols - actual_cols
        print(f"[!] Validation Failure: Missing columns in refusal_events: {missing}")

    return validation_passed, actual_counts

def main():
    os.makedirs(DB_DIR, exist_ok=True)
    print(f"[*] Initializing SENTRA-FS database at: {DB_PATH}")

    conn = sqlite3.connect(DB_PATH)
    try:
        init_db(conn)
        print("[*] Tables created successfully.")

        load_data(conn)
        print("[*] Data ingestion completed.")

        created_indexes = create_indexes(conn)
        print(f"[*] Created {len(created_indexes)} database indexes.")

        passed, counts = validate_db(conn)

        print("\n" + "=" * 55)
        print(" SENTRA-FS DATABASE INITIALIZATION REPORT")
        print("=" * 55)
        print(f"Database Path : {DB_PATH}")
        print(f"Tables Created: refusal_events, charge_crosswalk, defect_standards")
        print("Rows Loaded   :")
        for tbl, cnt in counts.items():
            expected = EXPECTED_COUNTS[tbl]
            status = "MATCH" if cnt == expected else "MISMATCH"
            print(f"  - {tbl:<18}: {cnt:,} rows (Expected: {expected:,}) [{status}]")
        print(f"Indexes Built : {', '.join(created_indexes)}")
        print(f"Validation    : {'SUCCESS - ALL AUDIT CRITERIA MET' if passed else 'FAILED'}")
        print("=" * 55 + "\n")

        if not passed:
            sys.exit(1)

    finally:
        conn.close()

if __name__ == "__main__":
    main()