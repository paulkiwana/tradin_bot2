# Deploying Crypto Monitor API to Render

This guide explains how to deploy the FastAPI wrapper for the auto crypto monitor to [Render](https://render.com).

## 1. Overview

- **App type**: Python Web Service (FastAPI)
- **Entry point**: `app.py` exposing `app = FastAPI(...)`
- **Primary endpoints**:
  - `GET /ui` – browser UI (desktop or phone, with Chrome notifications)
  - `GET /check-symbol?symbol=BTC/USDT` – JSON API
  - `GET /recent-alerts` – JSON feed of most recent auto-monitor alerts

On Render, desktop notifications are not available, so alerts are returned as JSON and surfaced as **Chrome notifications** from the `/ui` page (and optionally via **Telegram** if configured).

## 2. Prerequisites

- A GitHub, GitLab, or Bitbucket account with this project pushed to a repository.
- A Render account.

## 3. Prepare the repository

1. Make sure the following files are in the repo root:
   - `app.py` (FastAPI app)
   - `requirements.txt`
   - `crypto_monitor_auto.py`
2. Commit and push your changes to your remote repository.

## 4. Create the Render Web Service

1. Log in to Render and click **New +** → **Web Service**.
2. Connect your Git repo and select the branch containing this project.
3. Set the **Environment** to `Python 3` (e.g., Python 3.11).
4. Configure:
   - **Build Command**:
     ```bash
     pip install -r requirements.txt
     ```
   - **Start Command**:
     ```bash
     uvicorn app:app --host 0.0.0.0 --port 10000
     ```

Render exposes your service on port `10000` internally, so we bind uvicorn to that port.

## 5. Environment variables on Render

Any configuration you previously kept in `.env` (for local usage) should be added as Render environment variables.

Common examples:

- `EXCHANGE` (e.g., `bybit`, `binance`)
- `CHECK_INTERVAL`
- `RSI_OVERBOUGHT`
- `RSI_OVERSOLD`
- `SR_THRESHOLD`
- `QUOTE_CURRENCIES`
- `MIN_VOLUME_24H`
- `MIN_PRICE`
- `MAX_SYMBOLS`
- `REFRESH_SYMBOLS_HOURS`
- `NOTIFICATION_MODE` (set to `telegram` on Render if you want phone alerts)
- `TELEGRAM_BOT_TOKEN`
- `TELEGRAM_CHAT_ID`

In the Render dashboard for your service:

1. Go to **Environment** → **Environment Variables**.
2. Add each key/value pair that you want to override (values from `.env.example` are a good starting point).
3. Save and redeploy if prompted.

## 6. Testing the deployed API

After Render finishes building and deploying, you will get a public URL, e.g.:

`https://your-service-name.onrender.com`

You can test:

- **Health check**:
  ```bash
  curl https://your-service-name.onrender.com/health
  ```

- **Check a symbol**:
  ```bash
  curl "https://your-service-name.onrender.com/check-symbol?symbol=BTC/USDT"
  ```

- **Open the web UI** (desktop or phone):
  - Visit: `https://your-service-name.onrender.com/ui`

Expected JSON response:

```json
{
  "symbol": "BTC/USDT",
  "alerts": [
    "BTC/USDT Alert! ... "
  ],
  "alert_count": 1
}
```

If `alert_count` is `0`, there are currently no qualifying alerts for that symbol.

## 7. Notes and limitations

- This API performs live requests to the configured exchange using `ccxt`, so response times depend on exchange latency.
- On Render, desktop notifications are disabled; alerts are returned in the HTTP response body only.
- For higher throughput or scheduling, you can:
  - Use Render **Cron Jobs** to hit the `/check-symbol` endpoint periodically.
  - Or build a small client script or frontend that polls this API and displays alerts.

