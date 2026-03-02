# How the Crypto Monitor Works

## 📊 System Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    CRYPTO MONITOR                           │
│                                                             │
│  1. Fetch Price Data → 2. Analyze → 3. Alert (if needed)   │
└─────────────────────────────────────────────────────────────┘
```

## 🔄 Monitoring Loop

```
START
  │
  ├─→ For each cryptocurrency symbol:
  │     │
  │     ├─→ Fetch Historical Data
  │     │     ├─ 1-Month timeframe (100 candles)
  │     │     ├─ 1-Week timeframe (100 candles)
  │     │     ├─ 1-Day timeframe (100 candles)
  │     │     └─ 4-Hour timeframe (100 candles)
  │     │
  │     ├─→ Calculate Support/Resistance Levels
  │     │     ├─ Find pivot points on 1M chart
  │     │     ├─ Find pivot points on 1W chart
  │     │     └─ Cluster nearby levels
  │     │
  │     ├─→ Calculate RSI Indicators
  │     │     ├─ RSI(6) on 4H timeframe
  │     │     └─ RSI(6) on 1D timeframe
  │     │
  │     ├─→ Check Alert Conditions
  │     │     │
  │     │     ├─ Is price near S/R level? ──NO──┐
  │     │     │         │                        │
  │     │     │        YES                       │
  │     │     │         │                        │
  │     │     ├─ Is RSI extreme? ──NO──────────┐│
  │     │     │         │                       ││
  │     │     │        YES                      ││
  │     │     │         │                       ││
  │     │     └─→ SEND NOTIFICATION             ││
  │     │                                        ││
  │     └─→ Log Results ←──────────────────────┘│
  │                                              │
  ├─→ Wait (CHECK_INTERVAL seconds) ←───────────┘
  │
  └─→ REPEAT
```

## 🎯 Alert Logic

### Condition 1: Near Support/Resistance
```
Current Price: $50,000
Support Level: $49,500
Threshold: 2% (SR_THRESHOLD=0.02)

Calculation:
  Distance = |$50,000 - $49,500| = $500
  Percentage = $500 / $49,500 = 1.01%
  
  1.01% < 2% → ✅ NEAR SUPPORT
```

### Condition 2: Extreme RSI
```
RSI(4H) = 92.5
RSI(1D) = 88.3

Thresholds:
  RSI_OVERBOUGHT = 90
  RSI_OVERSOLD = 10

Check:
  92.5 > 90 → ✅ OVERSOLD (4H)
  OR
  88.3 > 90 → ❌ Not oversold (1D)
  
  Result: ✅ OVERSOLD condition met
```

### Combined Alert
```
✅ Near Support/Resistance
AND
✅ Extreme RSI

→ 🔔 SEND NOTIFICATION!
```

## 📈 Support/Resistance Detection

### Step 1: Find Pivot Points
```
Price Chart:
     *
    * *
   *   *     ← Local Maximum (Resistance)
  *     *
 *       *
*         *   ← Local Minimum (Support)
```

### Step 2: Cluster Nearby Levels
```
Raw Levels:
$50,100 (resistance)
$50,150 (resistance)
$50,080 (resistance)
$49,900 (support)
$49,850 (support)

After Clustering (2% threshold):
$50,110 (resistance) ← Average of nearby levels
$49,875 (support)    ← Average of nearby levels
```

### Step 3: Check Current Price
```
Current Price: $50,000

Distance to $50,110 resistance: 0.22% ✅ NEAR
Distance to $49,875 support: 0.25% ✅ NEAR
```

## 📊 RSI Calculation

### What is RSI?
RSI (Relative Strength Index) measures momentum from 0-100:
- **0-10**: Extremely overbought (price may drop)
- **10-30**: Overbought
- **30-70**: Normal range
- **70-90**: Oversold
- **90-100**: Extremely oversold (price may bounce)

### RSI Formula
```
1. Calculate price changes:
   Gains = positive changes
   Losses = negative changes (absolute)

2. Average gains and losses over period (6 candles):
   Avg Gain = sum(gains) / 6
   Avg Loss = sum(losses) / 6

3. Calculate Relative Strength:
   RS = Avg Gain / Avg Loss

4. Calculate RSI:
   RSI = 100 - (100 / (1 + RS))
```

### Example
```
Last 6 price changes: [+100, -50, +200, +150, -30, +80]

Gains: [100, 0, 200, 150, 0, 80] → Avg = 88.33
Losses: [0, 50, 0, 0, 30, 0] → Avg = 13.33

RS = 88.33 / 13.33 = 6.625
RSI = 100 - (100 / (1 + 6.625)) = 86.88

Result: RSI = 86.88 (Oversold, but not extreme)
```

## 🔔 Notification System

### Alert Deduplication
```
Alert Generated:
  Symbol: BTC/USDT
  Level: Support at $50,000
  Condition: Oversold
  
Store Alert Key: "BTC/USDT_support_OVERSOLD"
Store Timestamp: 10:00 AM

Next Check (10:05 AM):
  Same conditions met
  Check last alert: 5 minutes ago
  5 minutes < 60 minutes → ❌ Skip (too recent)

Next Check (11:05 AM):
  Same conditions met
  Check last alert: 65 minutes ago
  65 minutes > 60 minutes → ✅ Send new alert
```

## ⚙️ Configuration Impact

### CHECK_INTERVAL
```
300 seconds (5 min):  12 checks/hour  ← Recommended
600 seconds (10 min): 6 checks/hour   ← Safer for rate limits
60 seconds (1 min):   60 checks/hour  ← May hit limits
```

### SR_THRESHOLD
```
0.01 (1%): Stricter  → Fewer alerts, more precise
0.02 (2%): Balanced  → Recommended
0.03 (3%): Looser    → More alerts, less precise

Example at price $50,000:
  1% = $500 range  ($49,750 - $50,250)
  2% = $1,000 range ($49,500 - $50,500)
  3% = $1,500 range ($49,250 - $50,750)
```

### RSI Thresholds
```
More Sensitive (more alerts):
  RSI_OVERBOUGHT=80
  RSI_OVERSOLD=20

Default (balanced):
  RSI_OVERBOUGHT=90
  RSI_OVERSOLD=10

Less Sensitive (fewer alerts):
  RSI_OVERBOUGHT=95
  RSI_OVERSOLD=5
```

## 🎓 Trading Interpretation

### Scenario 1: Support + Oversold
```
Price: Near support level
RSI: > 90 (oversold)

Interpretation:
  → Price at strong support
  → Momentum extremely weak
  → Potential bounce opportunity
  
Action to Consider:
  ✓ Check chart for confirmation
  ✓ Look for bullish patterns
  ✓ Consider entry for long position
```

### Scenario 2: Resistance + Overbought
```
Price: Near resistance level
RSI: < 10 (overbought)

Interpretation:
  → Price at strong resistance
  → Momentum extremely strong
  → Potential reversal/pullback
  
Action to Consider:
  ✓ Check chart for confirmation
  ✓ Look for bearish patterns
  ✓ Consider exit or short position
```

## 🔍 Data Sources

### Exchange Data (via CCXT)
```
Binance API
  │
  ├─→ OHLCV Data (Open, High, Low, Close, Volume)
  │     ├─ 1-Month candles
  │     ├─ 1-Week candles
  │     ├─ 1-Day candles
  │     └─ 4-Hour candles
  │
  └─→ Real-time price updates
```

### Rate Limits
```
Most exchanges: 1200 requests/minute
Our app usage: ~4 requests per symbol per check

Example:
  3 symbols × 4 requests = 12 requests per check
  Check every 5 minutes = 12 requests/5min
  = 144 requests/hour (well within limits)
```

## 🛡️ Error Handling

```
Try to fetch data
  │
  ├─ Success → Continue
  │
  └─ Failure
       │
       ├─ Log error
       ├─ Skip this symbol
       └─ Continue with next symbol

Try to send notification
  │
  ├─ Success → Log alert
  │
  └─ Failure
       │
       ├─ Log error
       └─ Continue monitoring
```

## 📝 Logging

### Log Levels
```
INFO:    Normal operations
WARNING: Alerts triggered
ERROR:   Problems encountered
```

### Log Outputs
```
1. Console (real-time)
2. crypto_monitor.log (persistent)
3. GUI log window (if using GUI)
```

### Example Log Entry
```
2026-02-27 10:30:15 - INFO - Checking BTC/USDT...
2026-02-27 10:30:17 - INFO - BTC/USDT - Price: $50,234.56, RSI(4H): 92.34, RSI(1D): 88.21
2026-02-27 10:30:17 - WARNING - ALERT: BTC/USDT Alert!
Price: $50,234.56
Near SUPPORT: $50,000.00
Condition: OVERSOLD
RSI(4H): 92.34 | RSI(1D): 88.21
```

---

## 🎯 Summary

The Crypto Monitor continuously:
1. **Fetches** price data from exchanges
2. **Analyzes** support/resistance and RSI
3. **Alerts** you when conditions align
4. **Logs** all activity for review

It's designed to catch high-probability setups where:
- Price is at a key level (support/resistance)
- Momentum is extreme (oversold/overbought)
- These conditions historically lead to reversals

Remember: This is a tool for **alerts**, not **advice**. Always do your own analysis before trading!
