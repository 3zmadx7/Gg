---
name: Project module split
description: Where Python modules live — split between Git/ subfolder and project root
---

This project has modules in TWO locations:

**Git/ subfolder** (`/home/runner/workspace/Git/`):
- `data/` — DataLoader, oanda_downloader, market_data_engine
- `ml/` — ensemble, trainer, model_manager, xgboost/rf models
- `features/` — FeaturePipeline and all indicator engines
- `core/` — constants (LOOKAHEAD_5, HISTORICAL_DIR, etc.), config, exceptions
- `utils/` — logger, decorators, helpers

**Project root** (`/home/runner/workspace/`):
- `learning/` — TradeMemory, MistakeWeighting (imported by ml/trainer.py)
- `backtest/`, `decision/`, `intelligence/`, `risk/`, `trading/` — other modules

**Why:** The original GitHub-imported bot was in Git/ but the pipeline files and supporting modules were built at the project root. They grew in parallel.

**How to apply:** Any script that imports from `ml.trainer` will transitively need `learning/`. Always add BOTH paths to sys.path:
```python
SCRIPT_DIR = Path(__file__).parent.resolve()
PROJECT_ROOT = SCRIPT_DIR.parent  # if script is in Git/
for p in (str(SCRIPT_DIR), str(PROJECT_ROOT)):
    if p not in sys.path:
        sys.path.insert(0, p)
```
For Railway deployment, include the `learning/` directory in the GitHub repo alongside the Git/ contents.
