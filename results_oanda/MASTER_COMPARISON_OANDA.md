# OANDA Master Comparison

All six runs used OANDA midpoint M1 data, Jan-Feb 2026 training, and Mar-May 2026 backtesting.

| Pair | Model | Final balance | Return | Net profit | Trades | Win rate | Profit factor | Max drawdown | Sharpe | Sortino |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| EURUSD | v1_M5 | $15,036.89 | +50.37% | $+5,036.89 | 58 | 43.1% | 1.51 | -9.45% | 3.08 | 41.76 |
| GBPUSD | v2_M5 | $31,000.00 | +210.00% | $+21,000.00 | 80 | 62.5% | 3.33 | -7.83% | 9.56 | 0.00 |
| USDJPY | v3_M5 | $33,891.00 | +238.91% | $+23,891.00 | 85 | 64.7% | 3.43 | -7.14% | 9.62 | 51.42 |
| AUDUSD | v4_M5 | $22,256.75 | +122.57% | $+12,256.75 | 68 | 52.9% | 2.31 | -5.73% | 6.41 | 55.06 |
| USDCHF | v5_M5 | $11,689.00 | +16.89% | $+1,689.00 | 38 | 39.5% | 1.24 | -27.52% | 1.64 | 12412674218037380.00 |
| NZDUSD | v6_M5 | $16,296.00 | +62.96% | $+6,296.00 | 43 | 48.8% | 2.00 | -13.04% | 5.22 | 37.70 |

## Ranking

1. USDJPY: +238.91% return, PF 3.43, DD -7.14%
2. GBPUSD: +210.00% return, PF 3.33, DD -7.83%
3. AUDUSD: +122.57% return, PF 2.31, DD -5.73%
4. NZDUSD: +62.96% return, PF 2.00, DD -13.04%
5. EURUSD: +50.37% return, PF 1.51, DD -9.45%
6. USDCHF: +16.89% return, PF 1.24, DD -27.52%

Note: USDCHF Sortino is affected by the known Sortino display/math edge case.
