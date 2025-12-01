"""
Broker Factory

Factory pattern for creating broker instances.
Automatically instantiates the correct broker implementation based on broker name.

Author: Bhavin Prajapati
"""

from typing import Optional, Dict, Type
import logging

from brokers.base import BaseBroker
from brokers.config import BrokerConfig


logger = logging.getLogger(__name__)


class BrokerFactory:
    """
    Factory for creating broker instances.

    Usage:
        broker = BrokerFactory.create('zerodha', config)
        broker = BrokerFactory.create_from_env('upstox')
    """

    # Registry of available broker implementations
    _brokers: Dict[str, Type[BaseBroker]] = {}

    @classmethod
    def register_broker(cls, broker_name: str, broker_class: Type[BaseBroker]) -> None:
        """
        Register a broker implementation.

        Args:
            broker_name: Name of the broker (e.g., 'zerodha', 'upstox')
            broker_class: Broker class (must inherit from BaseBroker)
        """
        if not issubclass(broker_class, BaseBroker):
            raise TypeError(f"{broker_class} must inherit from BaseBroker")

        cls._brokers[broker_name.lower()] = broker_class
        logger.info(f"Registered broker: {broker_name}")

    @classmethod
    def create(
        cls,
        broker_name: str,
        config: Optional[BrokerConfig] = None,
        api_key: Optional[str] = None,
        api_secret: Optional[str] = None,
        access_token: Optional[str] = None,
        **kwargs
    ) -> BaseBroker:
        """
        Create a broker instance.

        Args:
            broker_name: Name of the broker
            config: BrokerConfig instance (optional if api_key/secret provided)
            api_key: API key (alternative to config)
            api_secret: API secret (alternative to config)
            access_token: Access token (optional)
            **kwargs: Additional broker-specific parameters

        Returns:
            BaseBroker: Broker instance

        Raises:
            ValueError: If broker not found or invalid configuration
        """
        broker_name_lower = broker_name.lower()

        if broker_name_lower not in cls._brokers:
            available = ', '.join(cls._brokers.keys())
            raise ValueError(
                f"Broker '{broker_name}' not found. "
                f"Available brokers: {available}"
            )

        # Get broker class
        broker_class = cls._brokers[broker_name_lower]

        # Determine credentials
        if config:
            api_key = config.api_key
            api_secret = config.api_secret
            access_token = config.access_token or access_token

            # Pass additional config settings to kwargs
            if config.extra_settings:
                kwargs.update(config.extra_settings)

        elif not (api_key and api_secret):
            raise ValueError("Either 'config' or 'api_key' and 'api_secret' must be provided")

        # Create broker instance
        try:
            broker = broker_class(
                api_key=api_key,
                api_secret=api_secret,
                access_token=access_token,
                **kwargs
            )

            logger.info(f"Created {broker_name} broker instance")
            return broker

        except Exception as e:
            logger.error(f"Error creating {broker_name} broker: {e}")
            raise

    @classmethod
    def create_from_env(cls, broker_name: str, env_prefix: Optional[str] = None) -> BaseBroker:
        """
        Create broker instance from environment variables.

        Args:
            broker_name: Name of the broker
            env_prefix: Custom environment variable prefix

        Returns:
            BaseBroker: Broker instance
        """
        config = BrokerConfig.from_env(broker_name, env_prefix)

        # Validate configuration
        is_valid, error_msg = config.validate()
        if not is_valid:
            raise ValueError(f"Invalid broker configuration: {error_msg}")

        return cls.create(broker_name, config=config)

    @classmethod
    def create_from_file(
        cls,
        broker_name: str,
        config_file: str
    ) -> BaseBroker:
        """
        Create broker instance from configuration file.

        Args:
            broker_name: Name of the broker
            config_file: Path to configuration file

        Returns:
            BaseBroker: Broker instance
        """
        config = BrokerConfig.from_file(config_file, broker_name)

        # Validate configuration
        is_valid, error_msg = config.validate()
        if not is_valid:
            raise ValueError(f"Invalid broker configuration: {error_msg}")

        return cls.create(broker_name, config=config)

    @classmethod
    def list_available_brokers(cls) -> list[str]:
        """
        Get list of registered/available brokers.

        Returns:
            List[str]: List of broker names
        """
        return list(cls._brokers.keys())

    @classmethod
    def is_broker_available(cls, broker_name: str) -> bool:
        """
        Check if a broker is available.

        Args:
            broker_name: Broker name

        Returns:
            bool: True if broker is registered
        """
        return broker_name.lower() in cls._brokers


# Auto-register brokers when they are imported
def _auto_register_brokers():
    """Auto-register all available broker implementations."""
    try:
        from brokers.implementations.zerodha import ZerodhaBroker
        BrokerFactory.register_broker('zerodha', ZerodhaBroker)
    except ImportError:
        logger.debug("Zerodha broker not available")

    try:
        from brokers.implementations.upstox import UpstoxBroker
        BrokerFactory.register_broker('upstox', UpstoxBroker)
    except ImportError:
        logger.debug("Upstox broker not available")

    try:
        from brokers.implementations.kotak import KotakBroker
        BrokerFactory.register_broker('kotak', KotakBroker)
        BrokerFactory.register_broker('kotaksecurities', KotakBroker)
    except ImportError:
        logger.debug("Kotak Securities broker not available")

    try:
        from brokers.implementations.angelone import AngelOneBroker
        BrokerFactory.register_broker('angelone', AngelOneBroker)
        BrokerFactory.register_broker('angel', AngelOneBroker)
    except ImportError:
        logger.debug("Angel One broker not available")

    try:
        from brokers.implementations.fyers import FyersBroker
        BrokerFactory.register_broker('fyers', FyersBroker)
    except ImportError:
        logger.debug("Fyers broker not available")

    try:
        from brokers.implementations.aliceblue import AliceBlueBroker
        BrokerFactory.register_broker('aliceblue', AliceBlueBroker)
        BrokerFactory.register_broker('alice', AliceBlueBroker)
    except ImportError:
        logger.debug("AliceBlue broker not available")


# Auto-register on module import
_auto_register_brokers()
