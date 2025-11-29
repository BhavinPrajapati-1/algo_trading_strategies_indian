"""
Performance Metrics and Analytics Tracking
==========================================
Track and analyze trading performance metrics in real-time.

This module provides utilities for:
    - Real-time P&L tracking
    - Win/loss ratio calculation
    - Trade execution metrics
    - Strategy performance analytics
    - MTM (Mark-to-Market) calculations

Usage:
    from utils.metrics import MetricsTracker, TradeMetrics

    # Initialize tracker
    tracker = MetricsTracker(strategy_name='banknifty_straddle')

    # Record trades
    tracker.record_trade(
        symbol='BANKNIFTY2350045000CE',
        action='SELL',
        quantity=15,
        price=150.50,
        order_id='ORDER123'
    )

    # Get metrics
    metrics = tracker.get_metrics()
    print(f"Total P&L: {metrics['total_pnl']}")
"""

import time
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from pathlib import Path
from dataclasses import dataclass, asdict
from collections import defaultdict
import sqlite3
from threading import Lock


@dataclass
class Trade:
    """Represents a single trade execution."""

    timestamp: str
    symbol: str
    action: str  # BUY or SELL
    quantity: int
    price: float
    order_id: str
    strategy: str
    status: str = "COMPLETED"
    pnl: float = 0.0
    commission: float = 0.0
    notes: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """Convert trade to dictionary."""
        return asdict(self)


@dataclass
class PositionMetrics:
    """Metrics for a specific position."""

    symbol: str
    entry_price: float
    current_price: float
    quantity: int
    side: str  # LONG or SHORT
    unrealized_pnl: float
    realized_pnl: float
    entry_time: str
    holding_duration: float  # in seconds


class MetricsTracker:
    """
    Track and calculate trading performance metrics.

    Attributes:
        strategy_name: Name of the trading strategy
        db_path: Path to SQLite database for persistence
        trades: List of all trades
        positions: Current open positions
    """

    def __init__(self, strategy_name: str, db_path: Optional[str] = None, persist: bool = True):
        """
        Initialize metrics tracker.

        Args:
            strategy_name: Name of the strategy
            db_path: Path to metrics database (default: ./metrics/<strategy>.db)
            persist: Whether to persist metrics to database
        """
        self.strategy_name = strategy_name
        self.persist = persist
        self.trades: List[Trade] = []
        self.positions: Dict[str, Dict[str, Any]] = {}
        self.daily_stats: Dict[str, Dict[str, float]] = defaultdict(
            lambda: {
                "total_trades": 0,
                "winning_trades": 0,
                "losing_trades": 0,
                "total_pnl": 0.0,
                "gross_profit": 0.0,
                "gross_loss": 0.0,
            }
        )

        # Thread safety
        self._lock = Lock()

        # Database setup
        if persist:
            if db_path is None:
                metrics_dir = Path("metrics")
                metrics_dir.mkdir(exist_ok=True)
                db_path = metrics_dir / f"{strategy_name}_metrics.db"

            self.db_path = db_path
            self._setup_database()

    def _setup_database(self):
        """Set up SQLite database for metrics persistence."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            # Trades table
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS trades (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    symbol TEXT NOT NULL,
                    action TEXT NOT NULL,
                    quantity INTEGER NOT NULL,
                    price REAL NOT NULL,
                    order_id TEXT UNIQUE,
                    strategy TEXT NOT NULL,
                    status TEXT DEFAULT 'COMPLETED',
                    pnl REAL DEFAULT 0.0,
                    commission REAL DEFAULT 0.0,
                    notes TEXT
                )
            """
            )

            # Daily metrics table
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS daily_metrics (
                    date TEXT PRIMARY KEY,
                    strategy TEXT NOT NULL,
                    total_trades INTEGER DEFAULT 0,
                    winning_trades INTEGER DEFAULT 0,
                    losing_trades INTEGER DEFAULT 0,
                    total_pnl REAL DEFAULT 0.0,
                    gross_profit REAL DEFAULT 0.0,
                    gross_loss REAL DEFAULT 0.0,
                    max_drawdown REAL DEFAULT 0.0,
                    sharpe_ratio REAL DEFAULT 0.0
                )
            """
            )

            # Positions table
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS positions (
                    symbol TEXT PRIMARY KEY,
                    strategy TEXT NOT NULL,
                    entry_price REAL NOT NULL,
                    current_price REAL,
                    quantity INTEGER NOT NULL,
                    side TEXT NOT NULL,
                    entry_time TEXT NOT NULL,
                    unrealized_pnl REAL DEFAULT 0.0,
                    realized_pnl REAL DEFAULT 0.0
                )
            """
            )

            conn.commit()

    def record_trade(
        self,
        symbol: str,
        action: str,
        quantity: int,
        price: float,
        order_id: str,
        pnl: float = 0.0,
        commission: float = 0.0,
        notes: str = "",
    ) -> Trade:
        """
        Record a trade execution.

        Args:
            symbol: Trading symbol
            action: BUY or SELL
            quantity: Number of contracts/shares
            price: Execution price
            order_id: Unique order identifier
            pnl: Realized P&L for this trade
            commission: Brokerage and charges
            notes: Additional notes

        Returns:
            Trade object
        """
        with self._lock:
            trade = Trade(
                timestamp=datetime.now().isoformat(),
                symbol=symbol,
                action=action.upper(),
                quantity=quantity,
                price=price,
                order_id=order_id,
                strategy=self.strategy_name,
                pnl=pnl,
                commission=commission,
                notes=notes,
            )

            self.trades.append(trade)

            # Update daily stats
            today = datetime.now().strftime("%Y-%m-%d")
            self.daily_stats[today]["total_trades"] += 1

            if pnl > 0:
                self.daily_stats[today]["winning_trades"] += 1
                self.daily_stats[today]["gross_profit"] += pnl
            elif pnl < 0:
                self.daily_stats[today]["losing_trades"] += 1
                self.daily_stats[today]["gross_loss"] += abs(pnl)

            self.daily_stats[today]["total_pnl"] += pnl

            # Update position
            self._update_position(symbol, action, quantity, price)

            # Persist to database
            if self.persist:
                self._save_trade_to_db(trade)

            return trade

    def _update_position(self, symbol: str, action: str, quantity: int, price: float):
        """Update position tracking based on trade."""
        if symbol not in self.positions:
            # New position
            self.positions[symbol] = {
                "entry_price": price,
                "current_price": price,
                "quantity": quantity if action == "BUY" else -quantity,
                "side": "LONG" if action == "BUY" else "SHORT",
                "entry_time": datetime.now().isoformat(),
                "unrealized_pnl": 0.0,
                "realized_pnl": 0.0,
            }
        else:
            # Existing position - update or close
            pos = self.positions[symbol]
            if action == "BUY":
                new_qty = pos["quantity"] + quantity
            else:
                new_qty = pos["quantity"] - quantity

            if new_qty == 0:
                # Position closed
                del self.positions[symbol]
            else:
                pos["quantity"] = new_qty
                pos["current_price"] = price

    def update_position_price(self, symbol: str, current_price: float):
        """
        Update current price for a position (for MTM calculation).

        Args:
            symbol: Trading symbol
            current_price: Current market price
        """
        with self._lock:
            if symbol in self.positions:
                pos = self.positions[symbol]
                pos["current_price"] = current_price

                # Calculate unrealized P&L
                if pos["side"] == "LONG":
                    pos["unrealized_pnl"] = (current_price - pos["entry_price"]) * pos["quantity"]
                else:
                    pos["unrealized_pnl"] = (pos["entry_price"] - current_price) * abs(pos["quantity"])

    def get_metrics(self, date: Optional[str] = None) -> Dict[str, Any]:
        """
        Get performance metrics.

        Args:
            date: Date for metrics (default: today, format: YYYY-MM-DD)

        Returns:
            Dictionary of metrics
        """
        if date is None:
            date = datetime.now().strftime("%Y-%m-%d")

        with self._lock:
            stats = self.daily_stats[date]

            # Calculate additional metrics
            total_trades = stats["total_trades"]
            winning_trades = stats["winning_trades"]
            losing_trades = stats["losing_trades"]

            win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0.0

            avg_win = (stats["gross_profit"] / winning_trades) if winning_trades > 0 else 0.0
            avg_loss = (stats["gross_loss"] / losing_trades) if losing_trades > 0 else 0.0

            profit_factor = (stats["gross_profit"] / stats["gross_loss"]) if stats["gross_loss"] > 0 else 0.0

            # Calculate unrealized P&L from open positions
            unrealized_pnl = sum(pos["unrealized_pnl"] for pos in self.positions.values())

            return {
                "date": date,
                "strategy": self.strategy_name,
                "total_trades": total_trades,
                "winning_trades": winning_trades,
                "losing_trades": losing_trades,
                "win_rate": round(win_rate, 2),
                "total_pnl": round(stats["total_pnl"], 2),
                "gross_profit": round(stats["gross_profit"], 2),
                "gross_loss": round(stats["gross_loss"], 2),
                "average_win": round(avg_win, 2),
                "average_loss": round(avg_loss, 2),
                "profit_factor": round(profit_factor, 2),
                "unrealized_pnl": round(unrealized_pnl, 2),
                "open_positions": len(self.positions),
            }

    def get_position_metrics(self, symbol: str) -> Optional[PositionMetrics]:
        """
        Get metrics for a specific position.

        Args:
            symbol: Trading symbol

        Returns:
            PositionMetrics object or None if position doesn't exist
        """
        with self._lock:
            if symbol not in self.positions:
                return None

            pos = self.positions[symbol]
            entry_time = datetime.fromisoformat(pos["entry_time"])
            duration = (datetime.now() - entry_time).total_seconds()

            return PositionMetrics(
                symbol=symbol,
                entry_price=pos["entry_price"],
                current_price=pos["current_price"],
                quantity=pos["quantity"],
                side=pos["side"],
                unrealized_pnl=pos["unrealized_pnl"],
                realized_pnl=pos["realized_pnl"],
                entry_time=pos["entry_time"],
                holding_duration=duration,
            )

    def _save_trade_to_db(self, trade: Trade):
        """Save trade to database."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    INSERT OR IGNORE INTO trades
                    (timestamp, symbol, action, quantity, price, order_id, strategy, status, pnl, commission, notes)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                    (
                        trade.timestamp,
                        trade.symbol,
                        trade.action,
                        trade.quantity,
                        trade.price,
                        trade.order_id,
                        trade.strategy,
                        trade.status,
                        trade.pnl,
                        trade.commission,
                        trade.notes,
                    ),
                )
                conn.commit()
        except Exception as e:
            # Log error but don't crash
            print(f"Error saving trade to DB: {e}")

    def save_daily_metrics(self, date: Optional[str] = None):
        """
        Save daily metrics to database.

        Args:
            date: Date to save (default: today)
        """
        if date is None:
            date = datetime.now().strftime("%Y-%m-%d")

        if not self.persist:
            return

        metrics = self.get_metrics(date)

        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    INSERT OR REPLACE INTO daily_metrics
                    (date, strategy, total_trades, winning_trades, losing_trades,
                     total_pnl, gross_profit, gross_loss)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                    (
                        date,
                        self.strategy_name,
                        metrics["total_trades"],
                        metrics["winning_trades"],
                        metrics["losing_trades"],
                        metrics["total_pnl"],
                        metrics["gross_profit"],
                        metrics["gross_loss"],
                    ),
                )
                conn.commit()
        except Exception as e:
            print(f"Error saving daily metrics: {e}")

    def export_metrics_json(self, filepath: Optional[str] = None) -> str:
        """
        Export metrics to JSON file.

        Args:
            filepath: Output file path (default: ./metrics/<strategy>_<date>.json)

        Returns:
            Path to exported file
        """
        if filepath is None:
            date = datetime.now().strftime("%Y%m%d")
            filepath = f"metrics/{self.strategy_name}_{date}.json"

        Path(filepath).parent.mkdir(parents=True, exist_ok=True)

        metrics = self.get_metrics()
        metrics["trades"] = [trade.to_dict() for trade in self.trades[-100:]]  # Last 100 trades
        metrics["positions"] = self.positions

        with open(filepath, "w") as f:
            json.dump(metrics, f, indent=2)

        return filepath

    def reset_daily(self):
        """Reset daily metrics (call at start of new trading day)."""
        with self._lock:
            today = datetime.now().strftime("%Y-%m-%d")
            if today in self.daily_stats:
                # Save yesterday's metrics
                self.save_daily_metrics(today)

            # Clear today's stats
            self.daily_stats[today] = {
                "total_trades": 0,
                "winning_trades": 0,
                "losing_trades": 0,
                "total_pnl": 0.0,
                "gross_profit": 0.0,
                "gross_loss": 0.0,
            }


def calculate_sharpe_ratio(returns: List[float], risk_free_rate: float = 0.05) -> float:
    """
    Calculate Sharpe ratio for a series of returns.

    Args:
        returns: List of period returns
        risk_free_rate: Annual risk-free rate (default: 5%)

    Returns:
        Sharpe ratio
    """
    if not returns or len(returns) < 2:
        return 0.0

    import numpy as np

    returns_array = np.array(returns)
    excess_returns = returns_array - (risk_free_rate / 252)  # Daily risk-free rate

    if excess_returns.std() == 0:
        return 0.0

    return (excess_returns.mean() / excess_returns.std()) * np.sqrt(252)


def calculate_max_drawdown(equity_curve: List[float]) -> Tuple[float, int, int]:
    """
    Calculate maximum drawdown from equity curve.

    Args:
        equity_curve: List of equity values over time

    Returns:
        Tuple of (max_drawdown_pct, peak_index, trough_index)
    """
    if not equity_curve or len(equity_curve) < 2:
        return 0.0, 0, 0

    import numpy as np

    equity = np.array(equity_curve)
    running_max = np.maximum.accumulate(equity)
    drawdown = (equity - running_max) / running_max

    max_dd_idx = np.argmin(drawdown)
    max_dd = drawdown[max_dd_idx]

    # Find peak before this drawdown
    peak_idx = np.argmax(equity[: max_dd_idx + 1]) if max_dd_idx > 0 else 0

    return abs(max_dd) * 100, peak_idx, max_dd_idx
