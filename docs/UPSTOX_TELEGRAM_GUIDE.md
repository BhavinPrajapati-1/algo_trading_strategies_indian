# Upstox Broker & Telegram Notifications Guide

Complete guide for using the Upstox broker implementation with Telegram notifications for real-time trading alerts.

## Table of Contents

1. [Overview](#overview)
2. [Prerequisites](#prerequisites)
3. [Installation](#installation)
4. [Upstox Setup](#upstox-setup)
5. [Telegram Bot Setup](#telegram-bot-setup)
6. [Configuration](#configuration)
7. [Usage Examples](#usage-examples)
8. [Notification Types](#notification-types)
9. [Troubleshooting](#troubleshooting)

---

## Overview

This implementation provides:

- **Complete Upstox API v2 integration** following the multi-broker architecture
- **Real-time Telegram notifications** for all trading events
- **Automated monitoring** of orders, positions, and P&L
- **Customizable alerts** with thresholds
- **Easy integration** with existing strategies

### Features

#### Upstox Broker Features
- ✅ Full OAuth 2.0 authentication
- ✅ Order placement (MARKET, LIMIT, SL, SL-M)
- ✅ Order modification and cancellation
- ✅ Position and holdings management
- ✅ Real-time market quotes and LTP
- ✅ Historical data retrieval
- ✅ Margin and profile information
- ✅ Multiple exchanges (NSE, BSE, NFO, BFO, MCX, CDS)

#### Telegram Notification Features
- 📤 Order placed notifications
- ✅ Order execution alerts
- ❌ Order cancellation/rejection alerts
- 📈 Position opened notifications
- 📉 Position closed with P&L
- 💰 Profit threshold alerts
- ⚠️ Loss threshold alerts
- 📊 Daily trading summary
- 🚨 Error and system notifications
- 📢 Custom messages

---

## Prerequisites

### 1. Upstox Account
- Active Upstox trading account
- API access enabled
- API credentials (API Key and API Secret)

### 2. Telegram Account
- Telegram account
- Telegram bot token
- Your Telegram chat ID

### 3. Python Environment
- Python 3.8 or higher
- pip package manager

---

## Installation

### 1. Install Required Packages

```bash
# Install Upstox Python SDK
pip install upstox-python-sdk

# Install Telegram bot library
pip install python-telegram-bot

# Optional: Install other dependencies
pip install pyyaml requests
```

### 2. Verify Installation

```python
import upstox_client
import telegram
print("✅ All packages installed successfully!")
```

---

## Upstox Setup

### Step 1: Create Upstox App

1. Visit [Upstox Developer Portal](https://upstox.com/developer/)
2. Log in with your Upstox credentials
3. Navigate to "My Apps"
4. Click "Create App"
5. Fill in app details:
   - **App Name**: Your app name (e.g., "My Trading Bot")
   - **Redirect URI**: `http://127.0.0.1:5000/callback`
   - **Description**: Brief description
6. Click "Create"
7. Note down:
   - **API Key** (Client ID)
   - **API Secret** (Client Secret)

### Step 2: Get Access Token

The access token is generated through OAuth 2.0 flow:

```python
from brokers.implementations.upstox import UpstoxBroker

# Initialize broker
broker = UpstoxBroker(
    api_key="your_api_key",
    api_secret="your_api_secret"
)

# Generate login URL
broker.login(redirect_uri="http://127.0.0.1:5000/callback")
# This will print a URL - open it in browser

# After login, copy the authorization code from redirect URL
authorization_code = "code_from_redirect_url"

# Generate access token
access_token = broker.get_access_token(
    authorization_code,
    redirect_uri="http://127.0.0.1:5000/callback"
)

# Set token
broker.set_access_token(access_token)
print(f"Access Token: {access_token}")
```

**Note:** Access tokens are valid for one trading day. You need to regenerate them daily.

### Step 3: Save Credentials

Store your credentials securely:

**Option 1: Environment Variables**

```bash
export UPSTOX_API_KEY="your_api_key"
export UPSTOX_API_SECRET="your_api_secret"
export UPSTOX_ACCESS_TOKEN="your_access_token"
```

**Option 2: Configuration File**

Edit `config/brokers.yaml`:

```yaml
brokers:
  upstox:
    api_key: "your_api_key"
    api_secret: "your_api_secret"
    access_token: "your_access_token"
```

---

## Telegram Bot Setup

### Step 1: Create Telegram Bot

1. Open Telegram and search for `@BotFather`
2. Start a chat and send `/newbot`
3. Follow the prompts:
   - Choose a name for your bot (e.g., "My Trading Bot")
   - Choose a username (must end with `bot`, e.g., "mytradingbot123_bot")
4. BotFather will give you a **bot token** - save it securely

Example token: `1234567890:ABCdefGHIjklMNOpqrsTUVwxyz`

### Step 2: Get Your Chat ID

1. Start a chat with your newly created bot
2. Send any message to the bot
3. Visit: `https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getUpdates`
4. Look for `"chat":{"id":123456789}`
5. Note down your **chat ID** (it's a number)

**Alternative Method:**

1. Search for `@userinfobot` on Telegram
2. Start a chat
3. It will reply with your chat ID

### Step 3: Test Bot Connection

```python
from notifications import TelegramNotifier

notifier = TelegramNotifier(
    bot_token="your_bot_token",
    chat_id="your_chat_id"
)

# Test connection
if notifier.test_connection():
    print("✅ Telegram bot working!")
else:
    print("❌ Connection failed")
```

### Step 4: Save Telegram Credentials

**Option 1: Environment Variables**

```bash
export TELEGRAM_BOT_TOKEN="your_bot_token"
export TELEGRAM_CHAT_ID="your_chat_id"
```

**Option 2: Configuration File**

Edit `config/brokers.yaml`:

```yaml
telegram:
  enabled: true
  bot_token: "your_bot_token"
  chat_id: "your_chat_id"
  notifications:
    notify_orders: true
    notify_positions: true
    notify_pnl: true
    profit_threshold: 5000.0
    loss_threshold: -2000.0
```

---

## Configuration

### Complete Configuration Example

Create `config/brokers.yaml`:

```yaml
# Broker Configuration
brokers:
  upstox:
    api_key: "your_upstox_api_key"
    api_secret: "your_upstox_api_secret"
    access_token: null  # Generated daily
    timeout: 7

# Telegram Configuration
telegram:
  enabled: true
  bot_token: "your_telegram_bot_token"
  chat_id: "your_telegram_chat_id"

  notifications:
    # Order notifications
    notify_orders: true
    notify_order_placed: true
    notify_order_executed: true
    notify_order_cancelled: true
    notify_order_rejected: true

    # Position notifications
    notify_positions: true
    notify_position_opened: true
    notify_position_closed: true

    # P&L alerts
    notify_pnl: true
    profit_threshold: 5000.0   # Alert at ₹5,000 profit
    loss_threshold: -2000.0    # Alert at ₹2,000 loss

    # Daily summary
    send_daily_summary: true
    daily_summary_time: "15:30"

    # Error notifications
    notify_errors: true
```

---

## Usage Examples

### Example 1: Basic Usage

```python
from brokers import BrokerFactory
from notifications import TelegramNotifier
from notifications.broker_notifier import BrokerNotifier

# Initialize broker
broker = BrokerFactory.create_from_env('upstox')

# Initialize Telegram
telegram = TelegramNotifier(
    bot_token="your_token",
    chat_id="your_chat_id"
)

# Create notifier wrapper
notifier = BrokerNotifier(broker, telegram)

# Place order with automatic notification
order_id = notifier.place_order(
    symbol="RELIANCE",
    exchange="NSE",
    transaction_type="BUY",
    quantity=1,
    order_type="MARKET",
    product_type="I"  # Intraday
)

print(f"Order placed: {order_id}")
# Notification sent automatically to Telegram!
```

### Example 2: Position Monitoring

```python
import time

# Monitor positions continuously
while True:
    # Get and check positions
    positions = notifier.monitor_positions(check_thresholds=True)

    for pos in positions:
        print(f"{pos.symbol}: P&L = ₹{pos.pnl:.2f}")

    # Check if profit/loss thresholds reached
    # Automatic notifications will be sent

    time.sleep(30)  # Check every 30 seconds
```

### Example 3: Manual Notifications

```python
# Send custom notification
telegram.notify_custom(
    message="Market looks bullish today!",
    title="Market Analysis"
)

# Send profit alert
telegram.notify_profit_alert(
    current_pnl=6500.0,
    total_trades=15,
    winning_trades=10
)

# Send loss alert
telegram.notify_loss_alert(
    current_pnl=-2500.0,
    max_loss=-2000.0,
    recommendation="Stop trading and review strategy"
)

# Send error notification
telegram.notify_error(
    error_message="API connection timeout",
    error_type="Connection Error"
)
```

### Example 4: Daily Summary

```python
# At end of trading day
notifier.send_daily_summary(
    total_trades=20,
    winning_trades=13,
    losing_trades=7,
    gross_profit=12500.0,
    gross_loss=-4200.0,
    largest_win=2800.0,
    largest_loss=-1500.0
)
```

### Example 5: Complete Trading Bot

```python
import logging
from datetime import datetime
import time

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def trading_bot():
    """Simple trading bot with notifications."""

    # Initialize
    broker = BrokerFactory.create_from_env('upstox')
    telegram = TelegramNotifier(
        bot_token=os.getenv('TELEGRAM_BOT_TOKEN'),
        chat_id=os.getenv('TELEGRAM_CHAT_ID'),
        profit_threshold=5000.0,
        loss_threshold=-2000.0
    )
    bot = BrokerNotifier(broker, telegram)

    # Startup notification
    telegram.notify_system_info("Trading bot started!", "Bot Startup")

    try:
        while True:
            # Monitor positions and orders
            positions = bot.monitor_positions(check_thresholds=True)
            orders = bot.monitor_orders(notify_on_execution=True)

            # Your trading logic here
            # ...

            time.sleep(30)  # Wait 30 seconds

    except KeyboardInterrupt:
        telegram.notify_system_info("Bot stopped by user", "Bot Shutdown")
    except Exception as e:
        logger.error(f"Bot error: {e}", exc_info=True)
        telegram.notify_error(str(e), "Bot Error")

if __name__ == "__main__":
    trading_bot()
```

---

## Notification Types

### 1. Order Notifications

#### Order Placed
```
📤 Order Placed

Symbol: RELIANCE
Type: BUY
Quantity: 10
Order Type: LIMIT
Price: ₹2,450.50
Order ID: 240312000123456

Time: 2024-03-12 09:30:15
```

#### Order Executed
```
✅ Order Executed

Symbol: RELIANCE
Type: BUY
Quantity: 10
Avg Price: ₹2,449.75
Total Value: ₹24,497.50
Order ID: 240312000123456

Time: 2024-03-12 09:30:45
```

### 2. Position Notifications

#### Position Opened
```
📈 Position Opened

Symbol: NIFTY24MAR21000CE
Quantity: 50
Entry Price: ₹125.50
Position Value: ₹6,275.00

Time: 2024-03-12 10:15:30
```

#### Position Closed
```
📉 Position Closed 💰

Symbol: NIFTY24MAR21000CE
Quantity: 50
Entry: ₹125.50
Exit: ₹132.75
P&L: ₹362.50 (+5.77%)

Time: 2024-03-12 14:45:20
```

### 3. P&L Alerts

#### Profit Alert
```
💰 Profit Alert

Current P&L: ₹5,250.00
Total Trades: 12
Winning Trades: 8
Win Rate: 66.7%

Congratulations! You've reached your profit target! 🎉

Time: 2024-03-12 13:30:00
```

#### Loss Alert
```
⚠️ Loss Alert

Current P&L: ₹-2,150.00
Max Loss Threshold: ₹-2,000.00

⚠️ Warning: Loss threshold breached!

Recommendation: Consider stopping trading for the day

Time: 2024-03-12 11:45:00
```

### 4. Daily Summary

```
📊 Daily Summary 💰

Date: 2024-03-12

Overall Performance:
• Total P&L: ₹4,350.00
• Total Trades: 18
• Win Rate: 61.1%

Trade Breakdown:
• Winning: 11 (₹7,200.00)
• Losing: 7 (₹-2,850.00)

Statistics:
• Avg Win: ₹654.55
• Avg Loss: ₹-407.14
• Largest Win: ₹1,250.00
• Largest Loss: ₹-850.00

Time: 15:30:00
```

---

## Troubleshooting

### Common Issues

#### 1. Upstox Authentication Errors

**Problem:** "Access token invalid or expired"

**Solution:**
- Upstox access tokens expire daily
- Generate a new token at the start of each trading day
- Implement automatic token refresh in production

```python
# Check if authenticated
if not broker.is_authenticated:
    # Re-authenticate
    authorization_code = get_new_authorization_code()
    access_token = broker.get_access_token(authorization_code)
    broker.set_access_token(access_token)
```

#### 2. Telegram Connection Failed

**Problem:** "Failed to send Telegram message"

**Solution:**
- Verify bot token is correct
- Verify chat ID is correct
- Ensure bot is not blocked
- Check internet connection
- Start a chat with your bot first

```python
# Test connection
notifier = TelegramNotifier(bot_token, chat_id)
if notifier.test_connection():
    print("Connected!")
else:
    print("Check credentials")
```

#### 3. Order Placement Errors

**Problem:** "Order rejected - Insufficient margins"

**Solution:**
- Check account margins before placing orders
- Use smaller position sizes
- Ensure sufficient funds in trading account

```python
# Check margins
margins = broker.get_margins()
print(f"Available: ₹{margins.available_cash}")
```

#### 4. Rate Limiting

**Problem:** "Too many API calls"

**Solution:**
- Implement delays between API calls
- Use caching for static data
- Monitor API usage limits

```python
import time

# Add delay between calls
time.sleep(1)  # 1 second delay
```

#### 5. Module Import Errors

**Problem:** "ModuleNotFoundError: No module named 'upstox_client'"

**Solution:**
```bash
pip install upstox-python-sdk python-telegram-bot
```

### Debug Mode

Enable detailed logging:

```python
import logging

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
```

### Support

For issues:
- Check [Upstox API Documentation](https://upstox.com/developer/api-documentation/)
- Check [python-telegram-bot Documentation](https://docs.python-telegram-bot.org/)
- Review logs in `logs/broker.log`
- Raise an issue on GitHub

---

## Security Best Practices

1. **Never commit credentials**
   - Add `config/brokers.yaml` to `.gitignore`
   - Use environment variables for sensitive data

2. **Secure token storage**
   - Store tokens encrypted
   - Use secure key management systems
   - Rotate credentials regularly

3. **Telegram bot security**
   - Keep bot token private
   - Don't share chat ID publicly
   - Use bot only for personal notifications

4. **API access**
   - Use HTTPS only
   - Monitor API usage
   - Set up IP whitelisting if available

---

## Advanced Features

### Async Notifications

For high-frequency trading, use async notifications:

```python
import asyncio

async def place_order_async():
    order_id = await broker.place_order_async(...)
    await telegram.send_message(...)

asyncio.run(place_order_async())
```

### Custom Message Formatting

Customize notification messages:

```python
def custom_order_notification(order):
    message = f"""
🎯 **Trade Alert**

Action: {order.transaction_type}
Symbol: {order.symbol}
Quantity: {order.quantity}
Price: ₹{order.price:.2f}

#trading #{order.symbol}
"""
    telegram.notify_custom(message)
```

### Integration with Trading Strategies

```python
from strategies.your_strategy import YourStrategy

strategy = YourStrategy(broker_notifier=notifier)
strategy.run()
```

---

## Conclusion

You now have a fully functional Upstox broker integration with Telegram notifications! This setup provides:

- ✅ Real-time trading capabilities
- ✅ Instant mobile notifications
- ✅ Automated monitoring
- ✅ Risk management alerts
- ✅ Performance tracking

Happy Trading! 🚀📈💰

---

**Disclaimer:** Trading in financial markets involves risk. This code is for educational purposes. Always test thoroughly in paper trading before using real money. The authors are not responsible for any financial losses.
