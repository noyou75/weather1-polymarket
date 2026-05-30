"""
Ingestion log — one row per API fetch attempt. Tracks health of data pipeline.
"""
from typing import Optional
from sqlmodel import Field, SQLModel


class IngestionLog(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    run_at: str = ""                         # ISO timestamp when run started
    source: str = ""                         # "gamma_api"
    status: str = ""                         # "ok" | "error" | "partial"
    events_fetched: int = 0
    markets_fetched: int = 0
    markets_stored: int = 0
    prices_stored: int = 0
    duration_ms: int = 0
    error_message: Optional[str] = None
