"""
Settlement source router — Phase 6D.
Shows verified settlement sources and historical market outcomes.
Read-only. No private keys. No real orders.
"""
from fastapi import APIRouter, Depends
from sqlmodel import Session, select

from database import get_session
from models.settlement_source import MarketSettlementSource, HistoricalMarketOutcome

router = APIRouter(prefix="/settlement", tags=["Settlement"])


@router.get("/sources", summary="Verified settlement sources per market type")
def list_sources(session: Session = Depends(get_session)):
    sources = session.exec(select(MarketSettlementSource)).all()
    return {
        "count": len(sources),
        "note": (
            "Phase 6D finding: All annual/monthly temperature markets use "
            "'Global Land-Ocean Temperature Index' (NASA GISTEMP v4) as settlement source. "
            "Verified from 11 closed market descriptions (Apr 2024 – Mar 2025)."
        ),
        "sources": [
            {
                "market_type": s.market_type,
                "source_code": s.source_code,
                "source_description": s.source_description,
                "evidence_quote": s.evidence_quote,
                "verified_at": s.verified_at,
            }
            for s in sources
        ],
    }


@router.get("/outcomes", summary="Historical market resolution outcomes from Gamma API")
def list_outcomes(market_type: str = "", limit: int = 50, session: Session = Depends(get_session)):
    stmt = select(HistoricalMarketOutcome).limit(limit)
    if market_type:
        stmt = stmt.where(HistoricalMarketOutcome.market_type == market_type)
    rows = session.exec(stmt).all()
    return {
        "count": len(rows),
        "note": "Final resolution outcomes only — no intermediate trade prices available via public API.",
        "outcomes": [
            {
                "market_id": r.market_id,
                "question": r.question[:80],
                "market_type": r.market_type,
                "resolved_yes": r.resolved_yes,
                "final_yes_price": r.final_yes_price,
                "settlement_source": r.settlement_source,
                "end_date": r.end_date,
            }
            for r in rows
        ],
    }


@router.post("/verify-now", summary="Run settlement source verification (read-only, no auth)")
def verify_now():
    from ingestion.settlement_sources import run_settlement_verification
    result = run_settlement_verification()
    return result
