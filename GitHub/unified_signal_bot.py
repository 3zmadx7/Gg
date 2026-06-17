"""
unified_signal_bot.py — Dual-Engine Telegram Forex Signal Bot
============================================================
Combines two distinct signal generation strategies:
1. Adaptive Ensemble: Startup-trained models with pure confidence-based signals.
2. Advanced Strategy: Modular engine using DecisionEngine, MarketScorer, and Intelligence filters.

Run with: python3 unified_signal_bot.py
"""

import os
import sys
import time
import datetime
import requests
import numpy as np
import pandas as pd
from pathlib import Path

# Ensure project root is in sys.path
PROJECT_ROOT = Path(__file__).parent.resolve()
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# Engine 1 Imports (Adaptive)
from data.oanda_downloader import download_oanda_candles
from features.feature_pipeline import FeaturePipeline
from ml.trainer import ModelTrainer
from core.constants import LOOKAHEAD_5

# Engine 2 Imports (Advanced)
from data.market_data_engine import MarketDataEngine
from ml.predictor import MLPredictor
from intelligence.market_scorer import MarketScorer
from intelligence.trend_analysis import TrendAnalyzer
from intelligence.volatility_analysis import VolatilityAnalyzer
from intelligence.momentum_analysis import MomentumAnalyzer
from intelligence.market_regime import MarketRegimeDetector
from features.support_resistance import SupportResistanceEngine
from decision.decision_engine import DecisionEngine
from decision.trend_reversal_detector import TrendReversalDetector
from core.config import config

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

OANDA_TOKEN = os.environ.get("OANDA_TOKEN", "")
OANDA_BASE_URL = os.environ.get("OANDA_BASE_URL", "").rstrip("/")
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "")

SIGNAL_COOLDOWN_SECONDS = 3600  # 60 minutes per pair per engine
LOOP_INTERVAL_SECONDS = 300     # Check every 5 minutes

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------

def log(message: str, level: str = "info") -> None:
    ts = datetime.datetime.utcnow().strftime("%H:%M UTC")
    prefix = {"info": "[ ]", "success": "[+]", "warning": "[!]", "error": "[X]"}.get(level, "[ ]")
    print(f"[{ts}] {prefix} {message}", flush=True)

# ---------------------------------------------------------------------------
# Telegram
# ---------------------------------------------------------------------------

def send_telegram(text: str) -> bool:
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
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
# Helpers
# ---------------------------------------------------------------------------

def _pip_size(pair: str) -> float:
    return 0.01 if "JPY" in pair else 0.0001

def _format_pair(pair: str) -> str:
    return pair[:3] + "/" + pair[3:]

# ---------------------------------------------------------------------------
# Unified Signal Bot
# ---------------------------------------------------------------------------

class UnifiedSignalBot:
    def __init__(self):
        log("Initializing Unified Dual-Engine Signal Bot...")
        self.models = {}  # Engine 1 models
        self.configs = {} # Engine 1 configs
        self.cooldowns_adaptive = {p: 0 for p in PORTFOLIO}
        self.cooldowns_advanced = {p: 0 for p in PORTFOLIO}
        
        # Initialize Engine 2 Components
        self.data_engine = MarketDataEngine()
        self.market_scorer = MarketScorer()
        self.trend_analyzer = TrendAnalyzer()
        self.vol_analyzer = VolatilityAnalyzer()
        self.mom_analyzer = MomentumAnalyzer()
        self.regime_detector = MarketRegimeDetector()
        self.sr_detector = SupportResistanceEngine()
        self.reversal_detector = TrendReversalDetector()
        
        self._load_engine1_configs()
        self._startup_training()

    def _load_engine1_configs(self):
        log("Loading Engine 1 (Adaptive) configs...")
        for pair in PORTFOLIO:
            path = Path("optimized_results") / pair / "best_config.json"
            try:
                import json
                with open(path) as f:
                    data = json.load(f)
                self.configs[pair] = data["config"]
            except Exception:
                log(f"  {pair}: config load error", "error")
                self.configs[pair] = None

    def _startup_training(self):
        log("=" * 60)
        log("ENGINE 1: STARTUP TRAINING")
        log("=" * 60)
        for pair, instrument in PORTFOLIO.items():
            if not self.configs.get(pair): continue
            log(f"Training Engine 1 for {pair}...")
            try:
                self._train_engine1(pair, instrument)
            except Exception as e:
                log(f"Engine 1 {pair} training failed: {e}", "error")

    def _train_engine1(self, pair: str, instrument: str):
        cfg = self.configs[pair]
        train_months = int(cfg.get("train_months", 3))
        to_dt = datetime.datetime.utcnow()
        from_dt = to_dt - datetime.timedelta(days=train_months * 31 + 7)
        
        df_m5 = download_oanda_candles(instrument, "M5", from_dt, to_dt)
        if df_m5.empty: return
        
        # Use simple trainer from ml.trainer
        trainer = ModelTrainer()
        X, y, feature_cols, _ = trainer.prepare_training_data(df_m5)
        
        model_params = {}
        if cfg.get("xgb_params"): model_params["xgboost"] = cfg["xgb_params"]
        if cfg.get("rf_params"): model_params["random_forest"] = cfg["rf_params"]
        
        trainer.train_all_models(X, y, feature_cols=feature_cols, model_params=model_params or None)
        self.models[pair] = trainer.get_ensemble()
        log(f"  {pair} Engine 1 ready", "success")

    def _check_adaptive_engine(self, pair: str, instrument: str, df_m5: pd.DataFrame):
        """Engine 1: Adaptive Ensemble Logic."""
        if not self.models.get(pair): return
        if time.time() - self.cooldowns_adaptive[pair] < SIGNAL_COOLDOWN_SECONDS: return
        
        ensemble = self.models[pair]
        fp = FeaturePipeline()
        df_feat = fp.compute_all(df_m5.copy())
        if df_feat.empty: return
        
        feat_cols = ensemble.feature_cols or []
        X = df_feat.reindex(columns=feat_cols, fill_value=0.0).iloc[[-1]].values
        X = np.nan_to_num(X, nan=0.0)
        
        proba = ensemble.predict_proba(X)[0]
        pred = int(np.argmax(proba))
        conf = float(proba[pred])
        threshold = self.configs[pair]["confidence_threshold"]
        
        if pred in (0, 1) and conf >= threshold:
            self._fire_signal(pair, df_m5, pred, conf, "ADAPTIVE ENSEMBLE")
            self.cooldowns_adaptive[pair] = time.time()

    def _check_advanced_engine(self, pair: str, instrument: str, df_m5: pd.DataFrame):
        """Engine 2: Advanced Modular Strategy Logic."""
        if not self.models.get(pair): return 
        if time.time() - self.cooldowns_advanced[pair] < SIGNAL_COOLDOWN_SECONDS: return
        
        try:
            # 1. Feature Prep (reuse or recompute if needed)
            fp = FeaturePipeline()
            df_feat = fp.compute_all(df_m5.copy())
            if df_feat.empty: return

            # 2. Intelligence Modules
            trend = self.trend_analyzer.analyze_trend(df_feat)
            vol = self.vol_analyzer.analyze_volatility(df_feat)
            mom = self.mom_analyzer.analyze_momentum(df_feat)
            regime = self.regime_detector.detect_regime(df_feat)
            sr = self.sr_detector.detect_levels(df_feat)
            
            # Reversal check
            reversal = self.reversal_detector.check(pair, {5: trend}, df_m5["close"].iloc[-1], sr)
            
            # 3. Decision Engine
            predictor = MLPredictor(self.models[pair])
            # Pass patterns/indicators summary
            pattern_info = {
                "candle_signal": df_feat["pattern_bullish"].iloc[-1] - df_feat["pattern_bearish"].iloc[-1] if "pattern_bullish" in df_feat.columns else 0,
                "price_action": "" # Optional
            }
            
            decision_engine = DecisionEngine(predictor, self.market_scorer)
            
            decision = decision_engine.make_decision(
                symbol=pair,
                df_entry={5: df_feat},
                trend_result=trend,
                vol_result=vol,
                momentum_result=mom,
                regime_result=regime,
                sr_info=sr,
                feature_summary={"indicators": df_feat.iloc[-1].to_dict(), "patterns": pattern_info},
                spread=0.0002,
                timeframe=5,
                reversal_info=reversal
            )
            
            action = decision.get("action")
            conf = decision.get("confidence", 0)
            
            if action in ("BUY", "SELL") and not decision.get("no_trade"):
                pred = 0 if action == "BUY" else 1
                self._fire_signal(pair, df_m5, pred, conf, "ADVANCED STRATEGY", reasons=decision.get("reasons"))
                self.cooldowns_advanced[pair] = time.time()
                
        except Exception as e:
            log(f"Advanced Engine Error {pair}: {e}", "error")

    def _fire_signal(self, pair: str, df: pd.DataFrame, pred: int, conf: float, engine_name: str, reasons: list = None):
        cfg = self.configs[pair]
        direction = LABEL[pred]
        atr_mult = float(cfg["atr_stop_multiplier"])
        rr = float(cfg["risk_reward"])
        pip_sz = _pip_size(pair)
        
        entry = float(df["close"].iloc[-1])
        # Simple ATR calculation
        hl = df["high"] - df["low"]
        atr = hl.rolling(14).mean().iloc[-1]
        sl_dist = atr * atr_mult
        
        if pred == 0: # BUY
            sl = entry - sl_dist
            tp = entry + sl_dist * rr
            emoji = "🟢"
        else: # SELL
            sl = entry + sl_dist
            tp = entry - sl_dist * rr
            emoji = "🔴"
            
        msg = (
            f"[{engine_name}]\n"
            f"{emoji} {direction} {_format_pair(pair)}\n"
            f"━━━━━━━━━━━━━━\n"
            f"Entry:  {entry:.5f}\n"
            f"SL:     {sl:.5f}\n"
            f"TP:     {tp:.5f}\n"
            f"Confidence: {conf*100:.1f}%\n"
        )
        if reasons:
            msg += f"Logic: {reasons[0]}\n"
        
        log(f"Fired {engine_name} signal for {pair}", "success")
        send_telegram(msg)

    def _fetch_candles(self, instrument: str) -> pd.DataFrame:
        """Fetch latest candles for real-time analysis."""
        try:
            url = f"{OANDA_BASE_URL}/instruments/{instrument}/candles"
            headers = {"Authorization": f"Bearer {OANDA_TOKEN}"}
            params = {"granularity": "M5", "count": "300", "price": "M"}
            resp = requests.get(url, headers=headers, params=params, timeout=30)
            resp.raise_for_status()
            candles = resp.json().get("candles", [])
            rows = []
            for c in candles:
                if not c.get("complete"): continue
                mid = c["mid"]
                rows.append({
                    "time": pd.to_datetime(c["time"]).tz_convert(None),
                    "open": float(mid["o"]), "high": float(mid["h"]),
                    "low": float(mid["l"]), "close": float(mid["c"]),
                    "volume": int(c.get("volume", 0))
                })
            return pd.DataFrame(rows)
        except Exception as e:
            log(f"Fetch candles error: {e}", "error")
            return pd.DataFrame()

    def run(self):
        log("Unified Bot Running...", "success")
        while True:
            for pair, instrument in PORTFOLIO.items():
                df_m5 = self._fetch_candles(instrument)
                if df_m5.empty: continue
                
                self._check_adaptive_engine(pair, instrument, df_m5)
                self._check_advanced_engine(pair, instrument, df_m5)
            
            time.sleep(LOOP_INTERVAL_SECONDS)

if __name__ == "__main__":
    bot = UnifiedSignalBot()
    bot.run()
