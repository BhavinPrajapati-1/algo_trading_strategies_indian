# Running Guide - How to Execute Scripts and Utilities

This guide explains how to run various components of the algo trading system without encountering import errors.

## 🎯 Quick Start

### Running the Dashboard

```bash
# Method 1: Using the launcher script (Recommended)
python run_dashboard.py

# Method 2: As a module
python -m utils.dashboard

# Method 3: With custom host/port
python run_dashboard.py --host 0.0.0.0 --port 8080

# Method 4: With debug mode
python run_dashboard.py --debug
```

### Running Examples

```bash
# List all available examples
python run_examples.py list

# Run specific example
python run_examples.py analytics
python run_examples.py upstox
python run_examples.py symbol_select

# Or run directly as modules
python -m examples.analytics_demo
python -m examples.upstox_telegram_example
python -m examples.dynamic_symbol_selection_strategy
```

---

## 📚 Understanding Python Import Errors

### Why `ModuleNotFoundError: No module named 'utils'` Occurs

When you run a Python file directly like this:
```bash
python ./utils/dashboard.py  # ❌ This causes the error
```

Python doesn't automatically add the parent directory to the Python path, so it can't find the `utils` module.

### The Solutions

#### Solution 1: Use Launcher Scripts ✅ (Best)

We've created launcher scripts that handle the Python path automatically:

```bash
python run_dashboard.py        # For dashboard
python run_examples.py         # For examples
```

#### Solution 2: Run as Module ✅

Always run from the project root as a module:

```bash
cd /path/to/algo_trading_strategies_indian
python -m utils.dashboard
python -m examples.analytics_demo
```

#### Solution 3: Set PYTHONPATH ✅

Add the project root to PYTHONPATH:

**Linux/Mac:**
```bash
export PYTHONPATH=$PYTHONPATH:/path/to/algo_trading_strategies_indian
python utils/dashboard.py
```

**Windows (CMD):**
```cmd
set PYTHONPATH=%PYTHONPATH%;C:\path\to\algo_trading_strategies_indian
python utils\dashboard.py
```

**Windows (PowerShell):**
```powershell
$env:PYTHONPATH += ";C:\path\to\algo_trading_strategies_indian"
python utils\dashboard.py
```

---

## 🚀 Running Different Components

### 1. Trading Dashboard

The dashboard provides a web interface for analytics:

```bash
# Basic usage
python run_dashboard.py

# Custom configuration
python run_dashboard.py --host 127.0.0.1 --port 5000 --debug
```

**Access:** Open browser to `http://127.0.0.1:5000/`

### 2. Analytics Demo

Demonstrates all analytics features:

```bash
python run_examples.py analytics

# Or as module
python -m examples.analytics_demo
```

### 3. Upstox + Telegram Example

Shows Upstox broker integration with Telegram notifications:

```bash
python run_examples.py upstox

# Or as module
python -m examples.upstox_telegram_example
```

**Prerequisites:**
- Set environment variables:
  ```bash
  export UPSTOX_API_KEY="your_key"
  export UPSTOX_API_SECRET="your_secret"
  export TELEGRAM_BOT_TOKEN="your_token"
  export TELEGRAM_CHAT_ID="your_chat_id"
  ```

### 4. Symbol Selection Strategy

Dynamic symbol selection example:

```bash
python run_examples.py symbol_select

# Or as module
python -m examples.dynamic_symbol_selection_strategy
```

### 5. Backtesting

Run backtests programmatically:

```python
import sys
sys.path.insert(0, '/path/to/project')

from utils.backtester import Backtester
from brokers import BrokerFactory

broker = BrokerFactory.create_from_env('zerodha')
backtester = Backtester(broker)
# ... run backtest
```

### 6. Report Generation

Generate trading reports:

```python
import sys
sys.path.insert(0, '/path/to/project')

from utils.report_generator import ReportGenerator

generator = ReportGenerator()
daily_report = generator.generate_daily_report()
weekly_report = generator.generate_weekly_report()
monthly_report = generator.generate_monthly_report()
```

---

## 🐍 Running from Python Scripts

If you're importing these modules in your own scripts:

```python
#!/usr/bin/env python3
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.absolute()
sys.path.insert(0, str(project_root))

# Now you can import
from brokers import BrokerFactory
from notifications import TelegramNotifier
from utils.backtester import Backtester
from utils.dashboard import app

# Your code here...
```

---

## 📦 Working with Brokers

### Using Upstox Broker

```python
import sys
sys.path.insert(0, '/path/to/project')

from brokers import BrokerFactory
from notifications import TelegramNotifier
from notifications.broker_notifier import BrokerNotifier

# Initialize
broker = BrokerFactory.create_from_env('upstox')
telegram = TelegramNotifier(bot_token, chat_id)
notifier = BrokerNotifier(broker, telegram)

# Trade with notifications
order_id = notifier.place_order(
    symbol="RELIANCE",
    exchange="NSE",
    transaction_type="BUY",
    quantity=1,
    order_type="MARKET"
)
```

### Using Zerodha Broker

```python
import sys
sys.path.insert(0, '/path/to/project')

from brokers import BrokerFactory

broker = BrokerFactory.create_from_env('zerodha')
positions = broker.get_positions()
```

---

## 🔧 Troubleshooting

### Problem: `ModuleNotFoundError: No module named 'utils'`

**Solutions:**
1. Use launcher scripts: `python run_dashboard.py`
2. Run as module: `python -m utils.dashboard`
3. Set PYTHONPATH (see above)

### Problem: `ImportError: No module named 'dotenv'`

**Solution:**
```bash
pip install -r requirements.txt
```

### Problem: `ModuleNotFoundError: No module named 'brokers'`

**Solution:**
Make sure you're running from the project root:
```bash
cd /path/to/algo_trading_strategies_indian
python -m your_script
```

### Problem: Dashboard shows blank page

**Solution:**
Check if all dependencies are installed:
```bash
pip install Flask matplotlib plotly jinja2
```

---

## 📂 Project Structure

Understanding the structure helps avoid import issues:

```
algo_trading_strategies_indian/
├── run_dashboard.py          # ← Launcher for dashboard
├── run_examples.py            # ← Launcher for examples
├── brokers/                   # Broker implementations
│   ├── __init__.py
│   ├── base.py
│   ├── factory.py
│   └── implementations/
│       ├── upstox.py
│       └── zerodha.py
├── notifications/             # Telegram notifications
│   ├── __init__.py
│   ├── telegram_bot.py
│   └── broker_notifier.py
├── utils/                     # Analytics utilities
│   ├── backtester.py
│   ├── dashboard.py
│   ├── report_generator.py
│   └── strategy_analyzer.py
├── examples/                  # Example scripts
│   ├── analytics_demo.py
│   ├── upstox_telegram_example.py
│   └── dynamic_symbol_selection_strategy.py
└── requirements.txt
```

---

## 💡 Best Practices

1. **Always run from project root:**
   ```bash
   cd /path/to/algo_trading_strategies_indian
   python -m module.name
   ```

2. **Use launcher scripts when available:**
   ```bash
   python run_dashboard.py
   python run_examples.py analytics
   ```

3. **For custom scripts, add this at the top:**
   ```python
   import sys
   from pathlib import Path
   sys.path.insert(0, str(Path(__file__).parent.absolute()))
   ```

4. **Virtual environment is recommended:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # Linux/Mac
   # or
   venv\Scripts\activate  # Windows
   pip install -r requirements.txt
   ```

---

## 🎓 Summary

| What You Want | How to Run |
|---------------|------------|
| Dashboard | `python run_dashboard.py` |
| Analytics demo | `python run_examples.py analytics` |
| Upstox example | `python run_examples.py upstox` |
| Any utility | `python -m utils.module_name` |
| Any example | `python -m examples.example_name` |
| Custom script | Add `sys.path.insert(0, project_root)` at top |

**Remember:** The key is to ensure Python knows where to find the project modules!

---

For more help, see:
- `docs/UPSTOX_TELEGRAM_GUIDE.md` - Upstox & Telegram setup
- `MULTI_BROKER_GUIDE.md` - Multi-broker architecture
- `TRADING_ANALYTICS.md` - Analytics features
