# NZDUSD Optimization Report

Trials run: 36. Valid after anti-overfitting filters: 8.

## Baseline vs Optimized
| Result | Return % | Win % | PF | Max DD % | Sharpe | Score |
|---|---|---|---|---|---|---|
| OANDA baseline | 62.96 | 48.80 | 2.00 | -13.04 | 5.22 | 1.37 |
| Best by score | 50.51 | 63.33 | 2.53 | -10.04 | 7.46 | 2.25 |
| Best by return | 59.88 | 47.73 | 1.91 | -18.46 | 4.85 | 1.21 |

## Top 5 Trials By Composite Score
| Trial | Model | TF | Conf | RR | ATR | Return % | Trades | Win % | PF | DD % | Sharpe | Score |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 25 | three_month_3m | M5 | 0.55 | 1.50 | 1.00 | 50.51 | 30 | 63.33 | 2.53 | -10.04 | 7.46 | 2.25 |
| 5 | baseline_2m | M5 | 0.68 | 2.50 | 2.00 | 54.90 | 30 | 46.67 | 2.14 | -9.12 | 5.61 | 1.47 |
| 16 | xgb_weight_2m | M5 | 0.65 | 2.50 | 1.50 | 54.90 | 30 | 46.67 | 2.14 | -11.67 | 5.61 | 1.44 |
| 3 | baseline_2m | M5 | 0.62 | 2.00 | 1.00 | 56.96 | 39 | 48.72 | 2.00 | -13.04 | 5.21 | 1.36 |
| 20 | rf_weight_2m | M5 | 0.60 | 2.00 | 1.50 | 59.88 | 44 | 47.73 | 1.91 | -18.46 | 4.85 | 1.21 |

## Winning Settings
- Confidence threshold: 0.55
- Risk-reward: 1:1.5
- ATR stop multiplier: 1.0x
- Training window: 3 months
- Timeframe: M5
- Model setup: three_month_3m with XGB weight 1.0 and RF weight 1.0

Portfolio recommendation: **YES**.
