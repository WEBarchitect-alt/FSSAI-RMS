import os
import sqlite3
from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

load_dotenv()

from backend.api.dependencies import get_db, DB_PATH
from backend.api.auth import router as auth_router
from backend.api.routes import admin_router, india_router
from backend.api.fda import router as fda_router
from backend.api.eu import router as eu_router

app = FastAPI(
    title="SENTRA-FS Intelligence API",
    description="Food Safety & Import Rejection Intelligence Platform",
    version="1.2.0"
)

raw_cors = os.getenv("CORS_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173")
origins = [origin.strip() for origin in raw_cors.split(",") if origin.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins if origins else ["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Router Registrations
app.include_router(auth_router)
app.include_router(admin_router)
app.include_router(india_router)
app.include_router(fda_router)
app.include_router(eu_router)

# -------------------------------------------------------------
# Preserved Core Endpoints
# -------------------------------------------------------------
@app.get("/health", tags=["System"])
def health_check():
    return {
        "status": "ok",
        "platform": "SENTRA-FS",
        "db_available": os.path.exists(DB_PATH)
    }

@app.get("/api/summary", tags=["Analytics"])
def get_summary(conn: sqlite3.Connection = Depends(get_db)):
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM refusal_events;")
    fda_count = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM eu_border_events;")
    eu_count = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM india_lab_rejections;")
    india_count = cursor.fetchone()[0]

    return {
        "refusal_events": fda_count,
        "eu_border_events": eu_count,
        "india_lab_rejections": india_count
    }