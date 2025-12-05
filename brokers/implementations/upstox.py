"""
Upstox Broker Implementation

Implements the BaseBroker interface for Upstox API v2.
Documentation: https://upstox.com/developer/api-documentation/

Author: Bhavin Prajapati
"""

from typing import List, Dict, Optional
from datetime import datetime, timedelta
import logging
import json

try:
    import upstox_client
    from upstox_client.rest import ApiException
except ImportError:
    upstox_client = None
    ApiException = Exception

from brokers.base import (
    BaseBroker,
    BrokerOrder,
    BrokerPosition,
    BrokerQuote,
    BrokerHolding,
    BrokerMargin
)


logger = logging.getLogger(__name__)


class UpstoxBroker(BaseBroker):
    """
    Upstox broker implementation using Upstox API v2.

    Documentation: https://upstox.com/developer/api-documentation/

    Installation:
        pip install upstox-python-sdk
    """

    def __init__(self, api_key: str, api_secret: str, access_token: Optional[str] = None):
        """
        Initialize Upstox broker.

        Args:
            api_key: Upstox API key
            api_secret: Upstox API secret
            access_token: Access token (if already authenticated)
        """
        super().__init__(api_key, api_secret, access_token)

        if upstox_client is None:
            raise ImportError(
                "Upstox Python SDK not installed. "
                "Install with: pip install upstox-python-sdk"
            )

        # Configure API client
        self.configuration = upstox_client.Configuration()

        if access_token:
            self.set_access_token(access_token)

    # ==========================================
    # Authentication
    # ==========================================

    def login(self, redirect_uri: Optional[str] = None, **kwargs) -> bool:
        """
        Login to Upstox (generates login URL or processes request token).

        Args:
            redirect_uri: Redirect URI for OAuth flow
            **kwargs: Additional parameters (code for token generation)

        Returns:
            bool: True if login successful
        """
        try:
            if 'code' in kwargs:
                # Generate access token from authorization code
                access_token = self.get_access_token(kwargs['code'])
                self.set_access_token(access_token)
                return True
            else:
                # Generate login URL
                redirect_uri = redirect_uri or "http://127.0.0.1:5000/callback"
                login_url = (
                    f"https://api.upstox.com/v2/login/authorization/dialog?"
                    f"client_id={self.api_key}&"
                    f"redirect_uri={redirect_uri}&"
                    f"response_type=code"
                )
                logger.info(f"Please login at: {login_url}")
                return False

        except Exception as e:
            logger.error(f"Authentication failed: {e}")
            return False

    def get_access_token(self, authorization_code: str, redirect_uri: str = "http://127.0.0.1:5000/callback") -> str:
        """
        Generate access token from authorization code.

        Args:
            authorization_code: Authorization code from OAuth flow
            redirect_uri: Redirect URI used in OAuth flow

        Returns:
            str: Access token
        """
        try:
            api_instance = upstox_client.LoginApi()
            api_response = api_instance.token(
                api_version='2.0',
                code=authorization_code,
                client_id=self.api_key,
                client_secret=self.api_secret,
                redirect_uri=redirect_uri,
                grant_type='authorization_code'
            )

            return api_response.access_token

        except ApiException as e:
            logger.error(f"Token generation failed: {e}")
            raise

    def set_access_token(self, access_token: str) -> None:
        """
        Set access token for API calls.

        Args:
            access_token: Valid access token
        """
        self.access_token = access_token
        self.configuration.access_token = access_token
        self._authenticated = True

        # Initialize API instances
        self._init_api_instances()

    def _init_api_instances(self):
        """Initialize Upstox API instances."""
        api_client = upstox_client.ApiClient(self.configuration)

        self.order_api = upstox_client.OrderApi(api_client)
        self.portfolio_api = upstox_client.PortfolioApi(api_client)
        self.user_api = upstox_client.UserApi(api_client)
        self.market_quote_api = upstox_client.MarketQuoteApi(api_client)
        self.market_history_api = upstox_client.HistoryApi(api_client)

    # ==========================================
    # Order Management
    # ==========================================

    def place_order(
        self,
        symbol: str,
        exchange: str,
        transaction_type: str,
        quantity: int,
        order_type: str = "MARKET",
        price: float = 0.0,
        product_type: str = "I",
        trigger_price: float = 0.0,
        validity: str = "DAY",
        **kwargs
    ) -> str:
        """
        Place an order on Upstox.

        Args:
            symbol: Trading symbol
            exchange: Exchange (NSE/BSE/NFO/BFO/MCX/CDS)
            transaction_type: BUY or SELL
            quantity: Order quantity
            order_type: MARKET/LIMIT/SL/SL-M
            price: Limit price
            product_type: I (Intraday)/D (Delivery)/CO/OCO
            trigger_price: Trigger price for SL orders
            validity: DAY/IOC
            **kwargs: disclosed_quantity, tag, etc.

        Returns:
            str: Order ID
        """
        try:
            # Map product type
            product_map = {
                'MIS': 'I',  # Intraday
                'CNC': 'D',  # Delivery
                'NRML': 'D'
            }
            product = product_map.get(product_type, product_type)

            # Map order type
            order_type_map = {
                'MARKET': 'MARKET',
                'LIMIT': 'LIMIT',
                'SL': 'SL',
                'SL-M': 'SL-M'
            }
            mapped_order_type = order_type_map.get(order_type, order_type)

            # Create order request
            order_data = upstox_client.PlaceOrderRequest(
                quantity=quantity,
                product=product,
                validity=validity,
                price=price if order_type in ['LIMIT', 'SL'] else 0,
                tag=kwargs.get('tag', ''),
                instrument_token=f"{exchange}|{symbol}",
                order_type=mapped_order_type,
                transaction_type=transaction_type,
                disclosed_quantity=kwargs.get('disclosed_quantity', 0),
                trigger_price=trigger_price if order_type in ['SL', 'SL-M'] else 0,
                is_amo=kwargs.get('is_amo', False)
            )

            response = self.order_api.place_order(
                body=order_data,
                api_version='2.0'
            )

            order_id = response.data.order_id
            logger.info(f"Order placed: {order_id} - {transaction_type} {quantity} {symbol}")
            return str(order_id)

        except ApiException as e:
            logger.error(f"Order placement failed: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error placing order: {e}")
            raise

    def modify_order(
        self,
        order_id: str,
        quantity: Optional[int] = None,
        price: Optional[float] = None,
        order_type: Optional[str] = None,
        trigger_price: Optional[float] = None,
        **kwargs
    ) -> str:
        """
        Modify an existing order.

        Args:
            order_id: Order ID to modify
            quantity: New quantity
            price: New price
            order_type: New order type
            trigger_price: New trigger price
            **kwargs: Additional parameters

        Returns:
            str: Order ID
        """
        try:
            modify_data = upstox_client.ModifyOrderRequest(
                quantity=quantity,
                validity=kwargs.get('validity', 'DAY'),
                price=price if price is not None else 0,
                order_type=order_type,
                trigger_price=trigger_price if trigger_price is not None else 0,
                disclosed_quantity=kwargs.get('disclosed_quantity', 0)
            )

            response = self.order_api.modify_order(
                order_id=order_id,
                body=modify_data,
                api_version='2.0'
            )

            logger.info(f"Order modified: {order_id}")
            return str(order_id)

        except ApiException as e:
            logger.error(f"Order modification failed: {e}")
            raise

    def cancel_order(self, order_id: str, **kwargs) -> bool:
        """
        Cancel an order.

        Args:
            order_id: Order ID to cancel
            **kwargs: Additional parameters

        Returns:
            bool: True if cancelled successfully
        """
        try:
            self.order_api.cancel_order(
                order_id=order_id,
                api_version='2.0'
            )
            logger.info(f"Order cancelled: {order_id}")
            return True

        except ApiException as e:
            logger.error(f"Order cancellation failed: {e}")
            return False

    def get_orders(self) -> List[BrokerOrder]:
        """
        Get all orders for the day.

        Returns:
            List[BrokerOrder]: List of orders
        """
        try:
            response = self.order_api.get_order_book(api_version='2.0')

            if not response.data:
                return []

            return [self._convert_to_broker_order(order) for order in response.data]

        except ApiException as e:
            logger.error(f"Failed to get orders: {e}")
            return []

    def get_order_history(self, order_id: str) -> List[BrokerOrder]:
        """
        Get order history/status updates.

        Args:
            order_id: Order ID

        Returns:
            List[BrokerOrder]: Order status history
        """
        try:
            response = self.order_api.get_order_details(
                api_version='2.0',
                order_id=order_id
            )

            if not response.data:
                return []

            return [self._convert_to_broker_order(order) for order in response.data]

        except ApiException as e:
            logger.error(f"Failed to get order history: {e}")
            return []

    # ==========================================
    # Position Management
    # ==========================================

    def get_positions(self) -> List[BrokerPosition]:
        """
        Get current positions.

        Returns:
            List[BrokerPosition]: List of positions
        """
        try:
            response = self.portfolio_api.get_positions(api_version='2.0')

            if not response.data:
                return []

            positions = []
            for pos in response.data:
                if pos.quantity != 0:  # Only include active positions
                    positions.append(self._convert_to_broker_position(pos))

            return positions

        except ApiException as e:
            logger.error(f"Failed to get positions: {e}")
            return []

    def get_holdings(self) -> List[BrokerHolding]:
        """
        Get holdings (long-term investments).

        Returns:
            List[BrokerHolding]: List of holdings
        """
        try:
            response = self.portfolio_api.get_holdings(api_version='2.0')

            if not response.data:
                return []

            return [self._convert_to_broker_holding(holding) for holding in response.data]

        except ApiException as e:
            logger.error(f"Failed to get holdings: {e}")
            return []

    def square_off_position(
        self,
        symbol: str,
        exchange: str,
        product_type: str = "I",
        **kwargs
    ) -> str:
        """
        Square off (exit) a position.

        Args:
            symbol: Trading symbol
            exchange: Exchange
            product_type: Product type (I/D)
            **kwargs: Additional parameters

        Returns:
            str: Order ID for square-off order
        """
        # Get current position
        positions = self.get_positions()
        position = next((p for p in positions if p.symbol == symbol and p.product_type == product_type), None)

        if not position:
            raise ValueError(f"No position found for {symbol}")

        # Determine transaction type (opposite of current position)
        transaction_type = "SELL" if position.quantity > 0 else "BUY"
        quantity = abs(position.quantity)

        # Place market order to square off
        return self.place_order(
            symbol=symbol,
            exchange=exchange,
            transaction_type=transaction_type,
            quantity=quantity,
            order_type="MARKET",
            product_type=product_type,
            **kwargs
        )

    # ==========================================
    # Market Data
    # ==========================================

    def get_quote(self, symbol: str, exchange: str) -> BrokerQuote:
        """
        Get quote/LTP for a symbol.

        Args:
            symbol: Trading symbol
            exchange: Exchange

        Returns:
            BrokerQuote: Quote data
        """
        try:
            instrument_key = f"{exchange}|{symbol}"
            response = self.market_quote_api.get_full_market_quote(
                symbol=instrument_key,
                api_version='2.0'
            )

            if not response.data:
                raise ValueError(f"No quote data for {symbol}")

            quote_data = response.data.get(instrument_key, {})
            return self._convert_to_broker_quote(quote_data, symbol, exchange)

        except ApiException as e:
            logger.error(f"Failed to get quote for {symbol}: {e}")
            raise

    def get_ltp(self, symbol: str, exchange: str) -> float:
        """
        Get Last Traded Price for a symbol.

        Args:
            symbol: Trading symbol
            exchange: Exchange

        Returns:
            float: Last traded price
        """
        try:
            instrument_key = f"{exchange}|{symbol}"
            response = self.market_quote_api.ltp(
                symbol=instrument_key,
                api_version='2.0'
            )

            if not response.data:
                raise ValueError(f"No LTP data for {symbol}")

            return response.data.get(instrument_key, {}).get('last_price', 0.0)

        except ApiException as e:
            logger.error(f"Failed to get LTP for {symbol}: {e}")
            raise

    def get_historical_data(
        self,
        symbol: str,
        exchange: str,
        from_date: datetime,
        to_date: datetime,
        interval: str = "day",
        **kwargs
    ) -> List[Dict]:
        """
        Get historical data.

        Args:
            symbol: Trading symbol
            exchange: Exchange
            from_date: Start date
            to_date: End date
            interval: 1minute/30minute/day/week/month
            **kwargs: Additional parameters

        Returns:
            List[Dict]: Historical data
        """
        try:
            instrument_key = f"{exchange}|{symbol}"

            # Map interval
            interval_map = {
                'minute': '1minute',
                '1minute': '1minute',
                '30minute': '30minute',
                'day': 'day',
                'week': 'week',
                'month': 'month'
            }
            mapped_interval = interval_map.get(interval, interval)

            response = self.market_history_api.get_historical_candle_data(
                instrument_key=instrument_key,
                interval=mapped_interval,
                to_date=to_date.strftime('%Y-%m-%d'),
                api_version='2.0'
            )

            if not response.data or not response.data.candles:
                return []

            # Convert to standard format
            historical_data = []
            for candle in response.data.candles:
                historical_data.append({
                    'date': candle[0],
                    'open': candle[1],
                    'high': candle[2],
                    'low': candle[3],
                    'close': candle[4],
                    'volume': candle[5] if len(candle) > 5 else 0,
                    'oi': candle[6] if len(candle) > 6 else 0
                })

            return historical_data

        except ApiException as e:
            logger.error(f"Failed to get historical data: {e}")
            raise

    # ==========================================
    # Account Information
    # ==========================================

    def get_margins(self) -> BrokerMargin:
        """
        Get margin information.

        Returns:
            BrokerMargin: Margin details
        """
        try:
            response = self.user_api.get_user_fund_margin(
                api_version='2.0',
                segment='SEC'  # Securities
            )

            if not response.data:
                raise ValueError("No margin data available")

            equity = response.data

            return BrokerMargin(
                available_cash=float(equity.get('available_margin', 0.0)),
                used_margin=float(equity.get('used_margin', 0.0)),
                total_margin=float(equity.get('available_margin', 0.0)) + float(equity.get('used_margin', 0.0)),
                collateral=float(equity.get('collateral', 0.0))
            )

        except ApiException as e:
            logger.error(f"Failed to get margins: {e}")
            raise

    def get_profile(self) -> Dict:
        """
        Get user profile information.

        Returns:
            Dict: Profile information
        """
        try:
            response = self.user_api.get_profile(api_version='2.0')

            if not response.data:
                return {}

            profile = response.data
            return {
                'user_id': profile.user_id,
                'user_name': profile.user_name,
                'email': profile.email,
                'user_type': profile.user_type,
                'broker': 'Upstox'
            }

        except ApiException as e:
            logger.error(f"Failed to get profile: {e}")
            raise

    # ==========================================
    # Instrument/Symbol Search
    # ==========================================

    def search_instruments(self, query: str, exchange: Optional[str] = None) -> List[Dict]:
        """
        Search for instruments.

        Args:
            query: Search query
            exchange: Filter by exchange (optional)

        Returns:
            List[Dict]: List of matching instruments
        """
        try:
            # Upstox doesn't have a direct search API
            # Fetch instruments and filter locally
            if exchange:
                instruments = self.get_instruments(exchange)
            else:
                # Search across common exchanges
                instruments = []
                for exch in ['NSE', 'BSE', 'NFO', 'BFO']:
                    try:
                        instruments.extend(self.get_instruments(exch))
                    except:
                        pass

            # Filter by query
            query_lower = query.lower()
            matches = [
                inst for inst in instruments
                if query_lower in inst.get('tradingsymbol', '').lower() or
                   query_lower in inst.get('name', '').lower()
            ]

            return matches[:50]  # Limit results

        except Exception as e:
            logger.error(f"Failed to search instruments: {e}")
            return []

    def get_instruments(self, exchange: str) -> List[Dict]:
        """
        Get all instruments for an exchange.

        Args:
            exchange: Exchange name

        Returns:
            List[Dict]: List of instruments
        """
        try:
            # Note: Upstox API v2 may require downloading CSV files
            # This is a placeholder - actual implementation may vary
            logger.warning("Instrument download may require CSV parsing")
            return []

        except Exception as e:
            logger.error(f"Failed to get instruments: {e}")
            return []

    # ==========================================
    # Option Chain
    # ==========================================

    def get_option_chain(self, symbol: str, expiry: str, **kwargs) -> Dict:
        """
        Get option chain for a symbol.

        Args:
            symbol: Underlying symbol
            expiry: Expiry date
            **kwargs: Additional parameters

        Returns:
            Dict: Option chain data
        """
        try:
            # Upstox doesn't provide a direct option chain API
            # This would require fetching instrument list and filtering
            logger.warning("Option chain requires instrument filtering")
            return {'calls': {}, 'puts': {}}

        except Exception as e:
            logger.error(f"Failed to get option chain: {e}")
            return {'calls': {}, 'puts': {}}

    # ==========================================
    # Helper Methods
    # ==========================================

    def _convert_to_broker_order(self, upstox_order) -> BrokerOrder:
        """Convert Upstox order to BrokerOrder."""
        return BrokerOrder(
            order_id=str(upstox_order.order_id),
            symbol=upstox_order.tradingsymbol,
            exchange=upstox_order.exchange,
            transaction_type=upstox_order.transaction_type,
            quantity=upstox_order.quantity,
            price=upstox_order.price,
            order_type=upstox_order.order_type,
            product_type=upstox_order.product,
            status=upstox_order.status,
            filled_quantity=upstox_order.filled_quantity,
            average_price=upstox_order.average_price,
            order_timestamp=upstox_order.order_timestamp,
            exchange_timestamp=upstox_order.exchange_timestamp,
            status_message=getattr(upstox_order, 'status_message', ''),
            tag=getattr(upstox_order, 'tag', ''),
            trigger_price=upstox_order.trigger_price,
            validity=upstox_order.validity
        )

    def _convert_to_broker_position(self, upstox_position) -> BrokerPosition:
        """Convert Upstox position to BrokerPosition."""
        return BrokerPosition(
            symbol=upstox_position.tradingsymbol,
            exchange=upstox_position.exchange,
            product_type=upstox_position.product,
            quantity=upstox_position.quantity,
            average_price=upstox_position.average_price,
            last_price=upstox_position.last_price,
            pnl=upstox_position.pnl,
            day_pnl=getattr(upstox_position, 'day_pnl', 0.0),
            unrealized_pnl=upstox_position.unrealised,
            realized_pnl=upstox_position.realised,
            value=upstox_position.value,
            multiplier=getattr(upstox_position, 'multiplier', 1)
        )

    def _convert_to_broker_holding(self, upstox_holding) -> BrokerHolding:
        """Convert Upstox holding to BrokerHolding."""
        return BrokerHolding(
            symbol=upstox_holding.tradingsymbol,
            exchange=upstox_holding.exchange,
            quantity=upstox_holding.quantity,
            average_price=upstox_holding.average_price,
            last_price=upstox_holding.last_price,
            pnl=upstox_holding.pnl,
            product_type='D'  # Delivery
        )

    def _convert_to_broker_quote(self, upstox_quote, symbol: str, exchange: str) -> BrokerQuote:
        """Convert Upstox quote to BrokerQuote."""
        ohlc = upstox_quote.get('ohlc', {})

        return BrokerQuote(
            symbol=symbol,
            exchange=exchange,
            last_price=upstox_quote.get('last_price', 0.0),
            volume=upstox_quote.get('volume', 0),
            open=ohlc.get('open', 0.0),
            high=ohlc.get('high', 0.0),
            low=ohlc.get('low', 0.0),
            close=ohlc.get('close', 0.0),
            bid_price=upstox_quote.get('depth', {}).get('buy', [{}])[0].get('price', 0.0),
            ask_price=upstox_quote.get('depth', {}).get('sell', [{}])[0].get('price', 0.0),
            bid_quantity=upstox_quote.get('depth', {}).get('buy', [{}])[0].get('quantity', 0),
            ask_quantity=upstox_quote.get('depth', {}).get('sell', [{}])[0].get('quantity', 0),
            timestamp=upstox_quote.get('timestamp'),
            oi=upstox_quote.get('oi', 0)
        )
