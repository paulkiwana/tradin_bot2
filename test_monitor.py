"""
Test script to verify the crypto monitor setup
"""
import sys

def test_imports():
    """Test if all required packages are installed"""
    print("Testing imports...")
    
    required_packages = {
        'ccxt': 'ccxt',
        'pandas': 'pandas',
        'numpy': 'numpy',
        'plyer': 'plyer',
        'dotenv': 'python-dotenv'
    }
    
    failed = []
    
    for module, package in required_packages.items():
        try:
            __import__(module)
            print(f"✓ {package} installed")
        except ImportError:
            print(f"✗ {package} NOT installed")
            failed.append(package)
    
    if failed:
        print(f"\nMissing packages: {', '.join(failed)}")
        print("Run: pip install -r requirements.txt")
        return False
    
    print("\n✓ All packages installed successfully!")
    return True


def test_exchange_connection():
    """Test connection to exchange"""
    print("\nTesting exchange connection...")
    
    try:
        import ccxt
        exchange = ccxt.bybit()
        
        # Fetch BTC/USDT ticker to test connection
        ticker = exchange.fetch_ticker('BTC/USDT')
        price = ticker['last']
        
        print(f"✓ Connected to Bybit successfully!")
        print(f"  Current BTC/USDT price: ${price:,.2f}")
        return True
        
    except Exception as e:
        print(f"✗ Failed to connect to exchange: {e}")
        return False


def test_rsi_calculation():
    """Test RSI calculation"""
    print("\nTesting RSI calculation...")
    
    try:
        import numpy as np
        from crypto_monitor import CryptoMonitor
        
        monitor = CryptoMonitor()
        
        # Test with sample data
        prices = np.array([44, 44.34, 44.09, 43.61, 44.33, 44.83, 45.10, 45.42, 45.84, 46.08, 45.89, 46.03, 45.61, 46.28, 46.28, 46.00, 46.03, 46.41, 46.22, 45.64])
        
        rsi = monitor.calculate_rsi(prices, period=6)
        
        print(f"✓ RSI calculation working!")
        print(f"  Sample RSI value: {rsi:.2f}")
        return True
        
    except Exception as e:
        print(f"✗ RSI calculation failed: {e}")
        return False


def test_support_resistance():
    """Test support/resistance detection"""
    print("\nTesting support/resistance detection...")
    
    try:
        import pandas as pd
        import numpy as np
        from crypto_monitor import CryptoMonitor
        
        monitor = CryptoMonitor()
        
        # Create sample data
        data = {
            'high': np.random.uniform(45000, 46000, 50),
            'low': np.random.uniform(44000, 45000, 50),
            'close': np.random.uniform(44500, 45500, 50)
        }
        df = pd.DataFrame(data)
        
        levels = monitor.find_support_resistance(df)
        
        print(f"✓ Support/Resistance detection working!")
        print(f"  Found {len(levels)} levels")
        return True
        
    except Exception as e:
        print(f"✗ Support/Resistance detection failed: {e}")
        return False


def test_notifications():
    """Test desktop notifications"""
    print("\nTesting desktop notifications...")
    
    try:
        from plyer import notification
        
        notification.notify(
            title='Crypto Monitor Test',
            message='If you see this, notifications are working!',
            app_name='Crypto Monitor',
            timeout=5
        )
        
        print("✓ Notification sent!")
        print("  Check if you received a desktop notification")
        return True
        
    except Exception as e:
        print(f"✗ Notification failed: {e}")
        print("  Notifications may not be supported on your system")
        return False


def main():
    print("=" * 50)
    print("Crypto Monitor - System Test")
    print("=" * 50)
    print()
    
    tests = [
        ("Package Installation", test_imports),
        ("Exchange Connection", test_exchange_connection),
        ("RSI Calculation", test_rsi_calculation),
        ("Support/Resistance Detection", test_support_resistance),
        ("Desktop Notifications", test_notifications)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"✗ {test_name} crashed: {e}")
            results.append((test_name, False))
        print()
    
    print("=" * 50)
    print("Test Summary")
    print("=" * 50)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status}: {test_name}")
    
    print()
    print(f"Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n✓ All tests passed! Your system is ready to run the crypto monitor.")
    else:
        print("\n⚠ Some tests failed. Please check the errors above.")
    
    print()


if __name__ == "__main__":
    main()
    input("\nPress Enter to exit...")
