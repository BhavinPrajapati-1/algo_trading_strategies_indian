"""
Trading Strategies Module

Broker-agnostic trading strategies that work with any broker.

Available Strategies:
- Short Straddle
- (More strategies can be added)

Author: Trading System Team
"""

from strategies.base_strategy import BaseStrategy, StrategyConfig
from strategies.short_straddle import ShortStraddleStrategy

__all__ = [
    'BaseStrategy',
    'StrategyConfig',
    'ShortStraddleStrategy'
]
