# STC-04_RB — independent Forex research

Research branch only; main and paper-state are untouched. EURUSD daily, LONG
only. Signal: completed prior day close > SMA200 and momentum60 > 0.
Target exposure 25% virtual equity. Commission 10bps, slippage 5bps,
Dukascopy BID/ASK spread additionally included. USD 10000 virtual start
for each 60/20/20 chronological segment (2025-01 to 2026-09).
Extra 2024 historical data provides SMA200 warmup.

**Not an exact execution replication of the Binance Spot daily simulator:**
Forex uses next session BID/ASK opening quote, has weekends and swap costs.
Swap/rollover omitted, so results are not broker-realistic net performance.
No changes to original live paper-trading workflow, no real orders.
