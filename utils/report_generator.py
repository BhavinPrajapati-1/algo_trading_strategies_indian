"""
Comprehensive Trade Report Generator

This module generates detailed trading reports for daily, weekly, and monthly periods.
Supports HTML, PDF, and JSON output formats with comprehensive analytics.

Author: Trading Analytics Team
"""

import os
import sqlite3
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
from pathlib import Path
import json
from collections import defaultdict
import logging

# Optional imports for enhanced reporting
try:
    import pandas as pd
    HAS_PANDAS = True
except ImportError:
    HAS_PANDAS = False

try:
    from jinja2 import Template
    HAS_JINJA2 = True
except ImportError:
    HAS_JINJA2 = False


@dataclass
class TradeRecord:
    """Individual trade record."""
    timestamp: str
    symbol: str
    action: str  # BUY/SELL
    quantity: int
    price: float
    order_id: str
    strategy: str
    pnl: float = 0.0
    commission: float = 0.0
    notes: str = ""


@dataclass
class DailyReport:
    """Daily trading report data."""
    date: str
    total_trades: int = 0
    winning_trades: int = 0
    losing_trades: int = 0
    total_pnl: float = 0.0
    gross_profit: float = 0.0
    gross_loss: float = 0.0
    win_rate: float = 0.0
    profit_factor: float = 0.0
    average_win: float = 0.0
    average_loss: float = 0.0
    largest_win: float = 0.0
    largest_loss: float = 0.0
    total_commission: float = 0.0
    net_pnl: float = 0.0
    trades: List[TradeRecord] = field(default_factory=list)
    strategy_breakdown: Dict[str, Dict] = field(default_factory=dict)
    symbol_breakdown: Dict[str, Dict] = field(default_factory=dict)


@dataclass
class PeriodReport:
    """Weekly or monthly report data."""
    start_date: str
    end_date: str
    period_type: str  # 'weekly' or 'monthly'
    total_trading_days: int = 0
    total_trades: int = 0
    winning_days: int = 0
    losing_days: int = 0
    total_pnl: float = 0.0
    average_daily_pnl: float = 0.0
    best_day_pnl: float = 0.0
    worst_day_pnl: float = 0.0
    win_rate: float = 0.0
    profit_factor: float = 0.0
    sharpe_ratio: float = 0.0
    max_drawdown: float = 0.0
    daily_reports: List[DailyReport] = field(default_factory=list)
    strategy_performance: Dict[str, Dict] = field(default_factory=dict)


class ReportGenerator:
    """
    Generate comprehensive trading reports.

    Features:
    - Daily, weekly, and monthly reports
    - Multiple output formats (JSON, HTML, PDF)
    - Strategy-wise breakdown
    - Symbol-wise analysis
    - Performance metrics and risk analytics
    """

    def __init__(self, metrics_db_path: Optional[str] = None, output_dir: str = "reports"):
        """
        Initialize report generator.

        Args:
            metrics_db_path: Path to metrics database (if None, searches in metrics/)
            output_dir: Directory to save generated reports
        """
        self.metrics_db_path = metrics_db_path
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Create subdirectories for different report types
        (self.output_dir / "daily").mkdir(exist_ok=True)
        (self.output_dir / "weekly").mkdir(exist_ok=True)
        (self.output_dir / "monthly").mkdir(exist_ok=True)

        self.logger = logging.getLogger(__name__)

    def _find_metrics_databases(self) -> List[Path]:
        """Find all metrics database files."""
        metrics_dir = Path("metrics")
        if not metrics_dir.exists():
            return []

        return list(metrics_dir.glob("*_metrics.db"))

    def _get_database_connection(self, db_path: str) -> sqlite3.Connection:
        """Get database connection."""
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _fetch_trades_for_date(self, conn: sqlite3.Connection, date: str) -> List[TradeRecord]:
        """Fetch all trades for a specific date."""
        cursor = conn.cursor()
        cursor.execute("""
            SELECT timestamp, symbol, action, quantity, price, order_id,
                   strategy, pnl, commission, notes
            FROM trades
            WHERE DATE(timestamp) = ?
            ORDER BY timestamp
        """, (date,))

        trades = []
        for row in cursor.fetchall():
            trades.append(TradeRecord(
                timestamp=row['timestamp'],
                symbol=row['symbol'],
                action=row['action'],
                quantity=row['quantity'],
                price=row['price'],
                order_id=row['order_id'],
                strategy=row['strategy'],
                pnl=row['pnl'],
                commission=row['commission'] if row['commission'] else 0.0,
                notes=row['notes'] if row['notes'] else ""
            ))

        return trades

    def _fetch_trades_for_period(self, conn: sqlite3.Connection,
                                  start_date: str, end_date: str) -> List[TradeRecord]:
        """Fetch all trades for a date range."""
        cursor = conn.cursor()
        cursor.execute("""
            SELECT timestamp, symbol, action, quantity, price, order_id,
                   strategy, pnl, commission, notes
            FROM trades
            WHERE DATE(timestamp) BETWEEN ? AND ?
            ORDER BY timestamp
        """, (start_date, end_date))

        trades = []
        for row in cursor.fetchall():
            trades.append(TradeRecord(
                timestamp=row['timestamp'],
                symbol=row['symbol'],
                action=row['action'],
                quantity=row['quantity'],
                price=row['price'],
                order_id=row['order_id'],
                strategy=row['strategy'],
                pnl=row['pnl'],
                commission=row['commission'] if row['commission'] else 0.0,
                notes=row['notes'] if row['notes'] else ""
            ))

        return trades

    def _calculate_daily_metrics(self, trades: List[TradeRecord]) -> Dict:
        """Calculate metrics for a list of trades."""
        if not trades:
            return {
                'total_trades': 0,
                'winning_trades': 0,
                'losing_trades': 0,
                'total_pnl': 0.0,
                'gross_profit': 0.0,
                'gross_loss': 0.0,
                'win_rate': 0.0,
                'profit_factor': 0.0,
                'average_win': 0.0,
                'average_loss': 0.0,
                'largest_win': 0.0,
                'largest_loss': 0.0,
                'total_commission': 0.0,
                'net_pnl': 0.0
            }

        total_trades = len(trades)
        winning_trades = sum(1 for t in trades if t.pnl > 0)
        losing_trades = sum(1 for t in trades if t.pnl < 0)

        total_pnl = sum(t.pnl for t in trades)
        total_commission = sum(t.commission for t in trades)
        net_pnl = total_pnl - total_commission

        gross_profit = sum(t.pnl for t in trades if t.pnl > 0)
        gross_loss = abs(sum(t.pnl for t in trades if t.pnl < 0))

        win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0.0
        profit_factor = (gross_profit / gross_loss) if gross_loss > 0 else float('inf')

        wins = [t.pnl for t in trades if t.pnl > 0]
        losses = [t.pnl for t in trades if t.pnl < 0]

        average_win = (sum(wins) / len(wins)) if wins else 0.0
        average_loss = (sum(losses) / len(losses)) if losses else 0.0

        largest_win = max(wins) if wins else 0.0
        largest_loss = min(losses) if losses else 0.0

        return {
            'total_trades': total_trades,
            'winning_trades': winning_trades,
            'losing_trades': losing_trades,
            'total_pnl': total_pnl,
            'gross_profit': gross_profit,
            'gross_loss': gross_loss,
            'win_rate': win_rate,
            'profit_factor': profit_factor,
            'average_win': average_win,
            'average_loss': average_loss,
            'largest_win': largest_win,
            'largest_loss': largest_loss,
            'total_commission': total_commission,
            'net_pnl': net_pnl
        }

    def _calculate_strategy_breakdown(self, trades: List[TradeRecord]) -> Dict[str, Dict]:
        """Calculate performance breakdown by strategy."""
        strategy_trades = defaultdict(list)

        for trade in trades:
            strategy_trades[trade.strategy].append(trade)

        breakdown = {}
        for strategy, strat_trades in strategy_trades.items():
            breakdown[strategy] = self._calculate_daily_metrics(strat_trades)

        return breakdown

    def _calculate_symbol_breakdown(self, trades: List[TradeRecord]) -> Dict[str, Dict]:
        """Calculate performance breakdown by symbol."""
        symbol_trades = defaultdict(list)

        for trade in trades:
            symbol_trades[trade.symbol].append(trade)

        breakdown = {}
        for symbol, sym_trades in symbol_trades.items():
            breakdown[symbol] = self._calculate_daily_metrics(sym_trades)

        return breakdown

    def generate_daily_report(self, date: Optional[str] = None,
                             db_path: Optional[str] = None,
                             output_format: str = 'json') -> DailyReport:
        """
        Generate daily trading report.

        Args:
            date: Date in YYYY-MM-DD format (default: today)
            db_path: Database path (if None, uses first found)
            output_format: Output format ('json', 'html', 'text')

        Returns:
            DailyReport object
        """
        if date is None:
            date = datetime.now().strftime('%Y-%m-%d')

        # Find database
        if db_path is None:
            dbs = self._find_metrics_databases()
            if not dbs:
                self.logger.error("No metrics databases found")
                return DailyReport(date=date)
            db_path = str(dbs[0])

        conn = self._get_database_connection(db_path)
        trades = self._fetch_trades_for_date(conn, date)
        conn.close()

        # Calculate metrics
        metrics = self._calculate_daily_metrics(trades)
        strategy_breakdown = self._calculate_strategy_breakdown(trades)
        symbol_breakdown = self._calculate_symbol_breakdown(trades)

        # Create report
        report = DailyReport(
            date=date,
            total_trades=metrics['total_trades'],
            winning_trades=metrics['winning_trades'],
            losing_trades=metrics['losing_trades'],
            total_pnl=metrics['total_pnl'],
            gross_profit=metrics['gross_profit'],
            gross_loss=metrics['gross_loss'],
            win_rate=metrics['win_rate'],
            profit_factor=metrics['profit_factor'],
            average_win=metrics['average_win'],
            average_loss=metrics['average_loss'],
            largest_win=metrics['largest_win'],
            largest_loss=metrics['largest_loss'],
            total_commission=metrics['total_commission'],
            net_pnl=metrics['net_pnl'],
            trades=trades,
            strategy_breakdown=strategy_breakdown,
            symbol_breakdown=symbol_breakdown
        )

        # Save report
        self._save_daily_report(report, output_format)

        return report

    def generate_weekly_report(self, start_date: Optional[str] = None,
                              end_date: Optional[str] = None,
                              db_path: Optional[str] = None,
                              output_format: str = 'json') -> PeriodReport:
        """
        Generate weekly trading report.

        Args:
            start_date: Start date (default: Monday of current week)
            end_date: End date (default: today or Friday)
            db_path: Database path
            output_format: Output format

        Returns:
            PeriodReport object
        """
        # Default to current week
        if start_date is None:
            today = datetime.now()
            start_of_week = today - timedelta(days=today.weekday())
            start_date = start_of_week.strftime('%Y-%m-%d')

        if end_date is None:
            end_date = datetime.now().strftime('%Y-%m-%d')

        # Generate daily reports for the week
        daily_reports = []
        current = datetime.strptime(start_date, '%Y-%m-%d')
        end = datetime.strptime(end_date, '%Y-%m-%d')

        while current <= end:
            date_str = current.strftime('%Y-%m-%d')
            daily_report = self.generate_daily_report(date_str, db_path, output_format='none')
            if daily_report.total_trades > 0:
                daily_reports.append(daily_report)
            current += timedelta(days=1)

        # Aggregate weekly metrics
        report = self._aggregate_period_report(
            daily_reports, start_date, end_date, 'weekly'
        )

        # Save report
        self._save_period_report(report, 'weekly', output_format)

        return report

    def generate_monthly_report(self, year: Optional[int] = None,
                               month: Optional[int] = None,
                               db_path: Optional[str] = None,
                               output_format: str = 'json') -> PeriodReport:
        """
        Generate monthly trading report.

        Args:
            year: Year (default: current year)
            month: Month (default: current month)
            db_path: Database path
            output_format: Output format

        Returns:
            PeriodReport object
        """
        if year is None:
            year = datetime.now().year
        if month is None:
            month = datetime.now().month

        # Calculate start and end dates
        start_date = datetime(year, month, 1).strftime('%Y-%m-%d')

        # Last day of month
        if month == 12:
            end_date = datetime(year, month, 31).strftime('%Y-%m-%d')
        else:
            end_date = (datetime(year, month + 1, 1) - timedelta(days=1)).strftime('%Y-%m-%d')

        # Generate daily reports for the month
        daily_reports = []
        current = datetime.strptime(start_date, '%Y-%m-%d')
        end = datetime.strptime(end_date, '%Y-%m-%d')

        while current <= end:
            date_str = current.strftime('%Y-%m-%d')
            daily_report = self.generate_daily_report(date_str, db_path, output_format='none')
            if daily_report.total_trades > 0:
                daily_reports.append(daily_report)
            current += timedelta(days=1)

        # Aggregate monthly metrics
        report = self._aggregate_period_report(
            daily_reports, start_date, end_date, 'monthly'
        )

        # Save report
        self._save_period_report(report, 'monthly', output_format)

        return report

    def _aggregate_period_report(self, daily_reports: List[DailyReport],
                                 start_date: str, end_date: str,
                                 period_type: str) -> PeriodReport:
        """Aggregate daily reports into period report."""
        total_trading_days = len(daily_reports)

        if total_trading_days == 0:
            return PeriodReport(
                start_date=start_date,
                end_date=end_date,
                period_type=period_type
            )

        # Aggregate metrics
        total_trades = sum(r.total_trades for r in daily_reports)
        total_pnl = sum(r.total_pnl for r in daily_reports)

        winning_days = sum(1 for r in daily_reports if r.total_pnl > 0)
        losing_days = sum(1 for r in daily_reports if r.total_pnl < 0)

        average_daily_pnl = total_pnl / total_trading_days if total_trading_days > 0 else 0.0

        daily_pnls = [r.total_pnl for r in daily_reports]
        best_day_pnl = max(daily_pnls) if daily_pnls else 0.0
        worst_day_pnl = min(daily_pnls) if daily_pnls else 0.0

        # Calculate aggregate win rate and profit factor
        total_wins = sum(r.winning_trades for r in daily_reports)
        total_losses = sum(r.losing_trades for r in daily_reports)
        win_rate = (total_wins / total_trades * 100) if total_trades > 0 else 0.0

        gross_profit = sum(r.gross_profit for r in daily_reports)
        gross_loss = sum(r.gross_loss for r in daily_reports)
        profit_factor = (gross_profit / gross_loss) if gross_loss > 0 else float('inf')

        # Calculate Sharpe ratio (simplified)
        import statistics
        if len(daily_pnls) > 1:
            avg_return = statistics.mean(daily_pnls)
            std_return = statistics.stdev(daily_pnls)
            sharpe_ratio = (avg_return / std_return) if std_return > 0 else 0.0
        else:
            sharpe_ratio = 0.0

        # Calculate max drawdown
        max_drawdown = self._calculate_max_drawdown(daily_pnls)

        # Strategy performance breakdown
        strategy_performance = self._aggregate_strategy_performance(daily_reports)

        return PeriodReport(
            start_date=start_date,
            end_date=end_date,
            period_type=period_type,
            total_trading_days=total_trading_days,
            total_trades=total_trades,
            winning_days=winning_days,
            losing_days=losing_days,
            total_pnl=total_pnl,
            average_daily_pnl=average_daily_pnl,
            best_day_pnl=best_day_pnl,
            worst_day_pnl=worst_day_pnl,
            win_rate=win_rate,
            profit_factor=profit_factor,
            sharpe_ratio=sharpe_ratio,
            max_drawdown=max_drawdown,
            daily_reports=daily_reports,
            strategy_performance=strategy_performance
        )

    def _calculate_max_drawdown(self, daily_pnls: List[float]) -> float:
        """Calculate maximum drawdown from daily P&L."""
        if not daily_pnls:
            return 0.0

        cumulative = 0.0
        peak = 0.0
        max_dd = 0.0

        for pnl in daily_pnls:
            cumulative += pnl
            if cumulative > peak:
                peak = cumulative
            drawdown = peak - cumulative
            if drawdown > max_dd:
                max_dd = drawdown

        return max_dd

    def _aggregate_strategy_performance(self, daily_reports: List[DailyReport]) -> Dict[str, Dict]:
        """Aggregate strategy performance across days."""
        strategy_data = defaultdict(lambda: {
            'total_trades': 0,
            'winning_trades': 0,
            'losing_trades': 0,
            'total_pnl': 0.0,
            'gross_profit': 0.0,
            'gross_loss': 0.0
        })

        for daily_report in daily_reports:
            for strategy, metrics in daily_report.strategy_breakdown.items():
                strategy_data[strategy]['total_trades'] += metrics['total_trades']
                strategy_data[strategy]['winning_trades'] += metrics['winning_trades']
                strategy_data[strategy]['losing_trades'] += metrics['losing_trades']
                strategy_data[strategy]['total_pnl'] += metrics['total_pnl']
                strategy_data[strategy]['gross_profit'] += metrics['gross_profit']
                strategy_data[strategy]['gross_loss'] += metrics['gross_loss']

        # Calculate derived metrics
        for strategy, data in strategy_data.items():
            total = data['total_trades']
            data['win_rate'] = (data['winning_trades'] / total * 100) if total > 0 else 0.0
            data['profit_factor'] = (data['gross_profit'] / data['gross_loss']) if data['gross_loss'] > 0 else float('inf')

        return dict(strategy_data)

    def _save_daily_report(self, report: DailyReport, output_format: str):
        """Save daily report to file."""
        if output_format == 'none':
            return

        filename_base = f"daily_report_{report.date}"

        if output_format in ['json', 'all']:
            self._save_json_report(report, self.output_dir / "daily" / f"{filename_base}.json")

        if output_format in ['text', 'all']:
            self._save_text_daily_report(report, self.output_dir / "daily" / f"{filename_base}.txt")

        if output_format in ['html', 'all'] and HAS_JINJA2:
            self._save_html_daily_report(report, self.output_dir / "daily" / f"{filename_base}.html")

    def _save_period_report(self, report: PeriodReport, period_type: str, output_format: str):
        """Save period report to file."""
        if output_format == 'none':
            return

        filename_base = f"{period_type}_report_{report.start_date}_to_{report.end_date}"

        if output_format in ['json', 'all']:
            self._save_json_report(report, self.output_dir / period_type / f"{filename_base}.json")

        if output_format in ['text', 'all']:
            self._save_text_period_report(report, self.output_dir / period_type / f"{filename_base}.txt")

    def _save_json_report(self, report: Any, filepath: Path):
        """Save report as JSON."""
        def default_serializer(obj):
            if hasattr(obj, '__dict__'):
                return {k: v for k, v in obj.__dict__.items() if not k.startswith('_')}
            return str(obj)

        with open(filepath, 'w') as f:
            json.dump(report, f, default=default_serializer, indent=2)

        self.logger.info(f"Report saved to {filepath}")

    def _save_text_daily_report(self, report: DailyReport, filepath: Path):
        """Save daily report as formatted text."""
        with open(filepath, 'w') as f:
            f.write("=" * 80 + "\n")
            f.write(f"DAILY TRADING REPORT - {report.date}\n")
            f.write("=" * 80 + "\n\n")

            f.write("SUMMARY\n")
            f.write("-" * 80 + "\n")
            f.write(f"Total Trades:        {report.total_trades}\n")
            f.write(f"Winning Trades:      {report.winning_trades}\n")
            f.write(f"Losing Trades:       {report.losing_trades}\n")
            f.write(f"Win Rate:            {report.win_rate:.2f}%\n\n")

            f.write(f"Total P&L:           ₹{report.total_pnl:,.2f}\n")
            f.write(f"Gross Profit:        ₹{report.gross_profit:,.2f}\n")
            f.write(f"Gross Loss:          ₹{report.gross_loss:,.2f}\n")
            f.write(f"Profit Factor:       {report.profit_factor:.2f}\n\n")

            f.write(f"Average Win:         ₹{report.average_win:,.2f}\n")
            f.write(f"Average Loss:        ₹{report.average_loss:,.2f}\n")
            f.write(f"Largest Win:         ₹{report.largest_win:,.2f}\n")
            f.write(f"Largest Loss:        ₹{report.largest_loss:,.2f}\n\n")

            f.write(f"Total Commission:    ₹{report.total_commission:,.2f}\n")
            f.write(f"Net P&L:             ₹{report.net_pnl:,.2f}\n\n")

            # Strategy breakdown
            if report.strategy_breakdown:
                f.write("\nSTRATEGY BREAKDOWN\n")
                f.write("-" * 80 + "\n")
                for strategy, metrics in report.strategy_breakdown.items():
                    f.write(f"\n{strategy}:\n")
                    f.write(f"  Trades: {metrics['total_trades']}, ")
                    f.write(f"Win Rate: {metrics['win_rate']:.2f}%, ")
                    f.write(f"P&L: ₹{metrics['total_pnl']:,.2f}\n")

            # Trade list
            if report.trades:
                f.write("\n\nTRADE LIST\n")
                f.write("-" * 80 + "\n")
                f.write(f"{'Time':<12} {'Symbol':<30} {'Action':<6} {'Qty':<6} {'Price':<10} {'P&L':<12}\n")
                f.write("-" * 80 + "\n")
                for trade in report.trades:
                    time_str = trade.timestamp.split()[1] if ' ' in trade.timestamp else trade.timestamp
                    f.write(f"{time_str:<12} {trade.symbol:<30} {trade.action:<6} ")
                    f.write(f"{trade.quantity:<6} {trade.price:<10.2f} ₹{trade.pnl:<12.2f}\n")

        self.logger.info(f"Text report saved to {filepath}")

    def _save_text_period_report(self, report: PeriodReport, filepath: Path):
        """Save period report as formatted text."""
        with open(filepath, 'w') as f:
            f.write("=" * 80 + "\n")
            f.write(f"{report.period_type.upper()} TRADING REPORT\n")
            f.write(f"{report.start_date} to {report.end_date}\n")
            f.write("=" * 80 + "\n\n")

            f.write("SUMMARY\n")
            f.write("-" * 80 + "\n")
            f.write(f"Total Trading Days:  {report.total_trading_days}\n")
            f.write(f"Total Trades:        {report.total_trades}\n")
            f.write(f"Winning Days:        {report.winning_days}\n")
            f.write(f"Losing Days:         {report.losing_days}\n")
            f.write(f"Win Rate:            {report.win_rate:.2f}%\n\n")

            f.write(f"Total P&L:           ₹{report.total_pnl:,.2f}\n")
            f.write(f"Average Daily P&L:   ₹{report.average_daily_pnl:,.2f}\n")
            f.write(f"Best Day P&L:        ₹{report.best_day_pnl:,.2f}\n")
            f.write(f"Worst Day P&L:       ₹{report.worst_day_pnl:,.2f}\n\n")

            f.write(f"Profit Factor:       {report.profit_factor:.2f}\n")
            f.write(f"Sharpe Ratio:        {report.sharpe_ratio:.2f}\n")
            f.write(f"Max Drawdown:        ₹{report.max_drawdown:,.2f}\n\n")

            # Strategy performance
            if report.strategy_performance:
                f.write("\nSTRATEGY PERFORMANCE\n")
                f.write("-" * 80 + "\n")
                for strategy, metrics in report.strategy_performance.items():
                    f.write(f"\n{strategy}:\n")
                    f.write(f"  Total Trades: {metrics['total_trades']}\n")
                    f.write(f"  Win Rate:     {metrics['win_rate']:.2f}%\n")
                    f.write(f"  P&L:          ₹{metrics['total_pnl']:,.2f}\n")
                    f.write(f"  Profit Factor: {metrics['profit_factor']:.2f}\n")

            # Daily breakdown
            if report.daily_reports:
                f.write("\n\nDAILY BREAKDOWN\n")
                f.write("-" * 80 + "\n")
                f.write(f"{'Date':<12} {'Trades':<8} {'Win Rate':<12} {'P&L':<15}\n")
                f.write("-" * 80 + "\n")
                for daily in report.daily_reports:
                    f.write(f"{daily.date:<12} {daily.total_trades:<8} ")
                    f.write(f"{daily.win_rate:<12.2f} ₹{daily.total_pnl:<15,.2f}\n")

        self.logger.info(f"Text report saved to {filepath}")

    def _save_html_daily_report(self, report: DailyReport, filepath: Path):
        """Save daily report as HTML."""
        # HTML template will be added in next iteration
        pass


def main():
    """Example usage."""
    generator = ReportGenerator()

    # Generate daily report for today
    daily_report = generator.generate_daily_report(output_format='all')
    print(f"Daily report generated: {daily_report.total_trades} trades, P&L: ₹{daily_report.total_pnl:,.2f}")

    # Generate weekly report
    weekly_report = generator.generate_weekly_report(output_format='all')
    print(f"Weekly report generated: {weekly_report.total_trading_days} days, P&L: ₹{weekly_report.total_pnl:,.2f}")

    # Generate monthly report
    monthly_report = generator.generate_monthly_report(output_format='all')
    print(f"Monthly report generated: {monthly_report.total_trading_days} days, P&L: ₹{monthly_report.total_pnl:,.2f}")


if __name__ == "__main__":
    main()
