---
name: Signal bot label mapping
description: Correct model label-to-action mapping for the forex signal bot ensemble
---

The ML ensemble trained in this project uses: **0=BUY, 1=SELL, 2=HOLD**.

This is confirmed in `pipeline_oanda.py` line 227:
```python
label = {0: "BUY", 1: "SELL", 2: "HOLD"}
```

And in `optimize_oanda.py` line 246 (identical mapping).

**Why:** `ml/trainer.py` sets `y = np.zeros(...)` (defaults all to 0), then sets `y[future_return < -sell_threshold] = 1` (SELL) and `y[hold_range] = 2` (HOLD). So positive future return stays 0 = BUY.

**How to apply:** In signal_bot.py, check `if pred in (0, 1)` to fire signals. The replit.md note saying "0=HOLD, 1=BUY, 2=SELL" is WRONG — trust the code.
