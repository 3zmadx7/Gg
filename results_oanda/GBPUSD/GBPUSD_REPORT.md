# GBPUSD OANDA 2026 Backtest Report

Generated from `results_oanda/GBPUSD/backtest_2026_oanda_20260607_184159.json` after running `python3 pipeline_oanda_GBPUSD.py`.

## Backtest Metrics

| Metric | GBPUSD |
|---|---:|
| Source | OANDA |
| Instrument | GBP_USD |
| Model version | v2_M5 |
| Test period | 2026-03-01 to 2026-05-31 |
| Initial balance | $10,000.00 |
| Final balance | $31,000.00 |
| Total return | +210.00% |
| Net profit | $+21,000.00 |
| Total trades | 80 |
| Win rate | 62.5% |
| Winning trades | 50 |
| Losing trades | 30 |
| Profit factor | 3.33 |
| Avg win | $600.00 |
| Avg loss | $-300.00 |
| Expectancy | $+262.50 |
| Max drawdown | -7.83% |
| Sharpe ratio | 9.56 |
| Sortino ratio | 0.00 |
| Take-profit exits | 50 |
| Stop-loss exits | 30 |
| End-of-data exits | 0 |

## First 10 Trades

| # | Entry time | Direction | Entry | Exit | Exit reason | Profit | Confidence |
|---:|---|---|---:|---:|---|---:|---:|
| 1 | 2026-03-02 15:00:00 | SELL | 1.34094 | 1.33494 | take_profit | $+600.00 | 0.698 |
| 2 | 2026-03-03 11:15:00 | BUY | 1.32648 | 1.33248 | take_profit | $+600.00 | 0.687 |
| 3 | 2026-03-03 14:30:00 | SELL | 1.33018 | 1.33318 | stop_loss | $-300.00 | 0.654 |
| 4 | 2026-03-03 18:00:00 | BUY | 1.33275 | 1.33875 | take_profit | $+600.00 | 0.763 |
| 5 | 2026-03-04 11:00:00 | BUY | 1.33782 | 1.33482 | stop_loss | $-300.00 | 0.725 |
| 6 | 2026-03-04 19:30:00 | BUY | 1.33603 | 1.33303 | stop_loss | $-300.00 | 0.643 |
| 7 | 2026-03-05 05:30:00 | SELL | 1.33330 | 1.33630 | stop_loss | $-300.00 | 0.650 |
| 8 | 2026-03-05 13:00:00 | SELL | 1.33653 | 1.33053 | take_profit | $+600.00 | 0.604 |
| 9 | 2026-03-05 20:00:00 | BUY | 1.33268 | 1.33868 | take_profit | $+600.00 | 0.701 |
| 10 | 2026-03-06 14:20:00 | BUY | 1.33298 | 1.33898 | take_profit | $+600.00 | 0.601 |

## Last 10 Trades

| # | Entry time | Direction | Entry | Exit | Exit reason | Profit | Confidence |
|---:|---|---|---:|---:|---|---:|---:|
| 71 | 2026-05-12 08:10:00 | BUY | 1.35036 | 1.34736 | stop_loss | $-300.00 | 0.672 |
| 72 | 2026-05-14 16:05:00 | SELL | 1.34735 | 1.34135 | take_profit | $+600.00 | 0.646 |
| 73 | 2026-05-15 10:35:00 | BUY | 1.33697 | 1.33397 | stop_loss | $-300.00 | 0.618 |
| 74 | 2026-05-15 14:00:00 | BUY | 1.33386 | 1.33086 | stop_loss | $-300.00 | 0.607 |
| 75 | 2026-05-18 06:00:00 | BUY | 1.33264 | 1.33864 | take_profit | $+600.00 | 0.648 |
| 76 | 2026-05-18 14:00:00 | BUY | 1.33864 | 1.34464 | take_profit | $+600.00 | 0.628 |
| 77 | 2026-05-19 13:30:00 | BUY | 1.33903 | 1.34503 | take_profit | $+600.00 | 0.613 |
| 78 | 2026-05-21 07:00:00 | SELL | 1.34354 | 1.34654 | stop_loss | $-300.00 | 0.646 |
| 79 | 2026-05-26 14:30:00 | SELL | 1.34641 | 1.34041 | take_profit | $+600.00 | 0.683 |
| 80 | 2026-05-28 14:00:00 | BUY | 1.34102 | 1.34702 | take_profit | $+600.00 | 0.800 |

## Notes

- OANDA midpoint M1 data saved to `data/historical_oanda/GBPUSD/tf_1.parquet` with 152,068 rows.
- Resampled bars: M5=30,559, M15=10,188, M30=5,094, H1=2,547, H4=659.
- Training used Jan-Feb 2026; backtest used Mar-May 2026; model saved as `models_oanda/model_v2_M5/`.
- Sortino ratio is affected by the known display/math edge case noted in the technical spec; use return, drawdown, profit factor, and Sharpe for comparison.
