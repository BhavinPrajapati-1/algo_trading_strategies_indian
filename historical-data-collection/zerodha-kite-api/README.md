# Zerodha Kite Connect - Historical Data Downloader

A robust Python script for downloading and storing historical stock data from **Zerodha Kite Connect API** into PostgreSQL database. The script uses backward pagination strategy for efficient data collection from NSE and BSE exchanges.

## About Zerodha Kite Connect API

[Zerodha Kite Connect](https://kite.trade/) is a comprehensive trading API platform that provides:

- **Complete Trading Suite**: Order management, portfolio tracking, market data
- **Historical Data Access**: Up to 60+ years of historical data
- **Real-time Data**: Live market feeds and WebSocket support
- **Multi-Exchange Support**: NSE, BSE, MCX, NFO coverage
- **Python SDK**: Official KiteConnect library for easy integration
- **Robust Infrastructure**: High-availability trading platform

## Features

- ✅ **Backward Pagination Strategy**: Efficient data collection starting from recent dates
- ✅ **Multi-Exchange Support**: Downloads data from NSE and BSE exchanges
- ✅ **Smart Filtering**: Only processes equity instruments (lot_size = 1) with valid names
- ✅ **Database Optimization**: Bulk inserts with conflict resolution (ON CONFLICT DO NOTHING)
- ✅ **Comprehensive Error Handling**: Retry mechanisms for API calls and database operations
- ✅ **Progress Tracking**: Real-time statistics and processing updates
- ✅ **Test Mode**: Ability to test with specific symbols before full processing
- ✅ **Automatic Instrument Management**: Downloads and filters latest instrument dump

## Prerequisites

### Required Python Packages

```bash
pip install kiteconnect psycopg2-binary pandas requests pathlib
```

### System Requirements

- Python 3.6+
- PostgreSQL database
- Internet connection for API access
- **Zerodha Kite Connect subscription** (₹2000/month)

### Getting Zerodha Kite Connect API Access

1. **Subscribe to Kite Connect**: Visit [Kite Connect](https://kite.trade/) and subscribe
2. **Create App**: Register your application in Kite Connect dashboard
3. **Get API Keys**: Obtain API Key and API Secret from your app
4. **Generate Access Token**: Use login flow to generate access token
5. **Setup Authentication**: Configure credentials in the script

## File Structure

```
project/
├── zerodha_kite_historical_data_backward_pagination.py  # Main script
├── key_files/
│   └── access_token.txt          # Access token file
├── instruments.csv               # Instrument dump (auto-generated)
├── requirements.txt              # Dependencies
└── README.md                     # This file
```

## Configuration

### 1. Database Configuration

Edit the `DB_PARAMS` dictionary in the script:

```python
DB_PARAMS = {
    'dbname': 'your_database_name',
    'user': 'your_username', 
    'password': 'your_password',
    'host': 'your_host',
    'port': 5432
}
```

### 2. Zerodha Kite Connect API Credentials

Update the following variables in the script:

```python
api_key = "your_api_key"           # From Kite Connect app
api_secret = "your_api_secret"     # From Kite Connect app
```

### 3. Access Token Setup

Create the access token file at the specified path:

```bash
mkdir -p key_files
echo "your_access_token_here" > key_files/access_token.txt
```

**How to get Access Token:**
- Use Kite Connect login flow to generate access token
- Store the token in `key_files/access_token.txt`
- Access tokens are valid until next trading day
- Implement auto-renewal for production use

### 4. Database Table Structure

The script automatically creates these tables:

#### Instruments Table
```sql
CREATE TABLE instruments (
    instrument_token BIGINT PRIMARY KEY,
    exchange_token   BIGINT,
    tradingsymbol    VARCHAR(100),
    name             VARCHAR(200),
    last_price       DECIMAL(10, 2),
    expiry           DATE,
    strike           DECIMAL(10, 2),
    tick_size        DECIMAL(10, 4),
    lot_size         INTEGER,
    instrument_type  VARCHAR(20),
    segment          VARCHAR(20),
    exchange         VARCHAR(10)
);
```

#### Historical Data Table
```sql
CREATE TABLE z_kite_api_historical_data (
    id            SERIAL PRIMARY KEY,
    tradingsymbol VARCHAR(100),
    exchange      VARCHAR(10),
    timestamp     TIMESTAMP,
    open_price    DECIMAL(15, 4),
    high_price    DECIMAL(15, 4),
    low_price     DECIMAL(15, 4),
    close_price   DECIMAL(15, 4),
    volume        BIGINT,
    UNIQUE (tradingsymbol, exchange, timestamp)
);
```

## Usage

### Basic Usage

Download data for all filtered instruments:
```bash
python zerodha_kite_historical_data_backward_pagination.py
```

### Test Mode

Test with specific symbols before full processing:
```python
# Edit the configuration section in main()
TEST_MODE = True
CUSTOM_TEST_SYMBOLS = ['RELIANCE', 'HDFCBANK']
```

### Limited Processing

Process only first N instruments:
```python
# Edit the configuration section in main()
LIMIT = 10  # Process only first 10 instruments
```

## Script Workflow

### 1. Authentication & Setup
- Reads access token from file
- Authenticates with Kite Connect API
- Tests API connection and displays user profile
- Creates database tables and indexes

### 2. Instrument Management
- Downloads latest instrument dump from Kite API
- Filters for NSE and BSE exchanges only
- Removes instruments with lot_size ≠ 1 (keeps only equity)
- Filters out instruments with empty names
- Saves filtered instruments to database and CSV

### 3. Backward Pagination Strategy
- Starts from current date and goes backward
- Processes data in configurable batches (default: 1800 days per batch)
- Fetches historical data for each date range
- Handles API rate limits with delays and retries

### 4. Data Processing & Storage
- Processes OHLCV data from API response
- Bulk inserts data into PostgreSQL with conflict resolution
- Provides real-time progress updates and statistics
- Handles data format variations and errors gracefully

## Pagination Configuration

The script uses backward pagination with these configurable parameters:

```python
PAGINATION_CONFIG = {
    'days_per_batch': 1800,        # Days per API call
    'max_years_back': 70,          # Maximum years to fetch
    'api_delay_seconds': 0,        # Delay between API calls
    'max_retries': 3,              # Retries for failed calls
    'retry_delay': 1.0            # Delay between retries
}
```

## Filtering Logic

The script applies progressive filtering:

1. **Exchange Filter**: NSE and BSE only
2. **Lot Size Filter**: Only instruments with lot_size = 1 (equity instruments)
3. **Name Filter**: Only instruments with non-empty names

## Error Handling

### API Error Handling
- Automatic retries for failed API calls (max 3 attempts)
- Exponential backoff between retries
- Rate limiting compliance with configurable delays
- Graceful handling of API response format variations

### Database Error Handling
- Duplicate record prevention with UNIQUE constraints
- Transaction rollback on errors
- Connection retry mechanisms
- Bulk insert optimization for performance

## Monitoring and Logging

### Real-time Statistics
The script provides comprehensive progress tracking:
- Processing progress (instruments completed/total)
- Success/failure rates for API calls
- Total records downloaded and API calls made
- Estimated completion time and processing rates

### Log Information
- Detailed API call information with timing
- Batch processing progress with record counts
- Error details for troubleshooting
- Final summary with performance metrics

## Performance Optimization

### Database Optimizations
- Bulk inserts using `execute_values`
- Strategic indexes for query performance
- Conflict resolution without duplicates
- Transaction batching for efficiency

### API Optimizations
- Backward pagination for recent data priority
- Configurable batch sizes for optimal API usage
- Retry mechanisms with exponential backoff
- Rate limiting compliance

## Cost Considerations

**Zerodha Kite Connect Pricing:**
- Monthly subscription: ₹2000
- API call limits: Check current Kite Connect documentation
- Historical data: Included in subscription
- Real-time data: Included in subscription

## Troubleshooting

### Common Issues

**1. Authentication Failed**
- Verify API key and secret are correct
- Check access token file exists and contains valid token
- Ensure access token is not expired (regenerate daily)
- Verify Kite Connect subscription is active

**2. Database Connection Failed**
- Verify database credentials in `DB_PARAMS`
- Ensure PostgreSQL is running and accessible
- Check firewall settings for database port
- Verify database exists and user has proper permissions

**3. API Rate Limiting**
- Increase `api_delay_seconds` in pagination config
- Reduce `days_per_batch` for smaller API calls
- Check Kite Connect API documentation for current limits

**4. Data Format Issues**
- Monitor logs for API response format changes
- Check Kite Connect API documentation for updates
- Verify instrument token validity

### Resume Interrupted Downloads

The script handles interrupted downloads gracefully:
- Database constraints prevent duplicate records
- Each instrument is processed independently
- Failed instruments are logged for review
- Progress statistics help track completion

## Instrument Filtering Examples

**Before Filtering:**
- Total instruments: ~50,000+ (all exchanges, all types)

**After Exchange Filter (NSE + BSE):**
- Instruments: ~15,000-20,000

**After Lot Size Filter (lot_size = 1):**
- Instruments: ~8,000-10,000 (equity instruments only)

**After Name Filter (non-empty names):**
- Final instruments: ~7,000-9,000 (ready for processing)

## Data Coverage

### Historical Data Range
- **Maximum**: Up to 60+ years (depending on instrument)
- **Default**: 70 years configurable limit
- **Frequency**: Daily OHLCV data
- **Exchanges**: NSE and BSE equity instruments

### Data Fields
- **OHLCV**: Open, High, Low, Close, Volume
- **Timestamp**: Trading date and time
- **Symbol Information**: Trading symbol and exchange
- **Precision**: Up to 4 decimal places for prices

## Security Considerations

- Store access tokens securely (use environment variables in production)
- Rotate access tokens regularly (daily for Kite Connect)
- Use database connections with minimal required privileges
- Monitor API usage to stay within rate limits
- Implement proper error logging without exposing credentials

## Support and Maintenance

### Regular Maintenance
- Monitor API call success rates
- Update access tokens daily
- Review error logs for recurring issues
- Monitor database disk space usage
- Update instrument data regularly

### Performance Monitoring
- Track API response times
- Monitor database insert performance
- Review filtering statistics for data quality
- Analyze failed symbols for patterns

For issues or enhancements, review the error logs and adjust configuration parameters as needed.

## Additional Resources

### Zerodha Kite Connect Links
- **Official Website**: [https://kite.trade/](https://kite.trade/)
- **API Documentation**: [https://kite.trade/docs/](https://kite.trade/docs/)
- **Python SDK**: [https://github.com/zerodhatech/pykiteconnect](https://github.com/zerodhatech/pykiteconnect)
- **Support**: Available through Kite Connect support portal

### API Endpoints Used
- **Authentication**: Token-based authentication with access tokens
- **Instruments**: Live instrument dump download
- **Historical Data**: OHLCV data with flexible date ranges
- **User Profile**: Account verification and validation