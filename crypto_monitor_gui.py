"""
Cryptocurrency Price Monitor - GUI Version
"""
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import threading
import queue
from crypto_monitor import CryptoMonitor
import logging
import os
from dotenv import load_dotenv, set_key


class CryptoMonitorGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Crypto Price Monitor")
        self.root.geometry("800x600")
        
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
        config_frame = ttk.LabelFrame(self.root, text="Configuration", padding=10)
        config_frame.pack(fill=tk.X, padx=10, pady=5)
        
        # Symbols
        ttk.Label(config_frame, text="Symbols (comma-separated):").grid(row=0, column=0, sticky=tk.W, pady=2)
        self.symbols_entry = ttk.Entry(config_frame, width=50)
        self.symbols_entry.grid(row=0, column=1, pady=2, padx=5)
        
        # Exchange
        ttk.Label(config_frame, text="Exchange:").grid(row=1, column=0, sticky=tk.W, pady=2)
        self.exchange_entry = ttk.Entry(config_frame, width=50)
        self.exchange_entry.grid(row=1, column=1, pady=2, padx=5)
        
        # Check Interval
        ttk.Label(config_frame, text="Check Interval (seconds):").grid(row=2, column=0, sticky=tk.W, pady=2)
        self.interval_entry = ttk.Entry(config_frame, width=50)
        self.interval_entry.grid(row=2, column=1, pady=2, padx=5)
        
        # RSI Thresholds
        ttk.Label(config_frame, text="RSI Overbought (>):").grid(row=3, column=0, sticky=tk.W, pady=2)
        self.rsi_overbought_entry = ttk.Entry(config_frame, width=50)
        self.rsi_overbought_entry.grid(row=3, column=1, pady=2, padx=5)
        
        ttk.Label(config_frame, text="RSI Oversold (<):").grid(row=4, column=0, sticky=tk.W, pady=2)
        self.rsi_oversold_entry = ttk.Entry(config_frame, width=50)
        self.rsi_oversold_entry.grid(row=4, column=1, pady=2, padx=5)
        
        # Save Config Button
        ttk.Button(config_frame, text="Save Configuration", command=self.save_config).grid(row=5, column=0, columnspan=2, pady=10)
        
        # Control Frame
        control_frame = ttk.Frame(self.root, padding=10)
        control_frame.pack(fill=tk.X, padx=10, pady=5)
        
        self.start_button = ttk.Button(control_frame, text="Start Monitoring", command=self.start_monitoring)
        self.start_button.pack(side=tk.LEFT, padx=5)
        
        self.stop_button = ttk.Button(control_frame, text="Stop Monitoring", command=self.stop_monitoring, state=tk.DISABLED)
        self.stop_button.pack(side=tk.LEFT, padx=5)
        
        self.status_label = ttk.Label(control_frame, text="Status: Stopped", foreground="red")
        self.status_label.pack(side=tk.LEFT, padx=20)
        
        # Log Frame
        log_frame = ttk.LabelFrame(self.root, text="Activity Log", padding=10)
        log_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        self.log_text = scrolledtext.ScrolledText(log_frame, height=20, state=tk.DISABLED)
        self.log_text.pack(fill=tk.BOTH, expand=True)
        
        # Clear Log Button
        ttk.Button(log_frame, text="Clear Log", command=self.clear_log).pack(pady=5)
    
    def load_config(self):
        """Load configuration from .env file"""
        load_dotenv()
        
        self.symbols_entry.insert(0, os.getenv('CRYPTO_SYMBOLS', 'BTC/USDT,ETH/USDT'))
        self.exchange_entry.insert(0, os.getenv('EXCHANGE', 'bybit'))
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
        
        set_key(env_file, 'CRYPTO_SYMBOLS', self.symbols_entry.get())
        set_key(env_file, 'EXCHANGE', self.exchange_entry.get())
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
        self.status_label.config(text="Status: Running", foreground="green")
        
        self.log_message("Starting crypto monitor...")
        
        # Start monitor in separate thread
        self.monitor_thread = threading.Thread(target=self.run_monitor, daemon=True)
        self.monitor_thread.start()
    
    def run_monitor(self):
        """Run the monitor in a separate thread"""
        try:
            self.monitor = CryptoMonitor()
            
            while self.is_running:
                for symbol in self.monitor.symbols:
                    if not self.is_running:
                        break
                    symbol = symbol.strip()
                    self.monitor.check_symbol(symbol)
                
                if not self.is_running:
                    break
                
                # Sleep in small increments to allow for quick stopping
                for _ in range(self.monitor.check_interval):
                    if not self.is_running:
                        break
                    import time
                    time.sleep(1)
        
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
        self.status_label.config(text="Status: Stopped", foreground="red")
        self.log_message("Monitor stopped")


def main():
    root = tk.Tk()
    app = CryptoMonitorGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
