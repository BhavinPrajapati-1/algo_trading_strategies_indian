"""
Broker Notifier Wrapper

Integrates Telegram notifications with broker operations.
Automatically sends notifications for orders, positions, and P&L updates.

Author: Bhavin Prajapati
"""

import logging
from typing import Optional, List
from datetime import datetime

from brokers.base import BaseBroker, BrokerOrder, BrokerPosition
from notifications.telegram_bot import TelegramNotifier


logger = logging.getLogger(__name__)


class BrokerNotifier:
    """
    Wrapper class that adds notification capabilities to broker operations.

    Automatically sends Telegram notifications for:
    - Order placement, execution, cancellation
    - Position updates
    - P&L alerts
    - Error conditions
    """

    def __init__(
        self,
        broker: BaseBroker,
        telegram_notifier: Optional[TelegramNotifier] = None,
        auto_notify_orders: bool = True,
        auto_notify_positions: bool = True,
        auto_notify_pnl: bool = True
    ):
        """
        Initialize broker notifier.

        Args:
            broker: Broker instance
            telegram_notifier: Telegram notifier instance
            auto_notify_orders: Automatically notify on order events
            auto_notify_positions: Automatically notify on position events
            auto_notify_pnl: Automatically notify on P&L thresholds
        """
        self.broker = broker
        self.notifier = telegram_notifier
        self.auto_notify_orders = auto_notify_orders
        self.auto_notify_positions = auto_notify_positions
        self.auto_notify_pnl = auto_notify_pnl

        # Track positions for change detection
        self._last_positions: List[BrokerPosition] = []
        self._daily_pnl = 0.0

        logger.info(f"BrokerNotifier initialized for {broker.broker_name}")

    # ==========================================
    # Order Management with Notifications
    # ==========================================

    def place_order(
        self,
        symbol: str,
        exchange: str,
        transaction_type: str,
        quantity: int,
        order_type: str = "MARKET",
        price: float = 0.0,
        product_type: str = "MIS",
        trigger_price: float = 0.0,
        validity: str = "DAY",
        notify: Optional[bool] = None,
        **kwargs
    ) -> str:
        """
        Place an order with optional notification.

        Args:
            symbol: Trading symbol
            exchange: Exchange
            transaction_type: BUY/SELL
            quantity: Order quantity
            order_type: Order type
            price: Order price
            product_type: Product type
            trigger_price: Trigger price
            validity: Order validity
            notify: Override auto_notify_orders
            **kwargs: Additional parameters

        Returns:
            str: Order ID
        """
        try:
            order_id = self.broker.place_order(
                symbol=symbol,
                exchange=exchange,
                transaction_type=transaction_type,
                quantity=quantity,
                order_type=order_type,
                price=price,
                product_type=product_type,
                trigger_price=trigger_price,
                validity=validity,
                **kwargs
            )

            # Send notification
            should_notify = notify if notify is not None else self.auto_notify_orders
            if should_notify and self.notifier:
                self.notifier.notify_order_placed(
                    symbol=symbol,
                    transaction_type=transaction_type,
                    quantity=quantity,
                    order_type=order_type,
                    price=price if price > 0 else 0.0,
                    order_id=order_id
                )

            return order_id

        except Exception as e:
            logger.error(f"Order placement failed: {e}")
            if self.notifier:
                self.notifier.notify_error(
                    error_message=str(e),
                    error_type="Order Placement Error"
                )
            raise

    def cancel_order(
        self,
        order_id: str,
        symbol: Optional[str] = None,
        notify: Optional[bool] = None,
        **kwargs
    ) -> bool:
        """
        Cancel an order with optional notification.

        Args:
            order_id: Order ID to cancel
            symbol: Trading symbol (for notification)
            notify: Override auto_notify_orders
            **kwargs: Additional parameters

        Returns:
            bool: True if cancelled successfully
        """
        try:
            result = self.broker.cancel_order(order_id, **kwargs)

            # Send notification
            should_notify = notify if notify is not None else self.auto_notify_orders
            if should_notify and self.notifier and result:
                self.notifier.notify_order_cancelled(
                    symbol=symbol or "Unknown",
                    order_id=order_id
                )

            return result

        except Exception as e:
            logger.error(f"Order cancellation failed: {e}")
            if self.notifier:
                self.notifier.notify_error(
                    error_message=str(e),
                    error_type="Order Cancellation Error"
                )
            raise

    def square_off_position(
        self,
        symbol: str,
        exchange: str,
        product_type: str = "MIS",
        notify: Optional[bool] = None,
        **kwargs
    ) -> str:
        """
        Square off a position with optional notification.

        Args:
            symbol: Trading symbol
            exchange: Exchange
            product_type: Product type
            notify: Override auto_notify_positions
            **kwargs: Additional parameters

        Returns:
            str: Order ID
        """
        try:
            # Get position before squaring off
            positions = self.broker.get_positions()
            position = next(
                (p for p in positions if p.symbol == symbol and p.product_type == product_type),
                None
            )

            if not position:
                raise ValueError(f"No position found for {symbol}")

            # Square off
            order_id = self.broker.square_off_position(
                symbol=symbol,
                exchange=exchange,
                product_type=product_type,
                **kwargs
            )

            # Send notification
            should_notify = notify if notify is not None else self.auto_notify_positions
            if should_notify and self.notifier:
                # Calculate P&L percentage
                pnl_pct = (position.pnl / (position.average_price * abs(position.quantity))) * 100

                self.notifier.notify_position_closed(
                    symbol=symbol,
                    quantity=abs(position.quantity),
                    entry_price=position.average_price,
                    exit_price=position.last_price,
                    pnl=position.pnl,
                    pnl_percentage=pnl_pct
                )

            return order_id

        except Exception as e:
            logger.error(f"Square off failed: {e}")
            if self.notifier:
                self.notifier.notify_error(
                    error_message=str(e),
                    error_type="Square Off Error"
                )
            raise

    # ==========================================
    # Monitoring and Alerts
    # ==========================================

    def monitor_orders(self, notify_on_execution: bool = True) -> List[BrokerOrder]:
        """
        Monitor orders and send notifications on status changes.

        Args:
            notify_on_execution: Send notification when orders execute

        Returns:
            List[BrokerOrder]: Current orders
        """
        try:
            orders = self.broker.get_orders()

            if notify_on_execution and self.notifier:
                for order in orders:
                    if order.status == "COMPLETE" and order.filled_quantity > 0:
                        # Check if we've already notified (simple check)
                        self.notifier.notify_order_executed(
                            symbol=order.symbol,
                            transaction_type=order.transaction_type,
                            quantity=order.filled_quantity,
                            average_price=order.average_price,
                            order_id=order.order_id
                        )
                    elif order.status == "REJECTED":
                        self.notifier.notify_order_rejected(
                            symbol=order.symbol,
                            order_id=order.order_id,
                            reason=order.status_message or "Unknown"
                        )

            return orders

        except Exception as e:
            logger.error(f"Order monitoring failed: {e}")
            return []

    def monitor_positions(self, check_thresholds: bool = True) -> List[BrokerPosition]:
        """
        Monitor positions and send alerts on significant changes.

        Args:
            check_thresholds: Check P&L thresholds

        Returns:
            List[BrokerPosition]: Current positions
        """
        try:
            positions = self.broker.get_positions()

            # Calculate total P&L
            total_pnl = sum(pos.pnl for pos in positions)

            # Check thresholds
            if check_thresholds and self.auto_notify_pnl and self.notifier:
                if total_pnl >= self.notifier.profit_threshold:
                    winning_positions = sum(1 for pos in positions if pos.pnl > 0)
                    self.notifier.notify_profit_alert(
                        current_pnl=total_pnl,
                        total_trades=len(positions),
                        winning_trades=winning_positions
                    )
                elif total_pnl <= self.notifier.loss_threshold:
                    self.notifier.notify_loss_alert(
                        current_pnl=total_pnl,
                        max_loss=self.notifier.loss_threshold
                    )

            # Detect new positions
            if self.auto_notify_positions and self.notifier:
                current_symbols = {pos.symbol for pos in positions}
                last_symbols = {pos.symbol for pos in self._last_positions}

                # New positions
                new_symbols = current_symbols - last_symbols
                for symbol in new_symbols:
                    pos = next(p for p in positions if p.symbol == symbol)
                    self.notifier.notify_position_opened(
                        symbol=symbol,
                        quantity=abs(pos.quantity),
                        entry_price=pos.average_price,
                        position_value=abs(pos.quantity * pos.average_price)
                    )

            # Update tracked positions
            self._last_positions = positions
            self._daily_pnl = total_pnl

            return positions

        except Exception as e:
            logger.error(f"Position monitoring failed: {e}")
            return []

    def send_daily_summary(
        self,
        total_trades: int,
        winning_trades: int,
        losing_trades: int,
        gross_profit: float,
        gross_loss: float,
        largest_win: float,
        largest_loss: float
    ) -> bool:
        """
        Send daily trading summary.

        Args:
            total_trades: Total number of trades
            winning_trades: Number of winning trades
            losing_trades: Number of losing trades
            gross_profit: Total profit
            gross_loss: Total loss
            largest_win: Largest winning trade
            largest_loss: Largest losing trade

        Returns:
            bool: True if notification sent
        """
        if not self.notifier:
            return False

        return self.notifier.notify_daily_summary(
            total_pnl=self._daily_pnl,
            total_trades=total_trades,
            winning_trades=winning_trades,
            losing_trades=losing_trades,
            gross_profit=gross_profit,
            gross_loss=gross_loss,
            largest_win=largest_win,
            largest_loss=largest_loss
        )

    # ==========================================
    # Utility Methods
    # ==========================================

    def get_broker(self) -> BaseBroker:
        """Get the underlying broker instance."""
        return self.broker

    def get_notifier(self) -> Optional[TelegramNotifier]:
        """Get the Telegram notifier instance."""
        return self.notifier

    def set_notifier(self, notifier: TelegramNotifier):
        """Set or replace the Telegram notifier."""
        self.notifier = notifier
        logger.info("Telegram notifier updated")

    def enable_notifications(self):
        """Enable all auto-notifications."""
        self.auto_notify_orders = True
        self.auto_notify_positions = True
        self.auto_notify_pnl = True
        if self.notifier:
            self.notifier.enable()
        logger.info("All notifications enabled")

    def disable_notifications(self):
        """Disable all auto-notifications."""
        self.auto_notify_orders = False
        self.auto_notify_positions = False
        self.auto_notify_pnl = False
        if self.notifier:
            self.notifier.disable()
        logger.info("All notifications disabled")

    def __repr__(self) -> str:
        """String representation."""
        return f"BrokerNotifier(broker={self.broker.broker_name}, notifications={'enabled' if self.notifier else 'disabled'})"
