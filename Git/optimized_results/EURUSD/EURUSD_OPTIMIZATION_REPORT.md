# EURUSD Optimization Report

Trials run: 36. Valid after anti-overfitting filters: 16.

## Baseline vs Optimized
| Result | Return % | Win % | PF | Max DD % | Sharpe | Score |
|---|---|---|---|---|---|---|
| OANDA baseline | 50.37 | 43.10 | 1.51 | -9.45 | 3.08 | 0.86 |
| Best by score | 51.99 | 56.00 | 2.62 | -7.64 | 7.46 | 2.14 |
| Best by return | 133.03 | 55.22 | 2.48 | -7.27 | 7.04 | 2.00 |

## Top 5 Trials By Composite Score
| Trial | Model | TF | Conf | RR | ATR | Return % | Trades | Win % | PF | DD % | Sharpe | Score |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 27 | three_month_3m | M5 | 0.62 | 2.00 | 1.00 | 51.99 | 25 | 56.00 | 2.62 | -7.64 | 7.46 | 2.14 |
| 22 | rf_weight_2m | M5 | 0.65 | 2.50 | 1.50 | 84.00 | 35 | 51.43 | 2.65 | -6.34 | 7.26 | 2.02 |
| 8 | conservative_2m | M5 | 0.60 | 2.00 | 1.50 | 133.03 | 67 | 55.22 | 2.48 | -7.27 | 7.04 | 2.00 |
| 9 | conservative_2m | M5 | 0.62 | 2.00 | 1.00 | 120.34 | 62 | 54.84 | 2.44 | -7.66 | 6.89 | 1.95 |
| 21 | rf_weight_2m | M5 | 0.62 | 2.00 | 1.00 | 87.00 | 46 | 54.35 | 2.38 | -5.84 | 6.70 | 1.91 |

## Winning Settings
- Confidence threshold: 0.62
- Risk-reward: 1:2.0
- ATR stop multiplier: 1.0x
- Training window: 3 months
- Timeframe: M5
- Model setup: three_month_3m with XGB weight 1.0 and RF weight 1.0

Portfolio recommendation: **YES**.
