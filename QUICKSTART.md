# Quick Start Guide

## 🚀 Get Started in 3 Steps

### Step 1: Install
Double-click `setup.bat` to install all dependencies.

### Step 2: Choose Your Mode

#### 🤖 Auto-Discovery Mode (Recommended - NEW!)
**Monitors ALL cryptocurrencies automatically!**

Edit `.env` file:
```env
QUOTE_CURRENCIES=USDT,USD,BTC,ETH
MIN_VOLUME_24H=1000000
MAX_SYMBOLS=100
```

Then run: `start_auto_gui.bat`

#### 📝 Manual Mode (Original)
**Specify exact cryptocurrencies:**

Edit `.env` file:
```env
CRYPTO_SYMBOLS=BTC/USDT,ETH/USDT,SOL/USDT
```

Then run: `start_gui.bat`

### Step 3: Get Alerts!
The monitor will notify you when opportunities arise.

---

## 🆚 Auto-Discovery vs Manual Mode

### 🤖 Auto-Discovery Mode (NEW!)
**Best for:** Comprehensive market scanning, catching new opportunities

✅ Monitors ALL cryptocurrencies on the exchange  
✅ Automatically discovers new listings  
✅ Filters by volume (only liquid coins)  
✅ Zero manual maintenance  
✅ Adapts to market changes  

**Files:** `start_auto_gui.bat` or `start_auto_monitor.bat`  
**Guide:** See [AUTO_DISCOVERY_GUIDE.md](AUTO_DISCOVERY_GUIDE.md)

### 📝 Manual Mode (Original)
**Best for:** Focused trading on specific coins

✅ Monitor exact cryptocurrencies you choose  
✅ Lower API usage  
✅ Faster check cycles  
✅ Precise control  

**Files:** `start_gui.bat` or `start_monitor.bat`

---

## 📊 What This App Does

The Crypto Monitor watches your selected cryptocurrencies and sends you a **desktop notification** when:

1. ✅ Price is near a **support or resistance level** (calculated from 1-week and 1-month charts)
2. ✅ **AND** the market is in an extreme condition:
   - **Oversold**: RSI6 > 90 (potential buying opportunity)
   - **Overbought**: RSI6 < 10 (potential selling opportunity)

---

## 🎯 Example Alert

```
🔔 BTC/USDT Alert!
Price: $52,345.67
Near SUPPORT: $52,000.00
Condition: OVERSOLD
RSI(4H): 92.34 | RSI(1D): 88.21
```

This means:
- Bitcoin is trading near a support level at $52,000
- The RSI indicates it's oversold (potential bounce opportunity)
- You might want to check the chart for a potential entry

---

## ⚙️ Configuration Tips

### Symbols
Add any trading pair available on your exchange:
```
CRYPTO_SYMBOLS=BTC/USDT,ETH/USDT,SOL/USDT,DOGE/USDT,ADA/USDT
```

### Check Interval
How often to check prices (in seconds):
```
CHECK_INTERVAL=300    # Check every 5 minutes
CHECK_INTERVAL=600    # Check every 10 minutes
CHECK_INTERVAL=60     # Check every 1 minute (may hit rate limits)
```

### RSI Thresholds
Adjust sensitivity for extreme conditions:
```
RSI_OVERBOUGHT=90     # Default: very extreme
RSI_OVERBOUGHT=80     # More sensitive (more alerts)

RSI_OVERSOLD=10       # Default: very extreme
RSI_OVERSOLD=20       # More sensitive (more alerts)
```

### Support/Resistance Sensitivity
How close price must be to a level:
```
SR_THRESHOLD=0.02     # 2% (default)
SR_THRESHOLD=0.01     # 1% (stricter - fewer alerts)
SR_THRESHOLD=0.03     # 3% (looser - more alerts)
```

---

## 🖥️ GUI vs Console

### GUI Version (`start_gui.bat`)
- ✅ Easy configuration without editing files
- ✅ Real-time activity log
- ✅ Start/Stop buttons
- ✅ Best for Windows users

### Console Version (`start_monitor.bat`)
- ✅ Lightweight
- ✅ Can run in background
- ✅ Better for servers/automation
- ✅ All output saved to `crypto_monitor.log`

---

## 🔧 Troubleshooting

### No notifications appearing?
- Check Windows notification settings
- Make sure "Focus Assist" is not blocking notifications
- Run `test_setup.bat` to verify notifications work

### Rate limit errors?
- Increase `CHECK_INTERVAL` to 600 or higher
- Reduce the number of symbols being monitored

### Connection errors?
- Check your internet connection
- Try a different exchange (e.g., `EXCHANGE=coinbase`)
- Some exchanges may require API keys for data access

### Installation errors?
- Make sure Python is installed and in PATH
- Try running as Administrator
- Install Visual C++ Redistributable if on Windows

---

## 📈 Understanding the Alerts

### Support Levels
- Price levels where buying pressure historically increases
- When price approaches support + oversold RSI = potential buy opportunity

### Resistance Levels
- Price levels where selling pressure historically increases
- When price approaches resistance + overbought RSI = potential sell opportunity

### RSI (Relative Strength Index)
- Measures momentum on a scale of 0-100
- **RSI > 90**: Extremely oversold (price may bounce up)
- **RSI < 10**: Extremely overbought (price may pull back)
- We use RSI6 (6-period) for faster signals

### Timeframes
- **1W & 1M**: Used to find major support/resistance levels
- **4H & 1D**: Used to check RSI conditions
- This combination finds major levels with short-term extreme conditions

---

## 🎓 Trading Tips

⚠️ **Important**: This tool provides alerts, not trading advice!

- Always do your own research
- Use alerts as a starting point for analysis
- Check the actual chart before making decisions
- Consider other factors (news, volume, market conditions)
- Never invest more than you can afford to lose

---

## 🆘 Need Help?

1. Run `test_setup.bat` to diagnose issues
2. Check `crypto_monitor.log` for detailed error messages
3. Read the full `README.md` for advanced configuration

---

## 📝 Quick Reference

| File | Purpose |
|------|---------|
| `setup.bat` | Install dependencies |
| `test_setup.bat` | Test your installation |
| `start_gui.bat` | Launch GUI version |
| `start_monitor.bat` | Launch console version |
| `.env` | Configuration file |
| `crypto_monitor.log` | Activity log |

---

Happy monitoring! 🚀📊
