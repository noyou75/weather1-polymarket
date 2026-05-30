"""
Polymarket read-only ingestion — Phase 2.

Data source: Polymarket Gamma API (public, no authentication required for reads).
Endpoint verified: GET https://gamma-api.polymarket.com/events?tag_slug=weather&active=true&closed=false

NO write endpoints. NO private keys. NO order placement. NO authentication headers.

Price fields (bestBid, bestAsk, spread, lastTradePrice, liquidity) are returned
directly by the Gamma API — no separate CLOB API call is needed for Phase 2.
"""
import json
import time
import logging
from datetime import datetime, timezone
from typing import Any

import httpx
from sqlmodel import Session, select

from database import engine
from models.markets import Market
from models.market_prices import MarketPrice
from models.ingestion_logs import IngestionLog

logger = logging.getLogger("weather1.ingestion")

# ── Verified API endpoints ────────────────────────────────────────────────────
# [VERIFIED 2026-05-30] via direct probe
GAMMA_BASE = "https://gamma-api.polymarket.com"
GAMMA_EVENTS_URL = f"{GAMMA_BASE}/events"

# ── Safety limits ─────────────────────────────────────────────────────────────
REQUEST_TIMEOUT = 12.0        # seconds per HTTP request
MAX_EVENTS_PER_FETCH = 200    # safety cap on events paginated
INTER_REQUEST_DELAY = 0.3     # seconds between paginated requests
MAX_RETRIES = 2


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _safe_float(val: Any) -> float | None:
    """Convert a value to float, returning None on failure."""
    try:
        return float(val) if val is not None else None
    except (TypeError, ValueError):
        return None


def _parse_clob_token_ids(raw: Any) -> tuple[str | None, str | None]:
    """
    Extract YES and NO token IDs from clobTokenIds field.
    Field is a JSON string list: '["token_yes_id", "token_no_id"]'
    or already parsed as a Python list.
    """
    try:
        if isinstance(raw, str):
            ids = json.loads(raw)
        elif isinstance(raw, list):
            ids = raw
        else:
            return None, None
        yes_id = str(ids[0]) if len(ids) > 0 else None
        no_id  = str(ids[1]) if len(ids) > 1 else None
        return yes_id, no_id
    except Exception:
        return None, None


def _parse_outcome_prices(raw: Any) -> tuple[float | None, float | None]:
    """Extract YES and NO prices from outcomePrices field."""
    try:
        if isinstance(raw, str):
            prices = json.loads(raw)
        elif isinstance(raw, list):
            prices = raw
        else:
            return None, None
        yes_p = _safe_float(prices[0]) if len(prices) > 0 else None
        no_p  = _safe_float(prices[1]) if len(prices) > 1 else None
        return yes_p, no_p
    except Exception:
        return None, None


def _fetch_weather_events_page(offset: int = 0, limit: int = 100) -> list[dict]:
    """
    Fetch one page of open weather events from Gamma API.
    Returns empty list on any error (never raises).
    """
    params = {
        "tag_slug": "weather",
        "active": "true",
        "closed": "false",
        "limit": limit,
        "offset": offset,
    }
    for attempt in range(MAX_RETRIES + 1):
        try:
            resp = httpx.get(
                GAMMA_EVENTS_URL,
                params=params,
                timeout=REQUEST_TIMEOUT,
                headers={"Accept": "application/json"},
                follow_redirects=True,
            )
            resp.raise_for_status()
            data = resp.json()
            return data if isinstance(data, list) else []
        except httpx.TimeoutException:
            logger.warning("Gamma API timeout (attempt %d/%d)", attempt + 1, MAX_RETRIES + 1)
        except httpx.HTTPStatusError as e:
            logger.error("Gamma API HTTP error %s: %s", e.response.status_code, e.response.text[:200])
            return []
        except Exception as e:
            logger.error("Gamma API fetch error: %s", e)
            return []
        if attempt < MAX_RETRIES:
            time.sleep(1.0 * (attempt + 1))
    return []


def _market_from_gamma(raw: dict, event_title: str, event_slug: str, fetched_at: str) -> Market:
    """Convert a Gamma API market dict into a Market model instance."""
    yes_price, no_price = _parse_outcome_prices(raw.get("outcomePrices"))
    yes_token, no_token = _parse_clob_token_ids(raw.get("clobTokenIds"))

    # Gamma gives spread as a decimal fraction (e.g. 0.01 = 1%)
    spread_raw = _safe_float(raw.get("spread"))

    return Market(
        market_id      = str(raw["id"]),
        condition_id   = raw.get("conditionId"),
        slug           = raw.get("slug"),
        question       = raw.get("question", ""),
        description    = (raw.get("description") or "")[:500],
        resolution_source = raw.get("resolutionSource"),
        outcomes       = json.dumps(raw.get("outcomes")) if raw.get("outcomes") else None,
        outcome_prices = json.dumps(raw.get("outcomePrices")) if raw.get("outcomePrices") else None,
        clob_token_id_yes = yes_token,
        clob_token_id_no  = no_token,
        yes_price      = yes_price,
        no_price       = no_price,
        best_bid       = _safe_float(raw.get("bestBid")),
        best_ask       = _safe_float(raw.get("bestAsk")),
        spread         = spread_raw,
        last_trade_price = _safe_float(raw.get("lastTradePrice")),
        liquidity      = _safe_float(raw.get("liquidity")),
        volume         = _safe_float(raw.get("volume")),
        volume_24hr    = _safe_float(raw.get("volume24hr")),
        category       = "weather",
        is_active      = bool(raw.get("active", True)),
        is_closed      = bool(raw.get("closed", False)),
        accepting_orders = bool(raw.get("acceptingOrders", False)),
        neg_risk       = bool(raw.get("negRisk", False)),
        end_date       = raw.get("endDate"),
        start_date     = raw.get("startDate"),
        last_updated   = raw.get("updatedAt"),
        fetched_at     = fetched_at,
        event_title    = event_title,
        event_slug     = event_slug,
        data_source    = "gamma_api",
    )


def _price_snapshot(market: Market, fetched_at: str) -> MarketPrice:
    return MarketPrice(
        market_id        = market.market_id,
        fetched_at       = fetched_at,
        yes_price        = market.yes_price,
        no_price         = market.no_price,
        best_bid         = market.best_bid,
        best_ask         = market.best_ask,
        spread           = market.spread,
        last_trade_price = market.last_trade_price,
        liquidity        = market.liquidity,
        volume_24hr      = market.volume_24hr,
    )


def run_ingestion() -> IngestionLog:
    """
    Main ingestion entry point. Called by scheduler and /ingestion/run-once endpoint.

    Fetches all open weather events from Gamma API (paginated),
    extracts embedded markets, upserts into SQLite, stores price snapshots.

    Returns an IngestionLog record (already committed to DB).
    NEVER raises — all errors are caught and logged.
    """
    t_start = time.monotonic()
    started_at = _now_iso()
    log = IngestionLog(run_at=started_at, source="gamma_api", status="error")

    events_fetched = 0
    all_markets: list[dict] = []
    fetched_at = _now_iso()

    # ── Paginate through all open weather events ──────────────────────────────
    try:
        offset = 0
        page_size = 100
        while events_fetched < MAX_EVENTS_PER_FETCH:
            page = _fetch_weather_events_page(offset=offset, limit=page_size)
            if not page:
                break
            for event in page:
                events_fetched += 1
                event_title = event.get("title", "")
                event_slug  = event.get("slug", "")
                for mkt in event.get("markets", []):
                    mkt["_event_title"] = event_title
                    mkt["_event_slug"]  = event_slug
                    all_markets.append(mkt)
            if len(page) < page_size:
                break   # last page
            offset += page_size
            time.sleep(INTER_REQUEST_DELAY)

        log.events_fetched = events_fetched
        log.markets_fetched = len(all_markets)
        logger.info("Fetched %d events, %d markets", events_fetched, len(all_markets))

    except Exception as e:
        log.error_message = f"Pagination error: {e}"
        log.duration_ms = int((time.monotonic() - t_start) * 1000)
        _commit_log(log)
        return log

    if not all_markets:
        log.status = "ok"
        log.error_message = "No weather markets returned by API (may be transient)"
        log.duration_ms = int((time.monotonic() - t_start) * 1000)
        _commit_log(log)
        return log

    # ── Upsert markets and price snapshots ────────────────────────────────────
    markets_stored = 0
    prices_stored = 0
    errors = []

    with Session(engine) as session:
        for raw in all_markets:
            market_id = str(raw.get("id", ""))
            if not market_id:
                continue
            try:
                new_mkt = _market_from_gamma(
                    raw,
                    event_title=raw.get("_event_title", ""),
                    event_slug=raw.get("_event_slug", ""),
                    fetched_at=fetched_at,
                )
                # Upsert: update existing or insert new
                existing = session.exec(
                    select(Market).where(Market.market_id == market_id)
                ).first()

                if existing:
                    # Update price and status fields
                    existing.yes_price        = new_mkt.yes_price
                    existing.no_price         = new_mkt.no_price
                    existing.best_bid         = new_mkt.best_bid
                    existing.best_ask         = new_mkt.best_ask
                    existing.spread           = new_mkt.spread
                    existing.last_trade_price = new_mkt.last_trade_price
                    existing.liquidity        = new_mkt.liquidity
                    existing.volume           = new_mkt.volume
                    existing.volume_24hr      = new_mkt.volume_24hr
                    existing.is_active        = new_mkt.is_active
                    existing.is_closed        = new_mkt.is_closed
                    existing.accepting_orders = new_mkt.accepting_orders
                    existing.fetched_at       = new_mkt.fetched_at
                    existing.last_updated     = new_mkt.last_updated
                    existing.outcome_prices   = new_mkt.outcome_prices
                    session.add(existing)
                else:
                    session.add(new_mkt)

                # Always store a price snapshot for history
                snapshot = _price_snapshot(new_mkt, fetched_at)
                session.add(snapshot)
                prices_stored += 1
                markets_stored += 1

            except Exception as e:
                errors.append(f"market {market_id}: {e}")
                logger.warning("Failed to store market %s: %s", market_id, e)

        try:
            session.commit()
        except Exception as e:
            errors.append(f"commit error: {e}")
            logger.error("DB commit failed: %s", e)

    log.markets_stored = markets_stored
    log.prices_stored = prices_stored
    log.status = "ok" if not errors else ("partial" if markets_stored > 0 else "error")
    log.error_message = "; ".join(errors[:5]) if errors else None
    log.duration_ms = int((time.monotonic() - t_start) * 1000)

    logger.info(
        "Ingestion complete: status=%s markets=%d prices=%d duration=%dms",
        log.status, markets_stored, prices_stored, log.duration_ms,
    )
    _commit_log(log)
    return log


def _commit_log(log: IngestionLog) -> None:
    """Persist the ingestion log. Uses expire_on_commit=False so log fields
    remain readable after the session closes."""
    try:
        with Session(engine, expire_on_commit=False) as session:
            session.add(log)
            session.commit()
    except Exception as e:
        logger.error("Failed to commit ingestion log: %s", e)


def get_ingestion_status() -> dict:
    """Return summary of ingestion health from DB."""
    try:
        with Session(engine) as session:
            # Latest log
            logs = session.exec(
                select(IngestionLog).order_by(IngestionLog.id.desc()).limit(1)  # type: ignore[arg-type]
            ).all()
            latest = logs[0] if logs else None

            # Market count
            market_count = session.exec(
                select(Market).where(
                    Market.is_active == True,  # noqa: E712
                    Market.is_closed == False,  # noqa: E712
                )
            )
            count = len(market_count.all())

            return {
                "last_run_at": latest.run_at if latest else None,
                "last_status": latest.status if latest else "never_run",
                "last_error": latest.error_message if latest else None,
                "last_markets_fetched": latest.markets_fetched if latest else 0,
                "last_markets_stored": latest.markets_stored if latest else 0,
                "last_duration_ms": latest.duration_ms if latest else 0,
                "active_weather_markets_in_db": count,
                "data_source": "gamma_api",
                "api_endpoint": GAMMA_EVENTS_URL,
            }
    except Exception as e:
        return {"status": "error", "error": str(e)}
