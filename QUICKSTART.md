# Quick Start Guide

Get up and running with secure environment-based authentication in 5 minutes!

## Prerequisites

- Python 3.6 or higher
- Zerodha trading account
- Kite Connect API subscription (₹2000/month)

---

## 5-Minute Setup

### 1. Install Dependencies (1 min)

```bash
cd algo_trading_strategies_indian
pip install -r requirements.txt
```

### 2. Configure Environment (2 min)

```bash
# Copy example file
cp .env.example .env

# Edit with your credentials
nano .env
```

Add your API credentials:

```env
ZERODHA_API_KEY=your_api_key_from_kite_developer_portal
ZERODHA_API_SECRET=your_api_secret_from_kite_developer_portal
ZERODHA_ACCESS_TOKEN=
```

**Where to get API credentials?**
1. Go to https://developers.kite.trade/
2. Login → Create App
3. Copy API Key and API Secret

### 3. Authenticate (2 min)

```bash
python zerodha_manual_auth.py
```

Follow the prompts:
1. Open the URL in your browser
2. Login with Zerodha credentials
3. Copy `request_token` from redirect URL
4. Paste into terminal
5. ✅ Done!

### 4. Test (30 sec)

```bash
python examples/example_strategy_with_env.py
```

You should see:
```
✅ Successfully connected to Zerodha API
✅ Logged in as: Your Name
```

---

## Daily Workflow

Every trading day before market hours:

```bash
# Authenticate (takes 30 seconds)
python zerodha_manual_auth.py

# Run your strategies
python your_strategy.py
```

---

## What's Next?

### Run a Strategy

```bash
# Example: BANKNIFTY short straddle
cd short-straddle/0920_short_straddle
python banknifty_0920_short_straddle.py
```

### Set Up MTM Monitoring

```bash
cd broker-utilities/mtm_square_off_zerodha
python zerodha_runner.py
```

### Collect Historical Data

```bash
cd historical-data-collection/shoonya-finvasia
python stock_historical_data.py
```

---

## Files Created

After setup, you'll have:

```
.env                        # Your credentials (not committed to git)
config/access_token.txt     # Daily access token
```

---

## Troubleshooting

### "Missing required credentials"

Make sure `.env` file exists and contains your API key and secret.

### "Access token expired"

Run authentication again:
```bash
python zerodha_manual_auth.py
```

### "Invalid request_token"

The token expires in 2 minutes. Get a fresh one by opening the login URL again.

---

## Security Notes

✅ **DO:**
- Keep `.env` file private
- Run authentication daily
- Use strong Zerodha password

❌ **DON'T:**
- Commit `.env` to git (already in `.gitignore`)
- Share access tokens
- Hardcode credentials in scripts

---

## Learn More

- **Authentication Guide**: [AUTHENTICATION.md](AUTHENTICATION.md)
- **Migration Guide**: [MIGRATION_GUIDE.md](MIGRATION_GUIDE.md)
- **Full README**: [README.md](README.md)

---

## Support

- 📧 Create an issue on GitHub
- 📖 Check [Kite Connect Documentation](https://kite.trade/docs/connect/v3/)

---

**You're all set! Happy trading! 🚀**
