# AUDUSD Optimization Report

Trials run: 36. Valid after anti-overfitting filters: 23.

## Baseline vs Optimized
| Result | Return % | Win % | PF | Max DD % | Sharpe | Score |
|---|---|---|---|---|---|---|
| OANDA baseline | 122.57 | 52.90 | 2.31 | -5.73 | 6.41 | 1.81 |
| Best by score | 123.91 | 52.94 | 2.71 | -12.10 | 7.41 | 2.06 |
| Best by return | 123.91 | 52.94 | 2.71 | -12.10 | 7.41 | 2.06 |

## Top 5 Trials By Composite Score
| Trial | Model | TF | Conf | RR | ATR | Return % | Trades | Win % | PF | DD % | Sharpe | Score |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 10 | conservative_2m | M5 | 0.65 | 2.50 | 1.50 | 123.91 | 51 | 52.94 | 2.71 | -12.10 | 7.41 | 2.06 |
| 17 | xgb_weight_2m | M5 | 0.68 | 2.50 | 2.00 | 117.54 | 51 | 50.98 | 2.57 | -9.68 | 6.90 | 1.90 |
| 9 | conservative_2m | M5 | 0.62 | 2.00 | 1.00 | 116.95 | 61 | 54.10 | 2.44 | -13.39 | 6.84 | 1.87 |
| 12 | conservative_2m | M5 | 0.70 | 3.00 | 1.50 | 94.83 | 36 | 47.22 | 2.63 | -11.32 | 6.94 | 1.82 |
| 31 | class_weight_3m | M5 | 0.55 | 1.50 | 1.00 | 60.21 | 44 | 59.09 | 2.11 | -8.87 | 5.94 | 1.75 |

## Winning Settings
- Confidence threshold: 0.65
- Risk-reward: 1:2.5
- ATR stop multiplier: 1.5x
- Training window: 2 months
- Timeframe: M5
- Model setup: conservative_2m with XGB weight 1.0 and RF weight 1.0

Portfolio recommendation: **MAYBE**.
