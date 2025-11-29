"""
Credentials Management Utility
==============================
This module provides a centralized way to load trading credentials from environment variables.
All trading scripts should use this module instead of hardcoding credentials.

Usage:
    from utils.credentials import get_zerodha_credentials, get_kite_instance

    # Get credentials
    api_key, api_secret, access_token = get_zerodha_credentials()

    # Or get ready-to-use KiteConnect instance
    kite = get_kite_instance()
"""

import os
from pathlib import Path
from kiteconnect import KiteConnect
from dotenv import load_dotenv

# Load environment variables from .env file
# This looks for .env in the current directory and parent directories
load_dotenv()


def get_zerodha_credentials():
    """
    Get Zerodha API credentials from environment variables.

    Returns:
        tuple: (api_key, api_secret, access_token)

    Raises:
        ValueError: If required credentials are not found
    """
    api_key = os.getenv('ZERODHA_API_KEY')
    api_secret = os.getenv('ZERODHA_API_SECRET')
    access_token = os.getenv('ZERODHA_ACCESS_TOKEN')

    # If access token is not in environment, try to load from file
    if not access_token:
        access_token_file = os.getenv('ACCESS_TOKEN_FILE', './config/access_token.txt')
        access_token_path = Path(access_token_file)

        if access_token_path.exists():
            with open(access_token_path, 'r') as f:
                access_token = f.read().strip()
            print(f"✅ Access token loaded from file: {access_token_file}")
        else:
            print(f"⚠️  Access token file not found: {access_token_file}")

    # Validate credentials
    missing = []
    if not api_key:
        missing.append('ZERODHA_API_KEY')
    if not api_secret:
        missing.append('ZERODHA_API_SECRET')
    if not access_token:
        missing.append('ZERODHA_ACCESS_TOKEN')

    if missing:
        raise ValueError(
            f"Missing required credentials: {', '.join(missing)}\n\n"
            "Please ensure these are set in your .env file.\n"
            "If you don't have a .env file, run: python zerodha_manual_auth.py"
        )

    return api_key, api_secret, access_token


def get_kite_instance():
    """
    Get a ready-to-use KiteConnect instance with credentials set.

    Returns:
        KiteConnect: Authenticated KiteConnect instance

    Raises:
        ValueError: If required credentials are not found
    """
    api_key, api_secret, access_token = get_zerodha_credentials()

    kite = KiteConnect(api_key=api_key)
    kite.set_access_token(access_token)

    return kite


def get_database_config():
    """
    Get PostgreSQL database configuration from environment variables.

    Returns:
        dict: Database configuration parameters
    """
    return {
        'dbname': os.getenv('DB_NAME', 'trading_db'),
        'user': os.getenv('DB_USER', 'postgres'),
        'password': os.getenv('DB_PASSWORD', 'password'),
        'host': os.getenv('DB_HOST', 'localhost'),
        'port': os.getenv('DB_PORT', '5432')
    }


def get_telegram_config():
    """
    Get Telegram notification configuration from environment variables.

    Returns:
        tuple: (bot_token, chat_id) or (None, None) if not configured
    """
    bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
    chat_id = os.getenv('TELEGRAM_CHAT_ID')

    return bot_token, chat_id


def get_shoonya_credentials():
    """
    Get Shoonya/Finvasia API credentials from environment variables.

    Returns:
        dict: Shoonya credentials
    """
    return {
        'user_id': os.getenv('SHOONYA_USER_ID'),
        'password': os.getenv('SHOONYA_PASSWORD'),
        'totp_key': os.getenv('SHOONYA_TOTP_KEY'),
        'vendor_code': os.getenv('SHOONYA_VENDOR_CODE'),
        'api_secret': os.getenv('SHOONYA_API_SECRET'),
        'imei': os.getenv('SHOONYA_IMEI')
    }


# Backward compatibility function for legacy scripts
def load_credentials_from_file(file_path):
    """
    Legacy function for backward compatibility.
    Loads access token from file.

    Args:
        file_path: Path to access token file

    Returns:
        str: Access token
    """
    import warnings
    warnings.warn(
        "load_credentials_from_file is deprecated. "
        "Use get_zerodha_credentials() or environment variables instead.",
        DeprecationWarning,
        stacklevel=2
    )

    with open(file_path, 'r') as f:
        return f.read().strip()
