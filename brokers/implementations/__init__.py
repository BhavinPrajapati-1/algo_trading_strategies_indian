"""
Broker Implementations

Concrete implementations of the BaseBroker interface for various brokers.

Available Brokers:
- Zerodha (Kite Connect)
- Upstox
- Kotak Securities
- Angel One
- Fyers
- AliceBlue

Author: Bhavin Prajapati
"""

__all__ = []

# Import available implementations
try:
    from brokers.implementations.zerodha import ZerodhaBroker
    __all__.append('ZerodhaBroker')
except ImportError:
    pass

try:
    from brokers.implementations.upstox import UpstoxBroker
    __all__.append('UpstoxBroker')
except ImportError:
    pass

try:
    from brokers.implementations.kotak import KotakBroker
    __all__.append('KotakBroker')
except ImportError:
    pass

try:
    from brokers.implementations.angelone import AngelOneBroker
    __all__.append('AngelOneBroker')
except ImportError:
    pass

try:
    from brokers.implementations.fyers import FyersBroker
    __all__.append('FyersBroker')
except ImportError:
    pass

try:
    from brokers.implementations.aliceblue import AliceBlueBroker
    __all__.append('AliceBlueBroker')
except ImportError:
    pass
