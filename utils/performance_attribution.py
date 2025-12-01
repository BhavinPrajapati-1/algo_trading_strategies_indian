"""
Performance Attribution System

Analyze trading performance by various dimensions:
- Index (NIFTY, BANK NIFTY, FINNIFTY, SENSEX)
- Strategy type (fixed SL, MTM-based, trailing, etc.)
- Time of day
- Market conditions
- Entry strike prices
- Premium levels

Author: Trading Analytics Team
"""

import sqlite3
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from pathlib import Path
import json
import logging
from collections import defaultdict
import re


@dataclass
class AttributionResult:
    """Performance attribution result."""
    dimension: str  # e.g., 'index', 'strategy_type', 'time_of_day'
    breakdown: Dict[str, Dict] = field(default_factory=dict)
    # Each category (e.g., 'NIFTY', 'BANK NIFTY') has metrics
    summary: Dict = field(default_factory=dict)
    insights: List[str] = field(default_factory=list)


class PerformanceAttributor:
    """
    Analyze performance attribution across various dimensions.

    Usage:
        attributor = PerformanceAttributor()
        index_attr = attributor.analyze_by_index(start_date, end_date)
        type_attr = attributor.analyze_by_strategy_type(start_date, end_date)
    """

    def __init__(self, metrics_dir: str = "metrics"):
        """
        Initialize performance attributor.

        Args:
            metrics_dir: Directory containing metrics databases
        """
        self.metrics_dir = Path(metrics_dir)
        self.logger = logging.getLogger(__name__)

    def _find_metrics_databases(self) -> List[Path]:
        """Find all metrics database files."""
        if not self.metrics_dir.exists():
            return []

        return list(self.metrics_dir.glob("*_metrics.db"))

    def _get_all_trades(self, start_date: Optional[str] = None,
                       end_date: Optional[str] = None) -> List[Dict]:
        """Get all trades from all strategy databases."""
        all_trades = []

        databases = self._find_metrics_databases()

        for db_path in databases:
            conn = sqlite3.connect(str(db_path))
            conn.row_factory = sqlite3.Row

            if start_date and end_date:
                query = """
                    SELECT * FROM trades
                    WHERE DATE(timestamp) BETWEEN ? AND ?
                    ORDER BY timestamp
                """
                cursor = conn.execute(query, (start_date, end_date))
            else:
                query = "SELECT * FROM trades ORDER BY timestamp"
                cursor = conn.execute(query)

            for row in cursor.fetchall():
                all_trades.append(dict(row))

            conn.close()

        return all_trades

    def _extract_index(self, symbol: str, strategy: str) -> str:
        """Extract underlying index from symbol or strategy name."""
        # Common index patterns
        if any(x in symbol.upper() for x in ['BANKNIFTY', 'BANK NIFTY', 'BANK_NIFTY']):
            return 'BANK NIFTY'
        elif 'NIFTY50' in symbol.upper() or 'NIFTY 50' in symbol.upper():
            return 'NIFTY 50'
        elif 'NIFTY' in symbol.upper() and 'BANK' not in symbol.upper():
            return 'NIFTY'
        elif 'FINNIFTY' in symbol.upper() or 'FIN NIFTY' in symbol.upper():
            return 'FINNIFTY'
        elif 'SENSEX' in symbol.upper():
            return 'SENSEX'
        elif 'MIDCPNIFTY' in symbol.upper():
            return 'MIDCPNIFTY'

        # Check strategy name as fallback
        if 'bank_nifty' in strategy.lower() or 'banknifty' in strategy.lower():
            return 'BANK NIFTY'
        elif 'nifty50' in strategy.lower() or 'nifty_50' in strategy.lower():
            return 'NIFTY 50'
        elif 'finnifty' in strategy.lower():
            return 'FINNIFTY'
        elif 'sensex' in strategy.lower():
            return 'SENSEX'

        return 'UNKNOWN'

    def _extract_strategy_type(self, strategy: str) -> str:
        """Extract strategy type from strategy name."""
        strategy_lower = strategy.lower()

        if 'fixed_stop_loss' in strategy_lower or 'fixed_sl' in strategy_lower:
            return 'Fixed Stop Loss'
        elif 'mtm' in strategy_lower and 'based' in strategy_lower:
            return 'MTM-Based Target'
        elif 'combined_premium' in strategy_lower:
            return 'Combined Premium'
        elif 'percentage' in strategy_lower and 'stop_loss' in strategy_lower:
            return 'Percentage-Based SL'
        elif 'trailing' in strategy_lower:
            return 'Trailing Stop Loss'
        elif '0920' in strategy_lower or '09:20' in strategy_lower:
            return '0920 Entry'
        else:
            return 'Other'

    def _extract_time_of_day(self, timestamp: str) -> str:
        """Categorize trade by time of day."""
        try:
            time_obj = datetime.fromisoformat(timestamp)
            hour = time_obj.hour

            if 9 <= hour < 11:
                return 'Morning (9-11 AM)'
            elif 11 <= hour < 13:
                return 'Mid-Day (11 AM-1 PM)'
            elif 13 <= hour < 15:
                return 'Afternoon (1-3 PM)'
            else:
                return 'After Hours (3 PM+)'

        except Exception:
            return 'Unknown'

    def _extract_option_type(self, symbol: str) -> str:
        """Extract whether option is CE (Call) or PE (Put)."""
        if 'CE' in symbol.upper():
            return 'CALL'
        elif 'PE' in symbol.upper():
            return 'PUT'
        else:
            return 'UNKNOWN'

    def _calculate_metrics(self, trades: List[Dict]) -> Dict:
        """Calculate performance metrics for a group of trades."""
        if not trades:
            return {
                'total_trades': 0,
                'total_pnl': 0.0,
                'win_rate': 0.0,
                'profit_factor': 0.0,
                'average_pnl': 0.0
            }

        total_trades = len(trades)
        pnls = [float(t['pnl']) for t in trades]

        total_pnl = sum(pnls)
        winning_trades = sum(1 for pnl in pnls if pnl > 0)
        losing_trades = sum(1 for pnl in pnls if pnl < 0)

        win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0.0

        gross_profit = sum(pnl for pnl in pnls if pnl > 0)
        gross_loss = abs(sum(pnl for pnl in pnls if pnl < 0))

        profit_factor = (gross_profit / gross_loss) if gross_loss > 0 else float('inf')
        average_pnl = total_pnl / total_trades if total_trades > 0 else 0.0

        return {
            'total_trades': total_trades,
            'winning_trades': winning_trades,
            'losing_trades': losing_trades,
            'total_pnl': total_pnl,
            'gross_profit': gross_profit,
            'gross_loss': gross_loss,
            'win_rate': win_rate,
            'profit_factor': profit_factor,
            'average_pnl': average_pnl
        }

    def analyze_by_index(self, start_date: Optional[str] = None,
                        end_date: Optional[str] = None) -> AttributionResult:
        """
        Analyze performance attribution by underlying index.

        Args:
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)

        Returns:
            AttributionResult with breakdown by index
        """
        trades = self._get_all_trades(start_date, end_date)

        if not trades:
            return AttributionResult(
                dimension='index',
                insights=['No trades found for the specified period']
            )

        # Group trades by index
        index_trades = defaultdict(list)

        for trade in trades:
            index = self._extract_index(trade['symbol'], trade['strategy'])
            index_trades[index].append(trade)

        # Calculate metrics for each index
        breakdown = {}
        for index, idx_trades in index_trades.items():
            breakdown[index] = self._calculate_metrics(idx_trades)

        # Generate insights
        insights = self._generate_index_insights(breakdown)

        # Overall summary
        summary = self._calculate_metrics(trades)

        return AttributionResult(
            dimension='index',
            breakdown=breakdown,
            summary=summary,
            insights=insights
        )

    def analyze_by_strategy_type(self, start_date: Optional[str] = None,
                                 end_date: Optional[str] = None) -> AttributionResult:
        """
        Analyze performance attribution by strategy type.

        Args:
            start_date: Start date
            end_date: End date

        Returns:
            AttributionResult with breakdown by strategy type
        """
        trades = self._get_all_trades(start_date, end_date)

        if not trades:
            return AttributionResult(
                dimension='strategy_type',
                insights=['No trades found for the specified period']
            )

        # Group trades by strategy type
        type_trades = defaultdict(list)

        for trade in trades:
            strategy_type = self._extract_strategy_type(trade['strategy'])
            type_trades[strategy_type].append(trade)

        # Calculate metrics for each type
        breakdown = {}
        for strategy_type, st_trades in type_trades.items():
            breakdown[strategy_type] = self._calculate_metrics(st_trades)

        # Generate insights
        insights = self._generate_strategy_type_insights(breakdown)

        # Overall summary
        summary = self._calculate_metrics(trades)

        return AttributionResult(
            dimension='strategy_type',
            breakdown=breakdown,
            summary=summary,
            insights=insights
        )

    def analyze_by_time_of_day(self, start_date: Optional[str] = None,
                               end_date: Optional[str] = None) -> AttributionResult:
        """
        Analyze performance attribution by time of day.

        Args:
            start_date: Start date
            end_date: End date

        Returns:
            AttributionResult with breakdown by time of day
        """
        trades = self._get_all_trades(start_date, end_date)

        if not trades:
            return AttributionResult(
                dimension='time_of_day',
                insights=['No trades found for the specified period']
            )

        # Group trades by time of day
        time_trades = defaultdict(list)

        for trade in trades:
            time_category = self._extract_time_of_day(trade['timestamp'])
            time_trades[time_category].append(trade)

        # Calculate metrics for each time period
        breakdown = {}
        for time_cat, time_tr in time_trades.items():
            breakdown[time_cat] = self._calculate_metrics(time_tr)

        # Generate insights
        insights = self._generate_time_insights(breakdown)

        # Overall summary
        summary = self._calculate_metrics(trades)

        return AttributionResult(
            dimension='time_of_day',
            breakdown=breakdown,
            summary=summary,
            insights=insights
        )

    def analyze_by_option_type(self, start_date: Optional[str] = None,
                               end_date: Optional[str] = None) -> AttributionResult:
        """
        Analyze performance attribution by option type (CALL vs PUT).

        Args:
            start_date: Start date
            end_date: End date

        Returns:
            AttributionResult with breakdown by option type
        """
        trades = self._get_all_trades(start_date, end_date)

        if not trades:
            return AttributionResult(
                dimension='option_type',
                insights=['No trades found for the specified period']
            )

        # Group trades by option type
        option_trades = defaultdict(list)

        for trade in trades:
            option_type = self._extract_option_type(trade['symbol'])
            option_trades[option_type].append(trade)

        # Calculate metrics for each option type
        breakdown = {}
        for opt_type, opt_trades in option_trades.items():
            breakdown[opt_type] = self._calculate_metrics(opt_trades)

        # Generate insights
        insights = self._generate_option_insights(breakdown)

        # Overall summary
        summary = self._calculate_metrics(trades)

        return AttributionResult(
            dimension='option_type',
            breakdown=breakdown,
            summary=summary,
            insights=insights
        )

    def _generate_index_insights(self, breakdown: Dict[str, Dict]) -> List[str]:
        """Generate insights from index attribution."""
        insights = []

        if not breakdown:
            return insights

        # Find best and worst performing indices
        sorted_by_pnl = sorted(breakdown.items(), key=lambda x: x[1]['total_pnl'], reverse=True)

        if sorted_by_pnl:
            best_index, best_metrics = sorted_by_pnl[0]
            insights.append(
                f"✅ {best_index} is the best performing index with total P&L of "
                f"₹{best_metrics['total_pnl']:,.2f} from {best_metrics['total_trades']} trades."
            )

            if len(sorted_by_pnl) > 1:
                worst_index, worst_metrics = sorted_by_pnl[-1]
                if worst_metrics['total_pnl'] < 0:
                    insights.append(
                        f"⚠️ {worst_index} is underperforming with negative P&L of "
                        f"₹{worst_metrics['total_pnl']:,.2f}. Consider reviewing strategies for this index."
                    )

        # Find index with highest win rate
        sorted_by_wr = sorted(breakdown.items(), key=lambda x: x[1]['win_rate'], reverse=True)
        if sorted_by_wr:
            best_wr_index, best_wr_metrics = sorted_by_wr[0]
            insights.append(
                f"📊 {best_wr_index} has the highest win rate at {best_wr_metrics['win_rate']:.2f}%."
            )

        return insights

    def _generate_strategy_type_insights(self, breakdown: Dict[str, Dict]) -> List[str]:
        """Generate insights from strategy type attribution."""
        insights = []

        if not breakdown:
            return insights

        # Find most profitable strategy type
        sorted_by_pnl = sorted(breakdown.items(), key=lambda x: x[1]['total_pnl'], reverse=True)

        if sorted_by_pnl:
            best_type, best_metrics = sorted_by_pnl[0]
            insights.append(
                f"✅ '{best_type}' strategies are most profitable with "
                f"₹{best_metrics['total_pnl']:,.2f} total P&L."
            )

        # Find most consistent (highest win rate)
        sorted_by_wr = sorted(breakdown.items(), key=lambda x: x[1]['win_rate'], reverse=True)
        if sorted_by_wr:
            best_wr_type, best_wr_metrics = sorted_by_wr[0]
            insights.append(
                f"📊 '{best_wr_type}' strategies have the highest win rate at "
                f"{best_wr_metrics['win_rate']:.2f}%."
            )

        # Identify underperformers
        for strategy_type, metrics in sorted_by_pnl:
            if metrics['total_pnl'] < -5000:  # Threshold for significant loss
                insights.append(
                    f"⚠️ '{strategy_type}' strategies are underperforming. "
                    f"Loss: ₹{metrics['total_pnl']:,.2f}. Review or disable these strategies."
                )

        return insights

    def _generate_time_insights(self, breakdown: Dict[str, Dict]) -> List[str]:
        """Generate insights from time of day attribution."""
        insights = []

        if not breakdown:
            return insights

        # Find most profitable time period
        sorted_by_pnl = sorted(breakdown.items(), key=lambda x: x[1]['total_pnl'], reverse=True)

        if sorted_by_pnl:
            best_time, best_metrics = sorted_by_pnl[0]
            insights.append(
                f"✅ {best_time} is the most profitable trading period with "
                f"₹{best_metrics['total_pnl']:,.2f} total P&L."
            )

        # Find time with highest win rate
        sorted_by_wr = sorted(breakdown.items(), key=lambda x: x[1]['win_rate'], reverse=True)
        if sorted_by_wr:
            best_wr_time, best_wr_metrics = sorted_by_wr[0]
            if best_wr_time != sorted_by_pnl[0][0]:  # Different from most profitable
                insights.append(
                    f"📊 {best_wr_time} has the highest win rate at {best_wr_metrics['win_rate']:.2f}%, "
                    f"indicating consistent performance during this period."
                )

        # Identify risky time periods
        for time_period, metrics in sorted_by_pnl:
            if metrics['win_rate'] < 40:  # Low win rate threshold
                insights.append(
                    f"⚠️ {time_period} has a low win rate of {metrics['win_rate']:.2f}%. "
                    f"Consider avoiding trading during this period or adjusting strategy parameters."
                )

        return insights

    def _generate_option_insights(self, breakdown: Dict[str, Dict]) -> List[str]:
        """Generate insights from option type attribution."""
        insights = []

        if not breakdown:
            return insights

        # Compare CALL vs PUT performance
        if 'CALL' in breakdown and 'PUT' in breakdown:
            call_pnl = breakdown['CALL']['total_pnl']
            put_pnl = breakdown['PUT']['total_pnl']

            if call_pnl > put_pnl * 1.2:  # Significantly better
                insights.append(
                    f"✅ CALL options outperforming PUTs significantly. "
                    f"CALL P&L: ₹{call_pnl:,.2f} vs PUT P&L: ₹{put_pnl:,.2f}"
                )
            elif put_pnl > call_pnl * 1.2:
                insights.append(
                    f"✅ PUT options outperforming CALLs significantly. "
                    f"PUT P&L: ₹{put_pnl:,.2f} vs CALL P&L: ₹{call_pnl:,.2f}"
                )
            else:
                insights.append(
                    f"📊 CALL and PUT options performing similarly. "
                    f"CALL: ₹{call_pnl:,.2f}, PUT: ₹{put_pnl:,.2f}"
                )

        return insights

    def generate_comprehensive_attribution(self, start_date: Optional[str] = None,
                                          end_date: Optional[str] = None) -> Dict[str, AttributionResult]:
        """
        Generate comprehensive attribution across all dimensions.

        Args:
            start_date: Start date
            end_date: End date

        Returns:
            Dictionary of AttributionResults for each dimension
        """
        results = {
            'index': self.analyze_by_index(start_date, end_date),
            'strategy_type': self.analyze_by_strategy_type(start_date, end_date),
            'time_of_day': self.analyze_by_time_of_day(start_date, end_date),
            'option_type': self.analyze_by_option_type(start_date, end_date)
        }

        return results

    def save_attribution_report(self, results: Dict[str, AttributionResult],
                               output_file: str = "reports/analysis/attribution_report.json"):
        """Save attribution results to file."""
        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        def default_serializer(obj):
            if hasattr(obj, '__dict__'):
                return {k: v for k, v in obj.__dict__.items() if not k.startswith('_')}
            return str(obj)

        with open(output_path, 'w') as f:
            json.dump(results, f, default=default_serializer, indent=2)

        self.logger.info(f"Attribution report saved to {output_path}")

        # Also save text version
        text_path = output_path.with_suffix('.txt')
        self._save_text_attribution(results, text_path)

    def _save_text_attribution(self, results: Dict[str, AttributionResult],
                              filepath: Path):
        """Save attribution as formatted text."""
        with open(filepath, 'w') as f:
            f.write("=" * 100 + "\n")
            f.write("PERFORMANCE ATTRIBUTION REPORT\n")
            f.write("=" * 100 + "\n\n")

            for dimension, result in results.items():
                f.write(f"\n{dimension.upper().replace('_', ' ')} ATTRIBUTION\n")
                f.write("-" * 100 + "\n\n")

                # Breakdown
                for category, metrics in result.breakdown.items():
                    f.write(f"{category}:\n")
                    f.write(f"  Trades: {metrics['total_trades']}\n")
                    f.write(f"  Win Rate: {metrics['win_rate']:.2f}%\n")
                    f.write(f"  Total P&L: ₹{metrics['total_pnl']:,.2f}\n")
                    f.write(f"  Profit Factor: {metrics['profit_factor']:.2f}\n")
                    f.write("\n")

                # Insights
                if result.insights:
                    f.write("INSIGHTS:\n")
                    for insight in result.insights:
                        f.write(f"  • {insight}\n")
                    f.write("\n")

        self.logger.info(f"Text attribution report saved to {filepath}")


def main():
    """Example usage."""
    attributor = PerformanceAttributor()

    # Generate comprehensive attribution
    results = attributor.generate_comprehensive_attribution()

    # Print insights
    print("\n" + "=" * 80)
    print("PERFORMANCE ATTRIBUTION ANALYSIS")
    print("=" * 80 + "\n")

    for dimension, result in results.items():
        print(f"\n{dimension.upper().replace('_', ' ')}:")
        print("-" * 80)

        for category, metrics in result.breakdown.items():
            print(f"\n{category}:")
            print(f"  Total P&L: ₹{metrics['total_pnl']:,.2f}")
            print(f"  Win Rate: {metrics['win_rate']:.2f}%")
            print(f"  Trades: {metrics['total_trades']}")

        if result.insights:
            print("\nInsights:")
            for insight in result.insights:
                print(f"  • {insight}")

    # Save report
    attributor.save_attribution_report(results)
    print(f"\nReports saved to reports/analysis/")


if __name__ == "__main__":
    main()
