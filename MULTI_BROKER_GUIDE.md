# Multi-Broker Architecture Guide

Complete guide to using multiple brokers with a unified API interface.

---

## 🎯 Overview

The repository now supports **multiple brokers** through a unified abstraction layer. Write your strategy once, and run it on **any supported broker** without changing code!

### ✅ Supported Brokers

| Broker | Status | Features |
|--------|--------|----------|
| **Zerodha** | ✅ **Fully Implemented** | All features working |
| **Upstox** | ⚙️ **Template Ready** | Awaiting SDK integration |
| **Kotak Securities** | ⚙️ **Template Ready** | Awaiting SDK integration |
| **Angel One** | 📝 **Planned** | Structure in place |
| **Fyers** | 📝 **Planned** | Structure in place |
| **AliceBlue** | 📝 **Planned** | Structure in place |

---

## 🏗️ Architecture

### Components

```
brokers/
├── base.py                 # Base interface (BaseBroker)
├── factory.py              # Broker factory pattern
├── config.py               # Configuration management
├── __init__.py            # Package exports
└── implementations/
    ├── zerodha.py         # Zerodha implementation ✅
    ├── upstox.py          # Upstox template
    ├── kotak.py           # Kotak template
    ├── angelone.py        # Angel One (planned)
    ├── fyers.py           # Fyers (planned)
    └── aliceblue.py       # AliceBlue (planned)
```

### Unified Interface

All brokers implement the same interface:

```python
from brokers.base import BaseBroker

# Every broker has these methods:
broker.place_order(...)
broker.get_positions()
broker.get_quote(...)
broker.get_ltp(...)
# ... and 20+ more standardized methods
```

---

## 🚀 Quick Start

### 1. Install Dependencies

```bash
# For Zerodha
pip install kiteconnect

# For other brokers (when implementing)
pip install upstox-python-sdk    # Upstox
pip install neo-python           # Kotak
# ... etc
```

### 2. Configure Credentials

**Option A: Environment Variables (.env file)**

```bash
# Copy and edit .env.example
cp .env.example .env

# Add your credentials
ZERODHA_API_KEY=your_key
ZERODHA_API_SECRET=your_secret
ZERODHA_ACCESS_TOKEN=your_token
```

**Option B: Configuration File (brokers.yaml)**

```yaml
brokers:
  zerodha:
    api_key: "your_api_key"
    api_secret: "your_api_secret"
    access_token: null
```

### 3. Use in Your Strategy

```python
from brokers import BrokerFactory

# Create broker instance from environment
broker = BrokerFactory.create_from_env('zerodha')

# Or from config file
broker = BrokerFactory.create_from_file('zerodha', 'config/brokers.yaml')

# Or directly
broker = BrokerFactory.create(
    'zerodha',
    api_key='your_key',
    api_secret='your_secret',
    access_token='your_token'
)

# Now use the broker
broker.place_order(
    symbol='NIFTY2412520000CE',
    exchange='NFO',
    transaction_type='SELL',
    quantity=50,
    order_type='MARKET',
    product_type='MIS'
)

# Get positions
positions = broker.get_positions()
for pos in positions:
    print(f"{pos.symbol}: {pos.pnl}")

# Get LTP
ltp = broker.get_ltp('BANKNIFTY2412546000CE', 'NFO')
print(f"LTP: {ltp}")
```

---

## 📚 Complete API Reference

### Authentication

```python
# Login (for first-time auth)
broker.login(request_token='...')

# Set existing token
broker.set_access_token('your_token')

# Generate token from request token
access_token = broker.get_access_token('request_token')
```

### Order Management

```python
# Place order
order_id = broker.place_order(
    symbol='BANKNIFTY2412546000CE',
    exchange='NFO',
    transaction_type='BUY',  # or 'SELL'
    quantity=50,
    order_type='MARKET',     # or 'LIMIT', 'SL', 'SL-M'
    price=150.50,            # For LIMIT orders
    product_type='MIS',      # or 'CNC', 'NRML'
    trigger_price=145.00,    # For SL orders
    validity='DAY'           # or 'IOC'
)

# Modify order
broker.modify_order(
    order_id='123456',
    quantity=75,
    price=155.00
)

# Cancel order
broker.cancel_order('123456')

# Get all orders
orders = broker.get_orders()

# Get order history
history = broker.get_order_history('123456')
```

### Position Management

```python
# Get positions
positions = broker.get_positions()
for pos in positions:
    print(f"Symbol: {pos.symbol}")
    print(f"Quantity: {pos.quantity}")
    print(f"P&L: ₹{pos.pnl:,.2f}")

# Get holdings
holdings = broker.get_holdings()

# Square off position
broker.square_off_position(
    symbol='BANKNIFTY2412546000CE',
    exchange='NFO',
    product_type='MIS'
)
```

### Market Data

```python
# Get quote
quote = broker.get_quote('NIFTY 50', 'NSE')
print(f"LTP: {quote.last_price}")
print(f"Open: {quote.open}")
print(f"High: {quote.high}")
print(f"Low: {quote.low}")

# Get LTP only
ltp = broker.get_ltp('NIFTY 50', 'NSE')

# Get historical data
from datetime import datetime
history = broker.get_historical_data(
    symbol='NIFTY 50',
    exchange='NSE',
    from_date=datetime(2024, 1, 1),
    to_date=datetime(2024, 12, 31),
    interval='day'  # or 'minute', '5minute', etc.
)
```

### Account Information

```python
# Get margins
margins = broker.get_margins()
print(f"Available: ₹{margins.available_cash:,.2f}")
print(f"Used: ₹{margins.used_margin:,.2f}")

# Get profile
profile = broker.get_profile()
print(f"User: {profile['user_name']}")
print(f"Email: {profile['email']}")
```

### Instrument Search

```python
# Search instruments
results = broker.search_instruments('NIFTY')

# Get all instruments for exchange
instruments = broker.get_instruments('NFO')
```

---

## 🔄 Switching Brokers

### In Code

```python
# Start with Zerodha
broker = BrokerFactory.create_from_env('zerodha')

# Switch to Upstox (once implemented)
broker = BrokerFactory.create_from_env('upstox')

# Your strategy code remains the same!
positions = broker.get_positions()  # Works with any broker
```

### Using Environment Variable

```python
import os
from brokers import BrokerFactory

# Set default broker in .env
broker_name = os.getenv('DEFAULT_BROKER', 'zerodha')
broker = BrokerFactory.create_from_env(broker_name)
```

---

## 🛠️ Adding New Broker Support

Want to add support for a broker? Follow these steps:

### 1. Create Implementation

```python
# brokers/implementations/yourbroker.py

from brokers.base import BaseBroker

class YourBrokerBroker(BaseBroker):
    def __init__(self, api_key, api_secret, access_token=None):
        super().__init__(api_key, api_secret, access_token)
        # Initialize your broker's SDK

    def place_order(self, ...):
        # Implement using your broker's API
        pass

    # Implement all other abstract methods
```

### 2. Register in Factory

```python
# brokers/factory.py

from brokers.implementations.yourbroker import YourBrokerBroker

BrokerFactory.register_broker('yourbroker', YourBrokerBroker)
```

### 3. Add Configuration

```yaml
# config/brokers.yaml

brokers:
  yourbroker:
    api_key: "..."
    api_secret: "..."
```

### 4. Use It

```python
broker = BrokerFactory.create_from_env('yourbroker')
```

---

## 📖 Example: Broker-Agnostic Strategy

```python
"""
Example: Multi-Broker Short Straddle Strategy
Works with ANY broker!
"""

import os
from datetime import datetime
from brokers import BrokerFactory

# Get broker from environment (or hardcode)
broker_name = os.getenv('DEFAULT_BROKER', 'zerodha')
broker = BrokerFactory.create_from_env(broker_name)

print(f"Using broker: {broker.broker_name}")

# Strategy parameters
underlying = 'BANKNIFTY'
atm_strike = 46000
quantity = 50

# Place short straddle
print("Entering short straddle...")

# Sell ATM Call
call_order_id = broker.place_order(
    symbol=f'{underlying}2412546000CE',
    exchange='NFO',
    transaction_type='SELL',
    quantity=quantity,
    order_type='MARKET',
    product_type='MIS'
)
print(f"Call sold: {call_order_id}")

# Sell ATM Put
put_order_id = broker.place_order(
    symbol=f'{underlying}2412546000PE',
    exchange='NFO',
    transaction_type='SELL',
    quantity=quantity,
    order_type='MARKET',
    product_type='MIS'
)
print(f"Put sold: {put_order_id}")

# Monitor positions
print("\nCurrent positions:")
positions = broker.get_positions()
for pos in positions:
    if underlying in pos.symbol:
        print(f"  {pos.symbol}: Qty={pos.quantity}, P&L=₹{pos.pnl:,.2f}")

# Get total P&L
total_pnl = sum(pos.pnl for pos in positions if underlying in pos.symbol)
print(f"\nTotal P&L: ₹{total_pnl:,.2f}")

# Square off if target/stop loss hit
if total_pnl >= 5000:
    print("Target hit! Squaring off...")
    for pos in positions:
        if underlying in pos.symbol:
            broker.square_off_position(
                symbol=pos.symbol,
                exchange=pos.exchange,
                product_type=pos.product_type
            )
```

---

## 🔐 Security Best Practices

1. **Never commit credentials**
   - Add `.env` and `brokers.yaml` to `.gitignore`
   - Use `.env.example` as template

2. **Use environment variables**
   - Preferred over config files
   - Easier to manage across environments

3. **Rotate tokens regularly**
   - Generate fresh access tokens daily
   - Don't hardcode tokens in scripts

4. **Limit permissions**
   - Use read-only API keys when possible
   - Create separate keys for testing

---

## 🐛 Troubleshooting

### Broker Not Found

```python
# Error: ValueError: Broker 'xyz' not found

# Solution: Check available brokers
from brokers import BrokerFactory
print(BrokerFactory.list_available_brokers())
# ['zerodha', 'upstox', 'kotak']
```

### Authentication Failed

```python
# Check configuration
from brokers.config import BrokerConfig

config = BrokerConfig.from_env('zerodha')
is_valid, error = config.validate()

if not is_valid:
    print(f"Config error: {error}")
```

### Method Not Implemented

```python
# Some brokers may not have all features implemented yet
# Check the implementation status in the class

broker = BrokerFactory.create_from_env('upstox')
try:
    broker.place_order(...)
except NotImplementedError as e:
    print(f"Feature not yet implemented: {e}")
```

---

## 📞 Support

- **Issues**: [GitHub Issues](https://github.com/buzzsubash/algo_trading_strategies_india/issues)
- **Email**: [PrajapatiBhavin1995@gmail.com](mailto:PrajapatiBhavin1995@gmail.com)
- **WhatsApp**: [+91 76004 60797](https://wa.me/917600460797)

---

## 🤝 Contributing

Want to add support for a broker? We welcome contributions!

1. Fork the repository
2. Create broker implementation
3. Add tests
4. Submit pull request

See [CONTRIBUTING.md](CONTRIBUTING.md) for details.

---

**Happy Trading with Multiple Brokers! 🚀📈**
