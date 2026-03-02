from fastapi import FastAPI, Query, Response

from crypto_monitor_auto import AutoCryptoMonitor, logger
import threading
import time
from datetime import datetime, timezone
from typing import List, Dict


app = FastAPI(
    title="Crypto Monitor API",
    description="HTTP API wrapper around the AutoCryptoMonitor for use on Render or other hosting platforms.",
    version="1.0.0",
)

# For web deployment we disable built-in desktop/Telegram notifications and instead
# surface alerts via HTTP so the browser (Chrome) can show notifications.
monitor = AutoCryptoMonitor(enable_notifications=False)

recent_alerts: List[Dict] = []
_alerts_lock = threading.Lock()
MAX_ALERTS = 200


def _background_auto_monitor() -> None:
    """Background loop: auto-discover symbols and collect alerts continuously."""
    logger.info("Starting background auto monitor loop for API.")
    while True:
        try:
            # Discover or refresh symbols
            if not monitor.active_symbols or monitor.should_refresh_symbols():
                logger.info("Background loop refreshing active symbols list...")
                monitor.active_symbols = monitor.discover_symbols()
                monitor.last_symbol_refresh = time.time()

            if not monitor.active_symbols:
                logger.error("Background loop: no active symbols discovered; sleeping before retry.")
                time.sleep(60)
                continue

            # Check each active symbol once per cycle
            for symbol in monitor.active_symbols:
                alerts = monitor.check_symbol(symbol)
                if alerts:
                    ts = datetime.now(timezone.utc).isoformat()
                    with _alerts_lock:
                        for msg in alerts:
                            recent_alerts.append(
                                {
                                    "symbol": symbol,
                                    "message": msg,
                                    "timestamp": ts,
                                }
                            )
                        # keep list bounded
                        if len(recent_alerts) > MAX_ALERTS:
                            del recent_alerts[: len(recent_alerts) - MAX_ALERTS]
                time.sleep(1)  # respect exchange rate limits

            # Short pause between full cycles
            time.sleep(5)
        except Exception as e:
            logger.error(f"Error in background auto monitor loop: {e}")
            time.sleep(60)


@app.on_event("startup")
def _start_background_worker() -> None:
    t = threading.Thread(target=_background_auto_monitor, daemon=True)
    t.start()


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.get("/check-symbol")
def check_symbol(symbol: str = Query(..., description="Symbol like BTC/USDT")) -> dict:
    """
    Check a single symbol for alert conditions and return any alerts as text messages.
    This is on-demand; the background loop runs automatically and powers /recent-alerts.
    """
    symbol = symbol.strip()
    alerts = monitor.check_symbol(symbol)
    ts = datetime.now(timezone.utc).isoformat()
    if alerts:
        with _alerts_lock:
            for msg in alerts:
                recent_alerts.append({"symbol": symbol, "message": msg, "timestamp": ts})
            if len(recent_alerts) > MAX_ALERTS:
                del recent_alerts[: len(recent_alerts) - MAX_ALERTS]
    return {
        "symbol": symbol,
        "alerts": alerts,
        "alert_count": len(alerts),
        "timestamp": ts,
    }


@app.get("/recent-alerts")
def get_recent_alerts(limit: int = 50) -> dict:
    """Return the most recent alerts collected by the background monitor."""
    limit = max(1, min(limit, MAX_ALERTS))
    with _alerts_lock:
        data = list(recent_alerts[-limit:])
    return {
        "count": len(data),
        "alerts": data,
    }


@app.get("/")
def root() -> dict:
    return {
        "message": "Crypto Monitor API is running.",
        "ui": "/ui",
        "endpoints": {
            "health": "/health",
            "check_symbol": "/check-symbol?symbol=BTC/USDT",
            "recent_alerts": "/recent-alerts",
        },
    }


@app.get("/ui", response_class=Response)
def ui() -> Response:
    """Simple HTML UI for checking a symbol from browser/mobile."""
    html = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
      <meta charset="UTF-8" />
      <meta name="viewport" content="width=device-width, initial-scale=1.0" />
      <title>Crypto Monitor UI</title>
      <style>
        body { font-family: system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; margin: 0; padding: 0; background: #020617; color: #e5e7eb; }
        .container { max-width: 600px; margin: 0 auto; padding: 1.5rem; }
        h1 { font-size: 1.75rem; margin-bottom: 0.5rem; }
        p { color: #9ca3af; }
        .card { background: #020617; border-radius: 1rem; padding: 1.25rem; border: 1px solid #1f2937; box-shadow: 0 10px 40px rgba(15,23,42,0.8); margin-top: 1.5rem; }
        label { display: block; margin-bottom: 0.5rem; font-weight: 500; }
        input { width: 100%; padding: 0.6rem 0.75rem; border-radius: 0.5rem; border: 1px solid #374151; background: #020617; color: #e5e7eb; outline: none; }
        input:focus { border-color: #22c55e; box-shadow: 0 0 0 1px #22c55e33; }
        button { margin-top: 0.75rem; width: 100%; padding: 0.7rem 1rem; border-radius: 9999px; border: none; background: linear-gradient(to right, #22c55e, #16a34a); color: #022c22; font-weight: 600; cursor: pointer; }
        button:disabled { opacity: 0.6; cursor: default; }
        .badge { display: inline-flex; align-items: center; gap: 0.4rem; font-size: 0.75rem; padding: 0.2rem 0.6rem; border-radius: 9999px; background: #022c22; color: #6ee7b7; border: 1px solid #05966933; }
        .badge-dot { width: 0.45rem; height: 0.45rem; border-radius: 9999px; background: #22c55e; box-shadow: 0 0 0 4px #22c55e33; }
        .result { margin-top: 1rem; white-space: pre-wrap; font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", "Courier New", monospace; font-size: 0.85rem; background: #020617; border-radius: 0.75rem; border: 1px solid #111827; padding: 0.8rem; max-height: 320px; overflow: auto; }
        .pill { display: inline-flex; align-items: center; gap: 0.35rem; padding: 0.2rem 0.6rem; border-radius: 9999px; font-size: 0.7rem; border: 1px solid #1f2937; color: #9ca3af; }
        .pill span { font-size: 0.5rem; opacity: 0.8; }
        .footer { margin-top: 1.5rem; font-size: 0.75rem; color: #6b7280; }
        a { color: #22c55e; text-decoration: none; }
      </style>
    </head>
    <body>
      <div class="container">
        <div class="badge">
          <span class="badge-dot"></span>
          Crypto Monitor · Online
        </div>
        <h1>Crypto Monitor Alerts</h1>
        <p>Auto monitor runs on the server and streams opportunities here. Keep this tab open in Chrome and allow notifications to get popups when new alerts appear.</p>

        <div class="card">
          <label for="symbol">Symbol</label>
          <input id="symbol" type="text" placeholder="BTC/USDT" value="BTC/USDT" />
          <button id="checkBtn">Check this symbol now</button>

          <div id="meta" style="margin-top:0.75rem; display:flex; gap:0.5rem; flex-wrap:wrap;">
            <div class="pill"><span>●</span>Live CCXT data</div>
            <div class="pill"><span>●</span>RSI + S/R levels</div>
          </div>

          <div id="result" class="result" style="display:none;"></div>

          <div id="stream" class="result" style="margin-top:0.75rem; display:none;"></div>
        </div>

        <div class="footer">
          Open from your phone or desktop browser. Chrome notifications are driven by this page; just keep it open. Server auto-monitor scans all symbols using your Render environment config.
        </div>
      </div>

      <script>
        const input = document.getElementById('symbol');
        const btn = document.getElementById('checkBtn');
        const result = document.getElementById('result');
        const stream = document.getElementById('stream');

        let lastNotifiedTs = null;

        function ensureNotificationPermission() {
          if (!('Notification' in window)) return;
          if (Notification.permission === 'default') {
            Notification.requestPermission();
          }
        }

        async function check() {
          const symbol = input.value.trim();
          if (!symbol) return;
          btn.disabled = true;
          btn.textContent = 'Checking...';
          result.style.display = 'block';
          result.textContent = 'Loading...';
          try {
            const resp = await fetch('/check-symbol?symbol=' + encodeURIComponent(symbol));
            if (!resp.ok) {
              result.textContent = 'Error: ' + resp.status + ' ' + resp.statusText;
            } else {
              const data = await resp.json();
              const alerts = (data.alerts || []).join('\\n\\n');
              result.textContent =
                'Symbol: ' + data.symbol + '\\n' +
                'Alert count: ' + data.alert_count + '\\n\\n' +
                (alerts || 'No alerts right now for this symbol.');
            }
          } catch (e) {
            result.textContent = 'Request failed: ' + e;
          } finally {
            btn.disabled = false;
            btn.textContent = 'Check this symbol now';
          }
        }

        btn.addEventListener('click', check);
        input.addEventListener('keydown', (e) => {
          if (e.key === 'Enter') check();
        });

        async function pollAlerts() {
          try {
            const resp = await fetch('/recent-alerts?limit=50');
            if (!resp.ok) return;
            const data = await resp.json();
            const alerts = data.alerts || [];
            if (!alerts.length) {
              stream.style.display = 'block';
              stream.textContent = 'No alerts yet. Monitoring in background...';
              return;
            }
            stream.style.display = 'block';
            const lines = alerts.map(a => {
              return `[${a.timestamp}] ${a.symbol} -> ${a.message.replace(/\\n/g, ' ')}`;
            });
            stream.textContent = lines.join('\\n\\n');

            // Browser notifications for new alerts
            if (!('Notification' in window) || Notification.permission !== 'granted') return;
            for (const a of alerts) {
              if (!a.timestamp) continue;
              if (lastNotifiedTs && a.timestamp <= lastNotifiedTs) continue;
              new Notification(a.symbol + ' alert', { body: a.message });
            }
            if (alerts.length) {
              lastNotifiedTs = alerts[alerts.length - 1].timestamp;
            }
          } catch (e) {
            // ignore errors during polling
          }
        }

        ensureNotificationPermission();
        pollAlerts();
        setInterval(pollAlerts, 15000);
      </script>
    </body>
    </html>
    """
    return Response(content=html, media_type="text/html")
