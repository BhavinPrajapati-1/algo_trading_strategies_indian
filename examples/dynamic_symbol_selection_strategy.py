"""
Example: Dynamic Symbol Selection Strategy

Demonstrates how to use SymbolSelector with multi-broker architecture
to intelligently select instruments and execute trades.

This strategy:
1. Selects the best instrument based on volatility
2. Calculates ATM strikes dynamically
3. Executes short straddle
4. Works with ANY broker (Zerodha, Upstox, Kotak, etc.)

Author: Bhavin Prajapati
"""

import os
import sys
from datetime import datetime
import logging

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from brokers import BrokerFactory
from utils.symbol_selector import SymbolSelector

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def main():
    """
    Main strategy execution.
    """
    print("\n" + "=" * 80)
    print("DYNAMIC SYMBOL SELECTION STRATEGY")
    print("=" * 80 + "\n")

    # ==========================================
    # Step 1: Initialize Broker
    # ==========================================
    # Get broker from environment or use default
    broker_name = os.getenv('DEFAULT_BROKER', 'zerodha')

    print(f"📊 Connecting to {broker_name.upper()} broker...")

    try:
        broker = BrokerFactory.create_from_env(broker_name)
        print(f"✅ Connected to {broker.broker_name}")
    except Exception as e:
        print(f"❌ Failed to connect to broker: {e}")
        return

    # ==========================================
    # Step 2: Initialize Symbol Selector
    # ==========================================
    print(f"\n🔍 Initializing Symbol Selector...")
    selector = SymbolSelector(broker)

    # ==========================================
    # Step 3: Select Best Instrument
    # ==========================================
    print(f"\n📈 Analyzing instruments for best trading opportunity...")

    # List of instruments to consider
    instruments_to_analyze = ['BANKNIFTY', 'NIFTY', 'FINNIFTY']

    # Select based on volatility (you can change to 'volume' or 'spread')
    selection_criteria = os.getenv('SELECTION_CRITERIA', 'volatility')

    print(f"   Criteria: {selection_criteria}")
    print(f"   Analyzing: {', '.join(instruments_to_analyze)}")

    try:
        best_instrument = selector.select_best_instrument(
            instruments=instruments_to_analyze,
            criteria=selection_criteria,
            lookback_days=5
        )

        print(f"✅ Selected: {best_instrument}")

    except Exception as e:
        logger.error(f"Error selecting instrument: {e}")
        # Fallback to default
        best_instrument = os.getenv('DEFAULT_INSTRUMENT', 'BANKNIFTY')
        print(f"⚠️  Using fallback: {best_instrument}")

    # ==========================================
    # Step 4: Get Instrument Details
    # ==========================================
    print(f"\n📋 Instrument Details:")

    instrument_info = selector.get_instrument_info(best_instrument)
    print(f"   Exchange: {instrument_info.exchange}")
    print(f"   Lot Size: {instrument_info.lot_size}")
    print(f"   Strike Interval: {instrument_info.strike_interval}")
    print(f"   Freeze Quantity: {instrument_info.freeze_quantity}")

    # ==========================================
    # Step 5: Get Current Spot Price
    # ==========================================
    print(f"\n💰 Fetching Current Price...")

    try:
        spot_price = selector.get_spot_price(best_instrument)
        print(f"   {best_instrument} LTP: ₹{spot_price:,.2f}")

    except Exception as e:
        logger.error(f"Error fetching spot price: {e}")
        return

    # ==========================================
    # Step 6: Calculate ATM Strike
    # ==========================================
    print(f"\n🎯 Calculating ATM Strike...")

    atm_strike = selector.get_atm_strike(best_instrument, spot_price)
    print(f"   ATM Strike: {atm_strike}")

    # ==========================================
    # Step 7: Get Nearest Expiry
    # ==========================================
    print(f"\n📅 Finding Nearest Expiry...")

    try:
        expiry = selector.get_nearest_expiry(best_instrument)
        print(f"   Expiry Date: {expiry}")

    except Exception as e:
        logger.error(f"Error getting expiry: {e}")
        # Use manual expiry as fallback
        expiry = "2024-12-26"
        print(f"⚠️  Using fallback expiry: {expiry}")

    # ==========================================
    # Step 8: Get Option Symbols
    # ==========================================
    print(f"\n🔢 Building Option Symbols...")

    # Get straddle symbols (same strike for Call and Put)
    call_symbol, put_symbol = selector.get_straddle_symbols(
        instrument=best_instrument,
        expiry=expiry,
        strike_offset=0,  # 0 = straddle, >0 = strangle
        spot_price=spot_price
    )

    print(f"   CALL: {call_symbol}")
    print(f"   PUT:  {put_symbol}")

    # ==========================================
    # Step 9: Execute Strategy (Demo)
    # ==========================================
    print(f"\n🚀 Strategy Execution:")

    # Get lot size from environment or use instrument default
    lots = int(os.getenv('DEFAULT_LOTS', '1'))
    quantity = lots * instrument_info.lot_size

    print(f"   Lots: {lots}")
    print(f"   Quantity per leg: {quantity}")

    # Check if we should execute or just simulate
    execute_trades = os.getenv('EXECUTE_TRADES', 'false').lower() == 'true'

    if execute_trades:
        print(f"\n⚠️  LIVE TRADING MODE")

        try:
            # Sell ATM Call
            print(f"\n   Selling {quantity} {call_symbol}...")
            call_order_id = broker.place_order(
                symbol=call_symbol,
                exchange='NFO',
                transaction_type='SELL',
                quantity=quantity,
                order_type='MARKET',
                product_type='MIS'
            )
            print(f"   ✅ Call Order ID: {call_order_id}")

            # Sell ATM Put
            print(f"\n   Selling {quantity} {put_symbol}...")
            put_order_id = broker.place_order(
                symbol=put_symbol,
                exchange='NFO',
                transaction_type='SELL',
                quantity=quantity,
                order_type='MARKET',
                product_type='MIS'
            )
            print(f"   ✅ Put Order ID: {put_order_id}")

            # Get positions
            print(f"\n📊 Current Positions:")
            positions = broker.get_positions()

            total_pnl = 0
            for pos in positions:
                if best_instrument in pos.symbol:
                    print(f"   {pos.symbol}: Qty={pos.quantity}, P&L=₹{pos.pnl:,.2f}")
                    total_pnl += pos.pnl

            print(f"\n   Total P&L: ₹{total_pnl:,.2f}")

        except Exception as e:
            logger.error(f"Error executing trades: {e}")

    else:
        print(f"\n📝 SIMULATION MODE (set EXECUTE_TRADES=true to go live)")
        print(f"   Would SELL: {quantity} {call_symbol}")
        print(f"   Would SELL: {quantity} {put_symbol}")

    # ==========================================
    # Step 10: Summary
    # ==========================================
    print(f"\n" + "=" * 80)
    print("STRATEGY EXECUTION COMPLETE")
    print("=" * 80)
    print(f"\n✅ Instrument: {best_instrument}")
    print(f"✅ Spot Price: ₹{spot_price:,.2f}")
    print(f"✅ ATM Strike: {atm_strike}")
    print(f"✅ Expiry: {expiry}")
    print(f"✅ Broker: {broker.broker_name}")
    print(f"\nConfiguration:")
    print(f"  • Selection Criteria: {selection_criteria}")
    print(f"  • Lots: {lots}")
    print(f"  • Quantity: {quantity}")
    print(f"  • Execute Mode: {'LIVE' if execute_trades else 'SIMULATION'}")

    print(f"\nTo run different configurations:")
    print(f"  • Change broker: export DEFAULT_BROKER=upstox")
    print(f"  • Change criteria: export SELECTION_CRITERIA=volume")
    print(f"  • Change lots: export DEFAULT_LOTS=2")
    print(f"  • Go live: export EXECUTE_TRADES=true")

    print()


if __name__ == "__main__":
    main()
