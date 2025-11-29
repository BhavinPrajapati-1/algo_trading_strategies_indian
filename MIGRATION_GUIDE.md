# Migration Guide: Moving to Environment Variables

This guide helps you migrate your existing trading scripts from hardcoded credentials to secure environment variables.

## Why Migrate?

✅ **Security**: No more hardcoded API keys in source code
✅ **Convenience**: Update credentials in one place
✅ **Safety**: `.env` files are automatically excluded from git
✅ **Best Practice**: Industry-standard credential management

---

## Quick Migration Steps

### 1. Install New Dependencies

```bash
pip install -r requirements.txt
```

This adds `python-dotenv` and `kiteconnect` if not already installed.

### 2. Create Your .env File

```bash
cp .env.example .env
```

Edit `.env` and add your credentials:

```env
ZERODHA_API_KEY=your_api_key_here
ZERODHA_API_SECRET=your_api_secret_here
ZERODHA_ACCESS_TOKEN=  # Leave empty, will be filled by auth script
```

### 3. Authenticate

```bash
python zerodha_manual_auth.py
```

Follow the prompts to get your access token.

### 4. Update Your Scripts

Choose one of the migration methods below based on your script complexity.

---

## Migration Methods

### Method 1: Simple Replacement (Recommended)

**Before:**
```python
from kiteconnect import KiteConnect

api_key = "your_hardcoded_key"
api_secret = "your_hardcoded_secret"
access_token = open('/path/to/access_token.txt').read()

kite = KiteConnect(api_key=api_key)
kite.set_access_token(access_token)
```

**After:**
```python
from utils.credentials import get_kite_instance

kite = get_kite_instance()
```

**That's it!** Just 2 lines instead of 6.

---

### Method 2: Keep Your Structure

If you want to keep your existing code structure:

**Before:**
```python
from kiteconnect import KiteConnect

api_key = "xxxxxx"
api_secret = "yyyyyy"
access_token = open('access_token.txt').read()

kite = KiteConnect(api_key=api_key)
kite.set_access_token(access_token)
```

**After:**
```python
from kiteconnect import KiteConnect
from utils.credentials import get_zerodha_credentials

api_key, api_secret, access_token = get_zerodha_credentials()

kite = KiteConnect(api_key=api_key)
kite.set_access_token(access_token)
```

Just replace the credential loading, keep everything else the same.

---

### Method 3: Direct Environment Variables

For full control:

**Before:**
```python
from kiteconnect import KiteConnect

api_key = "hardcoded_key"
access_token = open('/some/path/access_token.txt').read()

kite = KiteConnect(api_key=api_key)
kite.set_access_token(access_token)
```

**After:**
```python
import os
from dotenv import load_dotenv
from kiteconnect import KiteConnect

# Load .env file
load_dotenv()

# Get from environment
api_key = os.getenv('ZERODHA_API_KEY')
access_token = os.getenv('ZERODHA_ACCESS_TOKEN')

kite = KiteConnect(api_key=api_key)
kite.set_access_token(access_token)
```

---

## Common Migration Scenarios

### Scenario 1: Script with Hardcoded File Path

**Before:**
```python
access_token = open('/home/ubuntu/utilities/access_token.txt', 'r').read()
```

**After (Option A - Use utility):**
```python
from utils.credentials import get_kite_instance
kite = get_kite_instance()
```

**After (Option B - Use environment variable):**
```python
import os
from dotenv import load_dotenv

load_dotenv()
access_token = os.getenv('ZERODHA_ACCESS_TOKEN')
```

---

### Scenario 2: Script with Multiple Credentials

**Before:**
```python
# Zerodha
api_key = "xxx"
api_secret = "yyy"

# Database
db_name = "trading_db"
db_user = "postgres"
db_password = "secret"

# Telegram
bot_token = "telegram_token"
chat_id = "123456"
```

**After:**
```python
from utils.credentials import (
    get_zerodha_credentials,
    get_database_config,
    get_telegram_config
)

# Zerodha
api_key, api_secret, access_token = get_zerodha_credentials()

# Database
db_config = get_database_config()
# Use: db_config['dbname'], db_config['user'], etc.

# Telegram
bot_token, chat_id = get_telegram_config()
```

Add to your `.env`:
```env
ZERODHA_API_KEY=xxx
ZERODHA_API_SECRET=yyy

DB_NAME=trading_db
DB_USER=postgres
DB_PASSWORD=secret

TELEGRAM_BOT_TOKEN=telegram_token
TELEGRAM_CHAT_ID=123456
```

---

### Scenario 3: Strategy with Config File

If you're using the MTM system with `config.yaml`:

**Before (config.yaml):**
```yaml
zerodha:
  api_key: "hardcoded_key"
  api_secret: "hardcoded_secret"
```

**After (config.yaml):**
```yaml
zerodha:
  # Credentials now loaded from .env (optional fallback)
  api_key: ""
  api_secret: ""
```

**Your .env:**
```env
ZERODHA_API_KEY=your_key
ZERODHA_API_SECRET=your_secret
ZERODHA_ACCESS_TOKEN=your_token
```

The MTM scripts have been updated to check environment variables first!

---

## Step-by-Step: Migrating a Complete Strategy

Let's migrate a full short straddle strategy as an example.

### Original Script

```python
# banknifty_strategy.py (OLD VERSION)
from kiteconnect import KiteConnect
import datetime as dt

# Hardcoded credentials
api_key = "xxxxxx"
api_secret = "yyyyyy"
access_token = open('/home/user/access_token.txt').read()

# Initialize
kite = KiteConnect(api_key=api_key)
kite.set_access_token(access_token)

# Strategy parameters
lots = 1
lot_size = 15
quantity = lots * lot_size

# ... rest of strategy ...
```

### Migrated Script

```python
# banknifty_strategy.py (NEW VERSION)
from utils.credentials import get_kite_instance
import datetime as dt
import os

# Get authenticated Kite instance
kite = get_kite_instance()

# Strategy parameters (can use environment variables for defaults)
lots = int(os.getenv('DEFAULT_LOTS', '1'))
lot_size = int(os.getenv('DEFAULT_LOT_SIZE', '15'))
quantity = lots * lot_size

# ... rest of strategy (unchanged) ...
```

**What Changed:**
1. Import changed from `KiteConnect` to `get_kite_instance`
2. Removed all hardcoded credentials
3. (Optional) Added environment variable support for parameters
4. Everything else stays the same!

---

## Migrating Each Strategy Type

### Short Straddle Strategies

Find all scripts like:
- `banknifty_0920_short_straddle.py`
- `nifty_short_straddle.py`
- etc.

**Replace this:**
```python
api_key = ""
access_token = open('path/to/token.txt').read()
kite = KiteConnect(api_key=api_key)
kite.set_access_token(access_token)
```

**With this:**
```python
from utils.credentials import get_kite_instance
kite = get_kite_instance()
```

### Historical Data Scripts

**Before:**
```python
api_key = "xxx"
api_secret = "yyy"
kite = KiteConnect(api_key=api_key)
```

**After:**
```python
from utils.credentials import get_kite_instance, get_database_config

kite = get_kite_instance()
db_config = get_database_config()
```

Add database credentials to `.env`:
```env
DB_NAME=trading_db
DB_USER=postgres
DB_PASSWORD=your_password
```

### Broker Utilities (MTM System)

The MTM system files have already been updated! Just:

1. Create `.env` file with credentials
2. Run `python zerodha_manual_auth.py`
3. Run the system as usual

The system will automatically use environment variables.

---

## Testing Your Migration

After migrating, test your script:

```bash
# 1. Make sure .env is configured
cat .env  # Should show your credentials (without passwords)

# 2. Authenticate
python zerodha_manual_auth.py

# 3. Test your migrated script
python your_migrated_script.py
```

**Expected output:**
```
✅ Successfully connected to Zerodha API
✅ Logged in as: Your Name (USER_ID)
```

If you see this, migration was successful! 🎉

---

## Troubleshooting Migration

### Import Error: "No module named utils"

**Problem**: Script can't find the `utils` package.

**Solution**: Add parent directory to Python path:

```python
import os
import sys

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.credentials import get_kite_instance
```

Or run from repository root:
```bash
cd /path/to/algo_trading_strategies_indian
python short-straddle/your_script.py
```

### Error: "Missing required credentials"

**Problem**: `.env` file not found or incomplete.

**Solution**:
```bash
# Check if .env exists
ls -la .env

# If not, create it
cp .env.example .env

# Edit and add your credentials
nano .env
```

### Error: "Access token not found"

**Problem**: Haven't authenticated yet.

**Solution**:
```bash
python zerodha_manual_auth.py
```

### Script Still Using Old Credentials

**Problem**: Script has both old and new code.

**Solution**: Remove old credential lines:
```python
# DELETE THESE LINES:
# api_key = "xxx"
# api_secret = "yyy"
# access_token = open(...).read()

# KEEP THIS:
from utils.credentials import get_kite_instance
kite = get_kite_instance()
```

---

## Migration Checklist

Use this checklist for each script you migrate:

- [ ] Install new dependencies (`pip install -r requirements.txt`)
- [ ] Create `.env` file (`cp .env.example .env`)
- [ ] Add credentials to `.env`
- [ ] Run authentication script (`python zerodha_manual_auth.py`)
- [ ] Update imports in script
- [ ] Remove hardcoded credentials
- [ ] Test script execution
- [ ] Verify API connection works
- [ ] Delete old credential files (optional)
- [ ] Update any documentation

---

## Best Practices After Migration

### 1. Never Commit .env

The `.gitignore` already excludes it, but double-check:

```bash
git status
# Should NOT show .env file
```

### 2. Use Environment Variables for All Configs

Not just credentials! Use `.env` for:
- API keys
- Database passwords
- File paths
- Default trading parameters
- Notification settings

### 3. Separate Dev and Production

Create different `.env` files:

```bash
.env              # Development (your local machine)
.env.production   # Production (cloud server)
```

Load the right one:
```python
from dotenv import load_dotenv

# Load production config on server
load_dotenv('.env.production')
```

### 4. Document Your Environment Variables

Add comments in `.env`:

```env
# Zerodha API credentials from https://developers.kite.trade/
ZERODHA_API_KEY=xxx

# Generated daily via zerodha_manual_auth.py
ZERODHA_ACCESS_TOKEN=yyy
```

---

## Rolling Back (If Needed)

If you need to revert to old code:

1. Keep your old script as backup:
   ```bash
   cp script.py script.py.old
   ```

2. Your old credentials should still work (if you didn't delete them)

3. To fully roll back:
   ```bash
   git checkout script.py  # Restore from git
   ```

But we recommend fixing the issue instead of rolling back! The new method is more secure.

---

## Next Steps

After migrating:

1. ✅ Test all your scripts
2. ✅ Delete old credential files (keep backups offline)
3. ✅ Update any documentation
4. ✅ Set daily reminder to run `zerodha_manual_auth.py`
5. ✅ Consider automating with cron (advanced users)

---

## Need Help?

1. Check the [AUTHENTICATION.md](AUTHENTICATION.md) guide
2. See [examples/example_strategy_with_env.py](examples/example_strategy_with_env.py)
3. Create a GitHub issue

Happy trading! 🚀
