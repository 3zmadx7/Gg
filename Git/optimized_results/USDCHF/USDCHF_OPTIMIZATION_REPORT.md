# USDCHF Optimization Report

Trials run: 36. Valid after anti-overfitting filters: 6.

## Baseline vs Optimized
| Result | Return % | Win % | PF | Max DD % | Sharpe | Score |
|---|---|---|---|---|---|---|
| OANDA baseline | 16.89 | 39.50 | 1.24 | -27.52 | 1.64 | 0.38 |
| Best by score | 69.39 | 51.61 | 2.54 | -12.40 | 6.88 | 1.88 |
| Best by return | 79.54 | 58.06 | 2.02 | -15.65 | 5.53 | 1.57 |

## Top 5 Trials By Composite Score
| Trial | Model | TF | Conf | RR | ATR | Return % | Trades | Win % | PF | DD % | Sharpe | Score |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 5 | baseline_2m | M5 | 0.68 | 2.50 | 2.00 | 69.39 | 31 | 51.61 | 2.54 | -12.40 | 6.88 | 1.88 |
| 13 | xgb_weight_2m | M5 | 0.55 | 1.50 | 1.00 | 76.54 | 58 | 58.62 | 2.06 | -12.55 | 5.70 | 1.65 |
| 7 | conservative_2m | M5 | 0.55 | 1.50 | 1.00 | 79.54 | 62 | 58.06 | 2.02 | -15.65 | 5.53 | 1.57 |
| 15 | xgb_weight_2m | M5 | 0.62 | 2.00 | 1.00 | 60.20 | 38 | 52.63 | 2.11 | -15.65 | 5.66 | 1.52 |
| 25 | three_month_3m | M5 | 0.55 | 1.50 | 1.00 | 34.54 | 32 | 56.25 | 1.82 | -10.04 | 4.66 | 1.39 |

## Winning Settings
- Confidence threshold: 0.68
- Risk-reward: 1:2.5
- ATR stop multiplier: 2.0x
- Training window: 2 months
- Timeframe: M5
- Model setup: baseline_2m with XGB weight 1.0 and RF weight 1.0

Portfolio recommendation: **MAYBE**.
