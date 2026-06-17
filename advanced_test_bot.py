"""
test_bot.py — End-to-end connection and dry-run test for the signal bot
=======================================================================
Run from the Git/ folder: python3 test_bot.py

What this does:
  1. Verifies OANDA API connection for all 4 pairs
  2. Trains one model per pair (same startup flow as signal_bot.py)
  3. Sends one Telegram test message
  4. Dry-run signal check on latest candle for each pair (no Telegram send)
  5. Prints summary table
"""

import os
import sys
import json
import datetime
import numpy as np
import pandas as pd
from pathlib import Path

os.environ.setdefault("ENABLE_LIGHTGBM", "false")
os.environ.setdefault("ENABLE_LSTM", "false")

# Ensure both Git/ (data, ml, features, core, utils) and the project root
# (learning, decision, intelligence, etc.) are importable from anywhere.
SCRIPT_DIR = Path(__file__).parent.resolve()
PROJECT_ROOT = SCRIPT_DIR.parent
for _p in (str(SCRIPT_DIR), str(PROJECT_ROOT)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

# Import everything from signal_bot to keep the test consistent
from signal_bot import (
    PORTFOLIO,
    LABEL,
    OPTIMIZED_RESULTS_DIR,
    MODELS_LIVE_DIR,
    TEMP_DATA_DIR,
    OANDA_TOKEN,
    OANDA_BASE_URL,
    TELEGRAM_BOT_TOKEN,
    TELEGRAM_CHAT_ID,
    TF_RESAMPLE,
    LOOKAHEAD_5,
    log,
    fetch_latest_candles,
    send_telegram,
    _resample_ohlcv,
    _atr_ema,
    _pip_size,
    _format_pair,
    SignalBot,
)
import data.data_loader as _data_loader_mod
from data.oanda_downloader import download_oanda_candles
from features.feature_pipeline import FeaturePipeline
from ml.trainer import ModelTrainer


# ---------------------------------------------------------------------------
# OANDA connection test
# ---------------------------------------------------------------------------

def test_oanda_connection() -> bool:
    log("=" * 50)
    log("TEST 1 — OANDA API connection")
    log("=" * 50)
    all_ok = True
    for pair, instrument in PORTFOLIO.items():
        df = fetch_latest_candles(instrument, "M5", 10)
        if df.empty:
            log(f"  {pair}: FAILED — no candles returned", "error")
            all_ok = False
        else:
            log(f"  {pair}: OK — {len(df)} candles, "
                f"latest close = {df['close'].iloc[-1]:.5f}", "success")
    return all_ok


# ---------------------------------------------------------------------------
# Config loading test
# ---------------------------------------------------------------------------

def test_configs() -> dict:
    log("=" * 50)
    log("TEST 2 — Loading optimized configs")
    log("=" * 50)
    configs = {}
    for pair in PORTFOLIO:
        path = OPTIMIZED_RESULTS_DIR / pair / "best_config.json"
        try:
            with open(path) as f:
                data = json.load(f)
            configs[pair] = data["config"]
            log(f"  {pair}: OK — conf={configs[pair]['confidence_threshold']}  "
                f"RR={configs[pair]['risk_reward']}  "
                f"ATR={configs[pair]['atr_stop_multiplier']}  "
                f"months={configs[pair]['train_months']}", "success")
        except FileNotFoundError:
            log(f"  {pair}: FAILED — best_config.json not found at {path}", "error")
            configs[pair] = None
        except (KeyError, json.JSONDecodeError) as exc:
            log(f"  {pair}: FAILED — {exc}", "error")
            configs[pair] = None
    return configs


# ---------------------------------------------------------------------------
# Telegram connection test
# ---------------------------------------------------------------------------

def test_telegram() -> bool:
    log("=" * 50)
    log("TEST 3 — Telegram connection")
    log("=" * 50)
    loaded_pairs = ", ".join(PORTFOLIO.keys())
    test_msg = (
        f"✅ Bot connection test successful.\n"
        f"{loaded_pairs} loaded and ready."
    )
    log(f"  Sending test message to chat {TELEGRAM_CHAT_ID}...")
    ok = send_telegram(test_msg)
    if ok:
        log("  Telegram: OK — test message sent", "success")
    else:
        log("  Telegram: FAILED (check credentials)", "error")
    return ok


# ---------------------------------------------------------------------------
# Full training + dry-run
# ---------------------------------------------------------------------------

def test_train_and_dry_run(configs: dict) -> list:
    """Train one model per pair, then do a dry-run prediction on the latest candle."""
    log("=" * 50)
    log("TEST 4 — Training + dry-run signal check")
    log("=" * 50)

    models = {}

    for pair, instrument in PORTFOLIO.items():
        if configs.get(pair) is None:
            log(f"  {pair}: skipping training — no config", "warning")
            models[pair] = None
            continue

        cfg = configs[pair]
        train_months = int(cfg.get("train_months", 3))
        to_dt   = datetime.datetime.utcnow()
        from_dt = to_dt - datetime.timedelta(days=train_months * 31 + 7)

        log(f"  Training {pair} ({from_dt.date()} → {to_dt.date()})...")
        try:
            df_m5 = download_oanda_candles(instrument, "M5", from_dt, to_dt)
            if df_m5.empty or len(df_m5) < 1000:
                log(f"  {pair}: insufficient M5 data ({len(df_m5)} bars)", "error")
                models[pair] = None
                continue
            log(f"    M5 bars: {len(df_m5):,}", "info")

            resampled = {5: df_m5}
            for tf_min, rule in TF_RESAMPLE.items():
                resampled[tf_min] = _resample_ohlcv(df_m5, rule)

            pair_tmp = TEMP_DATA_DIR / pair
            pair_tmp.mkdir(parents=True, exist_ok=True)
            for tf_min, df_tf in resampled.items():
                df_tf.to_parquet(pair_tmp / f"tf_{tf_min}.parquet",
                                 index=False, engine="pyarrow", compression="snappy")

            original_hist_dir = _data_loader_mod.HISTORICAL_DIR
            _data_loader_mod.HISTORICAL_DIR = str(TEMP_DATA_DIR)
            try:
                from data.data_loader import DataLoader
                aligned = DataLoader(pair).load_aligned()
                trainer = ModelTrainer()
                X, y, feature_cols, df_clean = trainer.prepare_training_data(
                    aligned, lookahead=LOOKAHEAD_5,
                    buy_threshold=0.001, sell_threshold=0.001, target_type="class",
                )
                recency = (ModelTrainer.compute_recency_weights(df_clean["time"])
                           if "time" in df_clean.columns else None)
                model_params = {}
                if cfg.get("xgb_params"):
                    model_params["xgboost"] = cfg["xgb_params"]
                if cfg.get("rf_params"):
                    model_params["random_forest"] = cfg["rf_params"]
                trainer.train_all_models(
                    X, y, feature_cols=feature_cols, target_type="class",
                    recency_weights=recency, model_params=model_params or None,
                )
                ensemble = trainer.get_ensemble()
                models[pair] = ensemble
                log(f"    {pair}: model trained OK ({ensemble.get_num_models()} sub-models)", "success")
            finally:
                _data_loader_mod.HISTORICAL_DIR = original_hist_dir

        except Exception as exc:
            log(f"    {pair}: training FAILED — {exc}", "error")
            models[pair] = None

    # Clean up temp data
    try:
        import shutil
        shutil.rmtree(str(TEMP_DATA_DIR), ignore_errors=True)
    except Exception:
        pass

    # Dry-run predictions
    log("=" * 50)
    log("TEST 5 — Dry-run signal check (no Telegram sends)")
    log("=" * 50)

    results = []
    for pair, instrument in PORTFOLIO.items():
        latest_close  = "N/A"
        confidence    = "N/A"
        signal        = "N/A"
        would_fire    = "No"

        if models.get(pair) is None:
            log(f"  {pair}: SKIP — no model", "warning")
            results.append((pair, latest_close, confidence, signal, would_fire))
            continue

        df = fetch_latest_candles(instrument, "M5", 500)
        if df.empty or len(df) < 100:
            log(f"  {pair}: SKIP — not enough live M5 data", "warning")
            results.append((pair, latest_close, confidence, signal, would_fire))
            continue

        latest_close = f"{df['close'].iloc[-1]:.5f}"

        try:
            fp = FeaturePipeline()
            df_feat = fp.compute_all(df.copy())
            if df_feat.empty:
                raise RuntimeError("FeaturePipeline returned empty df")

            ensemble = models[pair]
            feat_cols = ensemble.feature_cols or []
            X = df_feat.reindex(columns=feat_cols, fill_value=0.0).iloc[[-1]].values
            X = np.nan_to_num(X, nan=0.0)

            proba = ensemble.predict_proba(X)[0]
            pred  = int(np.argmax(proba))
            conf  = float(proba[pred])
            signal = LABEL[pred]
            confidence = f"{conf * 100:.1f}%"

            threshold = configs[pair]["confidence_threshold"]
            if pred in (0, 1) and conf >= threshold:
                would_fire = "YES"

        except Exception as exc:
            log(f"  {pair}: prediction error — {exc}", "error")
            signal = "ERROR"

        results.append((pair, latest_close, confidence, signal, would_fire))
        log(f"  {pair}: close={latest_close}  conf={confidence}  "
            f"signal={signal}  would_fire={would_fire}")

    return results


# ---------------------------------------------------------------------------
# Summary table printer
# ---------------------------------------------------------------------------

def print_summary(results: list) -> None:
    log("=" * 60)
    log("DRY-RUN SUMMARY")
    log("=" * 60)
    header = f"{'Pair':<10} {'Latest Close':<15} {'Confidence':<14} {'Signal':<8} {'Would Fire?'}"
    log(header)
    log("-" * 60)
    for row in results:
        pair, close, conf, sig, fire = row
        fire_flag = "✅ YES" if fire == "YES" else "   no"
        log(f"{pair:<10} {close:<15} {conf:<14} {sig:<8} {fire_flag}")
    log("=" * 60)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    log("=" * 60)
    log("FOREX SIGNAL BOT — FULL CONNECTION AND DRY-RUN TEST")
    log("=" * 60)

    oanda_ok   = test_oanda_connection()
    configs    = test_configs()
    telegram_ok = test_telegram()

    configs_ok = all(c is not None for c in configs.values())

    if not oanda_ok:
        log("OANDA connection failed — cannot continue with dry-run.", "error")
        sys.exit(1)

    results = test_train_and_dry_run(configs)
    print_summary(results)

    log("=" * 60)
    if oanda_ok and telegram_ok and configs_ok:
        log("ALL TESTS PASSED ✅  Bot is ready for deployment.", "success")
    else:
        issues = []
        if not oanda_ok:     issues.append("OANDA connection")
        if not telegram_ok:  issues.append("Telegram connection")
        if not configs_ok:   issues.append("configs missing")
        log(f"Issues found: {', '.join(issues)}", "warning")
    log("=" * 60)
