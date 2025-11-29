# Authentication Guide

This guide explains how to securely authenticate with Zerodha Kite Connect API using environment variables and manual browser-based login.

## 🔒 Security First

**IMPORTANT**: This repository now uses **environment variables** for credential management. This is more secure than hardcoding credentials in your scripts.

### What Changed?

- ❌ **OLD (Insecure)**: Hardcoded API keys, usernames, and passwords in scripts
- ✅ **NEW (Secure)**: Credentials stored in `.env` file, manual browser-based authentication

### Benefits

1. **No Password Storage**: Your Zerodha password is never stored on disk
2. **No Auto-login Scripts**: Manual authentication is more secure
3. **Environment Variables**: Credentials in `.env` file (never committed to git)
4. **Easy Rotation**: Update credentials in one place (`.env` file)

---

## 🚀 Quick Start

### Step 1: Install Dependencies

```bash
pip install -r requirements.txt
```

This installs:
- `kiteconnect` - Zerodha Kite API client
- `python-dotenv` - Environment variable management
- Other required packages

### Step 2: Create .env File

```bash
# Copy the example file
cp .env.example .env

# Edit .env with your credentials
nano .env  # or use your favorite editor
```

### Step 3: Get Zerodha API Credentials

1. Go to [Kite Connect Developer Portal](https://developers.kite.trade/)
2. Login with your Zerodha account
3. Create a new App (if you haven't already)
4. Note down:
   - **API Key** (shown on app page)
   - **API Secret** (shown once, save it securely)

### Step 4: Configure .env File

Edit your `.env` file and add:

```env
# Zerodha API Credentials
ZERODHA_API_KEY=your_api_key_here
ZERODHA_API_SECRET=your_api_secret_here

# Leave this empty for now - will be filled by auth script
ZERODHA_ACCESS_TOKEN=
```

**Note**: You can also configure database, Telegram, and other settings in `.env`. See `.env.example` for all available options.

### Step 5: Authenticate (Daily)

**Run this script every trading day before market hours:**

```bash
python zerodha_manual_auth.py
```

The script will:

1. **Generate a login URL** - Copy and open it in your browser
2. **Login with Zerodha** - Enter your credentials in the browser
3. **Get redirected** - You'll be redirected to a URL with `request_token`
4. **Paste the token** - Copy just the `request_token` value and paste it
5. **Generate access token** - Script will generate and save your access token

#### Example Session:

```
======================================================================
  Zerodha Kite Connect - Manual Authentication
======================================================================

📋 API Key: xxxxx...

======================================================================
STEP 1: Login to Zerodha
======================================================================

Please open this URL in your browser:

  https://kite.zerodha.com/connect/login?v=3&api_key=xxxxx...

After logging in with your Zerodha credentials, you will be
redirected to a URL that looks like:

  https://yourapp.com/?action=login&status=success&request_token=XXXXXX

======================================================================

STEP 2: Extract Request Token
======================================================================

Paste the request_token from the URL (just the token part): XAI102wT2Z6y6Rh7aaw3mnplXIeaIJRt

📝 Request Token: XAI102wT2Z6y6Rh...

🔄 Generating access token...

======================================================================
✅ Authentication Successful!
======================================================================

Access Token: xxxxxxxxxxxxxxxxxxxxxxxxxxxxx

User ID: AB1234
User Name: John Doe
Email: john@example.com

✅ Access token saved to: ./config/access_token.txt
✅ Access token updated in .env file

======================================================================
⚠️  IMPORTANT: Access Token Validity
======================================================================

• Your access token is valid until ~6:00 AM next trading day
• You need to run this script again before market hours each day
• The token has been saved to:
  - .env file (ZERODHA_ACCESS_TOKEN)
  - ./config/access_token.txt

======================================================================
✅ You can now run your trading scripts!
======================================================================
```

### Step 6: Run Your Trading Strategies

Now you can run any trading script:

```bash
# Example: Run a BANKNIFTY strategy
python examples/example_strategy_with_env.py

# Example: Run MTM monitoring system
cd broker-utilities/mtm_square_off_zerodha/
python zerodha_runner.py
```

---

## 📝 Using Credentials in Your Scripts

### Option 1: Use the Credentials Utility (Recommended)

```python
from utils.credentials import get_kite_instance

# Get ready-to-use KiteConnect instance
kite = get_kite_instance()

# Start trading
profile = kite.profile()
print(f"Logged in as: {profile['user_name']}")
```

### Option 2: Manual Loading

```python
import os
from dotenv import load_dotenv
from kiteconnect import KiteConnect

# Load environment variables
load_dotenv()

# Get credentials
api_key = os.getenv('ZERODHA_API_KEY')
api_secret = os.getenv('ZERODHA_API_SECRET')
access_token = os.getenv('ZERODHA_ACCESS_TOKEN')

# Initialize KiteConnect
kite = KiteConnect(api_key=api_key)
kite.set_access_token(access_token)
```

### Option 3: Individual Credential Functions

```python
from utils.credentials import (
    get_zerodha_credentials,
    get_database_config,
    get_telegram_config
)

# Get Zerodha credentials
api_key, api_secret, access_token = get_zerodha_credentials()

# Get database config
db_config = get_database_config()

# Get Telegram config (for notifications)
bot_token, chat_id = get_telegram_config()
```

---

## 🔄 Daily Authentication Workflow

Since Zerodha access tokens expire daily, follow this routine:

### Before Market Hours (Before 9:15 AM)

1. Run authentication script:
   ```bash
   python zerodha_manual_auth.py
   ```

2. Open the login URL in browser
3. Login with your Zerodha credentials
4. Copy the `request_token` from redirect URL
5. Paste it into the script
6. ✅ You're authenticated for the day!

### During Market Hours

- Run your trading strategies normally
- All scripts will use the access token from `.env`
- No need to re-authenticate (token valid until next day ~6 AM)

### Pro Tips

1. **Set a reminder** at 9:00 AM every trading day to run authentication
2. **Save the login URL** as a bookmark for quick access
3. **Keep browser open** to make daily login faster
4. **Check token expiry** - if you get authentication errors during the day, re-run auth script

---

## 🛠️ Migrating Existing Scripts

If you have old scripts with hardcoded credentials, migrate them:

### Old Code (Insecure)
```python
api_key = "xxxxx"
api_secret = "yyyyy"
access_token = open('/path/to/access_token.txt').read()

kite = KiteConnect(api_key=api_key)
kite.set_access_token(access_token)
```

### New Code (Secure)
```python
from utils.credentials import get_kite_instance

kite = get_kite_instance()
```

That's it! Just 2 lines.

---

## ⚙️ Configuration Reference

### .env File Structure

```env
# ==============================================
# ZERODHA KITE CONNECT API
# ==============================================
ZERODHA_API_KEY=your_api_key
ZERODHA_API_SECRET=your_api_secret
ZERODHA_ACCESS_TOKEN=generated_by_auth_script

# ==============================================
# TELEGRAM NOTIFICATIONS (Optional)
# ==============================================
TELEGRAM_BOT_TOKEN=your_bot_token
TELEGRAM_CHAT_ID=your_chat_id

# ==============================================
# DATABASE (For historical data)
# ==============================================
DB_NAME=trading_db
DB_USER=postgres
DB_PASSWORD=your_password
DB_HOST=localhost
DB_PORT=5432

# ==============================================
# FILE PATHS (Optional)
# ==============================================
ACCESS_TOKEN_FILE=./config/access_token.txt
INSTRUMENTS_FILE=./config/instruments.pkl

# ==============================================
# TRADING DEFAULTS (Optional)
# ==============================================
DEFAULT_LOTS=1
DEFAULT_INSTRUMENT=BANKNIFTY
DEFAULT_LOT_SIZE=15
```

### Environment Variable Priority

The system loads credentials in this order:

1. **Environment variable** (`.env` file)
2. **Config file** (`config.yaml` for MTM system)
3. **Token file** (backward compatibility)
4. **Error** if none found

---

## 🔐 Security Best Practices

### DO ✅

- ✅ Keep `.env` file in `.gitignore` (already configured)
- ✅ Use different API keys for development and production
- ✅ Rotate credentials periodically
- ✅ Use file permissions to protect `.env`: `chmod 600 .env`
- ✅ Authenticate manually each day
- ✅ Keep API secret secure (never share)

### DON'T ❌

- ❌ Commit `.env` file to git
- ❌ Share your `.env` file with anyone
- ❌ Hardcode credentials in scripts
- ❌ Store Zerodha password in files
- ❌ Use auto-login scripts with password
- ❌ Share access tokens publicly

---

## 🐛 Troubleshooting

### Error: "API credentials not found"

**Solution**: Make sure `.env` file exists and contains:
```env
ZERODHA_API_KEY=your_actual_key
ZERODHA_API_SECRET=your_actual_secret
ZERODHA_ACCESS_TOKEN=your_actual_token
```

### Error: "Access token not found"

**Solution**: Run the authentication script:
```bash
python zerodha_manual_auth.py
```

### Error: "Invalid access token" or "Token expired"

**Solution**: Access tokens expire daily. Re-authenticate:
```bash
python zerodha_manual_auth.py
```

### Error: "Invalid request_token"

**Causes**:
- Request token expired (valid for ~2 minutes)
- Wrong API secret
- Already used the request token

**Solution**: Start over with a fresh login URL

### MTM System not connecting

**Solution**: Make sure these are set in `.env`:
```env
ZERODHA_API_KEY=xxx
ZERODHA_API_SECRET=yyy
ZERODHA_ACCESS_TOKEN=zzz
```

The MTM system (`config.yaml`) will use environment variables if available.

---

## 📚 Additional Resources

- [Zerodha Kite Connect API Docs](https://kite.trade/docs/connect/v3/)
- [API Forum](https://kite.trade/forum/)
- [Python Client Documentation](https://kite.trade/docs/pykiteconnect/v3/)

---

## 🤝 Need Help?

1. Check this guide first
2. Review the example script: `examples/example_strategy_with_env.py`
3. Check existing scripts in `/short-straddle` directory
4. Create an issue on GitHub

---

## 📋 Summary

**Setup (One-time)**
```bash
pip install -r requirements.txt
cp .env.example .env
# Edit .env with your API key and secret
```

**Daily Routine**
```bash
python zerodha_manual_auth.py
# Login in browser, paste request_token
```

**Run Strategies**
```bash
python your_strategy.py
```

That's it! 🚀
