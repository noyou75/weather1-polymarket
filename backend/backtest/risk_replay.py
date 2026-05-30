"""
Risk rule replay — Phase 6.
Enforces Section 7 risk rules during backtest simulation.
Rules from Phase 0 Section 7 / docs/phase0_plan.md.

No real capital. No real orders. Historical simulation only.
"""
from dataclasses import dataclass, field


# Section 7 risk constants (from Phase 0)
STARTING_CAPITAL    = 100.00
DEFAULT_POSITION    = 2.00
MAX_POSITION        = 5.00
MAX_OPEN_EXPOSURE   = 35.00
DAILY_SOFT_STOP_PCT = 0.07     # 7%
HARD_STOP_PCT       = 0.15     # 15%
STOP_LOSS_PCT       = 0.15     # 15% per-trade stop
TAKE_PROFIT_T1_PCT  = 0.10     # +10% → close 50%
TAKE_PROFIT_T2_PCT  = 0.20     # +20% → close additional 25%
TAKE_PROFIT_T3_PCT  = 0.40     # +40% → close all
RESOLUTION_CHECK_HOURS = 48   # 48h checkpoint


@dataclass
class RiskState:
    capital: float = STARTING_CAPITAL
    open_exposure: float = 0.0
    daily_loss: float = 0.0          # resets each simulated day
    cumulative_pnl: float = 0.0
    peak_capital: float = STARTING_CAPITAL
    max_drawdown_pct: float = 0.0
    daily_stop_triggered: int = 0
    kill_switch_triggered: int = 0
    trades_blocked_exposure: int = 0
    trades_blocked_daily_stop: int = 0
    trades_blocked_kill_switch: int = 0
    # For equity curve
    equity_curve: list = field(default_factory=list)


@dataclass
class TradeDecision:
    allowed: bool
    size_usd: float
    block_reason: str | None    # why blocked, if not allowed


def can_enter_trade(state: RiskState, gap_pp: float | None, wallet_confirmed: bool) -> TradeDecision:
    """Check if a new trade is allowed given current risk state."""
    if state.kill_switch_triggered > 0:
        return TradeDecision(False, 0.0, "Kill switch active")

    if state.daily_loss <= -(STARTING_CAPITAL * DAILY_SOFT_STOP_PCT):
        state.trades_blocked_daily_stop += 1
        return TradeDecision(False, 0.0, "Daily soft stop active")

    if state.open_exposure >= MAX_OPEN_EXPOSURE:
        state.trades_blocked_exposure += 1
        return TradeDecision(False, 0.0, f"Max open exposure ${MAX_OPEN_EXPOSURE} reached")

    # Determine position size
    size = DEFAULT_POSITION
    if gap_pp is not None and abs(gap_pp) >= 12 and wallet_confirmed:
        size = 3.00    # elevated: Module 1+2+4 all aligned
    size = min(size, MAX_POSITION)
    size = min(size, MAX_OPEN_EXPOSURE - state.open_exposure)

    return TradeDecision(True, size, None)


def apply_pnl(state: RiskState, pnl_usd: float, size_usd: float, period_label: str) -> bool:
    """Apply trade P&L to risk state. Returns True if kill switch triggered."""
    state.capital += pnl_usd
    state.open_exposure = max(0.0, state.open_exposure - size_usd)
    state.cumulative_pnl += pnl_usd
    state.daily_loss += min(pnl_usd, 0)  # only track losses for daily stop

    # Update drawdown
    if state.capital > state.peak_capital:
        state.peak_capital = state.capital
    dd = (state.peak_capital - state.capital) / state.peak_capital
    state.max_drawdown_pct = max(state.max_drawdown_pct, dd)

    # Record equity point
    state.equity_curve.append({
        "label": period_label,
        "capital": round(state.capital, 4),
        "drawdown_pct": round(dd * 100, 2),
    })

    # Check kill switch
    total_drawdown = (STARTING_CAPITAL - state.capital) / STARTING_CAPITAL
    if total_drawdown >= HARD_STOP_PCT:
        state.kill_switch_triggered += 1
        return True

    return False


def apply_take_profit(pnl_pct: float, size_usd: float) -> tuple[float, str]:
    """
    Apply take-profit ladder. Returns (fraction_closed, exit_reason).
    Simplified for backtest: uses final resolution as exit.
    """
    if pnl_pct >= TAKE_PROFIT_T3_PCT * 100:
        return 1.0, f"take_profit_t3 (+{pnl_pct:.1f}%)"
    elif pnl_pct >= TAKE_PROFIT_T2_PCT * 100:
        return 0.75, f"take_profit_t2 (+{pnl_pct:.1f}%)"
    elif pnl_pct >= TAKE_PROFIT_T1_PCT * 100:
        return 0.50, f"take_profit_t1 (+{pnl_pct:.1f}%)"
    elif pnl_pct <= -(STOP_LOSS_PCT * 100):
        return 1.0, f"stop_loss ({pnl_pct:.1f}%)"
    return 1.0, f"held_to_resolution ({pnl_pct:+.1f}%)"
