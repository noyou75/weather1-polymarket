"""
Weather1 — Database setup
SQLite via SQLModel.

Local default:  Weather1/data/weather1.db  (gitignored)
Railway cloud:  /data/weather1.db  (persistent Volume mounted at /data)

Override with env var:
  WEATHER1_DB_PATH=/data/weather1.db

Schema versioning: when SCHEMA_VERSION is bumped, all tables are dropped and
recreated automatically. Safe because no real trading data exists yet.
"""
import os
from pathlib import Path
from sqlmodel import SQLModel, create_engine, Session, text

# Import all models so SQLModel.metadata is populated before create_all() runs.
import models.markets        # noqa: F401
import models.market_prices  # noqa: F401
import models.positions      # noqa: F401
import models.signals        # noqa: F401
import models.logs           # noqa: F401
import models.ingestion_logs # noqa: F401
import models.top_wallets    # noqa: F401
import models.weather        # noqa: F401
import models.backtest           # noqa: F401
import models.settlement_source  # noqa: F401
import models.shadow              # noqa: F401

# Phase 6F: ShadowDailySummary added as additive table (no drop/recreate).
SCHEMA_VERSION = 9

# ── Database path: env var overrides local default ────────────────────────────
_env_db_path = os.getenv("WEATHER1_DB_PATH")
if _env_db_path:
    # Cloud deployment (Railway): use the mounted volume path
    _db_path = Path(_env_db_path)
else:
    # Local development: Weather1/data/weather1.db
    _db_path = Path(__file__).parent.parent / "data" / "weather1.db"

# Always ensure parent directory exists
_db_path.parent.mkdir(parents=True, exist_ok=True)

DATABASE_URL = f"sqlite:///{_db_path}"

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},
    echo=False,
)


def _get_stored_version() -> int:
    try:
        with engine.connect() as conn:
            result = conn.execute(text("SELECT value FROM _schema_version WHERE key='version'"))
            row = result.fetchone()
            return int(row[0]) if row else 0
    except Exception:
        return 0


def _set_stored_version(version: int) -> None:
    with engine.connect() as conn:
        conn.execute(text(
            "CREATE TABLE IF NOT EXISTS _schema_version (key TEXT PRIMARY KEY, value TEXT)"
        ))
        conn.execute(text(
            "INSERT OR REPLACE INTO _schema_version (key, value) VALUES ('version', :v)"
        ), {"v": str(version)})
        conn.commit()


def create_db_and_tables() -> None:
    """
    Create all tables. If SCHEMA_VERSION changed, drop and recreate.
    Phase 6F: additive tables (ShadowDailySummary) are created without drop.
    """
    stored = _get_stored_version()
    if stored < SCHEMA_VERSION:
        SQLModel.metadata.drop_all(engine)
        SQLModel.metadata.create_all(engine)
        _set_stored_version(SCHEMA_VERSION)
    else:
        SQLModel.metadata.create_all(engine)


def get_session():
    """FastAPI dependency — yields a database session."""
    with Session(engine) as session:
        yield session
