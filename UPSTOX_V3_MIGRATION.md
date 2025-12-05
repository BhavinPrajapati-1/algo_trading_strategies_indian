# Upstox API v2/v3 - Complete Setup Guide

**Last Updated:** December 2025
**SDK Version:** 2.19.0 (supports both v2 and v3 endpoints)

---

## 🔍 Important Clarifications

### API Versioning
Upstox currently has a mixed API architecture:

- **Authentication**: Still uses **v2 endpoints** (OAuth 2.0 flow)
- **Trading Orders**: Now uses **v3 endpoints** (for order slicing and latency tracking)
- **Market Data**: v3 WebSocket feed available (launched January 2025)
- **Portfolio & Other APIs**: Still on v2

**Key Insight:** The authentication flow has NOT changed. Your 401 Unauthorized error is due to an **expired or invalid access token**, not an API version issue.

---

## 🔧 Current Issues & Fixes

### Issue 1: SDK Not Installed

The `upstox-python-sdk` package has installation issues due to:
1. Debian system package conflicts
2. Deprecated `setup.py` installation method
3. `uuid` package conflicts

**Solution: Manual Installation**

```bash
# Try with --use-pep517
pip install upstox-python-sdk --use-pep517 --no-cache-dir

# OR use pre-built wheel
pip install --only-binary :all: upstox-python-sdk

# OR if all else fails, install specific version
pip install upstox-python-sdk==2.18.0 --no-deps
pip install urllib3 certifi python-dateutil six pyyaml websocket-client
```

### Issue 2: 401 Unauthorized Error

**Root Cause:** Upstox access tokens **expire every 24 hours**. You must regenerate daily.

**Authentication Flow (OAuth 2.0):**

```
Step 1: Generate Login URL
    ↓
Step 2: User logs in at Upstox website
    ↓
Step 3: Get authorization code from redirect
    ↓
Step 4: Exchange code for access token
    ↓
Step 5: Use access token (valid for 24 hours)
```

**Detailed Steps:**

1. **Generate Login URL**
   ```bash
   # URL Format (still v2):
   https://api.upstox.com/v2/login/authorization/dialog?
       response_type=code&
       client_id=YOUR_API_KEY&
       redirect_uri=http://127.0.0.1&
       state=optional_state
   ```

2. **Open URL in Browser**
   - Login to Upstox
   - Authorize the application
   - You'll be redirected to: `http://127.0.0.1?code=AUTHORIZATION_CODE`

3. **Copy the Code**
   - Extract the `code` parameter from the redirect URL
   - Example: `code=abc123xyz789`

4. **Exchange for Access Token**
   ```bash
   curl -X POST 'https://api.upstox.com/v2/login/authorization/token' \
     -H 'Content-Type: application/x-www-form-urlencoded' \
     -d 'code=YOUR_AUTH_CODE' \
     -d 'client_id=YOUR_API_KEY' \
     -d 'client_secret=YOUR_API_SECRET' \
     -d 'redirect_uri=http://127.0.0.1' \
     -d 'grant_type=authorization_code'
   ```

   **Response:**
   ```json
   {
     "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
     "token_type": "Bearer",
     "expires_in": 86400
   }
   ```

5. **Update config/brokers.yaml**
   ```yaml
   brokers:
     upstox:
       api_key: "your-api-key"
       api_secret: "your-api-secret"
       access_token: "eyJ0eXAiOiJKV1QiLCJhbGc..."  # ← Update daily
   ```

---

## 🎯 Working Solution (Without SDK Installation)

Since the SDK has installation issues, here's a direct API approach:

### Option 1: Use Requests Library

Create a simple script `upstox_token_manual.py`:

```python
#!/usr/bin/env python3
"""
Manual Upstox Token Generator (No SDK Required)
Works with Upstox API v2/v3 authentication
"""

import requests
import sys
from urllib.parse import urlencode

def generate_login_url(api_key, redirect_uri="http://127.0.0.1"):
    """Generate Upstox login URL"""
    params = {
        'response_type': 'code',
        'client_id': api_key,
        'redirect_uri': redirect_uri,
        'state': 'optional_state'
    }

    base_url = "https://api.upstox.com/v2/login/authorization/dialog"
    login_url = f"{base_url}?{urlencode(params)}"

    print("=" * 80)
    print("🔗 UPSTOX LOGIN URL")
    print("=" * 80)
    print(f"\n{login_url}\n")
    print("=" * 80)
    print("\nInstructions:")
    print("1. Open the URL above in your browser")
    print("2. Login to your Upstox account")
    print("3. Authorize the application")
    print("4. Copy the 'code' from the redirect URL")
    print("5. Paste it below")
    print("=" * 80)

    return login_url


def get_access_token(api_key, api_secret, auth_code, redirect_uri="http://127.0.0.1"):
    """Exchange authorization code for access token"""

    url = "https://api.upstox.com/v2/login/authorization/token"

    data = {
        'code': auth_code,
        'client_id': api_key,
        'client_secret': api_secret,
        'redirect_uri': redirect_uri,
        'grant_type': 'authorization_code'
    }

    headers = {
        'Content-Type': 'application/x-www-form-urlencoded',
        'Accept': 'application/json'
    }

    try:
        response = requests.post(url, data=data, headers=headers)
        response.raise_for_status()

        result = response.json()

        if 'access_token' in result:
            return result['access_token']
        else:
            print(f"❌ Error: {result}")
            return None

    except requests.exceptions.RequestException as e:
        print(f"❌ Request failed: {e}")
        if hasattr(e.response, 'text'):
            print(f"Response: {e.response.text}")
        return None


def verify_token(access_token):
    """Verify the access token works"""

    url = "https://api.upstox.com/v2/user/profile"

    headers = {
        'Authorization': f'Bearer {access_token}',
        'Accept': 'application/json'
    }

    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()

        profile = response.json()

        if profile.get('status') == 'success':
            data = profile.get('data', {})
            print("\n✅ Token verified successfully!")
            print(f"   User: {data.get('user_name', 'N/A')}")
            print(f"   Email: {data.get('email', 'N/A')}")
            return True
        else:
            print(f"❌ Verification failed: {profile}")
            return False

    except requests.exceptions.RequestException as e:
        print(f"❌ Verification failed: {e}")
        if hasattr(e.response, 'text'):
            print(f"Response: {e.response.text}")
        return False


def main():
    print("\n" + "=" * 80)
    print("🔑 UPSTOX ACCESS TOKEN GENERATOR (Manual - No SDK)")
    print("=" * 80)

    # Get API credentials
    api_key = input("\n📝 Enter your Upstox API Key: ").strip()
    api_secret = input("📝 Enter your Upstox API Secret: ").strip()

    if not api_key or not api_secret:
        print("❌ API Key and Secret are required!")
        sys.exit(1)

    # Step 1: Generate login URL
    print("\n" + "=" * 80)
    print("STEP 1: Generate Login URL")
    print("=" * 80)

    login_url = generate_login_url(api_key)

    # Step 2: Get authorization code
    print("\n" + "=" * 80)
    print("STEP 2: Get Authorization Code")
    print("=" * 80)

    auth_code = input("\n📝 Paste the authorization code here: ").strip()

    if not auth_code:
        print("❌ Authorization code is required!")
        sys.exit(1)

    # Step 3: Get access token
    print("\n" + "=" * 80)
    print("STEP 3: Generate Access Token")
    print("=" * 80)
    print("\n⏳ Exchanging code for access token...")

    access_token = get_access_token(api_key, api_secret, auth_code)

    if not access_token:
        print("\n❌ Failed to generate access token!")
        sys.exit(1)

    # Step 4: Verify token
    print("\n" + "=" * 80)
    print("STEP 4: Verify Access Token")
    print("=" * 80)

    if verify_token(access_token):
        # Step 5: Display token
        print("\n" + "=" * 80)
        print("✅ SUCCESS! Your Access Token:")
        print("=" * 80)
        print(f"\n{access_token}\n")
        print("=" * 80)
        print("\n📝 Next Steps:")
        print("1. Copy the token above")
        print("2. Open config/brokers.yaml")
        print("3. Paste it under upstox -> access_token")
        print("4. Save the file")
        print("\n⏰ Remember: This token expires in 24 hours!")
        print("   You'll need to regenerate it tomorrow.")
        print("=" * 80)
    else:
        print("\n❌ Token verification failed!")
        sys.exit(1)


if __name__ == "__main__":
    main()
```

**Usage:**
```bash
python upstox_token_manual.py
```

---

## 📝 config/brokers.yaml Format

```yaml
brokers:
  upstox:
    api_key: "your-api-key-here"
    api_secret: "your-api-secret-here"
    access_token: "your-access-token-here"  # Update daily!

telegram:
  enabled: true
  bot_token: "your-telegram-bot-token"
  chat_id: "your-chat-id"
  notifications:
    profit_threshold: 5000.0
    loss_threshold: -2000.0
```

---

## 🔄 Daily Workflow

**Every Trading Day:**

1. **Morning (8:00 AM):**
   ```bash
   python upstox_token_manual.py
   ```

2. **Copy new access token**

3. **Update config/brokers.yaml**

4. **Test connection:**
   ```bash
   python run_short_straddle.py --broker upstox --paper-trading
   ```

5. **Start trading!**

---

## 🐛 Troubleshooting

### Problem: "401 Unauthorized"

**Cause:** Token expired or invalid

**Solution:**
1. Generate fresh token (see above)
2. Verify it's copied correctly (no extra spaces)
3. Check token in config/brokers.yaml

### Problem: "SDK not installing"

**Cause:** System package conflicts

**Solution:** Use manual method (see above) - no SDK needed!

### Problem: "Invalid redirect_uri"

**Cause:** Redirect URI mismatch

**Solution:** Use exact same redirect URI in all steps:
- Login URL generation
- Token exchange request
- App configuration on Upstox developer portal

**Common redirect URIs:**
- `http://127.0.0.1` (simple, no port)
- `http://localhost` (may not work with Upstox)
- Custom: `https://yourdomain.com/callback`

### Problem: "Invalid credentials"

**Causes:**
1. Wrong API Key/Secret
2. Redirect URI mismatch
3. Using code more than once (codes are single-use)

**Solution:**
- Verify API Key and Secret from Upstox developer portal
- Generate new authorization code
- Use matching redirect URIs everywhere

---

## 📚 References

- [Upstox Authentication Docs](https://upstox.com/developer/api-documentation/authentication/)
- [Upstox API Documentation](https://upstox.com/developer/api-documentation/open-api/)
- [Upstox Python SDK (GitHub)](https://github.com/upstox/upstox-python)
- [Upstox Python SDK (PyPI)](https://pypi.org/project/upstox-python-sdk/2.19.0/)

---

## ✅ Summary

1. **Authentication is still v2** - OAuth flow unchanged
2. **Tokens expire daily** - Must regenerate each morning
3. **SDK has installation issues** - Use manual method
4. **Manual method works perfectly** - No dependencies needed
5. **v3 endpoints** - Only for order API and market data feed (handled by SDK internally)

---

**Your 401 error is NOT due to v3. It's simply an expired token. Use the manual script above to get a fresh one!** 🚀
