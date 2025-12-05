"""
Historical Data Fetcher

Universal module for fetching and storing historical market data from any broker.
Supports: Zerodha, Upstox, and other brokers through the unified API.

Features:
- Fetch OHLC data for any symbol
- Store data in SQLite database
- Cache management
- Multiple timeframes support
- Broker-agnostic interface

Author: Trading System Team
"""

import sqlite3
import pandas as pd
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Optional, Union
import logging
from dataclasses import dataclass, asdict

from brokers.base import BaseBroker


logger = logging.getLogger(__name__)


@dataclass
class HistoricalCandle:
    """Single candle data."""
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: int
    oi: int = 0  # Open Interest for derivatives


class HistoricalDataFetcher:
    """
    Fetch and store historical data from any broker.

    Usage:
        from brokers import BrokerFactory
        from utils.historical_data import HistoricalDataFetcher

        broker = BrokerFactory.create_from_env('upstox')
        fetcher = HistoricalDataFetcher(broker, db_path='data/historical.db')

        # Fetch data
        data = fetcher.fetch_and_store(
            symbol='RELIANCE',
            exchange='NSE',
            from_date='2024-01-01',
            to_date='2024-03-01',
            interval='day'
        )
    """

    def __init__(self, broker: BaseBroker, db_path: str = 'data/historical_data.db'):
        """
        Initialize historical data fetcher.

        Args:
            broker: Broker instance (Zerodha, Upstox, etc.)
            db_path: Path to SQLite database file
        """
        self.broker = broker
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

        # Initialize database
        self._init_database()

        logger.info(f"Historical data fetcher initialized with {broker.broker_name}")

    def _init_database(self):
        """Create database tables if they don't exist."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Create historical data table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS historical_data (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                symbol TEXT NOT NULL,
                exchange TEXT NOT NULL,
                interval TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                open REAL NOT NULL,
                high REAL NOT NULL,
                low REAL NOT NULL,
                close REAL NOT NULL,
                volume INTEGER NOT NULL,
                oi INTEGER DEFAULT 0,
                broker TEXT NOT NULL,
                fetched_at TEXT NOT NULL,
                UNIQUE(symbol, exchange, interval, timestamp, broker)
            )
        ''')

        # Create index for faster queries
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_symbol_exchange_interval
            ON historical_data(symbol, exchange, interval, timestamp)
        ''')

        # Create metadata table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS fetch_metadata (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                symbol TEXT NOT NULL,
                exchange TEXT NOT NULL,
                interval TEXT NOT NULL,
                from_date TEXT NOT NULL,
                to_date TEXT NOT NULL,
                records_count INTEGER NOT NULL,
                broker TEXT NOT NULL,
                fetched_at TEXT NOT NULL
            )
        ''')

        conn.commit()
        conn.close()

        logger.info("Database initialized successfully")

    def fetch_and_store(
        self,
        symbol: str,
        exchange: str,
        from_date: Union[str, datetime],
        to_date: Union[str, datetime],
        interval: str = 'day',
        force_refresh: bool = False
    ) -> pd.DataFrame:
        """
        Fetch historical data and store in database.

        Args:
            symbol: Trading symbol
            exchange: Exchange (NSE, BSE, NFO, etc.)
            from_date: Start date (YYYY-MM-DD or datetime)
            to_date: End date (YYYY-MM-DD or datetime)
            interval: Candle interval (minute, day, week, month)
            force_refresh: Force fetch even if data exists

        Returns:
            pd.DataFrame: Historical data
        """
        # Convert dates to datetime if strings
        if isinstance(from_date, str):
            from_date = datetime.strptime(from_date, '%Y-%m-%d')
        if isinstance(to_date, str):
            to_date = datetime.strptime(to_date, '%Y-%m-%d')

        logger.info(f"Fetching {symbol} ({exchange}) from {from_date} to {to_date}, interval: {interval}")

        # Check if data already exists
        if not force_refresh:
            existing_data = self._get_from_db(symbol, exchange, from_date, to_date, interval)
            if not existing_data.empty:
                logger.info(f"Found {len(existing_data)} existing records in database")
                return existing_data

        # Fetch from broker
        try:
            historical_data = self.broker.get_historical_data(
                symbol=symbol,
                exchange=exchange,
                from_date=from_date,
                to_date=to_date,
                interval=interval
            )

            if not historical_data:
                logger.warning(f"No data returned from broker for {symbol}")
                return pd.DataFrame()

            logger.info(f"Fetched {len(historical_data)} candles from {self.broker.broker_name}")

            # Store in database
            records_stored = self._store_in_db(
                symbol=symbol,
                exchange=exchange,
                interval=interval,
                data=historical_data
            )

            logger.info(f"Stored {records_stored} records in database")

            # Convert to DataFrame
            df = self._convert_to_dataframe(historical_data)

            # Store metadata
            self._store_metadata(
                symbol=symbol,
                exchange=exchange,
                interval=interval,
                from_date=from_date,
                to_date=to_date,
                records_count=len(df)
            )

            return df

        except Exception as e:
            logger.error(f"Error fetching historical data: {e}")
            raise

    def _store_in_db(
        self,
        symbol: str,
        exchange: str,
        interval: str,
        data: List[Dict]
    ) -> int:
        """Store historical data in database."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        records_stored = 0
        fetched_at = datetime.now().isoformat()

        for candle in data:
            try:
                # Handle different date formats
                if 'date' in candle:
                    timestamp = candle['date']
                elif 'timestamp' in candle:
                    timestamp = candle['timestamp']
                else:
                    continue

                # Convert to ISO format if datetime object
                if isinstance(timestamp, datetime):
                    timestamp = timestamp.isoformat()

                cursor.execute('''
                    INSERT OR REPLACE INTO historical_data
                    (symbol, exchange, interval, timestamp, open, high, low, close,
                     volume, oi, broker, fetched_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    symbol,
                    exchange,
                    interval,
                    timestamp,
                    float(candle.get('open', 0)),
                    float(candle.get('high', 0)),
                    float(candle.get('low', 0)),
                    float(candle.get('close', 0)),
                    int(candle.get('volume', 0)),
                    int(candle.get('oi', 0)),
                    self.broker.broker_name,
                    fetched_at
                ))

                records_stored += 1

            except Exception as e:
                logger.warning(f"Error storing candle: {e}")
                continue

        conn.commit()
        conn.close()

        return records_stored

    def _get_from_db(
        self,
        symbol: str,
        exchange: str,
        from_date: datetime,
        to_date: datetime,
        interval: str
    ) -> pd.DataFrame:
        """Retrieve historical data from database."""
        conn = sqlite3.connect(self.db_path)

        query = '''
            SELECT timestamp, open, high, low, close, volume, oi
            FROM historical_data
            WHERE symbol = ? AND exchange = ? AND interval = ?
            AND timestamp >= ? AND timestamp <= ?
            ORDER BY timestamp ASC
        '''

        df = pd.read_sql_query(
            query,
            conn,
            params=(
                symbol,
                exchange,
                interval,
                from_date.isoformat(),
                to_date.isoformat()
            )
        )

        conn.close()

        if not df.empty:
            df['timestamp'] = pd.to_datetime(df['timestamp'])

        return df

    def _convert_to_dataframe(self, data: List[Dict]) -> pd.DataFrame:
        """Convert historical data to pandas DataFrame."""
        if not data:
            return pd.DataFrame()

        df = pd.DataFrame(data)

        # Handle different date column names
        if 'date' in df.columns:
            df['timestamp'] = pd.to_datetime(df['date'])
            df = df.drop('date', axis=1)
        elif 'timestamp' in df.columns:
            df['timestamp'] = pd.to_datetime(df['timestamp'])

        # Ensure required columns exist
        required_cols = ['timestamp', 'open', 'high', 'low', 'close', 'volume']
        for col in required_cols:
            if col not in df.columns:
                if col == 'timestamp':
                    raise ValueError("Data must contain 'date' or 'timestamp' column")
                df[col] = 0

        # Add OI if missing
        if 'oi' not in df.columns:
            df['oi'] = 0

        # Sort by timestamp
        df = df.sort_values('timestamp').reset_index(drop=True)

        return df[['timestamp', 'open', 'high', 'low', 'close', 'volume', 'oi']]

    def _store_metadata(
        self,
        symbol: str,
        exchange: str,
        interval: str,
        from_date: datetime,
        to_date: datetime,
        records_count: int
    ):
        """Store fetch metadata."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            INSERT INTO fetch_metadata
            (symbol, exchange, interval, from_date, to_date, records_count, broker, fetched_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            symbol,
            exchange,
            interval,
            from_date.isoformat(),
            to_date.isoformat(),
            records_count,
            self.broker.broker_name,
            datetime.now().isoformat()
        ))

        conn.commit()
        conn.close()

    def get_data(
        self,
        symbol: str,
        exchange: str,
        from_date: Union[str, datetime],
        to_date: Union[str, datetime],
        interval: str = 'day'
    ) -> pd.DataFrame:
        """
        Get historical data (from DB if exists, else fetch).

        Args:
            symbol: Trading symbol
            exchange: Exchange
            from_date: Start date
            to_date: End date
            interval: Candle interval

        Returns:
            pd.DataFrame: Historical data
        """
        return self.fetch_and_store(
            symbol=symbol,
            exchange=exchange,
            from_date=from_date,
            to_date=to_date,
            interval=interval,
            force_refresh=False
        )

    def get_latest_candle(
        self,
        symbol: str,
        exchange: str,
        interval: str = 'day'
    ) -> Optional[Dict]:
        """Get the most recent candle for a symbol."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            SELECT timestamp, open, high, low, close, volume, oi
            FROM historical_data
            WHERE symbol = ? AND exchange = ? AND interval = ?
            ORDER BY timestamp DESC
            LIMIT 1
        ''', (symbol, exchange, interval))

        row = cursor.fetchone()
        conn.close()

        if row:
            return {
                'timestamp': row[0],
                'open': row[1],
                'high': row[2],
                'low': row[3],
                'close': row[4],
                'volume': row[5],
                'oi': row[6]
            }

        return None

    def clear_cache(self, symbol: Optional[str] = None, exchange: Optional[str] = None):
        """Clear cached historical data."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        if symbol and exchange:
            cursor.execute(
                'DELETE FROM historical_data WHERE symbol = ? AND exchange = ?',
                (symbol, exchange)
            )
            logger.info(f"Cleared cache for {symbol} ({exchange})")
        else:
            cursor.execute('DELETE FROM historical_data')
            cursor.execute('DELETE FROM fetch_metadata')
            logger.info("Cleared all cached data")

        conn.commit()
        conn.close()

    def get_fetch_stats(self) -> Dict:
        """Get statistics about fetched data."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('SELECT COUNT(*) FROM historical_data')
        total_records = cursor.fetchone()[0]

        cursor.execute('SELECT COUNT(DISTINCT symbol) FROM historical_data')
        unique_symbols = cursor.fetchone()[0]

        cursor.execute('SELECT broker, COUNT(*) FROM historical_data GROUP BY broker')
        broker_stats = dict(cursor.fetchall())

        conn.close()

        return {
            'total_records': total_records,
            'unique_symbols': unique_symbols,
            'by_broker': broker_stats,
            'database_path': str(self.db_path)
        }
