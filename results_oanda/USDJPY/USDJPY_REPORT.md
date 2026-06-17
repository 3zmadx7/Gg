# USDJPY OANDA 2026 Backtest Report

Generated from `results_oanda/USDJPY/backtest_2026_oanda_20260607_184304.json` after running `python3 pipeline_oanda_USDJPY.py`.

## Backtest Metrics

| Metric | USDJPY |
|---|---:|
| Source | OANDA |
| Instrument | USD_JPY |
| Model version | v3_M5 |
| Test period | 2026-03-01 to 2026-05-31 |
| Initial balance | $10,000.00 |
| Final balance | $33,891.00 |
| Total return | +238.91% |
| Net profit | $+23,891.00 |
| Total trades | 85 |
| Win rate | 64.7% |
| Winning trades | 55 |
| Losing trades | 30 |
| Profit factor | 3.43 |
| Avg win | $612.94 |
| Avg loss | $-327.35 |
| Expectancy | $+281.07 |
| Max drawdown | -7.14% |
| Sharpe ratio | 9.62 |
| Sortino ratio | 51.42 |
| Take-profit exits | 54 |
| Stop-loss exits | 30 |
| End-of-data exits | 1 |

## First 10 Trades

| # | Entry time | Direction | Entry | Exit | Exit reason | Profit | Confidence |
|---:|---|---|---:|---:|---|---:|---:|
| 1 | 2026-03-02 16:05:00 | SELL | 157.744 | 157.144 | take_profit | $+600.00 | 0.733 |
| 2 | 2026-03-03 00:20:00 | BUY | 157.298 | 157.898 | take_profit | $+600.00 | 0.608 |
| 3 | 2026-03-03 11:30:00 | SELL | 157.942 | 157.342 | take_profit | $+600.00 | 0.859 |
| 4 | 2026-03-04 08:35:00 | SELL | 157.515 | 156.915 | take_profit | $+600.00 | 0.631 |
| 5 | 2026-03-04 10:05:00 | BUY | 156.910 | 156.610 | stop_loss | $-300.00 | 0.688 |
| 6 | 2026-03-05 01:25:00 | BUY | 156.461 | 157.061 | take_profit | $+600.00 | 0.696 |
| 7 | 2026-03-05 07:30:00 | BUY | 157.056 | 157.656 | take_profit | $+600.00 | 0.756 |
| 8 | 2026-03-05 15:00:00 | BUY | 157.416 | 158.016 | take_profit | $+600.00 | 0.723 |
| 9 | 2026-03-06 13:55:00 | SELL | 157.873 | 158.173 | stop_loss | $-300.00 | 0.654 |
| 10 | 2026-03-08 23:30:00 | BUY | 158.236 | 158.836 | take_profit | $+600.00 | 0.634 |

## Last 10 Trades

| # | Entry time | Direction | Entry | Exit | Exit reason | Profit | Confidence |
|---:|---|---|---:|---:|---|---:|---:|
| 76 | 2026-05-06 07:55:00 | SELL | 155.820 | 156.120 | stop_loss | $-300.00 | 0.654 |
| 77 | 2026-05-06 08:35:00 | SELL | 156.185 | 156.485 | stop_loss | $-300.00 | 0.722 |
| 78 | 2026-05-07 01:00:00 | SELL | 156.312 | 156.612 | stop_loss | $-300.00 | 0.775 |
| 79 | 2026-05-08 13:00:00 | SELL | 156.645 | 156.945 | stop_loss | $-300.00 | 0.766 |
| 80 | 2026-05-12 05:25:00 | SELL | 157.668 | 157.068 | take_profit | $+600.00 | 0.605 |
| 81 | 2026-05-12 06:00:00 | BUY | 157.326 | 157.926 | take_profit | $+600.00 | 0.745 |
| 82 | 2026-05-14 13:35:00 | SELL | 158.116 | 157.516 | take_profit | $+600.00 | 0.759 |
| 83 | 2026-05-14 14:30:00 | BUY | 157.920 | 158.520 | take_profit | $+600.00 | 0.751 |
| 84 | 2026-05-19 13:30:00 | SELL | 159.153 | 159.453 | stop_loss | $-300.00 | 0.609 |
| 85 | 2026-05-28 14:00:00 | SELL | 159.478 | 159.365 | end_of_data | $+113.00 | 0.720 |

## Notes

- OANDA midpoint M1 data saved to `data/historical_oanda/USDJPY/tf_1.parquet` with 151,897 rows.
- Resampled bars: M5=30,553, M15=10,188, M30=5,094, H1=2,547, H4=659.
- Training used Jan-Feb 2026; backtest used Mar-May 2026; model saved as `models_oanda/model_v3_M5/`.
- USDJPY used `pip_size=0.01`; trade PnL values are normal dollar-sized values, not fractional pip noise.
