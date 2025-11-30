"""
Base Broker Interface

Abstract base class defining the interface that all broker implementations must follow.
This ensures a consistent API across different brokers.

Author: Bhavin Prajapati
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Optional, Union, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum


class OrderType(Enum):
    """Order types supported across brokers."""
    MARKET = "MARKET"
    LIMIT = "LIMIT"
    SL = "SL"  # Stop Loss
    SL_M = "SL-M"  # Stop Loss Market


class TransactionType(Enum):
    """Transaction types."""
    BUY = "BUY"
    SELL = "SELL"


class ProductType(Enum):
    """Product types."""
    MIS = "MIS"  # Intraday
    CNC = "CNC"  # Cash and Carry
    NRML = "NRML"  # Normal (Carry Forward)


class OrderStatus(Enum):
    """Order status."""
    PENDING = "PENDING"
    OPEN = "OPEN"
    COMPLETE = "COMPLETE"
    CANCELLED = "CANCELLED"
    REJECTED = "REJECTED"


class Exchange(Enum):
    """Exchanges."""
    NSE = "NSE"
    BSE = "BSE"
    NFO = "NFO"  # NSE Futures & Options
    BFO = "BFO"  # BSE Futures & Options
    MCX = "MCX"
    CDS = "CDS"


@dataclass
class BrokerOrder:
    """Standardized order object across brokers."""
    order_id: str
    symbol: str
    exchange: str
    transaction_type: str  # BUY/SELL
    quantity: int
    price: float
    order_type: str  # MARKET/LIMIT/SL/SL-M
    product_type: str  # MIS/CNC/NRML
    status: str
    filled_quantity: int = 0
    average_price: float = 0.0
    order_timestamp: Optional[datetime] = None
    exchange_timestamp: Optional[datetime] = None
    status_message: Optional[str] = None
    tag: Optional[str] = None
    trigger_price: float = 0.0
    validity: str = "DAY"


@dataclass
class BrokerPosition:
    """Standardized position object across brokers."""
    symbol: str
    exchange: str
    product_type: str
    quantity: int
    average_price: float
    last_price: float
    pnl: float
    day_pnl: float = 0.0
    unrealized_pnl: float = 0.0
    realized_pnl: float = 0.0
    value: float = 0.0
    multiplier: int = 1


@dataclass
class BrokerQuote:
    """Standardized quote/LTP object across brokers."""
    symbol: str
    exchange: str
    last_price: float
    volume: int = 0
    open: float = 0.0
    high: float = 0.0
    low: float = 0.0
    close: float = 0.0
    bid_price: float = 0.0
    ask_price: float = 0.0
    bid_quantity: int = 0
    ask_quantity: int = 0
    timestamp: Optional[datetime] = None
    oi: int = 0  # Open Interest (for derivatives)


@dataclass
class BrokerHolding:
    """Standardized holdings object."""
    symbol: str
    exchange: str
    quantity: int
    average_price: float
    last_price: float
    pnl: float
    product_type: str = "CNC"


@dataclass
class BrokerMargin:
    """Standardized margin object."""
    available_cash: float
    used_margin: float
    total_margin: float
    collateral: float = 0.0


class BaseBroker(ABC):
    """
    Abstract base class for all broker implementations.

    All broker-specific implementations must inherit from this class
    and implement all abstract methods.
    """

    def __init__(self, api_key: str, api_secret: str, access_token: Optional[str] = None):
        """
        Initialize broker connection.

        Args:
            api_key: API key for the broker
            api_secret: API secret for the broker
            access_token: Access token (if already authenticated)
        """
        self.api_key = api_key
        self.api_secret = api_secret
        self.access_token = access_token
        self._authenticated = False

    @property
    def broker_name(self) -> str:
        """Return the broker name."""
        return self.__class__.__name__.replace("Broker", "")

    @property
    def is_authenticated(self) -> bool:
        """Check if authenticated with broker."""
        return self._authenticated

    # ==========================================
    # Authentication Methods
    # ==========================================

    @abstractmethod
    def login(self, **kwargs) -> bool:
        """
        Login to the broker.

        Args:
            **kwargs: Broker-specific login parameters

        Returns:
            bool: True if login successful
        """
        pass

    @abstractmethod
    def get_access_token(self, request_token: str) -> str:
        """
        Generate access token from request token.

        Args:
            request_token: Request token from broker login flow

        Returns:
            str: Access token
        """
        pass

    @abstractmethod
    def set_access_token(self, access_token: str) -> None:
        """
        Set access token for API calls.

        Args:
            access_token: Valid access token
        """
        pass

    # ==========================================
    # Order Management
    # ==========================================

    @abstractmethod
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
        Place an order.

        Args:
            symbol: Trading symbol
            exchange: Exchange (NSE/BSE/NFO/BFO)
            transaction_type: BUY or SELL
            quantity: Order quantity
            order_type: MARKET/LIMIT/SL/SL-M
            price: Limit price (for LIMIT orders)
            product_type: MIS/CNC/NRML
            trigger_price: Trigger price (for SL orders)
            validity: Order validity (DAY/IOC)
            **kwargs: Broker-specific parameters

        Returns:
            str: Order ID
        """
        pass

    @abstractmethod
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
            **kwargs: Broker-specific parameters

        Returns:
            str: Order ID
        """
        pass

    @abstractmethod
    def cancel_order(self, order_id: str, **kwargs) -> bool:
        """
        Cancel an order.

        Args:
            order_id: Order ID to cancel
            **kwargs: Broker-specific parameters

        Returns:
            bool: True if cancelled successfully
        """
        pass

    @abstractmethod
    def get_orders(self) -> List[BrokerOrder]:
        """
        Get all orders for the day.

        Returns:
            List[BrokerOrder]: List of orders
        """
        pass

    @abstractmethod
    def get_order_history(self, order_id: str) -> List[BrokerOrder]:
        """
        Get order history/status updates.

        Args:
            order_id: Order ID

        Returns:
            List[BrokerOrder]: Order status history
        """
        pass

    # ==========================================
    # Position Management
    # ==========================================

    @abstractmethod
    def get_positions(self) -> List[BrokerPosition]:
        """
        Get current positions.

        Returns:
            List[BrokerPosition]: List of positions
        """
        pass

    @abstractmethod
    def get_holdings(self) -> List[BrokerHolding]:
        """
        Get holdings (long-term investments).

        Returns:
            List[BrokerHolding]: List of holdings
        """
        pass

    @abstractmethod
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
            **kwargs: Broker-specific parameters

        Returns:
            str: Order ID for square-off order
        """
        pass

    # ==========================================
    # Market Data
    # ==========================================

    @abstractmethod
    def get_quote(self, symbol: str, exchange: str) -> BrokerQuote:
        """
        Get quote/LTP for a symbol.

        Args:
            symbol: Trading symbol
            exchange: Exchange

        Returns:
            BrokerQuote: Quote data
        """
        pass

    @abstractmethod
    def get_ltp(self, symbol: str, exchange: str) -> float:
        """
        Get Last Traded Price for a symbol.

        Args:
            symbol: Trading symbol
            exchange: Exchange

        Returns:
            float: Last traded price
        """
        pass

    @abstractmethod
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
            interval: Interval (minute/day/week/month)
            **kwargs: Broker-specific parameters

        Returns:
            List[Dict]: Historical data
        """
        pass

    # ==========================================
    # Account Information
    # ==========================================

    @abstractmethod
    def get_margins(self) -> BrokerMargin:
        """
        Get margin information.

        Returns:
            BrokerMargin: Margin details
        """
        pass

    @abstractmethod
    def get_profile(self) -> Dict:
        """
        Get user profile information.

        Returns:
            Dict: Profile information
        """
        pass

    # ==========================================
    # Instrument/Symbol Search
    # ==========================================

    @abstractmethod
    def search_instruments(self, query: str, exchange: Optional[str] = None) -> List[Dict]:
        """
        Search for instruments.

        Args:
            query: Search query
            exchange: Filter by exchange (optional)

        Returns:
            List[Dict]: List of matching instruments
        """
        pass

    @abstractmethod
    def get_instruments(self, exchange: str) -> List[Dict]:
        """
        Get all instruments for an exchange.

        Args:
            exchange: Exchange name

        Returns:
            List[Dict]: List of instruments
        """
        pass

    # ==========================================
    # Option Chain & Greeks
    # ==========================================

    @abstractmethod
    def get_option_chain(
        self,
        symbol: str,
        expiry: str,
        **kwargs
    ) -> Dict:
        """
        Get option chain for a symbol.

        Args:
            symbol: Underlying symbol
            expiry: Expiry date
            **kwargs: Broker-specific parameters

        Returns:
            Dict: Option chain data
        """
        pass

    # ==========================================
    # Utility Methods
    # ==========================================

    def format_symbol(self, symbol: str, exchange: str, **kwargs) -> str:
        """
        Format symbol according to broker's convention.

        Args:
            symbol: Trading symbol
            exchange: Exchange
            **kwargs: Additional parameters

        Returns:
            str: Formatted symbol
        """
        # Default implementation - override in broker-specific class if needed
        return symbol

    def get_tradable_instruments(self, segment: str = "equity") -> List[str]:
        """
        Get list of tradable instruments.

        Args:
            segment: Market segment (equity/fno/currency/commodity)

        Returns:
            List[str]: List of symbols
        """
        # Default implementation - override in broker-specific class
        return []

    def validate_order_params(
        self,
        symbol: str,
        quantity: int,
        price: float = 0.0,
        **kwargs
    ) -> Tuple[bool, Optional[str]]:
        """
        Validate order parameters before placing order.

        Args:
            symbol: Trading symbol
            quantity: Order quantity
            price: Order price
            **kwargs: Additional parameters

        Returns:
            Tuple[bool, Optional[str]]: (is_valid, error_message)
        """
        # Basic validation - override for broker-specific rules
        if quantity <= 0:
            return False, "Quantity must be positive"

        if price < 0:
            return False, "Price cannot be negative"

        return True, None

    def __repr__(self) -> str:
        """String representation."""
        return f"{self.broker_name}Broker(authenticated={self.is_authenticated})"
