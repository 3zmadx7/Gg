# Project Coordinator File — AI Forex Trading Bot
> **This file is the single source of truth for any AI agent (or human) picking up this project.**
> It captures the full conversation history, every decision made, current state, and future plans.
> When starting a new session, just say: **"Read replit.md"** and you will understand everything.

---

## Who Is the User

- Non-technical ("noob on technical things" — his words). Knows how to push files to GitHub and connect GitHub to Railway for 24/7 hosting. That's about it.
- Communicates informally and directly. Gets straight to the point.
- Wants results and explanations in plain language — no jargon without translation.
- Decision-making style: reviews results, approves direction, then delegates execution.
- Workflow: uses multiple AI agents (Replit Agent, Codex/ChatGPT) in sequence. Each agent picks up from the memory files.

## User Preferences
- No frontend, no UI — console output only
- No unnecessary reinstallation of packages or re-downloading of data that already exists
- Keep explanations short and clear
- Always explain BEFORE coding anything significant
- Results should always include a comparison table across pairs
- When explaining deployment/infra topics, relate to tools he already knows (GitHub, Railway)

---

## What This Project Is

A **Python-based AI Forex Trading Bot** originally imported from GitHub into Replit. It was adapted to:
- Use **Dukascopy M1 bid-price CSV data** (free, no account needed) instead of MetaTrader5
- Run a clean **download → train → backtest pipeline** from a single Python script
- Test multiple currency pairs using ML (XGBoost + RandomForest ensemble)
- Produce console output + JSON results for each run

There is **no live trading** in this project yet. Everything so far is backtesting.

---

## The Full Conversation — What Was Discussed and Decided

### Phase 1 — Building the Foundation (Session 1)
The user imported a GitHub forex bot repo into Replit. The original bot required MetaTrader5 (Windows-only) and had no clean data pipeline. We rebuilt the data layer:

- Installed Node.js 20 so `npx dukascopy-node` could download historical M1 data
- Created `pipeline_2026.py` — a single script that does everything: download → resample → train → backtest → report
- Downloaded EURUSD M1 data for Jan–May 2026 (149,010 bars) from Dukascopy (free, no account)
- Resampled M1 → M5/M15/M30/H1/H4 and saved as Parquet files
- Trained XGBoost + RandomForest ensemble on Jan–Feb 2026
- Backtested on Mar–May 2026

**EURUSD result: +114.88% return in 3 months, 58.5% win rate, profit factor 2.70**

A bug was found and fixed: `ModelManager.list_versions()` sorts alphabetically, so `v9 > v11` in string sort. Fixed by sorting numerically using `int(version.replace("v",""))`.

### Phase 2 — GBPUSD Test (Session 2, Codex agent)
User wanted to test another pair. Codex created `pipeline_2026_GBPUSD.py` and ran the full pipeline.

**GBPUSD result: +222.00% return, 62.4% win rate, profit factor 3.31, max drawdown only -4.72%**

GBPUSD outperformed EURUSD on every metric. The agent also created `results/GBPUSD/GBPUSD_REPORT.md` with a full comparison table.

### Phase 3 — Multi-pair expansion (Session 3, Codex agent — hit rate limit)
User wanted to test USDJPY, AUDUSD, USDCHF, NZDUSD. Codex created all 4 pipeline files and managed to run USDJPY and AUDUSD before hitting the rate limit.

**USDJPY result: +247.29% return, 64.0% win rate, profit factor 3.41** (best so far)
**AUDUSD result: +98.67% return, 51.6% win rate, profit factor 2.06** (weakest so far)

Session 3 ended without: USDJPY/AUDUSD report MD files, USDCHF run, NZDUSD run, master comparison file.

### Phase 4 — Switch to OANDA API (latest decision)
The user obtained an OANDA practice account API token. We agreed to switch from Dukascopy to OANDA as the data source because Dukascopy downloads via `npx dukascopy-node` caused repeated errors and timeouts across multiple agent sessions.

**Key decisions made:**
- Old Dukascopy results in `results/` are kept as-is — do NOT delete them
- OANDA results go in a completely separate folder: `results_oanda/`
- OANDA models go in `models_oanda/` — do NOT mix with the old `models/` folder
- OANDA historical data goes in `data/historical_oanda/` — separate from `data/historical/`
- All 6 pairs are re-run fresh with OANDA data: EURUSD, GBPUSD, USDJPY, AUDUSD, USDCHF, NZDUSD
- Train on Jan–Feb 2026, backtest on Mar–May 2026 (same dates as before)

**Credentials — already saved as Replit environment variables:**
```
OANDA_TOKEN    → read via os.environ["OANDA_TOKEN"]
OANDA_BASE_URL → read via os.environ["OANDA_BASE_URL"]
```
This is a **practice account** (fxpractice.oanda.com). Never hardcode token values into any file.

**OANDA instrument names (different from Dukascopy):**
EUR_USD, GBP_USD, USD_JPY, AUD_USD, USD_CHF, NZD_USD

**OANDA candles API:**
```
GET {OANDA_BASE_URL}/instruments/{instrument}/candles
Header: Authorization: Bearer {OANDA_TOKEN}
Params: granularity=M1, from=2026-01-01T00:00:00Z, to=2026-05-31T23:59:59Z, price=M, count=5000
```
Response uses `candles[].mid.{o,h,l,c}` and `candles[].volume`. Only use rows where `complete=true`. Paginate if needed (max 5000 candles per call).

**What still needs to be built (no code written yet):**
1. `data/oanda_downloader.py` — fetches M1 candles from OANDA, returns clean DataFrame
2. `pipeline_oanda.py` — base template using OANDA downloader instead of Dukascopy
3. `pipeline_oanda_EURUSD.py`, `pipeline_oanda_GBPUSD.py`, etc. — one per pair
4. Run all 6, write reports, write master comparison, write OANDA vs Dukascopy comparison

See `AGENT_MEMORY.md` Section 9 for the full technical spec.

### Phase 5 — Optimization for Hedge Fund Portfolio (current phase)
The user reviewed the OANDA results and decided to optimize each pair before building the Telegram bot. The goal was stated as: *"build a system like a hedge fund"* — multiple pairs running simultaneously, each with the best possible settings, combined into one professional signal system.

**Key decisions made:**
- Optimize all 6 pairs, one at a time
- Scoring is risk-adjusted, not just raw return — a pair with +150% and -8% drawdown beats one with +300% and -30% drawdown
- USDCHF is flagged for likely removal (39% win rate, -27% drawdown baseline — fundamentally weak)
- Target: select the best **3–4 pairs** for the final Telegram signal bot portfolio
- Anti-overfitting rules are strict: minimum 25 trades, minimum 45% win rate, max -20% drawdown per trial
- 30–50 trials per pair (not 100 — more than that overfits on 2 months of training data)
- Output: `optimized_results/{PAIR}/` — does NOT touch any existing folders

**What gets optimized (in priority order):**
1. Confidence threshold (0.55–0.75)
2. Risk-Reward ratio (1:1.5 to 1:3)
3. ATR stop-loss multiplier (1.0–2.0×)
4. Training window length (2 months vs 3 months)
5. XGBoost/RF hyperparameters (secondary)
6. Timeframe (M5 vs M15 — only if pair still underperforms)

Full technical spec is in `AGENT_MEMORY.md` LATEST HANDOFF section.

### Phase 6 — Signal Bot Discussion (no code written yet)
The user asked: *"Can we turn this into a Telegram signal bot?"*

**Answer: Yes. Here is the full plan that was agreed:**

#### How the signal bot works
- A Python script runs in an infinite loop, waking up every 5 minutes on the M5 candle close
- It fetches the latest ~300 M5 candles from **Dukascopy's free public REST API** (same data source as training — no mismatch, no account needed)
- Computes the same 115 features the model was trained on
- Runs `ensemble.predict_proba()` on the latest candle
- If `confidence >= 0.60` AND signal is BUY or SELL → sends a Telegram message

#### What a signal message looks like
```
🟢 BUY EURUSD
Entry:  1.1532
SL:     1.1502  (-30 pips)
TP:     1.1592  (+60 pips)
Confidence: 81.6%
Time: 14:30 UTC
```

#### Live data source chosen: Dukascopy public REST API
- Free, no account required
- Same data as training data → no train/live mismatch
- Already available without any new credentials

#### Does the model need retraining?
- **No, not immediately.** The saved model (`models/model_v11_M5/` for EURUSD) loads instantly and can be used for live signals right away.
- Long-term: a monthly rolling retrain (last 2 months of data) is recommended to keep the model fresh as market conditions evolve. This would be a separate optional script.

#### What the user needs to provide
Only two things from Telegram:
1. **Bot Token** — created for free via @BotFather on Telegram (takes 2 minutes)
2. **Chat ID** — the user's personal Telegram chat ID

No broker account, no exchange API, no paid data feed.

### Phase 5 — Deployment Plan Discussion (no code written yet)
The user plans to deploy via **Railway + GitHub** (tools he already knows how to use).

**The agreed deployment plan:**
1. Agent packages everything into a clean GitHub-ready folder
2. User pushes it to a new GitHub repo (drag & drop in GitHub UI)
3. User connects that repo to Railway (one click)
4. User pastes `TELEGRAM_TOKEN` and `TELEGRAM_CHAT_ID` in Railway's Variables panel
5. Railway starts the bot automatically, runs 24/7
6. Signals arrive on Telegram

**What goes in the GitHub repo:**
- The signal bot Python script (runs forever, checks every 5 min)
- The trained model folder (`models/model_v11_M5/` or whichever pair is chosen)
- `requirements.txt`
- `Procfile` or `railway.json` telling Railway how to start the script
- Simple `README.md` explaining the two settings to paste

**This has NOT been coded yet.** It is the next major feature after the multi-pair testing is complete.

---

## Current State of All Pairs

| Pair | Model | Return | Win Rate | Profit Factor | Max DD | Sharpe | Status |
|---|---|---:|---:|---:|---:|---:|---|
| EURUSD | v11_M5 | +114.88% | 58.5% | 2.70 | -9.92% | 7.74 | ✅ Complete |
| GBPUSD | v12_M5 | +222.00% | 62.4% | 3.31 | -4.72% | 9.51 | ✅ Complete |
| USDJPY | v13_M5 | +247.29% | 64.0% | 3.41 | -8.04% | 9.56 | ✅ Backtest done, report MD missing |
| AUDUSD | v14_M5 | +98.67% | 51.6% | 2.06 | -11.95% | 5.47 | ✅ Backtest done, report MD missing |
| USDCHF | — | — | — | — | — | — | ❌ Not started (pipeline file exists) |
| NZDUSD | — | — | — | — | — | — | ❌ Not started (pipeline file exists) |

All pipelines trained on **Jan–Feb 2026**, backtested on **Mar–May 2026**, starting balance **$10,000**.

---

## Immediate Next Tasks (in order)

> **PRIORITY SHIFT: The user now has an OANDA API. All new work uses OANDA data.
> The old Dukascopy results stay in `results/` — do not touch them.
> All OANDA work goes in new separate folders.**

### OANDA Tasks (do these first — current priority)
1. **Create `data/oanda_downloader.py`** — OANDA REST API client that downloads M1 candles and returns a clean DataFrame. Must paginate (max 5000 bars per call). Credentials from `os.environ["OANDA_TOKEN"]` and `os.environ["OANDA_BASE_URL"]`.
2. **Create `pipeline_oanda.py`** — base pipeline template using OANDA downloader instead of Dukascopy. Saves data to `data/historical_oanda/`, models to `models_oanda/`, results to `results_oanda/`.
3. **Run all 6 pairs one at a time:**
   - `python3 pipeline_oanda_EURUSD.py`
   - `python3 pipeline_oanda_GBPUSD.py`
   - `python3 pipeline_oanda_USDJPY.py`
   - `python3 pipeline_oanda_AUDUSD.py`
   - `python3 pipeline_oanda_USDCHF.py`
   - `python3 pipeline_oanda_NZDUSD.py`
4. **Write report MD for each pair** in `results_oanda/{PAIR}/{PAIR}_REPORT.md`
5. **Create `results_oanda/MASTER_COMPARISON_OANDA.md`** — all 6 pairs in one table
6. **Create `results_oanda/OANDA_VS_DUKASCOPY.md`** — compare OANDA vs Dukascopy results for EURUSD and GBPUSD side by side
7. **Update `AGENT_MEMORY.md`** with Session 4 results

### OANDA Optimization (current priority — do this before the Telegram bot)
8. **Run optimization for each pair** — see `AGENT_MEMORY.md` LATEST HANDOFF for the full spec. 30–50 trials per pair, one pair at a time. Output goes to `optimized_results/{PAIR}/`.
9. **Create `optimized_results/MASTER_OPTIMIZATION_COMPARISON.md`** — baseline vs optimized for all 6 pairs, plus final portfolio recommendation (which 3–4 pairs to include in the Telegram bot).

### After optimization is complete
10. **Build the Telegram signal bot** — see Phase 5 in the conversation history above for full spec. Use only the pairs recommended by the optimization master comparison.
11. **Package for Railway/GitHub deployment** — see Phase 6 above for full spec.

---

## Technical Reference — Environment

| Item | Status |
|---|---|
| Python 3 | ✅ Available |
| Node.js 20 + `npx` | ✅ Installed via Nix |
| `dukascopy-node` npm package | ✅ Cached in `node_modules` |
| `xgboost`, `scikit-learn`, `pandas`, `numpy`, `pyarrow`, `joblib`, `rich` | ✅ Installed |
| `lightgbm` | ⚠️ DISABLED — `libgomp.so.1` missing. `ENABLE_LIGHTGBM=false` env var set |
| `LSTM` | ⚠️ DISABLED — `ENABLE_LSTM=false` env var set |
| MetaTrader5 | ❌ Windows-only, not installed, handled gracefully in code |

**Do NOT reinstall packages or re-download data that already exists.**

---

## Technical Reference — Key Files

| File | Purpose |
|---|---|
| `pipeline_2026.py` | Main EURUSD pipeline |
| `pipeline_2026_GBPUSD.py` | GBPUSD pipeline |
| `pipeline_2026_USDJPY.py` | USDJPY pipeline |
| `pipeline_2026_AUDUSD.py` | AUDUSD pipeline |
| `pipeline_2026_USDCHF.py` | USDCHF pipeline (not yet run) |
| `pipeline_2026_NZDUSD.py` | NZDUSD pipeline (not yet run) |
| `data/data_loader.py` | Loads parquet data for any symbol |
| `data/dukascopy_converter.py` | Parses Dukascopy M1 CSV → DataFrame |
| `ml/ensemble.py` | VotingEnsemble — `predict_proba(X)` |
| `ml/model_manager.py` | Saves/loads versioned models |
| `AGENT_MEMORY.md` | Technical memory for coding agents (more detail than this file) |

---

## Technical Reference — Known Bugs

| Bug | Status |
|---|---|
| Model version alphabetical sort (`v9 > v11`) | ✅ Fixed in all pipeline files |
| Sortino ratio shows `0.0` on some pairs | ⚠️ Known display bug, non-critical, do not fix |
| MT5 import error on startup | ✅ Handled gracefully, safe to ignore |

---

## Important Conventions

- **Dukascopy instrument names:** always lowercase, no slash — `eurusd`, `gbpusd`, `usdjpy`, `audusd`, `usdchf`, `nzdusd`
- **Model naming:** `model_v{N}_M5/` — auto-increments. Current highest: `v14_M5` (AUDUSD). Next will be v15 (USDCHF), v16 (NZDUSD)
- **Run pipelines one at a time** — parallel runs cause model version conflicts
- **Parquet `time` column** must be tz-naive UTC datetime — this is required by DataLoader
- **Confidence threshold for signals:** `>= 0.60`
- **Signal labels:** 0=HOLD, 1=BUY, 2=SELL (inside the model); displayed as BUY/SELL/HOLD in output
- **Always use batch prediction** (`ensemble.predict_proba(X_all)` on full dataset at once) — never bar-by-bar in backtests

---

## Replit Workflow

Name: **"Run Pipeline 2026"**
Command: `python3 pipeline_2026.py --backtest-only`

To run a full pipeline (download + train + backtest), run directly in Shell:
```bash
python3 pipeline_2026_{PAIR}.py
```

---

## Session History Summary

| Session | Agent | Date | What was done |
|---|---|---|---|
| 1 | Replit Agent | 2026-06-07 | Built full pipeline, ran EURUSD (+114.88%) with Dukascopy data |
| 2 | Codex | 2026-06-07 | Ran GBPUSD (+222.00%) with Dukascopy data |
| 3 | Codex | 2026-06-07 | Ran USDJPY (+247.29%) and AUDUSD (+98.67%) with Dukascopy data, hit rate limit |
| 4 | Replit Agent | 2026-06-07 | Saved OANDA credentials, updated memory files, defined OANDA pipeline spec |
| 5 | Codex | 2026-06-07 | Built OANDA pipeline, ran all 6 pairs, wrote reports + master comparison |
| 6 | Replit Agent | 2026-06-07 | Reviewed OANDA results, defined optimization strategy + hedge fund vision |
| 7 | Codex | 2026-06-08 | Optimized GBPUSD (+239%, PF 4.13 ✅), USDJPY (+178%, PF 5.51 ✅), AUDUSD (+124%, PF 2.71 MAYBE) — hit rate limit |
| 8 | Gemini | 2026-06-08 | Optimized EURUSD (+52%, PF 2.62 ✅), NZDUSD (+51%, PF 2.53 ✅), USDCHF (+69%, PF 2.54 MAYBE) — master comparison written (incomplete) |
| 9 | Replit Agent | 2026-06-08 | Fixed master comparison (was missing USDJPY + GBPUSD), confirmed final portfolio: USDJPY + GBPUSD + NZDUSD + EURUSD |
| 10 | Replit Agent | 2026-06-08 | Built and ran Stress Test + Monte Carlo simulation for all 6 pairs, generated `STRESS_TEST_REPORT.md` |
| 11 | Gemini | 2026-06-09 | Attempted signal bot build — put files in `Git/` subfolder but left 6 critical bugs in signal_bot.py; AGENT_MEMORY + replit.md NOT updated |
| 12 | Replit Agent | 2026-06-10 | Audited Gemini's work, found and documented all bugs, completely rewrote `Git/signal_bot.py` + `Git/test_bot.py`, updated `Git/README_DEPLOY.md`, confirmed OANDA live connection for all 4 pairs |
| 13 | Gemini CLI | 2026-06-15 | Merged external professional framework with existing advanced modules. Developed `unified_signal_bot.py` with Dual-Engine support (Adaptive + Advanced Modular). Prepared project for unified GitHub push and Railway deployment. |

---

## Quick Reference — Folder Structure (what goes where)

| Folder | Contents | Touch it? |
|---|---|---|
| `results/` | Old Dukascopy backtest JSONs and reports | ❌ Leave alone |
| `models/` | Old Dukascopy trained models (v11–v14) | ❌ Leave alone |
| `data/historical/` | Old Dukascopy parquet files | ❌ Leave alone |
| `data/duka_raw/` | Old Dukascopy raw CSVs | ❌ Leave alone |
| `results_oanda/` | New OANDA backtest results | ✅ Write here |
| `models_oanda/` | New OANDA trained models | ✅ Write here |
| `data/historical_oanda/` | New OANDA parquet files | ✅ Write here |
| `data/oanda_downloader.py` | New OANDA API client | ✅ Create this |
| `pipeline_oanda_*.py` | New OANDA pipeline scripts | ✅ Create these |
| `AGENT_MEMORY.md` | Technical agent memory | ✅ Append session log when done |
| `replit.md` | This coordinator file | ✅ Coordinator updates it |
