"""
Top Wallet Parser — Phase 3.

Reads the local polymarket_weather_top100.html snapshot (no network calls).
Extracts all 100 trader records from the embedded JavaScript `traders` array.
Stores structured records in SQLite and exports data/top100_wallets.json.

Safety:
- No network calls.
- No private keys.
- No authentication.
- No copy-trading logic.
- Top-wallet data is informational intelligence only (Module 4 confirmation).

Module 4 watchlist criteria (from Phase 0 plan):
- Efficiency > 8% all-time
- Sharp Selector strategy (primary)
- Used to CONFIRM existing signals, never as a primary trade trigger
"""
import json
import re
import logging
from pathlib import Path
from typing import Any
from sqlmodel import Session, select

from database import engine
from models.top_wallets import TopWallet

logger = logging.getLogger("weather1.ingestion.top_wallets")

# ── Source file location ──────────────────────────────────────────────────────
_project_root = Path(__file__).parent.parent.parent
HTML_PATH = _project_root / "data" / "raw" / "polymarket_weather_top100.html"
JSON_OUTPUT = _project_root / "data" / "top100_wallets.json"

# ── Module 4 watchlist: efficiency > 8% AND Sharp Selector ───────────────────
# From Phase 0 plan: min efficiency threshold for confirmation weight
WATCHLIST_MIN_EFFICIENCY = 8.0
WATCHLIST_REQUIRED_STRATEGY = "Sharp Selector"


def _find_html_file() -> Path | None:
    """Search for the source HTML in expected locations."""
    candidates = [
        HTML_PATH,
        _project_root / "polymarket_weather_top100.html",
        _project_root / "data" / "polymarket_weather_top100.html",
    ]
    for p in candidates:
        if p.exists():
            return p
    return None


def _parse_js_string(raw: str) -> str:
    """
    Unescape basic JS string escapes in strategy_detail text.
    The HTML embeds JS string literals, not JSON strings.
    """
    return (raw
            .replace("\\'", "'")
            .replace('\\"', '"')
            .replace("\\n", " ")
            .replace("\\t", " "))


def _extract_traders_from_html(html: str) -> list[dict[str, Any]]:
    """
    Extract the `traders` array from the embedded JavaScript.
    The array is a JS object literal, not valid JSON, so we parse
    field by field using targeted regex rather than json.loads().
    """
    # Find the traders array block
    array_match = re.search(
        r'const traders\s*=\s*\[(.*?)\]\s*;',
        html,
        re.DOTALL,
    )
    if not array_match:
        raise ValueError("Could not locate `const traders = [...]` in HTML file")

    array_text = array_match.group(1)

    # Split into individual trader objects using rank as delimiter
    # Each object starts with {rank:N,
    entries = re.split(r'(?=\{rank:\d+,)', array_text)
    entries = [e.strip().rstrip(',').strip() for e in entries if e.strip()]

    traders: list[dict[str, Any]] = []

    for entry in entries:
        try:
            trader = _parse_trader_entry(entry)
            if trader:
                traders.append(trader)
        except Exception as e:
            logger.warning("Failed to parse trader entry: %s | snippet: %s", e, entry[:80])

    return traders


def _parse_trader_entry(text: str) -> dict[str, Any] | None:
    """Parse a single trader JS object into a Python dict."""

    def get(pattern: str, default: str = "") -> str:
        m = re.search(pattern, text)
        return m.group(1) if m else default

    # Numeric fields
    rank_s = get(r'rank:(\d+)')
    if not rank_s:
        return None
    rank = int(rank_s)

    pnl_s = get(r'pnl:([\d.]+)')
    vol_s = get(r'vol:([\d.]+)')
    pnl = float(pnl_s) if pnl_s else 0.0
    vol = float(vol_s) if vol_s else 0.0
    efficiency = round((pnl / vol * 100), 4) if vol > 0 else 0.0

    # String fields
    wallet   = get(r'wallet:"(0x[a-fA-F0-9]+)"')
    username = get(r'username:"([^"]*)"')
    x_user   = get(r'xUsername:"([^"]*)"')
    verified = "true" in get(r'verified:(true|false)')

    # Strategies array: ["Tag1","Tag2"]
    strats_raw = get(r'strategies:(\[[^\]]+\])')
    try:
        strategies = json.loads(strats_raw) if strats_raw else []
    except Exception:
        strategies = []

    # strategy_detail: long JS string ending with "}
    # This is tricky — the string may contain escaped quotes and spans lines
    # We match everything between strategy_detail:" and the final "}
    detail_match = re.search(r'strategy_detail:"(.*?)"\s*\}', text, re.DOTALL)
    detail = _parse_js_string(detail_match.group(1)) if detail_match else ""
    # Trim to 2000 chars for DB storage
    detail = detail[:2000]

    if not wallet:
        logger.warning("Rank %d has no wallet address — skipping", rank)
        return None

    return {
        "rank": rank,
        "wallet_address": wallet,
        "username": username or None,
        "x_username": x_user or None,
        "verified": verified,
        "pnl_usd": pnl,
        "volume_usd": vol,
        "efficiency_pct": efficiency,
        "strategies": json.dumps(strategies),
        "strategy_detail": detail or None,
    }


def _is_watchlist(trader: dict[str, Any]) -> tuple[bool, str | None]:
    """
    Determine if a trader qualifies for the Module 4 watchlist.
    Criteria (from Phase 0 plan):
    - Efficiency > 8%
    - Has Sharp Selector strategy tag
    Both must be satisfied.
    """
    eff = trader.get("efficiency_pct", 0.0)
    strats_raw = trader.get("strategies", "[]")
    try:
        strats = json.loads(strats_raw) if isinstance(strats_raw, str) else strats_raw
    except Exception:
        strats = []

    has_sharp = WATCHLIST_REQUIRED_STRATEGY in strats
    above_threshold = eff >= WATCHLIST_MIN_EFFICIENCY

    if has_sharp and above_threshold:
        reason = f"efficiency {eff:.1f}% > {WATCHLIST_MIN_EFFICIENCY}% threshold · Sharp Selector"
        return True, reason
    return False, None


def run_top100_import() -> dict[str, Any]:
    """
    Main entry point: parse HTML → SQLite → JSON.
    Returns a summary dict. Never raises.
    """
    result: dict[str, Any] = {
        "status": "error",
        "source_file": str(HTML_PATH),
        "traders_parsed": 0,
        "traders_stored": 0,
        "watchlist_count": 0,
        "errors": [],
    }

    # ── Locate source file ────────────────────────────────────────────────────
    html_path = _find_html_file()
    if not html_path:
        msg = (
            f"Source file not found. Expected at: {HTML_PATH}. "
            "Please place polymarket_weather_top100.html in Weather1/data/raw/"
        )
        result["errors"].append(msg)
        logger.error(msg)
        return result

    result["source_file"] = str(html_path)
    logger.info("Parsing top100 HTML from: %s", html_path)

    # ── Parse HTML ────────────────────────────────────────────────────────────
    try:
        html = html_path.read_text(encoding="utf-8")
        raw_traders = _extract_traders_from_html(html)
        result["traders_parsed"] = len(raw_traders)
        logger.info("Parsed %d trader entries", len(raw_traders))
    except Exception as e:
        result["errors"].append(f"HTML parse error: {e}")
        logger.error("HTML parse failed: %s", e)
        return result

    if not raw_traders:
        result["errors"].append("No traders extracted from HTML")
        return result

    # ── Upsert into SQLite ────────────────────────────────────────────────────
    stored = 0
    watchlist_count = 0

    with Session(engine, expire_on_commit=False) as session:
        for t in raw_traders:
            try:
                on_wl, wl_reason = _is_watchlist(t)
                if on_wl:
                    watchlist_count += 1

                existing = session.exec(
                    select(TopWallet).where(
                        TopWallet.wallet_address == t["wallet_address"]
                    )
                ).first()

                if existing:
                    # Update all fields
                    existing.rank             = t["rank"]
                    existing.username         = t["username"]
                    existing.x_username       = t["x_username"]
                    existing.verified         = t["verified"]
                    existing.pnl_usd          = t["pnl_usd"]
                    existing.volume_usd       = t["volume_usd"]
                    existing.efficiency_pct   = t["efficiency_pct"]
                    existing.strategies       = t["strategies"]
                    existing.strategy_detail  = t["strategy_detail"]
                    existing.on_watchlist     = on_wl
                    existing.watchlist_reason = wl_reason
                    session.add(existing)
                else:
                    wallet = TopWallet(
                        rank             = t["rank"],
                        wallet_address   = t["wallet_address"],
                        username         = t["username"],
                        x_username       = t["x_username"],
                        verified         = t["verified"],
                        pnl_usd          = t["pnl_usd"],
                        volume_usd       = t["volume_usd"],
                        efficiency_pct   = t["efficiency_pct"],
                        strategies       = t["strategies"],
                        strategy_detail  = t["strategy_detail"],
                        on_watchlist     = on_wl,
                        watchlist_reason = wl_reason,
                    )
                    session.add(wallet)
                stored += 1
            except Exception as e:
                result["errors"].append(f"rank {t.get('rank')}: {e}")
                logger.warning("Failed to store rank %s: %s", t.get("rank"), e)

        try:
            session.commit()
        except Exception as e:
            result["errors"].append(f"commit error: {e}")
            logger.error("DB commit failed: %s", e)

    result["traders_stored"] = stored
    result["watchlist_count"] = watchlist_count

    # ── Export JSON snapshot ──────────────────────────────────────────────────
    try:
        JSON_OUTPUT.parent.mkdir(parents=True, exist_ok=True)
        json_records = []
        for t in raw_traders:
            on_wl, wl_reason = _is_watchlist(t)
            json_records.append({
                **t,
                "strategies": json.loads(t["strategies"]) if isinstance(t["strategies"], str) else t["strategies"],
                "on_watchlist": on_wl,
                "watchlist_reason": wl_reason,
            })
        JSON_OUTPUT.write_text(
            json.dumps({"snapshot_date": "2026-05", "count": len(json_records), "traders": json_records}, indent=2),
            encoding="utf-8",
        )
        result["json_exported"] = str(JSON_OUTPUT)
        logger.info("JSON snapshot written to %s", JSON_OUTPUT)
    except Exception as e:
        result["errors"].append(f"JSON export error: {e}")
        logger.warning("JSON export failed: %s", e)

    result["status"] = "ok" if stored == len(raw_traders) else ("partial" if stored > 0 else "error")
    logger.info("Import complete: %d stored, %d on watchlist", stored, watchlist_count)
    return result


def get_strategy_distribution() -> dict[str, int]:
    """Count traders per strategy tag."""
    dist: dict[str, int] = {}
    try:
        with Session(engine) as session:
            wallets = session.exec(select(TopWallet)).all()
            for w in wallets:
                try:
                    strats = json.loads(w.strategies or "[]")
                    for s in strats:
                        dist[s] = dist.get(s, 0) + 1
                except Exception:
                    pass
    except Exception as e:
        logger.error("Strategy distribution error: %s", e)
    return dist
