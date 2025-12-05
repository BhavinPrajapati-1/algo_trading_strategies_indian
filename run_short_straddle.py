#!/usr/bin/env python3
"""
Universal Short Straddle - Complete Solution

This script demonstrates the complete flow:
1. Load broker config from brokers.yaml
2. Fetch and store historical data
3. Run backtest (optional)
4. Execute live strategy with any broker
5. Send Telegram notifications

Works with ANY broker: Zerodha, Upstox, Kotak, Angel One, etc.

Usage:
    # Quick start (uses defaults)
    python run_short_straddle.py

    # With specific broker
    python run_short_straddle.py --broker upstox

    # Paper trading mode
    python run_short_straddle.py --paper-trading

    # With historical data fetch
    python run_short_straddle.py --fetch-history --days 30

    # Full options
    python run_short_straddle.py --broker upstox --symbol BANKNIFTY --lots 1 \\
        --stop-loss 5000 --target 3000 --paper-trading

Author: CEO's Magic Team 🚀
"""

import sys
import os
from pathlib import Path
import argparse
import time
from datetime import datetime, timedelta, time as dt_time
import logging
import yaml

# Add project root to path
project_root = Path(__file__).parent.absolute()
sys.path.insert(0, str(project_root))

from brokers import BrokerFactory
from strategies import ShortStraddleStrategy, StrategyConfig
from notifications import TelegramNotifier
from utils.historical_data import HistoricalDataFetcher


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/short_straddle.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


def load_broker_config(broker_name: str, config_file: str = 'config/brokers.yaml'):
    """
    Load broker configuration from brokers.yaml file.

    Args:
        broker_name: Name of broker (zerodha, upstox, etc.)
        config_file: Path to config file

    Returns:
        dict: Broker configuration
    """
    config_path = project_root / config_file

    if not config_path.exists():
        logger.error(f"Config file not found: {config_path}")
        logger.info("Please copy config/brokers.example.yaml to config/brokers.yaml")
        logger.info("And fill in your credentials")
        return None

    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)

    if 'brokers' not in config or broker_name not in config['brokers']:
        logger.error(f"Broker '{broker_name}' not found in config")
        return None

    broker_config = config['brokers'][broker_name]

    # Also load Telegram config if available
    telegram_config = config.get('telegram', {})

    return {
        'broker': broker_config,
        'telegram': telegram_config
    }


def initialize_broker(broker_name: str):
    """
    Initialize broker from configuration.

    Args:
        broker_name: Name of broker

    Returns:
        BaseBroker: Initialized broker instance
    """
    logger.info(f"Initializing {broker_name} broker...")

    config = load_broker_config(broker_name)

    if not config:
        raise ValueError(f"Could not load config for {broker_name}")

    broker_config = config['broker']

    # Create broker using factory
    # Unpack dictionary as keyword arguments
    broker = BrokerFactory.create(
        broker_name,
        api_key=broker_config.get('api_key'),
        api_secret=broker_config.get('api_secret'),
        access_token=broker_config.get('access_token')
    )

    # Verify authentication
    if not broker.is_authenticated:
        logger.error("Broker not authenticated!")
        logger.info("Please ensure access_token is set in config/brokers.yaml")
        raise ValueError("Broker authentication failed")

    # Get profile to verify
    profile = broker.get_profile()
    logger.info(f"✅ Connected to {broker_name}")
    logger.info(f"   User: {profile.get('user_name', profile.get('email', 'N/A'))}")

    return broker, config['telegram']


def initialize_telegram(telegram_config):
    """
    Initialize Telegram notifier.

    Args:
        telegram_config: Telegram configuration

    Returns:
        TelegramNotifier or None
    """
    if not telegram_config.get('enabled', False):
        logger.info("Telegram notifications disabled")
        return None

    bot_token = telegram_config.get('bot_token')
    chat_id = telegram_config.get('chat_id')

    if not bot_token or not chat_id:
        logger.warning("Telegram credentials not found - notifications disabled")
        return None

    try:
        notifier = TelegramNotifier(
            bot_token=bot_token,
            chat_id=chat_id,
            profit_threshold=telegram_config.get('notifications', {}).get('profit_threshold', 5000),
            loss_threshold=telegram_config.get('notifications', {}).get('loss_threshold', -2000)
        )

        if notifier.test_connection():
            logger.info("✅ Telegram notifications enabled")
            return notifier
        else:
            logger.warning("Telegram connection failed")
            return None

    except Exception as e:
        logger.warning(f"Could not initialize Telegram: {e}")
        return None


def fetch_historical_data(broker, symbol, exchange, days=30):
    """
    Fetch and store historical data.

    Args:
        broker: Broker instance
        symbol: Symbol to fetch
        exchange: Exchange
        days: Number of days of history

    Returns:
        DataFrame: Historical data
    """
    logger.info(f"Fetching historical data for {symbol}...")

    fetcher = HistoricalDataFetcher(broker, db_path='data/historical_data.db')

    to_date = datetime.now()
    from_date = to_date - timedelta(days=days)

    data = fetcher.fetch_and_store(
        symbol=symbol,
        exchange=exchange,
        from_date=from_date,
        to_date=to_date,
        interval='day'
    )

    logger.info(f"✅ Fetched {len(data)} candles")

    # Show stats
    stats = fetcher.get_fetch_stats()
    logger.info(f"Database stats:")
    logger.info(f"  Total records: {stats['total_records']}")
    logger.info(f"  Unique symbols: {stats['unique_symbols']}")
    logger.info(f"  Database: {stats['database_path']}")

    return data


def run_strategy(args):
    """
    Run the short straddle strategy.

    Args:
        args: Command line arguments
    """
    print("\n" + "=" * 80)
    print("🚀 UNIVERSAL SHORT STRADDLE STRATEGY")
    print("=" * 80)
    print(f"Broker: {args.broker}")
    print(f"Symbol: {args.symbol}")
    print(f"Lots: {args.lots}")
    print(f"Mode: {'PAPER TRADING' if args.paper_trading else 'LIVE TRADING'}")
    print("=" * 80 + "\n")

    # Initialize broker
    try:
        broker, telegram_config = initialize_broker(args.broker)
    except Exception as e:
        logger.error(f"Failed to initialize broker: {e}")
        return

    # Initialize Telegram
    notifier = initialize_telegram(telegram_config) if not args.no_telegram else None

    # Fetch historical data if requested
    if args.fetch_history:
        try:
            # For index, fetch spot data
            index_symbol = args.symbol
            index_exchange = 'NSE' if args.exchange == 'NFO' else args.exchange

            fetch_historical_data(
                broker=broker,
                symbol=index_symbol,
                exchange=index_exchange,
                days=args.history_days
            )
        except Exception as e:
            logger.warning(f"Could not fetch historical data: {e}")

    # Create strategy configuration
    config = StrategyConfig(
        strategy_name=f"{args.symbol}_ShortStraddle",
        symbol=args.symbol,
        exchange=args.exchange,
        lot_size=args.lot_size,
        lots=args.lots,
        strike_points=args.strike_points,
        entry_time=dt_time(args.entry_hour, args.entry_minute),
        exit_time=dt_time(args.exit_hour, args.exit_minute),
        square_off_time=dt_time(15, 25),
        stop_loss=args.stop_loss,
        target=args.target,
        position_type=args.position_type,
        enable_notifications=not args.no_telegram,
        paper_trading=args.paper_trading
    )

    # Create strategy
    strategy = ShortStraddleStrategy(
        broker=broker,
        config=config,
        notifier=notifier
    )

    # Start strategy
    logger.info("Starting strategy...")
    strategy.start()

    if notifier:
        notifier.notify_system_info(
            f"🚀 Short Straddle Started\n\n"
            f"Symbol: {args.symbol}\n"
            f"Lots: {args.lots}\n"
            f"Entry: {config.entry_time}\n"
            f"Exit: {config.exit_time}\n"
            f"Stop Loss: ₹{args.stop_loss if args.stop_loss else 'None'}\n"
            f"Target: ₹{args.target if args.target else 'None'}\n"
            f"Mode: {'Paper Trading' if args.paper_trading else 'Live'}",
            "Strategy Started"
        )

    # Main loop
    logger.info("Strategy running... Press Ctrl+C to stop")
    print("\n" + "=" * 80)
    print("📊 STRATEGY MONITORING")
    print("=" * 80)

    try:
        cycle_count = 0

        while strategy.is_active:
            cycle_count += 1

            # Run strategy cycle
            strategy.run_cycle()

            # Display status every 10 cycles
            if cycle_count % 10 == 0:
                status = strategy.get_strategy_stats()
                print(f"\n[{datetime.now().strftime('%H:%M:%S')}] Status:")
                print(f"  Entry Done: {status['entry_done']}")
                print(f"  P&L: ₹{status['pnl']:.2f}")
                print(f"  Positions: {status['positions_count']}")

                if status['entry_done']:
                    print(f"  Call: {status['call_symbol']}")
                    print(f"  Put: {status['put_symbol']}")
                    print(f"  Combined Premium: ₹{status['combined_premium']:.2f}")

            # Sleep before next cycle
            time.sleep(args.cycle_interval)

    except KeyboardInterrupt:
        logger.info("\n\nStopping strategy (user interrupted)...")

        if notifier:
            notifier.notify_system_info(
                "Strategy stopped by user",
                "Strategy Stopped"
            )

    except Exception as e:
        logger.error(f"Strategy error: {e}", exc_info=True)

        if notifier:
            notifier.notify_error(
                error_message=str(e),
                error_type="Strategy Error"
            )

    finally:
        # Final status
        final_status = strategy.get_strategy_stats()

        print("\n" + "=" * 80)
        print("📈 FINAL STATUS")
        print("=" * 80)
        print(f"Total P&L: ₹{final_status['pnl']:.2f}")
        print(f"Orders Placed: {final_status['orders_count']}")
        print("=" * 80 + "\n")

        logger.info("Strategy session completed")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Universal Short Straddle Strategy - Works with any broker!',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run with Upstox in paper trading mode
  python run_short_straddle.py --broker upstox --paper-trading

  # Run with Zerodha, 2 lots, with stop loss
  python run_short_straddle.py --broker zerodha --lots 2 --stop-loss 5000

  # Fetch 60 days history and run
  python run_short_straddle.py --fetch-history --history-days 60

  # Full configuration
  python run_short_straddle.py --broker upstox --symbol NIFTY --lots 1 \\
      --stop-loss 3000 --target 2000 --entry-time 09:20 --exit-time 15:15
        """
    )

    # Broker and symbol
    parser.add_argument('--broker', default='upstox',
                        help='Broker name (upstox, zerodha, kotak, etc.)')
    parser.add_argument('--symbol', default='BANKNIFTY',
                        help='Index symbol (BANKNIFTY, NIFTY, FINNIFTY, SENSEX)')
    parser.add_argument('--exchange', default='NFO',
                        help='Exchange (NFO, BFO)')

    # Position sizing
    parser.add_argument('--lots', type=int, default=1,
                        help='Number of lots to trade')
    parser.add_argument('--lot-size', type=int, default=15,
                        help='Lot size (15 for BANKNIFTY, 50 for NIFTY, etc.)')
    parser.add_argument('--strike-points', type=int, default=0,
                        help='Strike points from ATM (0=ATM, +ve=ITM, -ve=OTM)')

    # Timing
    parser.add_argument('--entry-time', default='09:20',
                        help='Entry time (HH:MM)')
    parser.add_argument('--exit-time', default='15:15',
                        help='Exit time (HH:MM)')

    # Risk management
    parser.add_argument('--stop-loss', type=float, default=None,
                        help='Stop loss in rupees')
    parser.add_argument('--target', type=float, default=None,
                        help='Profit target in rupees')
    parser.add_argument('--position-type', default='MIS',
                        help='Position type (MIS/NRML/CNC)')

    # Historical data
    parser.add_argument('--fetch-history', action='store_true',
                        help='Fetch historical data before running')
    parser.add_argument('--history-days', type=int, default=30,
                        help='Number of days of history to fetch')

    # Notifications
    parser.add_argument('--no-telegram', action='store_true',
                        help='Disable Telegram notifications')

    # Trading mode
    parser.add_argument('--paper-trading', action='store_true',
                        help='Enable paper trading (no real orders)')

    # System
    parser.add_argument('--cycle-interval', type=int, default=30,
                        help='Strategy cycle interval in seconds')

    args = parser.parse_args()

    # Parse entry/exit times
    entry_parts = args.entry_time.split(':')
    args.entry_hour = int(entry_parts[0])
    args.entry_minute = int(entry_parts[1])

    exit_parts = args.exit_time.split(':')
    args.exit_hour = int(exit_parts[0])
    args.exit_minute = int(exit_parts[1])

    # Create logs directory
    (project_root / 'logs').mkdir(exist_ok=True)
    (project_root / 'data').mkdir(exist_ok=True)

    # Run strategy
    run_strategy(args)


if __name__ == '__main__':
    main()
