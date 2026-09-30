import os
import sys
import sqlite3
import csv
import re
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DB_PATH = os.path.join(BASE_DIR, "backend", "db", "sentra_fs.db")
CLEAN_CSV_PATH = os.path.join(BASE_DIR, "data", "curated", "rasff_border_events_clean.csv")

EXPECTED_FDA_COUNTS = {
    "refusal_events": 62937,
    "charge_crosswalk": 146,
    "defect_standards": 194
}

CANONICAL_BRIDGE_MAPPINGS = [
    # EU High-Confidence Mappings
    ("EU", "herbs and spices", "herbs and spices", "SPICES_AND_HERBS", "HIGH"),
    ("EU", "nuts, nut products and seeds", "nuts, nut products and seeds", "NUTS_AND_SEEDS", "HIGH"),
    ("EU", "fish and fish products", "fish and fish products", "SEAFOOD", "HIGH"),
    ("EU", "crustaceans and products thereof", "crustaceans and products thereof", "SEAFOOD", "HIGH"),
    ("EU", "bivalve molluscs and products thereof", "bivalve molluscs and products thereof", "SEAFOOD", "HIGH"),
    ("EU", "cephalopods and products thereof", "cephalopods and products thereof", "SEAFOOD", "HIGH"),
    ("EU", "fruits and vegetables", "fruits and vegetables", "FRUITS_AND_VEGETABLES", "HIGH"),
    ("EU", "cereals and bakery products", "cereals and bakery products", "GRAINS_AND_CEREALS", "HIGH"),
    ("EU", "dietetic foods, food supplements and fortified foods", "dietetic foods, food supplements and fortified foods", "DIETARY_SUPPLEMENTS", "HIGH"),
    ("EU", "poultry meat and poultry meat products", "poultry meat and poultry meat products", "MEAT_AND_POULTRY", "HIGH"),
    ("EU", "meat and meat products (other than poultry)", "meat and meat products (other than poultry)", "MEAT_AND_POULTRY", "HIGH"),
    ("EU", "milk and milk products", "milk and milk products", "DAIRY", "HIGH"),
    ("EU", "fats and oils", "fats and oils", "FATS_AND_OILS", "HIGH"),
    ("EU", "cocoa and cocoa preparations, coffee and tea", "cocoa and cocoa preparations, coffee and tea", "BEVERAGES_AND_STIMULANTS", "HIGH"),
    # FDA In-Scope Core Industry Codes for Cross-Bridge Symmetry
    ("US", "28", "Spices, Flavors and Salts", "SPICES_AND_HERBS", "HIGH"),
    ("US", "23", "Nuts and Edible Seeds", "NUTS_AND_SEEDS", "HIGH"),
    ("US", "16", "Fishery/Seafood Products", "SEAFOOD", "HIGH"),
    ("US", "20", "Fruit and Fruit Products (Citrus)", "FRUITS_AND_VEGETABLES", "HIGH"),
    ("US", "21", "Fruit and Fruit Products (Non-Citrus)", "FRUITS_AND_VEGETABLES", "HIGH"),
    ("US", "22", "Fruit and Fruit Products (Dried/Processed)", "FRUITS_AND_VEGETABLES", "HIGH"),
    ("US", "24", "Vegetables and Vegetable Products (Fresh/Frozen)", "FRUITS_AND_VEGETABLES", "HIGH"),
    ("US", "25", "Vegetables and Vegetable Products (Canned/Processed)", "FRUITS_AND_VEGETABLES", "HIGH"),
    ("US", "02", "Whole Grain", "GRAINS_AND_CEREALS", "HIGH"),
    ("US", "03", "Bakery Products / Dough Mixes", "GRAINS_AND_CEREALS", "HIGH"),
    ("US", "04", "Macaroni and Noodle Products", "GRAINS_AND_CEREALS", "HIGH"),
    ("US", "05", "Cereal Preparations / Breakfast Foods", "GRAINS_AND_CEREALS", "HIGH"),
    ("US", "54", "Vitamins, Minerals, Dietary Supplements", "DIETARY_SUPPLEMENTS", "HIGH"),
    ("US", "17", "Meat and Poultry Products", "MEAT_AND_POULTRY", "HIGH"),
    ("US", "09", "Milk / Butter / Dried Milk Products", "DAIRY", "HIGH"),
    ("US", "12", "Cheese and Cheese Products", "DAIRY", "HIGH"),
    ("US", "26", "Vegetable Oils", "FATS_AND_OILS", "HIGH"),
    ("US", "31", "Coffee and Tea", "BEVERAGES_AND_STIMULANTS", "HIGH"),
    ("US", "34", "Chocolate and Cocoa Products", "BEVERAGES_AND_STIMULANTS", "HIGH")
]

DATE_FORMAT_PATTERN = re.compile(r"^(\d{2})-(\d{2})-(\d{4})")

def init_tables(conn):
    cursor = conn.cursor()
    cursor.execute("PRAGMA foreign_keys = ON;")

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS eu_border_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            reference TEXT NOT NULL UNIQUE,
            category TEXT,
            type TEXT NOT NULL,
            subject TEXT NOT NULL,
            event_date TEXT NOT NULL,
            event_year INTEGER NOT NULL,
            event_timestamp TEXT NOT NULL,
            notifying_country TEXT NOT NULL,
            classification TEXT NOT NULL,
            risk_decision TEXT NOT NULL,
            distribution TEXT,
            for_attention TEXT,
            for_follow_up TEXT,
            operator TEXT,
            origin TEXT,
            primary_origin_country TEXT,
            hazards_raw TEXT,
            primary_hazard_substance TEXT,
            primary_hazard_category TEXT,
            has_multiple_hazards INTEGER NOT NULL DEFAULT 0,
            food_class_scope TEXT NOT NULL
        );
    """)

    cursor.execute("CREATE INDEX IF NOT EXISTS idx_eu_event_date ON eu_border_events(event_date);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_eu_category ON eu_border_events(category);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_eu_classification ON eu_border_events(classification);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_eu_primary_origin ON eu_border_events(primary_origin_country);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_eu_primary_hazard_cat ON eu_border_events(primary_hazard_category);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_eu_food_class_scope ON eu_border_events(food_class_scope);")

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS canonical_commodity_bridge (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            jurisdiction_code TEXT NOT NULL,
            source_category_code TEXT NOT NULL,
            source_category_desc TEXT NOT NULL,
            canonical_commodity_group TEXT NOT NULL,
            mapping_confidence TEXT NOT NULL
        );
    """)

    cursor.execute("CREATE INDEX IF NOT EXISTS idx_bridge_jurisdiction ON canonical_commodity_bridge(jurisdiction_code);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_bridge_canonical_group ON canonical_commodity_bridge(canonical_commodity_group);")

    conn.commit()

def populate_bridge_table(conn):
    cursor = conn.cursor()
    cursor.execute("DELETE FROM canonical_commodity_bridge;")
    cursor.executemany("""
        INSERT INTO canonical_commodity_bridge (
            jurisdiction_code, source_category_code, source_category_desc,
            canonical_commodity_group, mapping_confidence
        ) VALUES (?, ?, ?, ?, ?);
    """, CANONICAL_BRIDGE_MAPPINGS)
    conn.commit()

def parse_date(date_str):
    d_clean = date_str.strip()
    m = DATE_FORMAT_PATTERN.match(d_clean)
    if m:
        day, month, year = m.group(1), m.group(2), m.group(3)
        iso_date = f"{year}-{month}-{day}"
        return iso_date, int(year)
    try:
        dt = datetime.strptime(d_clean[:10], "%d-%m-%Y")
        return dt.strftime("%Y-%m-%d"), dt.year
    except Exception:
        return "UNKNOWN_DATE", 0

def parse_origin(origin_raw):
    if not origin_raw or origin_raw.strip() == "":
        return None, None
    orig_clean = origin_raw.strip()
    parts = [p.strip() for p in orig_clean.split(",") if p.strip()]
    primary = parts[0] if parts else None
    return orig_clean, primary

def parse_hazard(h_raw):
    if not h_raw or h_raw.strip() == "":
        return None, None, None, 0
    h_str = h_raw.strip()
    clauses = [c.strip() for c in h_str.split(",") if c.strip()]
    has_multiple = 1 if len(clauses) > 1 else 0

    first_clause = clauses[0] if clauses else h_str
    m = re.match(r"^(.*?)\s*-\s*\{([^}]+)\}", first_clause)
    if m:
        substance = m.group(1).strip()
        cat = m.group(2).strip()
        return h_str, substance, cat, has_multiple

    if " - " in first_clause:
        parts = first_clause.split(" - ", 1)
        return h_str, parts[0].strip(), parts[1].strip(), has_multiple

    return h_str, first_clause, None, has_multiple

def derive_food_class_scope(type_raw):
    t = type_raw.strip().lower() if type_raw else ""
    if t == "food":
        return "HUMAN_FOOD"
    elif t == "feed":
        return "FEED"
    elif t == "food contact material":
        return "FCM"
    else:
        return "OTHER"

def load_rasff_data(conn):
    if not os.path.exists(CLEAN_CSV_PATH):
        print(f"FATAL ERROR: Clean CSV not found at: {CLEAN_CSV_PATH}")
        sys.exit(1)

    cursor = conn.cursor()
    cursor.execute("SELECT reference FROM eu_border_events;")
    existing_refs = {row[0] for row in cursor.fetchall()}

    rows_read = 0
    rows_skipped = 0
    rows_failed = 0
    insert_payload = []

    with open(CLEAN_CSV_PATH, "r", encoding="utf-8", errors="replace") as f:
        reader = csv.DictReader(f)
        for line_no, row in enumerate(reader, start=2):
            rows_read += 1
            ref = row["reference"].strip()
            if ref in existing_refs:
                rows_skipped += 1
                continue

            try:
                event_date, event_year = parse_date(row["date"])
                raw_origin, primary_origin = parse_origin(row.get("origin", ""))
                h_raw, h_sub, h_cat, has_multi = parse_hazard(row.get("hazards", ""))
                scope = derive_food_class_scope(row.get("type", ""))

                insert_payload.append((
                    ref,
                    row.get("category", "").strip() or None,
                    row.get("type", "").strip(),
                    row.get("subject", "").strip(),
                    event_date,
                    event_year,
                    row.get("date", "").strip(),
                    row.get("notifying_country", "").strip(),
                    row.get("classification", "").strip(),
                    row.get("risk_decision", "").strip(),
                    row.get("distribution", "").strip() or None,
                    row.get("forAttention", "").strip() or None,
                    row.get("forFollowUp", "").strip() or None,
                    row.get("operator", "").strip() or None,
                    raw_origin,
                    primary_origin,
                    h_raw,
                    h_sub,
                    h_cat,
                    has_multi,
                    scope
                ))
                existing_refs.add(ref)
            except Exception as e:
                rows_failed += 1
                print(f"[!] Row parsing error at line {line_no}: {e}")

    if insert_payload:
        cursor.executemany("""
            INSERT INTO eu_border_events (
                reference, category, type, subject, event_date, event_year,
                event_timestamp, notifying_country, classification, risk_decision,
                distribution, for_attention, for_follow_up, operator, origin,
                primary_origin_country, hazards_raw, primary_hazard_substance,
                primary_hazard_category, has_multiple_hazards, food_class_scope
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
        """, insert_payload)
        conn.commit()

    rows_inserted = len(insert_payload)
    return rows_read, rows_inserted, rows_skipped, rows_failed

def run_validations(conn):
    cursor = conn.cursor()
    cursor.execute("PRAGMA foreign_keys = ON;")
    validation_passed = True

    # 1. FDA row counts
    fda_counts = {}
    for tbl, exp in EXPECTED_FDA_COUNTS.items():
        cursor.execute(f"SELECT COUNT(*) FROM {tbl};")
        cnt = cursor.fetchone()[0]
        fda_counts[tbl] = (cnt, exp)
        if cnt != exp:
            validation_passed = False

    # 2. EU row count and unique refs
    cursor.execute("SELECT COUNT(*), COUNT(DISTINCT reference) FROM eu_border_events;")
    eu_total, eu_unique = cursor.fetchone()
    if eu_total != 30000 or eu_unique != 30000:
        validation_passed = False

    # 3. Hazard statistics
    cursor.execute("SELECT COUNT(*) FROM eu_border_events WHERE hazards_raw IS NOT NULL AND hazards_raw != '';")
    with_hazards = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM eu_border_events WHERE hazards_raw IS NULL OR hazards_raw = '';")
    without_hazards = cursor.fetchone()[0]

    # 4. Bridge statistics
    cursor.execute("""
        SELECT COUNT(e.id)
        FROM eu_border_events e
        INNER JOIN canonical_commodity_bridge b
            ON b.jurisdiction_code = 'EU' AND b.source_category_code = e.category;
    """)
    mapped_count = cursor.fetchone()[0]
    unmapped_count = eu_total - mapped_count

    cursor.execute("SELECT COUNT(*) FROM canonical_commodity_bridge WHERE mapping_confidence = 'HIGH';")
    high_conf_mappings = cursor.fetchone()[0]

    # 5. Foreign key check
    cursor.execute("PRAGMA foreign_key_check;")
    fk_violations = cursor.fetchall()
    if len(fk_violations) > 0:
        validation_passed = False

    return validation_passed, fda_counts, eu_total, eu_unique, with_hazards, without_hazards, mapped_count, unmapped_count, high_conf_mappings, len(fk_violations)

def main():
    if not os.path.exists(DB_PATH):
        print(f"FATAL ERROR: Target database not found at {DB_PATH}")
        sys.exit(1)

    print(f"[*] Connecting to database: {DB_PATH}")
    conn = sqlite3.connect(DB_PATH)
    try:
        init_tables(conn)
        populate_bridge_table(conn)
        read_cnt, ins_cnt, skip_cnt, fail_cnt = load_rasff_data(conn)
        val_passed, fda_cnts, eu_tot, eu_uniq, w_haz, wo_haz, map_cnt, unmap_cnt, high_cnt, fk_viol = run_validations(conn)

        print("\n" + "=" * 65)
        print(" SENTRA-FS EU RASFF INGESTION AUDIT REPORT")
        print("=" * 65)
        print("1. PRE-EXISTING FDA DATA INTEGRITY:")
        for tbl, (act, exp) in fda_cnts.items():
            status = "MATCH" if act == exp else "MISMATCH"
            print(f"   - {tbl:<18}: {act:,} rows (Expected: {exp:,}) [{status}]")

        print("\n2. EU RASFF INGESTION TELEMETRY:")
        print(f"   - Rows Read from Clean CSV      : {read_cnt:,}")
        print(f"   - Rows Inserted                 : {ins_cnt:,}")
        print(f"   - Rows Skipped (Already Present): {skip_cnt:,}")
        print(f"   - Rows Failed                   : {fail_cnt:,}")
        print(f"   - Total `eu_border_events` Rows : {eu_tot:,} (Expected: 30,000)")
        print(f"   - Distinct References           : {eu_uniq:,} (Expected: 30,000)")

        print("\n3. HAZARD DECOMPOSITION AUDIT:")
        print(f"   - Events with Populated Hazards : {w_haz:,} ({(w_haz/eu_tot)*100:.2f}%)")
        print(f"   - Events with Empty Hazards     : {wo_haz:,} ({(wo_haz/eu_tot)*100:.2f}%)")

        print("\n4. CANONICAL COMMODITY BRIDGE COVERAGE:")
        print(f"   - Events Mapped to Canonical Grp: {map_cnt:,} ({(map_cnt/eu_tot)*100:.2f}%)")
        print(f"   - Events Unmapped (Preserved)   : {unmap_cnt:,} ({(unmap_cnt/eu_tot)*100:.2f}%)")
        print(f"   - High-Confidence Bridge Rules  : {high_cnt} definitions")

        print("\n5. RELATIONAL INTEGRITY:")
        print(f"   - PRAGMA foreign_key_check      : {fk_viol} violations")

        print("=" * 65)
        print(f"OVERALL STATUS: {'SUCCESS - ALL AUDIT CONSTRAINTS SATISFIED' if val_passed else 'FAILED'}")
        print("=" * 65 + "\n")

        if not val_passed or fail_cnt > 0:
            sys.exit(1)

    finally:
        conn.close()

if __name__ == "__main__":
    main()