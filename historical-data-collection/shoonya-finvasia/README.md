# Stock Historical Data Downloader

A robust Python script for downloading and storing historical stock data from **Finvasia Shoonya API** into PostgreSQL database. The script downloads data for NSE and BSE exchanges with comprehensive error handling, retry mechanisms, and database optimization.

## About Finvasia Shoonya API

[Finvasia Shoonya](https://shoonya.com/) is a discount brokerage platform that provides free API access for algorithmic trading and data retrieval. The Shoonya API offers:

- **Free API Access**: No charges for API usage
- **Real-time Data**: Live market data and historical data access
- **Multi-Exchange Support**: NSE, BSE, MCX, NCDEX coverage
- **Comprehensive Features**: Trading, portfolio management, and market data
- **Python SDK**: Official NorenRestApiPy library for easy integration

## Features

- **Multi-Exchange Support**: Downloads data from both NSE (National Stock Exchange) and BSE (Bombay Stock Exchange)
- **Robust Error Handling**: Comprehensive retry mechanisms for API calls and database operations
- **API Reset Window Detection**: Automatically pauses operations during API maintenance windows
- **Progress Tracking**: Checkpoint system to resume interrupted downloads
- **Database Optimization**: Batch inserts with conflict resolution (ON CONFLICT DO NOTHING)
- **Comprehensive Logging**: Detailed logging with timestamps and error tracking
- **Signal Handling**: Graceful shutdown on CTRL+C or termination signals

## Prerequisites

### Required Python Packages

```bash
pip install psycopg2-binary pandas pyotp requests NorenRestApiPy
```

### System Requirements

- Python 3.6+
- PostgreSQL database
- Internet connection for API access
- **Finvasia Shoonya trading account** with API access

### Getting Finvasia Shoonya API Access

1. **Open Account**: Register at [Finvasia Shoonya](https://shoonya.com/)
2. **Enable API**: Contact support to enable API access for your account
3. **Get Credentials**: Obtain your API credentials from the trading platform
4. **Setup 2FA**: Configure TOTP (Time-based One-Time Password) for authentication
5. **Download SDK**: The script uses the official `NorenRestApiPy` library

## File Structure

```
project/
├── stock_historical_data.py    # Main script
├── api_helper.py              # Shoonya API wrapper
├── download_symbols.py        # Symbol file downloader
├── NSE_symbols.txt           # NSE symbols (auto-downloaded)
├── BSE_symbols.txt           # BSE symbols (auto-downloaded)
├── logs/                     # Log directory (auto-created)
├── historical_data_checkpoint.txt  # Progress checkpoint
├── historical_data_progress.json   # Detailed progress info
└── README.md                 # This file
```

## Configuration

### 1. Database Configuration

Edit the `DB_PARAMS` dictionary in `stock_historical_data.py`:

```python
DB_PARAMS = {
    'dbname': 'your_database_name',
    'user': 'your_username', 
    'password': 'your_password',
    'host': 'your_host',
    'port': 5432
}
```

### 2. Finvasia Shoonya API Credentials

Update the following variables in `stock_historical_data.py`:

```python
VENDOR_CODE = 'YOUR_VENDOR_CODE'    # Provided by Finvasia
API_KEY = 'your_api_key'            # Your API secret key
IMEI = 'your_imei'                  # Device identifier
USER_ID = 'your_user_id'            # Your Shoonya user ID
PASSWORD = 'your_password'          # Your login password
TOTP_SECRET = 'your_totp_secret'    # From authenticator app (Google Authenticator/Authy)
```

**How to get these credentials:**
- **VENDOR_CODE**: Provided by Finvasia when API access is enabled
- **API_KEY**: Generated in your Shoonya trading platform under API settings
- **USER_ID**: Your Shoonya login user ID
- **PASSWORD**: Your regular login password
- **TOTP_SECRET**: Setup 2FA in your account and note the secret key for programmatic access
- **IMEI**: Any unique device identifier (can be any alphanumeric string)

### 3. Database Table Structure

The script automatically creates the following table:

```sql
CREATE TABLE z_shoonya_stock_historical_data (
    id         SERIAL PRIMARY KEY,
    exchange   VARCHAR(10),
    token      INTEGER,
    symbol     VARCHAR(50),
    event_time TIMESTAMP,
    open       NUMERIC,
    high       NUMERIC,
    low        NUMERIC,
    close      NUMERIC,
    volume     NUMERIC
);
```

## Usage

### Basic Usage

Download data for both NSE and BSE:
```bash
python stock_historical_data.py
```

### Exchange-Specific Downloads

Download NSE data only:
```bash
python stock_historical_data.py --nse
```

Download BSE data only:
```bash
python stock_historical_data.py --bse
```

Download both exchanges explicitly:
```bash
python stock_historical_data.py --both
```

### Advanced Options

Skip symbol file download (use existing files):
```bash
python stock_historical_data.py --skip-download
```

Force re-download symbol files:
```bash
python download_symbols.py --force
```

## Script Workflow

### 1. Symbol File Download
- Downloads latest NSE_symbols.txt and BSE_symbols.txt from Finvasia Shoonya API
- Extracts and verifies symbol files from `https://api.shoonya.com/`
- Processes symbols based on exchange rules:
  - **NSE**: Only 'EQ' (Equity) instruments
  - **BSE**: All instruments except 'F' (Futures)

### 2. API Authentication
- Generates TOTP using provided secret key
- Authenticates with Finvasia Shoonya API using NorenRestApiPy
- Maintains session throughout the download process
- Uses secure 2FA authentication

### 3. Database Preparation
- Creates optimized database connection
- Sets up indexes for better performance
- Temporarily disables triggers for faster inserts

### 4. Data Download and Storage
- Fetches historical data for each symbol
- Processes data in batches for optimal performance
- Handles duplicate records with `ON CONFLICT DO NOTHING`
- Provides real-time progress updates

### 5. Cleanup and Finalization
- Re-enables database triggers
- Updates table statistics
- Logs final summary statistics

## API Reset Windows

The script automatically detects and handles API maintenance windows:

- **IST (Indian Standard Time)**: 05:00 - 09:00
- **SGT (Singapore Time)**: 08:00 - 11:30

During these windows, the script will pause and resume automatically.

## Error Handling

### Retry Mechanisms
- **API Calls**: Up to 1 retry with exponential backoff
- **Database Operations**: Up to 3 retries with delays
- **Symbol File Downloads**: Up to 3 retries

### Failure Recovery
- Tracks consecutive failures
- Takes extended breaks after multiple failures
- Provides detailed error logging for troubleshooting

## Monitoring and Logging

### Progress Tracking
- Real-time status updates every 5 seconds
- Checkpoint files for resume capability
- Detailed progress JSON with statistics

### Log Files
- `logs/symbol_download_[timestamp].log`: Symbol download logs
- `error_log.txt`: Error details and stack traces
- `historical_data_checkpoint.txt`: Progress checkpoints
- `historical_data_progress.json`: Detailed progress information

### Status Information
The script provides comprehensive status updates including:
- Processing progress percentage
- Success/error/skip counts
- API and database timing statistics
- Estimated completion time
- Records insertion rate

## Performance Optimization

### Database Optimizations
- Batch inserts (1000 records per batch)
- Disabled triggers during bulk operations
- Optimized indexes for symbol and timestamp queries
- Connection pooling and reuse

### API Optimizations
- Single-threaded processing for stability
- Adaptive retry delays based on failure patterns
- Timeout handling for long-running requests
- Automatic rate limiting during high failure rates

## Troubleshooting

### Common Issues

**1. Database Connection Failed**
- Verify database credentials in `DB_PARAMS`
- Ensure PostgreSQL is running and accessible
- Check firewall settings for database port

**2. API Authentication Failed**
- Verify Finvasia Shoonya API credentials
- Check TOTP secret is correctly configured
- Ensure account has API access enabled by Finvasia
- Verify 2FA setup in your Shoonya account

**3. Symbol Files Not Found**
- Run `python download_symbols.py --force`
- Check internet connectivity
- Verify Finvasia Shoonya API endpoints are accessible (`https://api.shoonya.com/`)

**4. Memory Issues with Large Datasets**
- Reduce `BATCH_SIZE` in configuration
- Monitor system resources during execution
- Consider processing exchanges separately

### Resume Interrupted Downloads

The script automatically saves progress and can resume from interruption:

1. Check `historical_data_progress.json` for last processed symbol
2. Simply restart the script - it will resume automatically
3. Use the same command-line arguments as the original run

## Configuration Options

### Adjustable Parameters

```python
# Batch and performance settings
BATCH_SIZE = 1000                    # Records per database batch
MAX_RETRIES = 3                      # General retry count
MAX_API_RETRIES = 1                  # API-specific retries
API_TIMEOUT = 10                     # API request timeout (seconds)

# Logging and monitoring
VERBOSE_LOGGING = True               # Detailed API response logging
MAX_LOG_ITEMS = 5                    # Sample records to display
STATUS_UPDATE_INTERVAL = 5           # Status update frequency (seconds)

# Error handling
MAX_CONSECUTIVE_FAILURES = 10        # Failure threshold for breaks
FAILURE_RECOVERY_PAUSE = 10          # Recovery pause duration (seconds)
```

## Data Format

### API Response Fields
- `ssboe`: Unix timestamp for the trading date
- `into`: Opening price
- `inth`: Highest price
- `intl`: Lowest price  
- `intc`: Closing price
- `intv`: Volume traded

### Database Storage
All price data is stored as `NUMERIC` type for precision, with volume as `NUMERIC` to handle large trading volumes.

## Security Considerations

- Store API credentials securely (consider environment variables)
- Use database connection with minimal required privileges
- Regularly rotate API keys and passwords
- Monitor API usage to stay within rate limits

## Support and Maintenance

### Regular Maintenance
- Monitor log files for recurring errors
- Update symbol files regularly (script does this automatically)
- Vacuum database periodically for optimal performance
- Review and adjust retry parameters based on API performance

### Monitoring Checklist
- [ ] Database disk space
- [ ] Finvasia Shoonya API rate limit usage
- [ ] Error log file sizes
- [ ] Network connectivity to Finvasia Shoonya API
- [ ] Database connection pool status
- [ ] TOTP authentication status

## Additional Resources

### Finvasia Shoonya Links
- **Official Website**: [https://shoonya.com/](https://shoonya.com/)
- **API Documentation**: Contact Finvasia support for detailed API docs
- **Python SDK**: [NorenRestApiPy on GitHub](https://github.com/Shoonya-Dev/ShoonyaApi-py)
- **Support**: Available through Shoonya trading platform

### API Endpoints Used
- **Login**: `https://api.shoonya.com/NorenWClientTP/`
- **WebSocket**: `wss://api.shoonya.com/NorenWSTP/`
- **Symbol Files**: 
  - NSE: `https://api.shoonya.com/NSE_symbols.txt.zip`
  - BSE: `https://api.shoonya.com/BSE_symbols.txt.zip`

For issues or enhancements, review the error logs and adjust configuration parameters as needed.