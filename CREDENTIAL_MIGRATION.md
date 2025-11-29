# Credential Migration Guide

This guide explains how to migrate your trading strategy files from hardcoded credentials to secure environment variables.

## 🎯 Why Migrate?

**Current Problem**: 14 strategy files have hardcoded credentials like:
```python
api_key = ""
api_secret = ""
```

**Security Issues**:
- ❌ Credentials visible in source code
- ❌ Risk of committing secrets to git
- ❌ Hard to rotate credentials
- ❌ Different credentials for dev/prod requires code changes

**After Migration**:
- ✅ Credentials in `.env` file (never committed)
- ✅ Same code works everywhere
- ✅ Easy credential rotation
- ✅ Follows security best practices

---

## 🔍 Step 1: Scan Files

See which files need migration:

```bash
python migrate_credentials.py --scan
```

**Output:**
```
Found 14 files with hardcoded credentials:

  📄 ./short-straddle/0920_short_straddle/banknifty_0920_short_straddle.py
  📄 ./short-straddle/combined_premium/bank_nifty_combined_premium_short_straddle.py
  📄 ./short-straddle/fixed_stop_loss/bank_nifty_fixed_stop_loss_short_straddle.py
  ... (11 more files)
```

---

## 📝 Step 2: Preview Changes (Dry Run)

See what would change WITHOUT modifying files:

```bash
python migrate_credentials.py --dry-run
```

**Example Output:**
```
======================================================================
Would migrate: ./short-straddle/0920_short_straddle/banknifty_0920_short_straddle.py
======================================================================
Changes would include:
  ✅ Add: import os, from dotenv import load_dotenv
  ✅ Add: load_dotenv()
  ✅ Replace: api_key = "" → api_key = os.getenv('ZERODHA_API_KEY')
  ✅ Replace: api_secret = "" → api_secret = os.getenv('ZERODHA_API_SECRET')
  ✅ Add: Credential validation with helpful error message
```

---

## 🚀 Step 3: Run Migration

Migrate all files automatically (creates `.backup` files):

```bash
python migrate_credentials.py --migrate
```

**What happens:**
1. Creates `.backup` file for each modified file
2. Adds `import os` and `from dotenv import load_dotenv`
3. Adds `load_dotenv()` call
4. Replaces hardcoded credentials with `os.getenv()`
5. Adds validation to show helpful error if credentials missing

**Example Migration:**

**Before:**
```python
from kiteconnect import KiteConnect
import datetime as dt

api_key = ""
api_secret = ""
access_token = open('C:/downloads/access_token.txt', 'r').read()

kite = KiteConnect(api_key=api_key)
kite.set_access_token(access_token)
```

**After:**
```python
from kiteconnect import KiteConnect
import datetime as dt
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

api_key = os.getenv('ZERODHA_API_KEY')
api_secret = os.getenv('ZERODHA_API_SECRET')
access_token = os.getenv('ZERODHA_ACCESS_TOKEN')

# Validate credentials are loaded
if not api_key or not api_secret or not access_token:
    print("⚠️  ERROR: Credentials not found in environment variables")
    print("Please ensure your .env file contains:")
    print("  - ZERODHA_API_KEY")
    print("  - ZERODHA_API_SECRET")
    print("  - ZERODHA_ACCESS_TOKEN")
    print("")
    print("Run: python zerodha_manual_auth.py to authenticate")
    print("See AUTHENTICATION.md for setup instructions")
    exit(1)

kite = KiteConnect(api_key=api_key)
kite.set_access_token(access_token)
```

---

## ✓ Step 4: Verify Migration

Check that all files have been migrated:

```bash
python migrate_credentials.py --verify
```

**Success:**
```
✅ Verification passed! No hardcoded credentials found.
```

**If issues remain:**
```
⚠️  Found 2 files still with hardcoded credentials:
   ./some/file.py
   ./another/file.py
```

---

## 🔧 Step 5: Setup Environment

Ensure your `.env` file has credentials:

```bash
# Check if .env exists
cat .env

# Should contain:
ZERODHA_API_KEY=your_api_key_here
ZERODHA_API_SECRET=your_api_secret_here
ZERODHA_ACCESS_TOKEN=your_token_here
```

If not set up, run:
```bash
# Copy example
cp .env.example .env

# Edit with your credentials
nano .env

# Authenticate to get access token
python zerodha_manual_auth.py
```

---

## 🧪 Step 6: Test Migrated Files

Test that a migrated strategy works:

```bash
# Try running a strategy
python short-straddle/0920_short_straddle/banknifty_0920_short_straddle.py
```

**If credentials are missing:**
```
⚠️  ERROR: Credentials not found in environment variables
Please ensure your .env file contains:
  - ZERODHA_API_KEY
  - ZERODHA_API_SECRET
  - ZERODHA_ACCESS_TOKEN

Run: python zerodha_manual_auth.py to authenticate
See AUTHENTICATION.md for setup instructions
```

**If successful:**
```
✅ Connected to Kite API
✅ Logged in as: Your Name
[Strategy continues...]
```

---

## 🔄 Rollback (If Needed)

If migration causes issues, rollback is easy:

```bash
# Restore a single file
mv short-straddle/0920_short_straddle/banknifty_0920_short_straddle.py.backup \
   short-straddle/0920_short_straddle/banknifty_0920_short_straddle.py

# Or restore all files
find . -name "*.py.backup" -exec sh -c 'mv "$1" "${1%.backup}"' _ {} \;

# Remove backup files after confirming migration works
find . -name "*.py.backup" -delete
```

---

## 📋 Manual Migration (Alternative)

If you prefer to migrate files manually:

### Option 1: Minimal Change

Add these lines at the top (after imports):
```python
import os
from dotenv import load_dotenv

load_dotenv()
```

Replace credential lines:
```python
# OLD:
api_key = ""
api_secret = ""

# NEW:
api_key = os.getenv('ZERODHA_API_KEY')
api_secret = os.getenv('ZERODHA_API_SECRET')
access_token = os.getenv('ZERODHA_ACCESS_TOKEN')
```

### Option 2: Use Utility (Best)

Replace the entire credential section:
```python
import sys
import os

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from utils.credentials import get_kite_instance

# Single line - gets authenticated instance
kite = get_kite_instance()
```

---

## 📊 Files That Need Migration

### By Category:

**0920 Entry Strategies (3 files)**
- `banknifty_0920_short_straddle.py`
- `finnifty_0920_short_straddle.py`
- `sensex_0920_short_straddle.py`

**Combined Premium (4 files)**
- `bank_nifty_combined_premium_short_straddle.py`
- `finnifty_combined_premium_short_straddle.py`
- `nifty50_combined_premium_short_straddle.py`
- `sensex_combined_premium_short_straddle.py`

**Fixed Stop Loss (2 files)**
- `bank_nifty_fixed_stop_loss_short_straddle.py`
- `bank_nifty_account_level_mtm_with_fixed_stop_loss_short_straddle.py`

**MTM Based (2 files)**
- `bank_nifty_mtm_based_short_straddle.py`
- `nifty50_mtm_based_short_straddle.py`

**Percentage Based (1 file)**
- `bank_nifty_percentage_based_stop_loss_short_straddle.py`

**Trailing Stop Loss (1 file)**
- `bank_nifty_trailing_percentage_based_stop_loss_short_straddle.py`

**Historical Data (1 file)**
- `zerodha_kite_historical_data.py`

---

## ⚠️ Important Notes

### Security
1. ✅ **Never commit** `.env` file (it's in `.gitignore`)
2. ✅ **Always use** environment variables for credentials
3. ✅ **Keep** `.backup` files until you verify migration works
4. ✅ **Review** changes before deleting backups

### Compatibility
1. ✅ Migrated files work **exactly the same**
2. ✅ No strategy logic changes
3. ✅ Only credential loading is different
4. ✅ Backward compatible with file-based tokens

### Testing
1. ✅ Test **one strategy** before migrating all
2. ✅ Verify `.env` has correct credentials
3. ✅ Run `zerodha_manual_auth.py` first
4. ✅ Check logs for any errors

---

## 🆘 Troubleshooting

### "ERROR: Credentials not found"

**Problem**: `.env` file missing or incomplete

**Solution**:
```bash
# Check .env exists
ls -la .env

# Check contents
cat .env

# Should have:
ZERODHA_API_KEY=xxx
ZERODHA_API_SECRET=yyy
ZERODHA_ACCESS_TOKEN=zzz

# If missing, run:
python zerodha_manual_auth.py
```

### "ModuleNotFoundError: No module named 'dotenv'"

**Problem**: python-dotenv not installed

**Solution**:
```bash
pip install python-dotenv
# or
pip install -r requirements.txt
```

### "Strategy not connecting to API"

**Problem**: Access token expired or invalid

**Solution**:
```bash
# Re-authenticate (tokens expire daily)
python zerodha_manual_auth.py
```

### "Import error: cannot import get_kite_instance"

**Problem**: Path not set correctly for utils import

**Solution**:
```python
# Add this before importing utils:
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
```

---

## 📚 Related Documentation

- **[AUTHENTICATION.md](AUTHENTICATION.md)** - Complete authentication guide
- **[MIGRATION_GUIDE.md](MIGRATION_GUIDE.md)** - General migration guide
- **[QUICKSTART.md](QUICKSTART.md)** - Quick setup guide
- **[CODE_QUALITY.md](CODE_QUALITY.md)** - Code quality standards

---

## 🎯 Summary

**Quick Migration Steps:**
1. `python migrate_credentials.py --scan` - See what needs migration
2. `python migrate_credentials.py --dry-run` - Preview changes
3. `python migrate_credentials.py --migrate` - Migrate all files
4. Ensure `.env` has credentials
5. Test a strategy
6. `python migrate_credentials.py --verify` - Confirm success
7. Delete `.backup` files once verified

**Benefits:**
- 🔒 More secure (no hardcoded credentials)
- 🔄 Easy credential rotation
- 🌍 Works across dev/prod environments
- ✅ Follows security best practices

---

**Ready to migrate? Start with:**
```bash
python migrate_credentials.py --dry-run
```
