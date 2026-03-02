# System Architecture

## 🏗️ High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         USER INTERFACE                          │
│                                                                 │
│  ┌──────────────────┐              ┌──────────────────┐        │
│  │   GUI Version    │              │ Console Version  │        │
│  │  (Tkinter UI)    │              │  (CLI Output)    │        │
│  └────────┬─────────┘              └────────┬─────────┘        │
│           │                                  │                  │
│           └──────────────┬───────────────────┘                  │
└───────────────────────────┼──────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│                    CRYPTO MONITOR CORE                          │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │              Configuration Manager                      │   │
│  │  • Load .env settings                                   │   │
│  │  • Validate parameters                                  │   │
│  │  • Manage symbols list                                  │   │
│  └─────────────────────────────────────────────────────────┘   │
│                            │                                    │
│                            ▼                                    │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │              Monitoring Loop                            │   │
│  │  • Iterate through symbols                              │   │
│  │  • Schedule checks                                      │   │
│  │  • Handle errors                                        │   │
│  └─────────────────────────────────────────────────────────┘   │
│                            │                                    │
│           ┌────────────────┼────────────────┐                   │
│           ▼                ▼                ▼                   │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐           │
│  │ Data Fetcher │ │   Analyzer   │ │Alert Manager │           │
│  └──────────────┘ └──────────────┘ └──────────────┘           │
└─────────────────────────────────────────────────────────────────┘
         │                  │                  │
         ▼                  ▼                  ▼
┌──────────────┐  ┌──────────────────┐  ┌──────────────┐
│   Exchange   │  │    Indicators    │  │Notifications │
│   (CCXT)     │  │  • S/R Detector  │  │   (Plyer)    │
│              │  │  • RSI Calculator│  │              │
└──────────────┘  └──────────────────┘  └──────────────┘
```

---

## 🔄 Data Flow

```
START
  │
  ├─→ [1] Load Configuration
  │     • Read .env file
  │     • Parse symbols
  │     • Set thresholds
  │
  ├─→ [2] Initialize Exchange Connection
  │     • Create CCXT instance
  │     • Verify connectivity
  │
  └─→ [3] Main Loop
        │
        ├─→ For Each Symbol:
        │     │
        │     ├─→ [4] Fetch Historical Data
        │     │     │
        │     │     ├─→ API Call: 1-Month OHLCV (100 candles)
        │     │     ├─→ API Call: 1-Week OHLCV (100 candles)
        │     │     ├─→ API Call: 1-Day OHLCV (100 candles)
        │     │     └─→ API Call: 4-Hour OHLCV (100 candles)
        │     │     │
        │     │     └─→ Convert to Pandas DataFrames
        │     │
        │     ├─→ [5] Calculate Support/Resistance
        │     │     │
        │     │     ├─→ Find Pivot Points (1M data)
        │     │     ├─→ Find Pivot Points (1W data)
        │     │     ├─→ Cluster Nearby Levels
        │     │     └─→ Return S/R List
        │     │
        │     ├─→ [6] Calculate RSI
        │     │     │
        │     │     ├─→ Calculate RSI(6) on 4H data
        │     │     └─→ Calculate RSI(6) on 1D data
        │     │
        │     ├─→ [7] Check Alert Conditions
        │     │     │
        │     │     ├─→ Is price near any S/R level?
        │     │     │     ├─ YES → Continue
        │     │     │     └─ NO → Skip to next symbol
        │     │     │
        │     │     ├─→ Is RSI extreme?
        │     │     │     ├─ YES (>90 or <10) → Continue
        │     │     │     └─ NO → Skip to next symbol
        │     │     │
        │     │     └─→ Check duplicate alert
        │     │           ├─ Recent alert exists → Skip
        │     │           └─ No recent alert → Generate Alert
        │     │
        │     ├─→ [8] Generate Alert (if conditions met)
        │     │     │
        │     │     ├─→ Format alert message
        │     │     ├─→ Send desktop notification
        │     │     ├─→ Log to file
        │     │     └─→ Store alert timestamp
        │     │
        │     └─→ [9] Log Results
        │           └─→ Write to crypto_monitor.log
        │
        ├─→ [10] Wait (CHECK_INTERVAL seconds)
        │
        └─→ REPEAT from [3]
```

---

## 🧩 Component Details

### 1. Configuration Manager
```python
Responsibilities:
  • Load environment variables from .env
  • Parse and validate settings
  • Provide configuration to other components

Inputs:
  • .env file

Outputs:
  • Configuration dictionary

Error Handling:
  • Use defaults if values missing
  • Validate data types
  • Log configuration issues
```

### 2. Exchange Interface (CCXT)
```python
Responsibilities:
  • Connect to cryptocurrency exchange
  • Fetch OHLCV data
  • Handle rate limiting
  • Manage API errors

Inputs:
  • Exchange name (e.g., 'binance')
  • Symbol (e.g., 'BTC/USDT')
  • Timeframe (e.g., '1d')
  • Limit (number of candles)

Outputs:
  • OHLCV data array
  • [timestamp, open, high, low, close, volume]

Error Handling:
  • Retry on network errors
  • Log API failures
  • Continue with next symbol on error
```

### 3. Support/Resistance Detector
```python
Algorithm:
  1. Identify local maxima (resistance)
     • Find peaks in 'high' prices
     • Use sliding window (5 candles)
  
  2. Identify local minima (support)
     • Find valleys in 'low' prices
     • Use sliding window (5 candles)
  
  3. Cluster nearby levels
     • Group levels within threshold
     • Calculate average of cluster
     • Determine level type (support/resistance)
  
  4. Check price proximity
     • Calculate distance to each level
     • Return levels within threshold

Inputs:
  • DataFrame with OHLCV data
  • Threshold percentage

Outputs:
  • List of (level_price, level_type) tuples

Parameters:
  • Window size: 5 candles
  • Clustering threshold: SR_THRESHOLD
```

### 4. RSI Calculator
```python
Algorithm:
  1. Calculate price changes
     • Δ = price[i] - price[i-1]
  
  2. Separate gains and losses
     • Gains: positive changes
     • Losses: absolute negative changes
  
  3. Calculate averages
     • Avg Gain = mean(gains over period)
     • Avg Loss = mean(losses over period)
  
  4. Calculate RS and RSI
     • RS = Avg Gain / Avg Loss
     • RSI = 100 - (100 / (1 + RS))
  
  5. Use exponential smoothing
     • For subsequent periods
     • Smooth with previous averages

Inputs:
  • Price array
  • Period (default: 6)

Outputs:
  • RSI value (0-100)

Special Cases:
  • Avg Loss = 0 → RSI = 100
  • Insufficient data → RSI = 50 (neutral)
```

### 5. Alert Manager
```python
Responsibilities:
  • Evaluate alert conditions
  • Prevent duplicate alerts
  • Format alert messages
  • Trigger notifications

Alert Conditions:
  1. Price near S/R level
     AND
  2. RSI extreme (>90 or <10)

Duplicate Prevention:
  • Store alert key: "symbol_level_condition"
  • Store timestamp
  • Check if alert sent within 1 hour
  • Skip if recent alert exists

Inputs:
  • Current price
  • S/R levels
  • RSI values
  • Symbol name

Outputs:
  • Alert notification
  • Log entry
```

### 6. Notification System
```python
Responsibilities:
  • Send desktop notifications
  • Cross-platform support
  • Handle notification failures

Notification Format:
  Title: "{SYMBOL} Trading Alert"
  Message:
    Price: ${current_price}
    Near {LEVEL_TYPE}: ${level_price}
    Condition: {OVERSOLD/OVERBOUGHT}
    RSI(4H): {rsi_4h} | RSI(1D): {rsi_1d}

Platform Support:
  • Windows: Native notifications
  • macOS: Notification Center
  • Linux: libnotify

Error Handling:
  • Log notification failures
  • Continue monitoring on error
```

### 7. Logging System
```python
Responsibilities:
  • Record all activity
  • Multiple output destinations
  • Structured log format

Log Levels:
  • INFO: Normal operations
  • WARNING: Alerts triggered
  • ERROR: Problems encountered

Outputs:
  • Console (stdout)
  • File (crypto_monitor.log)
  • GUI log widget (if using GUI)

Log Format:
  {timestamp} - {level} - {message}
  
Example:
  2026-02-27 10:30:15 - INFO - Checking BTC/USDT...
```

---

## 🔐 Security Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    Security Layers                      │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  [1] No Authentication Required                         │
│      • Uses public API endpoints only                   │
│      • No API keys needed                               │
│      • No personal data collected                       │
│                                                         │
│  [2] Read-Only Operations                               │
│      • Cannot execute trades                            │
│      • Cannot access accounts                           │
│      • Only fetches market data                         │
│                                                         │
│  [3] Local Processing                                   │
│      • All calculations done locally                    │
│      • No data sent to external servers                 │
│      • Configuration stored locally                     │
│                                                         │
│  [4] Error Isolation                                    │
│      • Errors don't crash application                   │
│      • Failed symbols don't affect others               │
│      • Graceful degradation                             │
│                                                         │
│  [5] Rate Limiting                                      │
│      • Respects exchange limits                         │
│      • Configurable check intervals                     │
│      • Prevents API abuse                               │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

---

## 📊 Performance Optimization

### Caching Strategy
```
Currently: No caching (always fresh data)

Future Optimization:
  • Cache S/R levels (update hourly)
  • Cache historical data (update per candle close)
  • Reduce redundant API calls
```

### Parallel Processing
```
Currently: Sequential processing

Future Optimization:
  • Fetch data for all symbols in parallel
  • Calculate indicators concurrently
  • Use asyncio for async operations
```

### Memory Management
```
Current Approach:
  • Load data per check
  • Process and discard
  • Minimal memory footprint

Typical Usage:
  • 50-100MB RAM
  • Grows slightly with more symbols
  • No memory leaks
```

---

## 🧪 Testing Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    Test Layers                          │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  [1] Dependency Tests                                   │
│      • Verify all packages installed                    │
│      • Check versions                                   │
│                                                         │
│  [2] Connection Tests                                   │
│      • Test exchange connectivity                       │
│      • Verify data fetching                             │
│      • Check API responses                              │
│                                                         │
│  [3] Calculation Tests                                  │
│      • Test RSI calculation                             │
│      • Test S/R detection                               │
│      • Verify accuracy with known data                  │
│                                                         │
│  [4] Notification Tests                                 │
│      • Test desktop notifications                       │
│      • Verify cross-platform support                    │
│                                                         │
│  [5] Integration Tests                                  │
│      • End-to-end workflow                              │
│      • Real data processing                             │
│      • Alert generation                                 │
│                                                         │
└─────────────────────────────────────────────────────────┘

Test Script: test_monitor.py
  • Automated testing
  • Clear pass/fail results
  • Diagnostic information
```

---

## 🔄 State Management

### Application State
```python
State Variables:
  • is_running: bool
  • current_symbol: str
  • last_check_time: datetime
  • alert_history: dict

Persistence:
  • Configuration: .env file
  • Logs: crypto_monitor.log
  • State: In-memory only (reset on restart)
```

### Alert State
```python
Alert Tracking:
  Key: "{symbol}_{level_type}_{condition}"
  Value: timestamp
  
Purpose:
  • Prevent duplicate notifications
  • 1-hour cooldown per unique alert
  
Example:
  {
    "BTC/USDT_support_OVERSOLD": 1709035815,
    "ETH/USDT_resistance_OVERBOUGHT": 1709032215
  }
```

---

## 🌐 Network Architecture

```
┌──────────────┐
│ Application  │
└──────┬───────┘
       │
       │ HTTPS
       ▼
┌──────────────┐
│ CCXT Library │
└──────┬───────┘
       │
       │ REST API
       ▼
┌──────────────────────────────────┐
│    Cryptocurrency Exchanges      │
│                                  │
│  • Binance                       │
│  • Coinbase                      │
│  • Kraken                        │
│  • Others...                     │
└──────────────────────────────────┘

Protocol: HTTPS (encrypted)
Authentication: None (public endpoints)
Rate Limiting: Exchange-specific
Typical Limit: 1200 requests/minute
```

---

## 📁 File System Architecture

```
Working Directory
│
├── Configuration
│   ├── .env (user settings)
│   └── .env.example (template)
│
├── Application Code
│   ├── crypto_monitor.py (core)
│   ├── crypto_monitor_gui.py (GUI)
│   └── test_monitor.py (tests)
│
├── Runtime Data
│   └── crypto_monitor.log (logs)
│
├── Documentation
│   ├── README.md
│   ├── QUICKSTART.md
│   ├── HOW_IT_WORKS.md
│   ├── FAQ.md
│   ├── ARCHITECTURE.md
│   └── PROJECT_SUMMARY.md
│
└── Utilities
    ├── setup.bat
    ├── start_gui.bat
    ├── start_monitor.bat
    └── test_setup.bat
```

---

## 🔮 Future Architecture Enhancements

### Planned Improvements

1. **Database Layer**
   ```
   • SQLite for alert history
   • Track alert outcomes
   • Performance analytics
   ```

2. **Web Interface**
   ```
   • Flask/FastAPI backend
   • React frontend
   • Real-time WebSocket updates
   ```

3. **Mobile Support**
   ```
   • Push notifications
   • Mobile-responsive web UI
   • Native mobile apps
   ```

4. **Advanced Analytics**
   ```
   • Backtesting engine
   • Win rate tracking
   • Performance metrics
   ```

5. **Cloud Deployment**
   ```
   • Docker containerization
   • Cloud hosting (AWS/GCP)
   • Scalable architecture
   ```

---

## 📊 Scalability Considerations

### Current Capacity
- **Symbols**: Tested with 10+ symbols
- **Check Frequency**: 5-minute intervals
- **API Calls**: ~150 calls/hour (3 symbols)
- **Memory**: 50-100MB
- **CPU**: <1% average

### Scaling Limits
- **Exchange Rate Limits**: Primary constraint
- **Network Bandwidth**: Minimal impact
- **Processing Power**: Not a bottleneck
- **Memory**: Linear growth with symbols

### Optimization Strategies
1. Batch API requests
2. Cache historical data
3. Parallel processing
4. Async I/O operations
5. Database for persistence

---

This architecture provides a solid foundation for a reliable, maintainable, and extensible cryptocurrency monitoring system.
