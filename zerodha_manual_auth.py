#!/usr/bin/env python3
"""
Zerodha Manual Authentication Script
=====================================
This script provides a secure way to authenticate with Zerodha Kite Connect API.
It uses browser-based login instead of storing username/password.

Usage:
    python zerodha_manual_auth.py

The script will:
1. Load API credentials from .env file
2. Generate and display a login URL
3. Prompt you to login via browser
4. Ask you to paste the request_token from the redirect URL
5. Generate and save the access_token

The access_token is valid until ~6 AM next trading day.
"""

import os
import sys
from pathlib import Path
from kiteconnect import KiteConnect
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


def get_env_variable(var_name, required=True):
    """Get environment variable with validation."""
    value = os.getenv(var_name)
    if required and not value:
        print(f"❌ Error: {var_name} not found in .env file")
        print(f"   Please set {var_name} in your .env file")
        sys.exit(1)
    return value


def save_access_token(access_token, file_path=None):
    """Save access token to file and .env."""
    # Save to file (for backward compatibility with existing scripts)
    if file_path:
        file_path = Path(file_path)
        file_path.parent.mkdir(parents=True, exist_ok=True)
        with open(file_path, 'w') as f:
            f.write(access_token)
        print(f"✅ Access token saved to: {file_path}")

    # Update .env file
    env_path = Path('.env')
    if env_path.exists():
        # Read existing .env content
        with open(env_path, 'r') as f:
            lines = f.readlines()

        # Update or append ZERODHA_ACCESS_TOKEN
        token_updated = False
        for i, line in enumerate(lines):
            if line.startswith('ZERODHA_ACCESS_TOKEN='):
                lines[i] = f'ZERODHA_ACCESS_TOKEN={access_token}\n'
                token_updated = True
                break

        if not token_updated:
            lines.append(f'\nZERODHA_ACCESS_TOKEN={access_token}\n')

        # Write back to .env
        with open(env_path, 'w') as f:
            f.writelines(lines)
        print(f"✅ Access token updated in .env file")
    else:
        print("⚠️  Warning: .env file not found. Please create one from .env.example")


def main():
    """Main authentication flow."""
    print("=" * 70)
    print("  Zerodha Kite Connect - Manual Authentication")
    print("=" * 70)
    print()

    # Check if .env exists
    if not Path('.env').exists():
        print("❌ Error: .env file not found!")
        print()
        print("Please follow these steps:")
        print("1. Copy .env.example to .env:")
        print("   cp .env.example .env")
        print()
        print("2. Edit .env and add your API credentials:")
        print("   - ZERODHA_API_KEY")
        print("   - ZERODHA_API_SECRET")
        print()
        sys.exit(1)

    # Load credentials from environment
    api_key = get_env_variable('ZERODHA_API_KEY')
    api_secret = get_env_variable('ZERODHA_API_SECRET')

    # Optional: custom file path for access token
    access_token_file = os.getenv('ACCESS_TOKEN_FILE', './config/access_token.txt')

    print(f"📋 API Key: {api_key[:10]}..." if len(api_key) > 10 else f"📋 API Key: {api_key}")
    print()

    # Initialize KiteConnect
    kite = KiteConnect(api_key=api_key)

    # Step 1: Generate login URL
    login_url = kite.login_url()
    print("=" * 70)
    print("STEP 1: Login to Zerodha")
    print("=" * 70)
    print()
    print("Please open this URL in your browser:")
    print()
    print(f"  {login_url}")
    print()
    print("After logging in with your Zerodha credentials, you will be")
    print("redirected to a URL that looks like:")
    print()
    print("  https://yourapp.com/?action=login&status=success&request_token=XXXXXX")
    print()
    print("  OR")
    print()
    print("  https://127.0.0.1/?request_token=XXXXXX&action=login")
    print()
    print("=" * 70)
    print()

    # Step 2: Get request token from user
    print("STEP 2: Extract Request Token")
    print("=" * 70)
    print()
    request_token = input("Paste the request_token from the URL (just the token part): ").strip()

    if not request_token:
        print("❌ Error: No request token provided")
        sys.exit(1)

    print()
    print(f"📝 Request Token: {request_token[:20]}..." if len(request_token) > 20 else f"📝 Request Token: {request_token}")
    print()

    # Step 3: Generate access token
    try:
        print("🔄 Generating access token...")
        data = kite.generate_session(request_token, api_secret=api_secret)
        access_token = data["access_token"]

        print()
        print("=" * 70)
        print("✅ Authentication Successful!")
        print("=" * 70)
        print()
        print(f"Access Token: {access_token}")
        print()
        print(f"User ID: {data.get('user_id', 'N/A')}")
        print(f"User Name: {data.get('user_name', 'N/A')}")
        print(f"Email: {data.get('email', 'N/A')}")
        print()

        # Save access token
        save_access_token(access_token, access_token_file)

        print()
        print("=" * 70)
        print("⚠️  IMPORTANT: Access Token Validity")
        print("=" * 70)
        print()
        print("• Your access token is valid until ~6:00 AM next trading day")
        print("• You need to run this script again before market hours each day")
        print("• The token has been saved to:")
        print(f"  - .env file (ZERODHA_ACCESS_TOKEN)")
        print(f"  - {access_token_file}")
        print()
        print("=" * 70)
        print("✅ You can now run your trading scripts!")
        print("=" * 70)
        print()

    except Exception as e:
        print()
        print("=" * 70)
        print("❌ Authentication Failed")
        print("=" * 70)
        print()
        print(f"Error: {str(e)}")
        print()
        print("Common issues:")
        print("• Invalid or expired request_token (tokens expire in ~2 minutes)")
        print("• Wrong API secret")
        print("• Network connectivity issues")
        print()
        print("Please try again.")
        print()
        sys.exit(1)


if __name__ == "__main__":
    main()
