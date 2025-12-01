"""
Broker Configuration Management

Handles loading and managing broker configurations from environment variables
and configuration files.

Author: Bhavin Prajapati
"""

import os
from typing import Dict, Optional
from dataclasses import dataclass, field
from pathlib import Path
import json
import yaml
from dotenv import load_dotenv


@dataclass
class BrokerConfig:
    """Configuration for a broker."""
    broker_name: str
    api_key: str
    api_secret: str
    access_token: Optional[str] = None

    # Additional broker-specific settings
    user_id: Optional[str] = None
    password: Optional[str] = None
    totp_secret: Optional[str] = None
    pin: Optional[str] = None

    # API endpoints (for brokers with custom endpoints)
    api_endpoint: Optional[str] = None
    login_endpoint: Optional[str] = None

    # Proxy settings
    proxy_url: Optional[str] = None

    # Timeout settings
    timeout: int = 7

    # Additional settings as dict
    extra_settings: Dict = field(default_factory=dict)

    @classmethod
    def from_env(cls, broker_name: str, env_prefix: Optional[str] = None) -> 'BrokerConfig':
        """
        Load broker configuration from environment variables.

        Args:
            broker_name: Name of the broker (zerodha, upstox, kotak, etc.)
            env_prefix: Custom environment variable prefix (default: broker_name.upper())

        Returns:
            BrokerConfig: Broker configuration

        Environment variables expected:
            {PREFIX}_API_KEY
            {PREFIX}_API_SECRET
            {PREFIX}_ACCESS_TOKEN (optional)
            {PREFIX}_USER_ID (optional)
            {PREFIX}_PASSWORD (optional)
            {PREFIX}_TOTP_SECRET (optional)
            {PREFIX}_PIN (optional)
        """
        load_dotenv()

        prefix = env_prefix or broker_name.upper()

        return cls(
            broker_name=broker_name.lower(),
            api_key=os.getenv(f'{prefix}_API_KEY', ''),
            api_secret=os.getenv(f'{prefix}_API_SECRET', ''),
            access_token=os.getenv(f'{prefix}_ACCESS_TOKEN'),
            user_id=os.getenv(f'{prefix}_USER_ID'),
            password=os.getenv(f'{prefix}_PASSWORD'),
            totp_secret=os.getenv(f'{prefix}_TOTP_SECRET'),
            pin=os.getenv(f'{prefix}_PIN'),
            api_endpoint=os.getenv(f'{prefix}_API_ENDPOINT'),
            login_endpoint=os.getenv(f'{prefix}_LOGIN_ENDPOINT'),
            proxy_url=os.getenv(f'{prefix}_PROXY_URL'),
            timeout=int(os.getenv(f'{prefix}_TIMEOUT', '7'))
        )

    @classmethod
    def from_file(cls, config_file: str, broker_name: str) -> 'BrokerConfig':
        """
        Load broker configuration from a file.

        Args:
            config_file: Path to configuration file (JSON or YAML)
            broker_name: Name of the broker

        Returns:
            BrokerConfig: Broker configuration
        """
        config_path = Path(config_file)

        if not config_path.exists():
            raise FileNotFoundError(f"Configuration file not found: {config_file}")

        # Load based on file extension
        if config_path.suffix in ['.yaml', '.yml']:
            with open(config_path, 'r') as f:
                config_data = yaml.safe_load(f)
        elif config_path.suffix == '.json':
            with open(config_path, 'r') as f:
                config_data = json.load(f)
        else:
            raise ValueError(f"Unsupported configuration file format: {config_path.suffix}")

        # Get broker-specific config
        broker_config = config_data.get('brokers', {}).get(broker_name, {})

        if not broker_config:
            raise ValueError(f"No configuration found for broker: {broker_name}")

        return cls(
            broker_name=broker_name,
            api_key=broker_config.get('api_key', ''),
            api_secret=broker_config.get('api_secret', ''),
            access_token=broker_config.get('access_token'),
            user_id=broker_config.get('user_id'),
            password=broker_config.get('password'),
            totp_secret=broker_config.get('totp_secret'),
            pin=broker_config.get('pin'),
            api_endpoint=broker_config.get('api_endpoint'),
            login_endpoint=broker_config.get('login_endpoint'),
            proxy_url=broker_config.get('proxy_url'),
            timeout=broker_config.get('timeout', 7),
            extra_settings=broker_config.get('extra_settings', {})
        )

    def validate(self) -> tuple[bool, Optional[str]]:
        """
        Validate configuration.

        Returns:
            Tuple[bool, Optional[str]]: (is_valid, error_message)
        """
        if not self.api_key:
            return False, f"{self.broker_name}: API key is required"

        if not self.api_secret:
            return False, f"{self.broker_name}: API secret is required"

        return True, None

    def to_dict(self) -> Dict:
        """Convert configuration to dictionary."""
        return {
            'broker_name': self.broker_name,
            'api_key': self.api_key[:10] + '...' if self.api_key else '',  # Masked
            'api_secret': '***masked***',  # Never expose
            'access_token': self.access_token[:20] + '...' if self.access_token else None,
            'user_id': self.user_id,
            'api_endpoint': self.api_endpoint,
            'timeout': self.timeout
        }

    def __repr__(self) -> str:
        """String representation (masks sensitive data)."""
        return f"BrokerConfig(broker={self.broker_name}, api_key={'*' * 10})"


class BrokerConfigManager:
    """
    Manage configurations for multiple brokers.
    """

    def __init__(self, config_file: Optional[str] = None):
        """
        Initialize configuration manager.

        Args:
            config_file: Path to configuration file (optional)
        """
        self.config_file = config_file
        self.configs: Dict[str, BrokerConfig] = {}

    def load_from_file(self, config_file: Optional[str] = None) -> None:
        """
        Load all broker configurations from file.

        Args:
            config_file: Path to configuration file
        """
        file_path = config_file or self.config_file

        if not file_path:
            raise ValueError("No configuration file specified")

        config_path = Path(file_path)

        if not config_path.exists():
            raise FileNotFoundError(f"Configuration file not found: {file_path}")

        # Load configuration
        if config_path.suffix in ['.yaml', '.yml']:
            with open(config_path, 'r') as f:
                config_data = yaml.safe_load(f)
        elif config_path.suffix == '.json':
            with open(config_path, 'r') as f:
                config_data = json.load(f)
        else:
            raise ValueError(f"Unsupported file format: {config_path.suffix}")

        # Load each broker configuration
        brokers = config_data.get('brokers', {})

        for broker_name in brokers:
            self.configs[broker_name] = BrokerConfig.from_file(file_path, broker_name)

    def load_from_env(self, broker_names: list[str]) -> None:
        """
        Load broker configurations from environment variables.

        Args:
            broker_names: List of broker names to load
        """
        for broker_name in broker_names:
            self.configs[broker_name] = BrokerConfig.from_env(broker_name)

    def get_config(self, broker_name: str) -> Optional[BrokerConfig]:
        """
        Get configuration for a specific broker.

        Args:
            broker_name: Broker name

        Returns:
            BrokerConfig: Broker configuration or None
        """
        return self.configs.get(broker_name.lower())

    def add_config(self, config: BrokerConfig) -> None:
        """
        Add a broker configuration.

        Args:
            config: BrokerConfig instance
        """
        self.configs[config.broker_name.lower()] = config

    def validate_all(self) -> Dict[str, tuple[bool, Optional[str]]]:
        """
        Validate all configurations.

        Returns:
            Dict: Validation results for each broker
        """
        results = {}

        for broker_name, config in self.configs.items():
            results[broker_name] = config.validate()

        return results

    def list_brokers(self) -> list[str]:
        """
        Get list of configured brokers.

        Returns:
            List[str]: List of broker names
        """
        return list(self.configs.keys())

    def __repr__(self) -> str:
        """String representation."""
        return f"BrokerConfigManager(brokers={self.list_brokers()})"
