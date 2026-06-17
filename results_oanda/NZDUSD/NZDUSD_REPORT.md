# NZDUSD OANDA 2026 Backtest Report

Generated from `results_oanda/NZDUSD/backtest_2026_oanda_20260607_184619.json` after running `python3 pipeline_oanda_NZDUSD.py`.

## Backtest Metrics

| Metric | NZDUSD |
|---|---:|
| Source | OANDA |
| Instrument | NZD_USD |
| Model version | v6_M5 |
| Test period | 2026-03-01 to 2026-05-31 |
| Initial balance | $10,000.00 |
| Final balance | $16,296.00 |
| Total return | +62.96% |
| Net profit | $+6,296.00 |
| Total trades | 43 |
| Win rate | 48.8% |
| Winning trades | 21 |
| Losing trades | 22 |
| Profit factor | 2.00 |
| Avg win | $600.00 |
| Avg loss | $-286.55 |
| Expectancy | $+146.42 |
| Max drawdown | -13.04% |
| Sharpe ratio | 5.22 |
| Sortino ratio | 37.70 |
| Take-profit exits | 21 |
| Stop-loss exits | 21 |
| End-of-data exits | 1 |

## First 10 Trades

| # | Entry time | Direction | Entry | Exit | Exit reason | Profit | Confidence |
|---:|---|---|---:|---:|---|---:|---:|
| 1 | 2026-03-02 15:00:00 | SELL | 0.59462 | 0.58862 | take_profit | $+600.00 | 0.848 |
| 2 | 2026-03-03 10:00:00 | SELL | 0.58920 | 0.59220 | stop_loss | $-300.00 | 0.703 |
| 3 | 2026-03-04 11:20:00 | SELL | 0.59219 | 0.58619 | take_profit | $+600.00 | 0.649 |
| 4 | 2026-03-06 13:55:00 | BUY | 0.58600 | 0.59200 | take_profit | $+600.00 | 0.714 |
| 5 | 2026-03-09 13:30:00 | SELL | 0.59198 | 0.59498 | stop_loss | $-300.00 | 0.630 |
| 6 | 2026-03-10 14:40:00 | BUY | 0.59500 | 0.59200 | stop_loss | $-300.00 | 0.759 |
| 7 | 2026-03-11 09:05:00 | SELL | 0.59255 | 0.58655 | take_profit | $+600.00 | 0.623 |
| 8 | 2026-03-12 15:15:00 | BUY | 0.58574 | 0.58274 | stop_loss | $-300.00 | 0.645 |
| 9 | 2026-03-13 06:00:00 | SELL | 0.58280 | 0.58580 | stop_loss | $-300.00 | 0.770 |
| 10 | 2026-03-16 14:10:00 | SELL | 0.58567 | 0.57967 | take_profit | $+600.00 | 0.629 |

## Last 10 Trades

| # | Entry time | Direction | Entry | Exit | Exit reason | Profit | Confidence |
|---:|---|---|---:|---:|---|---:|---:|
| 34 | 2026-05-01 15:00:00 | BUY | 0.59156 | 0.58856 | stop_loss | $-300.00 | 0.673 |
| 35 | 2026-05-04 10:45:00 | SELL | 0.58916 | 0.59216 | stop_loss | $-300.00 | 0.736 |
| 36 | 2026-05-06 04:00:00 | BUY | 0.59314 | 0.59014 | stop_loss | $-300.00 | 0.751 |
| 37 | 2026-05-15 01:40:00 | SELL | 0.58894 | 0.58294 | take_profit | $+600.00 | 0.616 |
| 38 | 2026-05-18 01:00:00 | BUY | 0.58242 | 0.58842 | take_profit | $+600.00 | 0.644 |
| 39 | 2026-05-20 16:25:00 | BUY | 0.58690 | 0.58390 | stop_loss | $-300.00 | 0.652 |
| 40 | 2026-05-27 00:50:00 | BUY | 0.58446 | 0.59046 | take_profit | $+600.00 | 0.631 |
| 41 | 2026-05-27 12:35:00 | SELL | 0.59027 | 0.59327 | stop_loss | $-300.00 | 0.606 |
| 42 | 2026-05-28 21:30:00 | BUY | 0.59301 | 0.59901 | take_profit | $+600.00 | 0.667 |
| 43 | 2026-05-29 14:15:00 | BUY | 0.59812 | 0.59808 | end_of_data | $-4.00 | 0.675 |

## Notes

- OANDA midpoint M1 data saved to `data/historical_oanda/NZDUSD/tf_1.parquet` with 151,313 rows.
- Resampled bars: M5=30,561, M15=10,188, M30=5,094, H1=2,547, H4=659.
- Training used Jan-Feb 2026; backtest used Mar-May 2026; model saved as `models_oanda/model_v6_M5/`.
