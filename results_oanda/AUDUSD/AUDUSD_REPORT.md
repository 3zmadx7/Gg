# AUDUSD OANDA 2026 Backtest Report

Generated from `results_oanda/AUDUSD/backtest_2026_oanda_20260607_184410.json` after running `python3 pipeline_oanda_AUDUSD.py`.

## Backtest Metrics

| Metric | AUDUSD |
|---|---:|
| Source | OANDA |
| Instrument | AUD_USD |
| Model version | v4_M5 |
| Test period | 2026-03-01 to 2026-05-31 |
| Initial balance | $10,000.00 |
| Final balance | $22,256.75 |
| Total return | +122.57% |
| Net profit | $+12,256.75 |
| Total trades | 68 |
| Win rate | 52.9% |
| Winning trades | 36 |
| Losing trades | 32 |
| Profit factor | 2.31 |
| Avg win | $600.00 |
| Avg loss | $-291.98 |
| Expectancy | $+180.25 |
| Max drawdown | -5.73% |
| Sharpe ratio | 6.41 |
| Sortino ratio | 55.06 |
| Take-profit exits | 36 |
| Stop-loss exits | 31 |
| End-of-data exits | 1 |

## First 10 Trades

| # | Entry time | Direction | Entry | Exit | Exit reason | Profit | Confidence |
|---:|---|---|---:|---:|---|---:|---:|
| 1 | 2026-03-02 14:40:00 | BUY | 0.70780 | 0.70480 | stop_loss | $-300.00 | 0.611 |
| 2 | 2026-03-03 10:00:00 | SELL | 0.70454 | 0.69854 | take_profit | $+600.00 | 0.741 |
| 3 | 2026-03-03 14:45:00 | BUY | 0.69825 | 0.69525 | stop_loss | $-300.00 | 0.705 |
| 4 | 2026-03-03 15:10:00 | BUY | 0.69534 | 0.70134 | take_profit | $+600.00 | 0.739 |
| 5 | 2026-03-03 16:10:00 | BUY | 0.70129 | 0.70729 | take_profit | $+600.00 | 0.728 |
| 6 | 2026-03-04 10:45:00 | BUY | 0.70458 | 0.70158 | stop_loss | $-300.00 | 0.667 |
| 7 | 2026-03-05 08:30:00 | BUY | 0.70161 | 0.69861 | stop_loss | $-300.00 | 0.848 |
| 8 | 2026-03-05 16:20:00 | BUY | 0.69852 | 0.70452 | take_profit | $+600.00 | 0.642 |
| 9 | 2026-03-06 08:00:00 | SELL | 0.70402 | 0.69802 | take_profit | $+600.00 | 0.682 |
| 10 | 2026-03-06 14:05:00 | BUY | 0.69796 | 0.70396 | take_profit | $+600.00 | 0.846 |

## Last 10 Trades

| # | Entry time | Direction | Entry | Exit | Exit reason | Profit | Confidence |
|---:|---|---|---:|---:|---|---:|---:|
| 59 | 2026-05-06 11:00:00 | SELL | 0.72646 | 0.72046 | take_profit | $+600.00 | 0.641 |
| 60 | 2026-05-08 08:05:00 | BUY | 0.72230 | 0.71930 | stop_loss | $-300.00 | 0.658 |
| 61 | 2026-05-15 01:30:00 | SELL | 0.71966 | 0.71366 | take_profit | $+600.00 | 0.628 |
| 62 | 2026-05-18 06:00:00 | BUY | 0.71318 | 0.71018 | stop_loss | $-300.00 | 0.754 |
| 63 | 2026-05-19 13:55:00 | SELL | 0.71094 | 0.71394 | stop_loss | $-300.00 | 0.628 |
| 64 | 2026-05-20 14:15:00 | BUY | 0.71410 | 0.71110 | stop_loss | $-300.00 | 0.659 |
| 65 | 2026-05-21 02:00:00 | SELL | 0.71212 | 0.71512 | stop_loss | $-300.00 | 0.769 |
| 66 | 2026-05-21 18:30:00 | SELL | 0.71611 | 0.71011 | take_profit | $+600.00 | 0.766 |
| 67 | 2026-05-28 05:00:00 | BUY | 0.71036 | 0.71636 | take_profit | $+600.00 | 0.715 |
| 68 | 2026-05-29 14:30:00 | BUY | 0.71808 | 0.71803 | end_of_data | $-5.00 | 0.696 |

## Notes

- OANDA midpoint M1 data saved to `data/historical_oanda/AUDUSD/tf_1.parquet` with 151,672 rows.
- Resampled bars: M5=30,560, M15=10,188, M30=5,094, H1=2,547, H4=659.
- Training used Jan-Feb 2026; backtest used Mar-May 2026; model saved as `models_oanda/model_v4_M5/`.
