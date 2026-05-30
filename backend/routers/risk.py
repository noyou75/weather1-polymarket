"""Risk monitor router — stub. Live kill switch enforced in Phase 7."""
from fastapi import APIRouter

router = APIRouter(prefix="/risk", tags=["Risk"])


@router.get("/state", summary="Current risk engine state")
def risk_state():
    return {
        "status": "GREEN",
        "starting_capital": 100.00,
        "current_capital": 102.04,
        "drawdown_usd": 0.00,
        "drawdown_pct": 0.00,
        "drawdown_limit_pct": 15.0,
        "daily_loss_usd": 0.00,
        "daily_loss_limit_usd": 7.00,
        "open_exposure_usd": 5.00,
        "max_exposure_usd": 35.00,
        "kill_switch_active": False,
        "daily_soft_stop_active": False,
        "positions_near_stop": 0,
        "data_source": "mock",
    }


@router.get("/rules", summary="All active risk rules")
def risk_rules():
    return {
        "position_sizing": {
            "default_size_usd": 2.00,
            "max_size_usd": 5.00,
            "elevated_size_usd": 3.00,
            "elevated_condition": "Module 1+2 agree AND Module 4 confirms",
        },
        "exposure_limits": {
            "max_total_exposure_usd": 35.00,
            "max_per_market_type_global_temp_usd": 15.00,
            "max_per_market_type_city_usd": 10.00,
            "max_per_single_market_usd": 5.00,
        },
        "loss_limits": {
            "daily_soft_stop_usd": 7.00,
            "portfolio_kill_switch_usd": 15.00,
            "stop_loss_per_position_pct": 15.0,
        },
        "take_profit": {
            "tier1_pct": 10,
            "tier1_action": "close 50%",
            "tier2_pct": 20,
            "tier2_action": "close additional 25%",
            "tier3_pct": 40,
            "tier3_action": "close remaining",
        },
        "resolution_rule": "48h before resolution = re-evaluation checkpoint (not forced close)",
        "data_source": "static_config",
    }
