# Trading Analytics & Backtesting Guide

Comprehensive guide to advanced analytics, reporting, backtesting, and performance attribution features.

---

## 📊 Overview

This repository now includes **advanced analytics capabilities** to help you:

- ✅ Generate **daily/weekly/monthly reports** with comprehensive P&L analysis
- ✅ **Compare strategies** and identify best performers
- ✅ **Backtest strategies** on historical data before deploying live
- ✅ **Visualize performance** through web-based dashboards
- ✅ **Analyze performance attribution** by index, strategy type, time of day, etc.

---

## 🆕 New Features

| Feature | Module | Purpose |
|---------|--------|---------|
| **Report Generator** | `utils/report_generator.py` | Daily/weekly/monthly P&L reports |
| **Strategy Analyzer** | `utils/strategy_analyzer.py` | Compare and rank strategies |
| **Backtester** | `utils/backtester.py` | Test strategies on historical data |
| **Dashboard** | `utils/dashboard.py` | Web-based analytics dashboard |
| **Performance Attribution** | `utils/performance_attribution.py` | Analyze by index, type, time |

---

## 📈 1. Report Generation

### Features

- **Daily Reports**: Complete trading summary for any date
- **Weekly Reports**: Aggregate performance across the week
- **Monthly Reports**: Month-end analysis with strategy breakdown
- **Multiple Formats**: JSON, Text, HTML

### Usage

```python
from utils.report_generator import ReportGenerator

# Initialize
generator = ReportGenerator()

# Generate daily report for today
daily_report = generator.generate_daily_report(
    date='2024-01-15',
    output_format='all'  # Saves JSON, text, and HTML
)

print(f"Total P&L: ₹{daily_report.total_pnl:,.2f}")
print(f"Win Rate: {daily_report.win_rate:.2f}%")
print(f"Profit Factor: {daily_report.profit_factor:.2f}")

# Generate weekly report
weekly_report = generator.generate_weekly_report(
    start_date='2024-01-15',
    end_date='2024-01-19',
    output_format='all'
)

print(f"Weekly P&L: ₹{weekly_report.total_pnl:,.2f}")
print(f"Trading Days: {weekly_report.total_trading_days}")
print(f"Average Daily P&L: ₹{weekly_report.average_daily_pnl:,.2f}")

# Generate monthly report
monthly_report = generator.generate_monthly_report(
    year=2024,
    month=1,
    output_format='all'
)

print(f"Monthly P&L: ₹{monthly_report.total_pnl:,.2f}")
print(f"Sharpe Ratio: {monthly_report.sharpe_ratio:.2f}")
print(f"Max Drawdown: ₹{monthly_report.max_drawdown:,.2f}")
```

### Report Contents

**Daily Report Includes:**
- Total trades, winning/losing breakdown
- Win rate and profit factor
- Gross profit, gross loss
- Average win/loss amounts
- Largest win/loss
- Total commission and net P&L
- Strategy-wise breakdown
- Symbol-wise breakdown
- Complete trade list

**Weekly/Monthly Reports Add:**
- Trading days count
- Winning/losing days
- Best/worst day P&L
- Average daily P&L
- Sharpe ratio
- Maximum drawdown
- Daily breakdown table
- Strategy performance comparison

### Output Files

Reports are saved to:
```
reports/
├── daily/
│   ├── daily_report_2024-01-15.json
│   ├── daily_report_2024-01-15.txt
│   └── daily_report_2024-01-15.html
├── weekly/
│   └── weekly_report_2024-01-15_to_2024-01-19.txt
└── monthly/
    └── monthly_report_2024-01-01_to_2024-01-31.txt
```

---

## 🏆 2. Strategy Comparison & Analysis

### Features

- Compare all strategies side-by-side
- Risk-adjusted performance metrics
- Strategy rankings by various metrics
- Actionable recommendations
- Weighted overall scoring

### Usage

```python
from utils.strategy_analyzer import StrategyAnalyzer

# Initialize
analyzer = StrategyAnalyzer()

# Analyze single strategy
strategy_metrics = analyzer.analyze_strategy(
    strategy_name='bank_nifty_combined_premium',
    start_date='2024-01-01',
    end_date='2024-01-31'
)

print(f"Total P&L: ₹{strategy_metrics.total_pnl:,.2f}")
print(f"Win Rate: {strategy_metrics.win_rate:.2f}%")
print(f"Sharpe Ratio: {strategy_metrics.sharpe_ratio:.2f}")
print(f"Max Drawdown: ₹{strategy_metrics.max_drawdown:,.2f}")

# Compare all strategies
comparison = analyzer.compare_strategies()

print(f"\n🏆 Overall Best Strategy: {comparison.overall_best_strategy}")

print("\nRankings by Total P&L:")
for i, strategy in enumerate(comparison.rankings['total_pnl'], 1):
    print(f"  {i}. {strategy}")

print("\nRecommendations:")
for rec in comparison.recommendations:
    print(f"  • {rec}")

# Save comparison report
analyzer.save_comparison_report(comparison, output_format='all')
```

### Metrics Calculated

**Performance Metrics:**
- Total P&L, Gross Profit/Loss
- Win rate, Profit factor
- Average win/loss
- Reward-risk ratio
- Largest win/loss

**Risk Metrics:**
- Maximum drawdown (absolute & %)
- Sharpe ratio (risk-adjusted returns)
- Sortino ratio (downside risk)
- Calmar ratio (return/drawdown)

**Trading Statistics:**
- Total trades, trading days
- Consecutive wins/losses (max)
- Average trades per day
- Total commission paid

### Rankings

Strategies are ranked by:
- Total P&L
- Win rate
- Profit factor
- Sharpe ratio
- Maximum drawdown (lower is better)

### Overall Best Strategy

Determined using **weighted scoring**:
- Total P&L: 30%
- Sharpe Ratio: 25%
- Profit Factor: 20%
- Win Rate: 15%
- Max Drawdown: 10%

---

## 🔬 3. Backtesting Framework

### Features

- Historical data replay through strategies
- Walk-forward testing capability
- Commission and slippage modeling
- Stop loss / take profit simulation
- Multiple position sizing methods
- Comprehensive performance metrics

### Usage

```python
from utils.backtester import (
    Backtester, BacktestConfig,
    HistoricalDataProvider, example_strategy
)
from datetime import datetime

# Configure backtest
config = BacktestConfig(
    initial_capital=100000.0,
    commission_per_trade=20.0,
    commission_pct=0.0003,  # 0.03%
    slippage_pct=0.001,     # 0.1%
    position_sizing='percentage',
    position_size=0.10,     # 10% of capital per trade
    enable_stop_loss=True,
    enable_take_profit=True
)

# Setup data provider
data_provider = HistoricalDataProvider(
    data_source='csv',  # or 'sqlite', 'postgres'
    data_path='historical_data'
)

# Initialize backtester
backtester = Backtester(config, data_provider)

# Run backtest
result = backtester.run_backtest(
    strategy_func=example_strategy,
    symbol='NIFTY50',
    start_date=datetime(2023, 1, 1),
    end_date=datetime(2023, 12, 31),
    strategy_params={
        'short_period': 10,
        'long_period': 20,
        'stop_loss_pct': 0.05,
        'take_profit_pct': 0.10
    }
)

# Print results
print(f"\n{'='*80}")
print("BACKTEST RESULTS")
print(f"{'='*80}")
print(f"Initial Capital:  ₹{result.initial_capital:,.2f}")
print(f"Final Capital:    ₹{result.final_capital:,.2f}")
print(f"Total P&L:        ₹{result.total_pnl:,.2f}")
print(f"Return:           {result.total_pnl/result.initial_capital*100:.2f}%")
print(f"\nTotal Trades:     {result.total_trades}")
print(f"Win Rate:         {result.win_rate:.2f}%")
print(f"Profit Factor:    {result.profit_factor:.2f}")
print(f"\nSharpe Ratio:     {result.sharpe_ratio:.2f}")
print(f"Sortino Ratio:    {result.sortino_ratio:.2f}")
print(f"Max Drawdown:     ₹{result.max_drawdown:,.2f} ({result.max_drawdown_pct:.2f}%)")
print(f"Calmar Ratio:     {result.calmar_ratio:.2f}")

# Save results
backtester.save_results(result)
```

### Writing a Strategy Function

```python
import pandas as pd
from typing import Dict

def my_strategy(data: pd.DataFrame, params: Dict) -> str:
    """
    Custom strategy function.

    Args:
        data: Historical price data up to current bar
              Columns: timestamp, open, high, low, close, volume
        params: Strategy parameters

    Returns:
        'BUY' - Enter long position
        'SELL' - Exit position
        'HOLD' - Do nothing
    """
    if len(data) < 20:
        return 'HOLD'

    # Example: Moving average crossover
    short_ma = data['close'].tail(10).mean()
    long_ma = data['close'].tail(20).mean()

    if short_ma > long_ma:
        return 'BUY'
    elif short_ma < long_ma:
        return 'SELL'

    return 'HOLD'
```

### Position Sizing Methods

**Fixed:**
```python
position_sizing='fixed'
position_size=15  # Always trade 15 lots
```

**Percentage of Capital:**
```python
position_sizing='percentage'
position_size=0.10  # Use 10% of capital per trade
```

**Kelly Criterion:**
```python
position_sizing='kelly'
# Automatically calculates optimal position size
```

### Historical Data Sources

**CSV Files:**
```python
data_provider = HistoricalDataProvider(
    data_source='csv',
    data_path='historical_data'
)
# Expects files like: historical_data/NIFTY50.csv
```

**SQLite Database:**
```python
data_provider = HistoricalDataProvider(
    data_source='sqlite',
    data_path='historical_data.db'
)
```

**PostgreSQL:**
```python
# Set environment variables:
# DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD

data_provider = HistoricalDataProvider(
    data_source='postgres'
)
```

---

## 📊 4. Web Dashboard

### Features

- Real-time performance monitoring
- Daily/weekly/monthly summaries
- Strategy comparison view
- Interactive charts
- Auto-refresh every 30 seconds

### Starting the Dashboard

```bash
# Method 1: Using the module directly
python utils/dashboard.py

# Method 2: Programmatic start
python -c "from utils.dashboard import run_dashboard; run_dashboard()"
```

Open your browser to: **http://localhost:5000**

### Dashboard Pages

**Home (/):**
- Today's summary card
- This week's performance
- Monthly overview
- Best strategy highlight

**Reports (/reports):**
- Download daily reports
- Download weekly reports
- Download monthly reports
- Strategy comparison reports

**Strategies (/strategies):**
- Strategy comparison table
- Rankings by various metrics
- Performance breakdown

**Charts (/charts):**
- Equity curve
- Daily P&L distribution
- Strategy performance comparison

### API Endpoints

```bash
# Daily summary
GET /api/daily-summary?date=2024-01-15

# Weekly summary
GET /api/weekly-summary

# Monthly summary
GET /api/monthly-summary?year=2024&month=1

# Strategy comparison
GET /api/strategy-comparison

# Equity curve data
GET /api/equity-curve?strategy=bank_nifty_combined_premium
```

### Customization

Edit `utils/dashboard.py` to:
- Change dashboard port
- Modify refresh intervals
- Add custom charts
- Customize styling

---

## 🎯 5. Performance Attribution

### Features

Analyze performance across multiple dimensions:
- **By Index**: NIFTY, BANK NIFTY, FINNIFTY, SENSEX
- **By Strategy Type**: Fixed SL, MTM-based, Trailing, etc.
- **By Time of Day**: Morning, mid-day, afternoon
- **By Option Type**: CALL vs PUT performance

### Usage

```python
from utils.performance_attribution import PerformanceAttributor

# Initialize
attributor = PerformanceAttributor()

# Analyze by index
index_attribution = attributor.analyze_by_index(
    start_date='2024-01-01',
    end_date='2024-01-31'
)

print("\nPerformance by Index:")
for index, metrics in index_attribution.breakdown.items():
    print(f"\n{index}:")
    print(f"  Total P&L:     ₹{metrics['total_pnl']:,.2f}")
    print(f"  Win Rate:      {metrics['win_rate']:.2f}%")
    print(f"  Profit Factor: {metrics['profit_factor']:.2f}")
    print(f"  Total Trades:  {metrics['total_trades']}")

print("\nInsights:")
for insight in index_attribution.insights:
    print(f"  • {insight}")

# Analyze by strategy type
type_attribution = attributor.analyze_by_strategy_type()

print("\nPerformance by Strategy Type:")
for strategy_type, metrics in type_attribution.breakdown.items():
    print(f"\n{strategy_type}:")
    print(f"  Total P&L: ₹{metrics['total_pnl']:,.2f}")
    print(f"  Win Rate:  {metrics['win_rate']:.2f}%")

# Analyze by time of day
time_attribution = attributor.analyze_by_time_of_day()

print("\nPerformance by Time of Day:")
for time_period, metrics in time_attribution.breakdown.items():
    print(f"{time_period}: ₹{metrics['total_pnl']:,.2f}")

# Comprehensive attribution (all dimensions)
all_attributions = attributor.generate_comprehensive_attribution(
    start_date='2024-01-01',
    end_date='2024-01-31'
)

# Save report
attributor.save_attribution_report(all_attributions)
```

### Attribution Dimensions

**Index Attribution:**
- Identifies which indices are most profitable
- Compares NIFTY 50, BANK NIFTY, FINNIFTY, SENSEX
- Shows win rates and profit factors by index

**Strategy Type Attribution:**
- Compares different strategy variants
- Fixed Stop Loss vs MTM-based vs Trailing
- Identifies most effective approach

**Time of Day Attribution:**
- Morning (9-11 AM)
- Mid-Day (11 AM-1 PM)
- Afternoon (1-3 PM)
- After Hours (3 PM+)

**Option Type Attribution:**
- CALL option performance
- PUT option performance
- Comparison between the two

### Insights Generated

Attribution analysis provides actionable insights:

✅ **Best Performers**: Identifies top-performing indices/strategies
⚠️ **Underperformers**: Flags strategies losing money
📊 **Consistency**: Highlights strategies with high win rates
🕐 **Timing**: Identifies best/worst trading times

---

## 📚 Complete Example

### End-to-End Analytics Workflow

```python
from utils.report_generator import ReportGenerator
from utils.strategy_analyzer import StrategyAnalyzer
from utils.performance_attribution import PerformanceAttributor
from datetime import datetime, timedelta

# Initialize components
report_gen = ReportGenerator()
analyzer = StrategyAnalyzer()
attributor = PerformanceAttributor()

# 1. Generate monthly report
print("=" * 80)
print("MONTHLY REPORT")
print("=" * 80)

monthly_report = report_gen.generate_monthly_report(
    year=2024,
    month=1,
    output_format='all'
)

print(f"Total P&L:        ₹{monthly_report.total_pnl:,.2f}")
print(f"Trading Days:     {monthly_report.total_trading_days}")
print(f"Total Trades:     {monthly_report.total_trades}")
print(f"Win Rate:         {monthly_report.win_rate:.2f}%")
print(f"Sharpe Ratio:     {monthly_report.sharpe_ratio:.2f}")

# 2. Compare strategies
print("\n" + "=" * 80)
print("STRATEGY COMPARISON")
print("=" * 80)

comparison = analyzer.compare_strategies(
    start_date='2024-01-01',
    end_date='2024-01-31'
)

print(f"\n🏆 Overall Best: {comparison.overall_best_strategy}")
print(f"\nTop 3 by P&L:")
for i, strategy in enumerate(comparison.rankings['total_pnl'][:3], 1):
    print(f"  {i}. {strategy}")

# 3. Performance attribution
print("\n" + "=" * 80)
print("PERFORMANCE ATTRIBUTION")
print("=" * 80)

attributions = attributor.generate_comprehensive_attribution(
    start_date='2024-01-01',
    end_date='2024-01-31'
)

# Index attribution
print("\nBy Index:")
for index, metrics in attributions['index'].breakdown.items():
    print(f"  {index}: ₹{metrics['total_pnl']:,.2f} ({metrics['win_rate']:.1f}% WR)")

# Strategy type attribution
print("\nBy Strategy Type:")
for stype, metrics in attributions['strategy_type'].breakdown.items():
    print(f"  {stype}: ₹{metrics['total_pnl']:,.2f}")

# Time of day attribution
print("\nBy Time of Day:")
for time, metrics in attributions['time_of_day'].breakdown.items():
    print(f"  {time}: ₹{metrics['total_pnl']:,.2f}")

# 4. Print all insights
print("\n" + "=" * 80)
print("KEY INSIGHTS")
print("=" * 80)

all_insights = []
for dim in ['index', 'strategy_type', 'time_of_day', 'option_type']:
    all_insights.extend(attributions[dim].insights)

for insight in all_insights:
    print(f"  • {insight}")

# 5. Save all reports
analyzer.save_comparison_report(comparison, output_format='all')
attributor.save_attribution_report(attributions)

print("\n✅ All reports saved to reports/ directory")
```

---

## 🔧 Installation

### Required Dependencies

```bash
# Core dependencies (already in requirements.txt)
pip install pandas numpy

# Analytics dependencies (recommended)
pip install matplotlib plotly jinja2

# Full installation
pip install -r requirements.txt
```

### Optional Dependencies

For enhanced features:

```bash
# For PostgreSQL support (backtesting with DB)
pip install psycopg2-binary

# For advanced SQL operations
pip install sqlalchemy
```

---

## 📂 File Structure

```
utils/
├── report_generator.py          # Daily/weekly/monthly reports
├── strategy_analyzer.py         # Strategy comparison
├── backtester.py                # Backtesting framework
├── dashboard.py                 # Web dashboard
├── performance_attribution.py   # Performance attribution
├── metrics.py                   # Existing metrics tracker
└── logging_config.py            # Logging utilities

reports/
├── daily/                       # Daily reports
├── weekly/                      # Weekly reports
├── monthly/                     # Monthly reports
├── backtest/                    # Backtest results
└── analysis/                    # Attribution & comparison
```

---

## 🎓 Best Practices

### 1. Regular Reporting

```bash
# Create a daily cron job
0 18 * * * python -c "from utils.report_generator import ReportGenerator; ReportGenerator().generate_daily_report(output_format='all')"
```

### 2. Strategy Review

Weekly review process:
1. Generate weekly report
2. Compare all strategies
3. Check performance attribution
4. Adjust allocations based on insights

### 3. Backtesting Before Deploy

Always backtest new strategies:
```python
# Backtest on 6 months of data
result = backtester.run_backtest(
    new_strategy,
    symbol='BANKNIFTY',
    start_date=datetime(2023, 6, 1),
    end_date=datetime(2023, 12, 31)
)

if result.sharpe_ratio > 1.0 and result.win_rate > 50:
    print("✅ Strategy passed backtest - ready for live deployment")
else:
    print("⚠️ Strategy needs optimization")
```

### 4. Monitor Attribution

Check attribution monthly:
- Identify underperforming indices → reduce allocation
- Find best time periods → focus trading during those hours
- Compare strategy types → allocate more to winners

---

## 🆘 Troubleshooting

### Issue: "No metrics databases found"

**Solution:** Ensure strategies have been run and metrics recorded:
```python
# Strategies automatically create metrics databases in metrics/
# Location: metrics/{strategy_name}_metrics.db
```

### Issue: "No historical data loaded"

**Solution:** Verify data source:
```python
# CSV: Ensure files exist in data_path directory
# SQLite: Check database path
# PostgreSQL: Verify environment variables and connection
```

### Issue: Dashboard shows "Error loading data"

**Solution:**
1. Check that metrics databases exist
2. Ensure at least one trade has been executed
3. Check browser console for detailed error

### Issue: Matplotlib/Plotly not installed

**Solution:**
```bash
pip install matplotlib plotly jinja2
```

---

## 📊 Performance Metrics Glossary

| Metric | Description | Good Value |
|--------|-------------|------------|
| **Win Rate** | % of winning trades | > 50% |
| **Profit Factor** | Gross profit / Gross loss | > 1.5 |
| **Sharpe Ratio** | Risk-adjusted returns | > 1.0 |
| **Sortino Ratio** | Downside risk-adjusted returns | > 1.5 |
| **Calmar Ratio** | Return / Max drawdown | > 0.5 |
| **Max Drawdown** | Largest peak-to-trough decline | < 20% |

---

## 🎯 Next Steps

1. **Install Dependencies:**
   ```bash
   pip install matplotlib plotly jinja2
   ```

2. **Generate Your First Report:**
   ```python
   from utils.report_generator import ReportGenerator
   report = ReportGenerator().generate_daily_report(output_format='all')
   ```

3. **Start the Dashboard:**
   ```bash
   python utils/dashboard.py
   ```

4. **Compare Strategies:**
   ```python
   from utils.strategy_analyzer import StrategyAnalyzer
   comparison = StrategyAnalyzer().compare_strategies()
   ```

5. **Run a Backtest:**
   ```python
   from utils.backtester import Backtester, BacktestConfig, HistoricalDataProvider
   # Follow backtesting example above
   ```

---

## 📞 Support

For questions or issues:
- **Issues**: [GitHub Issues](https://github.com/buzzsubash/algo_trading_strategies_india/issues)
- **Documentation**: [README.md](README.md)
- **Code Quality**: [CODE_QUALITY.md](CODE_QUALITY.md)

---

**Happy Trading! 🚀📈**
