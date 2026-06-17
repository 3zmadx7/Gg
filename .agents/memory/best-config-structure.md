---
name: best_config.json structure
description: The nested JSON structure of the optimized best_config.json files
---

The `Git/optimized_results/{PAIR}/best_config.json` files have this structure:

```json
{
  "pair": "EURUSD",
  "selected_by": "composite_score_with_filters",
  "recommendation": "yes",
  "config": {
    "confidence_threshold": 0.62,
    "risk_reward": 2.0,
    "atr_stop_multiplier": 1.0,
    "train_months": 3,
    "timeframe": "M5",
    "xgb_params": {"learning_rate": 0.06, ...},
    "rf_params": {"max_depth": 8, ...}
  },
  "metrics": { ... }
}
```

**Why this matters:** The trading settings are under the nested `"config"` key. Access as `data["config"]["confidence_threshold"]`, NOT `data["confidence_threshold"]`.

**How to apply:** When loading best_config.json, store only the inner dict:
```python
with open(path) as f:
    self.configs[pair] = json.load(f)["config"]
```
Then access directly: `self.configs[pair]["confidence_threshold"]`.
