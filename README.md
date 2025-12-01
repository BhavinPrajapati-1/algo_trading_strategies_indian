# Algo Trading - Option Selling Trading Strategies India

[![GitHub stars](https://img.shields.io/github/stars/buzzsubash/algo_trading_strategies_india?style=social)](https://github.com/buzzsubash/algo_trading_strategies_india/stargazers)
[![GitHub forks](https://img.shields.io/github/forks/buzzsubash/algo_trading_strategies_india?style=social)](https://github.com/buzzsubash/algo_trading_strategies_india/network/members)
[![License](https://img.shields.io/github/license/buzzsubash/algo_trading_strategies_india)](LICENSE)

## About
This repository is an **open-source** collection of **algorithmic trading strategies** for the Indian stock market, with a primary focus on **option selling** in:
- **NIFTY 50**
- **BANK NIFTY**
- **SENSEX**
- **MIDCAP NIFTY**
- **FIN NIFTY**

### 🔹 **Current Broker Support**
- ✅ **Zerodha** (Live & Ready to Deploy)
- ⚙️ **AngelOne, Upstox, Fyers, AliceBlue, etc.** *(Coming Soon!)*

## 🚀 Features

### 📈 **Trading Strategies**
✅ **Multiple short-straddle strategies** with different risk management techniques
✅ **Iron-fly strategies** for hedged option selling
✅ **Stop-loss mechanisms** including **fixed, percentage-based, and trailing stops**
✅ **Mark-to-market (MTM) based target execution**
✅ Future expansion for **multi-broker support**

### 📊 **Advanced Analytics & Backtesting** *(NEW!)*
✅ **Comprehensive Report Generation**
   - Daily/Weekly/Monthly P&L reports with complete trade breakdowns
   - Strategy and symbol-wise performance analysis
   - Export in JSON, Text, and HTML formats
   - Win rate, profit factor, Sharpe ratio, and max drawdown metrics

✅ **Strategy Comparison & Analysis**
   - Side-by-side comparison of all strategies
   - Risk-adjusted performance metrics (Sharpe, Sortino, Calmar ratios)
   - Weighted scoring system to identify best performers
   - Automated rankings by P&L, win rate, profit factor, and risk metrics
   - Actionable recommendations based on performance

✅ **Backtesting Framework**
   - Test strategies on historical data before live deployment
   - Commission and slippage modeling for realistic simulations
   - Multiple position sizing methods (Fixed, Percentage, Kelly Criterion)
   - Stop loss and take profit simulation
   - Support for CSV, SQLite, and PostgreSQL data sources
   - Comprehensive performance analytics (20+ metrics)

✅ **Real-time Web Dashboard**
   - Beautiful, responsive web interface for monitoring performance
   - Daily/Weekly/Monthly summary cards with auto-refresh
   - Strategy comparison and rankings view
   - RESTful API endpoints for integration
   - Visual analytics and performance charts

✅ **Performance Attribution Analysis**
   - Analyze by underlying index (NIFTY, BANK NIFTY, FINNIFTY, SENSEX)
   - Compare by strategy type (Fixed SL, MTM-based, Trailing, etc.)
   - Time-of-day analysis (Morning, Mid-day, Afternoon performance)
   - Option type breakdown (CALL vs PUT performance)
   - Automated insights and recommendations

📖 **Complete documentation available in [TRADING_ANALYTICS.md](TRADING_ANALYTICS.md)**

### 🚀 **Quick Start - Analytics Features**

```bash
# 1. Install analytics dependencies
pip install matplotlib plotly jinja2

# 2. Generate your first report
python -c "from utils.report_generator import ReportGenerator; ReportGenerator().generate_daily_report(output_format='all')"

# 3. Compare all strategies
python -c "from utils.strategy_analyzer import StrategyAnalyzer; print(StrategyAnalyzer().compare_strategies().overall_best_strategy)"

# 4. Start the web dashboard
python utils/dashboard.py
# Then open: http://localhost:5000

# 5. Run the comprehensive demo
python examples/analytics_demo.py
```

---

## 📂 Repository Structure

| Strategy Category | Sub-Category | Strategy Name | Zerodha | AngelOne | Upstox | Fyers | GitHub Link |
|------------------|-------------|---------------|---------|----------|--------|-------|-------------|
| **Short Straddle** | 0920 Expiry | FINNIFTY 0920 | ✅ | ❌ | ❌ | ❌ | [View Code](https://github.com/buzzsubash/algo_trading_strategies_india/blob/main/short-straddle/0920_short_straddle/finnifty_0920_short_straddle.py) |
|  |  | NIFTY50 0920 | ✅ | ❌ | ❌ | ❌ | [View Code](https://github.com/buzzsubash/algo_trading_strategies_india/blob/main/short-straddle/0920_short_straddle/nifty50_0920_short_straddle.py) |
|  |  | BANKNIFTY 0920 | ✅ | ❌ | ❌ | ❌ | [View Code](https://github.com/buzzsubash/algo_trading_strategies_india/blob/main/short-straddle/0920_short_straddle/banknifty_0920_short_straddle.py) |
|  |  | SENSEX 0920 | ✅ | ❌ | ❌ | ❌ | [View Code](https://github.com/buzzsubash/algo_trading_strategies_india/blob/main/short-straddle/0920_short_straddle/sensex_0920_short_straddle.py) |
|  | Combined Premium | BANK NIFTY Combined Premium | ✅ | ✅ | ❌ | ❌ | [View Code](https://github.com/buzzsubash/algo_trading_strategies_india/blob/main/short-straddle/combined_premium/bank_nifty_combined_premium_short_straddle.py) |
|  |  | FINNIFTY Combined Premium | ✅ | ❌ | ❌ | ❌ | [View Code](https://github.com/buzzsubash/algo_trading_strategies_india/blob/main/short-straddle/combined_premium/finnifty_combined_premium_short_straddle.py) |
|  |  | NIFTY50 Combined Premium | ✅ | ❌ | ❌ | ❌ | [View Code](https://github.com/buzzsubash/algo_trading_strategies_india/blob/main/short-straddle/combined_premium/nifty50_combined_premium_short_straddle.py) |
|  |  | SENSEX Combined Premium | ✅ | ❌ | ❌ | ❌ | [View Code](https://github.com/buzzsubash/algo_trading_strategies_india/blob/main/short-straddle/combined_premium/sensex_combined_premium_short_straddle.py) |
|  | Fixed Stop Loss | BANK NIFTY Fixed SL | ✅ | ❌ | ❌ | ❌ | [View Code](https://github.com/buzzsubash/algo_trading_strategies_india/blob/main/short-straddle/fixed_stop_loss/bank_nifty_fixed_stop_loss_short_straddle.py) |
|  |  | BANK NIFTY Account-Level MTM SL | ✅ | ❌ | ❌ | ❌ | [View Code](https://github.com/buzzsubash/algo_trading_strategies_india/blob/main/short-straddle/fixed_stop_loss/bank_nifty_account_level_mtm_with_fixed_stop_loss_short_straddle.py) |
|  | MTM Based Target | BANK NIFTY MTM-Based | ✅ | ❌ | ❌ | ❌ | [View Code](https://github.com/buzzsubash/algo_trading_strategies_india/blob/main/short-straddle/mtm_based_target/bank_nifty_mtm_based_short_straddle.py) |
|  |  | NIFTY50 MTM-Based | ✅ | ❌ | ❌ | ❌ | [View Code](https://github.com/buzzsubash/algo_trading_strategies_india/blob/main/short-straddle/mtm_based_target/nifty50_mtm_based_short_straddle.py) |
|  | Percentage-Based Stop Loss | BANK NIFTY Percentage-Based SL | ✅ | ❌ | ❌ | ❌ | [View Code](https://github.com/buzzsubash/algo_trading_strategies_india/blob/main/short-straddle/percentage_based_stop_loss/bank_nifty_percentage_based_stop_loss_short_straddle.py) |
|  | Trailing Stop Loss | BANK NIFTY Trailing Percentage-Based SL | ✅ | ❌ | ❌ | ❌ | [View Code](https://github.com/buzzsubash/algo_trading_strategies_india/blob/main/short-straddle/trailing_stop_loss/bank_nifty_trailing_percentage_based_stop_loss_short_straddle.py) |
| **Iron-Fly** | | | ⚙️ In Development | | | | *(Coming Soon!)* |
| **Short-Strangle** | | | ⚙️ In Development | | | | *(Coming Soon!)* |

---

### 📊 **Historical Data**

| **Data Source** | **Finvasia Shoonya** | **Zerodha Kite**                                                                                               | **AngelOne** | **Upstox** | **Fyers** |
|----------------|---------------------|----------------------------------------------------------------------------------------------------------------|--------------|------------|-----------|
| **Equity Data (NSE/BSE)** | ✅ **Ready** | ✅ **Ready**                                                                                                    | ⚙️ Coming Soon | ⚙️ Coming Soon | ⚙️ Coming Soon |
| **Options Data** | ⚙️ In Development | ⚙️ In Development                                                                                              | ⚙️ Coming Soon | ⚙️ Coming Soon | ⚙️ Coming Soon |
| **Futures Data** | ⚙️ In Development | ⚙️ In Development                                                                                              | ⚙️ Coming Soon | ⚙️ Coming Soon | ⚙️ Coming Soon |
| **Database Storage** | ✅ PostgreSQL | ✅ PostgreSQL                                                                                                   | ⚙️ Coming Soon | ⚙️ Coming Soon | ⚙️ Coming Soon |
| **API Cost** | 🆓 **Free** | 💰 ₹2000/month                                                                                                 | 💰 Paid | 💰 Paid | 💰 Paid |
| **GitHub Link** | [View Code](https://github.com/buzzsubash/algo_trading_strategies_india/tree/main/historical-data-collection/shoonya-finvasia) | [View Code](https://github.com/buzzsubash/algo_trading_strategies_india/tree/main/historical-data-collection/zerodha-kite-api) | *Coming Soon* | *Coming Soon* | *Coming Soon* |

---

### 🔧 **Broker Utilities & Auto-Login Scripts**

| **Utility Type** | **Broker** | **Description** | **Status** | **Features** | **GitHub Link** |
|------------------|------------|-----------------|------------|--------------|-----------------|
| **Auto-Login** | **Zerodha Kite** | Automated login with 2FA support | ✅ **Ready** | • TOTP Authentication<br>• Token Management<br>• Telegram Notifications<br>• Retry Mechanism<br>• Error Handling | [View Code](https://github.com/buzzsubash/algo_trading_strategies_india/blob/main/broker-utilities/zerodha-kite-connect-auto-login.py) |
| **Auto-Login** | **AngelOne** | Automated login script | ⚙️ **In Development** | • Session Management<br>• Token Storage<br>• Error Recovery | *Coming Soon* |
| **Auto-Login** | **Upstox** | Automated login script | ⚙️ **In Development** | • OAuth Integration<br>• Token Refresh<br>• Logging | *Coming Soon* |
| **Auto-Login** | **Fyers** | Automated login script | ⚙️ **In Development** | • PIN-based Auth<br>• Session Persistence | *Coming Soon* |
| **Session Manager** | **Multi-Broker** | Universal session management | ⚙️ **Planned** | • Cross-broker Support<br>• Unified Interface<br>• Health Monitoring | *Coming Soon* |
| **Token Validator** | **Multi-Broker** | Token validation utility | ⚙️ **Planned** | • Real-time Validation<br>• Auto-refresh<br>• Alerts | *Coming Soon* |
| **MTM Square-off System** | **Zerodha Kite** | Real-time MTM monitoring with automated square-off | ✅ **Ready** | • Real-time Position Monitoring<br>• Loss Threshold Protection<br>• Daily Profit Target Management<br>• Bulletproof Order Execution<br>• Trading Discipline Mode<br>• Volume Freeze Handling<br>• Comprehensive Logging | [View Code](https://github.com/buzzsubash/algo_trading_strategies_india/tree/main/broker-utilities/mtm_square_off_zerodha) |

---
---

## 📌 How to Use
1. Clone this repository:
   ```sh
   git clone https://github.com/buzzsubash/algo_trading_strategies_india.git
   

---

## 📩 Contact & Collaboration

We're always open to discussions on **algo trading**, whether it's:
✅ Enhancing existing strategies
✅ Designing new trading algorithms
✅ Deep-diving into strategy backtesting
✅ Exploring advanced risk management techniques

If you're interested in collaborating or discussing algo trading strategies, feel free to connect with us!

### 👥 **Project Maintainers**

#### **Bhavin Prajapati** - Lead Contributor & Analytics Developer
- 📧 **Email:** [PrajapatiBhavin1995@gmail.com](mailto:PrajapatiBhavin1995@gmail.com)
- 📱 **WhatsApp:** [+91 76004 60797](https://wa.me/917600460797)
- 💼 **Specialization:** Trading Analytics, Backtesting Framework, Performance Attribution

#### **Subash Krishnan** - Repository Creator
- 📱 **WhatsApp:** [https://wa.me/6594675969](https://wa.me/6594675969) [https://wa.me/919605006699](https://wa.me/919605006699)
- 🐦 **Twitter (X):** [https://x.com/buzzsubash](https://x.com/buzzsubash)
- 📍 **LinkedIn:** [https://www.linkedin.com/in/buzzsubash](https://www.linkedin.com/in/buzzsubash)
- 💻 **GitHub:** [https://github.com/buzzsubash](https://github.com/buzzsubash)
- 📘 **Facebook:** [https://www.facebook.com/buzzsubash/](https://www.facebook.com/buzzsubash/)
- 🏆 **Credly Certifications:** [https://www.credly.com/users/subash-krishnan](https://www.credly.com/users/subash-krishnan)
- 👾 **Reddit:** [https://www.reddit.com/user/buzzsubash/](https://www.reddit.com/user/buzzsubash/)
- 📝 **Blog:** [https://emcsaninfo.wordpress.com/](https://emcsaninfo.wordpress.com/)

---

## 💡 Feature Requests & Suggestions

We **actively encourage** the community to share ideas and feature requests! Your input helps make this project better for everyone.

### 🌟 **How to Submit a Feature Request:**

1. **GitHub Issues** (Preferred):
   - Go to [Issues](https://github.com/buzzsubash/algo_trading_strategies_india/issues)
   - Click "New Issue"
   - Select "Feature Request" template
   - Describe your idea in detail

2. **Direct Contact:**
   - Email: [PrajapatiBhavin1995@gmail.com](mailto:PrajapatiBhavin1995@gmail.com)
   - WhatsApp: [+91 76004 60797](https://wa.me/917600460797)
   - Subject: "Feature Request: [Your Feature Name]"

3. **Discussion Forum:**
   - Start a discussion in [GitHub Discussions](https://github.com/buzzsubash/algo_trading_strategies_india/discussions)
   - Tag it with `enhancement` or `feature-request`

### 💭 **What We're Looking For:**

✨ New trading strategies or variations
✨ Additional broker integrations
✨ Enhanced analytics and reporting features
✨ Performance optimization ideas
✨ UI/UX improvements for the dashboard
✨ New risk management techniques
✨ Integration with other trading tools/platforms
✨ Documentation improvements

**All suggestions are welcome!** Even if you're not sure if something is feasible, please share your ideas. We'll evaluate each request and provide feedback.

---

🚀 **Let's build, test, and innovate in the algo trading space together!**  


## ⚠️ Disclaimer & Risk Warning

This repository contains my **personal work** and is intended **purely for educational purposes**.  
These strategies are **not** financial or investment advice. And I am **not a SEBI registered** investment advisor or a research analyst.

Trading in derivatives, particularly in options, carries **significant risk** and can result in substantial financial losses. **Over 90% of traders in index options incur losses**, as highlighted by financial regulators and experts.


🔥 **Trade Responsibly. Invest Wisely. Stay Safe.** 🔥
