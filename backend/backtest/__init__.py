"""
Weather1 Backtest Framework — Phase 6.
Historical signal accuracy evaluation using available GISTEMP data.

IMPORTANT LIMITATIONS (always disclosed):
- No historical Polymarket orderbook data available.
- Entry prices are conservatively estimated, not actual historical prices.
- Open-Meteo ERA5 is hindcast (reanalysis), NOT true archived forecast-at-time.
- NASA GISTEMP used as signal data; Polymarket settlement source NOT confirmed.
- City-station temperature backtest requires additional historical price data (not available).
- Results labeled LOW / MEDIUM quality; do not imply guaranteed future performance.

This module generates HISTORICAL ANALYSIS ONLY. No trades. No orders. No portfolio.
"""
