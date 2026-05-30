"""
Module 4 — Top Wallet Confirmation Signal (Static).
Phase 5: uses local top100 snapshot only. No live wallet polling.

SAFETY RULES:
- This module CONFIRMS existing signals — it never GENERATES them.
- Never use wallet data alone to trigger a trade decision.
- Wallet data is static intelligence (May 2026 snapshot).
- Label all output: "Confirmation only — not copy-trading."
"""
import json
import logging
from dataclasses import dataclass

from sqlmodel import Session, select

from database import engine
from models.top_wallets import TopWallet
from strategy.module1_market_type import TYPE_ANNUAL_TEMP, TYPE_GLOBAL_MONTHLY_TEMP, TYPE_CITY_STATION_TEMP

logger = logging.getLogger("weather1.strategy.module4")

SAFETY_LABEL = "Confirmation only — not copy-trading. Static May 2026 snapshot."


@dataclass
class WalletConfirmationResult:
    confirmed: bool
    matching_wallets: list[str]   # usernames of matching watchlist wallets
    rationale: str
    confidence_contribution: int  # 0–15 points
    safety_label: str


# Static specialisation map: which market types each watchlist wallet specialises in
# Derived from Phase 0 analysis of Top 100 strategy descriptions [FROM_ATTACHED_FILES]
WALLET_SPECIALISATIONS: dict[str, list[str]] = {
    # gopfan2 / gopfan: global temperature anomaly specialists
    "gopfan2":    [TYPE_ANNUAL_TEMP, TYPE_GLOBAL_MONTHLY_TEMP],
    "gopfan":     [TYPE_ANNUAL_TEMP, TYPE_GLOBAL_MONTHLY_TEMP],
    # bama124: global temp record specialist (July 2024 market)
    "bama124":    [TYPE_ANNUAL_TEMP, TYPE_GLOBAL_MONTHLY_TEMP],
    # CoffeeLover: low-probability contrarian events (megaquakes etc.), some global temp
    "CoffeeLover": [TYPE_ANNUAL_TEMP],
    # DarbySkees: very selective, unknown specialisation (too few trades)
    "DarbySkees": [],
    # MrFox: patient, unknown specific specialisation
    "MrFox":      [],
    # MtnMark: mountain/orographic weather specialist
    "MtnMark":    [TYPE_CITY_STATION_TEMP],
    # mkuu: ultra-selective, unknown
    "mkuu":       [],
    # Miojinho: ultra-selective, surgical, unknown
    "Miojinho":   [],
    # bama124 (already above), aenews cluster
    "aenews-915": [TYPE_ANNUAL_TEMP, TYPE_GLOBAL_MONTHLY_TEMP],
    "chilling":   [TYPE_ANNUAL_TEMP, TYPE_GLOBAL_MONTHLY_TEMP],
    # 9985: city-specific temperature specialist
    "9985":       [TYPE_CITY_STATION_TEMP],
    # InsiderrrZ: unknown, very selective
    "InsiderrrZ": [],
    # xX25Xx: ultra-selective
    "xX25Xx":     [],
    # ocelot-204: infrequent, accurate
    "ocelot-204": [],
    # lesse: highly selective
    "lesse":      [],
    # ANudeEgg: global temp records
    "ANudeEgg":   [TYPE_ANNUAL_TEMP, TYPE_GLOBAL_MONTHLY_TEMP],
}


def _load_watchlist() -> list[TopWallet]:
    try:
        with Session(engine) as s:
            return s.exec(
                select(TopWallet).where(TopWallet.on_watchlist == True)  # noqa: E712
            ).all()
    except Exception as e:
        logger.error("Failed to load watchlist: %s", e)
        return []


def check(market_type: str, question: str) -> WalletConfirmationResult:
    """
    Check if any watchlist wallet specialises in this market type.
    Returns a WalletConfirmationResult.
    This confirmation is secondary only — never a primary trade trigger.
    """
    watchlist = _load_watchlist()
    if not watchlist:
        return WalletConfirmationResult(
            confirmed=False, matching_wallets=[],
            rationale="Watchlist not loaded (run POST /wallets/import-top100)",
            confidence_contribution=0, safety_label=SAFETY_LABEL,
        )

    matching: list[str] = []
    for w in watchlist:
        username = w.username or ""
        specialisations = WALLET_SPECIALISATIONS.get(username, [])
        if market_type in specialisations:
            matching.append(username)

    if matching:
        rationale = (
            f"Watchlist wallets specialising in {market_type}: {', '.join(matching[:3])}. "
            f"These wallets have historically profited from this market type. "
            f"This is a secondary confirmation signal, not a primary trigger."
        )
        contrib = 15 if len(matching) >= 2 else 8
    else:
        rationale = f"No watchlist wallets with confirmed specialisation in {market_type}."
        contrib = 0

    return WalletConfirmationResult(
        confirmed=len(matching) > 0,
        matching_wallets=matching[:5],
        rationale=rationale,
        confidence_contribution=contrib,
        safety_label=SAFETY_LABEL,
    )
