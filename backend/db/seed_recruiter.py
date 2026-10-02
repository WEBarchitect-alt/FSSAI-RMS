import os
import sqlite3
from datetime import datetime, timezone
import bcrypt

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DB_PATH = os.path.join(BASE_DIR, "backend", "db", "sentra_fs.db")

def seed_recruiter():
    if not os.path.exists(DB_PATH):
        raise FileNotFoundError(f"Database not found at {DB_PATH}")

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("SELECT id, username, role, is_active FROM users WHERE LOWER(username) = 'recruiter';")
    existing = cursor.fetchone()

    salt = bcrypt.gensalt(rounds=12)
    pw_hash = bcrypt.hashpw(b"12345678", salt).decode("utf-8")
    now_iso = datetime.now(timezone.utc).isoformat()

    if existing:
        # Update to guarantee known password while preserving user ID
        cursor.execute("""
            UPDATE users
            SET password_hash = ?, role = 'user', is_active = 1
            WHERE id = ?;
        """, (pw_hash, existing[0]))
        print(f"[OK] Recruiter account (ID: {existing[0]}) verified and updated with standard user credentials.")
    else:
        cursor.execute("""
            INSERT INTO users (username, display_name, password_hash, role, is_active, created_at)
            VALUES (?, ?, ?, 'user', 1, ?);
        """, ("recruiter", "Recruiter Reviewer", pw_hash, now_iso))
        print("[OK] Recruiter demo user successfully created with role='user'.")

    conn.commit()
    conn.close()

if __name__ == "__main__":
    seed_recruiter()