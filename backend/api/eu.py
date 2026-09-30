from typing import Optional, List
import math
import sqlite3

from fastapi import APIRouter, Depends, Query, HTTPException
from pydantic import BaseModel

from backend.api.dependencies import get_db, get_current_user

router = APIRouter(
    prefix="/api/eu",
    tags=["European Union RASFF Border Events"]
)

class EuSummaryResponse(BaseModel):
    total_events: int
    unique_origins: int
    unique_notifying_countries: int
    earliest_event_date: Optional[str] = None
    latest_event_date: Optional[str] = None
    serious_events: int
    events_with_hazards: int

class EuEventItem(BaseModel):
    id: int
    reference: Optional[str] = None
    category: Optional[str] = None
    type: Optional[str] = None
    subject: Optional[str] = None
    event_date: Optional[str] = None
    event_year: Optional[int] = None
    event_timestamp: Optional[str] = None
    notifying_country: Optional[str] = None
    classification: Optional[str] = None
    risk_decision: Optional[str] = None
    distribution: Optional[str] = None
    for_attention: Optional[str] = None
    for_follow_up: Optional[str] = None
    operator: Optional[str] = None
    origin: Optional[str] = None
    primary_origin_country: Optional[str] = None
    hazards_raw: Optional[str] = None
    primary_hazard_substance: Optional[str] = None
    primary_hazard_category: Optional[str] = None
    has_multiple_hazards: Optional[int] = None
    food_class_scope: Optional[str] = None

class EuPaginationResponse(BaseModel):
    total: int
    page: int
    page_size: int
    total_pages: int
    items: List[EuEventItem]

@router.get("/summary", response_model=EuSummaryResponse)
def get_eu_summary(
    conn: sqlite3.Connection = Depends(get_db),
    _current_user: dict = Depends(get_current_user)
):
    cursor = conn.cursor()
    cursor.execute("""
        SELECT
            COUNT(*) AS total_events,
            COUNT(DISTINCT origin) AS unique_origins,
            COUNT(DISTINCT notifying_country) AS unique_notifying_countries,
            MIN(event_date) AS earliest_event_date,
            MAX(event_date) AS latest_event_date,
            SUM(CASE WHEN LOWER(risk_decision) LIKE '%serious%' OR LOWER(classification) LIKE '%alert%' THEN 1 ELSE 0 END) AS serious_events,
            SUM(CASE WHEN hazards_raw IS NOT NULL AND TRIM(hazards_raw) != '' THEN 1 ELSE 0 END) AS events_with_hazards
        FROM eu_border_events;
    """)
    row = cursor.fetchone()

    return EuSummaryResponse(
        total_events=row["total_events"] or 0,
        unique_origins=row["unique_origins"] or 0,
        unique_notifying_countries=row["unique_notifying_countries"] or 0,
        earliest_event_date=row["earliest_event_date"],
        latest_event_date=row["latest_event_date"],
        serious_events=row["serious_events"] or 0,
        events_with_hazards=row["events_with_hazards"] or 0
    )

@router.get("/events", response_model=EuPaginationResponse)
def get_eu_events(
    page: int = Query(1, ge=1),
    page_size: int = Query(25, ge=10, le=100),
    search: Optional[str] = Query(None),
    origin: Optional[str] = Query(None),
    notifying_country: Optional[str] = Query(None),
    classification: Optional[str] = Query(None),
    risk_decision: Optional[str] = Query(None),
    year: Optional[int] = Query(None),
    conn: sqlite3.Connection = Depends(get_db),
    _current_user: dict = Depends(get_current_user)
):
    cursor = conn.cursor()
    where_clauses = []
    params = []

    if origin:
        where_clauses.append("(UPPER(origin) = UPPER(?) OR UPPER(primary_origin_country) = UPPER(?))")
        params.extend([origin.strip(), origin.strip()])

    if notifying_country:
        where_clauses.append("UPPER(notifying_country) = UPPER(?)")
        params.append(notifying_country.strip())

    if classification:
        where_clauses.append("classification = ?")
        params.append(classification.strip())

    if risk_decision:
        where_clauses.append("risk_decision = ?")
        params.append(risk_decision.strip())

    if year:
        where_clauses.append("event_year = ?")
        params.append(year)

    if search and search.strip():
        search_val = f"%{search.strip()}%"
        where_clauses.append("""
            (
                reference LIKE ?
                OR subject LIKE ?
                OR origin LIKE ?
                OR primary_origin_country LIKE ?
                OR notifying_country LIKE ?
                OR hazards_raw LIKE ?
                OR primary_hazard_substance LIKE ?
                OR primary_hazard_category LIKE ?
            )
        """)
        params.extend([search_val] * 8)

    where_sql = ("WHERE " + " AND ".join(where_clauses)) if where_clauses else ""

    cursor.execute(f"SELECT COUNT(*) AS total FROM eu_border_events {where_sql};", params)
    total = cursor.fetchone()["total"]

    offset = (page - 1) * page_size
    total_pages = math.ceil(total / page_size) if total > 0 else 0

    cursor.execute(f"""
        SELECT
            id, reference, category, type, subject, event_date, event_year,
            event_timestamp, notifying_country, classification, risk_decision,
            distribution, for_attention, for_follow_up, operator, origin,
            primary_origin_country, hazards_raw, primary_hazard_substance,
            primary_hazard_category, has_multiple_hazards, food_class_scope
        FROM eu_border_events
        {where_sql}
        ORDER BY event_date DESC, id DESC
        LIMIT ? OFFSET ?;
    """, params + [page_size, offset])

    rows = cursor.fetchall()
    items = [EuEventItem(**dict(r)) for r in rows]

    return EuPaginationResponse(
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
        items=items
    )

@router.get("/events/{id}", response_model=EuEventItem)
def get_eu_event_by_id(
    id: int,
    conn: sqlite3.Connection = Depends(get_db),
    _current_user: dict = Depends(get_current_user)
):
    cursor = conn.cursor()
    cursor.execute("""
        SELECT
            id, reference, category, type, subject, event_date, event_year,
            event_timestamp, notifying_country, classification, risk_decision,
            distribution, for_attention, for_follow_up, operator, origin,
            primary_origin_country, hazards_raw, primary_hazard_substance,
            primary_hazard_category, has_multiple_hazards, food_class_scope
        FROM eu_border_events
        WHERE id = ?;
    """, (id,))
    row = cursor.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="EU border event record not found")
    return EuEventItem(**dict(row)) 