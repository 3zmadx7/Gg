import pandas as pd
import numpy as np
from datetime import timedelta

# --- Configuration and Assumptions ---
CSV_FILE = '/home/runner/workspace/all_trades.csv'
OUTPUT_FILE = '/home/runner/workspace/trading_analysis_report.csv'

# Assumptions for Section 4 (Costs Analysis) - these are estimates as data is not in CSV
ASSUMED_SPREAD_PIPS = {
    'AUDUSD': 1.5, 'EURUSD': 1.2, 'GBPUSD': 1.8,
    'NZDUSD': 1.6, 'USDCHF': 1.7, 'USDJPY': 1.5
}
ASSUMED_COMMISSION_PER_0_05_LOT = 0.7  # $0.7 per 0.05 lot round turn
ASSUMED_SLIPPAGE_PER_0_05_LOT = 0.5    # $0.5 per 0.05 lot

# Base values from observing the provided CSV for 1.0 lot trades
BASE_RISK_1_0_LOT = 300.0
BASE_REWARD_1_0_LOT = 600.0

# --- Helper Functions ---
def calculate_rr(row, base_risk):
    if row['profit'] > 0:
        return row['profit'] / base_risk
    return 0 # Losing trades don't have a positive RR

# --- Main Analysis Script ---
def analyze_trading_data():
    df = pd.read_csv(CSV_FILE)

    # --- Preprocessing ---
    df['entry_time'] = pd.to_datetime(df['entry_time'])
    df['exit_time'] = pd.to_datetime(df['exit_time'])
    df['trade_date'] = df['entry_time'].dt.date
    df['is_win'] = df['profit'] > 0
    df['rr'] = df.apply(lambda row: calculate_rr(row, BASE_RISK_1_0_LOT), axis=1)

    # --- Section 1: Win Rate & RR Distribution ---
    section1_output = []

    # Overall metrics
    total_trades = len(df)
    total_wins = df['is_win'].sum()
    overall_win_rate = (total_wins / total_trades) * 100 if total_trades > 0 else 0
    overall_avg_rr_wins = df[df['is_win']]['rr'].mean()

    # Longest consecutive losing streak overall
    overall_losing_streak = 0
    current_losing_streak = 0
    for is_win in df['is_win']:
        if not is_win:
            current_losing_streak += 1
        else:
            overall_losing_streak = max(overall_losing_streak, current_losing_streak)
            current_losing_streak = 0
    overall_losing_streak = max(overall_losing_streak, current_losing_streak) # Check at the end

    section1_output.append(f"Overall Win Rate: {overall_win_rate:.2f}%")
    section1_output.append(f"Overall Average RR of Winning Trades: {overall_avg_rr_wins:.2f}")
    
    # RR distribution for overall wins
    overall_winning_trades = df[df['is_win']]
    total_winning_trades = len(overall_winning_trades)
    
    rr_1_1_count = (overall_winning_trades['rr'] >= 1).sum()
    rr_1_2_count = (overall_winning_trades['rr'] >= 2).sum()
    rr_1_3_count = (overall_winning_trades['rr'] >= 3).sum()
    rr_1_4_plus_count = (overall_winning_trades['rr'] >= 4).sum()

    section1_output.append(f"% of Overall Wins with RR>=1:1: {(rr_1_1_count / total_winning_trades * 100):.2f}%" if total_winning_trades > 0 else "0.00%")
    section1_output.append(f"% of Overall Wins with RR>=1:2: {(rr_1_2_count / total_winning_trades * 100):.2f}%" if total_winning_trades > 0 else "0.00%")
    section1_output.append(f"% of Overall Wins with RR>=1:3: {(rr_1_3_count / total_winning_trades * 100):.2f}%" if total_winning_trades > 0 else "0.00%")
    section1_output.append(f"% of Overall Wins with RR>=1:4+: {(rr_1_4_plus_count / total_winning_trades * 100):.2f}%" if total_winning_trades > 0 else "0.00%")
    section1_output.append(f"Overall Longest Consecutive Losing Streak: {overall_losing_streak}")

    section1_output.append("\n--- Per Pair Metrics ---")
    for pair, group in df.groupby('symbol'):
        pair_total_trades = len(group)
        pair_wins = group['is_win'].sum()
        pair_win_rate = (pair_wins / pair_total_trades) * 100 if pair_total_trades > 0 else 0
        pair_avg_rr_wins = group[group['is_win']]['rr'].mean()

        pair_losing_streak = 0
        current_losing_streak = 0
        for is_win in group['is_win']:
            if not is_win:
                current_losing_streak += 1
            else:
                pair_losing_streak = max(pair_losing_streak, current_losing_streak)
                current_losing_streak = 0
        pair_losing_streak = max(pair_losing_streak, current_losing_streak)

        section1_output.append(f"\nPair: {pair}")
        section1_output.append(f"  Win Rate: {pair_win_rate:.2f}%")
        section1_output.append(f"  Average RR of Winning Trades: {pair_avg_rr_wins:.2f}")

        pair_winning_trades = group[group['is_win']]
        pair_total_winning_trades = len(pair_winning_trades)
        pair_rr_1_1 = (pair_winning_trades['rr'] >= 1).sum()
        pair_rr_1_2 = (pair_winning_trades['rr'] >= 2).sum()
        pair_rr_1_3 = (pair_winning_trades['rr'] >= 3).sum()
        pair_rr_1_4_plus = (pair_winning_trades['rr'] >= 4).sum()

        section1_output.append(f"  % of Wins with RR>=1:1: {(pair_rr_1_1 / pair_total_winning_trades * 100):.2f}%" if pair_total_winning_trades > 0 else "0.00%")
        section1_output.append(f"  % of Wins with RR>=1:2: {(pair_rr_1_2 / pair_total_winning_trades * 100):.2f}%" if pair_total_winning_trades > 0 else "0.00%")
        section1_output.append(f"  % of Wins with RR>=1:3: {(pair_rr_1_3 / pair_total_winning_trades * 100):.2f}%" if pair_total_winning_trades > 0 else "0.00%")
        section1_output.append(f"  % of Wins with RR>=1:4+: {(pair_rr_1_4_plus / pair_total_winning_trades * 100):.2f}%" if pair_total_winning_trades > 0 else "0.00%")
        section1_output.append(f"  Longest Consecutive Losing Streak: {pair_losing_streak}")

    # --- Section 2: Daily P&L Distribution ---
    section2_output = []

    daily_pnl = df.groupby('trade_date')['profit'].sum().reset_index()
    daily_pnl.columns = ['Date', 'P&L']
    daily_pnl['Date'] = daily_pnl['Date'].astype(str) # Convert date to string for CSV output

    section2_output.append("Daily Net P&L:")
    section2_output.append(daily_pnl.to_csv(index=False, float_format='%.2f'))

    max_daily_loss = daily_pnl['P&L'].min()
    avg_daily_profit = daily_pnl[daily_pnl['P&L'] > 0]['P&L'].mean()
    median_daily_profit = daily_pnl[daily_pnl['P&L'] > 0]['P&L'].median()

    days_0_15 = daily_pnl[(daily_pnl['P&L'] > 0) & (daily_pnl['P&L'] <= 15)].shape[0]
    days_gt_15 = daily_pnl[daily_pnl['P&L'] > 15].shape[0]

    # Max consecutive losing days
    max_consecutive_losing_days = 0
    current_consecutive_losing_days = 0
    for pnl in daily_pnl['P&L']:
        if pnl < 0:
            current_consecutive_losing_days += 1
        else:
            max_consecutive_losing_days = max(max_consecutive_losing_days, current_consecutive_losing_days)
            current_consecutive_losing_days = 0
    max_consecutive_losing_days = max(max_consecutive_losing_days, current_consecutive_losing_days)

    section2_output.append(f"\nMaximum Daily Loss: ${max_daily_loss:.2f}")
    section2_output.append(f"Average Daily Profit (winning days): ${avg_daily_profit:.2f}")
    section2_output.append(f"Median Daily Profit (winning days): ${median_daily_profit:.2f}")
    section2_output.append(f"Number of days with profit $0-$15: {days_0_15}")
    section2_output.append(f"Number of days with profit >$15: {days_gt_15}")
    section2_output.append(f"Maximum Consecutive Losing Days: {max_consecutive_losing_days}")

    # --- Section 3: Simulation with Hard Limits ---
    section3_output = []

    STARTING_BALANCE = 1000
    RISK_PER_TRADE = 5
    REWARD_PER_TRADE = 10
    DAILY_PROFIT_CAP = 15
    DAILY_LOSS_LIMIT = 28
    OVERALL_LOSS_LIMIT = 50 # Account blows if balance drops by $50 from starting

    # Transform original trade P&L to simulation P&L
    # If original profit > 0, it's a win, so simulated P&L is REWARD_PER_TRADE
    # If original profit < 0, it's a loss, so simulated P&L is -RISK_PER_TRADE
    df['sim_pnl'] = df['profit'].apply(lambda p: REWARD_PER_TRADE if p > 0 else -RISK_PER_TRADE)

    balance = STARTING_BALANCE
    daily_balance_progression = []
    days_to_reach_profit_target = None
    max_drawdown_sim = 0
    peak_balance_sim = STARTING_BALANCE
    days_hit_profit_cap = 0
    days_hit_loss_cap = 0
    
    # Group trades by date to simulate day by day
    grouped_by_day = df.groupby('trade_date')

    for current_date, day_trades in grouped_by_day:
        day_pnl_tracker = 0 # Tracks P&L for the current day
        
        for index, trade_row in day_trades.iterrows():
            trade_pnl = trade_row['sim_pnl']

            # Check if daily profit cap or loss limit is hit
            if day_pnl_tracker + trade_pnl >= DAILY_PROFIT_CAP:
                actual_trade_pnl = DAILY_PROFIT_CAP - day_pnl_tracker
                day_pnl_tracker = DAILY_PROFIT_CAP
                days_hit_profit_cap += 1
                # Stop trading for the day
                break 
            elif day_pnl_tracker + trade_pnl <= -DAILY_LOSS_LIMIT:
                actual_trade_pnl = -DAILY_LOSS_LIMIT - day_pnl_tracker
                day_pnl_tracker = -DAILY_LOSS_LIMIT
                days_hit_loss_cap += 1
                # Stop trading for the day
                break
            else:
                actual_trade_pnl = trade_pnl
                day_pnl_tracker += trade_pnl
        
        balance += day_pnl_tracker # Add the day's net P&L to the balance
        
        daily_balance_progression.append({'Date': str(current_date), 'Balance': f"{balance:.2f}"})

        peak_balance_sim = max(peak_balance_sim, balance)
        drawdown_sim = peak_balance_sim - balance
        max_drawdown_sim = max(max_drawdown_sim, drawdown_sim)

        if balance >= STARTING_BALANCE + 100 and days_to_reach_profit_target is None:
            days_to_reach_profit_target = len(daily_balance_progression) # Number of trading days

        if balance <= STARTING_BALANCE - OVERALL_LOSS_LIMIT:
            section3_output.append("Does account reach $100 profit? No (Account blew up)")
            break
    else: # Loop completed without blowing up
        if days_to_reach_profit_target is not None:
            section3_output.append("Does account reach $100 profit? Yes")
            section3_output.append(f"If yes, how many trading days? {days_to_reach_profit_target}")
        else:
            section3_output.append("Does account reach $100 profit? No (Did not reach target)")

    section3_output.append(f"Maximum drawdown during simulation: ${max_drawdown_sim:.2f}")
    section3_output.append(f"Number of days hitting $15 profit cap: {days_hit_profit_cap}")
    section3_output.append(f"Number of days hitting $28 loss cap: {days_hit_loss_cap}")
    
    section3_output.append("\nDaily Balance Progression:")
    balance_df = pd.DataFrame(daily_balance_progression)
    section3_output.append(balance_df.to_csv(index=False))

    # --- Section 4: Costs Analysis (Spread, Commission, Slippage) ---
    section4_output = []

    # Average spread in pips per pair
    section4_output.append("Average Spread in Pips per Pair (Assumed):")
    for pair, spread_pips in ASSUMED_SPREAD_PIPS.items():
        section4_output.append(f"  {pair}: {spread_pips:.2f} pips")

    section4_output.append(f"\nAverage Commission per trade (in $ for 0.05 lot, Assumed): ${ASSUMED_COMMISSION_PER_0_05_LOT:.2f}")
    section4_output.append(f"Estimated Slippage ($ for 0.05 lot, Assumed): ${ASSUMED_SLIPPAGE_PER_0_05_LOT:.2f}")

    # Net average profit per winning trade after costs (for 0.05 lot)
    # Assuming a winning trade for 0.05 lot yields $10 (from simulation context).
    # Calculate total assumed costs for a 0.05 lot trade.
    avg_spread_pips_all_pairs = np.mean(list(ASSUMED_SPREAD_PIPS.values()))
    avg_spread_cost_0_05_lot = avg_spread_pips_all_pairs * 0.5 # 1 pip = $0.5 for 0.05 lot (common for major pairs)
    
    total_costs_per_0_05_lot_trade = avg_spread_cost_0_05_lot + ASSUMED_COMMISSION_PER_0_05_LOT + ASSUMED_SLIPPAGE_PER_0_05_LOT
    
    net_profit_winning_trade_0_05_lot = REWARD_PER_TRADE - total_costs_per_0_05_lot_trade
    
    section4_output.append(f"\nNet Average Profit per Winning Trade after costs (for 0.05 lot, based on $10 reward and assumed costs): ${net_profit_winning_trade_0_05_lot:.2f}")

    if net_profit_winning_trade_0_05_lot > 0:
        section4_output.append("Minimum lot size to have positive net profit after costs: 0.05 lot")
    else:
        section4_output.append("Minimum lot size to have positive net profit after costs: Not achievable with these costs and $10 reward per winning trade (assuming linear scaling of costs).")

    # --- Section 5: Monte Carlo / Bootstrap Probability ---
    section5_output = []

    # For Monte Carlo, we simulate sequences of daily P&L, applying caps within each day.
    # We need to generate a list of possible daily P&L outcomes *after* applying caps.
    # This is complex to do by resampling individual trades and then applying daily caps.
    # A simpler approach for MC is to resample the *historical daily P&L outcomes* (after caps).
    # Let's re-run the daily simulation to get the actual daily P&L values that occurred under the hard limits.
    
    simulated_daily_pnl_for_mc = []
    
    for current_date, day_trades in grouped_by_day:
        day_pnl_tracker = 0
        for index, trade_row in day_trades.iterrows():
            trade_pnl = trade_row['sim_pnl']
            if day_pnl_tracker + trade_pnl >= DAILY_PROFIT_CAP:
                day_pnl_tracker = DAILY_PROFIT_CAP
                break
            elif day_pnl_tracker + trade_pnl <= -DAILY_LOSS_LIMIT:
                day_pnl_tracker = -DAILY_LOSS_LIMIT
                break
            else:
                day_pnl_tracker += trade_pnl
        simulated_daily_pnl_for_mc.append(day_pnl_tracker)
    
    simulated_daily_pnl_series = pd.Series(simulated_daily_pnl_for_mc)

    NUM_MC_SIMULATIONS = 5000
    mc_results = []
    
    for _ in range(NUM_MC_SIMULATIONS):
        mc_balance = STARTING_BALANCE
        mc_days = 0
        mc_peak_balance = STARTING_BALANCE
        mc_max_drawdown = 0
        
        # Resample daily P&L outcomes with replacement
        simulated_daily_pnl_sequence = simulated_daily_pnl_series.sample(n=len(simulated_daily_pnl_series), replace=True).values
        
        for daily_pnl_outcome in simulated_daily_pnl_sequence:
            mc_days += 1
            mc_balance += daily_pnl_outcome
            
            mc_peak_balance = max(mc_peak_balance, mc_balance)
            mc_drawdown = mc_peak_balance - mc_balance
            mc_max_drawdown = max(mc_max_drawdown, mc_drawdown)

            if mc_balance >= STARTING_BALANCE + 100:
                mc_results.append({'outcome': 'profit_target', 'days': mc_days, 'max_drawdown': mc_max_drawdown})
                break
            if mc_balance <= STARTING_BALANCE - OVERALL_LOSS_LIMIT:
                mc_results.append({'outcome': 'loss_limit', 'days': mc_days, 'max_drawdown': mc_max_drawdown})
                break
        else: # If loop completes without hitting target or limit
            mc_results.append({'outcome': 'no_clear_outcome', 'days': mc_days, 'max_drawdown': mc_max_drawdown})
            
    mc_results_df = pd.DataFrame(mc_results)

    prob_success = (mc_results_df['outcome'] == 'profit_target').sum() / NUM_MC_SIMULATIONS * 100
    prob_loss_limit = (mc_results_df['outcome'] == 'loss_limit').sum() / NUM_MC_SIMULATIONS * 100
    
    days_to_target = mc_results_df[mc_results_df['outcome'] == 'profit_target']['days']
    median_days = days_to_target.median() if not days_to_target.empty else np.nan
    percentile_10 = days_to_target.quantile(0.1) if not days_to_target.empty else np.nan
    percentile_90 = days_to_target.quantile(0.9) if not days_to_target.empty else np.nan

    section5_output.append(f"Probability of success (reaching $100 profit): {prob_success:.2f}%")
    section5_output.append(f"Probability of hitting $50 loss limit: {prob_loss_limit:.2f}%")
    section5_output.append(f"Expected median number of trading days to reach $100: {median_days:.0f}")
    section5_output.append(f"10th percentile days to reach $100: {percentile_10:.0f}")
    section5_output.append(f"90th percentile days to reach $100: {percentile_90:.0f}")

    # --- Section 6: Final Recommendations ---
    section6_output = []

    # Is it realistic to pass this challenge with $5 risk / $10 reward?
    if prob_success > 50:
        section6_output.append("Is it realistic to pass this challenge with $5 risk / $10 reward? Yes")
    else:
        section6_output.append("Is it realistic to pass this challenge with $5 risk / $10 reward? No")

    # Should USDCHF be completely excluded?
    usdchf_data = df[df['symbol'] == 'USDCHF']
    usdchf_win_rate = (usdchf_data['is_win'].sum() / len(usdchf_data) * 100) if not usdchf_data.empty else 0
    
    if usdchf_win_rate < (overall_win_rate - 5): # If win rate is 5% or more below overall average
        section6_output.append("Should USDCHF be completely excluded? Yes (Win rate is significantly lower than overall average)")
    else:
        section6_output.append("Should USDCHF be completely excluded? No (Performance is acceptable or not significantly worse than average)")

    # What is the single biggest risk factor?
    if prob_loss_limit > 30:
        section6_output.append("What is the single biggest risk factor? High probability of hitting overall loss limit.")
    elif max_drawdown_sim > (STARTING_BALANCE * 0.2):
        section6_output.append("What is the single biggest risk factor? Maximum drawdown during simulation (exceeds 20% of starting balance).")
    elif overall_losing_streak > 10:
        section6_output.append("What is the single biggest risk factor? Longest consecutive losing streak.")
    else:
        section6_output.append("What is the single biggest risk factor? (Based on current metrics, risks appear manageable, but continuous monitoring of drawdown and losing streaks is advised.)")


    # --- Combine all sections ---
    full_report = []
    full_report.append("---SECTION_1_WIN_RATE_RR_DISTRIBUTION---")
    full_report.extend(section1_output)
    full_report.append("\n---SECTION_2_DAILY_P&L_DISTRIBUTION---")
    full_report.extend(section2_output)
    full_report.append("\n---SECTION_3_SIMULATION_HARD_LIMITS---")
    full_report.extend(section3_output)
    full_report.append("\n---SECTION_4_COSTS_ANALYSIS---")
    full_report.extend(section4_output)
    full_report.append("\n---SECTION_5_MONTE_CARLO_PROBABILITY---")
    full_report.extend(section5_output)
    full_report.append("\n---SECTION_6_FINAL_RECOMMENDATIONS---")
    full_report.extend(section6_output)

    with open(OUTPUT_FILE, 'w') as f:
        for line in full_report:
            f.write(str(line) + '\n')

    print(f"Analysis complete. Report saved to {OUTPUT_FILE}")

# Execute the analysis
analyze_trading_data()
