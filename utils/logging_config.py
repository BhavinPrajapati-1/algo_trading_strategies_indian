"""
Logging Configuration Utility
==============================
Centralized logging configuration for all trading scripts.

This module provides a consistent logging setup across all strategies and utilities,
replacing scattered print() statements with structured, filterable logs.

Features:
    - Console and file logging
    - Rotating file handlers (prevents huge log files)
    - Different log levels for different components
    - Structured formatting with timestamps
    - Color-coded console output (optional)
    - Trading-specific log formatters

Usage:
    from utils.logging_config import setup_logger, get_logger

    # In your main script
    logger = setup_logger('banknifty_strategy', level='INFO')
    logger.info("Strategy started")
    logger.error("Order failed", extra={'order_id': '12345'})

    # In other modules
    logger = get_logger(__name__)
    logger.debug("Processing data...")
"""

import logging
import logging.handlers
import os
import sys
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any
import json


class TradingFormatter(logging.Formatter):
    """
    Custom formatter for trading logs with color support and structured output.
    """

    # ANSI color codes
    COLORS = {
        'DEBUG': '\033[36m',      # Cyan
        'INFO': '\033[32m',       # Green
        'WARNING': '\033[33m',    # Yellow
        'ERROR': '\033[31m',      # Red
        'CRITICAL': '\033[35m',   # Magenta
        'RESET': '\033[0m'        # Reset
    }

    def __init__(self, fmt: Optional[str] = None, datefmt: Optional[str] = None,
                 use_colors: bool = True):
        """
        Initialize the trading formatter.

        Args:
            fmt: Log message format string
            datefmt: Date format string
            use_colors: Whether to use color output (disable for file logs)
        """
        super().__init__(fmt, datefmt)
        self.use_colors = use_colors and sys.stdout.isatty()

    def format(self, record: logging.LogRecord) -> str:
        """
        Format the log record with optional colors and trading-specific fields.

        Args:
            record: LogRecord to format

        Returns:
            Formatted log string
        """
        # Add custom fields if present
        if hasattr(record, 'order_id'):
            record.msg = f"[Order: {record.order_id}] {record.msg}"
        if hasattr(record, 'symbol'):
            record.msg = f"[{record.symbol}] {record.msg}"
        if hasattr(record, 'strategy'):
            record.msg = f"[Strategy: {record.strategy}] {record.msg}"

        # Format the message
        formatted = super().format(record)

        # Add colors for console output
        if self.use_colors:
            color = self.COLORS.get(record.levelname, self.COLORS['RESET'])
            formatted = f"{color}{formatted}{self.COLORS['RESET']}"

        return formatted


class JSONFormatter(logging.Formatter):
    """
    JSON formatter for structured logging (useful for log aggregation tools).
    """

    def format(self, record: logging.LogRecord) -> str:
        """
        Format log record as JSON.

        Args:
            record: LogRecord to format

        Returns:
            JSON-formatted log string
        """
        log_data = {
            'timestamp': datetime.utcnow().isoformat(),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno
        }

        # Add exception info if present
        if record.exc_info:
            log_data['exception'] = self.formatException(record.exc_info)

        # Add custom fields
        for key in ['order_id', 'symbol', 'strategy', 'mtm', 'pnl']:
            if hasattr(record, key):
                log_data[key] = getattr(record, key)

        return json.dumps(log_data)


def setup_logger(
    name: str,
    level: str = 'INFO',
    log_dir: Optional[str] = None,
    console: bool = True,
    file_logging: bool = True,
    json_logging: bool = False,
    max_bytes: int = 10 * 1024 * 1024,  # 10MB
    backup_count: int = 5
) -> logging.Logger:
    """
    Set up a logger with console and/or file handlers.

    Args:
        name: Logger name (usually __name__ or strategy name)
        level: Logging level ('DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL')
        log_dir: Directory for log files (default: ./logs)
        console: Enable console output
        file_logging: Enable file logging
        json_logging: Use JSON format for file logs
        max_bytes: Maximum size of each log file before rotation
        backup_count: Number of backup files to keep

    Returns:
        Configured logger instance

    Example:
        >>> logger = setup_logger('my_strategy', level='DEBUG')
        >>> logger.info("Strategy started")
        >>> logger.error("Order failed", extra={'order_id': '12345'})
    """
    # Create logger
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, level.upper()))
    logger.propagate = False

    # Remove existing handlers to avoid duplicates
    logger.handlers.clear()

    # Console handler with colors
    if console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(getattr(logging, level.upper()))

        console_format = TradingFormatter(
            fmt='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S',
            use_colors=True
        )
        console_handler.setFormatter(console_format)
        logger.addHandler(console_handler)

    # File handler with rotation
    if file_logging:
        # Create logs directory
        if log_dir is None:
            log_dir = os.path.join(os.getcwd(), 'logs')

        log_path = Path(log_dir)
        log_path.mkdir(parents=True, exist_ok=True)

        # Create rotating file handler
        log_file = log_path / f"{name}.log"
        file_handler = logging.handlers.RotatingFileHandler(
            log_file,
            maxBytes=max_bytes,
            backupCount=backup_count
        )
        file_handler.setLevel(logging.DEBUG)  # Always DEBUG for files

        # Use JSON or standard format
        if json_logging:
            file_formatter = JSONFormatter()
        else:
            file_formatter = TradingFormatter(
                fmt='%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S',
                use_colors=False
            )

        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)

    return logger


def get_logger(name: str) -> logging.Logger:
    """
    Get an existing logger or create a new one with default settings.

    Args:
        name: Logger name (usually __name__)

    Returns:
        Logger instance

    Example:
        >>> logger = get_logger(__name__)
        >>> logger.info("Module loaded")
    """
    logger = logging.getLogger(name)

    # If logger has no handlers, set it up with defaults
    if not logger.handlers:
        return setup_logger(name)

    return logger


def setup_trade_logger(
    strategy_name: str,
    log_level: str = 'INFO'
) -> logging.Logger:
    """
    Set up a specialized logger for trade execution tracking.

    Creates separate log files for:
    - General strategy logs
    - Trade execution logs (orders, fills, positions)
    - Error logs (separate file for errors only)

    Args:
        strategy_name: Name of the trading strategy
        log_level: Logging level

    Returns:
        Configured logger instance

    Example:
        >>> logger = setup_trade_logger('banknifty_straddle')
        >>> logger.info("Strategy initialized")
        >>> logger.info("Order placed", extra={'order_id': '123', 'symbol': 'BANKNIFTY'})
    """
    logger = setup_logger(
        strategy_name,
        level=log_level,
        log_dir='logs/strategies',
        console=True,
        file_logging=True,
        json_logging=False
    )

    # Add separate handler for trade execution logs
    trade_log_path = Path('logs/trades')
    trade_log_path.mkdir(parents=True, exist_ok=True)

    trade_handler = logging.handlers.RotatingFileHandler(
        trade_log_path / f"{strategy_name}_trades.log",
        maxBytes=10 * 1024 * 1024,
        backupCount=10
    )
    trade_handler.setLevel(logging.INFO)
    trade_formatter = TradingFormatter(
        fmt='%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S',
        use_colors=False
    )
    trade_handler.setFormatter(trade_formatter)

    # Only log messages with 'trade' or 'order' in them
    class TradeFilter(logging.Filter):
        def filter(self, record):
            msg = record.getMessage().lower()
            return any(keyword in msg for keyword in ['order', 'trade', 'fill', 'position', 'mtm'])

    trade_handler.addFilter(TradeFilter())
    logger.addHandler(trade_handler)

    # Add separate handler for errors only
    error_log_path = Path('logs/errors')
    error_log_path.mkdir(parents=True, exist_ok=True)

    error_handler = logging.handlers.RotatingFileHandler(
        error_log_path / f"{strategy_name}_errors.log",
        maxBytes=5 * 1024 * 1024,
        backupCount=5
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(trade_formatter)
    logger.addHandler(error_handler)

    return logger


# Convenience function for quick setup
def quick_setup(name: str = 'trading', level: str = 'INFO') -> logging.Logger:
    """
    Quick logger setup for simple scripts.

    Args:
        name: Logger name
        level: Log level

    Returns:
        Configured logger

    Example:
        >>> from utils.logging_config import quick_setup
        >>> logger = quick_setup()
        >>> logger.info("Script started")
    """
    return setup_logger(name, level=level, console=True, file_logging=True)


# Module-level logger for this utility
_module_logger = logging.getLogger(__name__)
