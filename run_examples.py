#!/usr/bin/env python3
"""
Example Scripts Launcher

Launches various example scripts with proper Python path configuration.

Usage:
    python run_examples.py [example_name]

Available Examples:
    analytics       - Trading analytics demo
    upstox          - Upstox with Telegram notifications demo
    symbol_select   - Dynamic symbol selection demo

Author: Trading Analytics Team
"""

import sys
import os
from pathlib import Path
import argparse

# Add project root to Python path
project_root = Path(__file__).parent.absolute()
sys.path.insert(0, str(project_root))


EXAMPLES = {
    'analytics': {
        'path': 'examples/analytics_demo.py',
        'description': 'Comprehensive trading analytics demonstration'
    },
    'upstox': {
        'path': 'examples/upstox_telegram_example.py',
        'description': 'Upstox broker with Telegram notifications'
    },
    'symbol_select': {
        'path': 'examples/dynamic_symbol_selection_strategy.py',
        'description': 'Dynamic symbol selection strategy'
    }
}


def list_examples():
    """List all available examples."""
    print("\n📚 Available Examples:")
    print("=" * 70)
    for name, info in EXAMPLES.items():
        print(f"\n  {name}")
        print(f"    Description: {info['description']}")
        print(f"    Path: {info['path']}")
    print("\n" + "=" * 70)
    print("\nUsage: python run_examples.py <example_name>")
    print("Example: python run_examples.py analytics\n")


def run_example(example_name):
    """Run a specific example."""
    if example_name not in EXAMPLES:
        print(f"❌ Error: Unknown example '{example_name}'")
        list_examples()
        sys.exit(1)

    example = EXAMPLES[example_name]
    example_path = project_root / example['path']

    if not example_path.exists():
        print(f"❌ Error: Example file not found: {example_path}")
        sys.exit(1)

    print("\n" + "=" * 70)
    print(f"🚀 Running: {example['description']}")
    print("=" * 70)
    print(f"File: {example['path']}\n")

    # Read and execute the example file
    with open(example_path, 'r') as f:
        code = f.read()

    # Execute in a namespace with proper __name__
    namespace = {
        '__name__': '__main__',
        '__file__': str(example_path),
    }

    try:
        exec(code, namespace)
    except KeyboardInterrupt:
        print("\n\n🛑 Example stopped by user")
    except Exception as e:
        print(f"\n❌ Error running example: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Run example scripts',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    parser.add_argument(
        'example',
        nargs='?',
        choices=list(EXAMPLES.keys()) + ['list'],
        help='Example to run (or "list" to show all)'
    )

    args = parser.parse_args()

    if not args.example or args.example == 'list':
        list_examples()
    else:
        run_example(args.example)


if __name__ == '__main__':
    main()
