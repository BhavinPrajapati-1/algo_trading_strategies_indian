"""
Dynamic Symbol Selection Module

Provides intelligent symbol/instrument selection for trading strategies.
Works seamlessly with the multi-broker architecture.

Features:
- ATM strike calculation for all indices
- Volatility-based instrument selection
- Liquidity filtering
- Technical indicator-based selection
- External service integration support

Author: Bhavin Prajapati
"""

from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass
import logging

from brokers.base import BaseBroker


logger = logging.getLogger(__name__)


@dataclass
class InstrumentInfo:
    """Information about a tradable instrument."""
    name: str
    exchange: str
    lot_size: int
    strike_interval: int  # Strike price interval (50 for NIFTY, 100 for BANKNIFTY)
    symbol: str  # Underlying symbol for LTP
    segment: str  # 'INDEX', 'EQUITY', 'COMMODITY'
    min_price_tick: float = 0.05
    freeze_quantity: Optional[int] = None


class SymbolSelector:
    """
    Intelligent symbol/instrument selection for trading strategies.

    Usage:
        selector = SymbolSelector(broker)

        # Get best instrument based on volatility
        best_instrument = selector.select_best_instrument(
            instruments=['BANKNIFTY', 'NIFTY', 'FINNIFTY'],
            criteria='volatility'
        )

        # Get ATM strike
        atm_strike = selector.get_atm_strike('BANKNIFTY')

        # Get option symbols
        call_symbol, put_symbol = selector.get_straddle_symbols(
            'BANKNIFTY', expiry='2024-12-26'
        )
    """

    # Predefined instrument configurations
    INSTRUMENTS = {
        'BANKNIFTY': InstrumentInfo(
            name='BANKNIFTY',
            exchange='NSE',
            lot_size=15,
            strike_interval=100,
            symbol='NIFTY BANK',
            segment='INDEX',
            freeze_quantity=900
        ),
        'NIFTY': InstrumentInfo(
            name='NIFTY',
            exchange='NSE',
            lot_size=50,  # Updated to current lot size
            strike_interval=50,
            symbol='NIFTY 50',
            segment='INDEX',
            freeze_quantity=1800
        ),
        'FINNIFTY': InstrumentInfo(
            name='FINNIFTY',
            exchange='NSE',
            lot_size=40,
            strike_interval=50,
            symbol='NIFTY FIN SERVICE',
            segment='INDEX',
            freeze_quantity=1800
        ),
        'MIDCPNIFTY': InstrumentInfo(
            name='MIDCPNIFTY',
            exchange='NSE',
            lot_size=75,
            strike_interval=25,
            symbol='NIFTY MID SELECT',
            segment='INDEX',
            freeze_quantity=4200
        ),
        'SENSEX': InstrumentInfo(
            name='SENSEX',
            exchange='BSE',
            lot_size=10,
            strike_interval=100,
            symbol='SENSEX',
            segment='INDEX',
            freeze_quantity=1000
        ),
        'BANKEX': InstrumentInfo(
            name='BANKEX',
            exchange='BSE',
            lot_size=15,
            strike_interval=100,
            symbol='BANKEX',
            segment='INDEX',
            freeze_quantity=1000
        )
    }

    def __init__(self, broker: BaseBroker):
        """
        Initialize symbol selector.

        Args:
            broker: Broker instance (any broker that implements BaseBroker)
        """
        self.broker = broker

    def get_instrument_info(self, instrument: str) -> InstrumentInfo:
        """
        Get information about an instrument.

        Args:
            instrument: Instrument name (BANKNIFTY, NIFTY, etc.)

        Returns:
            InstrumentInfo: Instrument configuration
        """
        instrument_upper = instrument.upper()
        if instrument_upper not in self.INSTRUMENTS:
            raise ValueError(f"Unknown instrument: {instrument}. "
                           f"Supported: {list(self.INSTRUMENTS.keys())}")

        return self.INSTRUMENTS[instrument_upper]

    def get_spot_price(self, instrument: str) -> float:
        """
        Get current spot price for an instrument.

        Args:
            instrument: Instrument name

        Returns:
            float: Current spot price
        """
        info = self.get_instrument_info(instrument)

        try:
            ltp = self.broker.get_ltp(info.symbol, info.exchange)
            logger.info(f"{instrument} LTP: {ltp}")
            return ltp

        except Exception as e:
            logger.error(f"Failed to get LTP for {instrument}: {e}")
            raise

    def get_atm_strike(self, instrument: str, spot_price: Optional[float] = None) -> int:
        """
        Calculate ATM (At The Money) strike for an instrument.

        Args:
            instrument: Instrument name
            spot_price: Current spot price (if None, will fetch)

        Returns:
            int: ATM strike price
        """
        info = self.get_instrument_info(instrument)

        if spot_price is None:
            spot_price = self.get_spot_price(instrument)

        interval = info.strike_interval
        remainder = spot_price % interval

        # Round to nearest strike
        if remainder < interval / 2:
            atm = spot_price - remainder
        else:
            atm = spot_price - remainder + interval

        return int(atm)

    def get_itm_otm_strikes(
        self,
        instrument: str,
        offset: int,
        spot_price: Optional[float] = None
    ) -> Tuple[int, int]:
        """
        Get ITM and OTM strikes with offset.

        Args:
            instrument: Instrument name
            offset: Number of strikes away from ATM (positive for OTM, negative for ITM)
            spot_price: Current spot price

        Returns:
            Tuple[int, int]: (call_strike, put_strike)
        """
        info = self.get_instrument_info(instrument)
        atm = self.get_atm_strike(instrument, spot_price)

        strike_offset = offset * info.strike_interval

        call_strike = atm + strike_offset  # Higher for calls
        put_strike = atm - strike_offset   # Lower for puts

        return call_strike, put_strike

    def get_option_symbol(
        self,
        instrument: str,
        strike: int,
        option_type: str,
        expiry: str
    ) -> str:
        """
        Build option trading symbol.

        Args:
            instrument: Instrument name
            strike: Strike price
            option_type: 'CE' or 'PE'
            expiry: Expiry date (YYYY-MM-DD or DDMMMYY format)

        Returns:
            str: Trading symbol (e.g., 'BANKNIFTY24DEC46000CE')
        """
        info = self.get_instrument_info(instrument)

        # Format expiry
        if '-' in expiry:  # YYYY-MM-DD format
            exp_date = datetime.strptime(expiry, '%Y-%m-%d')
            exp_str = exp_date.strftime('%y%b%d').upper()
        else:
            exp_str = expiry.upper()

        # Build symbol
        symbol = f"{info.name}{exp_str}{strike}{option_type}"

        logger.debug(f"Built symbol: {symbol}")
        return symbol

    def get_straddle_symbols(
        self,
        instrument: str,
        expiry: str,
        strike_offset: int = 0,
        spot_price: Optional[float] = None
    ) -> Tuple[str, str]:
        """
        Get Call and Put symbols for straddle/strangle.

        Args:
            instrument: Instrument name
            expiry: Expiry date
            strike_offset: Offset from ATM (0 for straddle, >0 for strangle)
            spot_price: Current spot price

        Returns:
            Tuple[str, str]: (call_symbol, put_symbol)
        """
        if strike_offset == 0:
            # Straddle - same strike
            atm = self.get_atm_strike(instrument, spot_price)
            call_strike = put_strike = atm
        else:
            # Strangle - different strikes
            call_strike, put_strike = self.get_itm_otm_strikes(
                instrument, strike_offset, spot_price
            )

        call_symbol = self.get_option_symbol(instrument, call_strike, 'CE', expiry)
        put_symbol = self.get_option_symbol(instrument, put_strike, 'PE', expiry)

        return call_symbol, put_symbol

    def select_best_instrument(
        self,
        instruments: List[str],
        criteria: str = 'volatility',
        lookback_days: int = 5
    ) -> str:
        """
        Select best instrument based on criteria.

        Args:
            instruments: List of instruments to compare
            criteria: Selection criteria ('volatility', 'volume', 'spread')
            lookback_days: Days to look back for analysis

        Returns:
            str: Best instrument name
        """
        if criteria == 'volatility':
            return self._select_by_volatility(instruments, lookback_days)
        elif criteria == 'volume':
            return self._select_by_volume(instruments)
        elif criteria == 'spread':
            return self._select_by_spread(instruments)
        else:
            logger.warning(f"Unknown criteria: {criteria}, defaulting to first instrument")
            return instruments[0]

    def _select_by_volatility(self, instruments: List[str], lookback_days: int) -> str:
        """
        Select instrument with highest recent volatility.

        Args:
            instruments: List of instruments
            lookback_days: Days to analyze

        Returns:
            str: Instrument with highest volatility
        """
        volatilities = {}

        end_date = datetime.now()
        start_date = end_date - timedelta(days=lookback_days)

        for instrument in instruments:
            try:
                info = self.get_instrument_info(instrument)

                # Get historical data
                hist_data = self.broker.get_historical_data(
                    symbol=info.symbol,
                    exchange=info.exchange,
                    from_date=start_date,
                    to_date=end_date,
                    interval='day'
                )

                if not hist_data:
                    continue

                # Calculate volatility (standard deviation of returns)
                closes = [candle['close'] for candle in hist_data]
                returns = [(closes[i] - closes[i-1]) / closes[i-1]
                          for i in range(1, len(closes))]

                import statistics
                volatility = statistics.stdev(returns) if len(returns) > 1 else 0

                volatilities[instrument] = volatility
                logger.info(f"{instrument} volatility: {volatility:.4f}")

            except Exception as e:
                logger.error(f"Error calculating volatility for {instrument}: {e}")
                volatilities[instrument] = 0

        if not volatilities:
            return instruments[0]

        # Return instrument with highest volatility
        best = max(volatilities.items(), key=lambda x: x[1])
        logger.info(f"Selected {best[0]} (volatility: {best[1]:.4f})")

        return best[0]

    def _select_by_volume(self, instruments: List[str]) -> str:
        """Select instrument with highest current volume."""
        volumes = {}

        for instrument in instruments:
            try:
                info = self.get_instrument_info(instrument)
                quote = self.broker.get_quote(info.symbol, info.exchange)

                volumes[instrument] = quote.volume
                logger.info(f"{instrument} volume: {quote.volume:,}")

            except Exception as e:
                logger.error(f"Error getting volume for {instrument}: {e}")
                volumes[instrument] = 0

        if not volumes:
            return instruments[0]

        best = max(volumes.items(), key=lambda x: x[1])
        return best[0]

    def _select_by_spread(self, instruments: List[str]) -> str:
        """Select instrument with tightest bid-ask spread."""
        spreads = {}

        for instrument in instruments:
            try:
                info = self.get_instrument_info(instrument)
                quote = self.broker.get_quote(info.symbol, info.exchange)

                if quote.bid_price > 0 and quote.ask_price > 0:
                    spread_pct = ((quote.ask_price - quote.bid_price) /
                                 quote.bid_price * 100)
                else:
                    spread_pct = float('inf')

                spreads[instrument] = spread_pct
                logger.info(f"{instrument} spread: {spread_pct:.4f}%")

            except Exception as e:
                logger.error(f"Error getting spread for {instrument}: {e}")
                spreads[instrument] = float('inf')

        if not spreads:
            return instruments[0]

        best = min(spreads.items(), key=lambda x: x[1])
        return best[0]

    def get_nearest_expiry(self, instrument: str) -> str:
        """
        Get nearest weekly expiry for an instrument.

        Args:
            instrument: Instrument name

        Returns:
            str: Nearest expiry date (YYYY-MM-DD)
        """
        info = self.get_instrument_info(instrument)

        # Get all instruments for the derivative exchange
        exchange = 'NFO' if info.exchange == 'NSE' else 'BFO'
        instruments = self.broker.get_instruments(exchange)

        # Filter by instrument name
        filtered = [inst for inst in instruments if inst.get('name') == info.name]

        if not filtered:
            raise ValueError(f"No derivatives found for {instrument}")

        # Get unique expiry dates
        expiries = list(set(inst.get('expiry') for inst in filtered if inst.get('expiry')))
        expiries = sorted([exp for exp in expiries if exp >= datetime.now().date()])

        if not expiries:
            raise ValueError(f"No future expiries found for {instrument}")

        return expiries[0].strftime('%Y-%m-%d')


def main():
    """Example usage."""
    from brokers import BrokerFactory

    # Create broker
    broker = BrokerFactory.create_from_env('zerodha')

    # Create selector
    selector = SymbolSelector(broker)

    # Example 1: Get ATM strike
    print("\n=== ATM Strike Calculation ===")
    atm = selector.get_atm_strike('BANKNIFTY')
    print(f"BANKNIFTY ATM: {atm}")

    # Example 2: Get straddle symbols
    print("\n=== Straddle Symbols ===")
    expiry = selector.get_nearest_expiry('BANKNIFTY')
    call, put = selector.get_straddle_symbols('BANKNIFTY', expiry)
    print(f"Call: {call}")
    print(f"Put: {put}")

    # Example 3: Select best instrument by volatility
    print("\n=== Best Instrument Selection ===")
    instruments = ['BANKNIFTY', 'NIFTY', 'FINNIFTY']
    best = selector.select_best_instrument(instruments, criteria='volatility')
    print(f"Best instrument (by volatility): {best}")


if __name__ == "__main__":
    main()
