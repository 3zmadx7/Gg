# Railway Deployment Guide — Forex Signal Bot

Plain English instructions. No technical experience needed beyond what you already know (GitHub + Railway).

---

## What You Need First (2 things from Telegram)

Before deploying, you need a Telegram bot token. It takes 2 minutes:

1. Open Telegram and search for **@BotFather**
2. Send `/newbot` and follow the prompts — pick a name and username
3. BotFather gives you a **Bot Token** that looks like `1234567890:ABCDEFabcdef...` — copy it
4. Start a chat with your new bot (search its username and hit Start)
5. Visit `https://api.telegram.org/bot<YOUR_TOKEN>/getUpdates` in your browser to get your **Chat ID** (it's a number like `987654321`)

---

## Step 1 — Prepare Your GitHub Repo

Create a new GitHub repository and push these files/folders into it.

**From the `Git/` folder of this project:**
- `signal_bot.py`
- `test_bot.py`
- `Procfile`
- `requirements_bot.txt`
- `data/` folder (the Python modules — `data_loader.py`, `oanda_downloader.py`, etc.)
- `ml/` folder
- `features/` folder
- `core/` folder
- `utils/` folder
- `optimized_results/` folder (contains `EURUSD/best_config.json`, etc.)
- `models_live/` folder (can be empty)

**Also include from the project root (one level up from Git/):**
- `learning/` folder — required because `ml/trainer.py` imports from it

> Easiest way: ZIP the entire `Git/` folder contents + the `learning/` folder together, then drag-drop into a new GitHub repo.

---

## Step 2 — Connect GitHub to Railway

1. Go to [railway.app](https://railway.app) and log in
2. Click **New Project** → **Deploy from GitHub Repo**
3. Select the GitHub repository you just created
4. Railway detects the `Procfile` automatically — it knows to run `python3 signal_bot.py` as a worker

---

## Step 3 — Add Environment Variables in Railway

In your Railway project, go to **Variables** and add these four:

| Variable | Value |
|---|---|
| `OANDA_TOKEN` | Your OANDA practice account API token |
| `OANDA_BASE_URL` | `https://api-fxpractice.oanda.com/v3` |
| `TELEGRAM_BOT_TOKEN` | The token from @BotFather |
| `TELEGRAM_CHAT_ID` | Your Telegram chat ID (the number) |

---

## Step 4 — Deploy

Click **Deploy** (or Railway does it automatically after adding variables).

---

## What Happens Once Live

1. **Startup (~2–5 min):** The bot fetches the last 2–3 months of M5 data from OANDA and trains one model for each of the 4 currency pairs (EURUSD, GBPUSD, USDJPY, NZDUSD). You will see console logs in Railway showing the training progress.

2. **Every 5 minutes:** The bot checks all 4 pairs. If a pair's model gives a BUY or SELL signal above its confidence threshold, you get a Telegram message like this:

```
🟢 BUY EUR/USD
━━━━━━━━━━━━━━
Entry:  1.15320
SL:     1.15020  (−30 pips)
TP:     1.15920  (+60 pips)
Confidence: 78.4%
Time: 14:30 UTC
```

3. **60-minute cooldown:** The bot will not send a second signal for the same pair within 60 minutes, regardless of what the model says.

---

## Troubleshooting

| Problem | Fix |
|---|---|
| Bot starts but no Telegram messages | Signals only fire when confidence exceeds the threshold. Normal — the bot may be quiet for hours on slow market days. |
| `OANDA_TOKEN` error on startup | Check the token is correctly pasted in Railway Variables (no extra spaces) |
| Telegram message not arriving | Make sure you started a chat with your bot BEFORE deploying |
| Bot crashes on startup | Check Railway logs — most common cause is a missing environment variable |

---

## Signal Pair Settings (from optimization)

| Pair | Confidence Threshold | Risk:Reward | ATR Stop Mult | Training Window |
|---|---|---|---|---|
| EURUSD | 62% | 1:2.0 | 1.0× ATR | 3 months |
| GBPUSD | 68% | 1:2.5 | 2.0× ATR | 2 months |
| USDJPY | 55% | 1:1.5 | 1.0× ATR | 3 months |
| NZDUSD | 55% | 1:1.5 | 1.0× ATR | 3 months |
