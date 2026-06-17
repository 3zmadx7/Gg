# AI Forex Bot — Agent Memory File
> **Purpose:** This file is the persistent memory for any AI agent working on this project.  
> Read it fully before doing anything. Update it when you finish your task.  
> Every agent that runs should append their results to the **Session Log** at the bottom.

---

## LATEST HANDOFF — NEXT AGENT READ THIS FIRST

### The Big Picture — What We Are Building
The user's goal is a **multi-pair hedge fund style Telegram signal bot**. Before building the bot, we need to find the best possible settings for each pair. Once optimized, the bot will send signals for the top 3–4 performing pairs simultaneously, giving a diversified, professional-grade signal system.

**Current state:**
- OANDA baseline runs are COMPLETE for all 6 pairs
- Data is downloaded and stored — do NOT re-download
- Next step: optimization to squeeze the best performance out of each pair
- After optimization: build Telegram signal bot using the best pairs and their best configs

---

### OANDA Baseline Results (starting point for optimization)

| Pair | Return | Win Rate | Profit Factor | Max DD | Sharpe | Priority |
|---|---:|---:|---:|---:|---:|---|
| USDJPY | +238.91% | 64.7% | 3.43 | -7.14% | 9.62 | 🟢 Optimize lightly |
| GBPUSD | +210.00% | 62.5% | 3.33 | -7.83% | 9.56 | 🟢 Optimize lightly |
| AUDUSD | +122.57% | 52.9% | 2.31 | -5.73% | 6.41 | 🟡 Optimize fully |
| NZDUSD | +62.96% | 48.8% | 2.00 | -13.04% | 5.22 | 🟡 Optimize fully |
| EURUSD | +50.37% | 43.1% | 1.51 | -9.45% | 3.08 | 🔴 Optimize fully — needs major improvement |
| USDCHF | +16.89% | 39.5% | 1.24 | -27.52% | 1.64 | ⛔ Optimize but likely drop |

**USDCHF warning:** 39% win rate + -27.5% max drawdown = the model fundamentally does not suit CHF. Optimize it, but if results don't improve meaningfully (above PF 1.8, DD below -15%), **recommend dropping it from the final portfolio**.

---

### Data Locations (do NOT re-download)
- OANDA parquets: `data/historical_oanda/{PAIR}/tf_5.parquet` (M5), `tf_15.parquet`, etc.
- OANDA baseline results: `results_oanda/{PAIR}/`
- OANDA baseline models: `models_oanda/model_v1_M5` (EURUSD) through `model_v6_M5` (NZDUSD)

---

### Optimization Strategy — What to Actually Tune

Run pairs **one at a time** (parallel runs cause model version conflicts in the shared `models_oanda/` folder). Do 30–50 trials per pair — more than that risks overfitting on such a short training window.

#### Tier 1 — Highest impact (always tune these)
1. **Confidence threshold** — currently 0.60. Try: 0.55, 0.60, 0.62, 0.65, 0.68, 0.70, 0.75
2. **Risk-Reward ratio** — currently ~1:2 (ATR-based). Try fixed RR: 1:1.5, 1:2, 1:2.5, 1:3
3. **ATR stop-loss multiplier** — try 1.0×, 1.5×, 2.0× ATR for SL sizing
4. **Training window** — currently Jan–Feb (2 months). Also try Jan–Mar (3 months, backtest Apr–May)

#### Tier 2 — Medium impact (tune if time allows)
5. **XGBoost hyperparams**: `n_estimators` (100–400), `max_depth` (3–7), `learning_rate` (0.05–0.2), `subsample` (0.7–1.0)
6. **RandomForest hyperparams**: `n_estimators` (100–400), `max_depth` (5–15), `min_samples_leaf` (1–5)
7. **Ensemble weighting**: try XGBoost weight 1.5× vs RF 1.0× (or vice versa)

#### Tier 3 — Try if pair is still underperforming
8. **Timeframe**: try M15 instead of M5 (retrain on M15 bars — use `tf_15.parquet`)
9. **Class weights**: give BUY/SELL labels more weight than HOLD in training

---

### Anti-Overfitting Rules — CRITICAL, do not skip

This is the most important section. With only 2 months of training data, it is very easy to find settings that look perfect on the test period but fail in live trading.

**Rule 1 — Score by risk-adjusted metrics, not raw return**
Use this composite score to rank trials:
```
score = (profit_factor × win_rate/100) - (abs(max_drawdown)/100) + (sharpe/10)
```
A trial with +300% return but -30% drawdown ranks LOWER than one with +150% and -8% drawdown.

**Rule 2 — Minimum trade count filter**
Reject any trial with fewer than **25 trades** in the test period. High return on 5 trades = luck, not edge.

**Rule 3 — Minimum win rate filter**
Reject any trial with win rate below **45%**. Below that, the RR ratio is carrying everything and the model has no real edge.

**Rule 4 — Drawdown cap**
Reject any trial with max drawdown worse than **-20%**. We are building a fund, not a gamble.

**Rule 5 — Report both "best by score" and "best by return"**
In the report, show the trial that wins on the composite score AND the trial with the highest raw return. The user can decide.

---

### Output Files Required

For each pair after optimization:
- `optimized_results/{PAIR}/trials.csv` — every trial with all metrics + composite score
- `optimized_results/{PAIR}/best_config.json` — the winning configuration (parameters)
- `optimized_results/{PAIR}/best_result.json` — the full backtest result of the best trial
- `optimized_results/{PAIR}/{PAIR}_OPTIMIZATION_REPORT.md` — human-readable summary:
  - Baseline vs optimized comparison table
  - Top 5 trials table
  - Winning settings explained in plain language
  - Whether the pair is recommended for the final portfolio (yes/maybe/drop)

After ALL pairs are done:
- `optimized_results/MASTER_OPTIMIZATION_COMPARISON.md` — all 6 pairs:
  - Baseline vs optimized side by side
  - Final portfolio recommendation (which pairs to include in Telegram bot)
  - Suggested confidence threshold per pair for live signals

Do **NOT** modify: `results/`, `models/`, `results_oanda/`, `models_oanda/`, `data/historical_oanda/`

---

### Final Portfolio Vision (what this is all building toward)
After optimization, the coordinator (Replit Agent) will review results and select **3–4 pairs** for the Telegram signal bot. The bot will:
- Monitor each pair independently with its own optimized confidence threshold
- Send signals in real time from OANDA live data
- Display which pair the signal is for, direction, entry, SL, TP, confidence
- Be deployed 24/7 on Railway via GitHub

The pairs with the best risk-adjusted scores after optimization will make the final cut.

---

---

### ⚡ SESSION 7 STOPPED HERE — CONTINUE FROM THIS POINT

The previous agent hit its rate limit mid-optimization. Here is the exact state:

#### Optimization status per pair

| Pair | Status | Trials | Best Return | Best Score | Recommendation |
|---|---|---:|---:|---:|---|
| GBPUSD | ✅ COMPLETE | 36 | +239.56% | 3.68 | **YES** |
| USDJPY | ✅ COMPLETE | 36 | +177.88% | 5.78 | **YES** |
| AUDUSD | ✅ COMPLETE | 36 | +123.91% | 2.06 | **MAYBE** |
| EURUSD | ❌ NOT STARTED | — | — | — | TBD |
| NZDUSD | ❌ NOT STARTED | — | — | — | TBD (empty folder exists) |
| USDCHF | ❌ NOT STARTED | — | — | — | TBD |

#### The optimization script already exists — DO NOT rewrite it
`optimize_oanda.py` (588 lines) is the reusable optimizer. It already handles all trial logic, scoring, and output file writing. To run the next pair, just call:
```bash
python3 optimize_oanda.py --pair EURUSD
python3 optimize_oanda.py --pair NZDUSD
python3 optimize_oanda.py --pair USDCHF
```
Check the script's argparse section first to confirm the exact flag names.

#### Run order for remaining pairs
1. EURUSD first — needs the most improvement (baseline was +50%, 43% win rate)
2. NZDUSD second — borderline pair, optimization may help
3. USDCHF last — likely to be dropped, but run it for completeness

#### Completed pair best configs (for reference)

**GBPUSD best config:**
- Confidence: 0.68 | RR: 1:2.5 | ATR SL: 2.0× | Train: 2 months | Model: conservative_2m
- Result: +239.56% | Win 63.6% | PF 4.13 | DD -6.42% | Sharpe 11.15

**USDJPY best config:**
- Confidence: 0.55 | RR: 1:1.5 | ATR SL: 1.0× | Train: 3 months | Model: three_month_3m
- Result: +177.88% | Win **78.7%** | PF 5.51 | DD **-3.29%** | Sharpe 14.71
- Note: Lower return than baseline but massively better quality — 78.7% win rate and only -3.3% drawdown. This is the highest-quality pair in the portfolio.

**AUDUSD best config:**
- Confidence: 0.65 | RR: 1:2.5 | ATR SL: 1.5× | Train: 2 months | Model: conservative_2m
- Result: +123.91% | Win 52.9% | PF 2.71 | DD -12.10% | Sharpe 7.41
- Note: Marginal improvement over baseline. "MAYBE" — final decision after seeing EURUSD and NZDUSD results.

#### After all 3 remaining pairs finish
Create `optimized_results/MASTER_OPTIMIZATION_COMPARISON.md` with:
- All 6 pairs: baseline vs optimized side by side
- Composite scores ranked
- Final portfolio recommendation: which pairs go in the Telegram signal bot
- Best config summary table for each recommended pair

Then update the Session Log at the bottom of this file with a Session 8 entry.

---

### After Optimization — Update This File
Append a Session 8 entry to the Session Log at the bottom. Include:
- Optimized results table for all pairs
- Whether each pair is recommended for the portfolio or dropped
- Best config per pair (confidence threshold, RR, ATR multiplier)

---

## 1. Project Overview

This is a Python-based AI Forex Trading Bot running entirely in a **Replit** console environment (no frontend, no UI). It was originally imported from GitHub and adapted to:
- Use **Dukascopy M1 bid-price CSV data** (downloaded via `npx dukascopy-node`) instead of MetaTrader5
- Run a full **ML training + backtesting pipeline** for a given currency pair and date range
- Output clean console results and a JSON report

The entry point for the pipeline is **`pipeline_2026.py`**.

---

## 2. Environment — What Is Already Installed

Do **NOT** reinstall or re-download these. They are already present.

| Item | Status |
|---|---|
| Python 3 | ✅ Available |
| Node.js 20 + `npx` | ✅ Installed via Nix |
| `dukascopy-node` npm package | ✅ Already pulled (cached in `node_modules`) |
| `xgboost`, `scikit-learn`, `pandas`, `numpy`, `pyarrow`, `joblib`, `rich`, `yfinance` | ✅ Installed via pip |
| `lightgbm` | ⚠️ Installed but **DISABLED** — `libgomp.so.1` is missing from this Nix environment. Set via env var `ENABLE_LIGHTGBM=false` |
| `LSTM` | ⚠️ **DISABLED** — `ENABLE_LSTM=false` |
| MetaTrader5 | ❌ Not installed (Windows-only). The `MT5Connector` class handles the missing package gracefully via `_try_import_mt5()` — do not attempt to install it |

### Key Environment Variables (already set in Replit Secrets)
```
ENABLE_LIGHTGBM=false
ENABLE_LSTM=false
```
Plus ~63 other bot configuration env vars. Do not touch them.

---

## 3. Repository Structure

```
/
├── pipeline_2026.py          ← MAIN PIPELINE (start here)
├── main.py                   ← Original bot entry point (not used in pipeline)
├── train.py                  ← Original training script (not used in pipeline)
├── requirements.txt
│
├── data/
│   ├── duka_raw/             ← Raw Dukascopy CSV downloads land here
│   │   └── eurusd-m1-bid-2026-01-01-2026-05-31.csv  (149,010 rows, EURUSD done)
│   ├── historical/
│   │   └── EURUSD/           ← Resampled parquet files for EURUSD
│   │       ├── tf_5.parquet   (M5)
│   │       ├── tf_15.parquet  (M15)
│   │       ├── tf_30.parquet  (M30)
│   │       ├── tf_60.parquet  (H1)
│   │       └── tf_240.parquet (H4)
│   ├── data_loader.py        ← DataLoader("EURUSD") reads from data/historical/SYMBOL/
│   ├── dukascopy_converter.py← Parses Dukascopy CSV → standardised DataFrame
│   └── mt5_connector.py      ← MT5 stub (graceful no-op without MT5 installed)
│
├── ml/
│   ├── ensemble.py           ← VotingEnsemble: wraps multiple models, predict_proba(X)
│   ├── model_manager.py      ← ModelManager: save/load versioned models
│   ├── trainer.py            ← Orchestrates XGBoost + RF training
│   ├── predictor.py          ← get_buy_sell_hold() — use batch mode, not bar-by-bar
│   ├── xgboost_model.py
│   ├── random_forest_model.py
│   ├── lightgbm_model.py     ← Disabled
│   └── lstm_model.py         ← Disabled
│
├── features/                 ← Feature engineering (called internally by trainer/predictor)
├── models/
│   ├── model_v11_M5/         ← EURUSD trained model (XGBoost + RandomForest, M5 timeframe)
│   │   ├── xgboost.ubj
│   │   ├── random_forest.ubj
│   │   └── metadata.json     ← Contains full feature_cols list (115 features)
│   └── ... (older/empty versions from original repo — ignore them)
│
├── results/
│   └── EURUSD/
│       └── backtest_2026_20260607_091908.json  ← EURUSD backtest results
│
└── AGENT_MEMORY.md           ← THIS FILE
```

---

## 4. The Pipeline (`pipeline_2026.py`) — How It Works

### CLI Modes
```bash
python3 pipeline_2026.py                   # Full run: download → convert → train → backtest
python3 pipeline_2026.py --skip-download   # Skip download, use existing CSV
python3 pipeline_2026.py --csv path.csv    # Use a specific existing CSV
python3 pipeline_2026.py --backtest-only   # Skip download+train, load saved model & backtest
```

### The 5 Steps

**Step 1 — Download**  
Runs: `npx dukascopy-node -i {instrument} -from {date} -to {date} -t m1 -f csv -fl`  
Output: `data/duka_raw/{instrument}-m1-bid-{date_range}.csv`  
Dukascopy instrument names: `eurusd`, `gbpusd`, `usdjpy`, etc. (all lowercase, no slash)

**Step 2 — Convert & Store**  
Parses the M1 CSV using `_load_dukascopy_csv()` → resamples to M5/M15/M30/H1/H4  
Saves parquets to `data/historical/{SYMBOL}/tf_{tf_minutes}.parquet`  
The `time` column is tz-naive UTC. This is required by `DataLoader`.

**Step 3 — Train**  
Loads M5 bars from the parquet for the train period  
Labels bars: 0=HOLD, 1=BUY, 2=SELL  
Trains XGBoost + RandomForest ensemble  
Saves to `models/model_v{N}_M5/` with `metadata.json` containing `feature_cols`

**Step 4 — Backtest**  
Loads M5 bars for the test period  
Computes all 115 features in one pass (batch, not bar-by-bar)  
Calls `ensemble.predict_proba(X_all)` in a single batch call (fast, ~0.1s)  
Entry condition: `confidence >= 0.60` and signal is BUY or SELL (not HOLD)  
Risk management: dynamic SL/TP from ATR; 1 lot position size  
Simulates trades bar-by-bar; exits on TP hit, SL hit, or end of data

**Step 5 — Report**  
Prints a formatted console table  
Saves JSON to `results/{SYMBOL}/backtest_2026_{timestamp}.json`

---

## 5. Critical Bug Fixed — Model Version Sorting

**Problem:** `ModelManager.list_versions()` sorts version strings alphabetically.  
Alphabetical sort: `v10_M5 < v11_M5 < v9_M5` — so `v9` appears "latest" even though `v11` is newer.

**Fix applied in `pipeline_2026.py`** (`--backtest-only` branch):
```python
all_versions = mm.list_versions(timeframe=5)
def _version_num(v: str) -> int:
    try:
        return int(v.split("_")[0].replace("v", ""))
    except Exception:
        return 0
all_versions_sorted = sorted(all_versions, key=_version_num)
latest_v = all_versions_sorted[-1]
ensemble = mm.load_ensemble(latest_v)
```
**Apply the same fix** when loading models for any new symbol/timeframe.

---

## 6. Data Format Details

### Dukascopy CSV columns (raw)
`Timestamp (UTC)`, `Open`, `High`, `Low`, `Close`, `Volume`  
Timestamp is Unix milliseconds (integer).

### Parquet schema after conversion
| Column | Type | Notes |
|---|---|---|
| `time` | datetime64[ns] tz-naive | UTC, used as index-like column |
| `open` | float64 | |
| `high` | float64 | |
| `low` | float64 | |
| `close` | float64 | |
| `volume` | float64 | |

### Feature list (115 features — from `models/model_v11_M5/metadata.json`)
ema_20, ema_50, ema_200, ema_cross, ema_slope_20, ema_slope_50, price_vs_ema200, rsi, rsi_oversold, rsi_overbought, macd, macd_signal, macd_histogram, macd_cross, macd_above_zero, adx, plus_di, minus_di, adx_strong, atr, bb_upper, bb_lower, bb_mid, bb_width, bb_pct, bb_position, stoch_k, stoch_d, stoch_cross, momentum_10, momentum_20, volatility, realized_vol, williams_r, cci, mass_index, obv, returns, log_return, volume_ratio, volume_trend, spread_pips, hl_range, body, upper_wick, lower_wick, price_position, nearest_support, nearest_resistance, dist_to_support, dist_to_resistance, pattern_bullish, pattern_bearish, vwap, hour, day_of_week, is_weekend, session_asia, session_london, session_ny, session_overlap, is_monday, is_friday, is_midweek, is_market_hours, mtf_alignment, trend15, momentum15, volatility15, atr15, rsi15, ema_cross15, adx15, adx_strong15, align15, ema_50_tf15, ema_200_tf15, ema_20_tf15, close_vs_ema2015, macd15, trend30, momentum30, volatility30, atr30, rsi30, ema_cross30, adx30, adx_strong30, align30, ema_50_tf30, ema_200_tf30, ema_20_tf30, close_vs_ema2030, trend60, momentum60, volatility60, atr60, rsi60, ema_cross60, adx60, adx_strong60, align60, ema_50_tf60, ema_200_tf60, trend240, momentum240, volatility240, atr240, rsi240, ema_cross240, adx240, adx_strong240, align240, ema_50_tf240, ema_200_tf240

---

## 7. Replit Workflow

The Replit workflow is named **"Run Pipeline 2026"** and runs:
```bash
python3 pipeline_2026.py --backtest-only
```
To run the full pipeline (download + train + backtest), either:
- Change the workflow command temporarily, OR
- Run directly in the Shell: `python3 pipeline_2026.py`

---

## 8. EURUSD Results (Completed — Session 1)

**Trained:** Jan 1, 2026 → Feb 28, 2026 (M5 bars, 11,184 bars)  
**Tested:** Mar 1, 2026 → May 31, 2026 (18,720 M5 bars)  
**Model saved:** `models/model_v11_M5/` (XGBoost + RandomForest)  
**Full results:** `results/EURUSD/backtest_2026_20260607_091908.json`

| Metric | Value |
|---|---|
| Initial Balance | $10,000 |
| Final Balance | $21,488 |
| Total Return | **+114.88%** |
| Net Profit | +$11,488 |
| Total Trades | 53 |
| Win Rate | 58.5% (31W / 22L) |
| Profit Factor | 2.70 |
| Avg Win | +$589 |
| Avg Loss | -$307 |
| Expectancy | +$217/trade |
| Max Drawdown | -9.92% |
| Sharpe Ratio | 7.74 |
| Sortino Ratio | 104.11 |
| TP exits | 30 |
| SL exits | 22 |

---

## 9. OANDA API — NEW DATA SOURCE (Priority Task)

### Why we switched
Dukascopy data downloads via `npx dukascopy-node` caused repeated errors and timeouts in previous sessions. OANDA provides a clean, reliable REST API — same professional-grade data, no npm tool required.

### Credentials (already saved as Replit environment variables — do NOT hardcode them)
```
OANDA_TOKEN    → os.environ["OANDA_TOKEN"]
OANDA_BASE_URL → os.environ["OANDA_BASE_URL"]   # https://api-fxpractice.oanda.com/v3
```
These are set. Just read them with `os.environ`. Never write the actual token values into any file.

### OANDA instrument names (DIFFERENT from Dukascopy)
| Pair | OANDA name |
|---|---|
| EURUSD | `EUR_USD` |
| GBPUSD | `GBP_USD` |
| USDJPY | `USD_JPY` |
| AUDUSD | `AUD_USD` |
| USDCHF | `USD_CHF` |
| NZDUSD | `NZD_USD` |

### OANDA candles API — how to call it
```
GET {OANDA_BASE_URL}/instruments/{instrument}/candles
Headers: Authorization: Bearer {OANDA_TOKEN}
Params:
  granularity = M1   (or M5, M15, M30, H1, H4)
  from        = 2026-01-01T00:00:00Z   (RFC3339)
  to          = 2026-05-31T23:59:59Z
  price       = M    (midpoint — use this for clean OHLCV)
  count       = 5000 (max per call — paginate if needed)
```
Response JSON structure:
```json
{
  "candles": [
    {
      "time": "2026-01-01T00:00:00.000000000Z",
      "mid": { "o": "1.1050", "h": "1.1055", "l": "1.1045", "c": "1.1052" },
      "volume": 123,
      "complete": true
    }
  ]
}
```
Only use candles where `"complete": true` (skip the last incomplete candle).

### What the agent needs to build

**Create `data/oanda_downloader.py`** — a module with a function:
```python
def download_oanda_candles(instrument: str, granularity: str, from_dt: datetime, to_dt: datetime) -> pd.DataFrame:
    # Returns DataFrame with columns: time (tz-naive UTC datetime), open, high, low, close, volume
    # Paginates automatically if date range > 5000 bars
```

**Create `pipeline_oanda.py`** — based on `pipeline_2026_GBPUSD.py` but replacing the dukascopy download step with `oanda_downloader.py`. Key differences:
- Step 1: Call `download_oanda_candles("EUR_USD", "M1", ...)` instead of `npx dukascopy-node`
- Save M1 data to `data/historical_oanda/{SYMBOL}/tf_1.parquet` (new folder, separate from Dukascopy)
- Resample M1 → M5/M15/M30/H1/H4, save to `data/historical_oanda/{SYMBOL}/tf_{tf}.parquet`
- Step 3 (train): same as before — XGBoost + RandomForest on Jan–Feb 2026
- Step 4 (backtest): same as before — Mar–May 2026
- Save results to `results_oanda/{SYMBOL}/` (new folder — do NOT touch the old `results/` folder)
- Save model to `models_oanda/model_v{N}_M5/` (new folder — do NOT touch `models/`)

**Then create pair-specific versions** by copying `pipeline_oanda.py` and changing SYMBOL + OANDA_INSTRUMENT:
- `pipeline_oanda_EURUSD.py` → SYMBOL="EURUSD", OANDA_INSTRUMENT="EUR_USD"
- `pipeline_oanda_GBPUSD.py` → SYMBOL="GBPUSD", OANDA_INSTRUMENT="GBP_USD"
- `pipeline_oanda_USDJPY.py` → SYMBOL="USDJPY", OANDA_INSTRUMENT="USD_JPY"
- `pipeline_oanda_AUDUSD.py` → SYMBOL="AUDUSD", OANDA_INSTRUMENT="AUD_USD"
- `pipeline_oanda_USDCHF.py` → SYMBOL="USDCHF", OANDA_INSTRUMENT="USD_CHF"
- `pipeline_oanda_NZDUSD.py` → SYMBOL="NZDUSD", OANDA_INSTRUMENT="NZD_USD"

### Run order
Run all 6 pairs **one at a time**:
```bash
python3 pipeline_oanda_EURUSD.py
python3 pipeline_oanda_GBPUSD.py
python3 pipeline_oanda_USDJPY.py
python3 pipeline_oanda_AUDUSD.py
python3 pipeline_oanda_USDCHF.py
python3 pipeline_oanda_NZDUSD.py
```

### After all 6 pairs finish
1. Create a report MD for each pair: `results_oanda/{PAIR}/{PAIR}_REPORT.md`
2. Create `results_oanda/MASTER_COMPARISON_OANDA.md` comparing all 6 OANDA results side by side
3. Create `results_oanda/OANDA_VS_DUKASCOPY.md` comparing OANDA vs Dukascopy results for EURUSD and GBPUSD (the pairs that have both)
4. Update `AGENT_MEMORY.md` with a Session 4 entry

### Important technical notes
- The model version sort bug fix must be applied (numeric sort, not alphabetical) — copy it from `pipeline_2026_GBPUSD.py`
- Run pairs one at a time — parallel runs cause model version conflicts
- The Sortino ratio may show 0.0 — known display bug, ignore it
- USDJPY: prices are ~150.xxx — the ATR-based SL/TP logic should handle this automatically via the features, but verify the trade PnL values are reasonable (not tiny like 0.001)
- If any pair download fails: retry once; if still failing, skip and note it

---

## 10. CURRENT STATUS OF ALL PAIRS (Dukascopy runs)

| Pair | Pipeline file | Data downloaded | Model | Backtest JSON | Report MD | Status |
|---|---|---|---|---|---|---|
| EURUSD | `pipeline_2026.py` | ✅ | `model_v11_M5` | ✅ | ✅ | **DONE** |
| GBPUSD | `pipeline_2026_GBPUSD.py` | ✅ | `model_v12_M5` | ✅ | ✅ | **DONE** |
| USDJPY | `pipeline_2026_USDJPY.py` | ✅ | `model_v13_M5` | ✅ | ❌ missing | **DONE — needs report** |
| AUDUSD | `pipeline_2026_AUDUSD.py` | ✅ | `model_v14_M5` | ✅ | ❌ missing | **DONE — needs report** |
| USDCHF | `pipeline_2026_USDCHF.py` | ❌ | ❌ | ❌ | ❌ | **NOT STARTED** |
| NZDUSD | `pipeline_2026_NZDUSD.py` | ❌ | ❌ | ❌ | ❌ | **NOT STARTED** |
| MASTER | — | — | — | — | ❌ missing | **NOT CREATED** |

---

## 9b. NEXT TASK — Continue from where Session 3 stopped

The previous agent (Session 3) hit its rate limit after finishing USDJPY and AUDUSD backtests but before writing their reports, and before running USDCHF and NZDUSD.

**Do these steps in order:**

### Step A — Write the missing USDJPY report
USDJPY is fully done. Just create `results/USDJPY/USDJPY_REPORT.md`.
Read `results/USDJPY/backtest_2026_20260607_130614.json` for the numbers.
Include: full metrics table, first 10 + last 10 trades, notes, comparison vs EURUSD and GBPUSD.

Known USDJPY results:
- Final balance: $34,729 | Return: **+247.29%** | Trades: 89 | Win rate: 64.0% | PF: 3.41 | Max DD: -8.04% | Sharpe: 9.56

### Step B — Write the missing AUDUSD report
AUDUSD is fully done. Just create `results/AUDUSD/AUDUSD_REPORT.md`.
Read `results/AUDUSD/backtest_2026_20260607_130845.json` for the numbers.
Include: full metrics table, first 10 + last 10 trades, notes, comparison vs other pairs.

Known AUDUSD results:
- Final balance: $19,867 | Return: **+98.67%** | Trades: 64 | Win rate: 51.6% | PF: 2.06 | Max DD: -11.95% | Sharpe: 5.47

### Step C — Run USDCHF full pipeline
The pipeline file `pipeline_2026_USDCHF.py` already exists. Just run it:
```bash
python3 pipeline_2026_USDCHF.py
```
Then create `results/USDCHF/USDCHF_REPORT.md`.

### Step D — Run NZDUSD full pipeline
The pipeline file `pipeline_2026_NZDUSD.py` already exists. Just run it:
```bash
python3 pipeline_2026_NZDUSD.py
```
Then create `results/NZDUSD/NZDUSD_REPORT.md`.

### Step E — Create the master comparison file
Once all 6 pairs are done, create `results/MASTER_COMPARISON.md` with one table comparing all 6 pairs:
Columns: Pair | Return % | Final Balance | Trades | Win Rate | Profit Factor | Max Drawdown | Sharpe | Expectancy
Sort by Total Return descending.

### Step F — Update AGENT_MEMORY.md
Append a Session 4 entry at the bottom of this file with results for each new pair.

---

### Important notes for USDCHF and NZDUSD runs
- Dukascopy instrument names: `usdchf`, `nzdusd` (lowercase, no slash)
- Run **one at a time** — parallel runs cause model version conflicts
- The model version number will auto-increment: next available after v14 will be v15 (USDCHF) and v16 (NZDUSD)
- The **Sortino ratio shows 0.0** on some pairs — known display bug, do not fix it, just note it in the report
- If a download fails, retry once. If it fails again, note it and skip
- The numeric model version sort fix is already inside `pipeline_2026_USDCHF.py` and `pipeline_2026_NZDUSD.py` (copied from GBPUSD pipeline)

---

## 10. Common Errors and Fixes

| Error | Cause | Fix |
|---|---|---|
| `No model for timeframe M5` | `load_latest_for_timeframe` picks old empty version | Use numeric sort (Section 5) |
| `LightGBM not available` | libgomp.so.1 missing in Nix | Expected — set `ENABLE_LIGHTGBM=false`, ignore |
| `ModuleNotFoundError: MetaTrader5` | MT5 is Windows-only | Expected — the code handles it gracefully, ignore |
| `KeyError: 'time'` in DataLoader | Parquet was saved with wrong column name | Ensure `_load_dukascopy_csv` returns column named `time` (lowercase) |
| dukascopy-node download timeout | Network issue | Retry; if persistent, use `--csv` flag with a pre-downloaded file |
| Feature count mismatch during backtest | Model was trained with different features | Always load model first and use `ensemble.feature_cols` as the feature list |
| Alphabetical model version sort bug | `v9 > v11` in string sort | Always sort by `int(version.replace("v","").split("_")[0])` |

---

## 11. Session Log

### Session 1 — 2026-06-07
**Agent:** Replit Agent  
**Work done:**
- Imported repo from GitHub
- Installed Node.js 20, all Python deps, set 65 env vars
- Created `data/dukascopy_converter.py` and `pipeline_2026.py`
- Downloaded EURUSD M1 data (Jan–May 2026): 149,010 bars
- Resampled to 5 timeframe parquets
- Trained XGBoost + RandomForest on Jan–Feb (11,184 M5 bars, ~8.5s)
- Fixed model version alphabetical sort bug
- Backtested Mar–May: **+114.88% return, 58.5% win rate, PF 2.70**
- Results saved: `results/EURUSD/backtest_2026_20260607_091908.json`

**Files created/modified:**
- `pipeline_2026.py` ← main pipeline (new file)
- `data/dukascopy_converter.py` ← Dukascopy CSV parser (new file)
- `models/model_v11_M5/` ← trained EURUSD model (new)
- `data/historical/EURUSD/tf_*.parquet` ← all 5 timeframe parquets (new)
- `data/duka_raw/eurusd-m1-bid-2026-01-01-2026-05-31.csv` ← raw M1 data (new)
- `results/EURUSD/backtest_2026_20260607_091908.json` ← results (new)
- `AGENT_MEMORY.md` ← this file (new)

---

> **Instructions for every agent:** When you finish your session, append a new Session entry below following the same format. Include: what you did, files created/modified, key results, bugs hit, and what remains.

### Session 2 — 2026-06-07
**Agent:** Codex
**Work done:**
- Created `pipeline_2026_GBPUSD.py` from `pipeline_2026.py`
- Updated the pipeline constants and console labels for GBPUSD (`SYMBOL="GBPUSD"`, `DUKA_INSTRUMENT="gbpusd"`)
- Added instrument-specific CSV lookup (`gbpusd-*.csv`) so GBPUSD runs do not accidentally reuse EURUSD raw data
- Downloaded GBPUSD M1 data (Jan-May 2026): 151,915 rows
- Resampled GBPUSD data to 5 timeframe parquets under `data/historical/GBPUSD/`
- Trained XGBoost + RandomForest on Jan-Feb 2026 (11,808 M5 bars, 115 features)
- Saved GBPUSD model as `models/model_v12_M5/`
- Updated the GBPUSD pipeline report writer to persist the full trade list in JSON for audit/reporting
- Backtested Mar-May 2026: **+222.00% return, 62.4% win rate, PF 3.31**
- Created `results/GBPUSD/GBPUSD_REPORT.md` with metrics, trade samples, notes, and EURUSD comparison

**Key GBPUSD results:**

| Metric | Value |
|---|---:|
| Initial Balance | $10,000 |
| Final Balance | $32,200 |
| Total Return | **+222.00%** |
| Net Profit | +$22,200 |
| Total Trades | 85 |
| Win Rate | 62.4% (53W / 32L) |
| Profit Factor | 3.31 |
| Avg Win | +$600 |
| Avg Loss | -$300 |
| Expectancy | +$261.18/trade |
| Max Drawdown | -4.72% |
| Sharpe Ratio | 9.51 |
| Sortino Ratio | 0.00 |
| TP exits | 53 |
| SL exits | 32 |
| End-of-data exits | 0 |

**Files created/modified:**
- `pipeline_2026_GBPUSD.py` ← GBPUSD pipeline variant (new)
- `data/duka_raw/gbpusd-m1-bid-2026-01-01-2026-05-31.csv` ← raw GBPUSD M1 data (new)
- `data/historical/GBPUSD/tf_*.parquet` ← all 5 GBPUSD timeframe parquets (new)
- `models/model_v12_M5/` ← trained GBPUSD model (new)
- `results/GBPUSD/backtest_2026_20260607_124237.json` ← first GBPUSD report, sample trades only (new)
- `results/GBPUSD/backtest_2026_20260607_124422.json` ← complete GBPUSD report with all trades (new)
- `results/GBPUSD/GBPUSD_REPORT.md` ← human-readable GBPUSD report (new)
- `AGENT_MEMORY.md` ← appended Session 2 log

**Notes / issues hit:**
- The filesystem sandbox helper failed with `bwrap: Unexpected capabilities but not setuid, old file caps config?`, so commands and file edits were run with explicit escalation approvals.
- `apply_patch` was unusable for the same sandbox reason; scoped non-interactive shell edits were used instead.
- The base pipeline saves models in global version directories (`models/model_v*_M5/`) without symbol-specific names. `v12_M5` is the GBPUSD model from this session.

---

### Session 3 — 2026-06-07 (INCOMPLETE — hit rate limit)
**Agent:** Codex
**Work done:**
- Created all 4 remaining pipeline files: `pipeline_2026_USDJPY.py`, `pipeline_2026_AUDUSD.py`, `pipeline_2026_USDCHF.py`, `pipeline_2026_NZDUSD.py`
- Ran full pipeline for USDJPY: download (clean + partial attempt) → resample → train → backtest ✅
- Ran full pipeline for AUDUSD: download → resample → train → backtest ✅
- Hit rate limit mid-session — USDCHF and NZDUSD were NOT run
- No report MD files were written for USDJPY or AUDUSD before the agent stopped

**Key USDJPY results (model_v13_M5):**
- Final balance: $34,729 | Return: **+247.29%** | Trades: 89 | Win rate: 64.0% | PF: 3.41 | Max DD: -8.04% | Sharpe: 9.56
- Results JSON: `results/USDJPY/backtest_2026_20260607_130614.json`

**Key AUDUSD results (model_v14_M5):**
- Final balance: $19,867 | Return: **+98.67%** | Trades: 64 | Win rate: 51.6% | PF: 2.06 | Max DD: -11.95% | Sharpe: 5.47
- Results JSON: `results/AUDUSD/backtest_2026_20260607_130845.json`

**Files created:**
- `pipeline_2026_USDJPY.py` ← USDJPY pipeline (new)
- `pipeline_2026_AUDUSD.py` ← AUDUSD pipeline (new)
- `pipeline_2026_USDCHF.py` ← USDCHF pipeline (new, NOT YET RUN)
- `pipeline_2026_NZDUSD.py` ← NZDUSD pipeline (new, NOT YET RUN)
- `data/duka_raw/usdjpy-m1-bid-2026-01-01-2026-05-31.csv` ← raw USDJPY M1 data (new)
- `data/duka_raw/audusd-m1-bid-2026-01-01-2026-05-31.csv` ← raw AUDUSD M1 data (new)
- `data/historical/USDJPY/tf_*.parquet` ← all 5 USDJPY timeframe parquets (new)
- `data/historical/AUDUSD/tf_*.parquet` ← all 5 AUDUSD timeframe parquets (new)
- `models/model_v13_M5/` ← trained USDJPY model (new)
- `models/model_v14_M5/` ← trained AUDUSD model (new)
- `results/USDJPY/backtest_2026_20260607_130614.json` ← USDJPY results (new)
- `results/AUDUSD/backtest_2026_20260607_130845.json` ← AUDUSD results (new)

**Leftover/junk files (safe to ignore, do not delete):**
- `data/duka_raw/partial_usdjpy-*.csv` ← aborted first download attempt
- `data/historical/USDJPY_partial_20260607_130336/` ← aborted first resample attempt
- `models/partial_model_v13_M5_USDJPY_20260607_130336/` ← aborted first train attempt
- `results/USDJPY/partial_backtest_*.json` ← aborted first backtest attempt

**What still needs to be done (see Section 9b for full instructions):**
- Step A: Write `results/USDJPY/USDJPY_REPORT.md`
- Step B: Write `results/AUDUSD/AUDUSD_REPORT.md`
- Step C: Run `python3 pipeline_2026_USDCHF.py` → write `results/USDCHF/USDCHF_REPORT.md`
- Step D: Run `python3 pipeline_2026_NZDUSD.py` → write `results/NZDUSD/NZDUSD_REPORT.md`
- Step E: Create `results/MASTER_COMPARISON.md` (all 6 pairs side by side)
- Step F: Update this AGENT_MEMORY.md with Session 4 log

---

### Session 4 — 2026-06-07 (OANDA pipeline complete)
**Agent:** Codex

**Work done:**
- Created OANDA REST downloader with automatic pagination: `data/oanda_downloader.py`
- Created shared OANDA pipeline: `pipeline_oanda.py`
- Created six pair-specific OANDA entrypoints:
  - `pipeline_oanda_EURUSD.py`
  - `pipeline_oanda_GBPUSD.py`
  - `pipeline_oanda_USDJPY.py`
  - `pipeline_oanda_AUDUSD.py`
  - `pipeline_oanda_USDCHF.py`
  - `pipeline_oanda_NZDUSD.py`
- Ran all six OANDA pairs one at a time: download → resample → train → backtest
- Saved OANDA data under `data/historical_oanda/`
- Saved OANDA models under `models_oanda/`
- Saved OANDA results under `results_oanda/`
- Created per-pair Markdown reports, master comparison, and OANDA-vs-Dukascopy comparison
- Did not modify legacy `results/` or `models/`

**Key OANDA results:**
| Pair | Model | Final Balance | Return | Trades | Win Rate | PF | Max DD | Sharpe |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| EURUSD | v1_M5 | $15,036.89 | +50.37% | 58 | 43.1% | 1.51 | -9.45% | 3.08 |
| GBPUSD | v2_M5 | $31,000.00 | +210.00% | 80 | 62.5% | 3.33 | -7.83% | 9.56 |
| USDJPY | v3_M5 | $33,891.00 | +238.91% | 85 | 64.7% | 3.43 | -7.14% | 9.62 |
| AUDUSD | v4_M5 | $22,256.75 | +122.57% | 68 | 52.9% | 2.31 | -5.73% | 6.41 |
| USDCHF | v5_M5 | $11,689.00 | +16.89% | 38 | 39.5% | 1.24 | -27.52% | 1.64 |
| NZDUSD | v6_M5 | $16,296.00 | +62.96% | 43 | 48.8% | 2.00 | -13.04% | 5.22 |

**Files created:**
- `data/oanda_downloader.py`
- `pipeline_oanda.py`
- `pipeline_oanda_EURUSD.py`
- `pipeline_oanda_GBPUSD.py`
- `pipeline_oanda_USDJPY.py`
- `pipeline_oanda_AUDUSD.py`
- `pipeline_oanda_USDCHF.py`
- `pipeline_oanda_NZDUSD.py`
- `data/historical_oanda/{PAIR}/tf_*.parquet`
- `models_oanda/model_v1_M5/` through `models_oanda/model_v6_M5/`
- `results_oanda/{PAIR}/backtest_2026_oanda_*.json`
- `results_oanda/{PAIR}/{PAIR}_REPORT.md`
- `results_oanda/MASTER_COMPARISON_OANDA.md`
- `results_oanda/OANDA_VS_DUKASCOPY.md`

**Notes / issues hit:**
- OANDA rejected requests that specify `count` together with both `from` and `to`; downloader pagination was corrected to use `from + count` chunks and locally stop at the requested end time.
- USDJPY uses `pip_size=0.01`; PnL values are normal dollar-sized values, not fractional pip noise.
- USDCHF Sortino produced an extreme value due to the known Sortino display/math edge case; comparison reports flag this.
- No OANDA downloads required retry after the pagination fix.

**What remains:**
- OANDA task is complete.
- Older Dukascopy Section 9b work remains unchanged because this session intentionally did not touch legacy `results/` or `models/`.

---

### Session 5 — 2026-06-07 (memory refreshed for optimization handoff)
**Agent:** Codex

**Work done:**
- Refreshed `AGENT_MEMORY.md` with a prominent "LATEST HANDOFF" section at the top.
- Clarified that the next task is pair-by-pair OANDA optimization, not another baseline run.
- Specified parallel-agent split: one agent per pair for EURUSD, GBPUSD, USDJPY, AUDUSD, USDCHF, and NZDUSD.
- Specified target of about 100 optimization trials per pair.
- Defined output folders:
  - `optimized_results/{PAIR}/` for optimization results and reports
  - `optimized_models/{PAIR}/` if optimized models are saved
- Repeated hard rule: do not modify legacy `results/` or `models/`, and do not overwrite OANDA baselines in `results_oanda/` or `models_oanda/`.

**Next task for the next AI agent:**
- Launch/coordinate parallel pair agents.
- Each pair agent should optimize only its assigned pair using `data/historical_oanda/{PAIR}/` as input.
- Each pair agent should produce:
  - `optimized_results/{PAIR}/trials.csv`
  - `optimized_results/{PAIR}/best_config.json`
  - `optimized_results/{PAIR}/best_result.json`
  - `optimized_results/{PAIR}/{PAIR}_OPTIMIZATION_REPORT.md`
- After all pairs finish, create `optimized_results/MASTER_OPTIMIZATION_COMPARISON.md`.

---

### Session 7 — 2026-06-08 (INCOMPLETE — hit rate limit mid-optimization)
**Agent:** Codex
**Work done:**
- Created `optimize_oanda.py` (588 lines) — reusable optimizer script for all pairs
- Ran full 36-trial optimization for GBPUSD → best: +239.56%, Win 63.6%, PF 4.13, DD -6.42%, Score 3.68 → **YES**
- Ran full 36-trial optimization for USDJPY → best: +177.88%, Win 78.7%, PF 5.51, DD -3.29%, Score 5.78 → **YES**
- Ran full 36-trial optimization for AUDUSD → best: +123.91%, Win 52.9%, PF 2.71, DD -12.1%, Score 2.06 → **MAYBE**
- Hit rate limit before starting EURUSD, NZDUSD, USDCHF
- Created empty `optimized_results/NZDUSD/` folder (no content yet)

**Files created:**
- `optimize_oanda.py` ← reusable optimizer (new)
- `optimized_results/GBPUSD/` ← trials.csv, best_config.json, best_result.json, GBPUSD_OPTIMIZATION_REPORT.md
- `optimized_results/USDJPY/` ← trials.csv, best_config.json, best_result.json, USDJPY_OPTIMIZATION_REPORT.md
- `optimized_results/AUDUSD/` ← trials.csv, best_config.json, best_result.json, AUDUSD_OPTIMIZATION_REPORT.md
- `optimized_results/NZDUSD/` ← empty folder only

**What still needs to be done:**
- Run `optimize_oanda.py` for EURUSD, NZDUSD, USDCHF (check exact CLI flags first)
- Create `optimized_results/MASTER_OPTIMIZATION_COMPARISON.md`
- Update this file with Session 8 log

---

---

## Session 6 — OANDA Optimization Results
Completed: 2026-06-08 10:22:08 UTC

Ran 36 trials per pair serially using OANDA parquets only. Applied anti-overfitting filters: minimum 25 trades, minimum 45% win rate, max drawdown no worse than -20%, and ranked valid trials by the required composite score.

| Pair | Return | Win Rate | PF | Max DD | Sharpe | Score | Portfolio | Best Config |
|---|---:|---:|---:|---:|---:|---:|---|---|
| NZDUSD | 50.51% | 63.3% | 2.53 | -10.04% | 7.46 | 2.25 | yes | conf 0.55, RR 1.5, ATR 1.0 |
| EURUSD | 51.99% | 56.0% | 2.62 | -7.64% | 7.46 | 2.14 | yes | conf 0.62, RR 2.0, ATR 1.0 |
| USDCHF | 69.39% | 51.6% | 2.54 | -12.40% | 6.88 | 1.88 | maybe | conf 0.68, RR 2.5, ATR 2.0 |

Output files written under `optimized_results/`, including per-pair trial CSVs/reports and `optimized_results/MASTER_OPTIMIZATION_COMPARISON.md`.

### Session 8 — 2026-06-08 (COMPLETE)
**Agent:** Gemini
**Work done:**
- Ran full 36-trial optimization for EURUSD → best: +51.99%, Win 56.0%, PF 2.62, DD -7.64%, Score 2.14 → **YES**
- Ran full 36-trial optimization for NZDUSD → best: +50.51%, Win 63.3%, PF 2.53, DD -10.04%, Score 2.25 → **YES**
- Ran full 36-trial optimization for USDCHF → best: +69.39%, Win 51.6%, PF 2.54, DD -12.40%, Score 1.88 → **MAYBE**
- Created `optimized_results/MASTER_OPTIMIZATION_COMPARISON.md` (but was missing USDJPY and GBPUSD — fixed by Replit Agent in Session 9)

**Session 9 — 2026-06-08 (Memory update)**
**Agent:** Replit Agent
**Work done:**
- Fixed master comparison to include all 6 pairs (Gemini's version only had the 3 new pairs)
- Calculated correct composite scores for all 6 pairs
- Confirmed final portfolio recommendation: **USDJPY + GBPUSD + NZDUSD + EURUSD**

**All 6 pairs optimized — final scores:**
| Pair | Opt Return | Win% | PF | Max DD | Score | Decision |
|---|---|---|---|---|---|---|
| USDJPY | +177.9% | 78.7 | 5.51 | -3.29% | 5.78 | IN |
| GBPUSD | +239.6% | 63.6 | 4.13 | -6.42% | 3.68 | IN |
| NZDUSD | +50.5% | 63.3 | 2.53 | -10.04% | 2.25 | IN |
| EURUSD | +52.0% | 56.0 | 2.62 | -7.64% | 2.14 | IN |
| AUDUSD | +123.9% | 52.9 | 2.71 | -12.10% | 2.06 | STANDBY |
| USDCHF | +69.4% | 51.6 | 2.54 | -12.40% | 1.88 | STANDBY |

**Next step: Build the Telegram signal bot using USDJPY, GBPUSD, NZDUSD, EURUSD.**
See replit.md Phase 6 for the full signal bot spec. Model configs are in `optimized_results/{PAIR}/best_config.json`.


### Session 10 — 2026-06-08 10:31:25 UTC (Stress Test and Monte Carlo Simulation)
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

### Session 10 — 2026-06-08 (COMPLETE)
**Agent:** (stress test agent)
**Work done:**
- Built `stress_test.py` — Monte Carlo (1,000 runs) + 4 stress scenarios for all 6 pairs
- Created `optimized_results/STRESS_TEST_REPORT.md`

**Key results — the 4 portfolio pairs all passed:**
| Pair | Ruin Prob | Worst DD | Bear Scenario | Verdict |
|---|---|---|---|---|
| USDJPY | 0.0% | -14.14% | +134.42% | ROBUST |
| GBPUSD | 0.0% | -20.70% | +176.34% | ROBUST |
| NZDUSD | 0.0% | -19.27% | +33.81% | ROBUST |
| EURUSD | 0.0% | -21.00% | +35.19% | ROBUST |
| AUDUSD | 0.2% | -31.78% | +84.65% | ROBUST (borderline — hits ruin threshold in 2/1000 runs) |
| USDCHF | 0.0% | -23.48% | +46.51% | ROBUST |

**Known limitation in the report:** Return percentile columns (5th/median/95th) are all identical — shuffling trade order doesn't change the sum of P&Ls, only the drawdown path. The ruin probabilities and drawdown distributions ARE valid.

**Next step: Build the Telegram signal bot.**
Portfolio confirmed: USDJPY + GBPUSD + NZDUSD + EURUSD
Best configs in: `optimized_results/{PAIR}/best_config.json`
Full signal bot spec in: `replit.md` Phase 6


### Session 11 — 2026-06-10 (Telegram Signal Bot — Audit + Complete Rebuild)
**Agent:** Replit Agent

**Context:**
Previous agent (Gemini) attempted to build the Telegram signal bot but left broken code. This session audited the damage and completely rewrote signal_bot.py and test_bot.py.

**What Gemini actually built (in Git/ subfolder):**
- Git/signal_bot.py — existed but had 6 critical bugs (see below)
- Git/test_bot.py — existed but had import errors + missing numpy
- Git/Procfile, requirements_bot.txt, README_DEPLOY.md — fine
- Git/optimized_results/ — all 4 best_config.json files present and correct
- Git/models_live/ — empty folder (correct)
- AGENT_MEMORY.md and replit.md session table — NOT updated by Gemini

**Bugs found in Gemini's signal_bot.py (all fixed in rewrite):**
1. `MODELS_LIVE_PATH` never defined — used as variable name but defined as `MODELS_ROOT` → NameError crash at startup
2. `OPTIMIZED_RESULTS_PATH = "/home/runner/workspace/optimized_results"` — absolute path that does not exist; actual location is `Git/optimized_results/`
3. Config key access wrong: `self.configs[pair]["confidence_threshold"]` → should be `self.configs[pair]["config"]["confidence_threshold"]` (best_config.json has a nested "config" sub-dict)
4. Label mapping wrong: used `prediction in [1, 2]` but actual model labels are 0=BUY, 1=SELL, 2=HOLD (confirmed from pipeline_oanda.py line 227)
5. `LOOKAHEAD_5` used in training but never imported
6. `sys.path` only added Git/ — but `learning/`, `decision/`, etc. live at project root; both paths needed

**Bugs in Gemini's test_bot.py (all fixed):**
- Imported `MODELS_LIVE_PATH` from signal_bot (undefined)
- Missing `import numpy as np`
- Referenced `constants.MODEL_DIR` but `constants` not in scope

**What this session built:**
- Completely rewrote `Git/signal_bot.py` (431 lines) — production quality, all bugs fixed
- Completely rewrote `Git/test_bot.py` (317 lines) — full end-to-end test
- Updated README_DEPLOY.md with correct deployment instructions
- OANDA connection verified live: EURUSD=1.15566, GBPUSD=1.33947, USDJPY=160.344, NZDUSD=0.58174

**Key technical decisions in signal_bot.py:**
- Uses `SCRIPT_DIR = Path(__file__).parent.resolve()` for all paths — works from any directory
- Adds both SCRIPT_DIR (Git/) and PROJECT_ROOT to sys.path so all modules resolve
- Startup training: downloads M5 data via download_oanda_candles(), resamples to M15/M30/H1/H4, saves to temp parquets, patches data_loader_mod.HISTORICAL_DIR, uses DataLoader + ModelTrainer (same as pipeline_oanda.py)
- Live signals: fetch_latest_candles() with count=500, FeaturePipeline.compute_all(), np.argmax(ensemble.predict_proba())
- Label check: `pred in (0, 1)` → BUY=0, SELL=1, HOLD=2
- Config access: `self.configs[pair]["confidence_threshold"]` (stores only the config sub-dict)
- Cooldown: 3600s per pair
- model_params passed as `{"xgboost": cfg["xgb_params"], "random_forest": cfg["rf_params"]}`

**How to run:**
```bash
cd Git
python3 test_bot.py   # full test (requires TELEGRAM_BOT_TOKEN + TELEGRAM_CHAT_ID)
python3 signal_bot.py # run the live bot
```

**For Railway deployment:**
Push the entire Git/ folder contents TO GitHub PLUS the `learning/` directory from the project root (ml/trainer.py imports from it). See README_DEPLOY.md.

**Environment variables required:**
- OANDA_TOKEN ✅ already set
- OANDA_BASE_URL ✅ already set
- TELEGRAM_BOT_TOKEN — user must create via @BotFather
- TELEGRAM_CHAT_ID — user must obtain from Telegram

**Next step:** User creates Telegram bot (takes 2 min via @BotFather), sets TELEGRAM_BOT_TOKEN + TELEGRAM_CHAT_ID as env vars, then runs `python3 Git/test_bot.py` to do the full end-to-end test including Telegram. After that, push to Railway for 24/7 operation.

---

### Session 13 — 2026-06-15 (Dual-Engine Integration)
**Agent:** Gemini CLI
**Work done:**
- Merged external professional "advanced" framework (`external_bot`) into the current project root.
- Unified the directory structure, ensuring all modular "engines" (`intelligence`, `learning`, `decision`, etc.) are correctly positioned.
- Developed `unified_signal_bot.py`: a production-grade script that runs two signal engines concurrently:
    1. **Adaptive Engine:** Fast-startup ML ensemble (startup training).
    2. **Advanced Engine:** Multi-factor conservative engine with Market Scorer, Regime Detection, and Trend Reversal filtering.
- Merged and sorted all dependencies into a master `requirements.txt`.
- Cleaned up the workspace and updated all memory files (`replit.md`, `AGENT_MEMORY.md`).

**Key Results:**
- One single bot now provides two layers of signals (Aggressive/Adaptive + Conservative/Advanced).
- Full support for OANDA, TradeLocker (new), and MT5 (framework ready).
- Improved structural integrity and modularity.

**What remains:**
- Final push to GitHub by the user.
- Test both engines using OANDA credentials in the new `unified_signal_bot.py`.
