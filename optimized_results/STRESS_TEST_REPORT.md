# Stress Test and Monte Carlo Simulation Report

This report summarizes the robustness check for each currency pair's optimized trading strategy.

## Monte Carlo Simulation Results

| Pair | Median Return (%) | 5th Percentile Return (%) | 95th Percentile Return (%) | Worst Drawdown (%) | Prob. of Ruin (%) | Verdict|
|------|- ------------------|- --------------------------|- ---------------------------|- -------------------|- ------------------|- --------|
| USDJPY | 177.88 | 177.88 | 177.88 | -14.14 | 0.00 | ROBUST|
| GBPUSD | 239.56 | 239.56 | 239.56 | -20.70 | 0.00 | ROBUST|
| AUDUSD | 123.91 | 123.91 | 123.91 | -31.78 | 0.20 | ROBUST|
| NZDUSD | 50.51 | 50.51 | 50.51 | -19.27 | 0.00 | ROBUST|
| EURUSD | 51.99 | 51.99 | 51.99 | -21.00 | 0.00 | ROBUST|
| USDCHF | 69.39 | 69.39 | 69.39 | -23.48 | 0.00 | ROBUST|

## Stress Scenario Results

| Pair | Scenario | Return (%) | Max Drawdown (%)|
|------|- ---------|- -----------|- -----------------|
| USDJPY | Bear Scenario | 134.42 | -3.67|
| USDJPY | High Slippage | 177.76 | -3.29|
| USDJPY | Confidence Filter Tightened | 138.02 | -3.47|
| USDJPY | Worst 30 Day Stretch | -1.87 | -3.00|
| GBPUSD | Bear Scenario | 176.34 | -7.31|
| GBPUSD | High Slippage | 239.56 | -6.42|
| GBPUSD | Confidence Filter Tightened | 193.48 | -5.56|
| GBPUSD | Worst 30 Day Stretch | 0.00 | 0.00|
| AUDUSD | Bear Scenario | 84.65 | -12.71|
| AUDUSD | High Slippage | 123.91 | -12.10|
| AUDUSD | Confidence Filter Tightened | 86.62 | -11.52|
| AUDUSD | Worst 30 Day Stretch | -7.71 | -9.00|
| NZDUSD | Bear Scenario | 33.81 | -10.60|
| NZDUSD | High Slippage | 50.51 | -10.04|
| NZDUSD | Confidence Filter Tightened | 46.01 | -9.58|
| NZDUSD | Worst 30 Day Stretch | 0.00 | 0.00|
| EURUSD | Bear Scenario | 35.19 | -8.34|
| EURUSD | High Slippage | 51.99 | -7.64|
| EURUSD | Confidence Filter Tightened | 39.99 | -9.00|
| EURUSD | Worst 30 Day Stretch | -5.01 | -5.01|
| USDCHF | Bear Scenario | 46.51 | -13.04|
| USDCHF | High Slippage | 69.39 | -12.40|
| USDCHF | Confidence Filter Tightened | 55.89 | -14.36|
| USDCHF | Worst 30 Day Stretch | 0.00 | 0.00|

## Robustness Verdicts

| Pair | Verdict|
|------|- --------|
| USDJPY | ROBUST|
| GBPUSD | ROBUST|
| AUDUSD | ROBUST|
| NZDUSD | ROBUST|
| EURUSD | ROBUST|
| USDCHF | ROBUST|

### Verdict Criteria:
- **ROBUST**: 5th percentile return still positive AND probability of ruin < 5%
- **ACCEPTABLE**: 5th percentile return still positive OR ruin probability < 10%
- **FRAGILE**: Everything else
