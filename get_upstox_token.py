#!/usr/bin/env python3
"""
Upstox Access Token Generator

This script helps you get an access token for Upstox API.
Upstox tokens expire daily, so you need to run this each trading day.

Prerequisites:
1. Upstox API Key and Secret from https://upstox.com/developer/
2. upstox-python-sdk installed: pip install upstox-python-sdk

Usage:
    python get_upstox_token.py

Author: Trading System
"""

import sys
import os
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.absolute()
sys.path.insert(0, str(project_root))

from brokers.implementations.upstox import UpstoxBroker


def main():
    """Main function to get Upstox access token."""

    print("\n" + "=" * 70)
    print("🔐 Upstox Access Token Generator")
    print("=" * 70)

    # Step 1: Get credentials
    print("\n📋 Step 1: Enter Your Credentials")
    print("-" * 70)

    api_key = os.getenv('UPSTOX_API_KEY')
    api_secret = os.getenv('UPSTOX_API_SECRET')

    if not api_key:
        api_key = input("Enter your Upstox API Key: ").strip()
    else:
        print(f"✓ Using API Key from environment: {api_key[:10]}...")

    if not api_secret:
        api_secret = input("Enter your Upstox API Secret: ").strip()
    else:
        print(f"✓ Using API Secret from environment: {api_secret[:10]}...")

    if not api_key or not api_secret:
        print("\n❌ Error: API Key and Secret are required!")
        print("Get them from: https://upstox.com/developer/")
        return

    # Step 2: Initialize broker
    print("\n🔧 Step 2: Initializing Upstox Broker")
    print("-" * 70)

    try:
        broker = UpstoxBroker(api_key, api_secret)
        print("✓ Broker initialized successfully")
    except ImportError as e:
        print(f"\n❌ Error: {e}")
        print("\nMissing dependency! Install it with:")
        print("  pip install upstox-python-sdk")
        return
    except Exception as e:
        print(f"\n❌ Error initializing broker: {e}")
        return

    # Step 3: Generate login URL
    print("\n🌐 Step 3: Login to Upstox")
    print("-" * 70)

    redirect_uri = "http://127.0.0.1:5000/callback"

    try:
        broker.login(redirect_uri=redirect_uri)
    except Exception as e:
        print(f"Error generating login URL: {e}")
        return

    print("\n📝 Instructions:")
    print("1. Open the URL above in your web browser")
    print("2. Login to your Upstox account")
    print("3. Authorize the application")
    print("4. After authorization, you'll be redirected to a URL like:")
    print(f"   {redirect_uri}?code=XXXXXXXXXXXXXX")
    print("5. Copy the 'code' parameter value from the URL")

    # Step 4: Get authorization code from user
    print("\n" + "=" * 70)
    authorization_code = input("\n🔑 Enter the authorization code: ").strip()

    if not authorization_code:
        print("\n❌ Error: Authorization code cannot be empty!")
        return

    # Step 5: Generate access token
    print("\n⏳ Step 4: Generating Access Token...")
    print("-" * 70)

    try:
        access_token = broker.get_access_token(
            authorization_code,
            redirect_uri=redirect_uri
        )

        print("\n✅ SUCCESS! Access token generated!")
        print("=" * 70)
        print(f"\n🎫 Your Access Token:\n")
        print(f"   {access_token}")
        print("\n" + "=" * 70)

        # Step 6: Save instructions
        print("\n💾 How to Use This Token:")
        print("-" * 70)
        print("\n**Option 1: Set as Environment Variable (Recommended)**")
        print("\nWindows (CMD):")
        print(f'  set UPSTOX_ACCESS_TOKEN={access_token}')
        print("\nWindows (PowerShell):")
        print(f'  $env:UPSTOX_ACCESS_TOKEN="{access_token}"')
        print("\nLinux/Mac:")
        print(f'  export UPSTOX_ACCESS_TOKEN="{access_token}"')

        print("\n**Option 2: Add to .env file**")
        print(f'  UPSTOX_ACCESS_TOKEN={access_token}')

        print("\n" + "=" * 70)
        print("⚠️  IMPORTANT NOTES:")
        print("-" * 70)
        print("• Upstox access tokens EXPIRE DAILY")
        print("• You need to run this script every trading day")
        print("• Keep your token secure and never commit it to git")
        print("• Token is valid only for today's trading session")
        print("=" * 70)

        # Step 7: Verify the token
        print("\n🔍 Step 5: Verifying Token...")
        print("-" * 70)

        try:
            broker.set_access_token(access_token)
            profile = broker.get_profile()

            print("\n✅ Token Verified Successfully!")
            print(f"👤 Logged in as: {profile.get('user_name', 'N/A')}")
            print(f"📧 Email: {profile.get('email', 'N/A')}")
            print(f"🏢 User Type: {profile.get('user_type', 'N/A')}")

            # Try to get margins
            try:
                margins = broker.get_margins()
                print(f"\n💰 Available Cash: ₹{margins.available_cash:,.2f}")
                print(f"📊 Used Margin: ₹{margins.used_margin:,.2f}")
            except Exception as e:
                print(f"\n⚠️  Note: Could not fetch margins: {e}")

        except Exception as e:
            print(f"\n⚠️  Warning: Token generated but verification failed: {e}")
            print("The token might still be valid. Try using it in your scripts.")

        print("\n" + "=" * 70)
        print("🎉 All Done! You can now use Upstox API")
        print("=" * 70)
        print("\nNext Steps:")
        print("  1. Set the environment variable (see above)")
        print("  2. Run: python run_examples.py upstox")
        print("  3. Or create your own trading script")
        print("\n")

    except Exception as e:
        print(f"\n❌ Error generating access token: {e}")
        print("\nPossible reasons:")
        print("  • Authorization code is incorrect")
        print("  • Authorization code has expired (they expire quickly)")
        print("  • Network connection issue")
        print("  • Invalid API credentials")
        print("\nTry again with a fresh authorization code.")
        return


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n🛑 Cancelled by user")
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
