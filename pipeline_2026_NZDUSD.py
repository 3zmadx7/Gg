#!/usr/bin/env python3
"""
2026 NZDUSD Pipeline: Dukascopy → Train → Backtest
====================================================
Downloads NZDUSD M1 data for Jan-May 2026 via dukascopy-node,
resamples to all required timeframes, trains ML on Jan-Feb,
and backtests on Mar-May 2026.

Usage:
  python pipeline_2026_NZDUSD.py                  # full run (download + train + backtest)
  python pipeline_2026_NZDUSD.py --skip-download  # skip download, use existing data
  python pipeline_2026_NZDUSD.py --csv path.csv   # use an existing Dukascopy M1 CSV
  python pipeline_2026_NZDUSD.py --backtest-only  # only backtest using trained model
"""

import argparse
import json
import os
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

# Disable LightGBM (requires libgomp not available in this env)
os.environ.setdefault("ENABLE_LIGHTGBM", "false")

import numpy as np
import pandas as pd

# ── constants ──────────────────────────────────────────────────────────────────

SYMBOL = "NZDUSD"
DUKA_INSTRUMENT = "nzdusd"
DUKA_RAW_DIR = Path("data/duka_raw")
STORAGE_DIR = Path("data/historical") / SYMBOL
PIP_SIZE = 0.01 if SYMBOL.endswith("JPY") else 0.0001

TRAIN_FROM = datetime(2026, 1, 1)
TRAIN_TO   = datetime(2026, 2, 28, 23, 59, 59)
TEST_FROM  = datetime(2026, 3, 1)
TEST_TO    = datetime(2026, 5, 31, 23, 59, 59)

# Maps bot timeframe integer → pandas resample rule
TF_RESAMPLE = {
    5:   "5min",
    15:  "15min",
    30:  "30min",
    60:  "1h",
    240: "4h",
}
TF_LABELS = {5: "M5", 15: "M15", 30: "M30", 60: "H1", 240: "H4"}


# ── helpers ────────────────────────────────────────────────────────────────────

def banner(msg: str) -> None:
    print(f"\n{'='*60}")
    print(f"  {msg}")
    print('='*60)


def _load_dukascopy_csv(path: Path) -> pd.DataFrame:
    """Load a dukascopy-node CSV (timestamp in Unix ms) into a DataFrame.
    Returns columns: time (tz-naive UTC), open, high, low, close, volume
    """
    with open(path) as fh:
        header = fh.readline().strip()
    sep = "," if "," in header else ";"

    raw = pd.read_csv(path, sep=sep, skipinitialspace=True,
                      thousands=",", na_values=["", "NA", "N/A"])
    raw.columns = [c.strip().lower() for c in raw.columns]

    ts_col = None
    for cand in ["timestamp", "gmt time", "date & time (utc)", "datetime", "date", "time"]:
        if cand in raw.columns:
            ts_col = cand
            break
    if ts_col is None:
        ts_col = raw.columns[0]

    if ts_col == "timestamp" and pd.api.types.is_numeric_dtype(raw[ts_col]):
        times = pd.to_datetime(raw[ts_col], unit="ms", utc=True).dt.tz_localize(None)
    else:
        _FMT = ["%d.%m.%Y %H:%M:%S.%f", "%d.%m.%Y %H:%M:%S",
                "%Y.%m.%d %H:%M:%S.%f", "%Y.%m.%d %H:%M:%S", "%Y-%m-%d %H:%M:%S"]
        series = raw[ts_col].astype(str).str.strip().str.strip('"')
        times = None
        for fmt in _FMT:
            try:
                times = pd.to_datetime(series, format=fmt, utc=True).dt.tz_localize(None)
                break
            except (ValueError, TypeError):
                continue
        if times is None:
            times = pd.to_datetime(series, utc=True).dt.tz_localize(None)

    df = pd.DataFrame({"time": times})
    for col in ["open", "high", "low", "close", "volume"]:
        df[col] = pd.to_numeric(raw[col], errors="coerce")

    df.dropna(subset=["open", "high", "low", "close"], inplace=True)
    df.sort_values("time", inplace=True)
    df.reset_index(drop=True, inplace=True)
    return df


def _resample_ohlcv(df: pd.DataFrame, rule: str) -> pd.DataFrame:
    """Resample a `time`-indexed OHLCV DataFrame to `rule`."""
    idx = df.set_index("time")
    rs = idx.resample(rule).agg(
        open=("open", "first"),
        high=("high", "max"),
        low=("low", "min"),
        close=("close", "last"),
        volume=("volume", "sum"),
    ).dropna(subset=["open"])
    rs = rs.reset_index()
    rs.sort_values("time", inplace=True)
    return rs.reset_index(drop=True)


# ── Step 1: Download ────────────────────────────────────────────────────────────

def step1_download(csv_override: str | None = None) -> Path:
    """Download M1 NZDUSD data via dukascopy-node; return path to CSV."""
    if csv_override:
        p = Path(csv_override)
        if not p.exists():
            print(f"ERROR: CSV not found: {p}")
            sys.exit(1)
        print(f"Using provided CSV: {p}")
        return p

    DUKA_RAW_DIR.mkdir(parents=True, exist_ok=True)

    existing = sorted(DUKA_RAW_DIR.glob(f"{DUKA_INSTRUMENT}-*.csv"))
    if existing:
        print(f"Found existing download: {existing[-1]}")
        return existing[-1]

    cmd = [
        "npx", "--yes", "dukascopy-node",
        "-i", DUKA_INSTRUMENT,
        "-from", "2026-01-01",
        "-to",   "2026-05-31",
        "-t",    "m1",
        "-v",
        "-f",    "csv",
        "-dir",  str(DUKA_RAW_DIR),
    ]
    print("Downloading NZDUSD M1 data (Jan-May 2026) from Dukascopy...")
    print(f"  {' '.join(cmd)}")
    print("  This may take several minutes — Dukascopy is fetching 5 months of M1 bars.")

    t0 = time.time()
    proc = subprocess.run(cmd, text=True)
    elapsed = time.time() - t0

    if proc.returncode != 0:
        print(f"ERROR: dukascopy-node exited with code {proc.returncode}")
        sys.exit(1)

    csvs = sorted(DUKA_RAW_DIR.glob(f"{DUKA_INSTRUMENT}-*.csv"))
    if not csvs:
        print("ERROR: dukascopy-node finished but no CSV found in data/duka_raw/")
        sys.exit(1)

    csv_path = csvs[-1]
    print(f"  Downloaded in {elapsed:.0f}s → {csv_path}")
    return csv_path


# ── Step 2: Convert & Store ─────────────────────────────────────────────────────

def step2_convert_and_store(csv_path: Path) -> pd.DataFrame:
    """Load M1 CSV, resample to all timeframes, write to bot storage."""
    banner("Step 2 — Convert & Resample to M5/M15/M30/H1/H4")

    print(f"Loading M1 CSV: {csv_path}")
    df_m1 = _load_dukascopy_csv(csv_path)
    rows_m1 = len(df_m1)
    print(f"  M1 rows : {rows_m1:,}")
    print(f"  Range   : {df_m1['time'].min()}  →  {df_m1['time'].max()}")

    # Basic validation
    bad = df_m1[df_m1["high"] < df_m1["low"]]
    if not bad.empty:
        print(f"  Warning: {len(bad)} bars have high < low — dropping them.")
        df_m1 = df_m1[df_m1["high"] >= df_m1["low"]].reset_index(drop=True)

    STORAGE_DIR.mkdir(parents=True, exist_ok=True)

    for tf_int, tf_rule in TF_RESAMPLE.items():
        df_tf = _resample_ohlcv(df_m1, tf_rule)
        out = STORAGE_DIR / f"tf_{tf_int}.parquet"
        df_tf.to_parquet(str(out), index=False, engine="pyarrow", compression="snappy")
        size_kb = out.stat().st_size / 1024
        print(f"  {TF_LABELS[tf_int]:>3}: {len(df_tf):>7,} bars  →  {out}  ({size_kb:.1f} KB)")

    return df_m1


# ── Step 3: Train on Jan-Feb ────────────────────────────────────────────────────

def step3_train() -> object:
    """Load Jan-Feb 2026 data, run feature pipeline, train ensemble."""
    banner("Step 3 — Train ML on Jan + Feb 2026")

    from data.data_loader import DataLoader
    from features.feature_pipeline import FeaturePipeline
    from ml.trainer import ModelTrainer
    from ml.model_manager import ModelManager
    from core.constants import LOOKAHEAD_5

    loader = DataLoader(SYMBOL)
    print("Loading aligned multi-timeframe data from storage...")
    aligned = loader.load_aligned()

    if aligned.empty:
        print("ERROR: No aligned data — run step 2 first.")
        sys.exit(1)

    # Filter to training window
    mask = (aligned["time"] >= TRAIN_FROM) & (aligned["time"] <= TRAIN_TO)
    train_df = aligned[mask].copy().reset_index(drop=True)
    print(f"  All data : {len(aligned):,} bars")
    print(f"  Train    : {len(train_df):,} M5 bars  ({TRAIN_FROM.date()} → {TRAIN_TO.date()})")

    if len(train_df) < 500:
        print("ERROR: Too few training bars. Check the data download.")
        sys.exit(1)

    trainer = ModelTrainer()
    print("\nComputing features...")
    try:
        X, y, feature_cols, df_clean = trainer.prepare_training_data(
            train_df,
            lookahead=LOOKAHEAD_5,
            buy_threshold=0.001,
            sell_threshold=0.001,
            target_type="class",
        )
    except Exception as e:
        print(f"ERROR during feature preparation: {e}")
        raise

    print(f"  Samples  : {len(X):,}")
    print(f"  Features : {len(feature_cols)}")
    label_dist = pd.Series(y).value_counts().to_dict()
    print(f"  Labels   : {label_dist}  (0=HOLD, 1=BUY, 2=SELL)")

    recency = ModelTrainer.compute_recency_weights(df_clean["time"]) if "time" in df_clean.columns else None

    print("\nTraining ensemble models (XGBoost + Random Forest)...")
    t0 = time.time()
    trainer.train_all_models(
        X, y,
        feature_cols=feature_cols,
        target_type="class",
        recency_weights=recency,
    )
    elapsed = time.time() - t0

    ensemble = trainer.get_ensemble()
    num_models = ensemble.get_num_models()
    print(f"  Trained {num_models} model(s) in {elapsed:.1f}s")

    model_manager = ModelManager()
    version = model_manager.save_ensemble(ensemble, timeframe=5)
    print(f"  Model saved as version: {version}")

    return ensemble, feature_cols


# ── Step 4: Backtest Mar-May ────────────────────────────────────────────────────

def step4_backtest(ensemble, feature_cols) -> dict:
    """
    Backtest on Mar-May 2026.

    Fast path:
      1. Compute all features on the full test window ONCE.
      2. Batch-predict every bar in one ensemble.predict_proba(X_all) call.
      3. Pure-Python bar-by-bar simulation using the pre-computed signal array.
    """
    banner("Step 4 — Backtest Mar + Apr + May 2026")

    from data.data_loader import DataLoader
    from features.feature_pipeline import FeaturePipeline
    from learning.performance_analyzer import PerformanceAnalyzer
    from core.constants import TradeDirection
    from core.config import config

    # ── Load and filter test data ──────────────────────────────────────────
    loader = DataLoader(SYMBOL)
    aligned = loader.load_aligned()

    mask = (aligned["time"] >= TEST_FROM) & (aligned["time"] <= TEST_TO)
    test_df = aligned[mask].copy().reset_index(drop=True)
    print(f"  Test period : {len(test_df):,} M5 bars  ({TEST_FROM.date()} → {TEST_TO.date()})")

    if len(test_df) < 300:
        print("ERROR: Not enough test bars.")
        sys.exit(1)

    # ── Compute features ONCE over the full test window ────────────────────
    fp = FeaturePipeline()
    print("  Computing features on full test dataset (one pass)...")
    t0 = time.time()
    test_df = fp.compute_all(test_df)
    print(f"  Features done in {time.time()-t0:.1f}s  |  {len(test_df.columns)} columns")

    # ── Batch-predict every bar in one call ────────────────────────────────
    feat_cols = ensemble.feature_cols or []
    if not feat_cols:
        # Fall back to whatever feature pipeline exposes
        feat_cols = [c for c in fp.get_feature_columns() if c in test_df.columns]

    # Build feature matrix: fill missing cols with 0, NaN → 0
    X_all = test_df.reindex(columns=feat_cols, fill_value=0.0).values
    X_all = np.nan_to_num(X_all, nan=0.0)

    print(f"  Batch-predicting {len(X_all):,} bars × {len(feat_cols)} features...")
    t0 = time.time()
    probas_all = ensemble.predict_proba(X_all)        # shape (n_bars, 3)
    pred_all   = np.argmax(probas_all, axis=1)        # 0=BUY, 1=SELL, 2=HOLD
    conf_all   = np.max(probas_all, axis=1)
    LABEL = {0: "BUY", 1: "SELL", 2: "HOLD"}
    print(f"  Batch prediction done in {time.time()-t0:.1f}s")

    # ── Bar-by-bar trade simulation ────────────────────────────────────────
    perf_analyzer = PerformanceAnalyzer()
    initial_balance = 10_000.0
    balance         = initial_balance
    position        = None
    trades          = []
    equity_curve    = [balance]

    WARMUP       = 200
    max_risk_pct = config.risk.get("max_risk_pct", 0.005)
    sl_floor     = config.risk.get("sl_pips", 30) * PIP_SIZE   # minimum SL distance

    ATR_COL = "atr" if "atr" in test_df.columns else None

    print(f"  Simulating trades (warmup={WARMUP} bars)...")
    t0 = time.time()

    rows = test_df.to_dict("records")   # list of dicts — fast random access

    for i in range(WARMUP, len(rows)):
        row = rows[i]
        ts  = row["time"]
        hi, lo, cl = row["high"], row["low"], row["close"]

        # ── Exit existing position ─────────────────────────────────────────
        if position is not None:
            direction = position["direction"]
            vol       = position["volume"]
            sl, tp    = position["sl"], position["tp"]

            if direction == TradeDirection.BUY.value:
                if lo <= sl:
                    pnl = (sl - position["entry"]) / PIP_SIZE * vol * 10
                    position.update(profit=pnl, exit_time=ts, exit_price=sl, exit_reason="stop_loss")
                    trades.append(dict(position)); balance += pnl; position = None
                elif hi >= tp:
                    pnl = (tp - position["entry"]) / PIP_SIZE * vol * 10
                    position.update(profit=pnl, exit_time=ts, exit_price=tp, exit_reason="take_profit")
                    trades.append(dict(position)); balance += pnl; position = None

            elif direction == TradeDirection.SELL.value:
                if hi >= sl:
                    pnl = (position["entry"] - sl) / PIP_SIZE * vol * 10
                    position.update(profit=pnl, exit_time=ts, exit_price=sl, exit_reason="stop_loss")
                    trades.append(dict(position)); balance += pnl; position = None
                elif lo <= tp:
                    pnl = (position["entry"] - tp) / PIP_SIZE * vol * 10
                    position.update(profit=pnl, exit_time=ts, exit_price=tp, exit_reason="take_profit")
                    trades.append(dict(position)); balance += pnl; position = None

        # ── Open new position using pre-computed signal ────────────────────
        if position is None and i < len(rows) - 5:
            confidence = float(conf_all[i])
            signal     = LABEL[int(pred_all[i])]

            if confidence >= 0.60 and signal in ("BUY", "SELL"):
                atr          = float(row[ATR_COL]) if ATR_COL else sl_floor
                dynamic_sl   = max(atr * 1.5, sl_floor)
                dynamic_tp   = dynamic_sl * 2.0
                risk_amount  = balance * max_risk_pct
                sl_pips_val  = dynamic_sl / PIP_SIZE
                volume       = risk_amount / max(sl_pips_val * PIP_SIZE * 10, 1e-9)
                volume       = max(min(round(volume, 2), 1.0), 0.01)

                position = {
                    "direction":   TradeDirection.BUY.value if signal == "BUY" else TradeDirection.SELL.value,
                    "entry":       cl,
                    "sl":          cl - dynamic_sl if signal == "BUY" else cl + dynamic_sl,
                    "tp":          cl + dynamic_tp if signal == "BUY" else cl - dynamic_tp,
                    "volume":      volume,
                    "entry_time":  ts,
                    "confidence":  confidence,
                    "profit":      0.0,
                }

        open_pnl = position.get("profit", 0.0) if position else 0.0
        equity_curve.append(balance + open_pnl)

    # Close any open position at the last bar
    if position is not None:
        last = rows[-1]
        direction = position["direction"]
        pnl = ((last["close"] - position["entry"]) if direction == TradeDirection.BUY.value
               else (position["entry"] - last["close"])) / PIP_SIZE * position["volume"] * 10
        position.update(profit=pnl, exit_time=last["time"],
                        exit_price=last["close"], exit_reason="end_of_data")
        trades.append(dict(position)); balance += pnl

    elapsed = time.time() - t0
    print(f"  Simulation complete in {elapsed:.1f}s")

    perf = perf_analyzer.analyze_trades(trades, start_balance=initial_balance)
    perf["equity_curve"] = equity_curve
    perf["final_balance"] = balance
    perf["total_return_pct"] = (balance - initial_balance) / initial_balance * 100
    perf["initial_balance"] = initial_balance
    perf["trades"] = trades
    perf["test_from"] = str(TEST_FROM.date())
    perf["test_to"] = str(TEST_TO.date())
    return perf


# ── Step 5: Report ───────────────────────────────────────────────────────────────

def step5_report(results: dict) -> None:
    banner("Step 5 — Backtest Report")

    total     = results.get("total_trades", 0)
    wins      = results.get("winning_trades", 0)
    losses    = results.get("losing_trades", 0)
    win_rate  = results.get("win_rate", 0)
    pf        = results.get("profit_factor", 0)
    net       = results.get("net_profit", 0)
    ret_pct   = results.get("total_return_pct", 0)
    max_dd    = results.get("max_drawdown", 0)
    sharpe    = results.get("sharpe_ratio", 0)
    sortino   = results.get("sortino_ratio", 0)
    exp       = results.get("expectancy", 0)
    avg_win   = results.get("avg_win", 0)
    avg_loss  = results.get("avg_loss", 0)
    init_bal  = results.get("initial_balance", 10_000)
    fin_bal   = results.get("final_balance", init_bal)

    print(f"  Period          : {results.get('test_from')} → {results.get('test_to')}")
    print(f"  Initial balance : ${init_bal:,.2f}")
    print(f"  Final balance   : ${fin_bal:,.2f}")
    print(f"  Total return    : {ret_pct:+.2f}%")
    print(f"  Net profit      : ${net:+,.2f}")
    print()
    print(f"  Total trades    : {total}")
    print(f"  Winning trades  : {wins}  ({win_rate:.1f}%)")
    print(f"  Losing trades   : {losses}")
    print(f"  Profit factor   : {pf:.2f}")
    print(f"  Avg win         : ${avg_win:+,.2f}")
    print(f"  Avg loss        : ${avg_loss:+,.2f}")
    print(f"  Expectancy      : ${exp:+,.2f}")
    print()
    print(f"  Max drawdown    : {max_dd:.2f}%")
    print(f"  Sharpe ratio    : {sharpe:.2f}")
    print(f"  Sortino ratio   : {sortino:.2f}")

    # Trade breakdown by exit reason
    trades = results.get("trades", [])
    if trades:
        tp_count = sum(1 for t in trades if t.get("exit_reason") == "take_profit")
        sl_count = sum(1 for t in trades if t.get("exit_reason") == "stop_loss")
        eod_count = sum(1 for t in trades if t.get("exit_reason") == "end_of_data")
        print()
        print(f"  Take-profit exits : {tp_count}")
        print(f"  Stop-loss exits   : {sl_count}")
        print(f"  End-of-data exits : {eod_count}")

    # Save report
    results_dir = Path("results") / SYMBOL
    results_dir.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_path = results_dir / f"backtest_2026_{ts}.json"

    saveable = {k: v for k, v in results.items()
                if k not in ("equity_curve", "trades")}
    if trades:
        saveable["trades"] = [
            {k2: str(v2) if not isinstance(v2, (int, float, str)) else v2
             for k2, v2 in t.items()} for t in trades
        ]

    with open(report_path, "w") as f:
        json.dump(saveable, f, indent=2, default=str)
    print(f"\n  Full report saved → {report_path}")


# ── CLI ──────────────────────────────────────────────────────────────────────────

def parse_args():
    p = argparse.ArgumentParser(description="2026 NZDUSD Dukascopy → Train → Backtest pipeline")
    p.add_argument("--csv", default=None, metavar="PATH",
                   help="Use an existing Dukascopy M1 CSV instead of downloading")
    p.add_argument("--skip-download", action="store_true",
                   help="Skip download; use whatever CSV is in data/duka_raw/")
    p.add_argument("--skip-convert", action="store_true",
                   help="Skip convert/resample; assume parquets already exist")
    p.add_argument("--backtest-only", action="store_true",
                   help="Load saved model and run backtest only (skip train)")
    return p.parse_args()


def main():
    args = parse_args()
    banner("2026 NZDUSD Pipeline  |  Train: Jan-Feb  |  Test: Mar-May")
    print(f"  Symbol   : {SYMBOL}")
    print(f"  Train    : {TRAIN_FROM.date()} → {TRAIN_TO.date()}")
    print(f"  Backtest : {TEST_FROM.date()} → {TEST_TO.date()}")

    # ── Step 1 ──────────────────────────────────────────────────────────────
    if not args.skip_download and not args.skip_convert and not args.backtest_only:
        banner("Step 1 — Download NZDUSD M1 Data (Jan-May 2026)")
        csv_path = step1_download(csv_override=args.csv)
    elif args.csv:
        csv_path = Path(args.csv)
    else:
        existing = sorted(DUKA_RAW_DIR.glob(f"{DUKA_INSTRUMENT}-*.csv")) if DUKA_RAW_DIR.exists() else []
        csv_path = existing[-1] if existing else None

    # ── Step 2 ──────────────────────────────────────────────────────────────
    if not args.skip_convert and not args.backtest_only:
        if csv_path is None:
            print("ERROR: No CSV found. Run without --skip-convert or provide --csv.")
            sys.exit(1)
        step2_convert_and_store(csv_path)

    if not (STORAGE_DIR / "tf_5.parquet").exists():
        print(f"ERROR: {STORAGE_DIR}/tf_5.parquet not found. Run step 2 first.")
        sys.exit(1)

    # ── Step 3 ──────────────────────────────────────────────────────────────
    if not args.backtest_only:
        ensemble, feature_cols = step3_train()
    else:
        banner("Step 3 — Loading saved model")
        from ml.model_manager import ModelManager
        mm = ModelManager()
        # Pick the newest trained version for M5 (numeric sort to avoid v9 > v11)
        all_versions = mm.list_versions(timeframe=5)
        def _version_num(v: str) -> int:
            try:
                return int(v.split("_")[0].replace("v", ""))
            except Exception:
                return 0
        all_versions_sorted = sorted(all_versions, key=_version_num)
        if not all_versions_sorted:
            print("ERROR: No saved M5 model found. Run training first.")
            sys.exit(1)
        latest_v = all_versions_sorted[-1]
        print(f"  Loading version: {latest_v}")
        ensemble = mm.load_ensemble(latest_v)
        feature_cols = ensemble.feature_cols or []
        if ensemble.get_num_models() == 0:
            print(f"ERROR: Model {latest_v} has 0 loaded sub-models.")
            sys.exit(1)
        print(f"  Loaded ensemble with {ensemble.get_num_models()} model(s)")

    # ── Step 4 ──────────────────────────────────────────────────────────────
    results = step4_backtest(ensemble, feature_cols)

    # ── Step 5 ──────────────────────────────────────────────────────────────
    step5_report(results)

    banner("Pipeline complete!")


if __name__ == "__main__":
    main()
