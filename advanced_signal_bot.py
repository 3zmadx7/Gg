"""
signal_bot.py — Multi-pair Telegram Forex Signal Bot
=====================================================
Trains one model per pair on startup, then checks signals every 5 minutes.
Run from the Git/ folder: python3 signal_bot.py
"""

import os
import sys
import json
import time
import shutil
import datetime
import requests
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

import data.data_loader as _data_loader_mod
from data.oanda_downloader import download_oanda_candles
from core.constants import LOOKAHEAD_5
from features.feature_pipeline import FeaturePipeline
from ml.trainer import ModelTrainer

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

PORTFOLIO = {
    "EURUSD": "EUR_USD",
    "GBPUSD": "GBP_USD",
    "USDJPY": "USD_JPY",
    "NZDUSD": "NZD_USD",
}

LABEL = {0: "BUY", 1: "SELL", 2: "HOLD"}

OPTIMIZED_RESULTS_DIR = SCRIPT_DIR / "optimized_results"
MODELS_LIVE_DIR = SCRIPT_DIR / "models_live"
TEMP_DATA_DIR = MODELS_LIVE_DIR / "_temp_train"

OANDA_TOKEN = os.environ.get("OANDA_TOKEN", "37ee33b35f88e073a08d533849f7a24b-524c89ef15f36cfe532f0918a6aee4c2")
OANDA_BASE_URL = os.environ.get("OANDA_BASE_URL", "https://api-fxpractice.oanda.com/v3").rstrip("/")
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "7887167602:AAEmpIny8aLfno4D-LbmEaP4hAjENKDdaoA")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "5244655536")

SIGNAL_COOLDOWN_SECONDS = 3600  # 60 minutes between signals per pair
LOOP_INTERVAL_SECONDS = 300     # Check every 5 minutes

TF_RESAMPLE = {
    15: "15min",
    30: "30min",
    60: "1h",
    240: "4h",
}

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------

def log(message: str, level: str = "info") -> None:
    ts = datetime.datetime.utcnow().strftime("%H:%M UTC")
    prefix = {"info": "[ ]", "success": "[+]", "warning": "[!]", "error": "[X]"}.get(level, "[ ]")
    print(f"[{ts}] {prefix} {message}", flush=True)

# ---------------------------------------------------------------------------
# OANDA helpers
# ---------------------------------------------------------------------------

def fetch_latest_candles(instrument: str, granularity: str = "M5", count: int = 500) -> pd.DataFrame:
    """Fetch the latest N complete candles from OANDA. Returns time as a column (tz-naive UTC)."""
    if not OANDA_TOKEN or not OANDA_BASE_URL:
        log("OANDA credentials not set", "error")
        return pd.DataFrame()
    url = f"{OANDA_BASE_URL}/instruments/{instrument}/candles"
    headers = {"Authorization": f"Bearer {OANDA_TOKEN}"}
    params = {"granularity": granularity, "count": str(count), "price": "M"}
    try:
        resp = requests.get(url, headers=headers, params=params, timeout=30)
        resp.raise_for_status()
        candles = resp.json().get("candles", [])
        rows = []
        for c in candles:
            if not c.get("complete"):
                continue
            mid = c["mid"]
            rows.append({
                "time": pd.to_datetime(c["time"]).tz_convert(None),
                "open":   float(mid["o"]),
                "high":   float(mid["h"]),
                "low":    float(mid["l"]),
                "close":  float(mid["c"]),
                "volume": int(c.get("volume", 0)),
            })
        if not rows:
            return pd.DataFrame()
        df = pd.DataFrame(rows)
        df.sort_values("time", inplace=True)
        df.reset_index(drop=True, inplace=True)
        return df
    except Exception as exc:
        log(f"fetch_latest_candles({instrument}): {exc}", "error")
        return pd.DataFrame()

# ---------------------------------------------------------------------------
# Technical helpers
# ---------------------------------------------------------------------------

def _resample_ohlcv(df: pd.DataFrame, rule: str) -> pd.DataFrame:
    """Resample a DataFrame (time column) to a coarser timeframe."""
    idx = df.set_index("time")
    rs = (
        idx.resample(rule)
        .agg(open=("open","first"), high=("high","max"),
             low=("low","min"), close=("close","last"),
             volume=("volume","sum"))
        .dropna(subset=["open"])
        .reset_index()
    )
    rs.sort_values("time", inplace=True)
    return rs.reset_index(drop=True)

def _atr_ema(df: pd.DataFrame, period: int = 14) -> pd.Series:
    """14-period EWM ATR."""
    hl = df["high"] - df["low"]
    hpc = (df["high"] - df["close"].shift()).abs()
    lpc = (df["low"]  - df["close"].shift()).abs()
    tr = pd.concat([hl, hpc, lpc], axis=1).max(axis=1)
    return tr.ewm(span=period, adjust=False).mean()

def _pip_size(pair: str) -> float:
    return 0.01 if "JPY" in pair else 0.0001

def _format_pair(pair: str) -> str:
    return pair[:3] + "/" + pair[3:]

# ---------------------------------------------------------------------------
# Telegram
# ---------------------------------------------------------------------------

def send_telegram(text: str) -> bool:
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        log("Telegram credentials not set — message not sent", "warning")
        return False
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    try:
        resp = requests.post(url, json={"chat_id": TELEGRAM_CHAT_ID, "text": text}, timeout=15)
        resp.raise_for_status()
        return True
    except Exception as exc:
        log(f"Telegram send failed: {exc}", "error")
        return False

# ---------------------------------------------------------------------------
# Signal Bot
# ---------------------------------------------------------------------------

class SignalBot:
    def __init__(self):
        self.models: dict = {}    # pair -> VotingEnsemble
        self.configs: dict = {}   # pair -> config sub-dict
        self.cooldowns: dict = {  # pair -> last signal datetime (init to 2 hrs ago)
            p: datetime.datetime.utcnow() - datetime.timedelta(hours=2)
            for p in PORTFOLIO
        }
        self._validate_env()
        self._load_configs()
        self._train_all_pairs()

    # ------------------------------------------------------------------
    # Startup helpers
    # ------------------------------------------------------------------

    def _validate_env(self) -> None:
        if not OANDA_TOKEN or not OANDA_BASE_URL:
            raise RuntimeError("OANDA_TOKEN or OANDA_BASE_URL environment variable is not set.")
        if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
            log("TELEGRAM_BOT_TOKEN / TELEGRAM_CHAT_ID not set — signals will NOT be sent", "warning")

    def _load_configs(self) -> None:
        log("Loading optimized configs...")
        for pair in PORTFOLIO:
            path = OPTIMIZED_RESULTS_DIR / pair / "best_config.json"
            try:
                with open(path) as f:
                    data = json.load(f)
                self.configs[pair] = data["config"]
                log(f"  {pair}: conf_threshold={self.configs[pair]['confidence_threshold']}  "
                    f"RR={self.configs[pair]['risk_reward']}  "
                    f"ATR_mult={self.configs[pair]['atr_stop_multiplier']}  "
                    f"train_months={self.configs[pair]['train_months']}", "success")
            except FileNotFoundError:
                log(f"  {pair}: best_config.json not found at {path}", "error")
                self.configs[pair] = None
            except (KeyError, json.JSONDecodeError) as exc:
                log(f"  {pair}: config load error — {exc}", "error")
                self.configs[pair] = None

    def _train_all_pairs(self) -> None:
        log("=" * 60)
        log("STARTUP TRAINING — training one model per pair")
        log("=" * 60)
        MODELS_LIVE_DIR.mkdir(parents=True, exist_ok=True)
        TEMP_DATA_DIR.mkdir(parents=True, exist_ok=True)
        for pair, instrument in PORTFOLIO.items():
            if self.configs.get(pair) is None:
                log(f"Skipping {pair} — no config", "warning")
                continue
            log(f"--- Training {pair} ---")
            try:
                self._train_pair(pair, instrument)
            except Exception as exc:
                log(f"{pair} training FAILED: {exc}", "error")
                self.models[pair] = None
        # Clean up temp data
        try:
            shutil.rmtree(str(TEMP_DATA_DIR), ignore_errors=True)
        except Exception:
            pass

    def _train_pair(self, pair: str, instrument: str) -> None:
        cfg = self.configs[pair]
        train_months = int(cfg.get("train_months", 3))

        # Download M5 data for the training window
        to_dt   = datetime.datetime.utcnow()
        from_dt = to_dt - datetime.timedelta(days=train_months * 31 + 7)
        log(f"  Downloading M5 data for {pair} ({from_dt.date()} → {to_dt.date()})...")
        df_m5 = download_oanda_candles(instrument, "M5", from_dt, to_dt)
        if df_m5.empty or len(df_m5) < 1000:
            raise RuntimeError(f"Not enough M5 data fetched: {len(df_m5)} bars")
        log(f"  M5 bars fetched: {len(df_m5):,}")

        # Resample M5 → M15 / M30 / H1 / H4
        resampled = {5: df_m5}
        for tf_min, rule in TF_RESAMPLE.items():
            resampled[tf_min] = _resample_ohlcv(df_m5, rule)

        # Save parquets to temp dir
        pair_tmp = TEMP_DATA_DIR / pair
        pair_tmp.mkdir(parents=True, exist_ok=True)
        for tf_min, df_tf in resampled.items():
            df_tf.to_parquet(pair_tmp / f"tf_{tf_min}.parquet",
                             index=False, engine="pyarrow", compression="snappy")

        # Patch DataLoader HISTORICAL_DIR, train, then restore
        original_hist_dir = _data_loader_mod.HISTORICAL_DIR
        _data_loader_mod.HISTORICAL_DIR = str(TEMP_DATA_DIR)
        try:
            from data.data_loader import DataLoader
            loader = DataLoader(pair)
            aligned = loader.load_aligned()
            log(f"  Aligned M5 rows: {len(aligned):,}")
            if len(aligned) < 500:
                raise RuntimeError("Too few aligned rows after DataLoader")

            trainer = ModelTrainer()
            log(f"  Computing features and preparing training data...")
            X, y, feature_cols, df_clean = trainer.prepare_training_data(
                aligned,
                lookahead=LOOKAHEAD_5,
                buy_threshold=0.001,
                sell_threshold=0.001,
                target_type="class",
            )
            log(f"  Samples: {len(X):,}  Features: {len(feature_cols)}  "
                f"BUY:{(y==0).sum()} SELL:{(y==1).sum()} HOLD:{(y==2).sum()}")

            recency = (ModelTrainer.compute_recency_weights(df_clean["time"])
                       if "time" in df_clean.columns else None)
            log(f"  Training XGBoost + RandomForest ensemble...")
            model_params = {}
            if cfg.get("xgb_params"):
                model_params["xgboost"] = cfg["xgb_params"]
            if cfg.get("rf_params"):
                model_params["random_forest"] = cfg["rf_params"]
            trainer.train_all_models(
                X, y,
                feature_cols=feature_cols,
                target_type="class",
                recency_weights=recency,
                model_params=model_params or None,
            )
            ensemble = trainer.get_ensemble()
            self.models[pair] = ensemble
            log(f"  {pair} model trained ({ensemble.get_num_models()} sub-models)", "success")
        finally:
            _data_loader_mod.HISTORICAL_DIR = original_hist_dir

    # ------------------------------------------------------------------
    # Live signal check (runs every 5 min)
    # ------------------------------------------------------------------

    def _check_pair(self, pair: str, instrument: str) -> None:
        if not self.models.get(pair):
            return

        # Cooldown guard
        now = datetime.datetime.utcnow()
        if (now - self.cooldowns[pair]).total_seconds() < SIGNAL_COOLDOWN_SECONDS:
            return

        # Fetch latest 500 M5 candles
        df = fetch_latest_candles(instrument, "M5", 500)
        if df.empty or len(df) < 100:
            log(f"{pair}: not enough M5 data for feature computation ({len(df)} bars)", "warning")
            return

        # Compute features
        try:
            fp = FeaturePipeline()
            df_feat = fp.compute_all(df.copy())
        except Exception as exc:
            log(f"{pair}: feature pipeline error — {exc}", "error")
            return

        if df_feat.empty:
            return

        # Predict on last row
        ensemble = self.models[pair]
        feat_cols = ensemble.feature_cols or []
        if not feat_cols:
            log(f"{pair}: ensemble has no feature_cols", "error")
            return

        X = df_feat.reindex(columns=feat_cols, fill_value=0.0).iloc[[-1]].values
        X = np.nan_to_num(X, nan=0.0)

        try:
            proba = ensemble.predict_proba(X)[0]
        except Exception as exc:
            log(f"{pair}: predict_proba error — {exc}", "error")
            return

        pred      = int(np.argmax(proba))
        conf      = float(proba[pred])
        threshold = self.configs[pair]["confidence_threshold"]

        log(f"{pair}: {LABEL[pred]} conf={conf*100:.1f}% (threshold={threshold*100:.0f}%)")

        if pred in (0, 1) and conf >= threshold:
            self._fire_signal(pair, df, pred, conf)

    def _fire_signal(self, pair: str, df: pd.DataFrame, pred: int, conf: float) -> None:
        cfg = self.configs[pair]
        direction    = LABEL[pred]       # "BUY" or "SELL"
        atr_mult     = float(cfg["atr_stop_multiplier"])
        rr           = float(cfg["risk_reward"])
        pip_sz       = _pip_size(pair)

        entry = float(df["close"].iloc[-1])
        atr   = float(_atr_ema(df).iloc[-1])
        sl_dist = atr * atr_mult

        if pred == 0:  # BUY
            sl = entry - sl_dist
            tp = entry + sl_dist * rr
            emoji = "🟢"
            sl_sign = "−"
            tp_sign = "+"
        else:           # SELL
            sl = entry + sl_dist
            tp = entry - sl_dist * rr
            emoji = "🔴"
            sl_sign = "+"
            tp_sign = "−"

        sl_pips = round(sl_dist / pip_sz, 1)
        tp_pips = round(sl_dist * rr / pip_sz, 1)

        ts_col = "time" if "time" in df.columns else None
        ts_str = df[ts_col].iloc[-1].strftime("%H:%M") if ts_col else "??"

        msg = (
            f"{emoji} {direction} {_format_pair(pair)}\n"
            f"━━━━━━━━━━━━━━\n"
            f"Entry:  {entry:.5f}\n"
            f"SL:     {sl:.5f}  ({sl_sign}{sl_pips} pips)\n"
            f"TP:     {tp:.5f}  ({tp_sign}{tp_pips} pips)\n"
            f"Confidence: {conf*100:.1f}%\n"
            f"Time: {ts_str} UTC"
        )

        log(f"{pair} — {direction} signal firing! conf={conf*100:.1f}%", "success")

        if send_telegram(msg):
            self.cooldowns[pair] = datetime.datetime.utcnow()
            log(f"{pair} — signal sent, cooldown activated", "success")

    # ------------------------------------------------------------------
    # Main loop
    # ------------------------------------------------------------------

    def run(self) -> None:
        loaded = [p for p, m in self.models.items() if m is not None]
        log(f"Signal bot started. Active pairs: {', '.join(loaded)}", "success")
        log(f"Checking signals every {LOOP_INTERVAL_SECONDS // 60} minutes.")

        while True:
            loop_start = time.time()
            for pair, instrument in PORTFOLIO.items():
                try:
                    self._check_pair(pair, instrument)
                except Exception as exc:
                    log(f"Unexpected error checking {pair}: {exc}", "error")

            elapsed = time.time() - loop_start
            sleep_time = max(0.0, LOOP_INTERVAL_SECONDS - elapsed)
            log(f"Cycle done in {elapsed:.1f}s. Sleeping {sleep_time:.0f}s...")
            time.sleep(sleep_time)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    bot = SignalBot()
    bot.run()
