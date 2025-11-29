#!/usr/bin/env python3
"""
Example Trading Strategy with Environment Variables
===================================================
This is an example strategy that demonstrates how to use environment variables
for credentials instead of hardcoding them in your scripts.

Before running:
1. Copy .env.example to .env
2. Fill in your credentials in .env
3. Run: python zerodha_manual_auth.py (to get access token)
4. Then run this script

This example is based on the BANKNIFTY short straddle strategy.
"""

import datetime as dt
import time
import os
import sys

# Add parent directory to path to import utils
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.credentials import get_kite_instance

# =============================================================================
# CONFIGURATION - Using environment variables (preferred method)
# =============================================================================

# Get KiteConnect instance with credentials from .env file
try:
    kite = get_kite_instance()
    print("✅ Successfully connected to Zerodha API")
except ValueError as e:
    print(f"❌ Error: {e}")
    sys.exit(1)

# =============================================================================
# STRATEGY PARAMETERS - Configurable in .env or here
# =============================================================================

# Load from environment or use defaults
lots = int(os.getenv('DEFAULT_LOTS', '1'))
instrument = os.getenv('DEFAULT_INSTRUMENT', 'BANKNIFTY')
lot_size = int(os.getenv('DEFAULT_LOT_SIZE', '15'))

# You can also hardcode strategy-specific parameters
# lots = 1
# instrument = 'BANKNIFTY'
# lot_size = 15

quantity = lots * lot_size
strike_points = 0  # 0 = ATM

# Stop-loss parameters
ce_stoploss_per = 25  # 25% stop loss for Call option
pe_stoploss_per = 25  # 25% stop loss for Put option

# Time parameters
trade_entry_time = dt.time(hour=9, minute=20)
re_entry_time = dt.time(hour=12, minute=30)
square_off_time = dt.time(hour=15, minute=6)

# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def round_5ps(value):
    """Round price to nearest 0.05"""
    return round(value * 20) / 20


def get_banknifty_atm_strike(ltp):
    """Calculate ATM strike for BANKNIFTY (100 point intervals)"""
    r = ltp % 100
    if r < 50:
        atm = ltp - r
    else:
        atm = ltp - r + 100
    return int(atm)


def get_nifty_atm_strike(ltp):
    """Calculate ATM strike for NIFTY (50 point intervals)"""
    r = ltp % 50
    if r < 25:
        atm = ltp - r
    else:
        atm = ltp - r + 50
    return int(atm)


# =============================================================================
# MAIN STRATEGY LOGIC
# =============================================================================

def main():
    """Main strategy execution"""
    print("=" * 70)
    print(f"  {instrument} Short Straddle Strategy")
    print("=" * 70)
    print(f"Instrument: {instrument}")
    print(f"Lots: {lots}")
    print(f"Lot Size: {lot_size}")
    print(f"Total Quantity: {quantity}")
    print(f"Entry Time: {trade_entry_time}")
    print(f"Square-off Time: {square_off_time}")
    print("=" * 70)
    print()

    # Test API connection
    try:
        profile = kite.profile()
        print(f"✅ Logged in as: {profile['user_name']} ({profile['user_id']})")
        print(f"📧 Email: {profile['email']}")
        print()
    except Exception as e:
        print(f"❌ Error connecting to API: {e}")
        print("Please check your credentials and run: python zerodha_manual_auth.py")
        return

    # Download instruments
    print("📥 Downloading NFO instruments...")
    try:
        instruments = kite.instruments("NFO")
        print(f"✅ Downloaded {len(instruments)} instruments")
        print()
    except Exception as e:
        print(f"❌ Error downloading instruments: {e}")
        return

    # Example: Get current LTP
    try:
        ltp_data = kite.ltp(f'NSE:{instrument}')
        current_ltp = ltp_data[f'NSE:{instrument}']['last_price']
        print(f"📊 Current {instrument} LTP: ₹{current_ltp}")
        print()
    except Exception as e:
        print(f"❌ Error fetching LTP: {e}")
        return

    # Calculate ATM strike
    if instrument == 'BANKNIFTY':
        atm_strike = get_banknifty_atm_strike(current_ltp)
    elif instrument == 'NIFTY':
        atm_strike = get_nifty_atm_strike(current_ltp)
    else:
        print(f"⚠️  Instrument {instrument} not supported in this example")
        return

    print(f"🎯 ATM Strike: {atm_strike}")
    print()

    print("=" * 70)
    print("ℹ️  This is an example script for demonstration purposes")
    print("=" * 70)
    print()
    print("Key Features Demonstrated:")
    print("  ✅ Loading credentials from .env file")
    print("  ✅ Using utility functions for KiteConnect")
    print("  ✅ No hardcoded API keys or secrets")
    print("  ✅ Secure credential management")
    print()
    print("To implement the full strategy:")
    print("  1. Add order placement logic")
    print("  2. Add stop-loss monitoring")
    print("  3. Add position tracking")
    print("  4. Add error handling and logging")
    print()
    print("See the /short-straddle directory for complete strategy examples.")
    print()


if __name__ == "__main__":
    main()
