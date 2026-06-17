#!/usr/bin/env python3
"""
2026 OANDA Pipeline: Download -> Train -> Backtest
==================================================
Downloads OANDA M1 midpoint data for Jan-May 2026, resamples to all required
timeframes, trains on Jan-Feb, and backtests on Mar-May.
"""

import argparse
import json
import os
import sys
import time
from datetime import datetime
from pathlib import Path

os.environ.setdefault("ENABLE_LIGHTGBM", "false")

import numpy as np
import pandas as pd

from data.oanda_downloader import download_oanda_candles


SYMBOL = os.environ.get("OANDA_SYMBOL", "EURUSD")
OANDA_INSTRUMENT = os.environ.get("OANDA_INSTRUMENT", "EUR_USD")
DATA_ROOT = Path("data/historical_oanda")
STORAGE_DIR = DATA_ROOT / SYMBOL
RESULTS_ROOT = Path("results_oanda")
MODELS_ROOT = Path("models_oanda")
PIP_SIZE = 0.01 if SYMBOL.endswith("JPY") else 0.0001

TRAIN_FROM = datetime(2026, 1, 1)
TRAIN_TO = datetime(2026, 2, 28, 23, 59, 59)
TEST_FROM = datetime(2026, 3, 1)
TEST_TO = datetime(2026, 5, 31, 23, 59, 59)
FULL_FROM = datetime(2026, 1, 1)
FULL_TO = datetime(2026, 5, 31, 23, 59, 59)

TF_RESAMPLE = {
    5: "5min",
    15: "15min",
    30: "30min",
    60: "1h",
    240: "4h",
}
TF_LABELS = {1: "M1", 5: "M5", 15: "M15", 30: "M30", 60: "H1", 240: "H4"}


def banner(msg: str) -> None:
    print(f"\n{'=' * 60}")
    print(f"  {msg}")
    print("=" * 60)


def _patch_oanda_paths() -> None:
    import data.data_loader as data_loader
    import ml.model_manager as model_manager

    data_loader.HISTORICAL_DIR = str(DATA_ROOT)
    model_manager.MODEL_DIR = str(MODELS_ROOT)


def _resample_ohlcv(df: pd.DataFrame, rule: str) -> pd.DataFrame:
    idx = df.set_index("time")
    rs = (
        idx.resample(rule)
        .agg(
            open=("open", "first"),
            high=("high", "max"),
            low=("low", "min"),
            close=("close", "last"),
            volume=("volume", "sum"),
        )
        .dropna(subset=["open"])
    )
    rs = rs.reset_index()
    rs.sort_values("time", inplace=True)
    return rs.reset_index(drop=True)


def step1_download() -> pd.DataFrame:
    banner(f"Step 1 - Download {SYMBOL} M1 Data From OANDA")
    print(f"  Instrument : {OANDA_INSTRUMENT}")
    print(f"  Range      : {FULL_FROM} -> {FULL_TO}")
    df = download_oanda_candles(OANDA_INSTRUMENT, "M1", FULL_FROM, FULL_TO)
    if df.empty:
        print("ERROR: OANDA returned no complete candles.")
        sys.exit(1)
    print(f"  M1 rows    : {len(df):,}")
    print(f"  Data range : {df['time'].min()} -> {df['time'].max()}")
    return df


def step2_store(df_m1: pd.DataFrame) -> None:
    banner("Step 2 - Store M1 And Resample To M5/M15/M30/H1/H4")
    bad = df_m1[df_m1["high"] < df_m1["low"]]
    if not bad.empty:
        print(f"  Warning: dropping {len(bad)} bars where high < low.")
        df_m1 = df_m1[df_m1["high"] >= df_m1["low"]].reset_index(drop=True)

    STORAGE_DIR.mkdir(parents=True, exist_ok=True)
    out_m1 = STORAGE_DIR / "tf_1.parquet"
    df_m1.to_parquet(str(out_m1), index=False, engine="pyarrow", compression="snappy")
    print(f"  {TF_LABELS[1]:>3}: {len(df_m1):>7,} bars -> {out_m1}")

    for tf_int, tf_rule in TF_RESAMPLE.items():
        df_tf = _resample_ohlcv(df_m1, tf_rule)
        out = STORAGE_DIR / f"tf_{tf_int}.parquet"
        df_tf.to_parquet(str(out), index=False, engine="pyarrow", compression="snappy")
        print(f"  {TF_LABELS[tf_int]:>3}: {len(df_tf):>7,} bars -> {out}")


def step3_train() -> tuple[object, list[str], str]:
    banner("Step 3 - Train ML On Jan + Feb 2026")
    _patch_oanda_paths()

    from core.constants import LOOKAHEAD_5
    from data.data_loader import DataLoader
    from ml.model_manager import ModelManager
    from ml.trainer import ModelTrainer

    loader = DataLoader(SYMBOL)
    aligned = loader.load_aligned()
    mask = (aligned["time"] >= TRAIN_FROM) & (aligned["time"] <= TRAIN_TO)
    train_df = aligned[mask].copy().reset_index(drop=True)
    print(f"  All data : {len(aligned):,} bars")
    print(f"  Train    : {len(train_df):,} M5 bars ({TRAIN_FROM.date()} -> {TRAIN_TO.date()})")
    if len(train_df) < 500:
        print("ERROR: Too few training bars.")
        sys.exit(1)

    trainer = ModelTrainer()
    print("  Computing features...")
    X, y, feature_cols, df_clean = trainer.prepare_training_data(
        train_df,
        lookahead=LOOKAHEAD_5,
        buy_threshold=0.001,
        sell_threshold=0.001,
        target_type="class",
    )
    print(f"  Samples  : {len(X):,}")
    print(f"  Features : {len(feature_cols)}")
    print(f"  Labels   : {pd.Series(y).value_counts().to_dict()} (0=HOLD, 1=BUY, 2=SELL)")

    recency = ModelTrainer.compute_recency_weights(df_clean["time"]) if "time" in df_clean.columns else None
    t0 = time.time()
    trainer.train_all_models(
        X,
        y,
        feature_cols=feature_cols,
        target_type="class",
        recency_weights=recency,
    )
    ensemble = trainer.get_ensemble()
    print(f"  Trained {ensemble.get_num_models()} model(s) in {time.time() - t0:.1f}s")

    model_manager = ModelManager()
    version = model_manager.save_ensemble(ensemble, timeframe=5)
    print(f"  Model saved as version: {version}")
    return ensemble, feature_cols, version


def _version_num(version: str) -> int:
    try:
        return int(version.split("_")[0].replace("v", ""))
    except Exception:
        return 0


def step3_load_latest() -> tuple[object, list[str], str]:
    banner("Step 3 - Load Latest OANDA Model")
    _patch_oanda_paths()

    from ml.model_manager import ModelManager

    mm = ModelManager()
    versions = sorted(mm.list_versions(timeframe=5), key=_version_num)
    if not versions:
        print("ERROR: No saved OANDA M5 model found.")
        sys.exit(1)
    latest = versions[-1]
    ensemble = mm.load_ensemble(latest)
    if ensemble.get_num_models() == 0:
        print(f"ERROR: Model {latest} has 0 loaded sub-models.")
        sys.exit(1)
    print(f"  Loaded {latest} with {ensemble.get_num_models()} model(s)")
    return ensemble, ensemble.feature_cols or [], latest


def step4_backtest(ensemble, feature_cols: list[str], model_version: str) -> dict:
    banner("Step 4 - Backtest Mar + Apr + May 2026")
    _patch_oanda_paths()

    from core.config import config
    from core.constants import TradeDirection
    from data.data_loader import DataLoader
    from features.feature_pipeline import FeaturePipeline
    from learning.performance_analyzer import PerformanceAnalyzer

    loader = DataLoader(SYMBOL)
    aligned = loader.load_aligned()
    mask = (aligned["time"] >= TEST_FROM) & (aligned["time"] <= TEST_TO)
    test_df = aligned[mask].copy().reset_index(drop=True)
    print(f"  Test period : {len(test_df):,} M5 bars ({TEST_FROM.date()} -> {TEST_TO.date()})")
    if len(test_df) < 300:
        print("ERROR: Not enough test bars.")
        sys.exit(1)

    fp = FeaturePipeline()
    print("  Computing features on full test dataset...")
    t0 = time.time()
    test_df = fp.compute_all(test_df)
    print(f"  Features done in {time.time() - t0:.1f}s | {len(test_df.columns)} columns")

    feat_cols = ensemble.feature_cols or feature_cols or []
    if not feat_cols:
        feat_cols = [c for c in fp.get_feature_columns() if c in test_df.columns]
    X_all = test_df.reindex(columns=feat_cols, fill_value=0.0).values
    X_all = np.nan_to_num(X_all, nan=0.0)

    print(f"  Batch-predicting {len(X_all):,} bars x {len(feat_cols)} features...")
    t0 = time.time()
    probas_all = ensemble.predict_proba(X_all)
    pred_all = np.argmax(probas_all, axis=1)
    conf_all = np.max(probas_all, axis=1)
    label = {0: "BUY", 1: "SELL", 2: "HOLD"}
    print(f"  Batch prediction done in {time.time() - t0:.1f}s")

    perf_analyzer = PerformanceAnalyzer()
    initial_balance = 10_000.0
    balance = initial_balance
    position = None
    trades = []
    equity_curve = [balance]

    warmup = 200
    max_risk_pct = config.risk.get("max_risk_pct", 0.005)
    sl_floor = config.risk.get("sl_pips", 30) * PIP_SIZE
    atr_col = "atr" if "atr" in test_df.columns else None
    rows = test_df.to_dict("records")

    print(f"  Simulating trades (warmup={warmup} bars, pip_size={PIP_SIZE})...")
    t0 = time.time()
    for i in range(warmup, len(rows)):
        row = rows[i]
        ts = row["time"]
        hi, lo, cl = row["high"], row["low"], row["close"]

        if position is not None:
            direction = position["direction"]
            vol = position["volume"]
            sl, tp = position["sl"], position["tp"]
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

        if position is None and i < len(rows) - 5:
            confidence = float(conf_all[i])
            signal = label[int(pred_all[i])]
            if confidence >= 0.60 and signal in ("BUY", "SELL"):
                atr = float(row[atr_col]) if atr_col else sl_floor
                dynamic_sl = max(atr * 1.5, sl_floor)
                dynamic_tp = dynamic_sl * 2.0
                risk_amount = balance * max_risk_pct
                sl_pips_val = dynamic_sl / PIP_SIZE
                volume = risk_amount / max(sl_pips_val * PIP_SIZE * 10, 1e-9)
                volume = max(min(round(volume, 2), 1.0), 0.01)
                position = {
                    "direction": TradeDirection.BUY.value if signal == "BUY" else TradeDirection.SELL.value,
                    "entry": cl,
                    "sl": cl - dynamic_sl if signal == "BUY" else cl + dynamic_sl,
                    "tp": cl + dynamic_tp if signal == "BUY" else cl - dynamic_tp,
                    "volume": volume,
                    "entry_time": ts,
                    "confidence": confidence,
                    "profit": 0.0,
                }

        open_pnl = position.get("profit", 0.0) if position else 0.0
        equity_curve.append(balance + open_pnl)

    if position is not None:
        last = rows[-1]
        direction = position["direction"]
        pnl = (
            (last["close"] - position["entry"])
            if direction == TradeDirection.BUY.value
            else (position["entry"] - last["close"])
        ) / PIP_SIZE * position["volume"] * 10
        position.update(profit=pnl, exit_time=last["time"], exit_price=last["close"], exit_reason="end_of_data")
        trades.append(dict(position)); balance += pnl

    print(f"  Simulation complete in {time.time() - t0:.1f}s")
    perf = perf_analyzer.analyze_trades(trades, start_balance=initial_balance)
    perf["equity_curve"] = equity_curve
    perf["final_balance"] = balance
    perf["total_return_pct"] = (balance - initial_balance) / initial_balance * 100
    perf["initial_balance"] = initial_balance
    perf["trades"] = trades
    perf["test_from"] = str(TEST_FROM.date())
    perf["test_to"] = str(TEST_TO.date())
    perf["symbol"] = SYMBOL
    perf["source"] = "OANDA"
    perf["instrument"] = OANDA_INSTRUMENT
    perf["model_version"] = model_version
    perf["pip_size"] = PIP_SIZE
    return perf


def step5_report(results: dict) -> Path:
    banner("Step 5 - Backtest Report")
    total = results.get("total_trades", 0)
    wins = results.get("winning_trades", 0)
    losses = results.get("losing_trades", 0)
    win_rate = results.get("win_rate", 0)
    pf = results.get("profit_factor", 0)
    net = results.get("net_profit", 0)
    ret_pct = results.get("total_return_pct", 0)
    max_dd = results.get("max_drawdown", 0)
    sharpe = results.get("sharpe_ratio", 0)
    sortino = results.get("sortino_ratio", 0)
    init_bal = results.get("initial_balance", 10_000)
    fin_bal = results.get("final_balance", init_bal)

    print(f"  Period        : {results.get('test_from')} -> {results.get('test_to')}")
    print(f"  Final balance : ${fin_bal:,.2f}")
    print(f"  Return        : {ret_pct:+.2f}%")
    print(f"  Net profit    : ${net:+,.2f}")
    print(f"  Trades        : {total} ({wins} wins, {losses} losses, {win_rate:.1f}% WR)")
    print(f"  PF / DD       : {pf:.2f} / {max_dd:.2f}%")
    print(f"  Sharpe/Sortino: {sharpe:.2f} / {sortino:.2f}")

    results_dir = RESULTS_ROOT / SYMBOL
    results_dir.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_path = results_dir / f"backtest_2026_oanda_{ts}.json"

    saveable = {k: v for k, v in results.items() if k not in ("equity_curve", "trades")}
    trades = results.get("trades", [])
    if trades:
        saveable["trades"] = [
            {k2: str(v2) if not isinstance(v2, (int, float, str)) else v2 for k2, v2 in t.items()}
            for t in trades
        ]

    with open(report_path, "w") as f:
        json.dump(saveable, f, indent=2, default=str)
    print(f"  Full report saved -> {report_path}")
    return report_path


def parse_args():
    parser = argparse.ArgumentParser(description=f"2026 {SYMBOL} OANDA -> Train -> Backtest pipeline")
    parser.add_argument("--skip-download", action="store_true", help="Skip OANDA download; use existing tf_1.parquet")
    parser.add_argument("--skip-convert", action="store_true", help="Skip resampling; assume parquets already exist")
    parser.add_argument("--backtest-only", action="store_true", help="Load latest model and run backtest only")
    return parser.parse_args()


def main():
    args = parse_args()
    banner(f"2026 {SYMBOL} OANDA Pipeline | Train: Jan-Feb | Test: Mar-May")
    print(f"  Symbol     : {SYMBOL}")
    print(f"  Instrument : {OANDA_INSTRUMENT}")
    print(f"  Data dir   : {STORAGE_DIR}")
    print(f"  Model dir  : {MODELS_ROOT}")
    print(f"  Results dir: {RESULTS_ROOT / SYMBOL}")

    if not args.skip_download and not args.skip_convert and not args.backtest_only:
        df_m1 = step1_download()
    elif (STORAGE_DIR / "tf_1.parquet").exists():
        df_m1 = pd.read_parquet(str(STORAGE_DIR / "tf_1.parquet"))
    else:
        df_m1 = None

    if not args.skip_convert and not args.backtest_only:
        if df_m1 is None:
            print("ERROR: No M1 parquet found. Run without --skip-convert.")
            sys.exit(1)
        step2_store(df_m1)

    if not (STORAGE_DIR / "tf_5.parquet").exists():
        print(f"ERROR: {STORAGE_DIR}/tf_5.parquet not found.")
        sys.exit(1)

    if args.backtest_only:
        ensemble, feature_cols, version = step3_load_latest()
    else:
        ensemble, feature_cols, version = step3_train()

    results = step4_backtest(ensemble, feature_cols, version)
    step5_report(results)
    banner("Pipeline complete")


if __name__ == "__main__":
    main()
