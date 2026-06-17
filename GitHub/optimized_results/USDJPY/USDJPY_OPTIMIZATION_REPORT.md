# USDJPY Optimization Report

Trials run: 36. Valid after anti-overfitting filters: 36.

## Baseline vs Optimized
| Result | Return % | Win % | PF | Max DD % | Sharpe | Score |
|---|---|---|---|---|---|---|
| OANDA baseline | 238.91 | 64.70 | 3.43 | -7.14 | 9.62 | 3.11 |
| Best by score | 177.88 | 78.69 | 5.51 | -3.29 | 14.71 | 5.78 |
| Best by return | 275.01 | 67.67 | 3.09 | -12.37 | 9.19 | 2.89 |

## Top 5 Trials By Composite Score
| Trial | Model | TF | Conf | RR | ATR | Return % | Trades | Win % | PF | DD % | Sharpe | Score |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 25 | three_month_3m | M5 | 0.55 | 1.50 | 1.00 | 177.88 | 61 | 78.69 | 5.51 | -3.29 | 14.71 | 5.78 |
| 21 | rf_weight_2m | M5 | 0.62 | 2.00 | 1.00 | 260.69 | 77 | 71.43 | 4.93 | -2.62 | 13.13 | 4.80 |
| 31 | class_weight_3m | M5 | 0.55 | 1.50 | 1.00 | 172.74 | 65 | 75.38 | 4.57 | -4.62 | 12.83 | 4.68 |
| 20 | rf_weight_2m | M5 | 0.60 | 2.00 | 1.50 | 241.96 | 81 | 66.67 | 3.89 | -3.52 | 10.83 | 3.64 |
| 34 | class_weight_3m | M5 | 0.65 | 2.50 | 1.50 | 130.91 | 37 | 62.16 | 3.97 | -5.81 | 10.30 | 3.44 |

## Winning Settings
- Confidence threshold: 0.55
- Risk-reward: 1:1.5
- ATR stop multiplier: 1.0x
- Training window: 3 months
- Timeframe: M5
- Model setup: three_month_3m with XGB weight 1.0 and RF weight 1.0

Portfolio recommendation: **YES**.
