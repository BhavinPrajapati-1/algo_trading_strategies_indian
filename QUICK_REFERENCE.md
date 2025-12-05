# ⚡ Quick Reference Card

**Fast lookup for common commands and configurations**

---

## 🚀 Most Common Commands

### First-Time Setup
```bash
pip install -r requirements.txt
cp config/brokers.example.yaml config/brokers.yaml
python get_upstox_token.py
# Edit config/brokers.yaml with your token
```

### Daily Paper Trading
```bash
python run_short_straddle.py --broker upstox --paper-trading --fetch-history
```

### Daily Live Trading
```bash
python run_short_straddle.py --broker upstox --lots 1 --stop-loss 5000 --target 3000
```

---

## 📊 Symbol Configurations

| Symbol | Exchange | Lot Size | Expiry | Strike Interval |
|--------|----------|----------|--------|-----------------|
| BANKNIFTY | NFO | 15 | Wednesday | 100 |
| NIFTY | NFO | 50 | Thursday | 50 |
| FINNIFTY | NFO | 40 | Tuesday | 50 |
| SENSEX | BFO | 10 | Last Thursday | 100 |

---

## 🎛️ Common Parameter Combinations

### Conservative (Small Risk)
```bash
python run_short_straddle.py \
  --broker upstox \
  --lots 1 \
  --stop-loss 3000 \
  --target 2000 \
  --entry-time 10:00 \
  --exit-time 14:30
```

### Aggressive (Higher Risk)
```bash
python run_short_straddle.py \
  --broker upstox \
  --lots 2 \
  --stop-loss 8000 \
  --target 5000 \
  --entry-time 09:20 \
  --exit-time 15:15
```

### NIFTY Trading
```bash
python run_short_straddle.py \
  --broker upstox \
  --symbol NIFTY \
  --lot-size 50 \
  --lots 1 \
  --stop-loss 5000 \
  --target 3000
```

---

## 🔑 Config File Template

```yaml
# config/brokers.yaml

brokers:
  upstox:
    api_key: "your-api-key"
    api_secret: "your-api-secret"
    access_token: "your-access-token"  # Update daily!

telegram:
  enabled: true
  bot_token: "bot-token-from-botfather"
  chat_id: "your-chat-id"
  notifications:
    profit_threshold: 5000.0
    loss_threshold: -2000.0
```

---

## 🐛 Quick Troubleshooting

| Problem | Solution |
|---------|----------|
| "Broker not authenticated" | Regenerate token: `python get_upstox_token.py` |
| "ModuleNotFoundError" | Run from project root directory |
| "No data returned" | Check symbol name and exchange |
| Token expired | Upstox tokens expire daily - regenerate each morning |
| Orders not placing | Remove `--paper-trading` flag for live trading |

---

## 📁 Important Files

| File | Purpose |
|------|---------|
| `run_short_straddle.py` | Main execution script |
| `get_upstox_token.py` | Generate Upstox access token |
| `config/brokers.yaml` | Your credentials (never commit!) |
| `data/historical_data.db` | Historical data storage |
| `logs/short_straddle.log` | Execution logs |
| `COMPLETE_USAGE_GUIDE.md` | Full documentation |

---

## 📱 Telegram Notification Types

- 🚀 Strategy Started
- 📝 Order Placed
- ✅ Position Opened
- 💰 P&L Updates
- 🎯 Target Hit
- 🛑 Stop Loss Hit
- 📊 Daily Summary
- ❌ Errors

---

## ⏰ Typical Daily Schedule

| Time | Action |
|------|--------|
| 8:00 AM | Generate new access token |
| 8:30 AM | Update config/brokers.yaml |
| 8:45 AM | Start strategy (paper mode to verify) |
| 9:00 AM | Switch to live mode if paper test passed |
| 9:20 AM | Strategy enters position |
| 9:20-15:15 | Monitor via Telegram |
| 15:15 PM | Auto square-off |
| 15:30 PM | Review logs and P&L |

---

## 🎯 Strike Selection Guide

| Parameter | Effect |
|-----------|--------|
| `--strike-points 0` | ATM (default) - Maximum premium |
| `--strike-points -100` | OTM - Lower premium, lower risk |
| `--strike-points 100` | ITM - Higher premium, higher risk |

---

## 💾 Database Queries

### View Historical Data
```bash
sqlite3 data/historical_data.db "SELECT * FROM historical_data WHERE symbol='BANKNIFTY' ORDER BY timestamp DESC LIMIT 10;"
```

### Get Statistics
```bash
sqlite3 data/historical_data.db "SELECT symbol, COUNT(*) as records FROM historical_data GROUP BY symbol;"
```

### Clear Old Data
```bash
sqlite3 data/historical_data.db "DELETE FROM historical_data WHERE timestamp < date('now', '-90 days');"
```

---

## 🔒 Security Checklist

- [ ] `config/brokers.yaml` in .gitignore
- [ ] Access token updated daily
- [ ] Never share screenshots with tokens
- [ ] Telegram bot token kept secure
- [ ] API keys rotated periodically

---

## 🎓 Learning Path

1. **Day 1-2**: Paper trading, understand flow
2. **Day 3-5**: Live with 1 lot, tight stop loss
3. **Day 6-10**: Increase to 2 lots if comfortable
4. **Week 2+**: Optimize parameters based on results

---

## 📊 Risk Management Rules

| Account Size | Max Lots | Stop Loss |
|--------------|----------|-----------|
| ₹50,000 | 1 | ₹2,000 |
| ₹1,00,000 | 1-2 | ₹3,000 |
| ₹2,00,000 | 2-3 | ₹5,000 |
| ₹5,00,000+ | 3-5 | ₹8,000 |

**Never risk more than 2-3% of account per trade!**

---

## 🆘 Emergency Commands

### Stop Strategy
```bash
# Press Ctrl+C in the terminal
# Or kill the process
pkill -f run_short_straddle.py
```

### Square Off All Positions (Manual)
```python
from brokers import BrokerFactory
import yaml

with open('config/brokers.yaml') as f:
    config = yaml.safe_load(f)

broker = BrokerFactory.create('upstox', config['brokers']['upstox'])
positions = broker.get_positions()

for pos in positions:
    # Square off each position
    broker.place_order(
        symbol=pos['symbol'],
        exchange=pos['exchange'],
        transaction_type='BUY' if pos['quantity'] < 0 else 'SELL',
        quantity=abs(pos['quantity']),
        order_type='MARKET',
        product_type=pos['product_type']
    )
```

---

## 📞 Quick Links

- **Upstox API Docs**: https://upstox.com/developer/
- **Zerodha Kite Connect**: https://kite.trade/docs/connect/v3/
- **Telegram Bot Creation**: https://core.telegram.org/bots#creating-a-new-bot
- **NSE Holiday Calendar**: https://www.nseindia.com/resources/exchange-communication-holidays

---

**Keep this reference handy! Print or bookmark! 📌**
