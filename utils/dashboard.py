"""
Trading Analytics Dashboard

Web-based dashboard for visualizing trading performance, reports, and analytics.
Uses Flask for web server and matplotlib/plotly for charts.

Author: Trading Analytics Team
"""

from flask import Flask, render_template, jsonify, request
import json
from pathlib import Path
from datetime import datetime, timedelta
import logging
from typing import Dict, List, Optional

# Import analytics modules
from utils.report_generator import ReportGenerator
from utils.strategy_analyzer import StrategyAnalyzer
from utils.metrics import MetricsTracker

# Optional visualization libraries
try:
    import matplotlib
    matplotlib.use('Agg')  # Non-interactive backend
    import matplotlib.pyplot as plt
    import matplotlib.dates as mdates
    HAS_MATPLOTLIB = True
except ImportError:
    HAS_MATPLOTLIB = False

try:
    import plotly.graph_objects as go
    import plotly.express as px
    from plotly.subplots import make_subplots
    HAS_PLOTLY = True
except ImportError:
    HAS_PLOTLY = False


app = Flask(__name__)
app.config['SECRET_KEY'] = 'trading-dashboard-secret-key'

# Initialize components
report_generator = ReportGenerator()
strategy_analyzer = StrategyAnalyzer()
logger = logging.getLogger(__name__)


@app.route('/')
def index():
    """Dashboard home page."""
    return render_template_string(HOME_TEMPLATE)


@app.route('/api/daily-summary')
def daily_summary():
    """Get daily trading summary."""
    date = request.args.get('date', datetime.now().strftime('%Y-%m-%d'))

    try:
        daily_report = report_generator.generate_daily_report(
            date=date,
            output_format='none'
        )

        return jsonify({
            'date': daily_report.date,
            'total_trades': daily_report.total_trades,
            'winning_trades': daily_report.winning_trades,
            'losing_trades': daily_report.losing_trades,
            'win_rate': daily_report.win_rate,
            'total_pnl': daily_report.total_pnl,
            'net_pnl': daily_report.net_pnl,
            'profit_factor': daily_report.profit_factor,
            'largest_win': daily_report.largest_win,
            'largest_loss': daily_report.largest_loss,
            'strategy_breakdown': daily_report.strategy_breakdown
        })

    except Exception as e:
        logger.error(f"Error generating daily summary: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/weekly-summary')
def weekly_summary():
    """Get weekly trading summary."""
    try:
        weekly_report = report_generator.generate_weekly_report(
            output_format='none'
        )

        return jsonify({
            'start_date': weekly_report.start_date,
            'end_date': weekly_report.end_date,
            'total_trading_days': weekly_report.total_trading_days,
            'total_trades': weekly_report.total_trades,
            'total_pnl': weekly_report.total_pnl,
            'average_daily_pnl': weekly_report.average_daily_pnl,
            'best_day_pnl': weekly_report.best_day_pnl,
            'worst_day_pnl': weekly_report.worst_day_pnl,
            'win_rate': weekly_report.win_rate,
            'sharpe_ratio': weekly_report.sharpe_ratio,
            'max_drawdown': weekly_report.max_drawdown
        })

    except Exception as e:
        logger.error(f"Error generating weekly summary: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/monthly-summary')
def monthly_summary():
    """Get monthly trading summary."""
    year = request.args.get('year', type=int)
    month = request.args.get('month', type=int)

    try:
        monthly_report = report_generator.generate_monthly_report(
            year=year,
            month=month,
            output_format='none'
        )

        return jsonify({
            'start_date': monthly_report.start_date,
            'end_date': monthly_report.end_date,
            'total_trading_days': monthly_report.total_trading_days,
            'total_trades': monthly_report.total_trades,
            'total_pnl': monthly_report.total_pnl,
            'average_daily_pnl': monthly_report.average_daily_pnl,
            'win_rate': monthly_report.win_rate,
            'profit_factor': monthly_report.profit_factor,
            'sharpe_ratio': monthly_report.sharpe_ratio,
            'max_drawdown': monthly_report.max_drawdown,
            'strategy_performance': monthly_report.strategy_performance
        })

    except Exception as e:
        logger.error(f"Error generating monthly summary: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/strategy-comparison')
def strategy_comparison():
    """Compare all strategies."""
    try:
        comparison = strategy_analyzer.compare_strategies()

        return jsonify({
            'strategies': comparison.strategies,
            'period': comparison.comparison_period,
            'overall_best': comparison.overall_best_strategy,
            'best_by_metric': comparison.best_strategy_by_metric,
            'rankings': comparison.rankings,
            'recommendations': comparison.recommendations
        })

    except Exception as e:
        logger.error(f"Error comparing strategies: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/equity-curve')
def equity_curve():
    """Generate equity curve data."""
    strategy = request.args.get('strategy', 'all')

    try:
        # This would fetch actual equity curve from metrics database
        # For now, return sample data structure
        return jsonify({
            'dates': ['2024-01-01', '2024-01-02', '2024-01-03'],
            'equity': [100000, 102000, 101500],
            'strategy': strategy
        })

    except Exception as e:
        logger.error(f"Error generating equity curve: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/reports')
def reports_page():
    """Reports listing page."""
    return render_template_string(REPORTS_TEMPLATE)


@app.route('/strategies')
def strategies_page():
    """Strategy comparison page."""
    return render_template_string(STRATEGIES_TEMPLATE)


@app.route('/charts')
def charts_page():
    """Charts and visualizations page."""
    return render_template_string(CHARTS_TEMPLATE)


# HTML Templates (embedded for simplicity)

HOME_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Trading Analytics Dashboard</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }
        .container {
            max-width: 1400px;
            margin: 0 auto;
            background: white;
            border-radius: 15px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            overflow: hidden;
        }
        header {
            background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
            color: white;
            padding: 30px;
            text-align: center;
        }
        header h1 { font-size: 2.5em; margin-bottom: 10px; }
        header p { font-size: 1.1em; opacity: 0.9; }
        nav {
            background: #2c3e50;
            padding: 15px;
            display: flex;
            justify-content: center;
            gap: 20px;
        }
        nav a {
            color: white;
            text-decoration: none;
            padding: 10px 20px;
            border-radius: 5px;
            transition: background 0.3s;
        }
        nav a:hover { background: #34495e; }
        .dashboard-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
            padding: 30px;
        }
        .card {
            background: white;
            border: 2px solid #e0e0e0;
            border-radius: 10px;
            padding: 25px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            transition: transform 0.3s, box-shadow 0.3s;
        }
        .card:hover {
            transform: translateY(-5px);
            box-shadow: 0 8px 12px rgba(0,0,0,0.2);
        }
        .card h2 {
            color: #2c3e50;
            margin-bottom: 15px;
            font-size: 1.5em;
            border-bottom: 3px solid #3498db;
            padding-bottom: 10px;
        }
        .metric {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin: 15px 0;
            padding: 10px;
            background: #f8f9fa;
            border-radius: 5px;
        }
        .metric-label {
            font-weight: 600;
            color: #555;
        }
        .metric-value {
            font-size: 1.3em;
            font-weight: bold;
        }
        .positive { color: #27ae60; }
        .negative { color: #e74c3c; }
        .neutral { color: #3498db; }
        .loading {
            text-align: center;
            padding: 20px;
            color: #7f8c8d;
            font-style: italic;
        }
        footer {
            background: #2c3e50;
            color: white;
            text-align: center;
            padding: 20px;
            margin-top: 40px;
        }
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>📊 Trading Analytics Dashboard</h1>
            <p>Real-time Performance Monitoring & Analysis</p>
        </header>

        <nav>
            <a href="/">Dashboard</a>
            <a href="/reports">Reports</a>
            <a href="/strategies">Strategies</a>
            <a href="/charts">Charts</a>
        </nav>

        <div class="dashboard-grid">
            <div class="card">
                <h2>Today's Summary</h2>
                <div id="daily-summary" class="loading">Loading...</div>
            </div>

            <div class="card">
                <h2>This Week</h2>
                <div id="weekly-summary" class="loading">Loading...</div>
            </div>

            <div class="card">
                <h2>This Month</h2>
                <div id="monthly-summary" class="loading">Loading...</div>
            </div>

            <div class="card">
                <h2>Best Strategy</h2>
                <div id="best-strategy" class="loading">Loading...</div>
            </div>
        </div>

        <footer>
            <p>Algorithmic Trading Strategies for Indian Markets | © 2024</p>
        </footer>
    </div>

    <script>
        function formatCurrency(value) {
            return '₹' + value.toLocaleString('en-IN', {minimumFractionDigits: 2, maximumFractionDigits: 2});
        }

        function formatPercent(value) {
            return value.toFixed(2) + '%';
        }

        function getValueClass(value) {
            return value > 0 ? 'positive' : value < 0 ? 'negative' : 'neutral';
        }

        async function loadDailySummary() {
            try {
                const response = await fetch('/api/daily-summary');
                const data = await response.json();

                const html = `
                    <div class="metric">
                        <span class="metric-label">Total Trades</span>
                        <span class="metric-value neutral">${data.total_trades}</span>
                    </div>
                    <div class="metric">
                        <span class="metric-label">Win Rate</span>
                        <span class="metric-value ${getValueClass(data.win_rate - 50)}">${formatPercent(data.win_rate)}</span>
                    </div>
                    <div class="metric">
                        <span class="metric-label">P&L</span>
                        <span class="metric-value ${getValueClass(data.total_pnl)}">${formatCurrency(data.total_pnl)}</span>
                    </div>
                    <div class="metric">
                        <span class="metric-label">Net P&L</span>
                        <span class="metric-value ${getValueClass(data.net_pnl)}">${formatCurrency(data.net_pnl)}</span>
                    </div>
                `;

                document.getElementById('daily-summary').innerHTML = html;
            } catch (error) {
                document.getElementById('daily-summary').innerHTML = `<p class="negative">Error loading data</p>`;
            }
        }

        async function loadWeeklySummary() {
            try {
                const response = await fetch('/api/weekly-summary');
                const data = await response.json();

                const html = `
                    <div class="metric">
                        <span class="metric-label">Trading Days</span>
                        <span class="metric-value neutral">${data.total_trading_days}</span>
                    </div>
                    <div class="metric">
                        <span class="metric-label">Total P&L</span>
                        <span class="metric-value ${getValueClass(data.total_pnl)}">${formatCurrency(data.total_pnl)}</span>
                    </div>
                    <div class="metric">
                        <span class="metric-label">Avg Daily P&L</span>
                        <span class="metric-value ${getValueClass(data.average_daily_pnl)}">${formatCurrency(data.average_daily_pnl)}</span>
                    </div>
                    <div class="metric">
                        <span class="metric-label">Best Day</span>
                        <span class="metric-value positive">${formatCurrency(data.best_day_pnl)}</span>
                    </div>
                `;

                document.getElementById('weekly-summary').innerHTML = html;
            } catch (error) {
                document.getElementById('weekly-summary').innerHTML = `<p class="negative">Error loading data</p>`;
            }
        }

        async function loadMonthlySummary() {
            try {
                const response = await fetch('/api/monthly-summary');
                const data = await response.json();

                const html = `
                    <div class="metric">
                        <span class="metric-label">Trading Days</span>
                        <span class="metric-value neutral">${data.total_trading_days}</span>
                    </div>
                    <div class="metric">
                        <span class="metric-label">Total P&L</span>
                        <span class="metric-value ${getValueClass(data.total_pnl)}">${formatCurrency(data.total_pnl)}</span>
                    </div>
                    <div class="metric">
                        <span class="metric-label">Sharpe Ratio</span>
                        <span class="metric-value ${getValueClass(data.sharpe_ratio)}">${data.sharpe_ratio.toFixed(2)}</span>
                    </div>
                    <div class="metric">
                        <span class="metric-label">Max Drawdown</span>
                        <span class="metric-value negative">${formatCurrency(data.max_drawdown)}</span>
                    </div>
                `;

                document.getElementById('monthly-summary').innerHTML = html;
            } catch (error) {
                document.getElementById('monthly-summary').innerHTML = `<p class="negative">Error loading data</p>`;
            }
        }

        async function loadBestStrategy() {
            try {
                const response = await fetch('/api/strategy-comparison');
                const data = await response.json();

                const html = `
                    <div class="metric">
                        <span class="metric-label">Overall Best</span>
                        <span class="metric-value positive">${data.overall_best || 'N/A'}</span>
                    </div>
                    <div class="metric">
                        <span class="metric-label">Best P&L</span>
                        <span class="metric-value neutral">${data.best_by_metric?.total_pnl || 'N/A'}</span>
                    </div>
                    <div class="metric">
                        <span class="metric-label">Best Sharpe</span>
                        <span class="metric-value neutral">${data.best_by_metric?.sharpe_ratio || 'N/A'}</span>
                    </div>
                    <div class="metric">
                        <span class="metric-label">Strategies</span>
                        <span class="metric-value neutral">${data.strategies?.length || 0}</span>
                    </div>
                `;

                document.getElementById('best-strategy').innerHTML = html;
            } catch (error) {
                document.getElementById('best-strategy').innerHTML = `<p class="negative">Error loading data</p>`;
            }
        }

        // Load all summaries on page load
        window.addEventListener('DOMContentLoaded', () => {
            loadDailySummary();
            loadWeeklySummary();
            loadMonthlySummary();
            loadBestStrategy();

            // Refresh every 30 seconds
            setInterval(() => {
                loadDailySummary();
                loadWeeklySummary();
                loadMonthlySummary();
            }, 30000);
        });
    </script>
</body>
</html>
"""

REPORTS_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Reports - Trading Analytics</title>
    <style>
        body { font-family: Arial, sans-serif; padding: 20px; background: #f5f5f5; }
        .container { max-width: 1200px; margin: 0 auto; background: white; padding: 30px; border-radius: 10px; }
        h1 { color: #2c3e50; }
        .report-links { display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 20px; margin-top: 30px; }
        .report-card { background: #ecf0f1; padding: 20px; border-radius: 8px; text-align: center; cursor: pointer; transition: 0.3s; }
        .report-card:hover { background: #3498db; color: white; transform: scale(1.05); }
    </style>
</head>
<body>
    <div class="container">
        <h1>📄 Trading Reports</h1>
        <p>Access comprehensive trading reports and analytics</p>

        <div class="report-links">
            <div class="report-card" onclick="downloadReport('daily')">
                <h3>Daily Report</h3>
                <p>Today's trading summary</p>
            </div>
            <div class="report-card" onclick="downloadReport('weekly')">
                <h3>Weekly Report</h3>
                <p>This week's performance</p>
            </div>
            <div class="report-card" onclick="downloadReport('monthly')">
                <h3>Monthly Report</h3>
                <p>This month's analysis</p>
            </div>
            <div class="report-card" onclick="downloadReport('comparison')">
                <h3>Strategy Comparison</h3>
                <p>Compare all strategies</p>
            </div>
        </div>

        <div style="margin-top: 40px;">
            <a href="/" style="color: #3498db; text-decoration: none;">← Back to Dashboard</a>
        </div>
    </div>

    <script>
        function downloadReport(type) {
            alert(`Downloading ${type} report...`);
            // In production, this would trigger actual report download
        }
    </script>
</body>
</html>
"""

STRATEGIES_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Strategy Analysis - Trading Analytics</title>
    <style>
        body { font-family: Arial, sans-serif; padding: 20px; background: #f5f5f5; }
        .container { max-width: 1400px; margin: 0 auto; background: white; padding: 30px; border-radius: 10px; }
        h1 { color: #2c3e50; }
        table { width: 100%; border-collapse: collapse; margin-top: 20px; }
        th, td { padding: 12px; text-align: left; border-bottom: 1px solid #ddd; }
        th { background: #3498db; color: white; }
        tr:hover { background: #f5f5f5; }
        .positive { color: #27ae60; font-weight: bold; }
        .negative { color: #e74c3c; font-weight: bold; }
    </style>
</head>
<body>
    <div class="container">
        <h1>📈 Strategy Comparison</h1>
        <p>Compare performance across all trading strategies</p>

        <div id="strategy-table">Loading strategies...</div>

        <div style="margin-top: 40px;">
            <a href="/" style="color: #3498db; text-decoration: none;">← Back to Dashboard</a>
        </div>
    </div>

    <script>
        async function loadStrategies() {
            try {
                const response = await fetch('/api/strategy-comparison');
                const data = await response.json();

                let html = '<table><thead><tr>';
                html += '<th>Rank</th><th>Strategy</th><th>Total P&L</th><th>Win Rate</th><th>Sharpe Ratio</th>';
                html += '</tr></thead><tbody>';

                if (data.rankings && data.rankings.total_pnl) {
                    data.rankings.total_pnl.forEach((strategy, index) => {
                        html += `<tr>
                            <td>${index + 1}</td>
                            <td>${strategy}</td>
                            <td class="${index === 0 ? 'positive' : ''}">...</td>
                            <td>...</td>
                            <td>...</td>
                        </tr>`;
                    });
                }

                html += '</tbody></table>';
                document.getElementById('strategy-table').innerHTML = html;
            } catch (error) {
                document.getElementById('strategy-table').innerHTML = '<p class="negative">Error loading strategies</p>';
            }
        }

        window.addEventListener('DOMContentLoaded', loadStrategies);
    </script>
</body>
</html>
"""

CHARTS_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Charts - Trading Analytics</title>
    <style>
        body { font-family: Arial, sans-serif; padding: 20px; background: #f5f5f5; }
        .container { max-width: 1400px; margin: 0 auto; background: white; padding: 30px; border-radius: 10px; }
        h1 { color: #2c3e50; }
        .chart-placeholder { background: #ecf0f1; height: 400px; border-radius: 8px; display: flex; align-items: center; justify-content: center; margin: 20px 0; color: #7f8c8d; }
    </style>
</head>
<body>
    <div class="container">
        <h1>📊 Performance Charts</h1>
        <p>Visual analytics and performance charts</p>

        <h2>Equity Curve</h2>
        <div class="chart-placeholder">Equity curve chart will be displayed here</div>

        <h2>Daily P&L Distribution</h2>
        <div class="chart-placeholder">P&L distribution chart will be displayed here</div>

        <h2>Strategy Performance Comparison</h2>
        <div class="chart-placeholder">Strategy comparison chart will be displayed here</div>

        <div style="margin-top: 40px;">
            <a href="/" style="color: #3498db; text-decoration: none;">← Back to Dashboard</a>
        </div>
    </div>
</body>
</html>
"""


def run_dashboard(host='0.0.0.0', port=5000, debug=False):
    """
    Start the dashboard server.

    Args:
        host: Host address
        port: Port number
        debug: Enable debug mode
    """
    logger.info(f"Starting dashboard on http://{host}:{port}")
    app.run(host=host, port=port, debug=debug)


if __name__ == "__main__":
    import sys

    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    print("\n" + "=" * 80)
    print("TRADING ANALYTICS DASHBOARD")
    print("=" * 80)
    print(f"\nStarting server...")
    print(f"Open your browser and navigate to: http://localhost:5000")
    print(f"\nPress CTRL+C to stop the server\n")

    run_dashboard(debug=True)
