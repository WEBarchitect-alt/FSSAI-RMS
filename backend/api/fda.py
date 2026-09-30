from typing import Optional, List
import math
import sqlite3

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel

from backend.api.dependencies import get_db, get_current_user


router = APIRouter(
    prefix="/api/fda",
    tags=["US FDA Refusals Investigation"]
)


# ============================================================
# RESPONSE MODELS
# ============================================================

class FdaRefusalItem(BaseModel):
    id: int
    refusal_id: Optional[str] = None
    entry_num: Optional[str] = None
    line_num: Optional[str] = None
    refusal_date: Optional[str] = None

    product_code: Optional[str] = None
    industry_code: Optional[str] = None
    food_class: Optional[str] = None
    product_desc: Optional[str] = None

    country_code: Optional[str] = None
    country_name: Optional[str] = None

    manufacturer_name: Optional[str] = None
    manufacturer_city: Optional[str] = None
    port_of_entry: Optional[str] = None

    primary_charge_code: Optional[str] = None
    primary_act_section: Optional[str] = None
    primary_charge_statement: Optional[str] = None

    charge_category: Optional[str] = None
    defect_standard_status: Optional[str] = None


class FdaPaginationResponse(BaseModel):
    total: int
    page: int
    page_size: int
    total_pages: int
    items: List[FdaRefusalItem]


class FdaFilterOptionsResponse(BaseModel):
    charge_categories: List[str]
    industry_codes: List[str]
    top_countries: List[str]


class FdaSummaryResponse(BaseModel):
    total_refusal_events: int
    unique_countries: int
    unique_industry_codes: int
    unique_charge_categories: int
    earliest_refusal_date: Optional[str] = None
    latest_refusal_date: Optional[str] = None


# ============================================================
# FILTER OPTIONS
# ============================================================

@router.get(
    "/filters",
    response_model=FdaFilterOptionsResponse
)
def get_fda_filter_options(
    conn: sqlite3.Connection = Depends(get_db),
    _current_user: dict = Depends(get_current_user)
):
    """
    Returns values used to populate FDA investigation filters.
    """

    cursor = conn.cursor()

    # --------------------------------------------------------
    # Charge categories
    # --------------------------------------------------------
    cursor.execute("""
        SELECT DISTINCT charge_category
        FROM refusal_events
        WHERE charge_category IS NOT NULL
          AND TRIM(charge_category) != ''
        ORDER BY charge_category ASC;
    """)

    charge_categories = [
        row["charge_category"]
        for row in cursor.fetchall()
    ]

    # --------------------------------------------------------
    # Industry codes
    # --------------------------------------------------------
    cursor.execute("""
        SELECT DISTINCT industry_code
        FROM refusal_events
        WHERE industry_code IS NOT NULL
          AND TRIM(industry_code) != ''
        ORDER BY industry_code ASC;
    """)

    industry_codes = [
        row["industry_code"]
        for row in cursor.fetchall()
    ]

    # --------------------------------------------------------
    # Top 30 origin countries
    # --------------------------------------------------------
    cursor.execute("""
        SELECT
            country_name,
            COUNT(*) AS record_count
        FROM refusal_events
        WHERE country_name IS NOT NULL
          AND TRIM(country_name) != ''
        GROUP BY country_name
        ORDER BY record_count DESC
        LIMIT 30;
    """)

    top_countries = [
        row["country_name"]
        for row in cursor.fetchall()
    ]

    return FdaFilterOptionsResponse(
        charge_categories=charge_categories,
        industry_codes=industry_codes,
        top_countries=top_countries
    )


# ============================================================
# FDA SUMMARY
# ============================================================

@router.get(
    "/summary",
    response_model=FdaSummaryResponse
)
def get_fda_summary(
    conn: sqlite3.Connection = Depends(get_db),
    _current_user: dict = Depends(get_current_user)
):
    """
    Returns high-level FDA refusal statistics.
    """

    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            COUNT(*) AS total_refusal_events,
            COUNT(DISTINCT country_code) AS unique_countries,
            COUNT(DISTINCT industry_code) AS unique_industry_codes,
            COUNT(DISTINCT charge_category) AS unique_charge_categories,
            MIN(refusal_date) AS earliest_refusal_date,
            MAX(refusal_date) AS latest_refusal_date
        FROM refusal_events;
    """)

    row = cursor.fetchone()

    return FdaSummaryResponse(
        total_refusal_events=row["total_refusal_events"] or 0,
        unique_countries=row["unique_countries"] or 0,
        unique_industry_codes=row["unique_industry_codes"] or 0,
        unique_charge_categories=row["unique_charge_categories"] or 0,
        earliest_refusal_date=row["earliest_refusal_date"],
        latest_refusal_date=row["latest_refusal_date"]
    )


# ============================================================
# FDA REFUSAL EVENTS
# ============================================================

@router.get(
    "/events",
    response_model=FdaPaginationResponse
)
def get_fda_refusal_events(
    page: int = Query(
        1,
        ge=1
    ),

    page_size: int = Query(
        25,
        ge=10,
        le=100
    ),

    search: Optional[str] = Query(
        None
    ),

    country_code: Optional[str] = Query(
        None
    ),

    industry_code: Optional[str] = Query(
        None
    ),

    charge_category: Optional[str] = Query(
        None
    ),

    year: Optional[str] = Query(
        None
    ),

    sort_by: str = Query(
        "refusal_date"
    ),

    sort_dir: str = Query(
        "desc"
    ),

    conn: sqlite3.Connection = Depends(get_db),
    _current_user: dict = Depends(get_current_user)
):
    """
    Query FDA refusal events with server-side filtering,
    searching, sorting and pagination.
    """

    cursor = conn.cursor()

    # --------------------------------------------------------
    # Allowed sorting columns
    # --------------------------------------------------------

    allowed_sort_columns = {
        "id": "id",
        "refusal_date": "refusal_date",
        "country_code": "country_code",
        "country_name": "country_name",
        "industry_code": "industry_code",
        "product_code": "product_code",
        "manufacturer_name": "manufacturer_name",
        "charge_category": "charge_category",
    }

    safe_sort_column = allowed_sort_columns.get(
        sort_by,
        "refusal_date"
    )

    safe_sort_direction = (
        "ASC"
        if sort_dir.lower() == "asc"
        else "DESC"
    )

    # --------------------------------------------------------
    # WHERE clauses
    # --------------------------------------------------------

    where_clauses = []
    params = []

    # Country
    if country_code:
        where_clauses.append(
            "UPPER(country_code) = UPPER(?)"
        )
        params.append(country_code.strip())

    # Industry
    if industry_code:
        where_clauses.append(
            "industry_code = ?"
        )
        params.append(industry_code.strip())

    # Charge category
    if charge_category:
        where_clauses.append(
            "charge_category = ?"
        )
        params.append(charge_category.strip())

    # Year
    if year:
        where_clauses.append(
            "substr(refusal_date, 1, 4) = ?"
        )
        params.append(year.strip())

    # General search
    if search and search.strip():

        search_value = f"%{search.strip()}%"

        where_clauses.append("""
            (
                refusal_id LIKE ?
                OR entry_num LIKE ?
                OR line_num LIKE ?
                OR product_code LIKE ?
                OR product_desc LIKE ?
                OR country_code LIKE ?
                OR country_name LIKE ?
                OR manufacturer_name LIKE ?
                OR manufacturer_city LIKE ?
                OR port_of_entry LIKE ?
                OR primary_charge_code LIKE ?
                OR primary_act_section LIKE ?
                OR primary_charge_statement LIKE ?
                OR charge_category LIKE ?
            )
        """)

        params.extend(
            [search_value] * 14
        )

    # --------------------------------------------------------
    # Build WHERE
    # --------------------------------------------------------

    where_sql = ""

    if where_clauses:
        where_sql = (
            "WHERE " +
            " AND ".join(where_clauses)
        )

    # --------------------------------------------------------
    # Total count
    # --------------------------------------------------------

    count_query = f"""
        SELECT COUNT(*) AS total
        FROM refusal_events
        {where_sql};
    """

    cursor.execute(
        count_query,
        params
    )

    total = cursor.fetchone()["total"]

    # --------------------------------------------------------
    # Pagination
    # --------------------------------------------------------

    offset = (page - 1) * page_size

    total_pages = (
        math.ceil(total / page_size)
        if total > 0
        else 0
    )

    # --------------------------------------------------------
    # Events query
    # --------------------------------------------------------

    events_query = f"""
        SELECT
            id,
            refusal_id,
            entry_num,
            line_num,
            refusal_date,
            product_code,
            industry_code,
            food_class,
            product_desc,
            country_code,
            country_name,
            manufacturer_name,
            manufacturer_city,
            port_of_entry,
            primary_charge_code,
            primary_act_section,
            primary_charge_statement,
            charge_category,
            defect_standard_status
        FROM refusal_events
        {where_sql}
        ORDER BY
            {safe_sort_column} {safe_sort_direction},
            id DESC
        LIMIT ? OFFSET ?;
    """

    event_params = params + [
        page_size,
        offset
    ]

    cursor.execute(
        events_query,
        event_params
    )

    rows = cursor.fetchall()

    # --------------------------------------------------------
    # Response items
    # --------------------------------------------------------

    items = [
        FdaRefusalItem(
            id=row["id"],
            refusal_id=row["refusal_id"],
            entry_num=row["entry_num"],
            line_num=row["line_num"],
            refusal_date=row["refusal_date"],
            product_code=row["product_code"],
            industry_code=row["industry_code"],
            food_class=row["food_class"],
            product_desc=row["product_desc"],
            country_code=row["country_code"],
            country_name=row["country_name"],
            manufacturer_name=row["manufacturer_name"],
            manufacturer_city=row["manufacturer_city"],
            port_of_entry=row["port_of_entry"],
            primary_charge_code=row["primary_charge_code"],
            primary_act_section=row["primary_act_section"],
            primary_charge_statement=row["primary_charge_statement"],
            charge_category=row["charge_category"],
            defect_standard_status=row["defect_standard_status"]
        )
        for row in rows
    ]

    return FdaPaginationResponse(
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
        items=items
    )