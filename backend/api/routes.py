from typing import Optional, List
import math
from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel

from backend.api.dependencies import get_db, require_admin

admin_router = APIRouter(prefix="/api/admin", tags=["Administration"])
india_router = APIRouter(prefix="/api/india/rejections", tags=["India FIRA Intelligence"])

# --- Admin Models ---

class AdminUserResponse(BaseModel):
    id: int
    username: str
    display_name: str
    role: str
    is_active: bool
    created_at: str
    last_login_at: Optional[str] = None

class ActivityLogResponse(BaseModel):
    id: int
    user_id: Optional[int] = None
    username: Optional[str] = None
    display_name: Optional[str] = None
    username_attempted: str
    event_type: str
    timestamp: str
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None

# --- India FIRA Models ---

class IndiaRejectionItem(BaseModel):
    id: int
    financial_year: Optional[str] = None
    country_of_origin: Optional[str] = None
    rejection_count: Optional[int] = None
    rejected_items: Optional[str] = None
    source_file: Optional[str] = None
    stage: Optional[str] = None

class IndiaRejectionsPaginationResponse(BaseModel):
    total: int
    page: int
    page_size: int
    total_pages: int
    items: List[IndiaRejectionItem]

# --- Admin Endpoints ---

@admin_router.get("/users", response_model=List[AdminUserResponse])
def get_admin_users(
    conn = Depends(get_db),
    _ = Depends(require_admin)
):
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, username, display_name, role, is_active, created_at, last_login_at
        FROM users
        ORDER BY id ASC;
    """)
    rows = cursor.fetchall()
    return [
        AdminUserResponse(
            id=r["id"],
            username=r["username"],
            display_name=r["display_name"],
            role=r["role"],
            is_active=bool(r["is_active"]),
            created_at=r["created_at"],
            last_login_at=r["last_login_at"]
        )
        for r in rows
    ]

@admin_router.get("/activity", response_model=List[ActivityLogResponse])
def get_admin_activity(
    limit: int = Query(50, ge=1, le=100),
    conn = Depends(get_db),
    _ = Depends(require_admin)
):
    cursor = conn.cursor()
    cursor.execute("""
        SELECT 
            l.id, l.user_id, u.username, u.display_name,
            l.username_attempted, l.event_type, l.timestamp,
            l.ip_address, l.user_agent
        FROM user_activity_log l
        LEFT JOIN users u ON l.user_id = u.id
        ORDER BY l.id DESC
        LIMIT ?;
    """, (limit,))
    rows = cursor.fetchall()
    return [
        ActivityLogResponse(
            id=r["id"],
            user_id=r["user_id"],
            username=r["username"],
            display_name=r["display_name"],
            username_attempted=r["username_attempted"],
            event_type=r["event_type"],
            timestamp=r["timestamp"],
            ip_address=r["ip_address"],
            user_agent=r["user_agent"]
        )
        for r in rows
    ]

# --- India FIRA Analytics Endpoints ---

@india_router.get("/summary")
def get_india_rejections_summary(conn = Depends(get_db)):
    cursor = conn.cursor()

    cursor.execute("""
        SELECT 
            COUNT(*) as total_rows,
            COALESCE(SUM(rejection_count), 0) as total_rejection_count,
            COUNT(DISTINCT country_of_origin) as total_countries,
            COUNT(DISTINCT financial_year) as total_years
        FROM india_lab_rejections;
    """)
    summary_row = cursor.fetchone()

    cursor.execute("SELECT DISTINCT financial_year FROM india_lab_rejections ORDER BY financial_year ASC;")
    financial_years = [r["financial_year"] for r in cursor.fetchall()]

    cursor.execute("""
        SELECT country_of_origin, SUM(rejection_count) as total_rejections
        FROM india_lab_rejections
        GROUP BY country_of_origin
        ORDER BY total_rejections DESC
        LIMIT 5;
    """)
    top_countries = [
        {"country": r["country_of_origin"], "total_rejections": r["total_rejections"]}
        for r in cursor.fetchall()
    ]

    return {
        "jurisdiction": "India",
        "regulator": "FSSAI / FIRA",
        "stage": "Laboratory Testing Stage",
        "total_rows": summary_row["total_rows"],
        "total_rejection_count": summary_row["total_rejection_count"],
        "total_countries": summary_row["total_countries"],
        "financial_years": financial_years,
        "top_countries": top_countries
    }

@india_router.get("/by-year")
def get_india_rejections_by_year(conn = Depends(get_db)):
    cursor = conn.cursor()
    cursor.execute("""
        SELECT 
            financial_year,
            SUM(rejection_count) as total_rejections,
            COUNT(DISTINCT country_of_origin) as countries_affected,
            COUNT(*) as record_count
        FROM india_lab_rejections
        GROUP BY financial_year
        ORDER BY financial_year ASC;
    """)
    rows = cursor.fetchall()
    return [
        {
            "financial_year": r["financial_year"],
            "total_rejections": r["total_rejections"],
            "countries_affected": r["countries_affected"],
            "record_count": r["record_count"]
        }
        for r in rows
    ]

@india_router.get("/by-country")
def get_india_rejections_by_country(
    limit: int = Query(50, ge=1, le=150),
    conn = Depends(get_db)
):
    cursor = conn.cursor()
    cursor.execute("""
        SELECT 
            country_of_origin,
            SUM(rejection_count) as total_rejections,
            COUNT(DISTINCT financial_year) as years_active,
            GROUP_CONCAT(DISTINCT financial_year) as active_financial_years
        FROM india_lab_rejections
        GROUP BY country_of_origin
        ORDER BY total_rejections DESC
        LIMIT ?;
    """, (limit,))
    rows = cursor.fetchall()
    return [
        {
            "country_of_origin": r["country_of_origin"],
            "total_rejections": r["total_rejections"],
            "years_active": r["years_active"],
            "active_financial_years": r["active_financial_years"].split(",") if r["active_financial_years"] else []
        }
        for r in rows
    ]

@india_router.get("/records", response_model=IndiaRejectionsPaginationResponse)
def get_india_rejection_records(
    page: int = Query(1, ge=1),
    page_size: int = Query(25, ge=10, le=100),
    country: Optional[str] = Query(None),
    financial_year: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    conn = Depends(get_db)
):
    cursor = conn.cursor()
    where_clauses = []
    params = []

    if country:
        where_clauses.append("UPPER(country_of_origin) = UPPER(?)")
        params.append(country.strip())

    if financial_year:
        where_clauses.append("financial_year = ?")
        params.append(financial_year.strip())

    if search and search.strip():
        search_val = f"%{search.strip()}%"
        where_clauses.append("(country_of_origin LIKE ? OR rejected_items LIKE ? OR source_file LIKE ?)")
        params.extend([search_val, search_val, search_val])

    where_sql = ("WHERE " + " AND ".join(where_clauses)) if where_clauses else ""

    cursor.execute(f"SELECT COUNT(*) AS total FROM india_lab_rejections {where_sql};", params)
    total = cursor.fetchone()["total"]

    offset = (page - 1) * page_size
    total_pages = math.ceil(total / page_size) if total > 0 else 0

    cursor.execute(f"""
        SELECT id, financial_year, country_of_origin, rejection_count, rejected_items, source_file, stage
        FROM india_lab_rejections
        {where_sql}
        ORDER BY id ASC
        LIMIT ? OFFSET ?;
    """, params + [page_size, offset])

    rows = cursor.fetchall()
    items = [IndiaRejectionItem(**dict(r)) for r in rows]

    return IndiaRejectionsPaginationResponse(
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
        items=items
    )