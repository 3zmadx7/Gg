# GBPUSD Optimization Report

Trials run: 36. Valid after anti-overfitting filters: 30.

## Baseline vs Optimized
| Result | Return % | Win % | PF | Max DD % | Sharpe | Score |
|---|---|---|---|---|---|---|
| OANDA baseline | 210.00 | 62.50 | 3.33 | -7.83 | 9.56 | 2.96 |
| Best by score | 239.56 | 63.64 | 4.13 | -6.42 | 11.15 | 3.68 |
| Best by return | 239.56 | 63.64 | 4.13 | -6.42 | 11.15 | 3.68 |

## Top 5 Trials By Composite Score
| Trial | Model | TF | Conf | RR | ATR | Return % | Trades | Win % | PF | DD % | Sharpe | Score |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 11 | conservative_2m | M5 | 0.68 | 2.50 | 2.00 | 239.56 | 66 | 63.64 | 4.13 | -6.42 | 11.15 | 3.68 |
| 34 | class_weight_3m | M5 | 0.65 | 2.50 | 1.50 | 118.50 | 34 | 61.76 | 4.04 | -4.96 | 10.84 | 3.53 |
| 20 | rf_weight_2m | M5 | 0.60 | 2.00 | 1.50 | 192.00 | 71 | 63.38 | 3.46 | -6.52 | 9.90 | 3.12 |
| 21 | rf_weight_2m | M5 | 0.62 | 2.00 | 1.00 | 180.00 | 69 | 62.32 | 3.31 | -7.10 | 9.50 | 2.94 |
| 23 | rf_weight_2m | M5 | 0.68 | 2.50 | 2.00 | 147.00 | 49 | 57.14 | 3.33 | -6.47 | 9.17 | 2.76 |

## Winning Settings
- Confidence threshold: 0.68
- Risk-reward: 1:2.5
- ATR stop multiplier: 2.0x
- Training window: 2 months
- Timeframe: M5
- Model setup: conservative_2m with XGB weight 1.0 and RF weight 1.0

Portfolio recommendation: **YES**.
