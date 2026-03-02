"""
Cryptocurrency Price Monitor with Support/Resistance and RSI Alerts
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


class CryptoMonitor:
    def __init__(self):
        load_dotenv()
        
        # Configuration
        self.symbols = os.getenv('CRYPTO_SYMBOLS', 'BTC/USDT,ETH/USDT').split(',')
        self.exchange_name = os.getenv('EXCHANGE', 'bybit')
        self.check_interval = int(os.getenv('CHECK_INTERVAL', 300))
        self.rsi_overbought = float(os.getenv('RSI_OVERBOUGHT', 90))
        self.rsi_oversold = float(os.getenv('RSI_OVERSOLD', 10))
        self.sr_threshold = float(os.getenv('SR_THRESHOLD', 0.02))
        
        # Initialize exchange
        self.exchange = getattr(ccxt, self.exchange_name)()
        
        # Alert tracking to avoid duplicate notifications
        self.last_alerts = {}
        
        logger.info(f"Initialized CryptoMonitor for {self.symbols} on {self.exchange_name}")
    
    def fetch_ohlcv(self, symbol, timeframe, limit=200):
        """Fetch OHLCV data from exchange"""
        try:
            ohlcv = self.exchange.fetch_ohlcv(symbol, timeframe, limit=limit)
            df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            return df
        except Exception as e:
            logger.error(f"Error fetching data for {symbol} {timeframe}: {e}")
            return None
    
    def calculate_rsi(self, prices, period=6):
        """Calculate RSI indicator"""
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
        levels = []
        
        # Find local maxima (resistance) and minima (support)
        highs = df['high'].values
        lows = df['low'].values
        closes = df['close'].values
        
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
        logger.info(f"Checking {symbol}...")
        
        try:
            # Fetch data for different timeframes
            df_1w = self.fetch_ohlcv(symbol, '1w', limit=100)
            df_1M = self.fetch_ohlcv(symbol, '1M', limit=100)
            df_4h = self.fetch_ohlcv(symbol, '4h', limit=100)
            df_1d = self.fetch_ohlcv(symbol, '1d', limit=100)
            
            if any(df is None for df in [df_1w, df_1M, df_4h, df_1d]):
                logger.warning(f"Could not fetch all data for {symbol}")
                return
            
            current_price = df_4h['close'].iloc[-1]
            
            # Find support/resistance levels on weekly and monthly timeframes
            sr_1w = self.find_support_resistance(df_1w, self.sr_threshold)
            sr_1M = self.find_support_resistance(df_1M, self.sr_threshold)
            
            all_sr_levels = sr_1w + sr_1M
            
            # Calculate RSI on 4H and 1D timeframes
            rsi_4h = self.calculate_rsi(df_4h['close'].values, period=6)
            rsi_1d = self.calculate_rsi(df_1d['close'].values, period=6)
            
            logger.info(f"{symbol} - Price: ${current_price:.2f}, RSI(4H): {rsi_4h:.2f}, RSI(1D): {rsi_1d:.2f}")
            
            # Check for alert conditions
            alerts = []
            
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
            
            if not alerts:
                logger.info(f"{symbol} - No alerts at this time")
                
        except Exception as e:
            logger.error(f"Error checking {symbol}: {e}")
    
    def send_notification(self, title, message):
        """Send desktop notification"""
        try:
            notification.notify(
                title=title,
                message=message,
                app_name='Crypto Monitor',
                timeout=10
            )
        except Exception as e:
            logger.error(f"Error sending notification: {e}")
    
    def run(self):
        """Main monitoring loop"""
        logger.info("Starting Crypto Monitor...")
        logger.info(f"Monitoring: {', '.join(self.symbols)}")
        logger.info(f"Check interval: {self.check_interval} seconds")
        
        while True:
            try:
                for symbol in self.symbols:
                    symbol = symbol.strip()
                    self.check_symbol(symbol)
                    time.sleep(2)  # Small delay between symbols to avoid rate limits
                
                logger.info(f"Waiting {self.check_interval} seconds until next check...")
                time.sleep(self.check_interval)
                
            except KeyboardInterrupt:
                logger.info("Stopping Crypto Monitor...")
                break
            except Exception as e:
                logger.error(f"Error in main loop: {e}")
                time.sleep(60)  # Wait a minute before retrying


if __name__ == "__main__":
    monitor = CryptoMonitor()
    monitor.run()
