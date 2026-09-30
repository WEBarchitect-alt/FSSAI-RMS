import os
import sys
import sqlite3

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DB_PATH = os.path.join(BASE_DIR, "backend", "db", "sentra_fs.db")

EXISTING_TABLES_EXPECTED = {
    "refusal_events": 62937,
    "charge_crosswalk": 146,
    "defect_standards": 194
}

NEW_TABLES_EXPECTED = [
    "jurisdictions",
    "regulatory_sources",
    "canonical_commodities",
    "canonical_parameters",
    "regulatory_standards"
]

INDEXES_TO_CREATE = [
    ("idx_reg_standards_jurisdiction", "regulatory_standards", "jurisdiction_code"),
    ("idx_reg_standards_commodity", "regulatory_standards", "commodity_code"),
    ("idx_reg_standards_parameter", "regulatory_standards", "parameter_code"),
    ("idx_reg_standards_source", "regulatory_standards", "source_id"),
    ("idx_commodities_group", "canonical_commodities", "commodity_group"),
    ("idx_parameters_category", "canonical_parameters", "hazard_category")
]

def apply_migration(conn):
    cursor = conn.cursor()
    cursor.execute("PRAGMA foreign_keys = ON;")

    # 1. jurisdictions
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS jurisdictions (
            jurisdiction_code TEXT PRIMARY KEY NOT NULL,
            jurisdiction_name TEXT NOT NULL,
            primary_regulator TEXT NOT NULL,
            region TEXT
        );
    """)

    # 2. regulatory_sources
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS regulatory_sources (
            source_id TEXT PRIMARY KEY NOT NULL,
            jurisdiction_code TEXT NOT NULL,
            issuing_body TEXT NOT NULL,
            title TEXT NOT NULL,
            source_type TEXT NOT NULL,
            official_url TEXT NOT NULL,
            retrieval_date TEXT NOT NULL,
            version_or_effective_date TEXT,
            FOREIGN KEY (jurisdiction_code) REFERENCES jurisdictions(jurisdiction_code)
        );
    """)

    # 3. canonical_commodities
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS canonical_commodities (
            commodity_code TEXT PRIMARY KEY NOT NULL,
            commodity_group TEXT NOT NULL,
            display_name TEXT NOT NULL,
            description TEXT,
            hs_code_prefix TEXT
        );
    """)

    # 4. canonical_parameters
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS canonical_parameters (
            parameter_code TEXT PRIMARY KEY NOT NULL,
            parameter_name TEXT NOT NULL,
            hazard_category TEXT NOT NULL,
            cas_number TEXT,
            default_unit TEXT
        );
    """)

    # 5. regulatory_standards
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS regulatory_standards (
            standard_id TEXT PRIMARY KEY NOT NULL,
            source_id TEXT NOT NULL,
            jurisdiction_code TEXT NOT NULL,
            legal_reference TEXT NOT NULL,
            commodity_code TEXT NOT NULL,
            parameter_code TEXT NOT NULL,
            rule_type TEXT NOT NULL,
            operator TEXT,
            numeric_limit REAL,
            unit TEXT,
            textual_condition TEXT,
            original_source_text TEXT NOT NULL,
            effective_date TEXT,
            FOREIGN KEY (source_id) REFERENCES regulatory_sources(source_id),
            FOREIGN KEY (jurisdiction_code) REFERENCES jurisdictions(jurisdiction_code),
            FOREIGN KEY (commodity_code) REFERENCES canonical_commodities(commodity_code),
            FOREIGN KEY (parameter_code) REFERENCES canonical_parameters(parameter_code)
        );
    """)

    # Indexes
    for idx_name, tbl_name, col_name in INDEXES_TO_CREATE:
        cursor.execute(f"CREATE INDEX IF NOT EXISTS {idx_name} ON {tbl_name}({col_name});")

    conn.commit()

def run_validations(conn):
    cursor = conn.cursor()
    cursor.execute("PRAGMA foreign_keys = ON;")
    validation_passed = True

    print("\n" + "=" * 65)
    print(" SENTRA-FS MULTI-JURISDICTION SCHEMA MIGRATION AUDIT")
    print("=" * 65)

    # 1. Verify existing tables & row counts
    print("[1] Verifying Pre-Existing FDA Tables Preservation:")
    for tbl, expected_cnt in EXISTING_TABLES_EXPECTED.items():
        cursor.execute(f"SELECT COUNT(*) FROM {tbl};")
        cnt = cursor.fetchone()[0]
        status = "PASS" if cnt == expected_cnt else "FAIL"
        if cnt != expected_cnt:
            validation_passed = False
        print(f"    - {tbl:<18}: {cnt:,} rows (Expected: {expected_cnt:,}) [{status}]")

    # 2. Verify new tables exist and contain exactly 0 rows
    print("\n[2] Verifying New Extension Tables Initial State:")
    for tbl in NEW_TABLES_EXPECTED:
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?;", (tbl,))
        exists = cursor.fetchone() is not None
        if not exists:
            validation_passed = False
            print(f"    - {tbl:<22}: Table missing [FAIL]")
            continue
        
        cursor.execute(f"SELECT COUNT(*) FROM {tbl};")
        cnt = cursor.fetchone()[0]
        status = "PASS" if cnt == 0 else "FAIL"
        if cnt != 0:
            validation_passed = False
        print(f"    - {tbl:<22}: {cnt} rows (Expected: 0) [{status}]")

    # 3. Verify created indexes
    print("\n[3] Verifying Multi-Jurisdiction Indexes:")
    for idx_name, tbl_name, col_name in INDEXES_TO_CREATE:
        cursor.execute("SELECT name FROM sqlite_master WHERE type='index' AND name=?;", (idx_name,))
        exists = cursor.fetchone() is not None
        status = "PASS" if exists else "FAIL"
        if not exists:
            validation_passed = False
        print(f"    - {idx_name:<32} on {tbl_name}({col_name}) [{status}]")

    # 4. Foreign Key Integrity Check
    print("\n[4] Executing Foreign Key Integrity Audit:")
    cursor.execute("PRAGMA foreign_key_check;")
    fk_violations = cursor.fetchall()
    if len(fk_violations) == 0:
        print("    - PRAGMA foreign_key_check: 0 violations detected [PASS]")
    else:
        validation_passed = False
        print(f"    - PRAGMA foreign_key_check: {len(fk_violations)} violations detected [FAIL]: {fk_violations}")

    print("=" * 65)
    print(f"OVERALL STATUS: {'MIGRATION SUCCESSFUL - ALL CHECKS PASSED' if validation_passed else 'MIGRATION FAILED'}")
    print("=" * 65 + "\n")

    return validation_passed

def main():
    if not os.path.exists(DB_PATH):
        print(f"ERROR: Target database not found at: {DB_PATH}")
        sys.exit(1)

    print(f"[*] Connecting to database at: {DB_PATH}")
    conn = sqlite3.connect(DB_PATH)
    try:
        print("[*] Applying non-destructive DDL migration...")
        apply_migration(conn)
        passed = run_validations(conn)
        if not passed:
            sys.exit(1)
    finally:
        conn.close()

if __name__ == "__main__":
    main()