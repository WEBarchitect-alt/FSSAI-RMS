from datetime import datetime, timezone, timedelta
from typing import Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status, Request
from pydantic import BaseModel
import bcrypt
import jwt

from backend.api.dependencies import (
    get_db,
    get_current_user,
    JWT_SECRET,
    JWT_ALGORITHM,
    JWT_EXPIRE_HOURS
)

router = APIRouter(prefix="/api/auth", tags=["Authentication"])

class LoginRequest(BaseModel):
    username: str
    password: str

class UserProfileResponse(BaseModel):
    id: int
    username: str
    display_name: str
    role: str
    is_active: bool
    created_at: str
    last_login_at: Optional[str] = None

class LoginSuccessResponse(BaseModel):
    access_token: str
    token_type: str
    user: UserProfileResponse

def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        return bcrypt.checkpw(
            plain_password.encode("utf-8"),
            hashed_password.encode("utf-8")
        )
    except Exception:
        return False

def record_activity_log(
    conn,
    user_id: Optional[int],
    username_attempted: str,
    event_type: str,
    request: Request
):
    ip_addr = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent")
    now_iso = datetime.now(timezone.utc).isoformat()

    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO user_activity_log (user_id, username_attempted, event_type, timestamp, ip_address, user_agent)
        VALUES (?, ?, ?, ?, ?, ?);
    """, (user_id, username_attempted, event_type, now_iso, ip_addr, user_agent))
    conn.commit()

@router.post("/login", response_model=LoginSuccessResponse)
def login(
    payload: LoginRequest,
    request: Request,
    conn = Depends(get_db)
):
    submitted_username = payload.username.strip().lower()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, username, display_name, password_hash, role, is_active, created_at, last_login_at
        FROM users
        WHERE username = ?;
    """, (submitted_username,))
    user = cursor.fetchone()

    generic_error = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid username or password.",
        headers={"WWW-Authenticate": "Bearer"},
    )

    # 1. User does not exist or is deactivated
    if not user or user["is_active"] != 1:
        record_activity_log(conn, None, submitted_username, "login_failed", request)
        raise generic_error

    # 2. Password mismatch
    if not verify_password(payload.password, user["password_hash"]):
        record_activity_log(conn, user["id"], submitted_username, "login_failed", request)
        raise generic_error

    # 3. Successful authentication
    now_iso = datetime.now(timezone.utc).isoformat()
    cursor.execute("UPDATE users SET last_login_at = ? WHERE id = ?;", (now_iso, user["id"]))
    record_activity_log(conn, user["id"], submitted_username, "login_success", request)
    conn.commit()

    # Generate JWT
    expire = datetime.now(timezone.utc) + timedelta(hours=JWT_EXPIRE_HOURS)
    token_payload = {
        "sub": user["username"],
        "uid": user["id"],
        "role": user["role"],
        "exp": expire,
        "iat": datetime.now(timezone.utc)
    }
    token = jwt.encode(token_payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

    return LoginSuccessResponse(
        access_token=token,
        token_type="bearer",
        user=UserProfileResponse(
            id=user["id"],
            username=user["username"],
            display_name=user["display_name"],
            role=user["role"],
            is_active=bool(user["is_active"]),
            created_at=user["created_at"],
            last_login_at=now_iso
        )
    )

@router.get("/me", response_model=UserProfileResponse)
def get_me(current_user: Dict[str, Any] = Depends(get_current_user)):
    return UserProfileResponse(
        id=current_user["id"],
        username=current_user["username"],
        display_name=current_user["display_name"],
        role=current_user["role"],
        is_active=bool(current_user["is_active"]),
        created_at=current_user["created_at"],
        last_login_at=current_user["last_login_at"]
    )

@router.post("/logout")
def logout(
    request: Request,
    current_user: Dict[str, Any] = Depends(get_current_user),
    conn = Depends(get_db)
):
    record_activity_log(
        conn,
        current_user["id"],
        current_user["username"],
        "logout",
        request
    )
    return {"status": "success", "message": "Session terminated successfully."}