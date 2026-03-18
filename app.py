from fastapi import FastAPI, Query, Response
from pydantic import BaseModel, Field

from crypto_monitor_auto import AutoCryptoMonitor, logger
import threading
import time
from datetime import datetime, timezone
from typing import List, Dict, Optional, Any
from collections import deque


app = FastAPI(
    title="Crypto Monitor API",
    description="HTTP API wrapper around the AutoCryptoMonitor for use on Render or other hosting platforms.",
    version="1.0.0",
)

MAX_ALERTS = 200
MAX_LOG_LINES = 600


class ConfigPayload(BaseModel):
    exchange: str = Field(default="bybit")
    quote_currencies: str = Field(default="USDT,USD,BTC,ETH")
    min_volume_24h: float = Field(default=1_000_000)
    max_symbols: int = Field(default=100)
    check_interval: int = Field(default=300)
    rsi_overbought: float = Field(default=90)
    rsi_oversold: float = Field(default=10)


class MonitorService:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._alerts_lock = threading.Lock()
        self._stop_event = threading.Event()
        self._thread: Optional[threading.Thread] = None

        # For web deployment we disable desktop/telegram notifications; UI surfaces alerts.
        self.monitor = AutoCryptoMonitor(enable_notifications=False)

        self.recent_alerts: List[Dict[str, Any]] = []
        self.log_lines: deque[str] = deque(maxlen=MAX_LOG_LINES)

        self.is_running: bool = False
        self.last_discovery_at: Optional[str] = None
        self.cycle: int = 0
        self.checked_this_cycle: int = 0
        self.last_cycle_started_at: Optional[str] = None

        self._install_log_tap()

    def _install_log_tap(self) -> None:
        import logging

        class _BufferHandler(logging.Handler):
            def __init__(self, buf: deque[str]):
                super().__init__()
                self.buf = buf

            def emit(self, record: logging.LogRecord) -> None:
                try:
                    msg = self.format(record)
                except Exception:
                    msg = record.getMessage()
                self.buf.append(msg)

        handler = _BufferHandler(self.log_lines)
        handler.setLevel(logging.INFO)
        handler.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(message)s"))
        logging.getLogger().addHandler(handler)

    def _apply_config_to_monitor(self, cfg: ConfigPayload) -> None:
        # Render env vars are static; this enables runtime tweaking via the web UI.
        self.monitor.exchange_name = (cfg.exchange or "").strip() or self.monitor.exchange_name
        self.monitor.check_interval = int(cfg.check_interval)
        self.monitor.rsi_overbought = float(cfg.rsi_overbought)
        self.monitor.rsi_oversold = float(cfg.rsi_oversold)
        self.monitor.quote_currencies = [s.strip() for s in (cfg.quote_currencies or "").split(",") if s.strip()]
        self.monitor.min_volume_24h = float(cfg.min_volume_24h)
        self.monitor.max_symbols = int(cfg.max_symbols)

        try:
            import ccxt

            self.monitor.exchange = getattr(ccxt, self.monitor.exchange_name)()
        except Exception as e:
            logger.error(f"Failed to init exchange '{self.monitor.exchange_name}': {e}")

    def get_config(self) -> ConfigPayload:
        with self._lock:
            return ConfigPayload(
                exchange=self.monitor.exchange_name,
                quote_currencies=",".join(self.monitor.quote_currencies),
                min_volume_24h=self.monitor.min_volume_24h,
                max_symbols=self.monitor.max_symbols,
                check_interval=self.monitor.check_interval,
                rsi_overbought=self.monitor.rsi_overbought,
                rsi_oversold=self.monitor.rsi_oversold,
            )

    def set_config(self, cfg: ConfigPayload) -> None:
        with self._lock:
            self._apply_config_to_monitor(cfg)

    def start(self) -> None:
        with self._lock:
            if self.is_running:
                return
            self._stop_event.clear()
            self.is_running = True
            self._thread = threading.Thread(target=self._run_loop, daemon=True)
            self._thread.start()

    def stop(self) -> None:
        with self._lock:
            if not self.is_running:
                return
            self._stop_event.set()
            self.is_running = False

    def discover_now(self) -> List[str]:
        with self._lock:
            symbols = self.monitor.discover_symbols()
            self.monitor.active_symbols = symbols
            self.monitor.last_symbol_refresh = time.time()
            self.last_discovery_at = datetime.now(timezone.utc).isoformat()
            return symbols

    def _append_alerts(self, symbol: str, alerts: List[str]) -> None:
        if not alerts:
            return
        ts = datetime.now(timezone.utc).isoformat()
        with self._alerts_lock:
            for msg in alerts:
                self.recent_alerts.append({"symbol": symbol, "message": msg, "timestamp": ts})
            if len(self.recent_alerts) > MAX_ALERTS:
                del self.recent_alerts[: len(self.recent_alerts) - MAX_ALERTS]

    def _run_loop(self) -> None:
        logger.info("Monitor loop started (controlled via /ui).")
        while not self._stop_event.is_set():
            try:
                with self._lock:
                    self.cycle += 1
                    self.checked_this_cycle = 0
                    self.last_cycle_started_at = datetime.now(timezone.utc).isoformat()

                    if not self.monitor.active_symbols or self.monitor.should_refresh_symbols():
                        logger.info("Refreshing active symbols list...")
                        self.monitor.active_symbols = self.monitor.discover_symbols()
                        self.monitor.last_symbol_refresh = time.time()
                        self.last_discovery_at = datetime.now(timezone.utc).isoformat()

                    symbols_snapshot = list(self.monitor.active_symbols)
                    interval = int(self.monitor.check_interval)

                if not symbols_snapshot:
                    logger.error("No active symbols discovered; sleeping before retry.")
                    self._stop_event.wait(30)
                    continue

                logger.info(f"=== Cycle {self.cycle}: Checking {len(symbols_snapshot)} symbols ===")
                for symbol in symbols_snapshot:
                    if self._stop_event.is_set():
                        break
                    alerts = self.monitor.check_symbol(symbol)
                    self._append_alerts(symbol, alerts)
                    with self._lock:
                        self.checked_this_cycle += 1
                    time.sleep(1)

                if self._stop_event.is_set():
                    break

                logger.info(f"Cycle {self.cycle} complete. Waiting {interval} seconds...")
                self._stop_event.wait(max(1, interval))
            except Exception as e:
                logger.error(f"Error in monitor loop: {e}")
                self._stop_event.wait(30)

        logger.info("Monitor loop stopped.")

    def status(self) -> Dict[str, Any]:
        with self._lock:
            symbols_count = len(self.monitor.active_symbols or [])
            alerts_count = len(getattr(self.monitor, "last_alerts", {}) or {})
            return {
                "is_running": self.is_running,
                "exchange": self.monitor.exchange_name,
                "symbols_monitoring": symbols_count,
                "alerts_sent": alerts_count,
                "cycle": self.cycle,
                "checked_this_cycle": self.checked_this_cycle,
                "last_discovery_at": self.last_discovery_at,
                "last_cycle_started_at": self.last_cycle_started_at,
            }

    def recent_alerts_payload(self, limit: int) -> Dict[str, Any]:
        limit = max(1, min(limit, MAX_ALERTS))
        with self._alerts_lock:
            data = list(self.recent_alerts[-limit:])
        return {"count": len(data), "alerts": data}

    def logs_payload(self, since: int = 0, limit: int = 200) -> Dict[str, Any]:
        limit = max(1, min(limit, MAX_LOG_LINES))
        lines = list(self.log_lines)
        since = max(0, min(since, len(lines)))
        chunk = lines[since:][-limit:]
        next_since = since + len(chunk)
        return {"lines": chunk, "next_since": next_since, "total": len(lines)}


svc = MonitorService()


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.get("/check-symbol")
def check_symbol(symbol: str = Query(..., description="Symbol like BTC/USDT")) -> dict:
    """
    Check a single symbol for alert conditions and return any alerts as text messages.
    This is on-demand; the UI-controlled loop powers /recent-alerts.
    """
    symbol = symbol.strip()
    alerts = svc.monitor.check_symbol(symbol)
    if alerts:
        svc._append_alerts(symbol, alerts)
    ts = datetime.now(timezone.utc).isoformat()
    return {
        "symbol": symbol,
        "alerts": alerts,
        "alert_count": len(alerts),
        "timestamp": ts,
    }


@app.get("/recent-alerts")
def get_recent_alerts(limit: int = 50) -> dict:
    """Return the most recent alerts collected by the background monitor."""
    return svc.recent_alerts_payload(limit=limit)


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


@app.get("/api/config")
def api_get_config() -> dict:
    return svc.get_config().model_dump()


@app.post("/api/config")
def api_set_config(payload: ConfigPayload) -> dict:
    svc.set_config(payload)
    return {"ok": True, "config": svc.get_config().model_dump()}


@app.get("/api/status")
def api_status() -> dict:
    return svc.status()


@app.post("/api/start")
def api_start() -> dict:
    svc.start()
    return {"ok": True, "status": svc.status()}


@app.post("/api/stop")
def api_stop() -> dict:
    svc.stop()
    return {"ok": True, "status": svc.status()}


@app.post("/api/discover")
def api_discover() -> dict:
    symbols = svc.discover_now()
    return {"ok": True, "count": len(symbols), "symbols": symbols[:20], "total": len(symbols)}


@app.get("/api/logs")
def api_logs(since: int = 0, limit: int = 200) -> dict:
    return svc.logs_payload(since=since, limit=limit)


@app.get("/ui", response_class=Response)
def ui() -> Response:
    """Web UI matching the desktop Auto-Discovery GUI."""
    html = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
      <meta charset="UTF-8" />
      <meta name="viewport" content="width=device-width, initial-scale=1.0" />
      <title>Crypto Monitor - Auto Discovery</title>
      <style>
        :root {
          --bg: #f3f4f6;
          --panel: #ffffff;
          --border: #d1d5db;
          --text: #111827;
          --muted: #6b7280;
          --btn: #e5e7eb;
          --btn-text: #111827;
          --primary: #2563eb;
          --danger: #dc2626;
          --ok: #16a34a;
          --shadow: 0 8px 24px rgba(17, 24, 39, 0.10);
        }
        body { font-family: system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; margin: 0; background: var(--bg); color: var(--text); }
        .app { max-width: 1200px; margin: 0 auto; padding: 16px; }
        .titlebar { display: flex; align-items: baseline; justify-content: space-between; gap: 12px; padding: 10px 12px; background: var(--panel); border: 1px solid var(--border); border-radius: 10px; box-shadow: var(--shadow); }
        .titlebar h1 { font-size: 18px; margin: 0; font-weight: 650; }
        .titlebar .status { display: inline-flex; align-items: center; gap: 8px; font-size: 13px; color: var(--muted); }
        .dot { width: 10px; height: 10px; border-radius: 9999px; background: #9ca3af; box-shadow: 0 0 0 3px rgba(156,163,175,0.25); }
        .dot.ok { background: var(--ok); box-shadow: 0 0 0 3px rgba(22,163,74,0.20); }
        .dot.bad { background: var(--danger); box-shadow: 0 0 0 3px rgba(220,38,38,0.20); }
        .grid { margin-top: 12px; display: grid; grid-template-columns: 1fr; gap: 12px; }
        @media (min-width: 980px) { .grid { grid-template-columns: 1.2fr 0.8fr; } }
        .panel { background: var(--panel); border: 1px solid var(--border); border-radius: 10px; box-shadow: var(--shadow); padding: 12px; }
        .panel h2 { margin: 0 0 10px 0; font-size: 14px; font-weight: 650; }
        .form { display: grid; grid-template-columns: 1fr; gap: 10px; }
        @media (min-width: 980px) { .form { grid-template-columns: 1fr 1fr; } }
        .field label { display: block; font-size: 12px; margin-bottom: 4px; }
        .hint { font-size: 11px; color: var(--muted); margin-top: 3px; }
        input { width: 100%; box-sizing: border-box; padding: 8px 10px; border-radius: 6px; border: 1px solid var(--border); outline: none; background: #fff; color: var(--text); font-size: 13px; }
        input:focus { border-color: rgba(37, 99, 235, 0.55); box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.15); }
        .actions { display: flex; flex-wrap: wrap; gap: 8px; align-items: center; margin-top: 10px; }
        button { appearance: none; border: 1px solid var(--border); background: var(--btn); color: var(--btn-text); border-radius: 6px; padding: 8px 10px; font-size: 13px; cursor: pointer; }
        button.primary { background: var(--primary); border-color: rgba(37, 99, 235, 0.85); color: #fff; }
        button.danger { background: var(--danger); border-color: rgba(220, 38, 38, 0.85); color: #fff; }
        button:disabled { opacity: 0.6; cursor: default; }
        .stats { display: flex; flex-wrap: wrap; gap: 18px; font-size: 13px; }
        .stat b { font-weight: 700; }
        .mono { font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", "Courier New", monospace; }
        .symbols { border: 1px solid var(--border); border-radius: 8px; padding: 8px; min-height: 54px; background: #fafafa; font-size: 12px; line-height: 1.35; }
        .log { border: 1px solid var(--border); border-radius: 8px; padding: 10px; background: #0b1220; color: #e5e7eb; height: 320px; overflow: auto; font-size: 12px; line-height: 1.35; white-space: pre-wrap; }
        .subpanels { display: grid; grid-template-columns: 1fr; gap: 12px; }
      </style>
    </head>
    <body>
      <div class="app">
        <div class="titlebar">
          <h1>Crypto Monitor - Auto Discovery</h1>
          <div class="status">
            <span id="statusDot" class="dot"></span>
            <span id="statusText">Status: Loading...</span>
          </div>
        </div>

        <div class="grid">
          <div>
            <div class="panel">
              <h2>Auto-Discovery Configuration</h2>
              <div class="form">
                <div class="field">
                  <label for="exchange">Exchange:</label>
                  <input id="exchange" type="text" placeholder="bybit" />
                </div>
                <div class="field">
                  <label for="quotes">Quote Currencies (comma-separated):</label>
                  <input id="quotes" type="text" placeholder="USDT,USD,BTC,ETH" />
                  <div class="hint">e.g., USDT,USD,BTC,ETH</div>
                </div>
                <div class="field">
                  <label for="minVol">Minimum 24h Volume ($):</label>
                  <input id="minVol" type="number" step="1" />
                </div>
                <div class="field">
                  <label for="maxSymbols">Max Symbols to Monitor:</label>
                  <input id="maxSymbols" type="number" step="1" />
                </div>
                <div class="field">
                  <label for="interval">Check Interval (seconds):</label>
                  <input id="interval" type="number" step="1" />
                </div>
                <div class="field">
                  <label for="rsiOver">RSI Overbought (&gt;):</label>
                  <input id="rsiOver" type="number" step="0.01" />
                </div>
                <div class="field">
                  <label for="rsiUnder">RSI Oversold (&lt;):</label>
                  <input id="rsiUnder" type="number" step="0.01" />
                </div>
              </div>

              <div class="actions">
                <button id="saveBtn">Save Configuration</button>
                <button id="startBtn" class="primary">Start Auto-Discovery</button>
                <button id="stopBtn" class="danger">Stop Monitoring</button>
                <button id="discoverBtn">Discover Symbols Now</button>
              </div>
            </div>

            <div class="panel" style="margin-top:12px;">
              <h2>Statistics</h2>
              <div class="stats">
                <div class="stat">Symbols Monitoring: <b id="statSymbols">0</b></div>
                <div class="stat">Alerts Sent: <b id="statAlerts">0</b></div>
                <div class="stat">Cycle: <b id="statCycle">0</b></div>
                <div class="stat">Progress: <b id="statProgress">0/0</b></div>
              </div>
            </div>

            <div class="panel" style="margin-top:12px;">
              <h2>Discovered Symbols (Top 20)</h2>
              <div id="symbolsBox" class="symbols mono">Loading...</div>
              <div class="hint" id="symbolsHint"></div>
            </div>
          </div>

          <div class="subpanels">
            <div class="panel">
              <h2>Activity Log</h2>
              <div id="logBox" class="log mono">Loading...</div>
              <div class="actions" style="margin-top:10px;">
                <button id="clearLogBtn">Clear Log</button>
              </div>
            </div>

            <div class="panel">
              <h2>Quick Check (single symbol)</h2>
              <div class="field">
                <label for="symbol">Symbol</label>
                <input id="symbol" type="text" placeholder="BTC/USDT" value="BTC/USDT" />
              </div>
              <div class="actions">
                <button id="checkBtn" class="primary">Check this symbol now</button>
              </div>
              <div id="checkResult" class="symbols mono" style="margin-top:10px; background:#0b1220; color:#e5e7eb; border-color:#111827; min-height:64px;">Result will appear here…</div>
            </div>
          </div>
        </div>
      </div>

      <script>
        const els = {
          statusDot: document.getElementById('statusDot'),
          statusText: document.getElementById('statusText'),
          exchange: document.getElementById('exchange'),
          quotes: document.getElementById('quotes'),
          minVol: document.getElementById('minVol'),
          maxSymbols: document.getElementById('maxSymbols'),
          interval: document.getElementById('interval'),
          rsiOver: document.getElementById('rsiOver'),
          rsiUnder: document.getElementById('rsiUnder'),
          saveBtn: document.getElementById('saveBtn'),
          startBtn: document.getElementById('startBtn'),
          stopBtn: document.getElementById('stopBtn'),
          discoverBtn: document.getElementById('discoverBtn'),
          statSymbols: document.getElementById('statSymbols'),
          statAlerts: document.getElementById('statAlerts'),
          statCycle: document.getElementById('statCycle'),
          statProgress: document.getElementById('statProgress'),
          symbolsBox: document.getElementById('symbolsBox'),
          symbolsHint: document.getElementById('symbolsHint'),
          logBox: document.getElementById('logBox'),
          clearLogBtn: document.getElementById('clearLogBtn'),
          symbol: document.getElementById('symbol'),
          checkBtn: document.getElementById('checkBtn'),
          checkResult: document.getElementById('checkResult'),
        };

        let logSince = 0;
        let lastDiscoveredText = '';

        async function json(url, opts) {
          const r = await fetch(url, opts);
          if (!r.ok) throw new Error(r.status + ' ' + r.statusText);
          return await r.json();
        }

        function setRunningUI(isRunning) {
          els.statusDot.className = 'dot ' + (isRunning ? 'ok' : 'bad');
          els.statusText.textContent = 'Status: ' + (isRunning ? 'Running' : 'Stopped');
          els.startBtn.disabled = isRunning;
          els.stopBtn.disabled = !isRunning;
        }

        async function loadConfig() {
          const cfg = await json('/api/config');
          els.exchange.value = cfg.exchange ?? '';
          els.quotes.value = cfg.quote_currencies ?? '';
          els.minVol.value = cfg.min_volume_24h ?? '';
          els.maxSymbols.value = cfg.max_symbols ?? '';
          els.interval.value = cfg.check_interval ?? '';
          els.rsiOver.value = cfg.rsi_overbought ?? '';
          els.rsiUnder.value = cfg.rsi_oversold ?? '';
        }

        async function saveConfig() {
          els.saveBtn.disabled = true;
          try {
            const payload = {
              exchange: els.exchange.value,
              quote_currencies: els.quotes.value,
              min_volume_24h: Number(els.minVol.value || 0),
              max_symbols: Number(els.maxSymbols.value || 0),
              check_interval: Number(els.interval.value || 0),
              rsi_overbought: Number(els.rsiOver.value || 0),
              rsi_oversold: Number(els.rsiUnder.value || 0),
            };
            await json('/api/config', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(payload) });
          } finally {
            els.saveBtn.disabled = false;
          }
        }

        async function start() {
          els.startBtn.disabled = true;
          await json('/api/start', { method: 'POST' });
          await pollStatus();
        }

        async function stop() {
          els.stopBtn.disabled = true;
          await json('/api/stop', { method: 'POST' });
          await pollStatus();
        }

        async function discover() {
          els.discoverBtn.disabled = true;
          try {
            const data = await json('/api/discover', { method: 'POST' });
            const list = (data.symbols || []).join(', ');
            lastDiscoveredText = list || '(no symbols discovered)';
            els.symbolsBox.textContent = lastDiscoveredText;
            els.symbolsHint.textContent = data.total ? ('and ' + Math.max(0, data.total - (data.symbols || []).length) + ' more') : '';
          } catch (e) {
            els.symbolsBox.textContent = 'Discovery failed: ' + e;
          } finally {
            els.discoverBtn.disabled = false;
          }
        }

        async function pollStatus() {
          try {
            const st = await json('/api/status');
            setRunningUI(!!st.is_running);
            els.statSymbols.textContent = String(st.symbols_monitoring ?? 0);
            els.statAlerts.textContent = String(st.alerts_sent ?? 0);
            els.statCycle.textContent = String(st.cycle ?? 0);
            els.statProgress.textContent = String(st.checked_this_cycle ?? 0) + '/' + String(st.symbols_monitoring ?? 0);
            if (!lastDiscoveredText) {
              els.symbolsBox.textContent = st.symbols_monitoring ? 'Click "Discover Symbols Now" to populate top 20.' : 'No symbols yet.';
            }
          } catch (e) {
            els.statusDot.className = 'dot';
            els.statusText.textContent = 'Status: Offline (refresh page)';
          }
        }

        async function pollLogs() {
          try {
            const data = await json('/api/logs?since=' + encodeURIComponent(logSince) + '&limit=200');
            const lines = data.lines || [];
            if (logSince === 0 && lines.length) {
              els.logBox.textContent = lines.join('\\n');
            } else if (lines.length) {
              els.logBox.textContent += '\\n' + lines.join('\\n');
            }
            logSince = data.next_since || logSince;
            els.logBox.scrollTop = els.logBox.scrollHeight;
          } catch (e) {}
        }

        async function quickCheck() {
          const symbol = (els.symbol.value || '').trim();
          if (!symbol) return;
          els.checkBtn.disabled = true;
          els.checkBtn.textContent = 'Checking...';
          try {
            const data = await json('/check-symbol?symbol=' + encodeURIComponent(symbol));
            const alerts = (data.alerts || []).join('\\n\\n');
            els.checkResult.textContent = 'Symbol: ' + data.symbol + '\\n' + 'Alert count: ' + data.alert_count + '\\n\\n' + (alerts || 'No alerts right now for this symbol.');
          } catch (e) {
            els.checkResult.textContent = 'Check failed: ' + e;
          } finally {
            els.checkBtn.disabled = false;
            els.checkBtn.textContent = 'Check this symbol now';
          }
        }

        els.saveBtn.addEventListener('click', saveConfig);
        els.startBtn.addEventListener('click', async () => { await saveConfig(); await start(); });
        els.stopBtn.addEventListener('click', stop);
        els.discoverBtn.addEventListener('click', async () => { await saveConfig(); await discover(); });
        els.clearLogBtn.addEventListener('click', () => { els.logBox.textContent = ''; logSince = 0; });
        els.checkBtn.addEventListener('click', quickCheck);
        els.symbol.addEventListener('keydown', (e) => { if (e.key === 'Enter') quickCheck(); });

        (async function boot() {
          await loadConfig();
          await pollStatus();
          await pollLogs();
          setInterval(pollStatus, 3000);
          setInterval(pollLogs, 1500);
        })();
      </script>
    </body>
    </html>
    """
    return Response(content=html, media_type="text/html")
