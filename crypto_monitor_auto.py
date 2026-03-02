"""
Cryptocurrency Price Monitor with Automatic Symbol Discovery
Monitors ALL cryptocurrencies on the exchange in real-time
"""
import ccxt
import pandas as pd
import numpy as np
from datetime import datetime
import time
import os
from dotenv import load_dotenv
from plyer import notification
import logging
import json
import requests

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('crypto_monitor.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class AutoCryptoMonitor:
    def __init__(self, enable_notifications: bool = True):
        load_dotenv()
        
        # Configuration
        self.exchange_name = os.getenv('EXCHANGE', 'bybit')
        self.check_interval = int(os.getenv('CHECK_INTERVAL', 300))
        self.rsi_overbought = float(os.getenv('RSI_OVERBOUGHT', 90))
        self.rsi_oversold = float(os.getenv('RSI_OVERSOLD', 10))
        self.sr_threshold = float(os.getenv('SR_THRESHOLD', 0.02))
        
        # Auto-discovery settings
        self.quote_currencies = os.getenv('QUOTE_CURRENCIES', 'USDT,USD,BTC,ETH').split(',')
        self.min_volume_24h = float(os.getenv('MIN_VOLUME_24H', 1000000))  # $1M minimum
        self.min_price = float(os.getenv('MIN_PRICE', 0.000001))
        self.max_symbols = int(os.getenv('MAX_SYMBOLS', 100))  # Limit to prevent overload
        self.refresh_symbols_interval = int(os.getenv('REFRESH_SYMBOLS_HOURS', 24)) * 3600
        self.notification_mode = os.getenv('NOTIFICATION_MODE', 'desktop')  # 'desktop' or 'telegram'
        self.telegram_bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
        self.telegram_chat_id = os.getenv('TELEGRAM_CHAT_ID')
        
        # Initialize exchange
        self.exchange = getattr(ccxt, self.exchange_name)()
        
        # Symbol management
        self.active_symbols = []
        self.last_symbol_refresh = 0
        self.symbol_cache_file = 'active_symbols.json'
        self.enable_notifications = enable_notifications
        
        # Alert tracking to avoid duplicate notifications
        self.last_alerts = {}
        
        logger.info(f"Initialized AutoCryptoMonitor on {self.exchange_name}")
        logger.info(f"Auto-discovering symbols with quote currencies: {', '.join(self.quote_currencies)}")
        logger.info(f"Minimum 24h volume: ${self.min_volume_24h:,.0f}")
    
    def discover_symbols(self):
        """Automatically discover all tradable symbols on the exchange"""
        logger.info("Discovering available cryptocurrencies...")
        
        try:
            # Load markets
            markets = self.exchange.load_markets()
            
            # Get tickers for volume filtering
            logger.info("Fetching market data for volume filtering...")
            tickers = self.exchange.fetch_tickers()
            
            discovered = []
            
            for symbol, market in markets.items():
                # Skip if not active
                if not market.get('active', True):
                    continue
                
                # Filter by quote currency
                quote = market.get('quote', '')
                if quote not in self.quote_currencies:
                    continue
                
                # Check if symbol has ticker data
                if symbol not in tickers:
                    continue
                
                ticker = tickers[symbol]
                
                # Filter by volume
                volume_24h = ticker.get('quoteVolume', 0)
                if volume_24h and volume_24h < self.min_volume_24h:
                    continue
                
                # Filter by price (avoid extremely low-priced coins)
                last_price = ticker.get('last', 0)
                if last_price and last_price < self.min_price:
                    continue
                
                # Add to discovered list
                discovered.append({
                    'symbol': symbol,
                    'volume': volume_24h,
                    'price': last_price,
                    'quote': quote
                })
            
            # Sort by volume (highest first) and limit
            discovered.sort(key=lambda x: x['volume'], reverse=True)
            discovered = discovered[:self.max_symbols]
            
            self.active_symbols = [item['symbol'] for item in discovered]
            
            logger.info(f"Discovered {len(self.active_symbols)} cryptocurrencies to monitor")
            logger.info(f"Top 10: {', '.join(self.active_symbols[:10])}")
            
            # Save to cache
            self.save_symbol_cache(discovered)
            
            return self.active_symbols
            
        except Exception as e:
            logger.error(f"Error discovering symbols: {e}")
            # Try to load from cache
            return self.load_symbol_cache()
    
    def save_symbol_cache(self, symbols_data):
        """Save discovered symbols to cache file"""
        try:
            cache_data = {
                'timestamp': time.time(),
                'exchange': self.exchange_name,
                'symbols': symbols_data
            }
            with open(self.symbol_cache_file, 'w') as f:
                json.dump(cache_data, f, indent=2)
            logger.info(f"Saved {len(symbols_data)} symbols to cache")
        except Exception as e:
            logger.error(f"Error saving symbol cache: {e}")
    
    def load_symbol_cache(self):
        """Load symbols from cache file"""
        try:
            if os.path.exists(self.symbol_cache_file):
                with open(self.symbol_cache_file, 'r') as f:
                    cache_data = json.load(f)
                
                symbols = [item['symbol'] for item in cache_data.get('symbols', [])]
                logger.info(f"Loaded {len(symbols)} symbols from cache")
                return symbols
        except Exception as e:
            logger.error(f"Error loading symbol cache: {e}")
        
        return []
    
    def should_refresh_symbols(self):
        """Check if it's time to refresh the symbol list"""
        return (time.time() - self.last_symbol_refresh) > self.refresh_symbols_interval
    
    def fetch_ohlcv(self, symbol, timeframe, limit=200):
        """Fetch OHLCV data from exchange"""
        try:
            ohlcv = self.exchange.fetch_ohlcv(symbol, timeframe, limit=limit)
            df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            return df
        except Exception as e:
            logger.debug(f"Error fetching data for {symbol} {timeframe}: {e}")
            return None
    
    def calculate_rsi(self, prices, period=6):
        """Calculate RSI indicator"""
        if len(prices) < period + 1:
            return 50
        
        deltas = np.diff(prices)
        gains = np.where(deltas > 0, deltas, 0)
        losses = np.where(deltas < 0, -deltas, 0)
        
        avg_gain = np.mean(gains[:period])
        avg_loss = np.mean(losses[:period])
        
        if avg_loss == 0:
            return 100
        
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        
        # Calculate for all periods using exponential moving average
        rsi_values = [rsi]
        for i in range(period, len(deltas)):
            avg_gain = (avg_gain * (period - 1) + gains[i]) / period
            avg_loss = (avg_loss * (period - 1) + losses[i]) / period
            
            if avg_loss == 0:
                rsi_values.append(100)
            else:
                rs = avg_gain / avg_loss
                rsi_values.append(100 - (100 / (1 + rs)))
        
        return rsi_values[-1] if rsi_values else 50
    
    def find_support_resistance(self, df, threshold=0.02):
        """
        Find support and resistance levels using pivot points
        Returns list of (level, type) tuples
        """
        if len(df) < 15:
            return []
        
        levels = []
        
        # Find local maxima (resistance) and minima (support)
        highs = df['high'].values
        lows = df['low'].values
        
        # Use a window to find local extrema
        window = 5
        
        for i in range(window, len(df) - window):
            # Check for local maximum (resistance)
            if highs[i] == max(highs[i-window:i+window+1]):
                levels.append((highs[i], 'resistance'))
            
            # Check for local minimum (support)
            if lows[i] == min(lows[i-window:i+window+1]):
                levels.append((lows[i], 'support'))
        
        # Cluster nearby levels
        if not levels:
            return []
        
        levels.sort(key=lambda x: x[0])
        clustered = []
        current_cluster = [levels[0]]
        
        for level in levels[1:]:
            if abs(level[0] - current_cluster[0][0]) / current_cluster[0][0] < threshold:
                current_cluster.append(level)
            else:
                # Average the cluster
                avg_price = np.mean([l[0] for l in current_cluster])
                level_type = max(set([l[1] for l in current_cluster]), 
                               key=[l[1] for l in current_cluster].count)
                clustered.append((avg_price, level_type))
                current_cluster = [level]
        
        # Add last cluster
        if current_cluster:
            avg_price = np.mean([l[0] for l in current_cluster])
            level_type = max(set([l[1] for l in current_cluster]), 
                           key=[l[1] for l in current_cluster].count)
            clustered.append((avg_price, level_type))
        
        return clustered
    
    def is_near_level(self, current_price, level, threshold=0.02):
        """Check if current price is near a support/resistance level"""
        return abs(current_price - level) / level < threshold
    
    def check_symbol(self, symbol):
        """Check a single symbol for alert conditions"""
        alerts = []
        try:
            # Fetch data for different timeframes
            df_1w = self.fetch_ohlcv(symbol, '1w', limit=100)
            df_1M = self.fetch_ohlcv(symbol, '1M', limit=100)
            df_4h = self.fetch_ohlcv(symbol, '4h', limit=100)
            df_1d = self.fetch_ohlcv(symbol, '1d', limit=100)
            
            if any(df is None for df in [df_1w, df_1M, df_4h, df_1d]):
                return alerts
            
            current_price = df_4h['close'].iloc[-1]
            
            # Find support/resistance levels on weekly and monthly timeframes
            sr_1w = self.find_support_resistance(df_1w, self.sr_threshold)
            sr_1M = self.find_support_resistance(df_1M, self.sr_threshold)
            
            all_sr_levels = sr_1w + sr_1M
            
            # Calculate RSI on 4H and 1D timeframes
            rsi_4h = self.calculate_rsi(df_4h['close'].values, period=6)
            rsi_1d = self.calculate_rsi(df_1d['close'].values, period=6)
            
            # Check for alert conditions
            # Check if near support/resistance
            near_levels = []
            for level, level_type in all_sr_levels:
                if self.is_near_level(current_price, level, self.sr_threshold):
                    near_levels.append((level, level_type))
            
            # Check RSI conditions
            is_oversold = rsi_4h > self.rsi_overbought or rsi_1d > self.rsi_overbought
            is_overbought = rsi_4h < self.rsi_oversold or rsi_1d < self.rsi_oversold
            
            # Generate alerts
            if near_levels and (is_oversold or is_overbought):
                for level, level_type in near_levels:
                    condition = "OVERSOLD" if is_oversold else "OVERBOUGHT"
                    alert_key = f"{symbol}_{level_type}_{condition}"
                    
                    # Check if we already sent this alert recently (within 1 hour)
                    if alert_key in self.last_alerts:
                        time_diff = time.time() - self.last_alerts[alert_key]
                        if time_diff < 3600:  # 1 hour
                            continue
                    
                    alert_msg = (
                        f"{symbol} Alert!\n"
                        f"Price: ${current_price:.2f}\n"
                        f"Near {level_type.upper()}: ${level:.2f}\n"
                        f"Condition: {condition}\n"
                        f"RSI(4H): {rsi_4h:.2f} | RSI(1D): {rsi_1d:.2f}"
                    )
                    
                    alerts.append(alert_msg)
                    self.last_alerts[alert_key] = time.time()
            
            # Send notifications
            for alert in alerts:
                self.send_notification(f"{symbol} Trading Alert", alert)
                logger.warning(f"ALERT: {alert}")
            
            # Only log if there's an alert or every 10th check
            if alerts:
                logger.info(f"{symbol} - Price: ${current_price:.2f}, RSI(4H): {rsi_4h:.2f}, RSI(1D): {rsi_1d:.2f}")

            return alerts
                
        except Exception as e:
            logger.debug(f"Error checking {symbol}: {e}")
            return alerts
    
    def send_notification(self, title, message):
        """Send notification via configured channel"""
        if not self.enable_notifications:
            logger.info(f"Notification (disabled): {title} - {message}")
            return

        if self.notification_mode == 'telegram' and self.telegram_bot_token and self.telegram_chat_id:
            try:
                text = f"{title}\n\n{message}"
                url = f"https://api.telegram.org/bot{self.telegram_bot_token}/sendMessage"
                resp = requests.post(url, json={"chat_id": self.telegram_chat_id, "text": text})
                if resp.status_code != 200:
                    logger.error(f"Error sending Telegram notification: {resp.status_code} {resp.text}")
            except Exception as e:
                logger.error(f"Error sending Telegram notification: {e}")
        else:
            try:
                notification.notify(
                    title=title,
                    message=message,
                    app_name='Crypto Monitor',
                    timeout=10
                )
            except Exception as e:
                logger.error(f"Error sending desktop notification: {e}")
    
    def run(self):
        """Main monitoring loop with automatic symbol discovery"""
        logger.info("Starting Auto Crypto Monitor...")
        logger.info(f"Exchange: {self.exchange_name}")
        logger.info(f"Quote currencies: {', '.join(self.quote_currencies)}")
        logger.info(f"Minimum 24h volume: ${self.min_volume_24h:,.0f}")
        logger.info(f"Max symbols to monitor: {self.max_symbols}")
        logger.info(f"Check interval: {self.check_interval} seconds")
        
        # Initial symbol discovery
        self.active_symbols = self.discover_symbols()
        self.last_symbol_refresh = time.time()
        
        if not self.active_symbols:
            logger.error("No symbols discovered! Check your configuration.")
            return
        
        cycle_count = 0
        
        while True:
            try:
                # Refresh symbol list periodically
                if self.should_refresh_symbols():
                    logger.info("Refreshing symbol list...")
                    self.active_symbols = self.discover_symbols()
                    self.last_symbol_refresh = time.time()
                
                cycle_count += 1
                logger.info(f"=== Cycle {cycle_count}: Checking {len(self.active_symbols)} symbols ===")
                
                # Check each symbol
                checked = 0
                for symbol in self.active_symbols:
                    self.check_symbol(symbol)
                    checked += 1
                    
                    # Progress update every 10 symbols
                    if checked % 10 == 0:
                        logger.info(f"Progress: {checked}/{len(self.active_symbols)} symbols checked")
                    
                    time.sleep(1)  # Small delay to avoid rate limits
                
                logger.info(f"Cycle {cycle_count} complete. Waiting {self.check_interval} seconds...")
                time.sleep(self.check_interval)
                
            except KeyboardInterrupt:
                logger.info("Stopping Auto Crypto Monitor...")
                break
            except Exception as e:
                logger.error(f"Error in main loop: {e}")
                time.sleep(60)
    
    def discover_symbols(self):
        """Automatically discover all tradable symbols on the exchange"""
        logger.info("Discovering available cryptocurrencies...")
        
        try:
            # Load markets
            markets = self.exchange.load_markets()
            
            # Get tickers for volume filtering
            logger.info("Fetching market data for volume filtering...")
            tickers = self.exchange.fetch_tickers()
            
            discovered = []
            
            for symbol, market in markets.items():
                # Skip if not active
                if not market.get('active', True):
                    continue
                
                # Filter by quote currency
                quote = market.get('quote', '')
                if quote not in self.quote_currencies:
                    continue
                
                # Check if symbol has ticker data
                if symbol not in tickers:
                    continue
                
                ticker = tickers[symbol]
                
                # Filter by volume
                volume_24h = ticker.get('quoteVolume', 0)
                if volume_24h and volume_24h < self.min_volume_24h:
                    continue
                
                # Filter by price (avoid extremely low-priced coins)
                last_price = ticker.get('last', 0)
                if last_price and last_price < self.min_price:
                    continue
                
                # Add to discovered list
                discovered.append({
                    'symbol': symbol,
                    'volume': volume_24h,
                    'price': last_price,
                    'quote': quote
                })
            
            # Sort by volume (highest first) and limit
            discovered.sort(key=lambda x: x['volume'], reverse=True)
            discovered = discovered[:self.max_symbols]
            
            active_symbols = [item['symbol'] for item in discovered]
            
            logger.info(f"Discovered {len(active_symbols)} cryptocurrencies to monitor")
            if active_symbols:
                logger.info(f"Top 10 by volume: {', '.join(active_symbols[:10])}")
            
            # Save to cache
            self.save_symbol_cache(discovered)
            
            return active_symbols
            
        except Exception as e:
            logger.error(f"Error discovering symbols: {e}")
            # Try to load from cache
            return self.load_symbol_cache()
    
    def save_symbol_cache(self, symbols_data):
        """Save discovered symbols to cache file"""
        try:
            cache_data = {
                'timestamp': time.time(),
                'exchange': self.exchange_name,
                'symbols': symbols_data
            }
            with open(self.symbol_cache_file, 'w') as f:
                json.dump(cache_data, f, indent=2)
            logger.info(f"Saved {len(symbols_data)} symbols to cache")
        except Exception as e:
            logger.error(f"Error saving symbol cache: {e}")
    
    def load_symbol_cache(self):
        """Load symbols from cache file"""
        try:
            if os.path.exists(self.symbol_cache_file):
                with open(self.symbol_cache_file, 'r') as f:
                    cache_data = json.load(f)
                
                symbols = [item['symbol'] for item in cache_data.get('symbols', [])]
                logger.info(f"Loaded {len(symbols)} symbols from cache")
                return symbols
        except Exception as e:
            logger.error(f"Error loading symbol cache: {e}")
        
        return []
    
    def should_refresh_symbols(self):
        """Check if it's time to refresh the symbol list"""
        return (time.time() - self.last_symbol_refresh) > self.refresh_symbols_interval


if __name__ == "__main__":
    monitor = AutoCryptoMonitor()
    monitor.run()
