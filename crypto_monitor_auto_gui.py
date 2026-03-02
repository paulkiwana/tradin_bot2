"""
Cryptocurrency Price Monitor - Auto-Discovery GUI Version
"""
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import threading
import queue
from crypto_monitor_auto import AutoCryptoMonitor
import logging
import os
from dotenv import load_dotenv, set_key
import json


class AutoCryptoMonitorGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Crypto Monitor - Auto Discovery")
        self.root.geometry("900x700")
        
        self.monitor = None
        self.monitor_thread = None
        self.is_running = False
        self.log_queue = queue.Queue()
        
        self.setup_ui()
        self.load_config()
        self.setup_logging()
        self.check_log_queue()
    
    def setup_ui(self):
        # Configuration Frame
        config_frame = ttk.LabelFrame(self.root, text="Auto-Discovery Configuration", padding=10)
        config_frame.pack(fill=tk.X, padx=10, pady=5)
        
        # Exchange
        ttk.Label(config_frame, text="Exchange:").grid(row=0, column=0, sticky=tk.W, pady=2)
        self.exchange_entry = ttk.Entry(config_frame, width=50)
        self.exchange_entry.grid(row=0, column=1, pady=2, padx=5)
        
        # Quote Currencies
        ttk.Label(config_frame, text="Quote Currencies (comma-separated):").grid(row=1, column=0, sticky=tk.W, pady=2)
        self.quote_entry = ttk.Entry(config_frame, width=50)
        self.quote_entry.grid(row=1, column=1, pady=2, padx=5)
        ttk.Label(config_frame, text="e.g., USDT,USD,BTC,ETH", font=('Arial', 8), foreground='gray').grid(row=2, column=1, sticky=tk.W, padx=5)
        
        # Min Volume
        ttk.Label(config_frame, text="Minimum 24h Volume ($):").grid(row=3, column=0, sticky=tk.W, pady=2)
        self.min_volume_entry = ttk.Entry(config_frame, width=50)
        self.min_volume_entry.grid(row=3, column=1, pady=2, padx=5)
        
        # Max Symbols
        ttk.Label(config_frame, text="Max Symbols to Monitor:").grid(row=4, column=0, sticky=tk.W, pady=2)
        self.max_symbols_entry = ttk.Entry(config_frame, width=50)
        self.max_symbols_entry.grid(row=4, column=1, pady=2, padx=5)
        
        # Check Interval
        ttk.Label(config_frame, text="Check Interval (seconds):").grid(row=5, column=0, sticky=tk.W, pady=2)
        self.interval_entry = ttk.Entry(config_frame, width=50)
        self.interval_entry.grid(row=5, column=1, pady=2, padx=5)
        
        # RSI Thresholds
        ttk.Label(config_frame, text="RSI Overbought (>):").grid(row=6, column=0, sticky=tk.W, pady=2)
        self.rsi_overbought_entry = ttk.Entry(config_frame, width=50)
        self.rsi_overbought_entry.grid(row=6, column=1, pady=2, padx=5)
        
        ttk.Label(config_frame, text="RSI Oversold (<):").grid(row=7, column=0, sticky=tk.W, pady=2)
        self.rsi_oversold_entry = ttk.Entry(config_frame, width=50)
        self.rsi_oversold_entry.grid(row=7, column=1, pady=2, padx=5)
        
        # Save Config Button
        ttk.Button(config_frame, text="Save Configuration", command=self.save_config).grid(row=8, column=0, columnspan=2, pady=10)
        
        # Control Frame
        control_frame = ttk.Frame(self.root, padding=10)
        control_frame.pack(fill=tk.X, padx=10, pady=5)
        
        self.start_button = ttk.Button(control_frame, text="Start Auto-Discovery", command=self.start_monitoring)
        self.start_button.pack(side=tk.LEFT, padx=5)
        
        self.stop_button = ttk.Button(control_frame, text="Stop Monitoring", command=self.stop_monitoring, state=tk.DISABLED)
        self.stop_button.pack(side=tk.LEFT, padx=5)
        
        self.discover_button = ttk.Button(control_frame, text="Discover Symbols Now", command=self.discover_now)
        self.discover_button.pack(side=tk.LEFT, padx=5)
        
        self.status_label = ttk.Label(control_frame, text="Status: Stopped", foreground="red")
        self.status_label.pack(side=tk.LEFT, padx=20)
        
        # Stats Frame
        stats_frame = ttk.LabelFrame(self.root, text="Statistics", padding=10)
        stats_frame.pack(fill=tk.X, padx=10, pady=5)
        
        self.symbols_count_label = ttk.Label(stats_frame, text="Symbols Monitoring: 0")
        self.symbols_count_label.pack(side=tk.LEFT, padx=10)
        
        self.alerts_count_label = ttk.Label(stats_frame, text="Alerts Sent: 0")
        self.alerts_count_label.pack(side=tk.LEFT, padx=10)
        
        # Discovered Symbols Frame
        symbols_frame = ttk.LabelFrame(self.root, text="Discovered Symbols (Top 20)", padding=10)
        symbols_frame.pack(fill=tk.X, padx=10, pady=5)
        
        self.symbols_text = tk.Text(symbols_frame, height=3, state=tk.DISABLED)
        self.symbols_text.pack(fill=tk.X)
        
        # Log Frame
        log_frame = ttk.LabelFrame(self.root, text="Activity Log", padding=10)
        log_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        self.log_text = scrolledtext.ScrolledText(log_frame, height=15, state=tk.DISABLED)
        self.log_text.pack(fill=tk.BOTH, expand=True)
        
        # Clear Log Button
        ttk.Button(log_frame, text="Clear Log", command=self.clear_log).pack(pady=5)
    
    def load_config(self):
        """Load configuration from .env file"""
        load_dotenv()
        
        self.exchange_entry.insert(0, os.getenv('EXCHANGE', 'bybit'))
        self.quote_entry.insert(0, os.getenv('QUOTE_CURRENCIES', 'USDT,USD,BTC,ETH'))
        self.min_volume_entry.insert(0, os.getenv('MIN_VOLUME_24H', '1000000'))
        self.max_symbols_entry.insert(0, os.getenv('MAX_SYMBOLS', '100'))
        self.interval_entry.insert(0, os.getenv('CHECK_INTERVAL', '300'))
        self.rsi_overbought_entry.insert(0, os.getenv('RSI_OVERBOUGHT', '90'))
        self.rsi_oversold_entry.insert(0, os.getenv('RSI_OVERSOLD', '10'))
    
    def save_config(self):
        """Save configuration to .env file"""
        env_file = '.env'
        
        # Create .env if it doesn't exist
        if not os.path.exists(env_file):
            with open(env_file, 'w') as f:
                f.write('')
        
        set_key(env_file, 'EXCHANGE', self.exchange_entry.get())
        set_key(env_file, 'QUOTE_CURRENCIES', self.quote_entry.get())
        set_key(env_file, 'MIN_VOLUME_24H', self.min_volume_entry.get())
        set_key(env_file, 'MAX_SYMBOLS', self.max_symbols_entry.get())
        set_key(env_file, 'CHECK_INTERVAL', self.interval_entry.get())
        set_key(env_file, 'RSI_OVERBOUGHT', self.rsi_overbought_entry.get())
        set_key(env_file, 'RSI_OVERSOLD', self.rsi_oversold_entry.get())
        
        messagebox.showinfo("Success", "Configuration saved successfully!")
        self.log_message("Configuration saved to .env file")
    
    def setup_logging(self):
        """Setup logging to redirect to GUI"""
        class QueueHandler(logging.Handler):
            def __init__(self, log_queue):
                super().__init__()
                self.log_queue = log_queue
            
            def emit(self, record):
                self.log_queue.put(self.format(record))
        
        queue_handler = QueueHandler(self.log_queue)
        queue_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
        
        logger = logging.getLogger()
        logger.addHandler(queue_handler)
        logger.setLevel(logging.INFO)
    
    def check_log_queue(self):
        """Check for new log messages and display them"""
        while not self.log_queue.empty():
            message = self.log_queue.get()
            self.log_message(message)
        
        self.root.after(100, self.check_log_queue)
    
    def log_message(self, message):
        """Add message to log text widget"""
        self.log_text.config(state=tk.NORMAL)
        self.log_text.insert(tk.END, message + '\n')
        self.log_text.see(tk.END)
        self.log_text.config(state=tk.DISABLED)
    
    def clear_log(self):
        """Clear the log text widget"""
        self.log_text.config(state=tk.NORMAL)
        self.log_text.delete(1.0, tk.END)
        self.log_text.config(state=tk.DISABLED)
    
    def update_symbols_display(self):
        """Update the discovered symbols display"""
        try:
            if os.path.exists('active_symbols.json'):
                with open('active_symbols.json', 'r') as f:
                    cache_data = json.load(f)
                
                symbols = cache_data.get('symbols', [])
                top_20 = symbols[:20]
                
                display_text = ', '.join([s['symbol'] for s in top_20])
                if len(symbols) > 20:
                    display_text += f" ... and {len(symbols) - 20} more"
                
                self.symbols_text.config(state=tk.NORMAL)
                self.symbols_text.delete(1.0, tk.END)
                self.symbols_text.insert(tk.END, display_text)
                self.symbols_text.config(state=tk.DISABLED)
                
                self.symbols_count_label.config(text=f"Symbols Monitoring: {len(symbols)}")
        except Exception as e:
            pass
    
    def discover_now(self):
        """Manually trigger symbol discovery"""
        self.log_message("Starting manual symbol discovery...")
        
        def discover_thread():
            try:
                load_dotenv(override=True)
                temp_monitor = AutoCryptoMonitor()
                symbols = temp_monitor.discover_symbols()
                self.root.after(0, lambda: self.log_message(f"Discovery complete! Found {len(symbols)} symbols"))
                self.root.after(0, self.update_symbols_display)
            except Exception as e:
                self.root.after(0, lambda: self.log_message(f"Discovery error: {e}"))
        
        threading.Thread(target=discover_thread, daemon=True).start()
    
    def start_monitoring(self):
        """Start the monitoring process"""
        if self.is_running:
            return
        
        # Save config first
        self.save_config()
        
        # Reload environment
        load_dotenv(override=True)
        
        self.is_running = True
        self.start_button.config(state=tk.DISABLED)
        self.stop_button.config(state=tk.NORMAL)
        self.discover_button.config(state=tk.DISABLED)
        self.status_label.config(text="Status: Running", foreground="green")
        
        self.log_message("Starting auto crypto monitor...")
        
        # Start monitor in separate thread
        self.monitor_thread = threading.Thread(target=self.run_monitor, daemon=True)
        self.monitor_thread.start()
        
        # Start stats updater
        self.update_stats()
    
    def run_monitor(self):
        """Run the monitor in a separate thread"""
        try:
            self.monitor = AutoCryptoMonitor()
            self.monitor.run()
        
        except Exception as e:
            self.log_message(f"Error in monitor: {e}")
            self.is_running = False
            self.root.after(0, self.update_stopped_state)
    
    def stop_monitoring(self):
        """Stop the monitoring process"""
        if not self.is_running:
            return
        
        self.is_running = False
        self.log_message("Stopping crypto monitor...")
        
        self.update_stopped_state()
    
    def update_stopped_state(self):
        """Update UI to stopped state"""
        self.start_button.config(state=tk.NORMAL)
        self.stop_button.config(state=tk.DISABLED)
        self.discover_button.config(state=tk.NORMAL)
        self.status_label.config(text="Status: Stopped", foreground="red")
        self.log_message("Monitor stopped")
    
    def update_stats(self):
        """Update statistics display"""
        if self.is_running:
            self.update_symbols_display()
            
            # Update alert count
            if self.monitor and hasattr(self.monitor, 'last_alerts'):
                alert_count = len(self.monitor.last_alerts)
                self.alerts_count_label.config(text=f"Alerts Sent: {alert_count}")
            
            # Schedule next update
            self.root.after(5000, self.update_stats)


def main():
    root = tk.Tk()
    app = AutoCryptoMonitorGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
