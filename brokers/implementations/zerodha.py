"""
Zerodha Broker Implementation

Implements the BaseBroker interface for Zerodha's Kite Connect API.

Author: Bhavin Prajapati
"""

from typing import List, Dict, Optional
from datetime import datetime
import logging

from kiteconnect import KiteConnect
from kiteconnect.exceptions import KiteException

from brokers.base import (
    BaseBroker,
    BrokerOrder,
    BrokerPosition,
    BrokerQuote,
    BrokerHolding,
    BrokerMargin,
    OrderType,
    TransactionType,
    ProductType,
    Exchange
)


logger = logging.getLogger(__name__)


class ZerodhaBroker(BaseBroker):
    """
    Zerodha broker implementation using Kite Connect API.

    Documentation: https://kite.trade/docs/connect/v3/
    """

    def __init__(self, api_key: str, api_secret: str, access_token: Optional[str] = None):
        """
        Initialize Zerodha broker.

        Args:
            api_key: Zerodha API key
            api_secret: Zerodha API secret
            access_token: Access token (if already authenticated)
        """
        super().__init__(api_key, api_secret, access_token)

        self.kite = KiteConnect(api_key=api_key)

        if access_token:
            self.set_access_token(access_token)

    # ==========================================
    # Authentication
    # ==========================================

    def login(self, request_token: Optional[str] = None, **kwargs) -> bool:
        """
        Login to Zerodha (generates access token from request token).

        Args:
            request_token: Request token from Zerodha login flow
            **kwargs: Additional parameters

        Returns:
            bool: True if login successful
        """
        if not request_token:
            # Generate login URL
            login_url = self.kite.login_url()
            logger.info(f"Please login at: {login_url}")
            return False

        try:
            data = self.kite.generate_session(request_token, api_secret=self.api_secret)
            self.access_token = data["access_token"]
            self.kite.set_access_token(self.access_token)
            self._authenticated = True

            logger.info("Successfully authenticated with Zerodha")
            return True

        except KiteException as e:
            logger.error(f"Authentication failed: {e}")
            return False

    def get_access_token(self, request_token: str) -> str:
        """
        Generate access token from request token.

        Args:
            request_token: Request token from login flow

        Returns:
            str: Access token
        """
        data = self.kite.generate_session(request_token, api_secret=self.api_secret)
        return data["access_token"]

    def set_access_token(self, access_token: str) -> None:
        """
        Set access token for API calls.

        Args:
            access_token: Valid access token
        """
        self.access_token = access_token
        self.kite.set_access_token(access_token)
        self._authenticated = True

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
        product_type: str = "MIS",
        trigger_price: float = 0.0,
        validity: str = "DAY",
        **kwargs
    ) -> str:
        """
        Place an order on Zerodha.

        Args:
            symbol: Trading symbol
            exchange: Exchange (NSE/BSE/NFO/BFO/MCX/CDS)
            transaction_type: BUY or SELL
            quantity: Order quantity
            order_type: MARKET/LIMIT/SL/SL-M
            price: Limit price
            product_type: MIS/CNC/NRML
            trigger_price: Trigger price for SL orders
            validity: DAY/IOC
            **kwargs: tag, disclosed_quantity, etc.

        Returns:
            str: Order ID
        """
        try:
            order_params = {
                "tradingsymbol": symbol,
                "exchange": exchange,
                "transaction_type": transaction_type,
                "quantity": quantity,
                "order_type": order_type,
                "product": product_type,
                "validity": validity
            }

            if order_type in ["LIMIT", "SL"]:
                order_params["price"] = price

            if order_type in ["SL", "SL-M"]:
                order_params["trigger_price"] = trigger_price

            # Add any additional parameters
            order_params.update(kwargs)

            order_id = self.kite.place_order(**order_params)

            logger.info(f"Order placed: {order_id} - {transaction_type} {quantity} {symbol}")
            return str(order_id)

        except KiteException as e:
            logger.error(f"Order placement failed: {e}")
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
            modify_params = {}

            if quantity is not None:
                modify_params["quantity"] = quantity
            if price is not None:
                modify_params["price"] = price
            if order_type is not None:
                modify_params["order_type"] = order_type
            if trigger_price is not None:
                modify_params["trigger_price"] = trigger_price

            modify_params.update(kwargs)

            result = self.kite.modify_order(order_id=order_id, **modify_params)

            logger.info(f"Order modified: {order_id}")
            return str(order_id)

        except KiteException as e:
            logger.error(f"Order modification failed: {e}")
            raise

    def cancel_order(self, order_id: str, **kwargs) -> bool:
        """
        Cancel an order.

        Args:
            order_id: Order ID to cancel
            **kwargs: variety parameter

        Returns:
            bool: True if cancelled successfully
        """
        try:
            self.kite.cancel_order(order_id=order_id, **kwargs)
            logger.info(f"Order cancelled: {order_id}")
            return True

        except KiteException as e:
            logger.error(f"Order cancellation failed: {e}")
            return False

    def get_orders(self) -> List[BrokerOrder]:
        """
        Get all orders for the day.

        Returns:
            List[BrokerOrder]: List of orders
        """
        try:
            orders = self.kite.orders()
            return [self._convert_to_broker_order(order) for order in orders]

        except KiteException as e:
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
            history = self.kite.order_history(order_id=order_id)
            return [self._convert_to_broker_order(order) for order in history]

        except KiteException as e:
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
            positions_data = self.kite.positions()
            positions = []

            # Zerodha returns both 'day' and 'net' positions
            for pos in positions_data.get('net', []):
                if pos['quantity'] != 0:  # Only include active positions
                    positions.append(self._convert_to_broker_position(pos))

            return positions

        except KiteException as e:
            logger.error(f"Failed to get positions: {e}")
            return []

    def get_holdings(self) -> List[BrokerHolding]:
        """
        Get holdings (long-term investments).

        Returns:
            List[BrokerHolding]: List of holdings
        """
        try:
            holdings = self.kite.holdings()
            return [self._convert_to_broker_holding(holding) for holding in holdings]

        except KiteException as e:
            logger.error(f"Failed to get holdings: {e}")
            return []

    def square_off_position(
        self,
        symbol: str,
        exchange: str,
        product_type: str = "MIS",
        **kwargs
    ) -> str:
        """
        Square off (exit) a position.

        Args:
            symbol: Trading symbol
            exchange: Exchange
            product_type: Product type
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
            instrument_key = f"{exchange}:{symbol}"
            quotes = self.kite.quote([instrument_key])
            quote_data = quotes.get(instrument_key, {})

            return self._convert_to_broker_quote(quote_data, symbol, exchange)

        except KiteException as e:
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
            instrument_key = f"{exchange}:{symbol}"
            ltp_data = self.kite.ltp([instrument_key])
            return ltp_data[instrument_key]["last_price"]

        except KiteException as e:
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
            interval: minute/day/3minute/5minute/10minute/15minute/30minute/60minute
            **kwargs: continuous, oi

        Returns:
            List[Dict]: Historical data
        """
        try:
            # Get instrument token
            instruments = self.kite.instruments(exchange)
            instrument = next((i for i in instruments if i['tradingsymbol'] == symbol), None)

            if not instrument:
                raise ValueError(f"Instrument not found: {symbol}")

            instrument_token = instrument['instrument_token']

            historical_data = self.kite.historical_data(
                instrument_token=instrument_token,
                from_date=from_date,
                to_date=to_date,
                interval=interval,
                **kwargs
            )

            return historical_data

        except KiteException as e:
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
            margins = self.kite.margins()
            equity = margins.get('equity', {})

            return BrokerMargin(
                available_cash=equity.get('available', {}).get('cash', 0.0),
                used_margin=equity.get('utilised', {}).get('debits', 0.0),
                total_margin=equity.get('net', 0.0),
                collateral=equity.get('available', {}).get('collateral', 0.0)
            )

        except KiteException as e:
            logger.error(f"Failed to get margins: {e}")
            raise

    def get_profile(self) -> Dict:
        """
        Get user profile information.

        Returns:
            Dict: Profile information
        """
        try:
            return self.kite.profile()

        except KiteException as e:
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
            if exchange:
                instruments = self.kite.instruments(exchange)
            else:
                # Search across all exchanges
                instruments = []
                for exch in ['NSE', 'BSE', 'NFO', 'BFO', 'MCX', 'CDS']:
                    try:
                        instruments.extend(self.kite.instruments(exch))
                    except:
                        pass

            # Filter by query
            query_lower = query.lower()
            matches = [
                inst for inst in instruments
                if query_lower in inst['tradingsymbol'].lower() or
                   query_lower in inst['name'].lower()
            ]

            return matches[:50]  # Limit results

        except KiteException as e:
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
            return self.kite.instruments(exchange)

        except KiteException as e:
            logger.error(f"Failed to get instruments: {e}")
            return []

    # ==========================================
    # Option Chain & Greeks
    # ==========================================

    def get_option_chain(self, symbol: str, expiry: str, **kwargs) -> Dict:
        """
        Get option chain for a symbol.

        Note: Zerodha doesn't provide a direct option chain API.
        This method fetches all option instruments and filters by underlying and expiry.

        Args:
            symbol: Underlying symbol
            expiry: Expiry date (YYYY-MM-DD)
            **kwargs: Additional parameters

        Returns:
            Dict: Option chain data
        """
        try:
            # Get all NFO instruments
            instruments = self.kite.instruments('NFO')

            # Filter by underlying and expiry
            options = [
                inst for inst in instruments
                if inst['name'] == symbol and inst['expiry'].strftime('%Y-%m-%d') == expiry
            ]

            # Organize by strike
            option_chain = {'calls': {}, 'puts': {}}

            for opt in options:
                strike = opt['strike']

                if opt['instrument_type'] == 'CE':
                    option_chain['calls'][strike] = opt
                elif opt['instrument_type'] == 'PE':
                    option_chain['puts'][strike] = opt

            return option_chain

        except KiteException as e:
            logger.error(f"Failed to get option chain: {e}")
            return {'calls': {}, 'puts': {}}

    # ==========================================
    # Helper Methods
    # ==========================================

    def _convert_to_broker_order(self, kite_order: Dict) -> BrokerOrder:
        """Convert Kite order to BrokerOrder."""
        return BrokerOrder(
            order_id=kite_order.get('order_id', ''),
            symbol=kite_order.get('tradingsymbol', ''),
            exchange=kite_order.get('exchange', ''),
            transaction_type=kite_order.get('transaction_type', ''),
            quantity=kite_order.get('quantity', 0),
            price=kite_order.get('price', 0.0),
            order_type=kite_order.get('order_type', ''),
            product_type=kite_order.get('product', ''),
            status=kite_order.get('status', ''),
            filled_quantity=kite_order.get('filled_quantity', 0),
            average_price=kite_order.get('average_price', 0.0),
            order_timestamp=kite_order.get('order_timestamp'),
            exchange_timestamp=kite_order.get('exchange_timestamp'),
            status_message=kite_order.get('status_message'),
            tag=kite_order.get('tag'),
            trigger_price=kite_order.get('trigger_price', 0.0),
            validity=kite_order.get('validity', 'DAY')
        )

    def _convert_to_broker_position(self, kite_position: Dict) -> BrokerPosition:
        """Convert Kite position to BrokerPosition."""
        return BrokerPosition(
            symbol=kite_position.get('tradingsymbol', ''),
            exchange=kite_position.get('exchange', ''),
            product_type=kite_position.get('product', ''),
            quantity=kite_position.get('quantity', 0),
            average_price=kite_position.get('average_price', 0.0),
            last_price=kite_position.get('last_price', 0.0),
            pnl=kite_position.get('pnl', 0.0),
            day_pnl=kite_position.get('day_pnl', 0.0),
            unrealized_pnl=kite_position.get('unrealised', 0.0),
            realized_pnl=kite_position.get('realised', 0.0),
            value=kite_position.get('value', 0.0),
            multiplier=kite_position.get('multiplier', 1)
        )

    def _convert_to_broker_holding(self, kite_holding: Dict) -> BrokerHolding:
        """Convert Kite holding to BrokerHolding."""
        return BrokerHolding(
            symbol=kite_holding.get('tradingsymbol', ''),
            exchange=kite_holding.get('exchange', ''),
            quantity=kite_holding.get('quantity', 0),
            average_price=kite_holding.get('average_price', 0.0),
            last_price=kite_holding.get('last_price', 0.0),
            pnl=kite_holding.get('pnl', 0.0),
            product_type='CNC'
        )

    def _convert_to_broker_quote(self, kite_quote: Dict, symbol: str, exchange: str) -> BrokerQuote:
        """Convert Kite quote to BrokerQuote."""
        ohlc = kite_quote.get('ohlc', {})
        depth = kite_quote.get('depth', {})
        buy = depth.get('buy', [{}])[0] if depth.get('buy') else {}
        sell = depth.get('sell', [{}])[0] if depth.get('sell') else {}

        return BrokerQuote(
            symbol=symbol,
            exchange=exchange,
            last_price=kite_quote.get('last_price', 0.0),
            volume=kite_quote.get('volume', 0),
            open=ohlc.get('open', 0.0),
            high=ohlc.get('high', 0.0),
            low=ohlc.get('low', 0.0),
            close=ohlc.get('close', 0.0),
            bid_price=buy.get('price', 0.0),
            ask_price=sell.get('price', 0.0),
            bid_quantity=buy.get('quantity', 0),
            ask_quantity=sell.get('quantity', 0),
            timestamp=kite_quote.get('timestamp'),
            oi=kite_quote.get('oi', 0)
        )
