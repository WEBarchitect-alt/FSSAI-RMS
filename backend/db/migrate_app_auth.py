import os
import sys
import sqlite3

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DB_PATH = os.path.join(BASE_DIR, "backend", "db", "sentra_fs.db")

EXPECTED_DATA_COUNTS = {
    "refusal_events": 62937,
    "eu_border_events": 30000,
    "india_lab_rejections": 135
}

def migrate():
    if not os.path.exists(DB_PATH):
        print(f"FATAL ERROR: Target database not found at {DB_PATH}")
        sys.exit(1)

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("PRAGMA foreign_keys = ON;")

    print(f"[*] Connecting to: {DB_PATH}")
    print("[*] Applying non-destructive authentication schema migration...")

    # 1. users table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            display_name TEXT NOT NULL,
            password_hash TEXT NOT NULL,
            role TEXT NOT NULL DEFAULT 'analyst',
            is_active INTEGER NOT NULL DEFAULT 1,
            created_at TEXT NOT NULL,
            last_login_at TEXT
        );
    """)

    # 2. user_activity_log table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS user_activity_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            username_attempted TEXT NOT NULL,
            event_type TEXT NOT NULL,
            timestamp TEXT NOT NULL,
            ip_address TEXT,
            user_agent TEXT,
            FOREIGN KEY (user_id) REFERENCES users(id)
        );
    """)

    # 3. Operational Indexes
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_activity_user_id ON user_activity_log(user_id);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_activity_timestamp ON user_activity_log(timestamp);")

    conn.commit()

    # Verify foreign keys integrity
    cursor.execute("PRAGMA foreign_key_check;")
    fk_violations = cursor.fetchall()
    if fk_violations:
        print(f"[!] Foreign key check failed: {fk_violations}")
        sys.exit(1)

    print("[+] Foreign key check: 0 violations.")

    # Strict assertion of pre-existing enforcement datasets
    print("[*] Auditing pre-existing data preservation:")
    all_passed = True
    for tbl, expected_cnt in EXPECTED_DATA_COUNTS.items():
        cursor.execute(f"SELECT COUNT(*) FROM {tbl};")
        cnt = cursor.fetchone()[0]
        status = "MATCH" if cnt == expected_cnt else "MISMATCH"
        if cnt != expected_cnt:
            all_passed = False
        print(f"    - {tbl:<22}: {cnt:,} rows (Expected: {expected_cnt:,}) [{status}]")

    # Confirm India total rejection_count sum using exact schema column
    cursor.execute("SELECT SUM(rejection_count) FROM india_lab_rejections;")
    india_sum = cursor.fetchone()[0]
    status_sum = "MATCH" if india_sum == 1138 else "MISMATCH"
    if india_sum != 1138:
        all_passed = False
    print(f"    - India rejection_count sum : {india_sum:,} (Expected: 1,138) [{status_sum}]")

    conn.close()

    if not all_passed:
        print("\n[!] FATAL: Pre-existing database record count mismatch after migration!")
        sys.exit(1)

    print("\n[+] Migration completed successfully. Auth & Activity tables ready.")

if __name__ == "__main__":
    migrate()