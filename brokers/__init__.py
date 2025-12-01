"""
Multi-Broker Support Module

This module provides a unified interface for interacting with multiple brokers.
Currently supported brokers:
- Zerodha (Kite Connect)
- Upstox
- Kotak Securities
- Angel One
- Fyers
- AliceBlue

Author: Bhavin Prajapati
"""

from brokers.base import BaseBroker, BrokerOrder, BrokerPosition, BrokerQuote
from brokers.factory import BrokerFactory
from brokers.config import BrokerConfig

__all__ = [
    'BaseBroker',
    'BrokerOrder',
    'BrokerPosition',
    'BrokerQuote',
    'BrokerFactory',
    'BrokerConfig'
]

__version__ = '1.0.0'
