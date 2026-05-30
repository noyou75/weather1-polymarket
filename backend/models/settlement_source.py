"""
Settlement source verification models — Phase 6D.
Records which Polymarket market types use which settlement data source.

FINDING (Phase 6D, verified 2026-05-30):
All annual and monthly global temperature markets use:
  "Global Land-Ocean Temperature Index" = NASA GISS Surface Temperature Analysis (GISTEMP v4)
  Evidence: market description boilerplate confirmed across 11 closed events.
"""
from typing import Optional
from sqlmodel import Field, SQLModel


# Settlement source constants
SOURCE_NASA_GISTEMP    = "VERIFIED_NASA_GISTEMP"    # Global Land-Ocean Temperature Index
SOURCE_NOAA_GLOBALTEMP = "VERIFIED_NOAA_GLOBALTEMP"
SOURCE_ERA5            = "VERIFIED_ERA5"
SOURCE_OTHER           = "VERIFIED_OTHER"
SOURCE_UNVERIFIED      = "UNVERIFIED"


class MarketSettlementSource(SQLModel, table=True):
    """
    Records the verified settlement source for a Polymarket market type.
    One record per market_type. Updated by the settlement source ingestion module.
    """
    id: Optional[int] = Field(default=None, primary_key=True)
    market_type: str = Field(index=True, unique=True)  # "annual_temp" | "global_monthly_temp"
    source_code: str = SOURCE_UNVERIFIED
    source_description: str = ""       # full text describing settlement source
    evidence_market_id: Optional[str] = None   # example market that confirmed this
    evidence_quote: Optional[str] = None        # exact description text used as evidence
    verified_at: Optional[str] = None
    notes: Optional[str] = None


class HistoricalMarketOutcome(SQLModel, table=True):
    """
    Records the confirmed YES/NO resolution outcome for a closed Polymarket market.
    Derived from closed market outcomePrices in the Gamma API.
    Used to validate backtest signal direction against real outcomes.

    NOTE: This captures FINAL RESOLUTION ONLY, not intermediate prices.
    Entry prices remain estimated in Phase 6D.
    """
    id: Optional[int] = Field(default=None, primary_key=True)
    market_id: str = Field(index=True, unique=True)   # Gamma integer id
    condition_id: Optional[str] = None
    question: str = ""
    market_type: str = ""                              # annual_temp | global_monthly_temp | etc.
    event_title: Optional[str] = None
    resolved_yes: Optional[bool] = None                # True if YES token = 1.0
    final_yes_price: Optional[float] = None            # 0.0 or 1.0
    settlement_source: str = SOURCE_UNVERIFIED
    end_date: Optional[str] = None
    fetched_at: Optional[str] = None
