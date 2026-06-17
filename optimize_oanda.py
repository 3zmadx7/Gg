#!/usr/bin/env python3
"""
Serial OANDA pair optimizer.

Writes only optimized_results/ and trains models in memory so baseline
models_oanda/ and results_oanda/ remain untouched.
"""

import json
import math
import os
import time
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from typing import Any

os.environ.setdefault("ENABLE_LIGHTGBM", "false")
os.environ.setdefault("ENABLE_LSTM", "false")

import numpy as np
import pandas as pd

import data.data_loader as data_loader
from core.constants import LOOKAHEAD_5, TradeDirection
from features.feature_pipeline import FeaturePipeline
from learning.performance_analyzer import PerformanceAnalyzer
from ml.trainer import ModelTrainer


DATA_ROOT = Path("data/historical_oanda")
OUT_ROOT = Path("optimized_results")
PAIRS = ["USDJPY", "GBPUSD", "AUDUSD", "NZDUSD", "EURUSD", "USDCHF"]

TRAIN_2M_TO = datetime(2026, 2, 28, 23, 59, 59)
TRAIN_3M_TO = datetime(2026, 3, 31, 23, 59, 59)
TRAIN_FROM = datetime(2026, 1, 1)
TEST_FROM_2M = datetime(2026, 3, 1)
TEST_FROM_3M = datetime(2026, 4, 1)
TEST_TO = datetime(2026, 5, 31, 23, 59, 59)

BASELINES = {
    "USDJPY": {"return": 238.91, "win_rate": 64.7, "profit_factor": 3.43, "max_drawdown": -7.14, "sharpe": 9.62},
    "GBPUSD": {"return": 210.00, "win_rate": 62.5, "profit_factor": 3.33, "max_drawdown": -7.83, "sharpe": 9.56},
    "AUDUSD": {"return": 122.57, "win_rate": 52.9, "profit_factor": 2.31, "max_drawdown": -5.73, "sharpe": 6.41},
    "NZDUSD": {"return": 62.96, "win_rate": 48.8, "profit_factor": 2.00, "max_drawdown": -13.04, "sharpe": 5.22},
    "EURUSD": {"return": 50.37, "win_rate": 43.1, "profit_factor": 1.51, "max_drawdown": -9.45, "sharpe": 3.08},
    "USDCHF": {"return": 16.89, "win_rate": 39.5, "profit_factor": 1.24, "max_drawdown": -27.52, "sharpe": 1.64},
}


@dataclass(frozen=True)
class ModelSpec:
    name: str
    train_months: int
    timeframe: int
    sample_weight_multiplier: float
    xgb: dict[str, Any]
    rf: dict[str, Any]
    weights: dict[str, float]


@dataclass(frozen=True)
class ExecSpec:
    confidence: float
    rr: float
    atr_mult: float


def finite(value: Any, default: float = 0.0) -> float:
    try:
        val = float(value)
    except Exception:
        return default
    return val if math.isfinite(val) else default


def score_trial(row: dict[str, Any]) -> float:
    pf = finite(row.get("profit_factor"))
    if pf == 0 and str(row.get("profit_factor")).lower() == "inf":
        pf = 10.0
    pf = min(pf, 10.0)
    return (
        pf * finite(row.get("win_rate")) / 100.0
        - abs(finite(row.get("max_drawdown"))) / 100.0
        + finite(row.get("sharpe_ratio")) / 10.0
    )


def passes_filters(row: dict[str, Any]) -> bool:
    return (
        int(row.get("total_trades", 0)) >= 25
        and finite(row.get("win_rate")) >= 45.0
        and finite(row.get("max_drawdown")) >= -20.0
    )


def load_aligned(pair: str, timeframe: int) -> pd.DataFrame:
    if timeframe == 5:
        old = data_loader.HISTORICAL_DIR
        data_loader.HISTORICAL_DIR = str(DATA_ROOT)
        try:
            return data_loader.DataLoader(pair).load_aligned()
        finally:
            data_loader.HISTORICAL_DIR = old

    path = DATA_ROOT / pair / f"tf_{timeframe}.parquet"
    df = pd.read_parquet(path)
    df["time"] = pd.to_datetime(df["time"])
    df.sort_values("time", inplace=True)
    return df.reset_index(drop=True)


def model_specs(pair: str) -> list[ModelSpec]:
    specs = [
        ModelSpec(
            "baseline_2m",
            2,
            5,
            1.0,
            {"n_estimators": 160, "max_depth": 6, "learning_rate": 0.05, "subsample": 0.8, "n_jobs": -1},
            {"n_estimators": 160, "max_depth": 8, "min_samples_leaf": 5, "n_jobs": -1},
            {"xgboost": 1.0, "random_forest": 1.0},
        ),
        ModelSpec(
            "conservative_2m",
            2,
            5,
            1.0,
            {"n_estimators": 120, "max_depth": 3, "learning_rate": 0.08, "subsample": 0.8, "n_jobs": -1},
            {"n_estimators": 140, "max_depth": 6, "min_samples_leaf": 5, "n_jobs": -1},
            {"xgboost": 1.0, "random_forest": 1.0},
        ),
        ModelSpec(
            "xgb_weight_2m",
            2,
            5,
            1.0,
            {"n_estimators": 220, "max_depth": 4, "learning_rate": 0.05, "subsample": 0.9, "n_jobs": -1},
            {"n_estimators": 180, "max_depth": 8, "min_samples_leaf": 3, "n_jobs": -1},
            {"xgboost": 1.5, "random_forest": 1.0},
        ),
        ModelSpec(
            "rf_weight_2m",
            2,
            5,
            1.0,
            {"n_estimators": 140, "max_depth": 5, "learning_rate": 0.10, "subsample": 0.8, "n_jobs": -1},
            {"n_estimators": 240, "max_depth": 10, "min_samples_leaf": 2, "n_jobs": -1},
            {"xgboost": 1.0, "random_forest": 1.5},
        ),
        ModelSpec(
            "three_month_3m",
            3,
            5,
            1.0,
            {"n_estimators": 180, "max_depth": 4, "learning_rate": 0.06, "subsample": 0.8, "n_jobs": -1},
            {"n_estimators": 180, "max_depth": 8, "min_samples_leaf": 4, "n_jobs": -1},
            {"xgboost": 1.0, "random_forest": 1.0},
        ),
        ModelSpec(
            "class_weight_3m",
            3,
            5,
            1.5,
            {"n_estimators": 180, "max_depth": 5, "learning_rate": 0.05, "subsample": 0.9, "n_jobs": -1},
            {"n_estimators": 220, "max_depth": 10, "min_samples_leaf": 3, "n_jobs": -1},
            {"xgboost": 1.0, "random_forest": 1.0},
        ),
    ]

    if pair in {"EURUSD", "USDCHF", "NZDUSD"}:
        specs[-1] = ModelSpec(
            "m15_class_weight_3m",
            3,
            15,
            1.5,
            {"n_estimators": 160, "max_depth": 4, "learning_rate": 0.06, "subsample": 0.9, "n_jobs": -1},
            {"n_estimators": 180, "max_depth": 8, "min_samples_leaf": 3, "n_jobs": -1},
            {"xgboost": 1.0, "random_forest": 1.0},
        )
    return specs


def exec_specs() -> list[ExecSpec]:
    return [
        ExecSpec(0.55, 1.5, 1.0),
        ExecSpec(0.60, 2.0, 1.5),
        ExecSpec(0.62, 2.0, 1.0),
        ExecSpec(0.65, 2.5, 1.5),
        ExecSpec(0.68, 2.5, 2.0),
        ExecSpec(0.70, 3.0, 1.5),
    ]


def train_model(pair: str, spec: ModelSpec):
    aligned = load_aligned(pair, spec.timeframe)
    train_to = TRAIN_2M_TO if spec.train_months == 2 else TRAIN_3M_TO
    train_df = aligned[(aligned["time"] >= TRAIN_FROM) & (aligned["time"] <= train_to)].copy().reset_index(drop=True)
    if len(train_df) < 500:
        raise RuntimeError(f"{pair} {spec.name}: only {len(train_df)} training bars")

    trainer = ModelTrainer()
    X, y, feature_cols, df_clean = trainer.prepare_training_data(
        train_df,
        lookahead=LOOKAHEAD_5,
        buy_threshold=0.001,
        sell_threshold=0.001,
        target_type="class",
    )
    recency = ModelTrainer.compute_recency_weights(df_clean["time"]) if "time" in df_clean.columns else None
    trainer.train_all_models(
        X,
        y,
        feature_cols=feature_cols,
        model_params={"xgboost": spec.xgb, "random_forest": spec.rf},
        sample_weight_multiplier=spec.sample_weight_multiplier,
        target_type="class",
        recency_weights=recency,
    )
    ensemble = trainer.get_ensemble()
    for name, weight in spec.weights.items():
        ensemble.set_model_weight(name, weight)
    return ensemble, feature_cols, aligned


def prepare_test_predictions(ensemble, feature_cols: list[str], aligned: pd.DataFrame, spec: ModelSpec):
    test_from = TEST_FROM_2M if spec.train_months == 2 else TEST_FROM_3M
    test_df = aligned[(aligned["time"] >= test_from) & (aligned["time"] <= TEST_TO)].copy().reset_index(drop=True)
    fp = FeaturePipeline()
    test_df = fp.compute_all(test_df)
    feat_cols = ensemble.feature_cols or feature_cols
    X = test_df.reindex(columns=feat_cols, fill_value=0.0).values
    X = np.nan_to_num(X, nan=0.0)
    probas = ensemble.predict_proba(X)
    return test_df, np.argmax(probas, axis=1), np.max(probas, axis=1), test_from


def simulate(pair: str, test_df: pd.DataFrame, pred: np.ndarray, conf: np.ndarray, exec_spec: ExecSpec, test_from: datetime) -> dict[str, Any]:
    pip_size = 0.01 if pair.endswith("JPY") else 0.0001
    initial_balance = 10_000.0
    balance = initial_balance
    max_risk_pct = 0.005
    sl_floor = 30 * pip_size
    warmup = 200
    label = {0: "BUY", 1: "SELL", 2: "HOLD"}
    rows = test_df.to_dict("records")
    position = None
    trades = []
    equity_curve = [balance]
    atr_col = "atr" if "atr" in test_df.columns else None

    for i in range(warmup, len(rows)):
        row = rows[i]
        ts = row["time"]
        hi, lo, cl = float(row["high"]), float(row["low"]), float(row["close"])

        if position is not None:
            direction = position["direction"]
            vol = position["volume"]
            sl, tp = position["sl"], position["tp"]
            if direction == TradeDirection.BUY.value:
                if lo <= sl:
                    pnl = (sl - position["entry"]) / pip_size * vol * 10
                    position.update(profit=pnl, exit_time=ts, exit_price=sl, exit_reason="stop_loss")
                    trades.append(dict(position)); balance += pnl; position = None
                elif hi >= tp:
                    pnl = (tp - position["entry"]) / pip_size * vol * 10
                    position.update(profit=pnl, exit_time=ts, exit_price=tp, exit_reason="take_profit")
                    trades.append(dict(position)); balance += pnl; position = None
            elif direction == TradeDirection.SELL.value:
                if hi >= sl:
                    pnl = (position["entry"] - sl) / pip_size * vol * 10
                    position.update(profit=pnl, exit_time=ts, exit_price=sl, exit_reason="stop_loss")
                    trades.append(dict(position)); balance += pnl; position = None
                elif lo <= tp:
                    pnl = (position["entry"] - tp) / pip_size * vol * 10
                    position.update(profit=pnl, exit_time=ts, exit_price=tp, exit_reason="take_profit")
                    trades.append(dict(position)); balance += pnl; position = None

        if position is None and i < len(rows) - 5:
            signal = label[int(pred[i])]
            if float(conf[i]) >= exec_spec.confidence and signal in ("BUY", "SELL"):
                atr = float(row[atr_col]) if atr_col else sl_floor
                dynamic_sl = max(atr * exec_spec.atr_mult, sl_floor)
                dynamic_tp = dynamic_sl * exec_spec.rr
                risk_amount = balance * max_risk_pct
                sl_pips = dynamic_sl / pip_size
                volume = risk_amount / max(sl_pips * pip_size * 10, 1e-9)
                volume = max(min(round(volume, 2), 1.0), 0.01)
                position = {
                    "direction": TradeDirection.BUY.value if signal == "BUY" else TradeDirection.SELL.value,
                    "entry": cl,
                    "sl": cl - dynamic_sl if signal == "BUY" else cl + dynamic_sl,
                    "tp": cl + dynamic_tp if signal == "BUY" else cl - dynamic_tp,
                    "volume": volume,
                    "entry_time": ts,
                    "confidence": float(conf[i]),
                    "profit": 0.0,
                }
        equity_curve.append(balance)

    if position is not None and rows:
        last = rows[-1]
        direction = position["direction"]
        pnl = (
            (float(last["close"]) - position["entry"])
            if direction == TradeDirection.BUY.value
            else (position["entry"] - float(last["close"]))
        ) / pip_size * position["volume"] * 10
        position.update(profit=pnl, exit_time=last["time"], exit_price=float(last["close"]), exit_reason="end_of_data")
        trades.append(dict(position)); balance += pnl

    perf = PerformanceAnalyzer().analyze_trades(trades, start_balance=initial_balance)
    perf["total_return_pct"] = (balance - initial_balance) / initial_balance * 100
    perf["final_balance"] = balance
    perf["initial_balance"] = initial_balance
    perf["test_from"] = str(test_from.date())
    perf["test_to"] = str(TEST_TO.date())
    perf["trades"] = trades
    return perf


def flatten_result(pair: str, trial_id: int, model_spec: ModelSpec, exec_spec: ExecSpec, perf: dict[str, Any]) -> dict[str, Any]:
    row = {
        "trial": trial_id,
        "pair": pair,
        "model_spec": model_spec.name,
        "train_months": model_spec.train_months,
        "timeframe": f"M{model_spec.timeframe}",
        "confidence": exec_spec.confidence,
        "rr": exec_spec.rr,
        "atr_mult": exec_spec.atr_mult,
        "sample_weight_multiplier": model_spec.sample_weight_multiplier,
        "xgb_weight": model_spec.weights.get("xgboost", 1.0),
        "rf_weight": model_spec.weights.get("random_forest", 1.0),
        "xgb_params": json.dumps(model_spec.xgb, sort_keys=True),
        "rf_params": json.dumps(model_spec.rf, sort_keys=True),
        "total_return_pct": finite(perf.get("total_return_pct")),
        "total_trades": int(perf.get("total_trades", 0)),
        "win_rate": finite(perf.get("win_rate")),
        "profit_factor": finite(perf.get("profit_factor"), default=10.0),
        "max_drawdown": finite(perf.get("max_drawdown")),
        "sharpe_ratio": finite(perf.get("sharpe_ratio")),
        "sortino_ratio": finite(perf.get("sortino_ratio")),
        "net_profit": finite(perf.get("net_profit")),
    }
    row["valid"] = passes_filters(row)
    row["composite_score"] = score_trial(row) if row["valid"] else -999.0
    return row


def json_safe(obj: Any) -> Any:
    if isinstance(obj, dict):
        return {k: json_safe(v) for k, v in obj.items() if k != "equity_curve"}
    if isinstance(obj, list):
        return [json_safe(v) for v in obj]
    if isinstance(obj, (pd.Timestamp, datetime)):
        return obj.isoformat()
    if isinstance(obj, float):
        return obj if math.isfinite(obj) else None
    return obj


def md_table(rows: list[dict[str, Any]], columns: list[tuple[str, str]]) -> str:
    out = ["| " + " | ".join(title for title, _ in columns) + " |"]
    out.append("|" + "|".join("---" for _ in columns) + "|")
    for row in rows:
        vals = []
        for _, key in columns:
            val = row.get(key, "")
            if isinstance(val, float):
                val = f"{val:.2f}"
            vals.append(str(val))
        out.append("| " + " | ".join(vals) + " |")
    return "\n".join(out)


def recommendation(pair: str, best: dict[str, Any]) -> str:
    if not best or not best.get("valid"):
        return "drop"
    score = finite(best.get("composite_score"))
    pf = finite(best.get("profit_factor"))
    dd = finite(best.get("max_drawdown"))
    wr = finite(best.get("win_rate"))
    if pair == "USDCHF" and (pf < 1.8 or dd < -15):
        return "drop"
    if score >= 1.9 and pf >= 2.0 and dd >= -12 and wr >= 50:
        return "yes"
    if score >= 1.2 and pf >= 1.5 and dd >= -20:
        return "maybe"
    return "drop"


def write_pair_report(pair: str, trials: list[dict[str, Any]], best_result: dict[str, Any], best_config: dict[str, Any]) -> None:
    out_dir = OUT_ROOT / pair
    baseline = BASELINES[pair]
    valid = [r for r in trials if r["valid"]]
    best_score = max(valid, key=lambda r: r["composite_score"]) if valid else max(trials, key=lambda r: r["composite_score"])
    best_return = max([r for r in trials if r["valid"]] or trials, key=lambda r: r["total_return_pct"])
    top5 = sorted(valid or trials, key=lambda r: r["composite_score"], reverse=True)[:5]
    rec = recommendation(pair, best_score)

    report = [
        f"# {pair} Optimization Report",
        "",
        f"Trials run: {len(trials)}. Valid after anti-overfitting filters: {len(valid)}.",
        "",
        "## Baseline vs Optimized",
        md_table(
            [
                {"name": "OANDA baseline", **baseline, "score": score_trial({"profit_factor": baseline["profit_factor"], "win_rate": baseline["win_rate"], "max_drawdown": baseline["max_drawdown"], "sharpe_ratio": baseline["sharpe"]})},
                {"name": "Best by score", "return": best_score["total_return_pct"], "win_rate": best_score["win_rate"], "profit_factor": best_score["profit_factor"], "max_drawdown": best_score["max_drawdown"], "sharpe": best_score["sharpe_ratio"], "score": best_score["composite_score"]},
                {"name": "Best by return", "return": best_return["total_return_pct"], "win_rate": best_return["win_rate"], "profit_factor": best_return["profit_factor"], "max_drawdown": best_return["max_drawdown"], "sharpe": best_return["sharpe_ratio"], "score": best_return["composite_score"]},
            ],
            [("Result", "name"), ("Return %", "return"), ("Win %", "win_rate"), ("PF", "profit_factor"), ("Max DD %", "max_drawdown"), ("Sharpe", "sharpe"), ("Score", "score")],
        ),
        "",
        "## Top 5 Trials By Composite Score",
        md_table(
            top5,
            [("Trial", "trial"), ("Model", "model_spec"), ("TF", "timeframe"), ("Conf", "confidence"), ("RR", "rr"), ("ATR", "atr_mult"), ("Return %", "total_return_pct"), ("Trades", "total_trades"), ("Win %", "win_rate"), ("PF", "profit_factor"), ("DD %", "max_drawdown"), ("Sharpe", "sharpe_ratio"), ("Score", "composite_score")],
        ),
        "",
        "## Winning Settings",
        f"- Confidence threshold: {best_score['confidence']}",
        f"- Risk-reward: 1:{best_score['rr']}",
        f"- ATR stop multiplier: {best_score['atr_mult']}x",
        f"- Training window: {best_score['train_months']} months",
        f"- Timeframe: {best_score['timeframe']}",
        f"- Model setup: {best_score['model_spec']} with XGB weight {best_score['xgb_weight']} and RF weight {best_score['rf_weight']}",
        "",
        f"Portfolio recommendation: **{rec.upper()}**.",
    ]
    (out_dir / f"{pair}_OPTIMIZATION_REPORT.md").write_text("\n".join(report) + "\n")


def optimize_pair(pair: str) -> dict[str, Any]:
    print(f"\n=== Optimizing {pair} ===")
    out_dir = OUT_ROOT / pair
    out_dir.mkdir(parents=True, exist_ok=True)
    trials: list[dict[str, Any]] = []
    results_by_trial: dict[int, dict[str, Any]] = {}
    trial_id = 0
    start = time.time()

    for mspec in model_specs(pair):
        print(f"{pair}: training {mspec.name} ({mspec.train_months}m, M{mspec.timeframe})")
        ensemble, feature_cols, aligned = train_model(pair, mspec)
        test_df, pred, conf, test_from = prepare_test_predictions(ensemble, feature_cols, aligned, mspec)
        for espec in exec_specs():
            trial_id += 1
            perf = simulate(pair, test_df, pred, conf, espec, test_from)
            row = flatten_result(pair, trial_id, mspec, espec, perf)
            trials.append(row)
            results_by_trial[trial_id] = perf
            print(
                f"{pair} trial {trial_id:02d}: {row['total_return_pct']:+.1f}% "
                f"WR {row['win_rate']:.1f}% PF {row['profit_factor']:.2f} "
                f"DD {row['max_drawdown']:.1f}% score {row['composite_score']:.2f} "
                f"{'valid' if row['valid'] else 'reject'}"
            )

    df = pd.DataFrame(trials)
    df.to_csv(out_dir / "trials.csv", index=False)
    valid = [r for r in trials if r["valid"]]
    best = max(valid, key=lambda r: r["composite_score"]) if valid else max(trials, key=lambda r: r["composite_score"])
    best_result = results_by_trial[int(best["trial"])]
    best_config = {
        "pair": pair,
        "selected_by": "composite_score_with_filters",
        "recommendation": recommendation(pair, best),
        "config": {
            "confidence_threshold": best["confidence"],
            "risk_reward": best["rr"],
            "atr_stop_multiplier": best["atr_mult"],
            "train_months": best["train_months"],
            "timeframe": best["timeframe"],
            "model_spec": best["model_spec"],
            "sample_weight_multiplier": best["sample_weight_multiplier"],
            "xgb_weight": best["xgb_weight"],
            "rf_weight": best["rf_weight"],
            "xgb_params": json.loads(best["xgb_params"]),
            "rf_params": json.loads(best["rf_params"]),
        },
        "metrics": best,
    }
    (out_dir / "best_config.json").write_text(json.dumps(json_safe(best_config), indent=2))
    (out_dir / "best_result.json").write_text(json.dumps(json_safe(best_result), indent=2))
    write_pair_report(pair, trials, best_result, best_config)
    print(f"{pair}: done in {(time.time() - start) / 60:.1f}m, best score {best['composite_score']:.2f}")
    return best_config


def write_master(configs: list[dict[str, Any]]) -> None:
    rows = []
    for cfg in configs:
        pair = cfg["pair"]
        m = cfg["metrics"]
        b = BASELINES[pair]
        rows.append({
            "pair": pair,
            "base_return": b["return"],
            "base_wr": b["win_rate"],
            "base_pf": b["profit_factor"],
            "base_dd": b["max_drawdown"],
            "base_score": score_trial({"profit_factor": b["profit_factor"], "win_rate": b["win_rate"], "max_drawdown": b["max_drawdown"], "sharpe_ratio": b["sharpe"]}),
            "opt_return": m["total_return_pct"],
            "opt_wr": m["win_rate"],
            "opt_pf": m["profit_factor"],
            "opt_dd": m["max_drawdown"],
            "opt_score": m["composite_score"],
            "trades": m["total_trades"],
            "confidence": m["confidence"],
            "rr": m["rr"],
            "atr": m["atr_mult"],
            "rec": cfg["recommendation"],
        })
    ranked = sorted(rows, key=lambda r: r["opt_score"], reverse=True)
    include = [r for r in ranked if r["rec"] == "yes"][:4]
    if len(include) < 3:
        include = (include + [r for r in ranked if r["rec"] == "maybe"])[:4]

    report = [
        "# Master Optimization Comparison",
        "",
        "## Baseline vs Optimized",
        md_table(
            ranked,
            [("Pair", "pair"), ("Base Ret %", "base_return"), ("Base WR", "base_wr"), ("Base PF", "base_pf"), ("Base DD", "base_dd"), ("Base Score", "base_score"), ("Opt Ret %", "opt_return"), ("Opt WR", "opt_wr"), ("Opt PF", "opt_pf"), ("Opt DD", "opt_dd"), ("Opt Score", "opt_score"), ("Trades", "trades"), ("Rec", "rec")],
        ),
        "",
        "## Live Signal Settings",
        md_table(
            ranked,
            [("Pair", "pair"), ("Confidence", "confidence"), ("RR", "rr"), ("ATR SL", "atr"), ("Recommendation", "rec")],
        ),
        "",
        "## Final Portfolio Recommendation",
        "Include these pairs in the Telegram bot: " + ", ".join(r["pair"] for r in include) + ".",
        "",
        "Rationale: selected pairs passed the trade-count, win-rate, and drawdown filters and ranked highest by the risk-adjusted composite score. Pairs marked drop should not be included unless future walk-forward validation changes their profile.",
    ]
    OUT_ROOT.mkdir(parents=True, exist_ok=True)
    (OUT_ROOT / "MASTER_OPTIMIZATION_COMPARISON.md").write_text("\n".join(report) + "\n")


def append_memory(configs: list[dict[str, Any]]) -> None:
    rows = []
    for cfg in sorted(configs, key=lambda c: c["metrics"]["composite_score"], reverse=True):
        m = cfg["metrics"]
        rows.append(
            f"| {cfg['pair']} | {m['total_return_pct']:.2f}% | {m['win_rate']:.1f}% | "
            f"{m['profit_factor']:.2f} | {m['max_drawdown']:.2f}% | {m['sharpe_ratio']:.2f} | "
            f"{m['composite_score']:.2f} | {cfg['recommendation']} | "
            f"conf {m['confidence']}, RR {m['rr']}, ATR {m['atr_mult']} |"
        )
    entry = [
        "",
        "---",
        "",
        "## Session 6 — OANDA Optimization Results",
        f"Completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}",
        "",
        "Ran 36 trials per pair serially using OANDA parquets only. Applied anti-overfitting filters: minimum 25 trades, minimum 45% win rate, max drawdown no worse than -20%, and ranked valid trials by the required composite score.",
        "",
        "| Pair | Return | Win Rate | PF | Max DD | Sharpe | Score | Portfolio | Best Config |",
        "|---|---:|---:|---:|---:|---:|---:|---|---|",
        *rows,
        "",
        "Output files written under `optimized_results/`, including per-pair trial CSVs/reports and `optimized_results/MASTER_OPTIMIZATION_COMPARISON.md`.",
    ]
    with open("AGENT_MEMORY.md", "a") as f:
        f.write("\n".join(entry) + "\n")


def main() -> None:
    OUT_ROOT.mkdir(parents=True, exist_ok=True)
    configs = []
    for pair in PAIRS:
        configs.append(optimize_pair(pair))
    write_master(configs)
    append_memory(configs)
    print("\nOptimization complete. Master report: optimized_results/MASTER_OPTIMIZATION_COMPARISON.md")


if __name__ == "__main__":
    main()
