import csv
import os
import sqlite3

DB_PATH = os.path.join("backend", "db", "sentra_fs.db")
CSV_PATH = os.path.join("data", "curated", "india_lab_rejection_aggregates.csv")

def main():
    print("[*] Loading India FIRA laboratory rejection data...")

    if not os.path.exists(CSV_PATH):
        raise FileNotFoundError(f"CSV not found: {CSV_PATH}")

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS india_lab_rejections (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            financial_year TEXT NOT NULL,
            country_of_origin TEXT NOT NULL,
            rejection_count INTEGER NOT NULL,
            rejected_items TEXT,
            source_file TEXT NOT NULL,
            stage TEXT NOT NULL
        )
    """)

    cur.execute("DELETE FROM india_lab_rejections")

    with open(CSV_PATH, "r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)

        rows = []
        for row in reader:
            rows.append((
                row["financial_year"],
                row["country_of_origin"],
                int(row["rejection_count"]),
                row["rejected_items"],
                row["source_file"],
                row["stage"]
            ))

    cur.executemany("""
        INSERT INTO india_lab_rejections (
            financial_year,
            country_of_origin,
            rejection_count,
            rejected_items,
            source_file,
            stage
        )
        VALUES (?, ?, ?, ?, ?, ?)
    """, rows)

    conn.commit()

    count = cur.execute(
        "SELECT COUNT(*) FROM india_lab_rejections"
    ).fetchone()[0]

    total = cur.execute(
        "SELECT COALESCE(SUM(rejection_count), 0) FROM india_lab_rejections"
    ).fetchone()[0]

    years = cur.execute("""
        SELECT financial_year
        FROM india_lab_rejections
        GROUP BY financial_year
        ORDER BY financial_year
    """).fetchall()

    print("=" * 70)
    print(" INDIA FIRA SQLITE INGESTION")
    print("=" * 70)
    print(f"Rows inserted       : {count}")
    print(f"Total rejections    : {total}")
    print(f"Financial years     : {[x[0] for x in years]}")
    print(f"Rows dropped        : 0")
    print("=" * 70)

    conn.close()

if __name__ == "__main__":
    main()
