# 🚀 Cryptocurrency Price Monitor

> **Never miss a trading opportunity!** Get instant desktop notifications when cryptocurrencies hit key technical levels.

A Python application that monitors cryptocurrency prices and sends desktop notifications when specific conditions are met:

✅ **Price is near support or resistance levels** (on 1-week or 1-month timeframes)  
✅ **RSI6 indicates oversold (>90) or overbought (<10) conditions** on 4H or 1D timeframes

---

## 🎯 Quick Links

- **[⚡ Quick Start Guide](QUICKSTART.md)** - Get started in 3 steps
- **[📚 Documentation Index](INDEX.md)** - Find any information quickly
- **[❓ FAQ](FAQ.md)** - Common questions answered
- **[🔧 How It Works](HOW_IT_WORKS.md)** - Technical deep dive
- **[☁️ Deploy to Render](RENDER_DEPLOY.md)** - FastAPI API deployment guide

---

## Features

- **Support/Resistance Detection**: Automatically identifies key support and resistance levels using pivot points on weekly and monthly charts
- **RSI Monitoring**: Tracks RSI(6) on 4-hour and daily timeframes
- **Desktop Notifications**: Sends alerts when conditions are met
- **Multi-Cryptocurrency Support**: Monitor multiple crypto pairs simultaneously
- **🆕 Auto-Discovery Mode**: Automatically discovers and monitors ALL cryptocurrencies on the exchange
- **Real-Time Updates**: Automatically detects new listings and removes delisted coins
- **Volume Filtering**: Focuses on liquid, actively traded cryptocurrencies
- **Configurable**: Easy configuration via environment variables
- **Dual Interface**: Both GUI and console versions
- **Logging**: Comprehensive logging to file and console

## Installation

### Quick Setup (Windows)

1. **Install Python 3.8 or higher** from [python.org](https://www.python.org/downloads/)
   - Make sure to check "Add Python to PATH" during installation

2. **Run the setup script**:
   - Double-click `setup.bat`
   - This will install all dependencies and create your configuration file

3. **Test your installation**:
   - Double-click `test_setup.bat` to verify everything is working

4. **Start monitoring**:
   - Double-click `start_gui.bat` for the GUI version (recommended)
   - OR double-click `start_monitor.bat` for console version

### Manual Setup (All Platforms)

1. **Install Python 3.8 or higher**

2. **Install dependencies**:
```bash
pip install -r requirements.txt
```

3. **Configure the application**:
   - Copy `.env.example` to `.env`
   - Edit `.env` to customize your settings

```bash
cp .env.example .env
```

4. **Test the installation**:
```bash
python test_monitor.py
```

## Configuration

Edit the `.env` file to customize your monitoring:

```env
# Cryptocurrency symbols to monitor (comma-separated)
CRYPTO_SYMBOLS=BTC/USDT,ETH/USDT,SOL/USDT

# Exchange to use (default: binance)
EXCHANGE=binance

# Check interval in seconds (default: 300 = 5 minutes)
CHECK_INTERVAL=300

# RSI thresholds
RSI_OVERBOUGHT=90
RSI_OVERSOLD=10

# Support/Resistance detection sensitivity (0.01 = 1%)
SR_THRESHOLD=0.02
```

### Configuration Options

- **CRYPTO_SYMBOLS**: Comma-separated list of trading pairs (e.g., `BTC/USDT,ETH/USDT`)
- **EXCHANGE**: Exchange to use (supports any CCXT exchange: `binance`, `coinbase`, `kraken`, etc.)
- **CHECK_INTERVAL**: How often to check prices in seconds (300 = 5 minutes)
- **RSI_OVERBOUGHT**: RSI threshold for oversold condition (default: 90)
- **RSI_OVERSOLD**: RSI threshold for overbought condition (default: 10)
- **SR_THRESHOLD**: Price proximity threshold for support/resistance (0.02 = 2%)

## Usage

### Choose Your Mode

#### 🤖 Auto-Discovery Mode (NEW - Recommended)
**Automatically monitors ALL cryptocurrencies on the exchange!**

**GUI Version:**
```bash
python crypto_monitor_auto_gui.py
```
Or double-click `start_auto_gui.bat` on Windows.

**Console Version:**
```bash
python crypto_monitor_auto.py
```
Or double-click `start_auto_monitor.bat` on Windows.

**Features:**
- Automatically discovers all available cryptocurrencies
- Filters by volume (only liquid coins)
- Catches new listings automatically
- Zero manual maintenance
- See [AUTO_DISCOVERY_GUIDE.md](AUTO_DISCOVERY_GUIDE.md) for details

#### 📝 Manual Mode (Original)
**Specify exact cryptocurrencies to monitor**

**GUI Version:**
```bash
python crypto_monitor_gui.py
```
Or double-click `start_gui.bat` on Windows.

**Console Version:**
```bash
python crypto_monitor.py
```
Or double-click `start_monitor.bat` on Windows.

**Features:**
- Precise control over which coins to monitor
- Lower API usage
- Faster check cycles
- Best for focused trading

The application will:
1. Connect to the configured exchange
2. Monitor the specified cryptocurrencies
3. Check prices and indicators at the configured interval
4. Send desktop notifications when alert conditions are met
5. Log all activity to `crypto_monitor.log`

### Alert Conditions

An alert is triggered when **ALL** of the following conditions are met:

1. **Price is near a support or resistance level** (within SR_THRESHOLD)
   - Support/resistance levels are calculated from 1-week and 1-month timeframes
   
2. **RSI indicates extreme conditions**:
   - **Oversold**: RSI6 > 90 on 4H or 1D timeframe
   - **Overbought**: RSI6 < 10 on 4H or 1D timeframe

### Example Alert

```
BTC/USDT Alert!
Price: $52,345.67
Near SUPPORT: $52,000.00
Condition: OVERSOLD
RSI(4H): 92.34 | RSI(1D): 88.21
```

## How It Works

### Support/Resistance Detection

The application uses a pivot point algorithm to identify support and resistance levels:

1. Scans 1-week and 1-month price data
2. Identifies local maxima (resistance) and minima (support)
3. Clusters nearby levels to reduce noise
4. Checks if current price is within threshold of any level

### RSI Calculation

- Uses a 6-period RSI (RSI6) for faster signals
- Monitors both 4-hour and daily timeframes
- Triggers on extreme readings (>90 oversold, <10 overbought)

### Notification System

- Desktop notifications appear when conditions are met
- Duplicate alerts are suppressed for 1 hour
- All alerts are logged to `crypto_monitor.log`

## Logging

All activity is logged to `crypto_monitor.log` including:
- Price checks and indicator values
- Alert conditions
- Errors and warnings

## Troubleshooting

### No notifications appearing
- Check that your system supports desktop notifications
- On Windows, ensure notifications are enabled in system settings
- Check `crypto_monitor.log` for errors

### Rate limit errors
- Increase `CHECK_INTERVAL` to reduce API calls
- Some exchanges have stricter rate limits than others

### Connection errors
- Verify your internet connection
- Try a different exchange in the configuration
- Check if the exchange is operational

## Advanced Usage

### Running as a Background Service

**Windows (using Task Scheduler)**:
1. Open Task Scheduler
2. Create a new task
3. Set trigger to "At startup"
4. Set action to run `python.exe` with argument `crypto_monitor.py`
5. Set working directory to the application folder

**Linux (using systemd)**:
Create a service file at `/etc/systemd/system/crypto-monitor.service`:

```ini
[Unit]
Description=Crypto Price Monitor
After=network.target

[Service]
Type=simple
User=your-username
WorkingDirectory=/path/to/codin_bot
ExecStart=/usr/bin/python3 crypto_monitor.py
Restart=always

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl enable crypto-monitor
sudo systemctl start crypto-monitor
```

## Dependencies

- **ccxt**: Cryptocurrency exchange integration
- **pandas**: Data manipulation
- **numpy**: Numerical calculations
- **ta**: Technical analysis indicators
- **plyer**: Cross-platform desktop notifications
- **python-dotenv**: Environment variable management

## License

MIT License - feel free to use and modify as needed.

## Disclaimer

This tool is for informational purposes only. Cryptocurrency trading carries significant risk. Always do your own research and never invest more than you can afford to lose.
