import os
import sqlite3
from typing import Dict, Any, Generator
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import jwt
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DB_PATH = os.path.join(BASE_DIR, "backend", "db", "sentra_fs.db")

JWT_SECRET = os.getenv("SENTRA_JWT_SECRET")
if not JWT_SECRET:
    raise RuntimeError(
        "CRITICAL: SENTRA_JWT_SECRET is not set in environment or .env file. "
        "Set SENTRA_JWT_SECRET before running the application."
    )

JWT_ALGORITHM = os.getenv("SENTRA_JWT_ALGORITHM", "HS256")
JWT_EXPIRE_HOURS = int(os.getenv("SENTRA_JWT_EXPIRE_HOURS", "8"))

security = HTTPBearer()

def get_db() -> Generator[sqlite3.Connection, None, None]:
    """Provides a SQLite connection with dict-like row factories and foreign keys enabled."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    try:
        yield conn
    finally:
        conn.close()

def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    conn: sqlite3.Connection = Depends(get_db)
) -> Dict[str, Any]:
    """Validates the Bearer JWT and retrieves the active user record."""
    token = credentials.credentials
    auth_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials or token expired.",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise auth_exception
    except jwt.PyJWTError:
        raise auth_exception

    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, username, display_name, role, is_active, created_at, last_login_at
        FROM users
        WHERE username = ?;
    """, (username,))
    user = cursor.fetchone()

    if user is None or user["is_active"] != 1:
        raise auth_exception

    return dict(user)

def require_admin(current_user: Dict[str, Any] = Depends(get_current_user)) -> Dict[str, Any]:
    """Ensures the authenticated user holds administrative privileges."""
    if current_user.get("role") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access forbidden: administrative role required."
        )
    return current_user