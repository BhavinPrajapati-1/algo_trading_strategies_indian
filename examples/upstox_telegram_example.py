"""
Upstox Broker with Telegram Notifications Example

This example demonstrates how to use the Upstox broker with Telegram notifications.

Prerequisites:
1. Install dependencies: pip install upstox-python-sdk python-telegram-bot
2. Get Upstox API credentials from https://upstox.com/developer/
3. Create Telegram bot with @BotFather and get bot token
4. Get your Telegram chat ID from @userinfobot
5. Configure config/brokers.yaml with your credentials

Author: Bhavin Prajapati
"""

import logging
import os
from datetime import datetime

# Import broker factory
from brokers import BrokerFactory

# Import Telegram notification system
from notifications import TelegramNotifier
from notifications.broker_notifier import BrokerNotifier


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def main():
    """Main example function."""

    # ==========================================
    # Step 1: Initialize Upstox Broker
    # ==========================================

    print("Initializing Upstox broker...")

    # Option 1: Create from environment variables
    # Set these in your environment:
    # export UPSTOX_API_KEY="your_api_key"
    # export UPSTOX_API_SECRET="your_api_secret"
    # export UPSTOX_ACCESS_TOKEN="your_access_token"  # Optional

    broker = BrokerFactory.create_from_env('upstox')

    # Option 2: Create from config file
    # broker = BrokerFactory.create_from_file('upstox', 'config/brokers.yaml')

    # Option 3: Create directly
    # from brokers.implementations.upstox import UpstoxBroker
    # broker = UpstoxBroker(
    #     api_key="your_api_key",
    #     api_secret="your_api_secret",
    #     access_token="your_access_token"  # Optional
    # )

    print(f"✅ Broker initialized: {broker}")

    # ==========================================
    # Step 2: Login (if needed)
    # ==========================================

    if not broker.is_authenticated:
        print("\nBroker not authenticated. Generating login URL...")

        # Generate login URL
        broker.login(redirect_uri="http://127.0.0.1:5000/callback")

        # After user logs in and you get the authorization code:
        # authorization_code = input("Enter authorization code: ")
        # access_token = broker.get_access_token(authorization_code)
        # broker.set_access_token(access_token)
        # print(f"✅ Authenticated successfully!")

        # For this example, we'll assume you already have an access token
        print("⚠️  Please set UPSTOX_ACCESS_TOKEN environment variable")
        return

    print("✅ Broker authenticated")

    # ==========================================
    # Step 3: Initialize Telegram Notifier
    # ==========================================

    print("\nInitializing Telegram notifier...")

    # Get Telegram credentials from environment
    telegram_token = os.getenv('TELEGRAM_BOT_TOKEN')
    telegram_chat_id = os.getenv('TELEGRAM_CHAT_ID')

    if not telegram_token or not telegram_chat_id:
        print("⚠️  Telegram credentials not found")
        print("   Set TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID environment variables")
        print("   Continuing without notifications...")
        telegram_notifier = None
    else:
        telegram_notifier = TelegramNotifier(
            bot_token=telegram_token,
            chat_id=telegram_chat_id,
            enable_notifications=True,
            profit_threshold=5000.0,
            loss_threshold=-2000.0
        )

        # Test connection
        print("Testing Telegram connection...")
        if telegram_notifier.test_connection():
            print("✅ Telegram connection successful")
        else:
            print("❌ Telegram connection failed")
            telegram_notifier = None

    # ==========================================
    # Step 4: Create Broker Notifier Wrapper
    # ==========================================

    print("\nCreating broker notifier wrapper...")

    broker_notifier = BrokerNotifier(
        broker=broker,
        telegram_notifier=telegram_notifier,
        auto_notify_orders=True,
        auto_notify_positions=True,
        auto_notify_pnl=True
    )

    print(f"✅ Broker notifier ready: {broker_notifier}")

    # ==========================================
    # Step 5: Example Trading Operations
    # ==========================================

    print("\n" + "="*50)
    print("Example Trading Operations")
    print("="*50)

    try:
        # Get account profile
        print("\n1. Getting account profile...")
        profile = broker.get_profile()
        print(f"   User: {profile.get('user_name', 'N/A')}")
        print(f"   Email: {profile.get('email', 'N/A')}")

        # Get margins
        print("\n2. Getting account margins...")
        margins = broker.get_margins()
        print(f"   Available Cash: ₹{margins.available_cash:,.2f}")
        print(f"   Used Margin: ₹{margins.used_margin:,.2f}")

        # Get current positions
        print("\n3. Getting current positions...")
        positions = broker_notifier.monitor_positions()
        if positions:
            print(f"   Total positions: {len(positions)}")
            for pos in positions:
                print(f"   - {pos.symbol}: Qty={pos.quantity}, P&L=₹{pos.pnl:.2f}")
        else:
            print("   No open positions")

        # Example: Place an order (COMMENTED OUT FOR SAFETY)
        print("\n4. Example order placement (commented for safety)...")
        print("   Uncomment the code below to place actual orders")

        # order_id = broker_notifier.place_order(
        #     symbol="RELIANCE",
        #     exchange="NSE",
        #     transaction_type="BUY",
        #     quantity=1,
        #     order_type="MARKET",
        #     product_type="MIS"
        # )
        # print(f"   Order placed: {order_id}")

        # Example: Get quote
        print("\n5. Getting market quote...")
        try:
            quote = broker.get_quote("RELIANCE", "NSE")
            print(f"   Symbol: {quote.symbol}")
            print(f"   LTP: ₹{quote.last_price:.2f}")
            print(f"   Volume: {quote.volume:,}")
            print(f"   Day High: ₹{quote.high:.2f}")
            print(f"   Day Low: ₹{quote.low:.2f}")
        except Exception as e:
            print(f"   Could not fetch quote: {e}")

        # Monitor orders
        print("\n6. Monitoring orders...")
        orders = broker_notifier.monitor_orders()
        if orders:
            print(f"   Total orders today: {len(orders)}")
            for order in orders[:5]:  # Show first 5
                print(f"   - {order.symbol}: {order.status} ({order.order_type})")
        else:
            print("   No orders today")

        # Send custom notification
        if telegram_notifier:
            print("\n7. Sending custom notification...")
            telegram_notifier.notify_custom(
                message="Upstox broker with Telegram notifications is working perfectly!",
                title="System Test"
            )

        # Example daily summary
        if telegram_notifier:
            print("\n8. Sending daily summary example...")
            broker_notifier.send_daily_summary(
                total_trades=10,
                winning_trades=6,
                losing_trades=4,
                gross_profit=8500.0,
                gross_loss=-3200.0,
                largest_win=2500.0,
                largest_loss=-1200.0
            )

        print("\n" + "="*50)
        print("✅ All operations completed successfully!")
        print("="*50)

    except Exception as e:
        logger.error(f"Error during trading operations: {e}", exc_info=True)
        if telegram_notifier:
            telegram_notifier.notify_error(
                error_message=str(e),
                error_type="Trading Operation Error"
            )


def simple_trading_bot_example():
    """
    Simple trading bot with Telegram notifications.

    This demonstrates a basic trading loop with automated notifications.
    """
    print("\n" + "="*50)
    print("Simple Trading Bot Example")
    print("="*50)

    # Initialize
    broker = BrokerFactory.create_from_env('upstox')

    telegram_notifier = TelegramNotifier(
        bot_token=os.getenv('TELEGRAM_BOT_TOKEN'),
        chat_id=os.getenv('TELEGRAM_CHAT_ID')
    )

    bot = BrokerNotifier(broker, telegram_notifier)

    # Send startup notification
    telegram_notifier.notify_system_info(
        "Trading bot started successfully!",
        title="Bot Startup"
    )

    try:
        # Monitor positions continuously
        print("Monitoring positions (press Ctrl+C to stop)...")

        import time
        while True:
            positions = bot.monitor_positions(check_thresholds=True)
            orders = bot.monitor_orders(notify_on_execution=True)

            print(f"Positions: {len(positions)}, Orders: {len(orders)}")

            # Sleep for 30 seconds
            time.sleep(30)

    except KeyboardInterrupt:
        print("\nStopping bot...")
        telegram_notifier.notify_system_info(
            "Trading bot stopped by user",
            title="Bot Shutdown"
        )
    except Exception as e:
        logger.error(f"Bot error: {e}", exc_info=True)
        telegram_notifier.notify_error(str(e), "Bot Error")


if __name__ == "__main__":
    # Run main example
    main()

    # Uncomment to run simple trading bot
    # simple_trading_bot_example()
