"""
Backtest models — Phase 6.
Stores historical simulation results. No real trading data.
"""
from typing import Optional
from sqlmodel import Field, SQLModel


class BacktestRun(SQLModel, table=True):
    """One record per backtest execution."""
    id: Optional[int] = Field(default=None, primary_key=True)
    run_at: str = ""
    status: str = "running"          # "running" | "ok" | "error"
    strategy_version: str = "v1.0"  # "v1.0" | "v1.1"
    total_signals: int = 0
    total_trades: int = 0
    win_rate_pct: float = 0.0
    total_return_pct: float = 0.0
    max_drawdown_pct: float = 0.0
    data_quality_rating: str = ""    # HIGH | MEDIUM | LOW | INSUFFICIENT
    readiness: str = ""              # READY_FOR_PAPER | NEEDS_MORE_DATA | FAIL | INSUFFICIENT_DATA
    duration_ms: int = 0
    # v1.1 vs v1.0 comparison (stored in v1.1 run)
    v10_win_rate_pct: Optional[float] = None
    v10_total_trades: Optional[int] = None
    v10_direction_accuracy_pct: Optional[float] = None
    safety_note: str = "BACKTEST ONLY — no real trades, no real orders, no paper portfolio."


class BacktestTrade(SQLModel, table=True):
    """One simulated trade record per backtest scenario."""
    id: Optional[int] = Field(default=None, primary_key=True)
    run_id: Optional[int] = Field(default=None, index=True)
    scenario_label: str = ""
    test_year: int = 0
    target_rank: int = 0
    entry_month: int = 0             # months elapsed when signal generated
    market_type: str = "annual_temp"
    signal_side: str = ""            # YES | NO | WATCH
    model_prob: Optional[float] = None
    gap_pp: Optional[float] = None
    entry_price: Optional[float] = None   # estimated
    exit_price: Optional[float] = None    # estimated
    size_usd: float = 0.0
    pnl_usd: float = 0.0
    pnl_pct: float = 0.0
    outcome: str = ""    # win | loss | stop_loss | take_profit | blocked | no_entry_watch
    exit_reason: str = ""
    direction_correct: Optional[bool] = None
    price_quality: str = "estimated"
    notes: Optional[str] = None


class BacktestMetrics(SQLModel, table=True):
    """Aggregate performance metrics for one backtest run."""
    id: Optional[int] = Field(default=None, primary_key=True)
    run_id: Optional[int] = Field(default=None, unique=True)

    # Performance
    total_return_pct: float = 0.0
    win_rate_pct: float = 0.0
    total_trades: int = 0
    winning_trades: int = 0
    losing_trades: int = 0
    skipped_trades: int = 0
    avg_return_per_trade_pct: float = 0.0
    max_drawdown_pct: float = 0.0
    sharpe_estimate: float = 0.0
    kill_switch_triggers: int = 0
    daily_stop_triggers: int = 0

    # Module accuracy
    module1_accuracy_pct: float = 0.0
    module2_direction_accuracy_pct: float = 0.0
    module4_confirmation_rate_pct: float = 0.0

    # Quality & acceptance
    data_quality_rating: str = ""
    data_quality_notes: Optional[str] = None   # JSON list
    limitations: Optional[str] = None           # JSON list
    pass_win_rate: bool = False
    pass_max_drawdown: bool = False
    pass_sharpe: bool = False
    pass_min_signals: bool = False
    pass_kill_switch: bool = False
    overall_pass: bool = False
    readiness: str = ""
    equity_curve: Optional[str] = None   # JSON list of {label, capital, drawdown_pct}
