# EURUSD OANDA 2026 Backtest Report

Generated from `results_oanda/EURUSD/backtest_2026_oanda_20260607_184052.json` after running `python3 pipeline_oanda_EURUSD.py`.

## Backtest Metrics

| Metric | EURUSD |
|---|---:|
| Source | OANDA |
| Instrument | EUR_USD |
| Model version | v1_M5 |
| Test period | 2026-03-01 to 2026-05-31 |
| Initial balance | $10,000.00 |
| Final balance | $15,036.89 |
| Total return | +50.37% |
| Net profit | $+5,036.89 |
| Total trades | 58 |
| Win rate | 43.1% |
| Winning trades | 25 |
| Losing trades | 33 |
| Profit factor | 1.51 |
| Avg win | $600.00 |
| Avg loss | $-301.91 |
| Expectancy | $+86.84 |
| Max drawdown | -9.45% |
| Sharpe ratio | 3.08 |
| Sortino ratio | 41.76 |
| Take-profit exits | 25 |
| Stop-loss exits | 32 |
| End-of-data exits | 1 |

## First 10 Trades

| # | Entry time | Direction | Entry | Exit | Exit reason | Profit | Confidence |
|---:|---|---|---:|---:|---|---:|---:|
| 1 | 2026-03-02 15:00:00 | SELL | 1.17162 | 1.16562 | take_profit | $+600.00 | 0.857 |
| 2 | 2026-03-03 08:20:00 | BUY | 1.16308 | 1.16008 | stop_loss | $-300.00 | 0.611 |
| 3 | 2026-03-03 09:45:00 | BUY | 1.16008 | 1.15708 | stop_loss | $-300.00 | 0.708 |
| 4 | 2026-03-03 14:25:00 | BUY | 1.15756 | 1.15456 | stop_loss | $-300.00 | 0.638 |
| 5 | 2026-03-03 15:10:00 | BUY | 1.15490 | 1.16090 | take_profit | $+600.00 | 0.704 |
| 6 | 2026-03-04 06:00:00 | BUY | 1.15908 | 1.16508 | take_profit | $+600.00 | 0.725 |
| 7 | 2026-03-04 11:25:00 | BUY | 1.16444 | 1.16144 | stop_loss | $-300.00 | 0.686 |
| 8 | 2026-03-05 09:00:00 | BUY | 1.16072 | 1.15772 | stop_loss | $-300.00 | 0.755 |
| 9 | 2026-03-05 15:35:00 | BUY | 1.15707 | 1.15407 | stop_loss | $-300.00 | 0.611 |
| 10 | 2026-03-09 05:00:00 | BUY | 1.15302 | 1.15902 | take_profit | $+600.00 | 0.681 |

## Last 10 Trades

| # | Entry time | Direction | Entry | Exit | Exit reason | Profit | Confidence |
|---:|---|---|---:|---:|---|---:|---:|
| 49 | 2026-05-01 12:00:00 | BUY | 1.17522 | 1.17222 | stop_loss | $-300.00 | 0.606 |
| 50 | 2026-05-04 12:00:00 | BUY | 1.16974 | 1.17574 | take_profit | $+600.00 | 0.776 |
| 51 | 2026-05-06 09:05:00 | BUY | 1.17602 | 1.17302 | stop_loss | $-300.00 | 0.622 |
| 52 | 2026-05-08 08:10:00 | BUY | 1.17448 | 1.17148 | stop_loss | $-300.00 | 0.611 |
| 53 | 2026-05-14 14:15:00 | SELL | 1.16978 | 1.16378 | take_profit | $+600.00 | 0.682 |
| 54 | 2026-05-15 09:50:00 | SELL | 1.16257 | 1.16557 | stop_loss | $-300.00 | 0.630 |
| 55 | 2026-05-18 19:05:00 | BUY | 1.16476 | 1.16176 | stop_loss | $-300.00 | 0.684 |
| 56 | 2026-05-19 14:00:00 | SELL | 1.16163 | 1.16463 | stop_loss | $-300.00 | 0.697 |
| 57 | 2026-05-27 14:20:00 | SELL | 1.16444 | 1.16744 | stop_loss | $-300.00 | 0.636 |
| 58 | 2026-05-29 14:55:00 | BUY | 1.16687 | 1.16486 | end_of_data | $-201.00 | 0.654 |

## Notes

- OANDA midpoint M1 data saved to `data/historical_oanda/EURUSD/tf_1.parquet` with 151,950 rows.
- Resampled bars: M5=30,563, M15=10,188, M30=5,094, H1=2,547, H4=659.
- Training used Jan-Feb 2026; backtest used Mar-May 2026; model saved as `models_oanda/model_v1_M5/`.
