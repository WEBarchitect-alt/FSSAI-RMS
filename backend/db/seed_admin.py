import os
import sys
import sqlite3
import getpass
from datetime import datetime, timezone
import bcrypt

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DB_PATH = os.path.join(BASE_DIR, "backend", "db", "sentra_fs.db")

def hash_password(plain_pwd: str) -> str:
    salt = bcrypt.gensalt(rounds=12)
    return bcrypt.hashpw(plain_pwd.encode("utf-8"), salt).decode("utf-8")

def main():
    if not os.path.exists(DB_PATH):
        print(f"FATAL ERROR: Target database not found at {DB_PATH}")
        sys.exit(1)

    print("=" * 60)
    print(" SENTRA-FS INITIAL ADMINISTRATOR SEED UTILITY")
    print("=" * 60)

    username = input("Enter admin username: ").strip().lower()
    if not username:
        print("Error: Username cannot be empty.")
        sys.exit(1)

    display_name = input("Enter display name (e.g., Lead Administrator): ").strip()
    if not display_name:
        print("Error: Display name cannot be empty.")
        sys.exit(1)

    pwd = getpass.getpass("Enter secure password: ")
    if len(pwd) < 8:
        print("Error: Password must be at least 8 characters long.")
        sys.exit(1)

    pwd_confirm = getpass.getpass("Confirm secure password: ")
    if pwd != pwd_confirm:
        print("Error: Passwords do not match.")
        sys.exit(1)

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("PRAGMA foreign_keys = ON;")

    # Refuse to overwrite an existing user
    cursor.execute("SELECT id, username, role FROM users WHERE username = ?;", (username,))
    existing = cursor.fetchone()
    if existing:
        print(f"\n[!] Error: User '{username}' already exists (User ID: {existing[0]}, Role: {existing[2]}).")
        print("Accidental overwrite is strictly prohibited.")
        conn.close()
        sys.exit(1)

    pwd_hash = hash_password(pwd)
    now_iso = datetime.now(timezone.utc).isoformat()

    cursor.execute("""
        INSERT INTO users (username, display_name, password_hash, role, is_active, created_at)
        VALUES (?, ?, ?, 'admin', 1, ?);
    """, (username, display_name, pwd_hash, now_iso))

    conn.commit()
    conn.close()

    print(f"\n[+] Administrator account '{username}' successfully created.")
    print("=" * 60)

if __name__ == "__main__":
    main()