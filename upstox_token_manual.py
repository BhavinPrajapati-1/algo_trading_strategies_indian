#!/usr/bin/env python3
"""
Manual Upstox Token Generator (No SDK Required)
Works with Upstox API v2/v3 authentication

This script generates Upstox access tokens without requiring the upstox-python-sdk.
It uses direct API calls via the requests library.

Author: Claude AI
Date: December 2025
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
    print("4. After authorization, you'll be redirected to a URL like:")
    print("   http://127.0.0.1/?code=XXXXXXXXXXXXXX")
    print("5. Copy the 'code' parameter value from the URL")
    print("6. Paste it below when prompted")
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
        print("\n⏳ Sending token request to Upstox...")
        response = requests.post(url, data=data, headers=headers)
        response.raise_for_status()

        result = response.json()

        if 'access_token' in result:
            print("✅ Access token generated successfully!")
            return result['access_token']
        else:
            print(f"❌ Error in response: {result}")
            return None

    except requests.exceptions.HTTPError as e:
        print(f"❌ HTTP Error: {e}")
        if hasattr(e.response, 'text'):
            print(f"Response: {e.response.text}")
        return None
    except requests.exceptions.RequestException as e:
        print(f"❌ Request failed: {e}")
        return None
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return None


def verify_token(access_token):
    """Verify the access token works by fetching user profile"""

    url = "https://api.upstox.com/v2/user/profile"

    headers = {
        'Authorization': f'Bearer {access_token}',
        'Accept': 'application/json'
    }

    try:
        print("\n⏳ Verifying token with Upstox API...")
        response = requests.get(url, headers=headers)
        response.raise_for_status()

        profile = response.json()

        if profile.get('status') == 'success':
            data = profile.get('data', {})
            print("\n✅ Token verified successfully!")
            print(f"   User ID: {data.get('user_id', 'N/A')}")
            print(f"   User Name: {data.get('user_name', 'N/A')}")
            print(f"   Email: {data.get('email', 'N/A')}")
            print(f"   User Type: {data.get('user_type', 'N/A')}")
            print(f"   Broker: {data.get('broker', 'N/A')}")
            return True
        else:
            print(f"❌ Verification failed: {profile}")
            return False

    except requests.exceptions.HTTPError as e:
        print(f"❌ HTTP Error during verification: {e}")
        if hasattr(e.response, 'text'):
            print(f"Response: {e.response.text}")
        return False
    except requests.exceptions.RequestException as e:
        print(f"❌ Verification request failed: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error during verification: {e}")
        return False


def main():
    print("\n" + "=" * 80)
    print("🔑 UPSTOX ACCESS TOKEN GENERATOR")
    print("=" * 80)
    print("\nThis script generates Upstox access tokens without SDK dependencies.")
    print("Perfect for when upstox-python-sdk has installation issues!")
    print("=" * 80)

    # Get API credentials
    print("\n📝 Please provide your Upstox API credentials:")
    print("   (You can find these at: https://account.upstox.com/developer/apps)")
    print()

    api_key = input("Enter your Upstox API Key: ").strip()
    if not api_key:
        print("\n❌ API Key is required!")
        sys.exit(1)

    api_secret = input("Enter your Upstox API Secret: ").strip()
    if not api_secret:
        print("\n❌ API Secret is required!")
        sys.exit(1)

    # Optional custom redirect URI
    print("\n📝 Redirect URI (press Enter to use default: http://127.0.0.1)")
    custom_redirect = input("   Or enter custom redirect URI: ").strip()
    redirect_uri = custom_redirect if custom_redirect else "http://127.0.0.1"

    # Step 1: Generate login URL
    print("\n" + "=" * 80)
    print("STEP 1: Generate Login URL")
    print("=" * 80)

    login_url = generate_login_url(api_key, redirect_uri)

    # Step 2: Get authorization code
    print("\n" + "=" * 80)
    print("STEP 2: Get Authorization Code")
    print("=" * 80)

    auth_code = input("\n📝 Paste the authorization code here: ").strip()

    if not auth_code:
        print("\n❌ Authorization code is required!")
        sys.exit(1)

    # Step 3: Get access token
    print("\n" + "=" * 80)
    print("STEP 3: Generate Access Token")
    print("=" * 80)

    access_token = get_access_token(api_key, api_secret, auth_code, redirect_uri)

    if not access_token:
        print("\n❌ Failed to generate access token!")
        print("\nPossible reasons:")
        print("1. Authorization code already used (codes are single-use)")
        print("2. Redirect URI mismatch")
        print("3. Invalid API credentials")
        print("4. Code expired (generate a new one)")
        print("\nPlease try again!")
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
        print()
        print("1. Copy the token above (select and Ctrl+C)")
        print("2. Open your config/brokers.yaml file")
        print("3. Under 'upstox' section, update the 'access_token' field:")
        print()
        print("   brokers:")
        print("     upstox:")
        print("       api_key: \"your-api-key\"")
        print("       api_secret: \"your-api-secret\"")
        print(f"       access_token: \"{access_token}\"")
        print()
        print("4. Save the file")
        print()
        print("=" * 80)
        print("⏰ IMPORTANT: This token expires in 24 hours!")
        print("   You must regenerate it every trading day.")
        print("=" * 80)
        print()
        print("🚀 Now you can run:")
        print("   python run_short_straddle.py --broker upstox --paper-trading")
        print()
    else:
        print("\n❌ Token verification failed!")
        print("The token was generated but couldn't be verified.")
        print("You can still try using it, but it may not work.")
        sys.exit(1)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n❌ Operation cancelled by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
