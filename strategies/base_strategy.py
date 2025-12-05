"""
Base Strategy Class

Abstract base class for all trading strategies.
Provides common functionality and ensures broker-agnostic implementation.

All strategies should inherit from BaseStrategy.

Author: Trading System Team
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from datetime import datetime, time, date
import logging

from brokers.base import BaseBroker
from notifications.telegram_bot import TelegramNotifier


logger = logging.getLogger(__name__)


@dataclass
class StrategyConfig:
    """Configuration for trading strategies."""
    # Strategy identification
    strategy_name: str
    symbol: str
    exchange: str

    # Trading parameters
    lot_size: int
    lots: int
    strike_points: int = 0  # 0 for ATM, +ve for ITM, -ve for OTM

    # Time parameters
    entry_time: time = time(9, 20)
    exit_time: time = time(15, 15)
    square_off_time: time = time(15, 25)

    # Risk management
    stop_loss: Optional[float] = None  # Points or percentage
    target: Optional[float] = None  # Points or percentage
    trailing_stop: Optional[float] = None

    # Position sizing
    max_positions: int = 2  # Max number of positions
    position_type: str = "MIS"  # MIS/NRML/CNC

    # Advanced settings
    enable_notifications: bool = True
    enable_logging: bool = True
    paper_trading: bool = False  # For testing without real orders

    # Custom parameters (strategy-specific)
    custom_params: Dict[str, Any] = field(default_factory=dict)


class BaseStrategy(ABC):
    """
    Abstract base class for all trading strategies.

    All strategies must implement:
    - calculate_positions()
    - should_enter()
    - should_exit()
    - place_entry_orders()
    - place_exit_orders()
    """

    def __init__(
        self,
        broker: BaseBroker,
        config: StrategyConfig,
        notifier: Optional[TelegramNotifier] = None
    ):
        """
        Initialize strategy.

        Args:
            broker: Broker instance (any broker)
            config: Strategy configuration
            notifier: Optional Telegram notifier
        """
        self.broker = broker
        self.config = config
        self.notifier = notifier

        # Strategy state
        self.positions = []
        self.orders = []
        self.is_active = False
        self.entry_done = False
        self.pnl = 0.0

        # Logging
        self.logger = logging.getLogger(f"Strategy.{config.strategy_name}")
        if config.enable_logging:
            self.logger.setLevel(logging.INFO)

        self.logger.info(f"{config.strategy_name} initialized with {broker.broker_name}")

    # ==========================================
    # Abstract Methods (Must be implemented)
    # ==========================================

    @abstractmethod
    def calculate_positions(self) -> List[Dict]:
        """
        Calculate what positions to take.

        Returns:
            List[Dict]: List of position dictionaries with:
                - symbol: str
                - exchange: str
                - transaction_type: str (BUY/SELL)
                - quantity: int
                - order_type: str (MARKET/LIMIT)
                - price: float (optional)
        """
        pass

    @abstractmethod
    def should_enter(self) -> bool:
        """
        Check if entry conditions are met.

        Returns:
            bool: True if should enter trade
        """
        pass

    @abstractmethod
    def should_exit(self) -> bool:
        """
        Check if exit conditions are met.

        Returns:
            bool: True if should exit trade
        """
        pass

    @abstractmethod
    def place_entry_orders(self) -> List[str]:
        """
        Place entry orders.

        Returns:
            List[str]: List of order IDs
        """
        pass

    @abstractmethod
    def place_exit_orders(self) -> List[str]:
        """
        Place exit orders (square off).

        Returns:
            List[str]: List of order IDs
        """
        pass

    # ==========================================
    # Common Methods (Provided by base class)
    # ==========================================

    def start(self):
        """Start the strategy."""
        self.is_active = True
        self.logger.info(f"Strategy {self.config.strategy_name} started")

        if self.notifier:
            self.notifier.notify_system_info(
                f"Strategy {self.config.strategy_name} started",
                "Strategy Started"
            )

    def stop(self):
        """Stop the strategy."""
        self.is_active = False
        self.logger.info(f"Strategy {self.config.strategy_name} stopped")

        if self.notifier:
            self.notifier.notify_system_info(
                f"Strategy {self.config.strategy_name} stopped",
                "Strategy Stopped"
            )

    def get_ltp(self, symbol: str, exchange: str) -> float:
        """
        Get Last Traded Price for a symbol.

        Args:
            symbol: Trading symbol
            exchange: Exchange

        Returns:
            float: LTP
        """
        try:
            return self.broker.get_ltp(symbol, exchange)
        except Exception as e:
            self.logger.error(f"Error getting LTP for {symbol}: {e}")
            raise

    def get_quote(self, symbol: str, exchange: str):
        """
        Get full quote for a symbol.

        Args:
            symbol: Trading symbol
            exchange: Exchange

        Returns:
            BrokerQuote: Quote data
        """
        try:
            return self.broker.get_quote(symbol, exchange)
        except Exception as e:
            self.logger.error(f"Error getting quote for {symbol}: {e}")
            raise

    def get_current_positions(self) -> List:
        """
        Get current open positions.

        Returns:
            List[BrokerPosition]: Current positions
        """
        try:
            return self.broker.get_positions()
        except Exception as e:
            self.logger.error(f"Error getting positions: {e}")
            return []

    def calculate_pnl(self) -> float:
        """
        Calculate current P&L from positions.

        Returns:
            float: Total P&L
        """
        try:
            positions = self.get_current_positions()
            total_pnl = sum(pos.pnl for pos in positions)
            self.pnl = total_pnl
            return total_pnl
        except Exception as e:
            self.logger.error(f"Error calculating P&L: {e}")
            return 0.0

    def check_stop_loss(self) -> bool:
        """
        Check if stop loss is hit.

        Returns:
            bool: True if stop loss hit
        """
        if not self.config.stop_loss:
            return False

        pnl = self.calculate_pnl()

        if pnl <= -abs(self.config.stop_loss):
            self.logger.warning(f"Stop loss hit! P&L: ₹{pnl:.2f}")

            if self.notifier:
                self.notifier.notify_loss_alert(
                    current_pnl=pnl,
                    max_loss=self.config.stop_loss,
                    recommendation="Stop loss triggered - exiting positions"
                )

            return True

        return False

    def check_target(self) -> bool:
        """
        Check if profit target is hit.

        Returns:
            bool: True if target hit
        """
        if not self.config.target:
            return False

        pnl = self.calculate_pnl()

        if pnl >= self.config.target:
            self.logger.info(f"Target hit! P&L: ₹{pnl:.2f}")

            if self.notifier:
                positions = self.get_current_positions()
                self.notifier.notify_profit_alert(
                    current_pnl=pnl,
                    total_trades=len(positions),
                    winning_trades=sum(1 for p in positions if p.pnl > 0)
                )

            return True

        return False

    def is_trading_time(self) -> bool:
        """
        Check if current time is within trading hours.

        Returns:
            bool: True if within trading hours
        """
        now = datetime.now().time()
        return self.config.entry_time <= now <= self.config.exit_time

    def is_square_off_time(self) -> bool:
        """
        Check if it's time to square off all positions.

        Returns:
            bool: True if square off time
        """
        now = datetime.now().time()
        return now >= self.config.square_off_time

    def is_market_holiday(self) -> bool:
        """
        Check if today is a market holiday.

        Returns:
            bool: True if holiday
        """
        # Override this method in specific strategies with actual holiday list
        # For now, check if it's weekend
        today = date.today()
        return today.weekday() >= 5  # Saturday or Sunday

    def square_off_all(self) -> List[str]:
        """
        Square off all open positions.

        Returns:
            List[str]: List of order IDs
        """
        self.logger.info("Squaring off all positions")

        order_ids = []
        positions = self.get_current_positions()

        for position in positions:
            try:
                if position.quantity != 0:
                    order_id = self.broker.square_off_position(
                        symbol=position.symbol,
                        exchange=position.exchange,
                        product_type=position.product_type
                    )

                    order_ids.append(order_id)
                    self.logger.info(f"Squared off {position.symbol}: Order {order_id}")

                    if self.notifier:
                        pnl_pct = (position.pnl / (position.average_price * abs(position.quantity))) * 100 if position.quantity != 0 else 0

                        self.notifier.notify_position_closed(
                            symbol=position.symbol,
                            quantity=abs(position.quantity),
                            entry_price=position.average_price,
                            exit_price=position.last_price,
                            pnl=position.pnl,
                            pnl_percentage=pnl_pct
                        )

            except Exception as e:
                self.logger.error(f"Error squaring off {position.symbol}: {e}")

        return order_ids

    def run_cycle(self):
        """
        Run one strategy cycle (check conditions and execute).

        This should be called periodically (e.g., every few seconds).
        """
        if not self.is_active:
            return

        try:
            # Check if market holiday
            if self.is_market_holiday():
                self.logger.info("Market holiday - skipping")
                return

            # Check square off time
            if self.is_square_off_time() and not self.entry_done:
                self.logger.info("Square off time reached")
                self.square_off_all()
                self.stop()
                return

            # Check stop loss
            if self.check_stop_loss():
                self.place_exit_orders()
                self.stop()
                return

            # Check target
            if self.check_target():
                self.place_exit_orders()
                self.stop()
                return

            # Check entry conditions
            if not self.entry_done and self.should_enter():
                if self.is_trading_time():
                    self.logger.info("Entry conditions met - placing orders")
                    self.place_entry_orders()
                    self.entry_done = True

            # Check exit conditions
            if self.entry_done and self.should_exit():
                self.logger.info("Exit conditions met - closing positions")
                self.place_exit_orders()
                self.stop()

        except Exception as e:
            self.logger.error(f"Error in strategy cycle: {e}")

            if self.notifier:
                self.notifier.notify_error(
                    error_message=str(e),
                    error_type="Strategy Cycle Error"
                )

    def get_status(self) -> Dict:
        """
        Get current strategy status.

        Returns:
            Dict: Strategy status information
        """
        return {
            'strategy_name': self.config.strategy_name,
            'broker': self.broker.broker_name,
            'is_active': self.is_active,
            'entry_done': self.entry_done,
            'pnl': self.pnl,
            'positions_count': len(self.get_current_positions()),
            'orders_count': len(self.orders)
        }

    def __repr__(self) -> str:
        """String representation."""
        return f"BaseStrategy(name={self.config.strategy_name}, broker={self.broker.broker_name}, active={self.is_active})"
