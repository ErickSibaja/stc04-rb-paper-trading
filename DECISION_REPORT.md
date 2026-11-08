# STC-04_RB — daily decision audit

Starting with the first daily session processed by the updated simulator,
each new entry in `paper-state/state.json` under `portfolio.history` records:

- `signals.BTCUSDT` and `signals.ETHUSDT`
- `close`: latest fully closed UTC daily candle price
- `sma200`: arithmetic mean of the latest 200 closed daily prices
- `momentum60_pct`: 100 × (latest close / close 60 sessions ago − 1)
- `above_sma200`, `positive_momentum60`, `eligible`
- `reason`: `eligible`, `below_or_equal_sma200`,
  `nonpositive_momentum60`, or
  `below_or_equal_sma200_and_nonpositive_momentum60`
- `reference_prices`: contemporaneously retrieved indicative Spot quotes;
  not exchange fills, not candle closing prices
- `fills`: number of hypothetical portfolio trades

**Historical integrity:** previous sessions are left unchanged; indicators
that were not saved in the original records cannot be certified retroactively
from portfolio state. Duplicate-day preview returns `signals: null` rather
than relabeling newly fetched market data as historical evidence.

The strategy only enters an asset when both trend and momentum are positive.
Each eligible asset targets 25% of portfolio equity, at most 50% total gross.
All trades are virtual; no Binance credentials or order endpoints are used.

The scheduled workflow still requires GitHub environment approval.
