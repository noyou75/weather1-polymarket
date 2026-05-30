"""
Backtest metrics calculator — Phase 6.
Computes performance metrics and evaluates against Phase 0 acceptance criteria.
"""
import math
from dataclasses import dataclass

from backtest.risk_replay import (
    STARTING_CAPITAL,
    DAILY_SOFT_STOP_PCT,
    HARD_STOP_PCT,
)

# Phase 0 Section 8 acceptance criteria
CRITERIA_WIN_RATE_MIN     = 52.0    # %
CRITERIA_MAX_DRAWDOWN_MAX = 12.0    # %
CRITERIA_SHARPE_MIN       = 0.8
CRITERIA_MIN_SIGNALS      = 30
CRITERIA_KILL_SWITCH_MAX  = 0       # prefer 0; >2 = reject


@dataclass
class BacktestMetricsData:
    # Counts
    total_signals: int
    total_trades: int          # signals that passed liquidity gate
    winning_trades: int
    losing_trades: int
    skipped_trades: int        # blocked by risk rules

    # Performance
    total_return_pct: float
    win_rate_pct: float
    avg_return_per_trade_pct: float
    max_drawdown_pct: float
    sharpe_estimate: float
    kill_switch_triggers: int
    daily_stop_triggers: int

    # Signal quality
    module1_accuracy_pct: float   # % markets correctly classified
    module2_direction_accuracy_pct: float  # % signals with correct direction
    module4_confirmation_rate_pct: float

    # Data quality
    data_quality_rating: str      # HIGH | MEDIUM | LOW | INSUFFICIENT
    data_quality_notes: list[str]
    limitations: list[str]

    # Phase 0 acceptance criteria
    pass_win_rate: bool
    pass_max_drawdown: bool
    pass_sharpe: bool
    pass_min_signals: bool
    pass_kill_switch: bool
    overall_pass: bool
    readiness: str   # "READY_FOR_PAPER" | "NEEDS_MORE_DATA" | "FAIL" | "INSUFFICIENT_DATA"


def _sharpe(returns: list[float]) -> float:
    """Simplified Sharpe: mean / std_dev of trade returns. Annualised roughly."""
    if len(returns) < 3:
        return 0.0
    mean = sum(returns) / len(returns)
    variance = sum((r - mean) ** 2 for r in returns) / len(returns)
    std = math.sqrt(variance) if variance > 0 else 0.0
    if std == 0:
        return 0.0
    # Annualise assuming ~20 trades per year (rough for weather prediction markets)
    return round((mean / std) * math.sqrt(20), 3)


def compute(
    trade_returns: list[float],    # % P&L per closed trade
    trade_outcomes: list[bool],    # True = win, False = loss
    risk_state,
    total_signals_evaluated: int,
    correctly_classified: int,
    correct_direction: int,
    wallet_confirmed_count: int,
    limitations: list[str],
    data_quality_notes: list[str],
) -> BacktestMetricsData:

    n_trades = len(trade_returns)
    wins     = sum(1 for w in trade_outcomes if w)
    losses   = n_trades - wins

    win_rate   = (wins / n_trades * 100) if n_trades > 0 else 0.0
    avg_return = (sum(trade_returns) / n_trades) if n_trades > 0 else 0.0
    total_ret  = (risk_state.capital - STARTING_CAPITAL) / STARTING_CAPITAL * 100
    sharpe     = _sharpe(trade_returns)

    m1_acc = (correctly_classified / total_signals_evaluated * 100) if total_signals_evaluated > 0 else 0.0
    m2_dir = (correct_direction / total_signals_evaluated * 100) if total_signals_evaluated > 0 else 0.0
    m4_rate = (wallet_confirmed_count / total_signals_evaluated * 100) if total_signals_evaluated > 0 else 0.0

    # Data quality rating
    # Phase 6D: settlement source VERIFIED for annual_temp → MEDIUM quality even with estimated prices
    # HIGH requires both verified settlement AND real historical entry/exit prices (not yet available)
    settlement_verified_note = any("VERIFIED" in n for n in data_quality_notes)
    if n_trades >= 20 and settlement_verified_note:
        rating = "MEDIUM"   # verified settlement + estimated prices = MEDIUM
    elif n_trades >= 30 and not any("No historical" in l for l in limitations):
        rating = "MEDIUM"
    elif n_trades >= 10:
        rating = "LOW"
    else:
        rating = "INSUFFICIENT"

    # Acceptance criteria (Phase 0 Section 8)
    p_wr  = win_rate >= CRITERIA_WIN_RATE_MIN
    p_dd  = risk_state.max_drawdown_pct * 100 <= CRITERIA_MAX_DRAWDOWN_MAX
    p_sh  = sharpe >= CRITERIA_SHARPE_MIN
    p_sig = total_signals_evaluated >= CRITERIA_MIN_SIGNALS
    p_ks  = risk_state.kill_switch_triggered <= CRITERIA_KILL_SWITCH_MAX
    overall = all([p_wr, p_dd, p_sh, p_sig, p_ks])

    if rating == "INSUFFICIENT" or not p_sig:
        readiness = "INSUFFICIENT_DATA"
    elif overall:
        readiness = "READY_FOR_PAPER"
    elif not p_dd or risk_state.kill_switch_triggered > 2:
        readiness = "FAIL"
    else:
        readiness = "NEEDS_MORE_DATA"

    return BacktestMetricsData(
        total_signals=total_signals_evaluated,
        total_trades=n_trades,
        winning_trades=wins,
        losing_trades=losses,
        skipped_trades=risk_state.trades_blocked_exposure + risk_state.trades_blocked_daily_stop,
        total_return_pct=round(total_ret, 3),
        win_rate_pct=round(win_rate, 2),
        avg_return_per_trade_pct=round(avg_return, 3),
        max_drawdown_pct=round(risk_state.max_drawdown_pct * 100, 3),
        sharpe_estimate=sharpe,
        kill_switch_triggers=risk_state.kill_switch_triggered,
        daily_stop_triggers=risk_state.trades_blocked_daily_stop,
        module1_accuracy_pct=round(m1_acc, 2),
        module2_direction_accuracy_pct=round(m2_dir, 2),
        module4_confirmation_rate_pct=round(m4_rate, 2),
        data_quality_rating=rating,
        data_quality_notes=data_quality_notes,
        limitations=limitations,
        pass_win_rate=p_wr,
        pass_max_drawdown=p_dd,
        pass_sharpe=p_sh,
        pass_min_signals=p_sig,
        pass_kill_switch=p_ks,
        overall_pass=overall,
        readiness=readiness,
    )
