"""Execution log model — audit trail for all system actions."""
from typing import Optional
from sqlmodel import Field, SQLModel


class ExecutionLog(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    timestamp: str = ""
    event_type: str = ""   # "signal_evaluated" | "paper_trade" | "risk_check" | "kill_switch" | "data_fetch"
    market_id: Optional[str] = None
    detail: str = ""
    result: str = ""       # "ok" | "skipped" | "blocked" | "error"
    module: Optional[str] = None
