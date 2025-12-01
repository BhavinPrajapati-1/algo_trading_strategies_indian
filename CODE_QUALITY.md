# Code Quality & Development Guide

This document describes the code quality tools, CI/CD workflows, and development practices for this project.

## 🎯 Overview

We maintain high code quality standards through:
- **Automated linting** and formatting
- **Security scanning** for vulnerabilities
- **Type checking** for better code safety
- **Comprehensive logging** for debugging
- **Performance metrics** tracking
- **CI/CD workflows** for continuous quality checks

---

## 🛠️ Development Setup

### Quick Start

```bash
# Clone the repository
git clone https://github.com/buzzsubash/algo_trading_strategies_india.git
cd algo_trading_strategies_india

# Install development dependencies
pip install -r requirements-dev.txt

# Set up pre-commit hooks
pre-commit install

# Run tests
pytest
```

### Environment Setup

1. **Create virtual environment**:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # Linux/Mac
   # or
   .venv\Scripts\activate  # Windows
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt       # Production dependencies
   pip install -r requirements-dev.txt   # Development dependencies
   ```

3. **Configure environment**:
   ```bash
   cp .env.example .env
   # Edit .env with your credentials
   ```

---

## 📝 Code Quality Tools

### 1. Code Formatting

#### Black (Auto-formatter)
```bash
# Format all files
black .

# Check without modifying
black --check .

# Format specific file
black utils/credentials.py
```

**Configuration**: `pyproject.toml`
- Line length: 120 characters
- Target Python: 3.8+

#### isort (Import Sorting)
```bash
# Sort imports
isort .

# Check only
isort --check-only .
```

### 2. Linting

#### Flake8
```bash
# Run flake8
flake8 .

# With specific checks
flake8 --select=E,W,F .
```

**Configuration**: `pyproject.toml` and `.flake8`

#### Pylint
```bash
# Run pylint on all Python files
find . -name "*.py" | xargs pylint

# Run on specific module
pylint utils/
```

**Configuration**: `pyproject.toml`

### 3. Type Checking

#### MyPy
```bash
# Type check entire project
mypy .

# Type check specific module
mypy utils/
```

### 4. Security Scanning

#### Bandit (Code Security)
```bash
# Scan for security issues
bandit -r .

# Generate JSON report
bandit -r . -f json -o bandit-report.json
```

#### Safety (Dependency Vulnerabilities)
```bash
# Check dependencies
safety check

# Check specific requirements file
safety check -r requirements.txt
```

### 5. Pre-commit Hooks

Automatically run checks before each commit:

```bash
# Install hooks
pre-commit install

# Run manually on all files
pre-commit run --all-files

# Update hook versions
pre-commit autoupdate
```

**Configured hooks**:
- Trailing whitespace removal
- YAML/JSON syntax validation
- Secret detection
- Black formatting
- isort import sorting
- Flake8 linting
- Bandit security scan

---

## 📊 Logging System

### Usage

```python
from utils.logging_config import setup_logger, get_logger

# Set up logger for your module
logger = setup_logger('my_strategy', level='INFO')

# Use the logger
logger.info("Strategy started")
logger.warning("High volatility detected")
logger.error("Order failed", extra={'order_id': '123'})
logger.debug("Processing data...")

# For trading strategies (specialized logging)
from utils.logging_config import setup_trade_logger

logger = setup_trade_logger('banknifty_straddle')
logger.info("Order placed", extra={
    'order_id': 'ORD123',
    'symbol': 'BANKNIFTY',
    'price': 150.50
})
```

### Log Levels

- **DEBUG**: Detailed diagnostic information
- **INFO**: General informational messages
- **WARNING**: Warning messages
- **ERROR**: Error messages
- **CRITICAL**: Critical issues

### Log Output

Logs are written to:
- **Console**: Color-coded output
- **File**: `logs/<strategy_name>.log` (rotating, max 10MB)
- **Trade logs**: `logs/trades/<strategy>_trades.log`
- **Error logs**: `logs/errors/<strategy>_errors.log`

---

## 📈 Performance Metrics

### Usage

```python
from utils.metrics import MetricsTracker

# Initialize tracker
tracker = MetricsTracker(strategy_name='my_strategy')

# Record trades
tracker.record_trade(
    symbol='BANKNIFTY2350045000CE',
    action='SELL',
    quantity=15,
    price=150.50,
    order_id='ORD123',
    pnl=500.0
)

# Update position prices (for MTM)
tracker.update_position_price('BANKNIFTY2350045000CE', 145.00)

# Get metrics
metrics = tracker.get_metrics()
print(f"Total P&L: {metrics['total_pnl']}")
print(f"Win Rate: {metrics['win_rate']}%")
print(f"Profit Factor: {metrics['profit_factor']}")

# Export metrics to JSON
tracker.export_metrics_json()
```

### Available Metrics

- Total trades
- Winning/losing trades
- Win rate
- Total P&L
- Gross profit/loss
- Average win/loss
- Profit factor
- Unrealized P&L
- Open positions count

---

## 🔄 CI/CD Workflows

### GitHub Actions

Three main workflows run automatically:

#### 1. Code Quality (`code-quality.yml`)

**Triggers**: Push/PR to main branches
**Runs**:
- Black formatting check
- Flake8 linting
- isort import sorting
- Pylint analysis
- MyPy type checking
- Code complexity analysis (radon)

**Status**: [![Code Quality](https://github.com/buzzsubash/algo_trading_strategies_india/actions/workflows/code-quality.yml/badge.svg)](https://github.com/buzzsubash/algo_trading_strategies_india/actions/workflows/code-quality.yml)

#### 2. Security Scanning (`security.yml`)

**Triggers**: Push/PR + Weekly schedule
**Runs**:
- Secret detection (TruffleHog, Gitleaks)
- Dependency vulnerability scanning (Safety, pip-audit)
- Code security analysis (Bandit)
- Credential management verification
- Static analysis (Semgrep)

**Status**: [![Security](https://github.com/buzzsubash/algo_trading_strategies_india/actions/workflows/security.yml/badge.svg)](https://github.com/buzzsubash/algo_trading_strategies_india/actions/workflows/security.yml)

#### 3. Dependency Management (`dependencies.yml`)

**Triggers**: Push/PR + Weekly schedule
**Runs**:
- Multi-platform installation testing
- Dependency audit and conflicts
- License compliance check
- Requirements validation
- Python version compatibility

**Status**: [![Dependencies](https://github.com/buzzsubash/algo_trading_strategies_india/actions/workflows/dependencies.yml/badge.svg)](https://github.com/buzzsubash/algo_trading_strategies_india/actions/workflows/dependencies.yml)

---

## 🧪 Testing

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=utils --cov-report=html

# Run specific test file
pytest tests/test_credentials.py

# Run with markers
pytest -m unit  # Only unit tests
pytest -m "not slow"  # Skip slow tests
```

### Test Structure

```
tests/
├── unit/               # Unit tests
├── integration/        # Integration tests
└── fixtures/          # Test fixtures
```

### Writing Tests

```python
import pytest
from utils.credentials import get_zerodha_credentials

def test_credentials_loading():
    """Test credential loading from environment."""
    # Test implementation
    pass

@pytest.mark.slow
def test_api_connection():
    """Test actual API connection (slow test)."""
    pass
```

---

## 📚 Documentation

### Docstring Style

Use Google-style docstrings:

```python
def calculate_mtm(entry_price: float, current_price: float, quantity: int) -> float:
    """
    Calculate mark-to-market profit/loss.

    Args:
        entry_price: Entry price of the position
        current_price: Current market price
        quantity: Position quantity (positive for long, negative for short)

    Returns:
        Unrealized P&L in rupees

    Raises:
        ValueError: If quantity is zero

    Example:
        >>> calculate_mtm(100.0, 105.0, 15)
        75.0
    """
    if quantity == 0:
        raise ValueError("Quantity cannot be zero")

    return (current_price - entry_price) * quantity
```

### Building Documentation

```bash
# Install Sphinx
pip install sphinx sphinx-rtd-theme

# Build HTML docs
cd docs/
make html

# View docs
open _build/html/index.html
```

---

## 🔧 Configuration Files

### `pyproject.toml`
Central configuration for all tools:
- Build system
- Project metadata
- Black settings
- isort configuration
- Pylint rules
- MyPy options
- Pytest settings
- Coverage configuration

### `.pre-commit-config.yaml`
Pre-commit hook configuration:
- File checks
- Secret detection
- Code formatting
- Linting
- Security scanning

### `requirements-dev.txt`
Development dependencies:
- Linting tools
- Testing frameworks
- Documentation generators
- Security scanners

---

## 🎨 Code Style Guidelines

### General Principles

1. **Readability**: Code is read more than written
2. **Simplicity**: Prefer simple solutions
3. **Consistency**: Follow existing patterns
4. **Documentation**: Document why, not what

### Python Style

- Follow PEP 8 (enforced by Black and Flake8)
- Line length: 120 characters
- Use type hints where practical
- Meaningful variable names
- Avoid magic numbers (use constants)

### Naming Conventions

```python
# Variables and functions: snake_case
entry_price = 100.0
def calculate_profit():
    pass

# Classes: PascalCase
class TradingStrategy:
    pass

# Constants: UPPER_SNAKE_CASE
MAX_POSITION_SIZE = 100
API_TIMEOUT = 30

# Private: _leading_underscore
def _internal_helper():
    pass
```

### Import Organization

```python
# Standard library
import os
import sys
from datetime import datetime

# Third-party
import pandas as pd
import numpy as np
from kiteconnect import KiteConnect

# Local/project
from utils.credentials import get_kite_instance
from utils.logging_config import setup_logger
```

---

## 🐛 Debugging

### Logging for Debugging

```python
import logging

# Set debug level
logger = setup_logger('my_module', level='DEBUG')

# Debug messages
logger.debug(f"Variable value: {variable}")
logger.debug(f"Function called with args: {args}")
```

### Using IPython Debugger

```python
# Add breakpoint
import ipdb; ipdb.set_trace()

# Or use Python 3.7+
breakpoint()
```

### Profiling

```bash
# Line profiler
kernprof -l -v script.py

# Memory profiler
python -m memory_profiler script.py

# Sampling profiler
py-spy top -- python script.py
```

---

## ✅ Best Practices

### Before Committing

1. Run linters: `black . && flake8 . && pylint utils/`
2. Run tests: `pytest`
3. Check security: `bandit -r .`
4. Review changes: `git diff`

### Writing Secure Code

- ✅ Use environment variables for credentials
- ✅ Never hardcode API keys
- ✅ Validate user inputs
- ✅ Handle exceptions properly
- ✅ Log security events
- ❌ Don't commit `.env` files
- ❌ Don't use `eval()` or `exec()`
- ❌ Don't trust external data

### Performance Tips

- Use generators for large datasets
- Profile before optimizing
- Cache expensive computations
- Use appropriate data structures
- Avoid premature optimization

---

## 📞 Getting Help

- **Issues**: [GitHub Issues](https://github.com/buzzsubash/algo_trading_strategies_india/issues)
- **Documentation**: [README.md](README.md)
- **Authentication**: [AUTHENTICATION.md](AUTHENTICATION.md)
- **Migration**: [MIGRATION_GUIDE.md](MIGRATION_GUIDE.md)

---

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run quality checks (linting, tests, security)
5. Commit with clear messages
6. Push and create a Pull Request

All PRs must pass CI/CD checks before merging.

---

**Happy coding! 🚀**
