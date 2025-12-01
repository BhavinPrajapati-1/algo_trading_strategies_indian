"""
Trading Analytics Demo

Demonstrates all the new analytics features:
- Report generation
- Strategy comparison
- Performance attribution
- Backtesting (example)

Author: Trading Analytics Team
"""

import sys
import os
from datetime import datetime, timedelta

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.report_generator import ReportGenerator
from utils.strategy_analyzer import StrategyAnalyzer
from utils.performance_attribution import PerformanceAttributor


def print_section(title):
    """Print a formatted section header."""
    print("\n" + "=" * 100)
    print(f"  {title}")
    print("=" * 100 + "\n")


def demo_report_generation():
    """Demonstrate report generation capabilities."""
    print_section("📊 REPORT GENERATION DEMO")

    generator = ReportGenerator()

    # Daily report
    print("Generating daily report...")
    try:
        daily_report = generator.generate_daily_report(output_format='all')

        if daily_report.total_trades > 0:
            print(f"✅ Daily Report for {daily_report.date}")
            print(f"   Total Trades:      {daily_report.total_trades}")
            print(f"   Win Rate:          {daily_report.win_rate:.2f}%")
            print(f"   Total P&L:         ₹{daily_report.total_pnl:,.2f}")
            print(f"   Net P&L:           ₹{daily_report.net_pnl:,.2f}")
            print(f"   Profit Factor:     {daily_report.profit_factor:.2f}")
            print(f"   Largest Win:       ₹{daily_report.largest_win:,.2f}")
            print(f"   Largest Loss:      ₹{daily_report.largest_loss:,.2f}")

            if daily_report.strategy_breakdown:
                print("\n   Strategy Breakdown:")
                for strategy, metrics in daily_report.strategy_breakdown.items():
                    print(f"     • {strategy}: ₹{metrics['total_pnl']:,.2f} "
                          f"({metrics['win_rate']:.1f}% WR)")
        else:
            print("⚠️  No trades found for today")

    except Exception as e:
        print(f"❌ Error generating daily report: {e}")

    # Weekly report
    print("\nGenerating weekly report...")
    try:
        weekly_report = generator.generate_weekly_report(output_format='all')

        if weekly_report.total_trading_days > 0:
            print(f"✅ Weekly Report ({weekly_report.start_date} to {weekly_report.end_date})")
            print(f"   Trading Days:      {weekly_report.total_trading_days}")
            print(f"   Total Trades:      {weekly_report.total_trades}")
            print(f"   Total P&L:         ₹{weekly_report.total_pnl:,.2f}")
            print(f"   Avg Daily P&L:     ₹{weekly_report.average_daily_pnl:,.2f}")
            print(f"   Best Day:          ₹{weekly_report.best_day_pnl:,.2f}")
            print(f"   Worst Day:         ₹{weekly_report.worst_day_pnl:,.2f}")
            print(f"   Sharpe Ratio:      {weekly_report.sharpe_ratio:.2f}")
            print(f"   Max Drawdown:      ₹{weekly_report.max_drawdown:,.2f}")
        else:
            print("⚠️  No trades found for this week")

    except Exception as e:
        print(f"❌ Error generating weekly report: {e}")

    # Monthly report
    print("\nGenerating monthly report...")
    try:
        monthly_report = generator.generate_monthly_report(output_format='all')

        if monthly_report.total_trading_days > 0:
            print(f"✅ Monthly Report ({monthly_report.start_date} to {monthly_report.end_date})")
            print(f"   Trading Days:      {monthly_report.total_trading_days}")
            print(f"   Total Trades:      {monthly_report.total_trades}")
            print(f"   Total P&L:         ₹{monthly_report.total_pnl:,.2f}")
            print(f"   Win Rate:          {monthly_report.win_rate:.2f}%")
            print(f"   Profit Factor:     {monthly_report.profit_factor:.2f}")
            print(f"   Sharpe Ratio:      {monthly_report.sharpe_ratio:.2f}")

            if monthly_report.strategy_performance:
                print("\n   Top Strategies:")
                sorted_strategies = sorted(
                    monthly_report.strategy_performance.items(),
                    key=lambda x: x[1]['total_pnl'],
                    reverse=True
                )[:3]

                for strategy, metrics in sorted_strategies:
                    print(f"     • {strategy}: ₹{metrics['total_pnl']:,.2f} "
                          f"({metrics['win_rate']:.1f}% WR)")
        else:
            print("⚠️  No trades found for this month")

    except Exception as e:
        print(f"❌ Error generating monthly report: {e}")


def demo_strategy_comparison():
    """Demonstrate strategy comparison."""
    print_section("🏆 STRATEGY COMPARISON DEMO")

    analyzer = StrategyAnalyzer()

    print("Comparing all strategies...")
    try:
        comparison = analyzer.compare_strategies()

        if comparison.strategies:
            print(f"✅ Analyzed {len(comparison.strategies)} strategies\n")

            print(f"🏆 Overall Best Strategy: {comparison.overall_best_strategy}\n")

            print("Best Strategy by Metric:")
            for metric, strategy in comparison.best_strategy_by_metric.items():
                print(f"   • {metric.replace('_', ' ').title()}: {strategy}")

            print("\nTop 5 by Total P&L:")
            for i, strategy in enumerate(comparison.rankings.get('total_pnl', [])[:5], 1):
                print(f"   {i}. {strategy}")

            print("\nTop 5 by Win Rate:")
            for i, strategy in enumerate(comparison.rankings.get('win_rate', [])[:5], 1):
                print(f"   {i}. {strategy}")

            if comparison.recommendations:
                print("\n💡 Recommendations:")
                for rec in comparison.recommendations:
                    print(f"   {rec}")

            # Save report
            analyzer.save_comparison_report(comparison, output_format='all')
            print("\n✅ Comparison reports saved to reports/analysis/")

        else:
            print("⚠️  No strategies found for comparison")

    except Exception as e:
        print(f"❌ Error comparing strategies: {e}")


def demo_performance_attribution():
    """Demonstrate performance attribution."""
    print_section("🎯 PERFORMANCE ATTRIBUTION DEMO")

    attributor = PerformanceAttributor()

    # Index attribution
    print("Analyzing performance by index...")
    try:
        index_attr = attributor.analyze_by_index()

        if index_attr.breakdown:
            print("✅ Performance by Index:")
            for index, metrics in index_attr.breakdown.items():
                print(f"\n   {index}:")
                print(f"     Total Trades:    {metrics['total_trades']}")
                print(f"     Win Rate:        {metrics['win_rate']:.2f}%")
                print(f"     Total P&L:       ₹{metrics['total_pnl']:,.2f}")
                print(f"     Profit Factor:   {metrics['profit_factor']:.2f}")

            if index_attr.insights:
                print("\n   Insights:")
                for insight in index_attr.insights:
                    print(f"     • {insight}")
        else:
            print("⚠️  No index data available")

    except Exception as e:
        print(f"❌ Error in index attribution: {e}")

    # Strategy type attribution
    print("\n\nAnalyzing performance by strategy type...")
    try:
        type_attr = attributor.analyze_by_strategy_type()

        if type_attr.breakdown:
            print("✅ Performance by Strategy Type:")
            for stype, metrics in type_attr.breakdown.items():
                print(f"\n   {stype}:")
                print(f"     Total Trades:    {metrics['total_trades']}")
                print(f"     Win Rate:        {metrics['win_rate']:.2f}%")
                print(f"     Total P&L:       ₹{metrics['total_pnl']:,.2f}")

            if type_attr.insights:
                print("\n   Insights:")
                for insight in type_attr.insights:
                    print(f"     • {insight}")
        else:
            print("⚠️  No strategy type data available")

    except Exception as e:
        print(f"❌ Error in strategy type attribution: {e}")

    # Time of day attribution
    print("\n\nAnalyzing performance by time of day...")
    try:
        time_attr = attributor.analyze_by_time_of_day()

        if time_attr.breakdown:
            print("✅ Performance by Time of Day:")
            for time_period, metrics in time_attr.breakdown.items():
                print(f"   {time_period}: ₹{metrics['total_pnl']:,.2f} "
                      f"({metrics['total_trades']} trades, {metrics['win_rate']:.1f}% WR)")

            if time_attr.insights:
                print("\n   Insights:")
                for insight in time_attr.insights:
                    print(f"     • {insight}")
        else:
            print("⚠️  No time of day data available")

    except Exception as e:
        print(f"❌ Error in time attribution: {e}")

    # Save comprehensive attribution
    print("\n\nGenerating comprehensive attribution report...")
    try:
        all_attr = attributor.generate_comprehensive_attribution()
        attributor.save_attribution_report(all_attr)
        print("✅ Attribution reports saved to reports/analysis/")
    except Exception as e:
        print(f"❌ Error saving attribution: {e}")


def main():
    """Run all demos."""
    print("\n" + "=" * 100)
    print("  TRADING ANALYTICS & BACKTESTING - COMPREHENSIVE DEMO")
    print("=" * 100)
    print("\n  This demo showcases all the new analytics features.")
    print("  Reports will be saved to the reports/ directory.\n")

    # Run demos
    demo_report_generation()
    demo_strategy_comparison()
    demo_performance_attribution()

    # Summary
    print_section("✅ DEMO COMPLETE")
    print("All reports have been generated and saved to:")
    print("  • reports/daily/       - Daily reports")
    print("  • reports/weekly/      - Weekly reports")
    print("  • reports/monthly/     - Monthly reports")
    print("  • reports/analysis/    - Strategy comparison & attribution\n")

    print("To view the web dashboard, run:")
    print("  python utils/dashboard.py")
    print("\nThen open: http://localhost:5000\n")

    print("For backtesting examples, see:")
    print("  TRADING_ANALYTICS.md - Section 3: Backtesting Framework\n")


if __name__ == "__main__":
    main()
