import json
import numpy as np
import pandas as pd
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Dict, Any

# --- Configuration ---
PAIRS = ["USDJPY", "GBPUSD", "AUDUSD", "NZDUSD", "EURUSD", "USDCHF"]
INITIAL_BALANCE = 10000.0
RUIN_DRAWDOWN_THRESHOLD = -30.0 # in percentage
MONTE_CARLO_RUNS = 1000
RANDOM_SEED = 42
OPTIMIZED_RESULTS_ROOT = Path("optimized_results")

# Pip sizes for different pairs
PIP_SIZES = {
    "USDJPY": 0.01,
    "GBPUSD": 0.0001,
    "AUDUSD": 0.0001,
    "NZDUSD": 0.0001,
    "EURUSD": 0.0001,
    "USDCHF": 0.0001,
}

# --- Helper Functions ---
def load_best_trades(pair: str) -> List[Dict[str, Any]]:
    """Loads the best trades from the best_result.json for a given pair."""
    file_path = OPTIMIZED_RESULTS_ROOT / pair / "best_result.json"
    if not file_path.exists():
        print(f"Error: {file_path} not found.")
        return []
    with open(file_path, 'r') as f:
        data = json.load(f)
    return data.get("trades", [])

def calculate_equity_curve(trades: List[Dict[str, Any]]) -> pd.Series:
    """Calculates the equity curve from a list of trades."""
    balance = INITIAL_BALANCE
    equity_curve = [balance]
    for trade in trades:
        balance += trade["profit"]
        equity_curve.append(balance)
    return pd.Series(equity_curve)

def calculate_metrics(equity_curve: pd.Series) -> Dict[str, float]:
    """Calculates return and max drawdown from an equity curve."""
    final_balance = equity_curve.iloc[-1]
    total_return_pct = (final_balance - INITIAL_BALANCE) / INITIAL_BALANCE * 100

    peak = equity_curve.expanding(min_periods=1).max()
    drawdown = (equity_curve - peak) / peak * 100
    max_drawdown_pct = drawdown.min()
    
    return {
        "total_return_pct": total_return_pct,
        "max_drawdown_pct": max_drawdown_pct,
    }

def run_monte_carlo(trades: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Runs Monte Carlo simulations on the trades."""
    np.random.seed(RANDOM_SEED)
    returns = []
    drawdowns = []
    ruin_count = 0

    for _ in range(MONTE_CARLO_RUNS):
        shuffled_trades = trades.copy()
        np.random.shuffle(shuffled_trades)
        equity_curve = calculate_equity_curve(shuffled_trades)
        metrics = calculate_metrics(equity_curve)
        
        returns.append(metrics["total_return_pct"])
        drawdowns.append(metrics["max_drawdown_pct"])

        if metrics["max_drawdown_pct"] <= RUIN_DRAWDOWN_THRESHOLD:
            ruin_count += 1
    
    return {
        "median_return": np.median(returns),
        "5th_percentile_return": np.percentile(returns, 5),
        "95th_percentile_return": np.percentile(returns, 95),
        "worst_drawdown": np.min(drawdowns),
        "probability_of_ruin": (ruin_count / MONTE_CARLO_RUNS) * 100,
    }

def simulate_modified_trades(original_trades: List[Dict[str, Any]], pair: str, modification_type: str) -> Dict[str, float]:
    """Simulates trades with specific modifications."""
    modified_trades = []
    pip_size = PIP_SIZES[pair]

    if modification_type == "bear_scenario":
        for trade in original_trades:
            new_trade = trade.copy()
            if new_trade["profit"] > 0:
                new_trade["profit"] *= 0.8 # Reduce winning trades by 20%
            modified_trades.append(new_trade)
    elif modification_type == "high_slippage":
        for trade in original_trades:
            new_trade = trade.copy()
            # Add 2-pip cost to every trade. Profit is in currency, so convert pips to currency.
            # Assuming 10 units per pip for calculation (standard lot size for Oanda is 100,000 units, 1 unit = $1)
            # For simplicity, let's assume a fixed cost per trade in USD.
            # Let's assume a 2-pip cost is $20 per standard lot, and scale by volume.
            # The `volume` in the trade object is likely in lots (e.g., 0.1 for mini lot, 1.0 for standard).
            # The profit calculation in optimize_oanda.py is:
            # pnl = (sl - position["entry"]) / pip_size * vol * 10
            # So, vol * 10 is the equivalent of units.
            # A 2-pip cost would be 2 * pip_size * (vol * 10)
            cost_per_trade = 2 * pip_size * new_trade["volume"] * 10 # 2 pips * pip_value_per_unit * units
            new_trade["profit"] -= cost_per_trade
            modified_trades.append(new_trade)
    elif modification_type == "confidence_filter_tightened":
        # Sort trades by confidence and remove bottom 20%
        sorted_trades = sorted(original_trades, key=lambda x: x.get("confidence", 0.0))
        num_to_remove = int(len(sorted_trades) * 0.20)
        modified_trades = sorted_trades[num_to_remove:]
    else:
        modified_trades = original_trades # Default for worst 30-day stretch, handled differently

    equity_curve = calculate_equity_curve(modified_trades)
    return calculate_metrics(equity_curve)

def find_worst_30_day_stretch(trades: List[Dict[str, Any]]) -> Dict[str, float]:
    """Finds the worst consecutive 30-day period in the backtest."""
    if not trades:
        return {"total_return_pct": 0.0, "max_drawdown_pct": 0.0}

    # Ensure trades are sorted by entry_time
    sorted_trades = sorted(trades, key=lambda x: datetime.fromisoformat(x["entry_time"].replace('Z', '+00:00')))

    max_loss = 0.0
    worst_stretch_return = 0.0
    worst_stretch_drawdown = 0.0

    for i in range(len(sorted_trades)):
        start_time = datetime.fromisoformat(sorted_trades[i]["entry_time"].replace('Z', '+00:00'))
        end_time_window = start_time + timedelta(days=30)
        
        current_stretch_trades = []
        for j in range(i, len(sorted_trades)):
            trade_time = datetime.fromisoformat(sorted_trades[j]["entry_time"].replace('Z', '+00:00'))
            if trade_time < end_time_window:
                current_stretch_trades.append(sorted_trades[j])
            else:
                break
        
        if current_stretch_trades:
            equity_curve = calculate_equity_curve(current_stretch_trades)
            metrics = calculate_metrics(equity_curve)
            
            # We are looking for the worst return in a 30-day window
            if metrics["total_return_pct"] < worst_stretch_return:
                worst_stretch_return = metrics["total_return_pct"]
                worst_stretch_drawdown = metrics["max_drawdown_pct"]

    return {"total_return_pct": worst_stretch_return, "max_drawdown_pct": worst_stretch_drawdown}


def calculate_robustness_verdict(mc_results: Dict[str, Any]) -> str:
    """Determines the robustness verdict based on Monte Carlo results."""
    fifth_percentile_positive = mc_results["5th_percentile_return"] > 0
    ruin_prob_low = mc_results["probability_of_ruin"] < 5
    ruin_prob_medium = mc_results["probability_of_ruin"] < 10

    if fifth_percentile_positive and ruin_prob_low:
        return "ROBUST"
    elif fifth_percentile_positive or ruin_prob_medium:
        return "ACCEPTABLE"
    else:
        return "FRAGILE"

def format_table(headers: List[str], rows: List[List[Any]]) -> str:
    """Formats data into a Markdown table."""
    header_line = "| " + " | ".join(headers) + "|"
    separator_line = "|-" + "-|- ".join(['-' * len(h) for h in headers]) + "-|"
    
    body_lines = []
    for row in rows:
        body_lines.append("| " + " | ".join(map(str, row)) + "|")
    
    return "\n".join([header_line, separator_line] + body_lines)

def main():
    all_mc_results = {}
    all_stress_results = {}
    all_verdicts = {}

    print("--- Running Stress Test and Monte Carlo Simulations ---")

    for pair in PAIRS:
        print(f"\nProcessing {pair}...")
        trades = load_best_trades(pair)
        if not trades:
            print(f"Skipping {pair} due to no trades found.")
            continue

        # Monte Carlo Simulation
        mc_results = run_monte_carlo(trades)
        all_mc_results[pair] = mc_results
        all_verdicts[pair] = calculate_robustness_verdict(mc_results)

        print(f"  Monte Carlo Results for {pair}:")
        print(f"    Median Return: {mc_results['median_return']:.2f}%")
        print(f"    5th Percentile Return: {mc_results['5th_percentile_return']:.2f}%")
        print(f"    95th Percentile Return: {mc_results['95th_percentile_return']:.2f}%")
        print(f"    Worst Drawdown: {mc_results['worst_drawdown']:.2f}%")
        print(f"    Probability of Ruin: {mc_results['probability_of_ruin']:.2f}%")
        print(f"    Robustness Verdict: {all_verdicts[pair]}")

        # Stress Scenarios
        stress_results = {}
        stress_results["bear_scenario"] = simulate_modified_trades(trades, pair, "bear_scenario")
        stress_results["high_slippage"] = simulate_modified_trades(trades, pair, "high_slippage")
        stress_results["confidence_filter_tightened"] = simulate_modified_trades(trades, pair, "confidence_filter_tightened")
        stress_results["worst_30_day_stretch"] = find_worst_30_day_stretch(trades)
        all_stress_results[pair] = stress_results

        print(f"  Stress Scenarios for {pair}:")
        for scenario, metrics in stress_results.items():
            print(f"    {scenario.replace('_', ' ').title()}: Return {metrics['total_return_pct']:.2f}%, Drawdown {metrics['max_drawdown_pct']:.2f}%")

    # Generate Report
    report_path = OPTIMIZED_RESULTS_ROOT / "STRESS_TEST_REPORT.md"
    with open(report_path, 'w') as f:
        f.write("# Stress Test and Monte Carlo Simulation Report\n\n")
        f.write("This report summarizes the robustness check for each currency pair's optimized trading strategy.\n\n")

        f.write("## Monte Carlo Simulation Results\n\n")
        mc_headers = ["Pair", "Median Return (%)", "5th Percentile Return (%)", "95th Percentile Return (%)", "Worst Drawdown (%)", "Prob. of Ruin (%)", "Verdict"]
        mc_rows = []
        for pair in PAIRS:
            if pair in all_mc_results:
                res = all_mc_results[pair]
                mc_rows.append([
                    pair,
                    f"{res['median_return']:.2f}",
                    f"{res['5th_percentile_return']:.2f}",
                    f"{res['95th_percentile_return']:.2f}",
                    f"{res['worst_drawdown']:.2f}",
                    f"{res['probability_of_ruin']:.2f}",
                    all_verdicts[pair]
                ])
        f.write(format_table(mc_headers, mc_rows))
        f.write("\n\n")

        f.write("## Stress Scenario Results\n\n")
        stress_headers = ["Pair", "Scenario", "Return (%)", "Max Drawdown (%)"]
        stress_rows = []
        for pair in PAIRS:
            if pair in all_stress_results:
                for scenario, metrics in all_stress_results[pair].items():
                    stress_rows.append([
                        pair,
                        scenario.replace('_', ' ').title(),
                        f"{metrics['total_return_pct']:.2f}",
                        f"{metrics['max_drawdown_pct']:.2f}"
                    ])
        f.write(format_table(stress_headers, stress_rows))
        f.write("\n\n")

        f.write("## Robustness Verdicts\n\n")
        verdict_headers = ["Pair", "Verdict"]
        verdict_rows = []
        for pair in PAIRS:
            if pair in all_verdicts:
                verdict_rows.append([pair, all_verdicts[pair]])
        f.write(format_table(verdict_headers, verdict_rows))
        f.write("\n\n")
        f.write("### Verdict Criteria:\n")
        f.write("- **ROBUST**: 5th percentile return still positive AND probability of ruin < 5%\n")
        f.write("- **ACCEPTABLE**: 5th percentile return still positive OR ruin probability < 10%\n")
        f.write("- **FRAGILE**: Everything else\n")

    print(f"\nStress test report generated at {report_path}")

    # Update AGENT_MEMORY.md
    append_memory_log()

def append_memory_log():
    log_entry = f"""
### Session 10 — {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')} (Stress Test and Monte Carlo Simulation)
**Agent:** Replit Agent
**Work done:**
- Created `stress_test.py` to perform robustness checks.
- Implemented Monte Carlo simulations (1,000 runs) for all 6 pairs using optimized trade data.
- Implemented four stress scenarios for all 6 pairs:
  - Bear scenario (20% reduction in winning trades)
  - High slippage (2-pip cost per trade)
  - Confidence filter tightened (removed bottom 20% of trades by confidence)
  - Worst 30-day stretch analysis
- Generated `optimized_results/STRESS_TEST_REPORT.md` with detailed results and robustness verdicts.
- Printed console summaries for each pair.

**Files created/modified:**
- `stress_test.py` (new)
- `optimized_results/STRESS_TEST_REPORT.md` (new)
- `AGENT_MEMORY.md` (modified)

**Key Results:**
(See `optimized_results/STRESS_TEST_REPORT.md` for full details)

**What remains:**
- Update the session history table in `replit.md`.
"""
    with open("AGENT_MEMORY.md", "a") as f:
        f.write(log_entry)
    print("\nAGENT_MEMORY.md updated with Session 10 log.")

if __name__ == "__main__":
    main()