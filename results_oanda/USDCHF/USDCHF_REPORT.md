# USDCHF OANDA 2026 Backtest Report

Generated from `results_oanda/USDCHF/backtest_2026_oanda_20260607_184515.json` after running `python3 pipeline_oanda_USDCHF.py`.

## Backtest Metrics

| Metric | USDCHF |
|---|---:|
| Source | OANDA |
| Instrument | USD_CHF |
| Model version | v5_M5 |
| Test period | 2026-03-01 to 2026-05-31 |
| Initial balance | $10,000.00 |
| Final balance | $11,689.00 |
| Total return | +16.89% |
| Net profit | $+1,689.00 |
| Total trades | 38 |
| Win rate | 39.5% |
| Winning trades | 15 |
| Losing trades | 23 |
| Profit factor | 1.24 |
| Avg win | $572.60 |
| Avg loss | $-300.00 |
| Expectancy | $+44.45 |
| Max drawdown | -27.52% |
| Sharpe ratio | 1.64 |
| Sortino ratio | 12412674218037380.00 |
| Take-profit exits | 14 |
| Stop-loss exits | 23 |
| End-of-data exits | 1 |

## First 10 Trades

| # | Entry time | Direction | Entry | Exit | Exit reason | Profit | Confidence |
|---:|---|---|---:|---:|---|---:|---:|
| 1 | 2026-03-02 15:00:00 | BUY | 0.77825 | 0.78425 | take_profit | $+600.00 | 0.814 |
| 2 | 2026-03-03 08:30:00 | BUY | 0.78356 | 0.78056 | stop_loss | $-300.00 | 0.681 |
| 3 | 2026-03-04 06:00:00 | SELL | 0.78235 | 0.77635 | take_profit | $+600.00 | 0.754 |
| 4 | 2026-03-06 18:20:00 | SELL | 0.77645 | 0.77945 | stop_loss | $-300.00 | 0.608 |
| 5 | 2026-03-09 05:05:00 | SELL | 0.78004 | 0.78304 | stop_loss | $-300.00 | 0.622 |
| 6 | 2026-03-12 13:20:00 | BUY | 0.78248 | 0.78848 | take_profit | $+600.00 | 0.676 |
| 7 | 2026-03-13 09:05:00 | SELL | 0.78822 | 0.79122 | stop_loss | $-300.00 | 0.748 |
| 8 | 2026-03-16 07:00:00 | BUY | 0.79091 | 0.78791 | stop_loss | $-300.00 | 0.644 |
| 9 | 2026-03-16 11:30:00 | SELL | 0.78804 | 0.79104 | stop_loss | $-300.00 | 0.636 |
| 10 | 2026-03-18 18:30:00 | BUY | 0.79075 | 0.78775 | stop_loss | $-300.00 | 0.751 |

## Last 10 Trades

| # | Entry time | Direction | Entry | Exit | Exit reason | Profit | Confidence |
|---:|---|---|---:|---:|---|---:|---:|
| 29 | 2026-04-28 08:00:00 | SELL | 0.78936 | 0.79236 | stop_loss | $-300.00 | 0.769 |
| 30 | 2026-04-30 08:20:00 | SELL | 0.78991 | 0.78391 | take_profit | $+600.00 | 0.822 |
| 31 | 2026-04-30 12:50:00 | SELL | 0.78372 | 0.77772 | take_profit | $+600.00 | 0.639 |
| 32 | 2026-05-06 11:30:00 | BUY | 0.77788 | 0.78388 | take_profit | $+600.00 | 0.621 |
| 33 | 2026-05-15 10:00:00 | SELL | 0.78596 | 0.78896 | stop_loss | $-300.00 | 0.686 |
| 34 | 2026-05-19 14:00:00 | BUY | 0.78890 | 0.78590 | stop_loss | $-300.00 | 0.772 |
| 35 | 2026-05-20 16:20:00 | SELL | 0.78746 | 0.78146 | take_profit | $+600.00 | 0.612 |
| 36 | 2026-05-25 13:00:00 | BUY | 0.78106 | 0.78706 | take_profit | $+600.00 | 0.814 |
| 37 | 2026-05-28 12:00:00 | SELL | 0.78906 | 0.78306 | take_profit | $+600.00 | 0.732 |
| 38 | 2026-05-29 14:50:00 | BUY | 0.78001 | 0.78190 | end_of_data | $+189.00 | 0.802 |

## Notes

- OANDA midpoint M1 data saved to `data/historical_oanda/USDCHF/tf_1.parquet` with 151,064 rows.
- Resampled bars: M5=30,529, M15=10,186, M30=5,094, H1=2,547, H4=659.
- Training used Jan-Feb 2026; backtest used Mar-May 2026; model saved as `models_oanda/model_v5_M5/`.
- Sortino ratio is affected by the known display/math edge case noted in the technical spec; use return, drawdown, profit factor, and Sharpe for comparison.
