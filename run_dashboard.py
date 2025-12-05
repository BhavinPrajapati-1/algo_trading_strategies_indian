#!/usr/bin/env python3
"""
Trading Dashboard Launcher

Launches the trading analytics dashboard with proper Python path configuration.

Usage:
    python run_dashboard.py [options]

Options:
    --host HOST     Host to bind to (default: 127.0.0.1)
    --port PORT     Port to bind to (default: 5000)
    --debug         Enable debug mode
    --help          Show this help message

Author: Trading Analytics Team
"""

import sys
import os
from pathlib import Path
import argparse

# Add project root to Python path
project_root = Path(__file__).parent.absolute()
sys.path.insert(0, str(project_root))

# Now import the dashboard
from utils.dashboard import app, logger


def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description='Trading Analytics Dashboard',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python run_dashboard.py
  python run_dashboard.py --host 0.0.0.0 --port 8080
  python run_dashboard.py --debug

The dashboard will be available at http://host:port/
Default: http://127.0.0.1:5000/
        """
    )

    parser.add_argument(
        '--host',
        default='127.0.0.1',
        help='Host to bind to (default: 127.0.0.1)'
    )

    parser.add_argument(
        '--port',
        type=int,
        default=5000,
        help='Port to bind to (default: 5000)'
    )

    parser.add_argument(
        '--debug',
        action='store_true',
        help='Enable debug mode'
    )

    return parser.parse_args()


def main():
    """Main entry point."""
    args = parse_arguments()

    print("=" * 60)
    print("📊 Trading Analytics Dashboard")
    print("=" * 60)
    print(f"Host: {args.host}")
    print(f"Port: {args.port}")
    print(f"Debug: {args.debug}")
    print(f"URL: http://{args.host}:{args.port}/")
    print("=" * 60)
    print("\nPress Ctrl+C to stop the server\n")

    try:
        app.run(
            host=args.host,
            port=args.port,
            debug=args.debug
        )
    except KeyboardInterrupt:
        print("\n\n🛑 Dashboard stopped by user")
    except Exception as e:
        logger.error(f"Error starting dashboard: {e}", exc_info=True)
        print(f"\n❌ Error: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
