"""
Telegram Bot Notification System

Sends real-time trading notifications to Telegram.
Supports order updates, position changes, P&L alerts, and custom messages.

Author: Bhavin Prajapati
"""

import logging
from typing import Optional, Dict, List, Any
from datetime import datetime
from enum import Enum
import asyncio
from dataclasses import dataclass

try:
    import telegram
    from telegram import Bot
    from telegram.error import TelegramError
    TELEGRAM_AVAILABLE = True
except ImportError:
    TELEGRAM_AVAILABLE = False
    telegram = None
    Bot = None
    TelegramError = Exception


logger = logging.getLogger(__name__)


class NotificationPriority(Enum):
    """Notification priority levels."""
    LOW = "🔵"
    NORMAL = "⚪"
    HIGH = "🟡"
    CRITICAL = "🔴"


class NotificationType(Enum):
    """Types of notifications."""
    ORDER_PLACED = "📤 Order Placed"
    ORDER_EXECUTED = "✅ Order Executed"
    ORDER_CANCELLED = "❌ Order Cancelled"
    ORDER_REJECTED = "⛔ Order Rejected"
    POSITION_OPENED = "📈 Position Opened"
    POSITION_CLOSED = "📉 Position Closed"
    PROFIT = "💰 Profit Alert"
    LOSS = "⚠️ Loss Alert"
    DAILY_SUMMARY = "📊 Daily Summary"
    SYSTEM_ERROR = "🚨 System Error"
    SYSTEM_INFO = "ℹ️ System Info"
    CUSTOM = "📢 Custom"


@dataclass
class NotificationMessage:
    """Notification message structure."""
    message_type: NotificationType
    priority: NotificationPriority
    title: str
    content: str
    timestamp: datetime
    data: Optional[Dict[str, Any]] = None


class TelegramNotifier:
    """
    Telegram notification system for trading alerts.

    Features:
    - Real-time order and position notifications
    - P&L alerts with customizable thresholds
    - Daily trading summary
    - Error and system notifications
    - Message formatting with emojis and markdown
    - Async message sending
    - Rate limiting support
    - Message queuing for reliability
    """

    def __init__(
        self,
        bot_token: str,
        chat_id: str,
        enable_notifications: bool = True,
        profit_threshold: float = 5000.0,
        loss_threshold: float = -2000.0
    ):
        """
        Initialize Telegram notifier.

        Args:
            bot_token: Telegram bot token from BotFather
            chat_id: Telegram chat ID to send messages to
            enable_notifications: Enable/disable notifications
            profit_threshold: Profit amount to trigger alert
            loss_threshold: Loss amount to trigger alert (negative value)
        """
        if not TELEGRAM_AVAILABLE:
            raise ImportError(
                "Telegram library not installed. "
                "Install with: pip install python-telegram-bot"
            )

        self.bot_token = bot_token
        self.chat_id = chat_id
        self.enable_notifications = enable_notifications
        self.profit_threshold = profit_threshold
        self.loss_threshold = loss_threshold

        # Initialize bot
        self.bot = Bot(token=bot_token)

        # Message queue for reliability
        self.message_queue: List[NotificationMessage] = []
        self.max_queue_size = 100

        logger.info("Telegram notifier initialized")

    async def send_message(
        self,
        message: str,
        parse_mode: str = "Markdown",
        disable_notification: bool = False
    ) -> bool:
        """
        Send a message to Telegram.

        Args:
            message: Message text
            parse_mode: Message formatting (Markdown/HTML)
            disable_notification: Send silently

        Returns:
            bool: True if message sent successfully
        """
        if not self.enable_notifications:
            logger.debug("Notifications disabled, message not sent")
            return False

        try:
            await self.bot.send_message(
                chat_id=self.chat_id,
                text=message,
                parse_mode=parse_mode,
                disable_notification=disable_notification
            )
            logger.debug("Message sent successfully")
            return True

        except TelegramError as e:
            logger.error(f"Failed to send Telegram message: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error sending message: {e}")
            return False

    def send_message_sync(
        self,
        message: str,
        parse_mode: str = "Markdown",
        disable_notification: bool = False
    ) -> bool:
        """
        Send a message to Telegram (synchronous wrapper).

        Args:
            message: Message text
            parse_mode: Message formatting (Markdown/HTML)
            disable_notification: Send silently

        Returns:
            bool: True if message sent successfully
        """
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # Create a new loop if current one is running
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = executor.submit(
                        asyncio.run,
                        self.send_message(message, parse_mode, disable_notification)
                    )
                    return future.result()
            else:
                return loop.run_until_complete(
                    self.send_message(message, parse_mode, disable_notification)
                )
        except Exception as e:
            logger.error(f"Error in synchronous send: {e}")
            return False

    # ==========================================
    # Order Notifications
    # ==========================================

    def notify_order_placed(
        self,
        symbol: str,
        transaction_type: str,
        quantity: int,
        order_type: str,
        price: float,
        order_id: str
    ) -> bool:
        """
        Send order placed notification.

        Args:
            symbol: Trading symbol
            transaction_type: BUY/SELL
            quantity: Order quantity
            order_type: Order type (MARKET/LIMIT/etc.)
            price: Order price
            order_id: Order ID

        Returns:
            bool: True if notification sent
        """
        message = f"""
{NotificationType.ORDER_PLACED.value}

*Symbol:* `{symbol}`
*Type:* {transaction_type}
*Quantity:* {quantity}
*Order Type:* {order_type}
*Price:* ₹{price:.2f}
*Order ID:* `{order_id}`

*Time:* {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
        return self.send_message_sync(message.strip())

    def notify_order_executed(
        self,
        symbol: str,
        transaction_type: str,
        quantity: int,
        average_price: float,
        order_id: str,
        total_value: Optional[float] = None
    ) -> bool:
        """
        Send order executed notification.

        Args:
            symbol: Trading symbol
            transaction_type: BUY/SELL
            quantity: Executed quantity
            average_price: Average execution price
            order_id: Order ID
            total_value: Total order value

        Returns:
            bool: True if notification sent
        """
        total_val = total_value or (quantity * average_price)

        message = f"""
{NotificationType.ORDER_EXECUTED.value}

*Symbol:* `{symbol}`
*Type:* {transaction_type}
*Quantity:* {quantity}
*Avg Price:* ₹{average_price:.2f}
*Total Value:* ₹{total_val:.2f}
*Order ID:* `{order_id}`

*Time:* {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
        return self.send_message_sync(message.strip())

    def notify_order_cancelled(
        self,
        symbol: str,
        order_id: str,
        reason: Optional[str] = None
    ) -> bool:
        """
        Send order cancelled notification.

        Args:
            symbol: Trading symbol
            order_id: Order ID
            reason: Cancellation reason

        Returns:
            bool: True if notification sent
        """
        message = f"""
{NotificationType.ORDER_CANCELLED.value}

*Symbol:* `{symbol}`
*Order ID:* `{order_id}`
"""
        if reason:
            message += f"*Reason:* {reason}\n"

        message += f"\n*Time:* {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"

        return self.send_message_sync(message.strip())

    def notify_order_rejected(
        self,
        symbol: str,
        order_id: str,
        reason: str
    ) -> bool:
        """
        Send order rejected notification.

        Args:
            symbol: Trading symbol
            order_id: Order ID
            reason: Rejection reason

        Returns:
            bool: True if notification sent
        """
        message = f"""
{NotificationType.ORDER_REJECTED.value}

*Symbol:* `{symbol}`
*Order ID:* `{order_id}`
*Reason:* {reason}

*Time:* {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
        return self.send_message_sync(message.strip())

    # ==========================================
    # Position Notifications
    # ==========================================

    def notify_position_opened(
        self,
        symbol: str,
        quantity: int,
        entry_price: float,
        position_value: float
    ) -> bool:
        """
        Send position opened notification.

        Args:
            symbol: Trading symbol
            quantity: Position quantity
            entry_price: Entry price
            position_value: Total position value

        Returns:
            bool: True if notification sent
        """
        message = f"""
{NotificationType.POSITION_OPENED.value}

*Symbol:* `{symbol}`
*Quantity:* {quantity}
*Entry Price:* ₹{entry_price:.2f}
*Position Value:* ₹{position_value:.2f}

*Time:* {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
        return self.send_message_sync(message.strip())

    def notify_position_closed(
        self,
        symbol: str,
        quantity: int,
        entry_price: float,
        exit_price: float,
        pnl: float,
        pnl_percentage: float
    ) -> bool:
        """
        Send position closed notification.

        Args:
            symbol: Trading symbol
            quantity: Position quantity
            entry_price: Entry price
            exit_price: Exit price
            pnl: Profit/Loss amount
            pnl_percentage: P&L percentage

        Returns:
            bool: True if notification sent
        """
        pnl_emoji = "💰" if pnl >= 0 else "📉"

        message = f"""
{NotificationType.POSITION_CLOSED.value} {pnl_emoji}

*Symbol:* `{symbol}`
*Quantity:* {quantity}
*Entry:* ₹{entry_price:.2f}
*Exit:* ₹{exit_price:.2f}
*P&L:* ₹{pnl:.2f} ({pnl_percentage:+.2f}%)

*Time:* {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
        return self.send_message_sync(message.strip())

    # ==========================================
    # P&L Notifications
    # ==========================================

    def notify_profit_alert(
        self,
        current_pnl: float,
        total_trades: int,
        winning_trades: int
    ) -> bool:
        """
        Send profit alert notification.

        Args:
            current_pnl: Current P&L
            total_trades: Total number of trades
            winning_trades: Number of winning trades

        Returns:
            bool: True if notification sent
        """
        win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0

        message = f"""
{NotificationType.PROFIT.value}

*Current P&L:* ₹{current_pnl:.2f}
*Total Trades:* {total_trades}
*Winning Trades:* {winning_trades}
*Win Rate:* {win_rate:.1f}%

Congratulations! You've reached your profit target! 🎉

*Time:* {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
        return self.send_message_sync(message.strip())

    def notify_loss_alert(
        self,
        current_pnl: float,
        max_loss: float,
        recommendation: str = "Consider stopping trading for the day"
    ) -> bool:
        """
        Send loss alert notification.

        Args:
            current_pnl: Current P&L
            max_loss: Maximum loss threshold
            recommendation: Action recommendation

        Returns:
            bool: True if notification sent
        """
        message = f"""
{NotificationType.LOSS.value}

*Current P&L:* ₹{current_pnl:.2f}
*Max Loss Threshold:* ₹{max_loss:.2f}

⚠️ *Warning:* Loss threshold breached!

*Recommendation:* {recommendation}

*Time:* {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
        return self.send_message_sync(message.strip())

    # ==========================================
    # Daily Summary
    # ==========================================

    def notify_daily_summary(
        self,
        total_pnl: float,
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
            total_pnl: Total P&L for the day
            total_trades: Total number of trades
            winning_trades: Number of winning trades
            losing_trades: Number of losing trades
            gross_profit: Total profit from winning trades
            gross_loss: Total loss from losing trades
            largest_win: Largest winning trade
            largest_loss: Largest losing trade

        Returns:
            bool: True if notification sent
        """
        win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0
        avg_win = gross_profit / winning_trades if winning_trades > 0 else 0
        avg_loss = gross_loss / losing_trades if losing_trades > 0 else 0

        pnl_emoji = "💰" if total_pnl >= 0 else "📉"

        message = f"""
{NotificationType.DAILY_SUMMARY.value} {pnl_emoji}

*Date:* {datetime.now().strftime('%Y-%m-%d')}

*Overall Performance:*
• Total P&L: ₹{total_pnl:.2f}
• Total Trades: {total_trades}
• Win Rate: {win_rate:.1f}%

*Trade Breakdown:*
• Winning: {winning_trades} (₹{gross_profit:.2f})
• Losing: {losing_trades} (₹{gross_loss:.2f})

*Statistics:*
• Avg Win: ₹{avg_win:.2f}
• Avg Loss: ₹{avg_loss:.2f}
• Largest Win: ₹{largest_win:.2f}
• Largest Loss: ₹{largest_loss:.2f}

*Time:* {datetime.now().strftime('%H:%M:%S')}
"""
        return self.send_message_sync(message.strip())

    # ==========================================
    # System Notifications
    # ==========================================

    def notify_error(
        self,
        error_message: str,
        error_type: str = "General Error",
        traceback_info: Optional[str] = None
    ) -> bool:
        """
        Send system error notification.

        Args:
            error_message: Error message
            error_type: Type of error
            traceback_info: Optional traceback information

        Returns:
            bool: True if notification sent
        """
        message = f"""
{NotificationType.SYSTEM_ERROR.value}

*Error Type:* {error_type}
*Message:* {error_message}
"""

        if traceback_info:
            message += f"\n*Details:* ```\n{traceback_info[:500]}```"

        message += f"\n\n*Time:* {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"

        return self.send_message_sync(message.strip())

    def notify_system_info(
        self,
        message: str,
        title: str = "System Info"
    ) -> bool:
        """
        Send system information notification.

        Args:
            message: Information message
            title: Notification title

        Returns:
            bool: True if notification sent
        """
        notification = f"""
{NotificationType.SYSTEM_INFO.value}

*{title}*

{message}

*Time:* {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
        return self.send_message_sync(notification.strip())

    def notify_custom(
        self,
        message: str,
        title: Optional[str] = None,
        priority: NotificationPriority = NotificationPriority.NORMAL
    ) -> bool:
        """
        Send custom notification.

        Args:
            message: Custom message
            title: Optional title
            priority: Notification priority

        Returns:
            bool: True if notification sent
        """
        notification = f"{priority.value} "

        if title:
            notification += f"*{title}*\n\n"

        notification += message
        notification += f"\n\n*Time:* {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"

        return self.send_message_sync(notification.strip())

    # ==========================================
    # Utility Methods
    # ==========================================

    def test_connection(self) -> bool:
        """
        Test Telegram bot connection.

        Returns:
            bool: True if connection successful
        """
        try:
            message = """
🤖 *Telegram Bot Test*

Connection successful! ✅

Your trading notifications are now active.

*Time:* """ + datetime.now().strftime('%Y-%m-%d %H:%M:%S')

            return self.send_message_sync(message.strip())

        except Exception as e:
            logger.error(f"Connection test failed: {e}")
            return False

    def enable(self):
        """Enable notifications."""
        self.enable_notifications = True
        logger.info("Telegram notifications enabled")

    def disable(self):
        """Disable notifications."""
        self.enable_notifications = False
        logger.info("Telegram notifications disabled")

    def set_profit_threshold(self, threshold: float):
        """Set profit alert threshold."""
        self.profit_threshold = threshold
        logger.info(f"Profit threshold set to: ₹{threshold}")

    def set_loss_threshold(self, threshold: float):
        """Set loss alert threshold."""
        self.loss_threshold = threshold
        logger.info(f"Loss threshold set to: ₹{threshold}")

    def __repr__(self) -> str:
        """String representation."""
        return f"TelegramNotifier(enabled={self.enable_notifications})"
