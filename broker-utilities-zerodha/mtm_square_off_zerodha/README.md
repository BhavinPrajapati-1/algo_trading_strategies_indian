# MTM-Based Square-off Trading System

A comprehensive automated trading system for Zerodha Kite Connect that monitors Mark-to-Market (MTM) values in real-time and executes automatic square-off when loss thresholds are breached or daily profit targets are reached.

## What This System Does

### Core Features

**Real-time MTM Monitoring**
- Continuously monitors your portfolio's Mark-to-Market value every 3 seconds
- Tracks both unrealized P&L from open positions and realized P&L from closed trades
- Provides comprehensive position-by-position profit/loss breakdown

**Automated Risk Management**
- Automatically squares off all positions when MTM falls below your configured loss threshold
- Implements emergency stop-loss protection to limit trading losses
- Executes trades using market orders for immediate execution

**Trading Discipline Mode**
- Tracks daily maximum profit achieved during trading sessions
- Automatically squares off positions when daily profit target is reached
- Prevents overtrading by blocking new positions after target achievement

**Live Market Data Integration**
- Subscribes to real-time price feeds via Zerodha WebSocket API
- Maintains fresh LTP (Last Traded Price) data for accurate MTM calculations
- Handles multiple instruments simultaneously across NSE, BSE, and derivatives

**Bulletproof Order Execution**
- Implements prioritized square-off strategy (short positions covered first)
- Handles volume freeze limits by splitting large orders automatically
- Provides comprehensive order tracking and verification
- Includes retry mechanisms for failed orders with exponential backoff

## System Architecture

The system consists of three main components:

### 1. LTP Subscriber (`zerodha_ltp_subscriber.py`)
- Connects to Zerodha WebSocket API for real-time price data
- Maintains subscriptions to all instruments in your portfolio
- Stores live market data in SQLite database
- Automatically subscribes to new positions and maintains data throughout trading day

### 2. MTM Monitor (`zerodha_mtm_monitor.py`)
- Calculates total portfolio MTM every 3 seconds
- Monitors loss thresholds and daily profit targets
- Executes automatic square-off when conditions are triggered
- Tracks order execution and provides detailed logging

### 3. System Runner (`zerodha_runner.py`)
- Manages both LTP Subscriber and MTM Monitor processes
- Provides health monitoring and automatic process restart
- Offers system status reporting and control commands
- Handles graceful shutdown and cleanup

## Configuration

### Basic Settings (`config.yaml`)

```yaml
zerodha:
  api_key: "your_api_key_here"
  api_secret: "your_api_secret_here"

trading:
  mtm_loss_threshold: -10000    # Square-off when MTM reaches -10,000
  daily_max_profit_target: 2000  # Square-off when daily profit hits 2,000

risk_management:
  auto_square_off_enabled: true
  max_order_retries: 3
  order_retry_delay: 2

# Volume freeze quantities for different instruments
instruments:
  BANKNIFTY:
    volume_freeze_quantity: 900
  NIFTY:
    volume_freeze_quantity: 1800
  FINNIFTY:
    volume_freeze_quantity: 1800
```

## Setup Instructions

### Prerequisites

1. **Python Environment**
   - Python 3.7 or higher
   - Required packages: `kiteconnect`, `PyYAML`, `pandas`, `requests`

2. **Zerodha API Credentials**
   - API Key and Secret from Zerodha Developer Console
   - Valid access token (regenerate daily or use login automation)

3. **System Requirements**
   - Stable internet connection for real-time data
   - Minimum 100MB disk space for databases
   - Linux/Windows environment (tested on Ubuntu)

### Installation Steps

1. **Create project directory and files**
   ```bash
   mkdir zerodha-mtm-system
   cd zerodha-mtm-system
   ```

2. **Install dependencies**
   ```bash
   pip install kiteconnect PyYAML pandas requests colorlog
   ```

3. **Create configuration file**
   - Copy the sample `config.yaml` above
   - Update with your API credentials and risk parameters

4. **Create access token file**
   ```bash
   mkdir -p access_token
   echo "your_access_token_here" > access_token/access_token.txt
   ```

## Usage

### Start the Complete System

```bash
python zerodha_runner.py
```

This single command:
- Checks all prerequisites
- Starts LTP Subscriber for real-time data
- Starts MTM Monitor for risk management
- Begins continuous monitoring
- Auto-restarts any failed components

### Monitor System Status

```bash
# Quick status check
python zerodha_runner.py status

# Live status summary
python zerodha_runner.py summary

# Check prerequisites
python zerodha_runner.py check
```

### Stop the System

```bash
# Graceful shutdown
python zerodha_runner.py stop

# Or use Ctrl+C in the running terminal
```

## How It Works

### Normal Operation Flow

1. **System Startup**
   - Validates configuration and API connectivity
   - Connects to Zerodha WebSocket for live data
   - Fetches current positions from your account

2. **Real-time Monitoring**
   - Subscribes to live price feeds for all position instruments
   - Calculates total portfolio MTM every 3 seconds
   - Tracks both unrealized and realized P&L

3. **Risk Management**
   - Continuously compares MTM against configured thresholds
   - Monitors daily maximum profit for discipline enforcement
   - Triggers square-off when conditions are met

### Square-off Execution

When triggered, the system:

1. **Position Categorization**
   - Separates short positions (negative quantity) and long positions
   - Prioritizes short position coverage to reduce risk exposure

2. **Order Placement**
   - Places market orders for immediate execution
   - Splits large orders to handle volume freeze limits
   - Implements retry logic for failed orders

3. **Execution Verification**
   - Monitors order status until completion
   - Handles partial fills and pending orders
   - Provides detailed execution logging

4. **Post-execution Verification**
   - Confirms all positions are closed
   - Reports final MTM and remaining positions
   - Logs complete execution summary

## Risk Management Features

### Loss Protection
- **Threshold Monitoring**: Continuously tracks MTM against loss limit
- **Emergency Square-off**: Immediate position closure when threshold breached
- **Risk Prioritization**: Covers short positions first to minimize exposure

### Trading Discipline
- **Daily Target Tracking**: Monitors maximum profit achieved during session
- **Target-based Square-off**: Closes positions when daily target reached
- **Overtrading Prevention**: Blocks new positions after target achievement

### Order Execution Safety
- **Volume Freeze Handling**: Automatically splits orders exceeding limits
- **Retry Mechanisms**: Multiple attempts for failed orders
- **Timeout Protection**: Prevents hanging on unresponsive API calls
- **Execution Verification**: Confirms order completion before proceeding

## Monitoring and Logs

### Log Files
- `ltp_subscriber.log`: WebSocket data feed activity
- `mtm_monitor.log`: MTM calculations and square-off actions
- `system_runner.log`: Overall system health and process management

### Database Files
- `zerodha_trading.db`: Live price data and position information
- `zerodha_mtm.db`: MTM history and square-off tracking

### Key Metrics to Monitor
- **LTP Data Freshness**: Should be under 10 seconds old
- **Position Synchronization**: Matches actual Zerodha positions
- **MTM Calculation Accuracy**: Reflects real portfolio value
- **System Process Health**: Both components running smoothly

## Configuration Options

### Risk Parameters

```yaml
trading:
  mtm_loss_threshold: -10000      # Loss limit (negative value)
  daily_max_profit_target: 5000   # Daily profit target

risk_management:
  auto_square_off_enabled: true   # Enable/disable automation
  max_order_retries: 3           # Retry attempts for failed orders
  order_retry_delay: 2           # Seconds between retries
```

### Performance Tuning

```yaml
websocket:
  position_check_interval: 5     # Position monitoring frequency
  
system_monitoring:
  health_check_interval: 3       # Process health check frequency
```

### Instrument Configuration

```yaml
instruments:
  BANKNIFTY:
    volume_freeze_quantity: 900
  NIFTY:
    volume_freeze_quantity: 1800
  # Add other instruments as needed
```

## Safety Considerations

### Before Going Live

- Test with small position sizes initially
- Verify MTM calculations match Zerodha's display
- Ensure stable internet connectivity
- Keep Zerodha mobile app ready as backup
- Monitor logs during initial runs

### Risk Warnings

- **Market Orders**: System uses market orders which may have slippage
- **Network Dependency**: Requires stable internet for real-time operation
- **API Limits**: Respects Zerodha's API rate limits but monitor usage
- **Manual Override**: Always maintain ability to manually square-off via Zerodha platforms

### Best Practices

- **Regular Monitoring**: Check system status periodically during trading
- **Backup Plans**: Have manual square-off procedures ready
- **Position Limits**: Don't rely solely on automated systems for large positions
- **Testing**: Test configuration changes with small amounts first

## Troubleshooting

### Common Issues

**"Access Token Invalid"**
- Update the access token file with fresh token
- Restart the system after token update

**"No LTP Data"**
- Check internet connectivity
- Verify WebSocket connection in logs
- Ensure positions exist in your account

**"Square-off Failed"**
- Check order logs for specific error messages
- Verify sufficient margin for order placement
- Manual square-off via Zerodha app if needed

### Emergency Procedures

**If System Becomes Unresponsive**
1. Use Zerodha mobile app for immediate square-off
2. Stop system processes: `pkill -f zerodha`
3. Check logs for error details
4. Restart system after resolving issues

**If Auto Square-off Fails**
1. Immediately square-off manually via Zerodha platforms
2. Check system logs for failure reasons
3. Verify order status in Zerodha order book
4. Report issues for system improvement

## Performance Expectations

- **Response Time**: New position detection within 5 seconds
- **MTM Updates**: Every 3 seconds with fresh market data
- **Square-off Speed**: Typically completes within 30-60 seconds
- **Resource Usage**: Minimal CPU/memory impact on modern systems

## Support and Maintenance

### Regular Maintenance
- Monitor log files for errors or warnings
- Clean old database records periodically
- Update access tokens as required
- Backup configuration and database files

### System Updates
- Review and test configuration changes
- Monitor system performance after updates
- Keep backup of working configurations

## Disclaimer

This system is for educational and personal use. Users are responsible for:
- Verifying system behavior before live trading
- Understanding associated risks and limitations
- Maintaining appropriate risk management practices
- Complying with applicable trading regulations

Always maintain manual oversight and backup procedures when using automated trading systems.