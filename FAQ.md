# Frequently Asked Questions (FAQ)

## General Questions

### Q: What does this app do?
**A:** The Crypto Monitor watches cryptocurrency prices and sends desktop notifications when:
1. Price is near a support or resistance level (from weekly/monthly charts)
2. AND the RSI indicator shows extreme conditions (oversold >90 or overbought <10)

These conditions often indicate potential trading opportunities.

### Q: Is this a trading bot?
**A:** No! This is an **alert system only**. It notifies you of potential opportunities but does not execute trades. You maintain full control over all trading decisions.

### Q: Do I need to pay for this?
**A:** No, the app is completely free. You only need a computer with Python installed.

### Q: Do I need an exchange account?
**A:** No, the app only reads public market data. You don't need an account or API keys.

---

## Setup & Installation

### Q: What operating system does this work on?
**A:** The app works on:
- ✅ Windows (with convenient .bat scripts)
- ✅ macOS (manual Python commands)
- ✅ Linux (manual Python commands)

### Q: I get "Python not found" error
**A:** 
1. Install Python from [python.org](https://www.python.org/downloads/)
2. During installation, check "Add Python to PATH"
3. Restart your computer
4. Run `setup.bat` again

### Q: Installation fails with "error: Microsoft Visual C++ required"
**A:** On Windows, install the [Visual C++ Redistributable](https://aka.ms/vs/17/release/vc_redist.x64.exe)

### Q: Can I run this on a Raspberry Pi?
**A:** Yes! Follow the manual setup instructions in README.md. Note that desktop notifications may not work on headless systems.

---

## Configuration

### Q: What cryptocurrencies can I monitor?
**A:** Any trading pair available on your chosen exchange. Popular examples:
- BTC/USDT, ETH/USDT, SOL/USDT
- BTC/USD, ETH/USD (on Coinbase)
- Any altcoin with sufficient trading volume

### Q: How many cryptocurrencies can I monitor at once?
**A:** Technically unlimited, but consider:
- Each symbol requires 4 API calls per check
- More symbols = longer check time
- Recommended: 3-10 symbols to start

### Q: Which exchange should I use?
**A:** 
- **Binance** (default): Largest volume, most pairs
- **Coinbase**: Good for US users
- **Kraken**: Reliable, good for EUR pairs
- See [CCXT supported exchanges](https://github.com/ccxt/ccxt) for full list

### Q: How often should I check prices?
**A:** 
- **5 minutes** (300s): Recommended balance
- **10 minutes** (600s): Safer for rate limits
- **1 minute** (60s): Only if monitoring 1-2 symbols

### Q: What's the difference between oversold and overbought?
**A:** 
- **Oversold (RSI > 90)**: Price has dropped too much, may bounce up
- **Overbought (RSI < 10)**: Price has risen too much, may pull back

Note: Our thresholds are reversed from traditional RSI because we're looking for extreme conditions!

---

## Usage

### Q: I'm not getting any alerts
**A:** This is normal! Alerts only trigger when specific conditions align:
1. Price must be near a support/resistance level
2. RSI must be in extreme territory (>90 or <10)

These conditions are rare by design. Try:
- Adjusting `SR_THRESHOLD` to 0.03 (3%)
- Adjusting `RSI_OVERBOUGHT` to 80
- Adjusting `RSI_OVERSOLD` to 20
- Monitoring more symbols

### Q: I'm getting too many alerts
**A:** Make the conditions stricter:
- Decrease `SR_THRESHOLD` to 0.01 (1%)
- Keep `RSI_OVERBOUGHT` at 90 or increase to 95
- Keep `RSI_OVERSOLD` at 10 or decrease to 5
- Monitor fewer symbols

### Q: How do I know if the app is working?
**A:** 
1. Check the log window (GUI) or `crypto_monitor.log` file
2. You should see regular "Checking [SYMBOL]..." messages
3. Run `test_setup.bat` to verify all components

### Q: Can I run this 24/7?
**A:** Yes! The app is designed for continuous operation. On Windows:
1. Use Task Scheduler to start at boot
2. Or just leave it running in the background

### Q: Does this use a lot of internet data?
**A:** No, very minimal:
- Each check: ~50KB per symbol
- 3 symbols every 5 minutes: ~2MB per hour
- 24/7 operation: ~50MB per day

### Q: Will this slow down my computer?
**A:** No, the app uses minimal resources:
- CPU: <1% when checking
- RAM: ~50-100MB
- Disk: Only log files grow (a few MB per day)

---

## Notifications

### Q: I don't see desktop notifications
**A:** 
**Windows:**
1. Check Settings → System → Notifications
2. Ensure notifications are enabled
3. Turn off "Focus Assist" or add Crypto Monitor to priority list

**macOS:**
1. System Preferences → Notifications
2. Find Python or Terminal
3. Enable notifications

**Linux:**
1. Install `libnotify-bin`: `sudo apt install libnotify-bin`
2. Ensure notification daemon is running

### Q: Can I get notifications on my phone?
**A:** Not directly, but you can:
1. Use remote desktop to your computer
2. Set up email/SMS forwarding (requires custom scripting)
3. Use third-party notification forwarding apps

### Q: Notifications disappear too quickly
**A:** Notification timeout is set to 10 seconds. To change it, edit `crypto_monitor.py`:
```python
notification.notify(
    ...
    timeout=30  # Change to 30 seconds
)
```

### Q: Can I customize notification sounds?
**A:** This depends on your operating system's notification settings. The app uses the system default notification sound.

---

## Technical Questions

### Q: What is support and resistance?
**A:** 
- **Support**: Price level where buying pressure increases (floor)
- **Resistance**: Price level where selling pressure increases (ceiling)

The app finds these automatically by analyzing historical price action.

### Q: What is RSI?
**A:** RSI (Relative Strength Index) measures momentum from 0-100:
- High RSI (>90): Oversold, price may bounce
- Low RSI (<10): Overbought, price may drop
- We use a 6-period RSI for faster signals

### Q: Why use 1-week and 1-month timeframes for S/R?
**A:** Higher timeframes show major support/resistance levels that:
- Are more significant
- Have more traders watching them
- Are more likely to cause reactions

### Q: Why check RSI on 4H and 1D timeframes?
**A:** These timeframes show short-term momentum while filtering out noise. They're fast enough to catch opportunities but slow enough to be reliable.

### Q: How accurate are the alerts?
**A:** The app identifies technical setups, not guarantees:
- ✅ Alerts highlight potential opportunities
- ❌ Not all alerts lead to profitable trades
- ⚠️ Always do your own analysis
- ⚠️ Consider other factors (news, volume, trend)

### Q: Can I backtest this strategy?
**A:** The current version doesn't include backtesting, but you could:
1. Log all alerts with timestamps
2. Manually review outcomes
3. Adjust thresholds based on results

---

## Troubleshooting

### Q: "Rate limit exceeded" error
**A:** 
1. Increase `CHECK_INTERVAL` to 600 (10 minutes)
2. Reduce number of symbols being monitored
3. Try a different exchange

### Q: "Symbol not found" error
**A:** 
1. Check symbol format: `BTC/USDT` (not `BTCUSDT`)
2. Verify symbol exists on your exchange
3. Check exchange's website for correct symbol name

### Q: App crashes immediately
**A:** 
1. Run `test_setup.bat` to diagnose
2. Check `crypto_monitor.log` for error messages
3. Ensure all dependencies installed: `pip install -r requirements.txt`

### Q: "Connection timeout" errors
**A:** 
1. Check internet connection
2. Try different exchange
3. Check if exchange is operational (downdetector.com)
4. Some networks block cryptocurrency exchange APIs

### Q: GUI window freezes
**A:** 
1. Use console version instead: `start_monitor.bat`
2. Check `crypto_monitor.log` for errors
3. Restart the application

### Q: Log file getting too large
**A:** The log file can grow over time. To manage:
1. Manually delete `crypto_monitor.log` (safe to delete)
2. Or set up log rotation (advanced)

---

## Trading & Strategy

### Q: Should I trade every alert?
**A:** No! Alerts are starting points for analysis. Consider:
- Overall market trend
- Volume confirmation
- News and events
- Multiple timeframe analysis
- Risk management

### Q: What's a good win rate for these alerts?
**A:** This varies greatly based on:
- Your entry/exit strategy
- Market conditions
- Risk management
- Timeframe you trade

Track your own results to determine effectiveness.

### Q: Can I use this for day trading?
**A:** Yes, but consider:
- Alerts may be infrequent
- Best for swing trading (days to weeks)
- Combine with other analysis tools

### Q: What about stop losses?
**A:** The app doesn't provide stop loss levels. You should:
- Set stops based on your risk tolerance
- Consider placing stops beyond S/R levels
- Use proper position sizing

### Q: Does this work in bear markets?
**A:** Yes! The app finds both:
- Oversold conditions (potential bounces)
- Overbought conditions (potential drops)

Both can be profitable in any market condition.

---

## Advanced

### Q: Can I add more indicators?
**A:** Yes! The code is open source. You can modify `crypto_monitor.py` to add:
- MACD
- Bollinger Bands
- Volume analysis
- Custom indicators

### Q: Can I export alerts to a spreadsheet?
**A:** Currently, alerts are logged to `crypto_monitor.log`. You can:
1. Parse the log file with a script
2. Import into Excel/Google Sheets
3. Or modify the code to export to CSV

### Q: Can I run multiple instances?
**A:** Yes, but:
- Use different `.env` files
- Monitor different symbols in each instance
- Be mindful of total API calls

### Q: Can I deploy this to a cloud server?
**A:** Yes! Works on:
- AWS EC2
- Google Cloud
- DigitalOcean
- Any VPS with Python

Note: Desktop notifications won't work on headless servers. Consider email/SMS alternatives.

### Q: How do I contribute to the project?
**A:** The code is open source:
1. Fork the repository
2. Make improvements
3. Submit pull requests
4. Report issues and suggestions

---

## Safety & Security

### Q: Is my data safe?
**A:** Yes:
- No personal data collected
- No API keys required
- Only reads public market data
- All processing happens locally

### Q: Can this app trade without my permission?
**A:** No! The app only:
- Reads market data
- Calculates indicators
- Sends notifications

It cannot and will not execute trades.

### Q: Do I need to provide API keys?
**A:** No, the app only reads public data which doesn't require authentication.

---

## Getting Help

### Q: Where can I get more help?
**A:** 
1. Read `README.md` for detailed documentation
2. Check `HOW_IT_WORKS.md` for technical details
3. Review `QUICKSTART.md` for quick setup
4. Run `test_setup.bat` to diagnose issues
5. Check `crypto_monitor.log` for error messages

### Q: How do I report a bug?
**A:** Include:
1. Error message from log file
2. Your configuration (.env settings)
3. Steps to reproduce
4. Operating system and Python version

### Q: Can I request features?
**A:** Yes! Common requests:
- Additional indicators
- Email/SMS notifications
- Backtesting capabilities
- Web interface
- Mobile app

---

## Disclaimer

**Q: Is this financial advice?**

**A:** NO! This tool is for informational purposes only:
- Not financial advice
- Not investment recommendations
- No guarantees of profit
- Cryptocurrency trading is risky
- Only invest what you can afford to lose
- Always do your own research (DYOR)

---

Still have questions? Check the log files, run the test script, or review the documentation!
