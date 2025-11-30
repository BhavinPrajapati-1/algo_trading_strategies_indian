"""
Backtesting Framework for Trading Strategies

Replay historical data through trading strategies to evaluate performance
before deploying to live markets.

Features:
- Historical data replay
- Walk-forward testing
- Parameter optimization
- Slippage and commission modeling
- Comprehensive performance analytics

Author: Trading Analytics Team
"""

import sqlite3
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Callable, Any
from dataclasses import dataclass, field
from pathlib import Path
import json
import logging
from collections import defaultdict


@dataclass
class BacktestTrade:
    """Record of a backtested trade."""
    entry_time: datetime
    exit_time: Optional[datetime] = None
    symbol: str = ""
    action: str = ""  # BUY/SELL
    entry_price: float = 0.0
    exit_price: float = 0.0
    quantity: int = 0
    pnl: float = 0.0
    commission: float = 0.0
    slippage: float = 0.0
    status: str = "OPEN"  # OPEN/CLOSED
    strategy_signal: str = ""
    notes: str = ""


@dataclass
class BacktestResult:
    """Comprehensive backtest results."""
    strategy_name: str
    start_date: datetime
    end_date: datetime
    initial_capital: float
    final_capital: float

    # Trade Statistics
    total_trades: int = 0
    winning_trades: int = 0
    losing_trades: int = 0

    # P&L Metrics
    total_pnl: float = 0.0
    gross_profit: float = 0.0
    gross_loss: float = 0.0
    net_profit: float = 0.0
    total_commission: float = 0.0
    total_slippage: float = 0.0

    # Performance Ratios
    win_rate: float = 0.0
    profit_factor: float = 0.0
    average_win: float = 0.0
    average_loss: float = 0.0
    largest_win: float = 0.0
    largest_loss: float = 0.0

    # Risk Metrics
    max_drawdown: float = 0.0
    max_drawdown_pct: float = 0.0
    sharpe_ratio: float = 0.0
    sortino_ratio: float = 0.0
    calmar_ratio: float = 0.0

    # Trade Details
    trades: List[BacktestTrade] = field(default_factory=list)
    equity_curve: List[Tuple[datetime, float]] = field(default_factory=list)
    daily_returns: List[float] = field(default_factory=list)

    # Additional Metrics
    max_consecutive_wins: int = 0
    max_consecutive_losses: int = 0
    average_trade_duration: float = 0.0  # in hours
    total_bars: int = 0

    # Parameter Optimization Results (if applicable)
    optimized_parameters: Dict[str, Any] = field(default_factory=dict)


@dataclass
class BacktestConfig:
    """Configuration for backtesting."""
    initial_capital: float = 100000.0
    commission_per_trade: float = 20.0  # Flat fee
    commission_pct: float = 0.0003  # 0.03% per trade
    slippage_pct: float = 0.001  # 0.1% slippage
    position_sizing: str = "fixed"  # fixed, percentage, kelly
    position_size: float = 1.0  # Number of lots or percentage
    max_positions: int = 10
    enable_stop_loss: bool = True
    enable_take_profit: bool = True
    risk_free_rate: float = 0.06  # 6% annual


class HistoricalDataProvider:
    """
    Provide historical market data for backtesting.

    Supports loading from:
    - PostgreSQL database
    - CSV files
    - SQLite database
    """

    def __init__(self, data_source: str, data_path: Optional[str] = None):
        """
        Initialize data provider.

        Args:
            data_source: Type of data source ('postgres', 'csv', 'sqlite')
            data_path: Path to data file (for csv/sqlite)
        """
        self.data_source = data_source
        self.data_path = data_path
        self.logger = logging.getLogger(__name__)

    def load_data(self, symbol: str, start_date: datetime,
                  end_date: datetime, timeframe: str = '1min') -> pd.DataFrame:
        """
        Load historical data for a symbol.

        Args:
            symbol: Trading symbol
            start_date: Start date
            end_date: End date
            timeframe: Timeframe ('1min', '5min', '15min', '1hour', '1day')

        Returns:
            DataFrame with columns: timestamp, open, high, low, close, volume
        """
        if self.data_source == 'csv':
            return self._load_from_csv(symbol, start_date, end_date)
        elif self.data_source == 'sqlite':
            return self._load_from_sqlite(symbol, start_date, end_date)
        elif self.data_source == 'postgres':
            return self._load_from_postgres(symbol, start_date, end_date)
        else:
            raise ValueError(f"Unsupported data source: {self.data_source}")

    def _load_from_csv(self, symbol: str, start_date: datetime,
                       end_date: datetime) -> pd.DataFrame:
        """Load data from CSV file."""
        if not self.data_path:
            raise ValueError("data_path required for CSV data source")

        csv_path = Path(self.data_path) / f"{symbol}.csv"

        if not csv_path.exists():
            self.logger.error(f"CSV file not found: {csv_path}")
            return pd.DataFrame()

        df = pd.read_csv(csv_path)

        # Convert timestamp column
        if 'timestamp' in df.columns:
            df['timestamp'] = pd.to_datetime(df['timestamp'])
        elif 'date' in df.columns:
            df['timestamp'] = pd.to_datetime(df['date'])
            df = df.drop('date', axis=1)

        # Filter by date range
        df = df[(df['timestamp'] >= start_date) & (df['timestamp'] <= end_date)]

        return df.sort_values('timestamp').reset_index(drop=True)

    def _load_from_sqlite(self, symbol: str, start_date: datetime,
                         end_date: datetime) -> pd.DataFrame:
        """Load data from SQLite database."""
        if not self.data_path:
            raise ValueError("data_path required for SQLite data source")

        conn = sqlite3.connect(self.data_path)

        query = """
            SELECT timestamp, open, high, low, close, volume
            FROM historical_data
            WHERE symbol = ? AND timestamp BETWEEN ? AND ?
            ORDER BY timestamp
        """

        df = pd.read_sql_query(
            query,
            conn,
            params=(symbol, start_date.isoformat(), end_date.isoformat())
        )

        conn.close()

        if not df.empty:
            df['timestamp'] = pd.to_datetime(df['timestamp'])

        return df

    def _load_from_postgres(self, symbol: str, start_date: datetime,
                           end_date: datetime) -> pd.DataFrame:
        """Load data from PostgreSQL database."""
        try:
            import psycopg2
            from psycopg2 import sql
        except ImportError:
            self.logger.error("psycopg2 not installed. Install with: pip install psycopg2-binary")
            return pd.DataFrame()

        # Connection parameters from environment
        import os
        conn_params = {
            'host': os.getenv('DB_HOST', 'localhost'),
            'port': os.getenv('DB_PORT', '5432'),
            'database': os.getenv('DB_NAME', 'trading_data'),
            'user': os.getenv('DB_USER', 'postgres'),
            'password': os.getenv('DB_PASSWORD', '')
        }

        try:
            conn = psycopg2.connect(**conn_params)
            query = """
                SELECT timestamp, open, high, low, close, volume
                FROM historical_data
                WHERE symbol = %s AND timestamp BETWEEN %s AND %s
                ORDER BY timestamp
            """

            df = pd.read_sql_query(
                query,
                conn,
                params=(symbol, start_date, end_date)
            )

            conn.close()

            if not df.empty:
                df['timestamp'] = pd.to_datetime(df['timestamp'])

            return df

        except Exception as e:
            self.logger.error(f"Error loading from PostgreSQL: {e}")
            return pd.DataFrame()


class Backtester:
    """
    Backtest trading strategies on historical data.

    Example usage:
        backtester = Backtester(config, data_provider)
        result = backtester.run_backtest(strategy_func, symbol, start_date, end_date)
        backtester.save_results(result)
    """

    def __init__(self, config: BacktestConfig,
                 data_provider: HistoricalDataProvider):
        """
        Initialize backtester.

        Args:
            config: Backtest configuration
            data_provider: Historical data provider
        """
        self.config = config
        self.data_provider = data_provider
        self.logger = logging.getLogger(__name__)

        # State variables
        self.current_capital = config.initial_capital
        self.positions: Dict[str, BacktestTrade] = {}
        self.trades: List[BacktestTrade] = []
        self.equity_curve: List[Tuple[datetime, float]] = []

    def run_backtest(self, strategy_func: Callable,
                    symbol: str,
                    start_date: datetime,
                    end_date: datetime,
                    strategy_params: Optional[Dict] = None) -> BacktestResult:
        """
        Run backtest for a strategy.

        Args:
            strategy_func: Strategy function that returns signals
                          Signature: func(data: pd.DataFrame, params: dict) -> str
                          Returns: 'BUY', 'SELL', or 'HOLD'
            symbol: Trading symbol
            start_date: Backtest start date
            end_date: Backtest end date
            strategy_params: Parameters to pass to strategy

        Returns:
            BacktestResult object
        """
        self.logger.info(f"Starting backtest: {symbol} from {start_date} to {end_date}")

        # Load historical data
        data = self.data_provider.load_data(symbol, start_date, end_date)

        if data.empty:
            self.logger.error("No historical data loaded")
            return BacktestResult(
                strategy_name="Unknown",
                start_date=start_date,
                end_date=end_date,
                initial_capital=self.config.initial_capital,
                final_capital=self.config.initial_capital
            )

        # Reset state
        self.current_capital = self.config.initial_capital
        self.positions = {}
        self.trades = []
        self.equity_curve = []

        # Run simulation
        strategy_params = strategy_params or {}

        for idx, row in data.iterrows():
            current_time = row['timestamp']
            current_price = row['close']

            # Update equity curve
            equity = self._calculate_current_equity(current_price)
            self.equity_curve.append((current_time, equity))

            # Get strategy signal
            # Pass data up to current bar
            historical_data = data.iloc[:idx+1]
            signal = strategy_func(historical_data, strategy_params)

            # Execute trades based on signal
            if signal == 'BUY' and symbol not in self.positions:
                self._execute_buy(symbol, current_time, current_price)

            elif signal == 'SELL' and symbol in self.positions:
                self._execute_sell(symbol, current_time, current_price)

            # Check stop loss / take profit
            if self.config.enable_stop_loss or self.config.enable_take_profit:
                self._check_exit_conditions(symbol, current_time, current_price,
                                            strategy_params)

        # Close any remaining positions
        final_price = data.iloc[-1]['close']
        final_time = data.iloc[-1]['timestamp']

        for symbol in list(self.positions.keys()):
            self._execute_sell(symbol, final_time, final_price, forced=True)

        # Calculate results
        result = self._calculate_results(
            strategy_func.__name__,
            start_date,
            end_date,
            len(data)
        )

        self.logger.info(f"Backtest complete: {result.total_trades} trades, "
                        f"P&L: ₹{result.total_pnl:,.2f}")

        return result

    def _execute_buy(self, symbol: str, timestamp: datetime, price: float):
        """Execute buy order."""
        # Calculate position size
        quantity = self._calculate_position_size(price)

        if quantity == 0:
            return

        # Calculate costs
        gross_value = price * quantity
        commission = self.config.commission_per_trade + (gross_value * self.config.commission_pct)
        slippage = gross_value * self.config.slippage_pct

        total_cost = gross_value + commission + slippage

        # Check if we have enough capital
        if total_cost > self.current_capital:
            self.logger.debug(f"Insufficient capital for BUY: Need ₹{total_cost:,.2f}, Have ₹{self.current_capital:,.2f}")
            return

        # Create trade record
        trade = BacktestTrade(
            entry_time=timestamp,
            symbol=symbol,
            action='BUY',
            entry_price=price + (price * self.config.slippage_pct),  # Apply slippage
            quantity=quantity,
            commission=commission,
            slippage=slippage,
            status='OPEN'
        )

        self.positions[symbol] = trade
        self.current_capital -= total_cost

        self.logger.debug(f"BUY {quantity} {symbol} @ ₹{price:.2f} | Capital: ₹{self.current_capital:,.2f}")

    def _execute_sell(self, symbol: str, timestamp: datetime, price: float,
                     forced: bool = False):
        """Execute sell order."""
        if symbol not in self.positions:
            return

        position = self.positions[symbol]

        # Calculate P&L
        exit_price = price - (price * self.config.slippage_pct)  # Apply slippage
        gross_value = exit_price * position.quantity

        commission = self.config.commission_per_trade + (gross_value * self.config.commission_pct)
        slippage = gross_value * self.config.slippage_pct

        entry_value = position.entry_price * position.quantity
        pnl = gross_value - entry_value - commission - slippage - position.commission

        # Update trade record
        position.exit_time = timestamp
        position.exit_price = exit_price
        position.pnl = pnl
        position.status = 'CLOSED'
        position.notes = 'Forced close' if forced else 'Normal exit'

        # Update capital
        self.current_capital += gross_value - commission - slippage

        # Save trade
        self.trades.append(position)
        del self.positions[symbol]

        self.logger.debug(f"SELL {position.quantity} {symbol} @ ₹{price:.2f} | "
                         f"P&L: ₹{pnl:,.2f} | Capital: ₹{self.current_capital:,.2f}")

    def _calculate_position_size(self, price: float) -> int:
        """Calculate position size based on configuration."""
        if self.config.position_sizing == 'fixed':
            return int(self.config.position_size)

        elif self.config.position_sizing == 'percentage':
            # Use percentage of capital
            position_value = self.current_capital * self.config.position_size
            quantity = int(position_value / price)
            return quantity

        elif self.config.position_sizing == 'kelly':
            # Kelly criterion (simplified)
            # This would require historical win rate and risk/reward
            # For now, use conservative fixed percentage
            position_value = self.current_capital * 0.02  # 2% per trade
            quantity = int(position_value / price)
            return quantity

        return 0

    def _check_exit_conditions(self, symbol: str, timestamp: datetime,
                               current_price: float, params: Dict):
        """Check stop loss and take profit conditions."""
        if symbol not in self.positions:
            return

        position = self.positions[symbol]

        # Stop loss
        if self.config.enable_stop_loss:
            stop_loss_pct = params.get('stop_loss_pct', 0.05)  # 5% default
            stop_price = position.entry_price * (1 - stop_loss_pct)

            if current_price <= stop_price:
                self.logger.debug(f"Stop loss triggered for {symbol}")
                position.notes = 'Stop loss'
                self._execute_sell(symbol, timestamp, current_price)
                return

        # Take profit
        if self.config.enable_take_profit:
            take_profit_pct = params.get('take_profit_pct', 0.10)  # 10% default
            target_price = position.entry_price * (1 + take_profit_pct)

            if current_price >= target_price:
                self.logger.debug(f"Take profit triggered for {symbol}")
                position.notes = 'Take profit'
                self._execute_sell(symbol, timestamp, current_price)
                return

    def _calculate_current_equity(self, current_price: float) -> float:
        """Calculate current total equity."""
        equity = self.current_capital

        # Add unrealized P&L from open positions
        for symbol, position in self.positions.items():
            unrealized_pnl = (current_price - position.entry_price) * position.quantity
            equity += unrealized_pnl

        return equity

    def _calculate_results(self, strategy_name: str,
                          start_date: datetime,
                          end_date: datetime,
                          total_bars: int) -> BacktestResult:
        """Calculate comprehensive backtest results."""
        total_trades = len(self.trades)

        if total_trades == 0:
            return BacktestResult(
                strategy_name=strategy_name,
                start_date=start_date,
                end_date=end_date,
                initial_capital=self.config.initial_capital,
                final_capital=self.current_capital,
                total_bars=total_bars
            )

        # P&L calculations
        pnls = [t.pnl for t in self.trades]
        total_pnl = sum(pnls)
        total_commission = sum(t.commission for t in self.trades)
        total_slippage = sum(t.slippage for t in self.trades)

        winning_trades = sum(1 for pnl in pnls if pnl > 0)
        losing_trades = sum(1 for pnl in pnls if pnl < 0)

        gross_profit = sum(pnl for pnl in pnls if pnl > 0)
        gross_loss = abs(sum(pnl for pnl in pnls if pnl < 0))

        # Ratios
        win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0.0
        profit_factor = (gross_profit / gross_loss) if gross_loss > 0 else float('inf')

        wins = [pnl for pnl in pnls if pnl > 0]
        losses = [pnl for pnl in pnls if pnl < 0]

        average_win = (sum(wins) / len(wins)) if wins else 0.0
        average_loss = (sum(losses) / len(losses)) if losses else 0.0

        largest_win = max(wins) if wins else 0.0
        largest_loss = min(losses) if losses else 0.0

        # Risk metrics
        equity_values = [eq for _, eq in self.equity_curve]
        max_drawdown, max_dd_pct = self._calculate_max_drawdown(equity_values)

        daily_returns = self._calculate_daily_returns()
        sharpe_ratio = self._calculate_sharpe_ratio(daily_returns)
        sortino_ratio = self._calculate_sortino_ratio(daily_returns)
        calmar_ratio = (total_pnl / max_drawdown) if max_drawdown > 0 else 0.0

        # Consecutive stats
        max_consec_wins, max_consec_losses = self._calculate_consecutive_stats(pnls)

        # Trade duration
        durations = []
        for trade in self.trades:
            if trade.exit_time:
                duration = (trade.exit_time - trade.entry_time).total_seconds() / 3600
                durations.append(duration)

        average_duration = (sum(durations) / len(durations)) if durations else 0.0

        return BacktestResult(
            strategy_name=strategy_name,
            start_date=start_date,
            end_date=end_date,
            initial_capital=self.config.initial_capital,
            final_capital=self.current_capital,
            total_trades=total_trades,
            winning_trades=winning_trades,
            losing_trades=losing_trades,
            total_pnl=total_pnl,
            gross_profit=gross_profit,
            gross_loss=gross_loss,
            net_profit=total_pnl - total_commission - total_slippage,
            total_commission=total_commission,
            total_slippage=total_slippage,
            win_rate=win_rate,
            profit_factor=profit_factor,
            average_win=average_win,
            average_loss=average_loss,
            largest_win=largest_win,
            largest_loss=largest_loss,
            max_drawdown=max_drawdown,
            max_drawdown_pct=max_dd_pct,
            sharpe_ratio=sharpe_ratio,
            sortino_ratio=sortino_ratio,
            calmar_ratio=calmar_ratio,
            trades=self.trades,
            equity_curve=self.equity_curve,
            daily_returns=daily_returns,
            max_consecutive_wins=max_consec_wins,
            max_consecutive_losses=max_consec_losses,
            average_trade_duration=average_duration,
            total_bars=total_bars
        )

    def _calculate_max_drawdown(self, equity_values: List[float]) -> Tuple[float, float]:
        """Calculate maximum drawdown in absolute and percentage terms."""
        if not equity_values:
            return 0.0, 0.0

        peak = equity_values[0]
        max_dd = 0.0
        max_dd_pct = 0.0

        for equity in equity_values:
            if equity > peak:
                peak = equity

            drawdown = peak - equity
            drawdown_pct = (drawdown / peak * 100) if peak > 0 else 0.0

            if drawdown > max_dd:
                max_dd = drawdown
                max_dd_pct = drawdown_pct

        return max_dd, max_dd_pct

    def _calculate_daily_returns(self) -> List[float]:
        """Calculate daily returns from equity curve."""
        if len(self.equity_curve) < 2:
            return []

        # Group by date
        daily_equity = defaultdict(list)

        for timestamp, equity in self.equity_curve:
            date = timestamp.date()
            daily_equity[date].append(equity)

        # Get end-of-day equity for each day
        sorted_dates = sorted(daily_equity.keys())
        daily_returns = []

        for i in range(1, len(sorted_dates)):
            prev_equity = daily_equity[sorted_dates[i-1]][-1]
            curr_equity = daily_equity[sorted_dates[i]][-1]
            daily_return = curr_equity - prev_equity
            daily_returns.append(daily_return)

        return daily_returns

    def _calculate_sharpe_ratio(self, daily_returns: List[float]) -> float:
        """Calculate Sharpe ratio."""
        if len(daily_returns) < 2:
            return 0.0

        import statistics

        avg_return = statistics.mean(daily_returns)
        std_return = statistics.stdev(daily_returns)

        if std_return == 0:
            return 0.0

        # Annualized Sharpe (assuming 252 trading days)
        daily_rf = self.config.risk_free_rate / 252
        sharpe = (avg_return - daily_rf) / std_return * (252 ** 0.5)

        return sharpe

    def _calculate_sortino_ratio(self, daily_returns: List[float]) -> float:
        """Calculate Sortino ratio (uses downside deviation)."""
        if len(daily_returns) < 2:
            return 0.0

        import statistics

        avg_return = statistics.mean(daily_returns)
        downside_returns = [r for r in daily_returns if r < 0]

        if not downside_returns:
            return float('inf')

        downside_dev = statistics.stdev(downside_returns) if len(downside_returns) > 1 else 0.0

        if downside_dev == 0:
            return 0.0

        # Annualized Sortino
        daily_rf = self.config.risk_free_rate / 252
        sortino = (avg_return - daily_rf) / downside_dev * (252 ** 0.5)

        return sortino

    def _calculate_consecutive_stats(self, pnls: List[float]) -> Tuple[int, int]:
        """Calculate maximum consecutive wins and losses."""
        max_wins = 0
        max_losses = 0
        current_wins = 0
        current_losses = 0

        for pnl in pnls:
            if pnl > 0:
                current_wins += 1
                current_losses = 0
                max_wins = max(max_wins, current_wins)
            elif pnl < 0:
                current_losses += 1
                current_wins = 0
                max_losses = max(max_losses, current_losses)

        return max_wins, max_losses

    def save_results(self, result: BacktestResult,
                    output_dir: str = "reports/backtest"):
        """Save backtest results to file."""
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"backtest_{result.strategy_name}_{timestamp}"

        # Save JSON
        json_path = output_path / f"{filename}.json"
        self._save_json_results(result, json_path)

        # Save text report
        text_path = output_path / f"{filename}.txt"
        self._save_text_results(result, text_path)

        self.logger.info(f"Results saved to {output_path}")

    def _save_json_results(self, result: BacktestResult, filepath: Path):
        """Save results as JSON."""
        def default_serializer(obj):
            if isinstance(obj, datetime):
                return obj.isoformat()
            if hasattr(obj, '__dict__'):
                return {k: v for k, v in obj.__dict__.items() if not k.startswith('_')}
            return str(obj)

        with open(filepath, 'w') as f:
            json.dump(result, f, default=default_serializer, indent=2)

    def _save_text_results(self, result: BacktestResult, filepath: Path):
        """Save results as formatted text."""
        with open(filepath, 'w') as f:
            f.write("=" * 100 + "\n")
            f.write("BACKTEST RESULTS\n")
            f.write("=" * 100 + "\n\n")

            f.write(f"Strategy:          {result.strategy_name}\n")
            f.write(f"Period:            {result.start_date} to {result.end_date}\n")
            f.write(f"Initial Capital:   ₹{result.initial_capital:,.2f}\n")
            f.write(f"Final Capital:     ₹{result.final_capital:,.2f}\n")
            f.write(f"Return:            ₹{result.total_pnl:,.2f} ({result.total_pnl/result.initial_capital*100:.2f}%)\n\n")

            f.write("TRADE STATISTICS\n")
            f.write("-" * 100 + "\n")
            f.write(f"Total Trades:      {result.total_trades}\n")
            f.write(f"Winning Trades:    {result.winning_trades}\n")
            f.write(f"Losing Trades:     {result.losing_trades}\n")
            f.write(f"Win Rate:          {result.win_rate:.2f}%\n\n")

            f.write("P&L METRICS\n")
            f.write("-" * 100 + "\n")
            f.write(f"Gross Profit:      ₹{result.gross_profit:,.2f}\n")
            f.write(f"Gross Loss:        ₹{result.gross_loss:,.2f}\n")
            f.write(f"Net Profit:        ₹{result.net_profit:,.2f}\n")
            f.write(f"Profit Factor:     {result.profit_factor:.2f}\n")
            f.write(f"Average Win:       ₹{result.average_win:,.2f}\n")
            f.write(f"Average Loss:      ₹{result.average_loss:,.2f}\n")
            f.write(f"Largest Win:       ₹{result.largest_win:,.2f}\n")
            f.write(f"Largest Loss:      ₹{result.largest_loss:,.2f}\n\n")

            f.write("COSTS\n")
            f.write("-" * 100 + "\n")
            f.write(f"Total Commission:  ₹{result.total_commission:,.2f}\n")
            f.write(f"Total Slippage:    ₹{result.total_slippage:,.2f}\n\n")

            f.write("RISK METRICS\n")
            f.write("-" * 100 + "\n")
            f.write(f"Max Drawdown:      ₹{result.max_drawdown:,.2f} ({result.max_drawdown_pct:.2f}%)\n")
            f.write(f"Sharpe Ratio:      {result.sharpe_ratio:.2f}\n")
            f.write(f"Sortino Ratio:     {result.sortino_ratio:.2f}\n")
            f.write(f"Calmar Ratio:      {result.calmar_ratio:.2f}\n\n")

            f.write("OTHER STATISTICS\n")
            f.write("-" * 100 + "\n")
            f.write(f"Max Consecutive Wins:   {result.max_consecutive_wins}\n")
            f.write(f"Max Consecutive Losses: {result.max_consecutive_losses}\n")
            f.write(f"Avg Trade Duration:     {result.average_trade_duration:.2f} hours\n")
            f.write(f"Total Bars Processed:   {result.total_bars}\n")


def example_strategy(data: pd.DataFrame, params: Dict) -> str:
    """
    Example moving average crossover strategy.

    Args:
        data: Historical price data
        params: Strategy parameters (short_period, long_period)

    Returns:
        'BUY', 'SELL', or 'HOLD'
    """
    if len(data) < 2:
        return 'HOLD'

    short_period = params.get('short_period', 10)
    long_period = params.get('long_period', 20)

    if len(data) < long_period:
        return 'HOLD'

    # Calculate moving averages
    short_ma = data['close'].tail(short_period).mean()
    long_ma = data['close'].tail(long_period).mean()

    prev_short_ma = data['close'].iloc[-short_period-1:-1].mean()
    prev_long_ma = data['close'].iloc[-long_period-1:-1].mean()

    # Crossover logic
    if short_ma > long_ma and prev_short_ma <= prev_long_ma:
        return 'BUY'
    elif short_ma < long_ma and prev_short_ma >= prev_long_ma:
        return 'SELL'

    return 'HOLD'


def main():
    """Example usage."""
    # Setup
    config = BacktestConfig(
        initial_capital=100000.0,
        commission_per_trade=20.0,
        slippage_pct=0.001,
        position_sizing='percentage',
        position_size=0.10  # 10% of capital per trade
    )

    data_provider = HistoricalDataProvider(
        data_source='csv',
        data_path='historical_data'
    )

    backtester = Backtester(config, data_provider)

    # Run backtest
    result = backtester.run_backtest(
        strategy_func=example_strategy,
        symbol='NIFTY50',
        start_date=datetime(2023, 1, 1),
        end_date=datetime(2023, 12, 31),
        strategy_params={'short_period': 10, 'long_period': 20}
    )

    # Save results
    backtester.save_results(result)

    print(f"\nBacktest Complete!")
    print(f"Total P&L: ₹{result.total_pnl:,.2f}")
    print(f"Win Rate: {result.win_rate:.2f}%")
    print(f"Sharpe Ratio: {result.sharpe_ratio:.2f}")
    print(f"Max Drawdown: ₹{result.max_drawdown:,.2f} ({result.max_drawdown_pct:.2f}%)")


if __name__ == "__main__":
    main()
