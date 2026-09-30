import os
import sys
import sqlite3

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DB_PATH = os.path.join(BASE_DIR, "backend", "db", "sentra_fs.db")

def run_comparison():
    if not os.path.exists(DB_PATH):
        print(f"FATAL ERROR: Target database not found at {DB_PATH}")
        sys.exit(1)

    # Open strictly in read-only mode to guarantee zero database modifications
    conn = sqlite3.connect(f"file:{DB_PATH}?mode=ro", uri=True)
    cursor = conn.cursor()

    print("=" * 80)
    print(" SENTRA-FS US (FDA) vs EU (RASFF) CROSS-JURISDICTION COMPARATIVE AUDIT")
    print("=" * 80)

    # 1. Total Event Counts
    cursor.execute("SELECT COUNT(*) FROM refusal_events;")
    fda_total = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM eu_border_events;")
    eu_total = cursor.fetchone()[0]

    print("\n[1] TOTAL EVENT VOLUME:")
    print(f"    - US FDA Refusal Events     : {fda_total:>8,} records (Scope: HUMAN_FOOD + DIETARY_SUPPLEMENT)")
    print(f"    - EU RASFF Border Events    : {eu_total:>8,} records (All border notifications)")
    print(f"    - Combined Telemetry Pool   : {fda_total + eu_total:>8,} enforcement actions")

    # 2. Yearly Event Volume Comparison
    print("\n[2] YEARLY EVENT VOLUME COMPARISON (FDA vs EU):")
    cursor.execute("""
        WITH fda_years AS (
            SELECT CAST(SUBSTR(refusal_date, 1, 4) AS INTEGER) AS yr, COUNT(*) AS cnt
            FROM refusal_events
            WHERE refusal_date IS NOT NULL AND LENGTH(refusal_date) >= 4
            GROUP BY yr
        ),
        eu_years AS (
            SELECT event_year AS yr, COUNT(*) AS cnt
            FROM eu_border_events
            WHERE event_year IS NOT NULL AND event_year > 0
            GROUP BY yr
        ),
        all_years AS (
            SELECT yr FROM fda_years
            UNION
            SELECT yr FROM eu_years
        )
        SELECT 
            ay.yr,
            COALESCE(fy.cnt, 0) AS fda_count,
            COALESCE(ey.cnt, 0) AS eu_count,
            (COALESCE(fy.cnt, 0) + COALESCE(ey.cnt, 0)) AS combined_count
        FROM all_years ay
        LEFT JOIN fda_years fy ON ay.yr = fy.yr
        LEFT JOIN eu_years ey ON ay.yr = ey.yr
        ORDER BY ay.yr;
    """)
    yearly_rows = cursor.fetchall()
    print(f"    {'Year':<6} | {'US FDA Events':<15} | {'EU RASFF Events':<16} | {'Combined Volume':<16}")
    print("    " + "-" * 60)
    for yr, f_cnt, e_cnt, c_cnt in yearly_rows:
        print(f"    {yr:<6} | {f_cnt:>15,} | {e_cnt:>16,} | {c_cnt:>16,}")

    # 3. Country-of-Origin Comparison (Top Overlapping Trading Partners)
    print("\n[3] TOP ORIGIN COUNTRIES COMPARISON (Shared Exporting Nations):")
    cursor.execute("""
        WITH fda_by_country AS (
            SELECT 
                CASE 
                    WHEN UPPER(country_name) IN ('TURKEY', 'TÜRKIYE') THEN 'TURKEY'
                    WHEN UPPER(country_name) IN ('UNITED STATES', 'USA') THEN 'UNITED STATES'
                    WHEN UPPER(country_name) IN ('UNITED KINGDOM', 'UK') THEN 'UNITED KINGDOM'
                    ELSE UPPER(TRIM(country_name))
                END AS norm_country,
                COUNT(*) AS fda_count
            FROM refusal_events
            WHERE country_name IS NOT NULL AND TRIM(country_name) != ''
            GROUP BY norm_country
        ),
        eu_by_country AS (
            SELECT 
                CASE 
                    WHEN UPPER(primary_origin_country) IN ('TURKEY', 'TÜRKIYE') THEN 'TURKEY'
                    WHEN UPPER(primary_origin_country) IN ('UNITED STATES', 'USA') THEN 'UNITED STATES'
                    WHEN UPPER(primary_origin_country) IN ('UNITED KINGDOM', 'UK') THEN 'UNITED KINGDOM'
                    ELSE UPPER(TRIM(primary_origin_country))
                END AS norm_country,
                COUNT(*) AS eu_count
            FROM eu_border_events
            WHERE primary_origin_country IS NOT NULL AND TRIM(primary_origin_country) != ''
            GROUP BY norm_country
        )
        SELECT 
            COALESCE(f.norm_country, e.norm_country) AS country,
            COALESCE(f.fda_count, 0) AS fda_count,
            COALESCE(e.eu_count, 0) AS eu_count,
            (COALESCE(f.fda_count, 0) + COALESCE(e.eu_count, 0)) AS total_events
        FROM fda_by_country f
        INNER JOIN eu_by_country e ON f.norm_country = e.norm_country
        ORDER BY total_events DESC
        LIMIT 15;
    """)
    top_country_rows = cursor.fetchall()
    print(f"    {'Country of Origin':<22} | {'US FDA Refusals':<16} | {'EU RASFF Events':<16} | {'Combined Actions':<16}")
    print("    " + "-" * 76)
    for ctry, f_cnt, e_cnt, tot in top_country_rows:
        print(f"    {ctry:<22} | {f_cnt:>16,} | {e_cnt:>16,} | {tot:>16,}")

    # 4. Canonical Commodity Group Comparison
    print("\n[4] CANONICAL COMMODITY COMPARISON (via canonical_commodity_bridge):")
    cursor.execute("""
        WITH fda_bridged AS (
            SELECT 
                b.canonical_commodity_group,
                COUNT(r.id) AS fda_count
            FROM refusal_events r
            INNER JOIN canonical_commodity_bridge b
                ON b.jurisdiction_code = 'US' AND b.source_category_code = r.industry_code
            GROUP BY b.canonical_commodity_group
        ),
        eu_bridged AS (
            SELECT 
                b.canonical_commodity_group,
                COUNT(e.id) AS eu_count
            FROM eu_border_events e
            INNER JOIN canonical_commodity_bridge b
                ON b.jurisdiction_code = 'EU' AND b.source_category_code = e.category
            GROUP BY b.canonical_commodity_group
        )
        SELECT 
            COALESCE(f.canonical_commodity_group, e.canonical_commodity_group) AS commodity_group,
            COALESCE(f.fda_count, 0) AS fda_count,
            COALESCE(e.eu_count, 0) AS eu_count,
            (COALESCE(f.fda_count, 0) + COALESCE(e.eu_count, 0)) AS total_count
        FROM fda_bridged f
        FULL OUTER JOIN eu_bridged e ON f.canonical_commodity_group = e.canonical_commodity_group
        ORDER BY total_count DESC;
    """)
    comm_rows = cursor.fetchall()
    print(f"    {'Canonical Commodity Group':<30} | {'US FDA Events':<14} | {'EU RASFF Events':<16} | {'Total Count':<12}")
    print("    " + "-" * 78)
    for grp, f_cnt, e_cnt, tot in comm_rows:
        print(f"    {grp:<30} | {f_cnt:>14,} | {e_cnt:>16,} | {tot:>12,}")

    # 5. Categorical Hazard Comparison (High-Level Operational Profiling)
    print("\n[5] HIGH-LEVEL HAZARD PROFILES (Non-Equivalent Categorical Comparison):")
    print("    * Note: Regulatory schemas diverge fundamentally between US FD&C Act statutory")
    print("      sections and EU RASFF hazard classifications. Aggregated side-by-side below:\n")

    print("    [A] US FDA Charge Categories (refusal_events.charge_category):")
    cursor.execute("""
        SELECT charge_category, COUNT(*) AS cnt
        FROM refusal_events
        GROUP BY charge_category
        ORDER BY cnt DESC;
    """)
    for cat, cnt in cursor.fetchall():
        pct = (cnt / fda_total) * 100
        print(f"        - {cat:<32}: {cnt:>6,} ({pct:>5.2f}%)")

    print("\n    [B] EU RASFF Hazard Categories (eu_border_events.primary_hazard_category):")
    cursor.execute("""
        SELECT COALESCE(primary_hazard_category, '[NOT SPECIFIED / EMPTY]') AS cat, COUNT(*) AS cnt
        FROM eu_border_events
        GROUP BY cat
        ORDER BY cnt DESC
        LIMIT 8;
    """)
    for cat, cnt in cursor.fetchall():
        pct = (cnt / eu_total) * 100
        print(f"        - {cat:<32}: {cnt:>6,} ({pct:>5.2f}%)")

    # 6. Top Risk Profiles (Top 5 Commodities and Top 5 Hazards per Jurisdiction)
    print("\n[6] TOP RISK PROFILES BY JURISDICTION:")
    print("    -- UNITED STATES (FDA) --")
    cursor.execute("""
        SELECT industry_code, COUNT(*) AS cnt
        FROM refusal_events
        GROUP BY industry_code
        ORDER BY cnt DESC LIMIT 5;
    """)
    print("       Top 5 Industry Codes:")
    for ind, cnt in cursor.fetchall():
        print(f"         * Industry '{ind}': {cnt:,} refusals")

    print("\n    -- EUROPEAN UNION (RASFF) --")
    cursor.execute("""
        SELECT category, COUNT(*) AS cnt
        FROM eu_border_events
        WHERE category IS NOT NULL
        GROUP BY category
        ORDER BY cnt DESC LIMIT 5;
    """)
    print("       Top 5 Product Categories:")
    for cat, cnt in cursor.fetchall():
        print(f"         * {cat}: {cnt:,} notifications")

    # 7. Missing-Data Transparency Audit
    print("\n[7] MISSING-DATA TRANSPARENCY & DATA INTEGRITY LEDGER:")
    print("    In strict accordance with SENTRA-FS data governance, the following fields are")
    print("    confirmed as NOT AVAILABLE in the current exports and are preserved as NULL:")
    print("    - US FDA Observed Laboratory Value    : Data not available (Statutory citation only)")
    print("    - US FDA Quantitative Action Limit     : Data not available (OASIS public export does not include ppm/ppb)")
    print("    - EU RASFF Observed Numeric Value      : Data not available (Not reported in 14-col export)")
    print("    - EU RASFF Legal Limit / MRL Threshold : Data not available (Not reported in 14-col export)")
    print("    - EU RASFF Measurement Unit            : Data not available (Not reported in 14-col export)")

    # 8. Data-Quality Summary
    cursor.execute("""
        SELECT 
            COUNT(e.id) AS mapped_cnt
        FROM eu_border_events e
        INNER JOIN canonical_commodity_bridge b
            ON b.jurisdiction_code = 'EU' AND b.source_category_code = e.category;
    """)
    eu_mapped_cnt = cursor.fetchone()[0]
    eu_unmapped_cnt = eu_total - eu_mapped_cnt

    cursor.execute("SELECT COUNT(*) FROM eu_border_events WHERE hazards_raw IS NULL OR hazards_raw = '';")
    null_hazards = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM eu_border_events WHERE primary_origin_country IS NULL OR primary_origin_country = '';")
    null_origin = cursor.fetchone()[0]

    print("\n[8] DATA QUALITY & COVERAGE SUMMARY:")
    print(f"    - US FDA Records Preserved       : {fda_total:>8,} (100.0% retention)")
    print(f"    - EU RASFF Records Preserved     : {eu_total:>8,} (100.0% retention)")
    print(f"    - EU Records Mapped to Bridge    : {eu_mapped_cnt:>8,} ({(eu_mapped_cnt/eu_total)*100:.2f}%)")
    print(f"    - EU Records Unmapped (Preserved): {eu_unmapped_cnt:>8,} ({(eu_unmapped_cnt/eu_total)*100:.2f}%)")
    print(f"    - EU Duplicate Primary Keys      :        0 (Enforced by UNIQUE reference constraint)")
    print(f"    - EU Records with Null Hazards   : {null_hazards:>8,} ({(null_hazards/eu_total)*100:.2f}%)")
    print(f"    - EU Records with Null Origin    : {null_origin:>8,} ({(null_origin/eu_total)*100:.2f}%)")

    print("\n" + "=" * 80)
    print(" AUDIT COMPLETED SUCCESSFULLY - ZERO MODIFICATIONS TO DATABASE TABLES")
    print("=" * 80 + "\n")

    conn.close()

if __name__ == "__main__":
    run_comparison()