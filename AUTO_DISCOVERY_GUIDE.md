# 🤖 Auto-Discovery Mode Guide

## 🌟 What is Auto-Discovery?

Instead of manually specifying which cryptocurrencies to monitor, **Auto-Discovery Mode** automatically:

✅ **Discovers ALL cryptocurrencies** available on the exchange  
✅ **Filters by trading volume** (only liquid, actively traded coins)  
✅ **Monitors new listings** automatically (refreshes every 24 hours)  
✅ **Removes delisted coins** automatically  
✅ **Prioritizes by volume** (monitors most active coins first)  

---

## 🚀 Quick Start

### Option 1: GUI (Recommended)
Double-click **`start_auto_gui.bat`**

### Option 2: Console
Double-click **`start_auto_monitor.bat`**

Or manually:
```bash
python crypto_monitor_auto_gui.py  # GUI
python crypto_monitor_auto.py      # Console
```

---

## ⚙️ Configuration

Edit `.env` file with these settings:

```env
# Exchange to use
EXCHANGE=binance

# Quote currencies to monitor (finds all coins paired with these)
QUOTE_CURRENCIES=USDT,USD,BTC,ETH

# Minimum 24-hour volume (filters out low-volume coins)
MIN_VOLUME_24H=1000000

# Maximum symbols to monitor (prevents overload)
MAX_SYMBOLS=100

# Check interval in seconds
CHECK_INTERVAL=300

# How often to refresh symbol list (in hours)
REFRESH_SYMBOLS_HOURS=24

# RSI thresholds
RSI_OVERBOUGHT=90
RSI_OVERSOLD=10

# Support/Resistance sensitivity
SR_THRESHOLD=0.02
```

---

## 🎯 How It Works

### 1. Symbol Discovery Process

```
START
  │
  ├─→ Connect to Exchange
  │
  ├─→ Fetch ALL available markets
  │     │
  │     └─→ Example: Binance has 2000+ trading pairs
  │
  ├─→ Filter by Quote Currency
  │     │
  │     ├─ USDT pairs: BTC/USDT, ETH/USDT, SOL/USDT, etc.
  │     ├─ USD pairs: BTC/USD, ETH/USD, etc.
  │     ├─ BTC pairs: ETH/BTC, SOL/BTC, etc.
  │     └─ ETH pairs: SOL/ETH, MATIC/ETH, etc.
  │
  ├─→ Fetch 24h Volume Data
  │     │
  │     └─→ Get real-time trading volume for each pair
  │
  ├─→ Apply Filters
  │     │
  │     ├─ Volume > MIN_VOLUME_24H ($1M default)
  │     ├─ Price > MIN_PRICE (avoid dust coins)
  │     └─ Market is active (not delisted)
  │
  ├─→ Sort by Volume (highest first)
  │
  ├─→ Limit to MAX_SYMBOLS (top 100 by default)
  │
  └─→ Save to Cache (active_symbols.json)
```

### 2. Monitoring Process

```
Every CHECK_INTERVAL seconds:
  │
  ├─→ Check if symbol list needs refresh (every 24h)
  │     │
  │     └─→ If yes: Re-discover symbols
  │
  ├─→ For each discovered symbol:
  │     │
  │     ├─→ Fetch price data (1M, 1W, 1D, 4H)
  │     ├─→ Calculate S/R levels
  │     ├─→ Calculate RSI
  │     ├─→ Check alert conditions
  │     └─→ Send notification if conditions met
  │
  └─→ Wait and repeat
```

### 3. Real-Time Updates

- **New Listings**: Automatically added on next refresh (every 24h)
- **Delistings**: Automatically removed on next refresh
- **Volume Changes**: Symbols that drop below volume threshold are removed
- **Cache**: Symbols saved to `active_symbols.json` for quick restart

---

## 📊 Configuration Examples

### Conservative Setup (Fewer, Higher Quality)
```env
QUOTE_CURRENCIES=USDT,USD
MIN_VOLUME_24H=5000000      # $5M minimum
MAX_SYMBOLS=50              # Top 50 only
CHECK_INTERVAL=600          # Check every 10 minutes
```
**Result:** ~50 major cryptocurrencies, lower API usage

### Balanced Setup (Recommended)
```env
QUOTE_CURRENCIES=USDT,USD,BTC,ETH
MIN_VOLUME_24H=1000000      # $1M minimum
MAX_SYMBOLS=100             # Top 100
CHECK_INTERVAL=300          # Check every 5 minutes
```
**Result:** ~100 active cryptocurrencies, moderate API usage

### Aggressive Setup (Maximum Coverage)
```env
QUOTE_CURRENCIES=USDT,USD,BTC,ETH,BUSD,USDC
MIN_VOLUME_24H=500000       # $500k minimum
MAX_SYMBOLS=200             # Top 200
CHECK_INTERVAL=900          # Check every 15 minutes
```
**Result:** ~200 cryptocurrencies, higher API usage

### Altcoin Focus
```env
QUOTE_CURRENCIES=BTC,ETH    # Only altcoin pairs
MIN_VOLUME_24H=100000       # $100k minimum (smaller altcoins)
MAX_SYMBOLS=100
CHECK_INTERVAL=300
```
**Result:** Focus on altcoins paired with BTC/ETH

---

## 🎯 Advantages of Auto-Discovery

### ✅ Never Miss New Coins
- New listings automatically detected
- No manual updates needed
- Catch early opportunities

### ✅ Always Up-to-Date
- Delisted coins removed automatically
- Volume filters keep list relevant
- Adapts to market changes

### ✅ Comprehensive Coverage
- Monitor entire market
- Don't miss opportunities in lesser-known coins
- Discover hidden gems

### ✅ Zero Maintenance
- Set it and forget it
- Automatic symbol management
- No manual list updates

### ✅ Volume-Based Prioritization
- Focus on liquid, tradable coins
- Avoid low-volume scams
- Monitor what matters

---

## ⚠️ Important Considerations

### Rate Limits
**More symbols = more API calls**

Calculate your API usage:
```
Symbols × 4 calls per check = Total calls per cycle

Examples:
  50 symbols × 4 = 200 calls per cycle
  100 symbols × 4 = 400 calls per cycle
  200 symbols × 4 = 800 calls per cycle

With 5-minute intervals:
  200 calls × 12 cycles/hour = 2,400 calls/hour
```

**Binance limit:** ~1,200 requests/minute = 72,000/hour  
**Your usage:** Well within limits even with 200 symbols

**Recommendation:** Start with 100 symbols, adjust based on performance

### Performance Impact

| Symbols | Check Time | Recommended Interval |
|---------|------------|---------------------|
| 50 | ~3-4 minutes | 5 minutes |
| 100 | ~6-8 minutes | 10 minutes |
| 200 | ~12-15 minutes | 15 minutes |

### Alert Frequency
**More symbols = more alerts**

With 100 symbols:
- Expect 5-20 alerts per day (depending on market conditions)
- Volatile markets = more alerts
- Sideways markets = fewer alerts

---

## 🔍 Symbol Cache System

### Cache File: `active_symbols.json`

```json
{
  "timestamp": 1709035815,
  "exchange": "binance",
  "symbols": [
    {
      "symbol": "BTC/USDT",
      "volume": 28500000000,
      "price": 52345.67,
      "quote": "USDT"
    },
    {
      "symbol": "ETH/USDT",
      "volume": 15200000000,
      "price": 3234.56,
      "quote": "USDT"
    }
    // ... more symbols
  ]
}
```

### Cache Benefits
- **Fast Startup**: No need to re-discover on every restart
- **Offline Reference**: See what's being monitored
- **Historical Record**: Track symbol changes over time
- **Fallback**: Used if discovery fails

### Cache Refresh
- Automatically refreshed every 24 hours (configurable)
- Manual refresh: Click "Discover Symbols Now" in GUI
- Or delete `active_symbols.json` to force re-discovery

---

## 📈 Real-World Examples

### Example 1: Binance USDT Pairs
```env
EXCHANGE=binance
QUOTE_CURRENCIES=USDT
MIN_VOLUME_24H=1000000
MAX_SYMBOLS=100
```

**Discovers:**
- BTC/USDT, ETH/USDT, BNB/USDT
- SOL/USDT, ADA/USDT, XRP/USDT
- DOGE/USDT, MATIC/USDT, DOT/USDT
- Plus 90+ more active USDT pairs

### Example 2: Multi-Quote Coverage
```env
EXCHANGE=binance
QUOTE_CURRENCIES=USDT,BTC,ETH
MIN_VOLUME_24H=500000
MAX_SYMBOLS=150
```

**Discovers:**
- All major USDT pairs
- Popular BTC pairs (altcoins vs Bitcoin)
- Popular ETH pairs (altcoins vs Ethereum)
- Comprehensive market coverage

### Example 3: Coinbase USD Focus
```env
EXCHANGE=coinbase
QUOTE_CURRENCIES=USD
MIN_VOLUME_24H=2000000
MAX_SYMBOLS=50
```

**Discovers:**
- BTC/USD, ETH/USD, SOL/USD
- Major coins available on Coinbase
- USD-focused (good for US traders)

---

## 🆚 Manual vs Auto-Discovery

### Manual Mode (Original)
```env
CRYPTO_SYMBOLS=BTC/USDT,ETH/USDT,SOL/USDT
```

**Pros:**
- ✅ Precise control
- ✅ Lower API usage
- ✅ Faster checks
- ✅ Focus on specific coins

**Cons:**
- ❌ Manual updates needed
- ❌ Miss new listings
- ❌ Limited coverage

**Best For:**
- Traders focused on specific coins
- Lower-powered systems
- Strict rate limit concerns

### Auto-Discovery Mode (New)
```env
QUOTE_CURRENCIES=USDT,USD,BTC,ETH
MIN_VOLUME_24H=1000000
MAX_SYMBOLS=100
```

**Pros:**
- ✅ Automatic updates
- ✅ Comprehensive coverage
- ✅ Catches new listings
- ✅ Zero maintenance

**Cons:**
- ❌ Higher API usage
- ❌ Longer check cycles
- ❌ More alerts

**Best For:**
- Traders wanting full market coverage
- Opportunity seekers
- Set-and-forget operation

---

## 🎮 Using the Auto-Discovery GUI

### Main Features

1. **Auto-Discovery Configuration**
   - Set quote currencies (USDT, USD, BTC, ETH)
   - Set minimum volume filter
   - Set maximum symbols to monitor
   - Save configuration with one click

2. **Control Panel**
   - **Start Auto-Discovery**: Begin monitoring all discovered symbols
   - **Stop Monitoring**: Stop the monitor
   - **Discover Symbols Now**: Manually trigger symbol discovery

3. **Statistics Display**
   - Shows number of symbols being monitored
   - Shows total alerts sent
   - Updates in real-time

4. **Discovered Symbols List**
   - Shows top 20 discovered symbols
   - Sorted by trading volume
   - Updates after each discovery

5. **Activity Log**
   - Real-time log of all activity
   - Shows discoveries, checks, and alerts
   - Scrollable history

---

## 💡 Pro Tips

### 1. Start Conservative
```env
MAX_SYMBOLS=50
CHECK_INTERVAL=600  # 10 minutes
```
Monitor performance, then increase if desired.

### 2. Focus on Liquid Markets
```env
MIN_VOLUME_24H=5000000  # $5M
```
Higher volume = better liquidity = more reliable signals

### 3. Use Multiple Quote Currencies
```env
QUOTE_CURRENCIES=USDT,BTC,ETH
```
Different pairs show different opportunities

### 4. Monitor the Logs
- Check `crypto_monitor.log` regularly
- Look for errors or rate limit warnings
- Adjust settings based on performance

### 5. Adjust for Your System
- Slower computer? Reduce MAX_SYMBOLS
- Fast internet? Increase MAX_SYMBOLS
- Rate limit errors? Increase CHECK_INTERVAL

---

## 🔄 Symbol Refresh Strategy

### When Symbols Are Refreshed

1. **On Startup**: Always discovers symbols when app starts
2. **Scheduled**: Every REFRESH_SYMBOLS_HOURS (default: 24h)
3. **Manual**: Click "Discover Symbols Now" in GUI
4. **Fallback**: Loads from cache if discovery fails

### What Gets Updated

- ✅ New coin listings added
- ✅ Delisted coins removed
- ✅ Volume rankings updated
- ✅ Active status verified

### Refresh Frequency Recommendations

| Market Conditions | Refresh Interval |
|-------------------|------------------|
| Bull market (many new listings) | 6-12 hours |
| Normal market | 24 hours (default) |
| Bear market (fewer listings) | 48-72 hours |

---

## 📊 Expected Coverage

### Binance (USDT pairs, $1M+ volume)
- **~150-200 symbols** typically discovered
- Includes all major coins
- Many altcoins and DeFi tokens
- New listings added automatically

### Coinbase (USD pairs, $1M+ volume)
- **~50-80 symbols** typically discovered
- Major cryptocurrencies
- US-compliant coins only
- More conservative listing policy

### Kraken (USD/USDT pairs, $1M+ volume)
- **~80-120 symbols** typically discovered
- Major coins and popular altcoins
- European-friendly
- Good EUR pair support

---

## 🎯 Use Cases

### 1. Market-Wide Opportunity Scanner
```env
QUOTE_CURRENCIES=USDT
MIN_VOLUME_24H=1000000
MAX_SYMBOLS=200
```
**Goal:** Scan entire market for opportunities

### 2. Major Coins Only
```env
QUOTE_CURRENCIES=USDT,USD
MIN_VOLUME_24H=10000000  # $10M
MAX_SYMBOLS=30
```
**Goal:** Focus on top-tier cryptocurrencies

### 3. Altcoin Hunter
```env
QUOTE_CURRENCIES=BTC,ETH
MIN_VOLUME_24H=500000
MAX_SYMBOLS=100
```
**Goal:** Find altcoin opportunities vs BTC/ETH

### 4. New Listing Catcher
```env
QUOTE_CURRENCIES=USDT
MIN_VOLUME_24H=100000   # Lower threshold
MAX_SYMBOLS=200
REFRESH_SYMBOLS_HOURS=6  # Refresh every 6 hours
```
**Goal:** Catch new listings quickly

---

## 🔧 Troubleshooting

### "Too many symbols, checks taking too long"
**Solution:**
```env
MAX_SYMBOLS=50          # Reduce
CHECK_INTERVAL=900      # Increase to 15 min
```

### "Not discovering any symbols"
**Solution:**
```env
MIN_VOLUME_24H=100000   # Lower threshold
QUOTE_CURRENCIES=USDT,USD,BTC,ETH,BUSD  # Add more quotes
```

### "Rate limit errors"
**Solution:**
```env
MAX_SYMBOLS=50          # Reduce symbols
CHECK_INTERVAL=600      # Increase interval
```

### "Missing new listings"
**Solution:**
```env
REFRESH_SYMBOLS_HOURS=6  # Refresh more frequently
```

### "Too many low-quality coins"
**Solution:**
```env
MIN_VOLUME_24H=5000000   # Increase to $5M
MIN_PRICE=0.01           # Filter sub-penny coins
```

---

## 📁 Files Created

### `active_symbols.json`
- Contains all discovered symbols
- Updated every refresh cycle
- Includes volume and price data
- Used as fallback cache

**Example:**
```json
{
  "timestamp": 1709035815,
  "exchange": "binance",
  "symbols": [
    {"symbol": "BTC/USDT", "volume": 28500000000, "price": 52345.67},
    {"symbol": "ETH/USDT", "volume": 15200000000, "price": 3234.56}
  ]
}
```

---

## 🎓 Understanding the Filters

### Quote Currency Filter
```
All Markets: BTC/USDT, BTC/USD, BTC/BTC, ETH/USDT, ETH/BTC, DOGE/USDT...

QUOTE_CURRENCIES=USDT
  → BTC/USDT ✅
  → ETH/USDT ✅
  → BTC/USD ❌
  → ETH/BTC ❌

QUOTE_CURRENCIES=USDT,BTC
  → BTC/USDT ✅
  → ETH/USDT ✅
  → ETH/BTC ✅
  → BTC/USD ❌
```

### Volume Filter
```
Symbol: SHIB/USDT
24h Volume: $850,000

MIN_VOLUME_24H=1000000
  → $850,000 < $1,000,000 ❌ Filtered out

MIN_VOLUME_24H=500000
  → $850,000 > $500,000 ✅ Included
```

### Max Symbols Limit
```
Discovered: 250 symbols (sorted by volume)

MAX_SYMBOLS=100
  → Takes top 100 by volume
  → Ignores bottom 150

Result: Monitors highest volume coins only
```

---

## 🚀 Performance Optimization

### Optimal Settings for Different Scenarios

#### Scenario 1: Home Computer, Casual Monitoring
```env
MAX_SYMBOLS=50
CHECK_INTERVAL=600      # 10 minutes
MIN_VOLUME_24H=2000000
```

#### Scenario 2: Dedicated Server, Serious Trading
```env
MAX_SYMBOLS=200
CHECK_INTERVAL=300      # 5 minutes
MIN_VOLUME_24H=500000
```

#### Scenario 3: Low-Power Device (Raspberry Pi)
```env
MAX_SYMBOLS=30
CHECK_INTERVAL=900      # 15 minutes
MIN_VOLUME_24H=5000000
```

---

## 📊 Expected Results

### Discovery Phase (First Run)
```
[10:00:00] Starting Auto Crypto Monitor...
[10:00:01] Discovering available cryptocurrencies...
[10:00:05] Fetching market data for volume filtering...
[10:00:15] Discovered 156 cryptocurrencies to monitor
[10:00:15] Top 10: BTC/USDT, ETH/USDT, BNB/USDT, SOL/USDT...
[10:00:15] Saved 156 symbols to cache
[10:00:15] === Cycle 1: Checking 100 symbols ===
```

### Monitoring Phase
```
[10:00:16] Checking BTC/USDT...
[10:00:18] Checking ETH/USDT...
[10:00:20] Progress: 10/100 symbols checked
...
[10:08:45] Progress: 100/100 symbols checked
[10:08:45] Cycle 1 complete. Waiting 300 seconds...
```

### Alert Phase
```
[10:15:30] ALERT: SOL/USDT Alert!
Price: $145.67
Near SUPPORT: $144.00
Condition: OVERSOLD
RSI(4H): 92.34 | RSI(1D): 88.21
```

---

## 🎯 Comparison Table

| Feature | Manual Mode | Auto-Discovery Mode |
|---------|-------------|---------------------|
| Symbol Selection | Manual list | Automatic |
| New Listings | Manual update | Automatic |
| Coverage | Limited | Comprehensive |
| Maintenance | Regular updates needed | Zero maintenance |
| API Calls | Lower | Higher |
| Check Speed | Faster | Slower (more symbols) |
| Best For | Specific coins | Full market scan |

---

## 🌟 Best Practices

### 1. Start with Discovery Test
```bash
python crypto_monitor_auto.py
```
Let it run for one cycle, check the log, verify symbols discovered.

### 2. Monitor the First Hour
- Watch for rate limit errors
- Check alert frequency
- Verify symbol quality
- Adjust settings if needed

### 3. Review Weekly
- Check `active_symbols.json`
- Review alert history in logs
- Adjust volume/symbol limits
- Fine-tune thresholds

### 4. Combine with Manual
- Use auto-discovery for scanning
- Use manual mode for focused trading
- Run both simultaneously (different configs)

---

## 🎉 Summary

Auto-Discovery Mode transforms the Crypto Monitor into a **comprehensive market scanner** that:

✅ Monitors **ALL** cryptocurrencies automatically  
✅ Adapts to **new listings** in real-time  
✅ Filters by **volume and liquidity**  
✅ Requires **zero manual maintenance**  
✅ Provides **complete market coverage**  

Perfect for traders who want to:
- Never miss opportunities
- Monitor the entire market
- Catch new coin listings early
- Reduce manual work

---

**Ready to monitor everything?** → Run `start_auto_gui.bat`

---

*Last Updated: February 27, 2026*
