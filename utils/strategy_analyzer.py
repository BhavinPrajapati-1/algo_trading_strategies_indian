"""
Strategy Effectiveness Analyzer

Compare and analyze performance across different trading strategies.
Provides comprehensive metrics for strategy comparison and effectiveness evaluation.

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
import statistics


@dataclass
class StrategyMetrics:
    """Comprehensive metrics for a single strategy."""
    strategy_name: str
    total_trades: int = 0
    winning_trades: int = 0
    losing_trades: int = 0

    # P&L Metrics
    total_pnl: float = 0.0
    gross_profit: float = 0.0
    gross_loss: float = 0.0
    net_pnl: float = 0.0

    # Performance Ratios
    win_rate: float = 0.0
    profit_factor: float = 0.0
    average_win: float = 0.0
    average_loss: float = 0.0
    reward_risk_ratio: float = 0.0

    # Trade Statistics
    largest_win: float = 0.0
    largest_loss: float = 0.0
    consecutive_wins: int = 0
    consecutive_losses: int = 0
    max_consecutive_wins: int = 0
    max_consecutive_losses: int = 0

    # Risk Metrics
    max_drawdown: float = 0.0
    sharpe_ratio: float = 0.0
    sortino_ratio: float = 0.0
    calmar_ratio: float = 0.0

    # Trading Activity
    trading_days: int = 0
    average_trades_per_day: float = 0.0
    total_commission: float = 0.0

    # Time Analysis
    first_trade_date: Optional[str] = None
    last_trade_date: Optional[str] = None

    # Additional Data
    daily_pnls: List[float] = field(default_factory=list)
    monthly_pnls: Dict[str, float] = field(default_factory=dict)


@dataclass
class StrategyComparison:
    """Comparison result between strategies."""
    strategies: List[str]
    comparison_period: str
    metrics_comparison: Dict[str, List[float]]
    rankings: Dict[str, List[str]]  # metric_name -> [strategy names in rank order]
    best_strategy_by_metric: Dict[str, str]
    overall_best_strategy: str
    recommendations: List[str] = field(default_factory=list)


class StrategyAnalyzer:
    """
    Analyze and compare trading strategy performance.

    Features:
    - Individual strategy analysis
    - Multi-strategy comparison
    - Risk-adjusted performance metrics
    - Strategy effectiveness scoring
    - Performance attribution by index/type
    """

    def __init__(self, metrics_dir: str = "metrics", output_dir: str = "reports/analysis"):
        """
        Initialize strategy analyzer.

        Args:
            metrics_dir: Directory containing metrics databases
            output_dir: Directory to save analysis reports
        """
        self.metrics_dir = Path(metrics_dir)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        self.logger = logging.getLogger(__name__)

    def _get_database_connection(self, db_path: str) -> sqlite3.Connection:
        """Get database connection."""
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _find_strategy_databases(self) -> Dict[str, Path]:
        """Find all strategy metrics databases."""
        if not self.metrics_dir.exists():
            return {}

        databases = {}
        for db_file in self.metrics_dir.glob("*_metrics.db"):
            strategy_name = db_file.stem.replace("_metrics", "")
            databases[strategy_name] = db_file

        return databases

    def analyze_strategy(self, strategy_name: str,
                        start_date: Optional[str] = None,
                        end_date: Optional[str] = None) -> StrategyMetrics:
        """
        Analyze performance of a single strategy.

        Args:
            strategy_name: Name of the strategy
            start_date: Start date for analysis (YYYY-MM-DD)
            end_date: End date for analysis (YYYY-MM-DD)

        Returns:
            StrategyMetrics object
        """
        # Find database
        databases = self._find_strategy_databases()
        db_path = databases.get(strategy_name)

        if not db_path:
            self.logger.error(f"Database for strategy '{strategy_name}' not found")
            return StrategyMetrics(strategy_name=strategy_name)

        conn = self._get_database_connection(str(db_path))

        # Fetch trades
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

        trades = cursor.fetchall()
        conn.close()

        if not trades:
            return StrategyMetrics(strategy_name=strategy_name)

        # Calculate metrics
        return self._calculate_strategy_metrics(strategy_name, trades)

    def _calculate_strategy_metrics(self, strategy_name: str,
                                    trades: List[sqlite3.Row]) -> StrategyMetrics:
        """Calculate comprehensive metrics for a strategy."""
        if not trades:
            return StrategyMetrics(strategy_name=strategy_name)

        # Basic counts
        total_trades = len(trades)
        pnls = [float(t['pnl']) for t in trades]
        winning_trades = sum(1 for pnl in pnls if pnl > 0)
        losing_trades = sum(1 for pnl in pnls if pnl < 0)

        # P&L calculations
        total_pnl = sum(pnls)
        gross_profit = sum(pnl for pnl in pnls if pnl > 0)
        gross_loss = abs(sum(pnl for pnl in pnls if pnl < 0))
        total_commission = sum(float(t['commission'] or 0) for t in trades)
        net_pnl = total_pnl - total_commission

        # Win/Loss statistics
        wins = [pnl for pnl in pnls if pnl > 0]
        losses = [pnl for pnl in pnls if pnl < 0]

        win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0.0
        profit_factor = (gross_profit / gross_loss) if gross_loss > 0 else float('inf')

        average_win = (sum(wins) / len(wins)) if wins else 0.0
        average_loss = (sum(losses) / len(losses)) if losses else 0.0
        reward_risk_ratio = (abs(average_win / average_loss)) if average_loss != 0 else 0.0

        largest_win = max(wins) if wins else 0.0
        largest_loss = min(losses) if losses else 0.0

        # Consecutive wins/losses
        max_consec_wins, max_consec_losses = self._calculate_consecutive_stats(pnls)

        # Date analysis
        timestamps = [t['timestamp'] for t in trades]
        first_trade_date = timestamps[0].split()[0] if timestamps else None
        last_trade_date = timestamps[-1].split()[0] if timestamps else None

        # Daily P&Ls
        daily_pnls = self._calculate_daily_pnls(trades)
        trading_days = len(daily_pnls)
        average_trades_per_day = total_trades / trading_days if trading_days > 0 else 0.0

        # Risk metrics
        max_drawdown = self._calculate_max_drawdown(daily_pnls)
        sharpe_ratio = self._calculate_sharpe_ratio(daily_pnls)
        sortino_ratio = self._calculate_sortino_ratio(daily_pnls)
        calmar_ratio = (sum(daily_pnls) / max_drawdown) if max_drawdown > 0 else 0.0

        # Monthly P&Ls
        monthly_pnls = self._calculate_monthly_pnls(trades)

        return StrategyMetrics(
            strategy_name=strategy_name,
            total_trades=total_trades,
            winning_trades=winning_trades,
            losing_trades=losing_trades,
            total_pnl=total_pnl,
            gross_profit=gross_profit,
            gross_loss=gross_loss,
            net_pnl=net_pnl,
            win_rate=win_rate,
            profit_factor=profit_factor,
            average_win=average_win,
            average_loss=average_loss,
            reward_risk_ratio=reward_risk_ratio,
            largest_win=largest_win,
            largest_loss=largest_loss,
            max_consecutive_wins=max_consec_wins,
            max_consecutive_losses=max_consec_losses,
            max_drawdown=max_drawdown,
            sharpe_ratio=sharpe_ratio,
            sortino_ratio=sortino_ratio,
            calmar_ratio=calmar_ratio,
            trading_days=trading_days,
            average_trades_per_day=average_trades_per_day,
            total_commission=total_commission,
            first_trade_date=first_trade_date,
            last_trade_date=last_trade_date,
            daily_pnls=daily_pnls,
            monthly_pnls=monthly_pnls
        )

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
            else:
                current_wins = 0
                current_losses = 0

        return max_wins, max_losses

    def _calculate_daily_pnls(self, trades: List[sqlite3.Row]) -> List[float]:
        """Calculate P&L for each trading day."""
        daily_pnl = defaultdict(float)

        for trade in trades:
            date = trade['timestamp'].split()[0]
            daily_pnl[date] += float(trade['pnl'])

        return list(daily_pnl.values())

    def _calculate_monthly_pnls(self, trades: List[sqlite3.Row]) -> Dict[str, float]:
        """Calculate P&L for each month."""
        monthly_pnl = defaultdict(float)

        for trade in trades:
            month = trade['timestamp'][:7]  # YYYY-MM
            monthly_pnl[month] += float(trade['pnl'])

        return dict(monthly_pnl)

    def _calculate_max_drawdown(self, daily_pnls: List[float]) -> float:
        """Calculate maximum drawdown."""
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

    def _calculate_sharpe_ratio(self, daily_pnls: List[float],
                                risk_free_rate: float = 0.0) -> float:
        """
        Calculate Sharpe ratio.

        Args:
            daily_pnls: List of daily P&L values
            risk_free_rate: Annual risk-free rate (default 0%)

        Returns:
            Sharpe ratio
        """
        if len(daily_pnls) < 2:
            return 0.0

        avg_return = statistics.mean(daily_pnls)
        std_return = statistics.stdev(daily_pnls)

        if std_return == 0:
            return 0.0

        # Annualized Sharpe (assuming 252 trading days)
        sharpe = (avg_return - risk_free_rate / 252) / std_return * (252 ** 0.5)
        return sharpe

    def _calculate_sortino_ratio(self, daily_pnls: List[float],
                                 target_return: float = 0.0) -> float:
        """
        Calculate Sortino ratio (uses downside deviation instead of total volatility).

        Args:
            daily_pnls: List of daily P&L values
            target_return: Target return (default 0)

        Returns:
            Sortino ratio
        """
        if len(daily_pnls) < 2:
            return 0.0

        avg_return = statistics.mean(daily_pnls)

        # Downside deviation (only negative returns)
        downside_returns = [pnl for pnl in daily_pnls if pnl < target_return]

        if not downside_returns:
            return float('inf')

        downside_dev = statistics.stdev(downside_returns) if len(downside_returns) > 1 else 0.0

        if downside_dev == 0:
            return 0.0

        # Annualized Sortino
        sortino = (avg_return - target_return) / downside_dev * (252 ** 0.5)
        return sortino

    def compare_strategies(self, strategy_names: Optional[List[str]] = None,
                          start_date: Optional[str] = None,
                          end_date: Optional[str] = None) -> StrategyComparison:
        """
        Compare performance of multiple strategies.

        Args:
            strategy_names: List of strategy names (if None, compares all)
            start_date: Start date for comparison
            end_date: End date for comparison

        Returns:
            StrategyComparison object
        """
        # Find strategies
        if strategy_names is None:
            databases = self._find_strategy_databases()
            strategy_names = list(databases.keys())

        if not strategy_names:
            self.logger.error("No strategies found for comparison")
            return StrategyComparison(
                strategies=[],
                comparison_period="",
                metrics_comparison={},
                rankings={},
                best_strategy_by_metric={},
                overall_best_strategy=""
            )

        # Analyze each strategy
        strategy_metrics = {}
        for strategy in strategy_names:
            metrics = self.analyze_strategy(strategy, start_date, end_date)
            if metrics.total_trades > 0:
                strategy_metrics[strategy] = metrics

        if not strategy_metrics:
            self.logger.error("No trading data found for strategies")
            return StrategyComparison(
                strategies=strategy_names,
                comparison_period=f"{start_date or 'All'} to {end_date or 'All'}",
                metrics_comparison={},
                rankings={},
                best_strategy_by_metric={},
                overall_best_strategy=""
            )

        # Build comparison
        metrics_comparison = self._build_metrics_comparison(strategy_metrics)
        rankings = self._build_rankings(strategy_metrics)
        best_by_metric = self._find_best_by_metric(strategy_metrics)
        overall_best = self._find_overall_best_strategy(strategy_metrics)
        recommendations = self._generate_recommendations(strategy_metrics)

        return StrategyComparison(
            strategies=list(strategy_metrics.keys()),
            comparison_period=f"{start_date or 'All'} to {end_date or 'All'}",
            metrics_comparison=metrics_comparison,
            rankings=rankings,
            best_strategy_by_metric=best_by_metric,
            overall_best_strategy=overall_best,
            recommendations=recommendations
        )

    def _build_metrics_comparison(self, strategy_metrics: Dict[str, StrategyMetrics]) -> Dict[str, List]:
        """Build comparison dictionary of key metrics."""
        comparison = {
            'total_pnl': [],
            'win_rate': [],
            'profit_factor': [],
            'sharpe_ratio': [],
            'max_drawdown': [],
            'total_trades': [],
            'average_trades_per_day': []
        }

        for strategy, metrics in strategy_metrics.items():
            comparison['total_pnl'].append((strategy, metrics.total_pnl))
            comparison['win_rate'].append((strategy, metrics.win_rate))
            comparison['profit_factor'].append((strategy, metrics.profit_factor))
            comparison['sharpe_ratio'].append((strategy, metrics.sharpe_ratio))
            comparison['max_drawdown'].append((strategy, metrics.max_drawdown))
            comparison['total_trades'].append((strategy, metrics.total_trades))
            comparison['average_trades_per_day'].append((strategy, metrics.average_trades_per_day))

        return comparison

    def _build_rankings(self, strategy_metrics: Dict[str, StrategyMetrics]) -> Dict[str, List[str]]:
        """Build rankings for each metric."""
        rankings = {}

        # Total P&L (descending)
        rankings['total_pnl'] = sorted(
            strategy_metrics.keys(),
            key=lambda s: strategy_metrics[s].total_pnl,
            reverse=True
        )

        # Win Rate (descending)
        rankings['win_rate'] = sorted(
            strategy_metrics.keys(),
            key=lambda s: strategy_metrics[s].win_rate,
            reverse=True
        )

        # Profit Factor (descending)
        rankings['profit_factor'] = sorted(
            strategy_metrics.keys(),
            key=lambda s: strategy_metrics[s].profit_factor if strategy_metrics[s].profit_factor != float('inf') else 0,
            reverse=True
        )

        # Sharpe Ratio (descending)
        rankings['sharpe_ratio'] = sorted(
            strategy_metrics.keys(),
            key=lambda s: strategy_metrics[s].sharpe_ratio,
            reverse=True
        )

        # Max Drawdown (ascending - lower is better)
        rankings['max_drawdown'] = sorted(
            strategy_metrics.keys(),
            key=lambda s: strategy_metrics[s].max_drawdown
        )

        return rankings

    def _find_best_by_metric(self, strategy_metrics: Dict[str, StrategyMetrics]) -> Dict[str, str]:
        """Find best strategy for each metric."""
        best = {}

        # Best total P&L
        best['total_pnl'] = max(strategy_metrics.items(), key=lambda x: x[1].total_pnl)[0]

        # Best win rate
        best['win_rate'] = max(strategy_metrics.items(), key=lambda x: x[1].win_rate)[0]

        # Best profit factor
        best['profit_factor'] = max(
            strategy_metrics.items(),
            key=lambda x: x[1].profit_factor if x[1].profit_factor != float('inf') else 0
        )[0]

        # Best Sharpe ratio
        best['sharpe_ratio'] = max(strategy_metrics.items(), key=lambda x: x[1].sharpe_ratio)[0]

        # Best (lowest) drawdown
        best['max_drawdown'] = min(strategy_metrics.items(), key=lambda x: x[1].max_drawdown)[0]

        return best

    def _find_overall_best_strategy(self, strategy_metrics: Dict[str, StrategyMetrics]) -> str:
        """
        Determine overall best strategy using weighted scoring.

        Weights:
        - Total P&L: 30%
        - Sharpe Ratio: 25%
        - Profit Factor: 20%
        - Win Rate: 15%
        - Max Drawdown: 10%
        """
        if not strategy_metrics:
            return ""

        # Normalize metrics to 0-100 scale
        scores = {}

        for strategy in strategy_metrics.keys():
            score = 0.0

            # Total P&L (30%)
            pnl_values = [m.total_pnl for m in strategy_metrics.values()]
            max_pnl = max(pnl_values) if pnl_values else 1
            if max_pnl > 0:
                score += (strategy_metrics[strategy].total_pnl / max_pnl) * 30

            # Sharpe Ratio (25%)
            sharpe_values = [m.sharpe_ratio for m in strategy_metrics.values() if m.sharpe_ratio != float('inf')]
            max_sharpe = max(sharpe_values) if sharpe_values else 1
            if max_sharpe > 0:
                score += (strategy_metrics[strategy].sharpe_ratio / max_sharpe) * 25

            # Profit Factor (20%)
            pf_values = [m.profit_factor for m in strategy_metrics.values() if m.profit_factor != float('inf')]
            max_pf = max(pf_values) if pf_values else 1
            if max_pf > 0:
                pf = strategy_metrics[strategy].profit_factor
                if pf != float('inf'):
                    score += (pf / max_pf) * 20

            # Win Rate (15%)
            wr_values = [m.win_rate for m in strategy_metrics.values()]
            max_wr = max(wr_values) if wr_values else 1
            if max_wr > 0:
                score += (strategy_metrics[strategy].win_rate / max_wr) * 15

            # Max Drawdown (10%) - inverse (lower is better)
            dd_values = [m.max_drawdown for m in strategy_metrics.values() if m.max_drawdown > 0]
            if dd_values:
                max_dd = max(dd_values)
                strategy_dd = strategy_metrics[strategy].max_drawdown
                if strategy_dd > 0:
                    score += (1 - (strategy_dd / max_dd)) * 10

            scores[strategy] = score

        return max(scores.items(), key=lambda x: x[1])[0]

    def _generate_recommendations(self, strategy_metrics: Dict[str, StrategyMetrics]) -> List[str]:
        """Generate actionable recommendations based on analysis."""
        recommendations = []

        # Find best and worst performers
        if not strategy_metrics:
            return recommendations

        best_pnl = max(strategy_metrics.items(), key=lambda x: x[1].total_pnl)
        worst_pnl = min(strategy_metrics.items(), key=lambda x: x[1].total_pnl)

        best_sharpe = max(strategy_metrics.items(), key=lambda x: x[1].sharpe_ratio)

        # Recommendation 1: Focus on best performers
        recommendations.append(
            f"✅ '{best_pnl[0]}' has the highest total P&L (₹{best_pnl[1].total_pnl:,.2f}). "
            f"Consider allocating more capital to this strategy."
        )

        # Recommendation 2: Risk-adjusted performance
        if best_sharpe[1].sharpe_ratio > 1.0:
            recommendations.append(
                f"✅ '{best_sharpe[0]}' has excellent risk-adjusted returns "
                f"(Sharpe: {best_sharpe[1].sharpe_ratio:.2f}). This strategy provides "
                f"consistent performance relative to risk."
            )

        # Recommendation 3: Underperformers
        if worst_pnl[1].total_pnl < 0:
            recommendations.append(
                f"⚠️ '{worst_pnl[0]}' is underperforming with negative P&L "
                f"(₹{worst_pnl[1].total_pnl:,.2f}). Review or discontinue this strategy."
            )

        # Recommendation 4: Win rate analysis
        high_wr_strategies = [
            (name, metrics) for name, metrics in strategy_metrics.items()
            if metrics.win_rate > 60
        ]
        if high_wr_strategies:
            names = ', '.join([name for name, _ in high_wr_strategies])
            recommendations.append(
                f"✅ High win rate strategies: {names}. These provide consistent winning trades."
            )

        # Recommendation 5: Drawdown warning
        high_dd_strategies = [
            (name, metrics) for name, metrics in strategy_metrics.items()
            if metrics.max_drawdown > 10000  # ₹10,000 threshold
        ]
        if high_dd_strategies:
            for name, metrics in high_dd_strategies:
                recommendations.append(
                    f"⚠️ '{name}' has high drawdown (₹{metrics.max_drawdown:,.2f}). "
                    f"Consider reducing position sizes or implementing tighter stop losses."
                )

        return recommendations

    def save_comparison_report(self, comparison: StrategyComparison,
                              output_format: str = 'text'):
        """Save strategy comparison report."""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

        if output_format in ['text', 'all']:
            filepath = self.output_dir / f"strategy_comparison_{timestamp}.txt"
            self._save_text_comparison(comparison, filepath)

        if output_format in ['json', 'all']:
            filepath = self.output_dir / f"strategy_comparison_{timestamp}.json"
            self._save_json_comparison(comparison, filepath)

    def _save_text_comparison(self, comparison: StrategyComparison, filepath: Path):
        """Save comparison as text report."""
        with open(filepath, 'w') as f:
            f.write("=" * 100 + "\n")
            f.write("STRATEGY COMPARISON REPORT\n")
            f.write(f"Period: {comparison.comparison_period}\n")
            f.write(f"Strategies Analyzed: {len(comparison.strategies)}\n")
            f.write("=" * 100 + "\n\n")

            # Overall best
            f.write(f"🏆 OVERALL BEST STRATEGY: {comparison.overall_best_strategy}\n\n")

            # Rankings
            f.write("RANKINGS BY METRIC\n")
            f.write("-" * 100 + "\n")

            for metric, ranked_strategies in comparison.rankings.items():
                f.write(f"\n{metric.upper().replace('_', ' ')}:\n")
                for i, strategy in enumerate(ranked_strategies, 1):
                    f.write(f"  {i}. {strategy}\n")

            # Best by metric
            f.write("\n\nBEST STRATEGY BY METRIC\n")
            f.write("-" * 100 + "\n")
            for metric, strategy in comparison.best_strategy_by_metric.items():
                f.write(f"{metric.replace('_', ' ').title():<25} : {strategy}\n")

            # Recommendations
            if comparison.recommendations:
                f.write("\n\nRECOMMENDATIONS\n")
                f.write("-" * 100 + "\n")
                for i, rec in enumerate(comparison.recommendations, 1):
                    f.write(f"{i}. {rec}\n\n")

        self.logger.info(f"Comparison report saved to {filepath}")

    def _save_json_comparison(self, comparison: StrategyComparison, filepath: Path):
        """Save comparison as JSON."""
        def default_serializer(obj):
            if hasattr(obj, '__dict__'):
                return {k: v for k, v in obj.__dict__.items() if not k.startswith('_')}
            return str(obj)

        with open(filepath, 'w') as f:
            json.dump(comparison, f, default=default_serializer, indent=2)

        self.logger.info(f"Comparison JSON saved to {filepath}")


def main():
    """Example usage."""
    analyzer = StrategyAnalyzer()

    # Compare all strategies
    comparison = analyzer.compare_strategies()

    print(f"\n🏆 Overall Best Strategy: {comparison.overall_best_strategy}")
    print(f"\nStrategies Compared: {', '.join(comparison.strategies)}")

    print("\nRecommendations:")
    for i, rec in enumerate(comparison.recommendations, 1):
        print(f"{i}. {rec}")

    # Save report
    analyzer.save_comparison_report(comparison, output_format='all')


if __name__ == "__main__":
    main()
