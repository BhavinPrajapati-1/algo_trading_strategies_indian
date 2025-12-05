"""
Short Straddle Strategy - Broker Agnostic

Universal short straddle implementation that works with any broker:
- Zerodha
- Upstox
- Kotak
- Angel One
- etc.

Strategy:
- Sell ATM Call and Put at entry time
- Square off at exit time or on stop loss/target
- Manage risk with configurable parameters

Author: Trading System Team
"""

from typing import List, Dict, Optional
from datetime import datetime, date, timedelta, time as dt_time
import logging

from strategies.base_strategy import BaseStrategy, StrategyConfig
from brokers.base import BaseBroker
from notifications.telegram_bot import TelegramNotifier


logger = logging.getLogger(__name__)


class ShortStraddleStrategy(BaseStrategy):
    """
    Short Straddle Strategy - Broker Agnostic.

    Sells ATM Call and Put options at configured entry time.
    Works with any broker through the unified broker interface.

    Usage:
        from brokers import BrokerFactory
        from strategies import ShortStraddleStrategy, StrategyConfig

        broker = BrokerFactory.create_from_env('upstox')

        config = StrategyConfig(
            strategy_name="BankNifty_ShortStraddle",
            symbol="BANKNIFTY",
            exchange="NFO",
            lot_size=15,
            lots=1,
            strike_points=0,  # ATM
            entry_time=dt_time(9, 20),
            exit_time=dt_time(15, 15),
            stop_loss=5000,
            target=3000
        )

        strategy = ShortStraddleStrategy(broker, config)
        strategy.start()

        # Run in loop
        while strategy.is_active:
            strategy.run_cycle()
            time.sleep(30)
    """

    def __init__(
        self,
        broker: BaseBroker,
        config: StrategyConfig,
        notifier: Optional[TelegramNotifier] = None,
        nse_holidays: Optional[List[date]] = None
    ):
        """
        Initialize Short Straddle Strategy.

        Args:
            broker: Broker instance (any broker)
            config: Strategy configuration
            notifier: Optional Telegram notifier
            nse_holidays: List of NSE holiday dates
        """
        super().__init__(broker, config, notifier)

        # NSE holidays (override is_market_holiday)
        self.nse_holidays = nse_holidays or self._get_default_holidays()

        # Option symbols
        self.call_symbol = None
        self.put_symbol = None
        self.expiry_date = None

        # Entry prices
        self.call_entry_price = 0.0
        self.put_entry_price = 0.0
        self.combined_premium = 0.0

        logger.info(f"Short Straddle initialized for {config.symbol}")

    def _get_default_holidays(self) -> List[date]:
        """Get default NSE holidays for current year."""
        current_year = datetime.now().year

        # 2024 holidays (update annually)
        if current_year == 2024:
            return [
                date(2024, 1, 26),  # Republic Day
                date(2024, 3, 8),   # Maha Shivaratri
                date(2024, 3, 25),  # Holi
                date(2024, 3, 29),  # Good Friday
                date(2024, 4, 11),  # Id-Ul-Fitr
                date(2024, 4, 17),  # Ram Navami
                date(2024, 4, 21),  # Mahavir Jayanti
                date(2024, 5, 1),   # Maharashtra Day
                date(2024, 6, 17),  # Eid-ul-Adha
                date(2024, 7, 17),  # Muharram
                date(2024, 8, 15),  # Independence Day
                date(2024, 10, 2),  # Gandhi Jayanti
                date(2024, 11, 1),  # Diwali Laxmi Pujan
                date(2024, 11, 15), # Gurunanak Jayanti
                date(2024, 12, 25), # Christmas
            ]

        # Return empty list for other years (should be updated)
        logger.warning(f"Using default holidays - please update for year {current_year}")
        return []

    def is_market_holiday(self) -> bool:
        """Check if today is a market holiday."""
        today = date.today()

        # Check weekends
        if today.weekday() >= 5:
            return True

        # Check NSE holidays
        if today in self.nse_holidays:
            return True

        return False

    def get_expiry_date(self) -> date:
        """
        Calculate the nearest expiry date based on symbol.

        Returns:
            date: Expiry date
        """
        current_date = date.today()
        symbol = self.config.symbol.upper()

        # BANKNIFTY, FINNIFTY - Weekly (Wednesday)
        if symbol in ['BANKNIFTY', 'FINNIFTY']:
            wd = current_date.weekday()
            if wd < 2:  # Monday or Tuesday
                exp_date = current_date + timedelta(days=2 - wd)
            elif wd == 2:  # Wednesday
                exp_date = current_date
            else:  # Thursday or Friday
                exp_date = current_date + timedelta(days=9 - wd)

        # NIFTY - Thursday expiry (changed from Wednesday in recent update)
        elif symbol in ['NIFTY', 'NIFTY50']:
            wd = current_date.weekday()
            if wd < 3:  # Mon-Wed
                exp_date = current_date + timedelta(days=3 - wd)
            elif wd == 3:  # Thursday
                exp_date = current_date
            else:  # Friday
                exp_date = current_date + timedelta(days=10 - wd)

        # Monthly expiries (SENSEX, etc.) - Last Thursday
        else:
            # Find last Thursday of current month
            year = current_date.year
            month = current_date.month

            # Get last day of month
            if month == 12:
                next_month = date(year + 1, 1, 1)
            else:
                next_month = date(year, month + 1, 1)

            last_day = next_month - timedelta(days=1)

            # Find last Thursday
            days_to_subtract = (last_day.weekday() - 3) % 7
            exp_date = last_day - timedelta(days=days_to_subtract)

        # Adjust for holidays
        while exp_date in self.nse_holidays:
            exp_date -= timedelta(days=1)

        return exp_date

    def get_atm_strike(self) -> int:
        """
        Get ATM strike price.

        Returns:
            int: ATM strike price
        """
        # Get index LTP
        index_symbol = self.config.symbol
        ltp = self.get_ltp(index_symbol, self.config.exchange.replace('NFO', 'NSE'))

        # Round to nearest strike
        symbol = index_symbol.upper()

        if symbol == 'BANKNIFTY':
            strike_interval = 100
        elif symbol in ['NIFTY', 'NIFTY50']:
            strike_interval = 50
        elif symbol == 'FINNIFTY':
            strike_interval = 50
        elif symbol == 'SENSEX':
            strike_interval = 100
        else:
            strike_interval = 100  # Default

        # Round to nearest strike
        atm_strike = round(ltp / strike_interval) * strike_interval

        # Adjust for ITM/OTM
        atm_strike += self.config.strike_points

        return int(atm_strike)

    def build_option_symbol(self, strike: int, option_type: str) -> str:
        """
        Build option symbol in broker's format.

        Args:
            strike: Strike price
            option_type: 'CE' for call, 'PE' for put

        Returns:
            str: Option symbol
        """
        if not self.expiry_date:
            self.expiry_date = self.get_expiry_date()

        symbol = self.config.symbol
        expiry = self.expiry_date

        # Format: BANKNIFTY24JAN50000CE
        # Symbol + Year(2) + Month(3 letters) + Strike + CE/PE
        year = expiry.strftime('%y')
        month = expiry.strftime('%b').upper()
        day = expiry.strftime('%d')

        # Different brokers may have different formats
        # This is the standard NSE format
        option_symbol = f"{symbol}{year}{month}{strike}{option_type}"

        return option_symbol

    def calculate_positions(self) -> List[Dict]:
        """
        Calculate positions to take (ATM Call and Put).

        Returns:
            List[Dict]: List of position details
        """
        # Get ATM strike
        atm_strike = self.get_atm_strike()

        # Build option symbols
        self.call_symbol = self.build_option_symbol(atm_strike, 'CE')
        self.put_symbol = self.build_option_symbol(atm_strike, 'PE')

        # Calculate quantity
        quantity = self.config.lot_size * self.config.lots

        positions = [
            {
                'symbol': self.call_symbol,
                'exchange': self.config.exchange,
                'transaction_type': 'SELL',
                'quantity': quantity,
                'order_type': 'MARKET',
                'product_type': self.config.position_type
            },
            {
                'symbol': self.put_symbol,
                'exchange': self.config.exchange,
                'transaction_type': 'SELL',
                'quantity': quantity,
                'order_type': 'MARKET',
                'product_type': self.config.position_type
            }
        ]

        logger.info(f"Calculated positions: CALL={self.call_symbol}, PUT={self.put_symbol}, Qty={quantity}")

        return positions

    def should_enter(self) -> bool:
        """
        Check if entry conditions are met.

        Returns:
            bool: True if should enter
        """
        now = datetime.now().time()

        # Check if entry time
        if now < self.config.entry_time:
            return False

        # Check if already entered
        if self.entry_done:
            return False

        # Check if market holiday
        if self.is_market_holiday():
            logger.info("Market holiday - not entering")
            return False

        logger.info("Entry conditions met")
        return True

    def should_exit(self) -> bool:
        """
        Check if exit conditions are met.

        Returns:
            bool: True if should exit
        """
        now = datetime.now().time()

        # Check exit time
        if now >= self.config.exit_time:
            logger.info("Exit time reached")
            return True

        # Check stop loss
        if self.check_stop_loss():
            return True

        # Check target
        if self.check_target():
            return True

        return False

    def place_entry_orders(self) -> List[str]:
        """
        Place entry orders (sell ATM call and put).

        Returns:
            List[str]: List of order IDs
        """
        logger.info("Placing entry orders")

        positions = self.calculate_positions()
        order_ids = []

        for position in positions:
            try:
                if self.config.paper_trading:
                    # Paper trading - just log
                    order_id = f"PAPER_{datetime.now().timestamp()}"
                    logger.info(f"[PAPER] {position['transaction_type']} {position['symbol']}: {order_id}")
                else:
                    # Real order
                    order_id = self.broker.place_order(
                        symbol=position['symbol'],
                        exchange=position['exchange'],
                        transaction_type=position['transaction_type'],
                        quantity=position['quantity'],
                        order_type=position['order_type'],
                        product_type=position['product_type']
                    )

                    logger.info(f"Order placed: {position['symbol']} - {order_id}")

                order_ids.append(order_id)
                self.orders.append(order_id)

                # Get entry price
                if 'CE' in position['symbol']:
                    self.call_entry_price = self.get_ltp(position['symbol'], position['exchange'])
                else:
                    self.put_entry_price = self.get_ltp(position['symbol'], position['exchange'])

                # Notify
                if self.notifier:
                    self.notifier.notify_order_placed(
                        symbol=position['symbol'],
                        transaction_type=position['transaction_type'],
                        quantity=position['quantity'],
                        order_type=position['order_type'],
                        price=0,  # Market order
                        order_id=order_id
                    )

            except Exception as e:
                logger.error(f"Error placing order for {position['symbol']}: {e}")

                if self.notifier:
                    self.notifier.notify_error(
                        error_message=str(e),
                        error_type="Order Placement Error"
                    )

        # Calculate combined premium
        self.combined_premium = self.call_entry_price + self.put_entry_price
        logger.info(f"Combined premium received: ₹{self.combined_premium:.2f}")

        if self.notifier:
            self.notifier.notify_custom(
                message=f"Short Straddle Entered\n\n"
                        f"Call: {self.call_symbol} @ ₹{self.call_entry_price:.2f}\n"
                        f"Put: {self.put_symbol} @ ₹{self.put_entry_price:.2f}\n"
                        f"Combined Premium: ₹{self.combined_premium:.2f}\n"
                        f"Quantity: {self.config.lot_size * self.config.lots}",
                title="Position Opened"
            )

        return order_ids

    def place_exit_orders(self) -> List[str]:
        """
        Place exit orders (square off all positions).

        Returns:
            List[str]: List of order IDs
        """
        logger.info("Placing exit orders")

        order_ids = self.square_off_all()

        # Calculate final P&L
        final_pnl = self.calculate_pnl()
        logger.info(f"Strategy closed with P&L: ₹{final_pnl:.2f}")

        return order_ids

    def get_strategy_stats(self) -> Dict:
        """
        Get strategy statistics.

        Returns:
            Dict: Strategy stats
        """
        stats = self.get_status()
        stats.update({
            'call_symbol': self.call_symbol,
            'put_symbol': self.put_symbol,
            'call_entry_price': self.call_entry_price,
            'put_entry_price': self.put_entry_price,
            'combined_premium': self.combined_premium,
            'expiry_date': str(self.expiry_date) if self.expiry_date else None
        })

        return stats

    def __repr__(self) -> str:
        """String representation."""
        return f"ShortStraddleStrategy({self.config.symbol}, broker={self.broker.broker_name}, active={self.is_active})"
