import os
import sqlite3
import json
import uuid
import urllib.request
import urllib.error
from datetime import datetime, timezone, timedelta
from typing import Optional, Dict, Any

from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
import jwt
import bcrypt
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DB_PATH = os.path.join(BASE_DIR, "backend", "db", "sentra_fs.db")

JWT_SECRET = os.getenv("SENTRA_JWT_SECRET") or os.getenv("JWT_SECRET_KEY")
if not JWT_SECRET:
    raise RuntimeError(
        "CRITICAL: SENTRA_JWT_SECRET environment variable is not set. "
        "Create a .env file with SENTRA_JWT_SECRET defined."
    )

JWT_ALGORITHM = os.getenv("SENTRA_JWT_ALGORITHM", os.getenv("JWT_ALGORITHM", "HS256"))
JWT_EXPIRE_HOURS = int(os.getenv("SENTRA_JWT_EXPIRE_HOURS", "8"))
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID", "").strip()

router = APIRouter(prefix="/api/auth", tags=["Authentication"])
security = HTTPBearer()

# --- Pydantic Schemas ---

class LoginRequest(BaseModel):
    username: str
    password: str

class RegisterRequest(BaseModel):
    full_name: str
    email: str
    password: str
    confirm_password: str

class GoogleAuthRequest(BaseModel):
    id_token: str

class UserResponse(BaseModel):
    id: int
    username: str
    display_name: str
    role: str
    last_login_at: Optional[str] = None

class TokenResponse(BaseModel):
    access_token: str
    token_type: str
    user: UserResponse

# --- Database Dependency ---

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    try:
        yield conn
    finally:
        conn.close()

# --- Security Helpers ---

def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        return bcrypt.checkpw(
            plain_password.encode("utf-8"),
            hashed_password.encode("utf-8")
        )
    except Exception:
        return False

def hash_password(password: str) -> str:
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")

def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(hours=JWT_EXPIRE_HOURS)
    )
    to_encode.update({"exp": expire, "iat": datetime.now(timezone.utc)})
    return jwt.encode(to_encode, JWT_SECRET, algorithm=JWT_ALGORITHM)

def record_activity_log(
    conn: sqlite3.Connection,
    user_id: Optional[int],
    username_attempted: str,
    event_type: str,
    request: Request
):
    ip_addr = request.client.host if request.client else "unknown"
    user_agent = request.headers.get("user-agent", "unknown")
    now_iso = datetime.now(timezone.utc).isoformat()

    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO user_activity_log (user_id, username_attempted, event_type, timestamp, ip_address, user_agent)
        VALUES (?, ?, ?, ?, ?, ?);
    """, (user_id, username_attempted, event_type, now_iso, ip_addr, user_agent))
    conn.commit()

# --- Current User Dependency ---

def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    conn: sqlite3.Connection = Depends(get_db)
) -> Dict[str, Any]:
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

# --- Routes ---

@router.post("/login", response_model=TokenResponse)
def login(
    payload: LoginRequest,
    request: Request,
    conn: sqlite3.Connection = Depends(get_db)
):
    submitted_username = payload.username.strip().lower()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, username, display_name, password_hash, role, is_active, last_login_at
        FROM users
        WHERE LOWER(username) = ?;
    """, (submitted_username,))
    user = cursor.fetchone()

    generic_error = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid username or password.",
        headers={"WWW-Authenticate": "Bearer"},
    )

    if not user or user["is_active"] != 1:
        record_activity_log(conn, None, submitted_username, "LOGIN_FAILED", request)
        raise generic_error

    if not verify_password(payload.password, user["password_hash"]):
        record_activity_log(conn, user["id"], submitted_username, "LOGIN_FAILED", request)
        raise generic_error

    now_iso = datetime.now(timezone.utc).isoformat()
    cursor.execute("UPDATE users SET last_login_at = ? WHERE id = ?;", (now_iso, user["id"]))
    record_activity_log(conn, user["id"], submitted_username, "LOGIN_SUCCESS", request)
    conn.commit()

    token = create_access_token(data={"sub": user["username"], "role": user["role"]})

    return TokenResponse(
        access_token=token,
        token_type="bearer",
        user=UserResponse(
            id=user["id"],
            username=user["username"],
            display_name=user["display_name"],
            role=user["role"],
            last_login_at=now_iso
        )
    )

@router.post("/register")
def register(
    payload: RegisterRequest,
    conn: sqlite3.Connection = Depends(get_db)
):
    if payload.password != payload.confirm_password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Passwords do not match."
        )

    if len(payload.password) < 6:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password must be at least 6 characters long."
        )

    submitted_email = payload.email.strip().lower()
    cursor = conn.cursor()

    cursor.execute("SELECT id FROM users WHERE LOWER(username) = ?;", (submitted_email,))
    existing_user = cursor.fetchone()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="An account with this email address already exists."
        )

    pw_hash = hash_password(payload.password)
    now_iso = datetime.now(timezone.utc).isoformat()

    cursor.execute("""
        INSERT INTO users (username, display_name, password_hash, role, is_active, created_at)
        VALUES (?, ?, ?, 'user', 1, ?);
    """, (submitted_email, payload.full_name.strip(), pw_hash, now_iso))
    conn.commit()

    return {"status": "success", "message": "Account created successfully."}

@router.post("/google", response_model=TokenResponse)
def google_auth(
    payload: GoogleAuthRequest,
    request: Request,
    conn: sqlite3.Connection = Depends(get_db)
):
    # Verify the Google Token via Google's tokeninfo endpoint
    token_url = f"https://oauth2.googleapis.com/tokeninfo?id_token={payload.id_token.strip()}"
    try:
        req = urllib.request.Request(token_url, headers={"User-Agent": "SENTRA-FS-Backend"})
        with urllib.request.urlopen(req, timeout=10) as response:
            if response.status != 200:
                raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid Google token.")
            google_data = json.loads(response.read().decode("utf-8"))
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not verify Google authentication token."
        )

    # Optional Client ID audience verification if GOOGLE_CLIENT_ID is set
    if GOOGLE_CLIENT_ID:
        aud = google_data.get("aud")
        if aud != GOOGLE_CLIENT_ID:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Google token was not issued for this application."
            )

    email = google_data.get("email", "").strip().lower()
    name = google_data.get("name", "").strip() or email.split("@")[0]
    email_verified = google_data.get("email_verified")

    if not email or str(email_verified).lower() not in ("true", "1"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Google account email is not verified."
        )

    cursor = conn.cursor()
    cursor.execute("SELECT id, username, display_name, role, is_active FROM users WHERE LOWER(username) = ?;", (email,))
    user = cursor.fetchone()
    now_iso = datetime.now(timezone.utc).isoformat()

    if user:
        if user["is_active"] != 1:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account is disabled.")
        user_id = user["id"]
        role = user["role"]
        display_name = user["display_name"]
        cursor.execute("UPDATE users SET last_login_at = ? WHERE id = ?;", (now_iso, user_id))
    else:
        # Create user with a cryptographically unusable random bcrypt hash
        dummy_secret = str(uuid.uuid4())
        pw_hash = hash_password(dummy_secret)
        cursor.execute("""
            INSERT INTO users (username, display_name, password_hash, role, is_active, created_at, last_login_at)
            VALUES (?, ?, ?, 'user', 1, ?, ?);
        """, (email, name, pw_hash, now_iso, now_iso))
        user_id = cursor.lastrowid
        role = "user"
        display_name = name

    record_activity_log(conn, user_id, email, "LOGIN_GOOGLE", request)
    conn.commit()

    token = create_access_token(data={"sub": email, "role": role})

    return TokenResponse(
        access_token=token,
        token_type="bearer",
        user=UserResponse(
            id=user_id,
            username=email,
            display_name=display_name,
            role=role,
            last_login_at=now_iso
        )
    )

@router.post("/logout")
def logout(
    request: Request,
    current_user: Dict[str, Any] = Depends(get_current_user),
    conn: sqlite3.Connection = Depends(get_db)
):
    record_activity_log(
        conn,
        current_user["id"],
        current_user["username"],
        "LOGOUT",
        request
    )
    return {"message": "Successfully logged out."}