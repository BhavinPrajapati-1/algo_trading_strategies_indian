# 🚀 Complete Usage Guide - Short Straddle Trading System

**Universal Short Straddle Strategy with Historical Data & Backtesting**

This guide shows you how to use the complete end-to-end trading system that works with ANY broker (Upstox, Zerodha, Kotak, Angel One, etc.).

---

## 📋 Table of Contents

1. [Quick Start](#quick-start)
2. [System Overview](#system-overview)
3. [Prerequisites](#prerequisites)
4. [Step-by-Step Setup](#step-by-step-setup)
5. [Running the System](#running-the-system)
6. [Complete Workflow Examples](#complete-workflow-examples)
7. [Understanding the Output](#understanding-the-output)
8. [Troubleshooting](#troubleshooting)
9. [Advanced Usage](#advanced-usage)

---

## 🎯 Quick Start

**For the impatient CEO who wants to see it work NOW:**

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Copy and configure brokers.yaml
cp config/brokers.example.yaml config/brokers.yaml
# Edit config/brokers.yaml and add your access token

# 3. Run in paper trading mode (no real money)
python run_short_straddle.py --broker upstox --paper-trading --fetch-history

# 4. Watch the magic happen! ✨
```

---

## 🎨 System Overview

This system provides a **complete trading solution**:

```
┌─────────────────────────────────────────────────────────┐
│                    YOUR TRADING SYSTEM                  │
└─────────────────────────────────────────────────────────┘
                            │
        ┌───────────────────┼───────────────────┐
        │                   │                   │
        ▼                   ▼                   ▼
┌──────────────┐   ┌──────────────┐   ┌──────────────┐
│   BROKERS    │   │  HISTORICAL  │   │  STRATEGIES  │
│              │   │     DATA     │   │              │
│ • Upstox    │   │              │   │ • Short      │
│ • Zerodha   │◄──┤ • Fetching   │──►│   Straddle   │
│ • Kotak     │   │ • Storage    │   │ • Base       │
│ • Any Other │   │ • Caching    │   │   Framework  │
└──────────────┘   └──────────────┘   └──────────────┘
        │                   │                   │
        └───────────────────┼───────────────────┘
                            │
                            ▼
                   ┌──────────────┐
                   │  TELEGRAM    │
                   │ NOTIFICATIONS│
                   └──────────────┘
```

**Key Features:**
- 🔄 **Broker Agnostic**: Works with ANY broker
- 📊 **Historical Data**: Automatic fetching and SQLite storage
- 🎯 **Smart Strategies**: Options trading strategies (Short Straddle, more coming)
- 📱 **Real-time Alerts**: Telegram notifications for all events
- 🧪 **Paper Trading**: Test without risking real money
- ⚡ **Production Ready**: Full error handling and logging

---

## ✅ Prerequisites

### 1. Python Environment
- Python 3.8 or higher
- pip package manager

### 2. Broker Account & API Access
- Active broker account (Upstox/Zerodha/etc.)
- API credentials (API Key, API Secret)
- **Access Token** (Get using `get_upstox_token.py` for Upstox)

### 3. Telegram Bot (Optional but Recommended)
- Telegram bot token from @BotFather
- Your Telegram chat ID

### 4. System Requirements
- Internet connection
- ~100MB disk space for historical data
- Windows/Linux/Mac (cross-platform)

---

## 🔧 Step-by-Step Setup

### Step 1: Install Dependencies

```bash
# Clone the repository (if not already done)
cd algo_trading_strategies_indian

# Install all required packages
pip install -r requirements.txt
```

**Expected packages:**
- `upstox-python-sdk` - Upstox API client
- `kiteconnect` - Zerodha API client
- `python-telegram-bot` - Telegram notifications
- `pandas`, `numpy` - Data processing
- `PyYAML` - Configuration management
- And more...

### Step 2: Get Your Access Token

**For Upstox users:**

```bash
python get_upstox_token.py
```

Follow the interactive prompts:
1. Enter your API Key and Secret
2. Open the generated URL in your browser
3. Login and authorize
4. Copy the authorization code from the redirect URL
5. Paste it back into the terminal
6. **Save the access token** - you'll need it!

**For Zerodha users:**
- Use Kite Connect's login flow
- Or use their session management

### Step 3: Configure Brokers

```bash
# Copy the example config
cp config/brokers.example.yaml config/brokers.yaml

# Edit with your favorite editor
nano config/brokers.yaml
# or
code config/brokers.yaml
```

**Add your broker credentials:**

```yaml
# config/brokers.yaml

brokers:
  upstox:
    api_key: "your-api-key-here"
    api_secret: "your-api-secret-here"
    access_token: "YOUR-ACCESS-TOKEN-FROM-STEP-2"

  zerodha:
    api_key: "your-zerodha-api-key"
    api_secret: "your-zerodha-api-secret"
    access_token: "your-zerodha-access-token"

# Optional: Telegram notifications
telegram:
  enabled: true
  bot_token: "your-bot-token-from-botfather"
  chat_id: "your-telegram-chat-id"
  notifications:
    profit_threshold: 5000.0    # Notify when profit exceeds ₹5000
    loss_threshold: -2000.0     # Notify when loss exceeds ₹2000
```

**Important:**
- Never commit `config/brokers.yaml` to git (it's in .gitignore)
- Keep your tokens secure!
- Upstox tokens expire daily - regenerate each morning

### Step 4: Verify Setup

Test that everything is configured correctly:

```bash
# Quick verification - just fetch profile
python -c "
from pathlib import Path
import yaml
import sys
sys.path.insert(0, str(Path.cwd()))
from brokers import BrokerFactory

with open('config/brokers.yaml') as f:
    config = yaml.safe_load(f)

broker = BrokerFactory.create('upstox', config['brokers']['upstox'])
print(f'✅ Connected as: {broker.get_profile().get(\"user_name\", \"User\")}')
"
```

If you see your username, you're ready! 🎉

---

## 🎮 Running the System

### Basic Usage

```bash
python run_short_straddle.py [OPTIONS]
```

### Common Scenarios

#### 1. Paper Trading (RECOMMENDED FOR FIRST RUN)

Test the system without placing real orders:

```bash
python run_short_straddle.py \
    --broker upstox \
    --paper-trading \
    --fetch-history \
    --history-days 30
```

**What this does:**
- Connects to Upstox
- Fetches 30 days of historical data
- Simulates the short straddle strategy
- Shows you what WOULD happen (no real orders)
- Sends Telegram notifications (if configured)

#### 2. Live Trading with BANKNIFTY

When you're ready for real trading:

```bash
python run_short_straddle.py \
    --broker upstox \
    --symbol BANKNIFTY \
    --lots 1 \
    --stop-loss 5000 \
    --target 3000 \
    --entry-time 09:20 \
    --exit-time 15:15
```

**What this does:**
- Enters short straddle at 9:20 AM
- Sells 1 lot of ATM Call and Put
- Exits at 3:15 PM or when stop loss/target hit
- Real orders placed on Upstox!

#### 3. NIFTY Trading with 2 Lots

```bash
python run_short_straddle.py \
    --broker upstox \
    --symbol NIFTY \
    --lots 2 \
    --lot-size 50 \
    --stop-loss 8000 \
    --target 5000
```

#### 4. Fetch Historical Data Only

Just want to download and store data for analysis?

```bash
python run_short_straddle.py \
    --broker upstox \
    --symbol BANKNIFTY \
    --fetch-history \
    --history-days 60 \
    --paper-trading
```

Press Ctrl+C immediately after data is fetched.

---

## 📊 Complete Workflow Examples

### Example 1: CEO's Daily Trading Routine

**Morning (before market opens):**

```bash
# 1. Generate fresh access token (Upstox tokens expire daily)
python get_upstox_token.py
# Copy the token and update config/brokers.yaml

# 2. Fetch latest historical data
python run_short_straddle.py \
    --broker upstox \
    --fetch-history \
    --history-days 10 \
    --paper-trading
# Press Ctrl+C after data download completes
```

**Market Hours (9:00 AM onwards):**

```bash
# 3. Start live trading
python run_short_straddle.py \
    --broker upstox \
    --symbol BANKNIFTY \
    --lots 1 \
    --stop-loss 5000 \
    --target 3000 \
    --entry-time 09:20 \
    --exit-time 15:15
```

**What happens:**
- 9:00-9:20: System waits for entry time
- 9:20: Calculates ATM strike, sells Call and Put
- 9:20-15:15: Monitors positions every 30 seconds
  - Checks stop loss
  - Checks target
  - Updates you via Telegram
- 15:15: Automatically squares off all positions
- Sends final P&L summary via Telegram

**End of Day:**
- Review Telegram notifications
- Check `logs/short_straddle.log` for details
- Historical data stored in `data/historical_data.db`

### Example 2: Weekend Analysis & Backtesting

```bash
# Download entire week's data
python run_short_straddle.py \
    --broker upstox \
    --symbol BANKNIFTY \
    --fetch-history \
    --history-days 7 \
    --paper-trading

# Data is now in data/historical_data.db
# Use it for analysis with pandas:

python -c "
import sqlite3
import pandas as pd

conn = sqlite3.connect('data/historical_data.db')
df = pd.read_sql('SELECT * FROM historical_data WHERE symbol=\"BANKNIFTY\" ORDER BY timestamp DESC LIMIT 100', conn)
print(df.head())
print(f'\n📊 Total records: {len(df)}')
conn.close()
"
```

### Example 3: Multi-Broker Comparison

Test the same strategy on different brokers:

```bash
# Test with Upstox
python run_short_straddle.py --broker upstox --paper-trading

# Test with Zerodha
python run_short_straddle.py --broker zerodha --paper-trading

# Compare execution, data quality, speed, etc.
```

---

## 📈 Understanding the Output

### Console Output

```
================================================================================
🚀 UNIVERSAL SHORT STRADDLE STRATEGY
================================================================================
Broker: upstox
Symbol: BANKNIFTY
Lots: 1
Mode: PAPER TRADING
================================================================================

2024-01-15 09:15:32 - INFO - Initializing upstox broker...
2024-01-15 09:15:33 - INFO - ✅ Connected to upstox
2024-01-15 09:15:33 - INFO -    User: John Doe
2024-01-15 09:15:34 - INFO - Fetching historical data for BANKNIFTY...
2024-01-15 09:15:36 - INFO - ✅ Fetched 30 candles
2024-01-15 09:15:36 - INFO - Database stats:
2024-01-15 09:15:36 - INFO -   Total records: 150
2024-01-15 09:15:36 - INFO -   Unique symbols: 2
2024-01-15 09:15:36 - INFO -   Database: data/historical_data.db
2024-01-15 09:15:37 - INFO - Starting strategy...
2024-01-15 09:15:37 - INFO - Strategy running... Press Ctrl+C to stop

================================================================================
📊 STRATEGY MONITORING
================================================================================

[09:15:37] Status:
  Entry Done: False
  P&L: ₹0.00
  Positions: 0

[09:20:05] Status:
  Entry Done: True
  P&L: ₹1250.50
  Positions: 2
  Call: BANKNIFTY24JAN47000CE
  Put: BANKNIFTY24JAN47000PE
  Combined Premium: ₹385.50
```

### Telegram Notifications

You'll receive notifications for:
- 🚀 **Strategy Started**: Confirmation with parameters
- 📝 **Order Placed**: Each order with details
- ✅ **Position Opened**: Summary of the straddle
- 💰 **P&L Updates**: When crossing thresholds
- 🎯 **Target Hit**: Profit target reached
- 🛑 **Stop Loss Hit**: Risk limit reached
- 📊 **Daily Summary**: End-of-day P&L
- ❌ **Errors**: Any issues that occur

### Log Files

Detailed logs in `logs/short_straddle.log`:

```
2024-01-15 09:20:05,123 - strategies.short_straddle - INFO - Entry conditions met
2024-01-15 09:20:05,234 - strategies.short_straddle - INFO - Calculated positions: CALL=BANKNIFTY24JAN47000CE, PUT=BANKNIFTY24JAN47000PE, Qty=15
2024-01-15 09:20:06,345 - strategies.short_straddle - INFO - [PAPER] SELL BANKNIFTY24JAN47000CE: PAPER_1705302606.345
2024-01-15 09:20:06,456 - strategies.short_straddle - INFO - [PAPER] SELL BANKNIFTY24JAN47000PE: PAPER_1705302606.456
2024-01-15 09:20:06,567 - strategies.short_straddle - INFO - Combined premium received: ₹385.50
```

### Database

Historical data stored in SQLite (`data/historical_data.db`):

**Tables:**
1. `historical_data` - OHLC candles
2. `fetch_metadata` - Fetch history and stats

**Query examples:**

```sql
-- Get latest 100 candles for BANKNIFTY
SELECT * FROM historical_data
WHERE symbol='BANKNIFTY' AND exchange='NSE'
ORDER BY timestamp DESC LIMIT 100;

-- Get fetch statistics
SELECT symbol, COUNT(*) as records, MIN(timestamp), MAX(timestamp)
FROM historical_data
GROUP BY symbol;
```

---

## 🔧 Troubleshooting

### Problem: "ModuleNotFoundError: No module named 'brokers'"

**Solution:**
Always run from project root:

```bash
cd /path/to/algo_trading_strategies_indian
python run_short_straddle.py
```

Or use launcher scripts:
```bash
python run_examples.py upstox
```

### Problem: "Broker not authenticated"

**Solution:**
1. Verify access token in `config/brokers.yaml`
2. For Upstox, regenerate token: `python get_upstox_token.py`
3. Check token hasn't expired (Upstox tokens expire daily)

### Problem: "No data returned from broker"

**Possible causes:**
1. Market closed - historical data only available for past dates
2. Invalid symbol name
3. Exchange incorrect (NFO for options, NSE for stocks)
4. API rate limits hit

**Solution:**
- Check market hours
- Verify symbol: `BANKNIFTY` not `BANK NIFTY`
- Use correct exchange
- Add delays between requests

### Problem: "Could not find a suitable TLS CA certificate bundle"

**Solution:**
This is a PostgreSQL interference issue with pip. Use:

```bash
pip install -r requirements.txt --trusted-host pypi.org --trusted-host files.pythonhosted.org
```

### Problem: Strategy not entering positions

**Check:**
1. Current time vs entry time
2. Market holiday? (weekends, NSE holidays)
3. Is it a valid trading day?
4. Check logs for specific errors

### Problem: Orders not going through

**Paper Trading:**
- This is normal! Paper trading doesn't place real orders
- Remove `--paper-trading` flag for live trading

**Live Trading:**
- Check available margin
- Verify RMS limits
- Check order logs for rejection reasons
- Ensure exchange is open

---

## 🎓 Advanced Usage

### Custom Entry/Exit Times

```bash
python run_short_straddle.py \
    --entry-time 10:00 \
    --exit-time 14:30
```

### Different Strike Selection

```bash
# 100 points OTM
python run_short_straddle.py --strike-points -100

# 100 points ITM
python run_short_straddle.py --strike-points 100

# ATM (default)
python run_short_straddle.py --strike-points 0
```

### Cycle Interval (Monitoring Frequency)

```bash
# Check every 10 seconds (more responsive, more API calls)
python run_short_straddle.py --cycle-interval 10

# Check every 60 seconds (fewer API calls, slower response)
python run_short_straddle.py --cycle-interval 60
```

### Disable Telegram Notifications

```bash
python run_short_straddle.py --no-telegram
```

### Multiple Lot Sizes

```bash
# NIFTY: 50 units per lot
python run_short_straddle.py --symbol NIFTY --lot-size 50 --lots 2

# BANKNIFTY: 15 units per lot (default)
python run_short_straddle.py --symbol BANKNIFTY --lot-size 15 --lots 3

# FINNIFTY: 40 units per lot
python run_short_straddle.py --symbol FINNIFTY --lot-size 40 --lots 1
```

### Force Refresh Historical Data

By default, the system caches historical data. To force re-download:

```python
from utils.historical_data import HistoricalDataFetcher
from brokers import BrokerFactory

broker = BrokerFactory.create_from_config('upstox', 'config/brokers.yaml')
fetcher = HistoricalDataFetcher(broker)

# Force refresh
fetcher.fetch_and_store(
    symbol='BANKNIFTY',
    exchange='NSE',
    from_date='2024-01-01',
    to_date='2024-01-15',
    interval='day',
    force_refresh=True  # ← This forces re-download
)
```

### Clear Cache

```python
from utils.historical_data import HistoricalDataFetcher
from brokers import BrokerFactory

broker = BrokerFactory.create_from_config('upstox', 'config/brokers.yaml')
fetcher = HistoricalDataFetcher(broker)

# Clear specific symbol
fetcher.clear_cache(symbol='BANKNIFTY', exchange='NSE')

# Clear everything
fetcher.clear_cache()
```

---

## 📝 All Command-Line Options

```bash
python run_short_straddle.py --help
```

**Output:**

```
usage: run_short_straddle.py [-h] [--broker BROKER] [--symbol SYMBOL]
                             [--exchange EXCHANGE] [--lots LOTS]
                             [--lot-size LOT_SIZE] [--strike-points STRIKE_POINTS]
                             [--entry-time ENTRY_TIME] [--exit-time EXIT_TIME]
                             [--stop-loss STOP_LOSS] [--target TARGET]
                             [--position-type POSITION_TYPE] [--fetch-history]
                             [--history-days HISTORY_DAYS] [--no-telegram]
                             [--paper-trading] [--cycle-interval CYCLE_INTERVAL]

Universal Short Straddle Strategy - Works with any broker!

optional arguments:
  -h, --help            show this help message and exit
  --broker BROKER       Broker name (upstox, zerodha, kotak, etc.)
  --symbol SYMBOL       Index symbol (BANKNIFTY, NIFTY, FINNIFTY, SENSEX)
  --exchange EXCHANGE   Exchange (NFO, BFO)
  --lots LOTS           Number of lots to trade
  --lot-size LOT_SIZE   Lot size (15 for BANKNIFTY, 50 for NIFTY, etc.)
  --strike-points STRIKE_POINTS
                        Strike points from ATM (0=ATM, +ve=ITM, -ve=OTM)
  --entry-time ENTRY_TIME
                        Entry time (HH:MM)
  --exit-time EXIT_TIME
                        Exit time (HH:MM)
  --stop-loss STOP_LOSS
                        Stop loss in rupees
  --target TARGET       Profit target in rupees
  --position-type POSITION_TYPE
                        Position type (MIS/NRML/CNC)
  --fetch-history       Fetch historical data before running
  --history-days HISTORY_DAYS
                        Number of days of history to fetch
  --no-telegram         Disable Telegram notifications
  --paper-trading       Enable paper trading (no real orders)
  --cycle-interval CYCLE_INTERVAL
                        Strategy cycle interval in seconds
```

---

## 🎯 Success Checklist

Before going live, ensure:

- [ ] Dependencies installed (`pip install -r requirements.txt`)
- [ ] Access token generated and added to `config/brokers.yaml`
- [ ] Telegram bot configured (optional but recommended)
- [ ] Paper trading tested successfully
- [ ] Historical data fetched and stored
- [ ] Logs directory exists and writable
- [ ] Sufficient margin in trading account
- [ ] Understanding of short straddle risks
- [ ] Market timing understood (entry/exit times)
- [ ] Stop loss and target configured appropriately

---

## 🏆 Best Practices

1. **Always Start with Paper Trading**
   - Test thoroughly before risking real money
   - Verify Telegram notifications work
   - Understand the timing and flow

2. **Daily Token Refresh** (Upstox)
   - Run `get_upstox_token.py` every morning
   - Update `config/brokers.yaml` before trading

3. **Monitor Actively**
   - Keep Telegram notifications enabled
   - Check logs periodically
   - Don't assume everything works - verify!

4. **Risk Management**
   - Always use stop loss
   - Start with 1 lot
   - Don't over-leverage

5. **Data Management**
   - Fetch historical data regularly
   - Backup `data/historical_data.db` weekly
   - Clear old data if storage is limited

6. **Keep Config Secure**
   - Never commit `config/brokers.yaml` to git
   - Use environment variables for production
   - Rotate API keys periodically

---

## 📚 File Structure

```
algo_trading_strategies_indian/
├── run_short_straddle.py          ← Main execution script (START HERE)
├── get_upstox_token.py             ← Token generator for Upstox
├── requirements.txt                ← Python dependencies
├── COMPLETE_USAGE_GUIDE.md         ← This file!
│
├── config/
│   ├── brokers.yaml                ← Your credentials (create from example)
│   └── brokers.example.yaml        ← Template
│
├── brokers/
│   ├── base.py                     ← Abstract broker interface
│   ├── factory.py                  ← Broker factory
│   └── implementations/
│       ├── upstox.py               ← Upstox implementation
│       └── zerodha.py              ← Zerodha implementation
│
├── strategies/
│   ├── base_strategy.py            ← Abstract strategy base class
│   └── short_straddle.py           ← Short straddle implementation
│
├── utils/
│   └── historical_data.py          ← Data fetcher and storage
│
├── notifications/
│   ├── telegram_bot.py             ← Telegram notifier
│   └── broker_notifier.py          ← Broker + Telegram integration
│
├── data/
│   └── historical_data.db          ← SQLite database (auto-created)
│
└── logs/
    └── short_straddle.log          ← Execution logs (auto-created)
```

---

## 🎉 Conclusion

You now have a **complete, production-ready** trading system that:

✅ Works with **ANY broker** (truly broker-agnostic)
✅ **Fetches and stores** historical data automatically
✅ Implements **smart options strategies** (Short Straddle + more coming)
✅ **Notifies you instantly** via Telegram
✅ Includes **paper trading** for safe testing
✅ Has **comprehensive risk management**
✅ Is **fully configurable** via command-line
✅ Provides **detailed logging** for analysis

**The system works like MAGIC! ✨**

Start with paper trading, understand the flow, then gradually move to live trading with small sizes.

---

## 📞 Support & Resources

- **Documentation**: Read all `.md` files in the repo
- **Examples**: Check `examples/` directory
- **Logs**: Always check `logs/short_straddle.log` for details
- **Broker Docs**:
  - Upstox: https://upstox.com/developer/api-documentation
  - Zerodha: https://kite.trade/docs/connect/v3/

---

**Happy Trading! 🚀📈💰**

*Remember: Trading involves risk. Never trade with money you can't afford to lose. This system is a tool - your judgment and risk management are paramount.*
