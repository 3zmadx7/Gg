
import os
import json
import glob

results_oanda_path = "/home/runner/workspace/results_oanda"
pair_dirs = ["AUDUSD", "EURUSD", "GBPUSD", "NZDUSD", "USDCHF", "USDJPY"]

all_pairs_summary = []

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
            
            summary = {
                "symbol": data.get("symbol", pair),
                "net_profit": data.get("net_profit"),
                "total_return_pct": data.get("total_return_pct"),
                "total_trades": data.get("total_trades"),
                "winning_trades": data.get("winning_trades"),
                "losing_trades": data.get("losing_trades"),
                "win_rate": data.get("win_rate"),
                "profit_factor": data.get("profit_factor"),
                "max_drawdown": data.get("max_drawdown"),
                "sharpe_ratio": data.get("sharpe_ratio"),
                "sortino_ratio": data.get("sortino_ratio"),
                "test_from": data.get("test_from"),
                "test_to": data.get("test_to"),
            }
            all_pairs_summary.append(summary)
        except json.JSONDecodeError:
            print(f"Error decoding JSON from {latest_backtest_file} for {pair}")
        except Exception as e:
            print(f"An error occurred while processing {latest_backtest_file} for {pair}: {e}")
    else:
        print(f"No backtest JSON file found for {pair} in {pair_path}")

# Now, format and translate to Arabic
arabic_summary_content = []
arabic_summary_content.append("## ملخص نتائج الاختبار الخلفي (Backtest) لأزواج العملات\n")
arabic_summary_content.append("هذا الملخص يجمع أهم مقاييس الأداء من الاختبارات الخلفية لكل زوج عملات.\n\n")

for summary in all_pairs_summary:
    arabic_summary_content.append(f"### الزوج: {summary['symbol']}\n")
    arabic_summary_content.append(f"- فترة الاختبار: من {summary['test_from']} إلى {summary['test_to']}\n")
    arabic_summary_content.append(f"- صافي الربح: ${summary['net_profit']:.2f}\n")
    arabic_summary_content.append(f"- العائد الكلي: {summary['total_return_pct']:.2f}%\n")
    arabic_summary_content.append(f"- إجمالي الصفقات: {summary['total_trades']}\n")
    arabic_summary_content.append(f"- الصفقات الرابحة: {summary['winning_trades']}\n")
    arabic_summary_content.append(f"- الصفقات الخاسرة: {summary['losing_trades']}\n")
    arabic_summary_content.append(f"- معدل الربح: {summary['win_rate']:.2f}%\n")
    arabic_summary_content.append(f"- عامل الربح: {summary['profit_factor']:.2f}\n")
    arabic_summary_content.append(f"- أقصى تراجع (Max Drawdown): {summary['max_drawdown']:.2f}%\n")
    arabic_summary_content.append(f"- نسبة شارب (Sharpe Ratio): {summary['sharpe_ratio']:.2f}\n")
    arabic_summary_content.append(f"- نسبة سورتينو (Sortino Ratio): {summary['sortino_ratio']:.2f}\n")
    arabic_summary_content.append("\n")

final_arabic_content = "".join(arabic_summary_content)

# Write to file
with open("/home/runner/workspace/results_summary_arabic.txt", "w", encoding="utf-8") as f:
    f.write(final_arabic_content)

print("Successfully created 'results_summary_arabic.txt' with the summarized results in Arabic.")
