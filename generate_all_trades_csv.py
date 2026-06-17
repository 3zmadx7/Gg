
import os
import json
import glob
import pandas as pd

results_oanda_path = "/home/runner/workspace/results_oanda"
pair_dirs = ["AUDUSD", "EURUSD", "GBPUSD", "NZDUSD", "USDCHF", "USDJPY"]

all_trades_data = []

for pair in pair_dirs:
    pair_path = os.path.join(results_oanda_path, pair)
    
    # Find the latest backtest JSON file
    backtest_files = glob.glob(os.path.join(pair_path, "backtest_*.json"))
    
    if backtest_files:
        # Sort by modification time to get the latest
        backtest_files.sort(key=os.path.getmtime, reverse=True)
        latest_backtest_file = backtest_files[0]
        
        try:
            with open(latest_backtest_file, 'r') as f:
                data = json.load(f)
            
            trades = data.get("trades", [])
            for trade in trades:
                # Add the symbol to each trade for identification
                trade["symbol"] = pair
                all_trades_data.append(trade)
            
        except json.JSONDecodeError:
            print(f"Error decoding JSON from {latest_backtest_file} for {pair}")
        except Exception as e:
            print(f"An error occurred while processing {latest_backtest_file} for {pair}: {e}")
    else:
        print(f"No backtest JSON file found for {pair} in {pair_path}")

if all_trades_data:
    df_trades = pd.DataFrame(all_trades_data)
    # Reorder columns to put 'symbol' first for better readability
    cols = ['symbol'] + [col for col in df_trades.columns if col != 'symbol']
    df_trades = df_trades[cols]
    
    output_csv_path = "/home/runner/workspace/all_trades.csv"
    df_trades.to_csv(output_csv_path, index=False)
    print(f"Successfully created '{output_csv_path}' with all trades data.")
else:
    print("No trades data found to write to CSV.")
