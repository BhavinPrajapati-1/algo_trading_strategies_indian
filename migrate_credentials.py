#!/usr/bin/env python3
"""
Credential Migration Helper
===========================
This script helps migrate strategy files from hardcoded credentials
to environment variable-based credentials.

Usage:
    python migrate_credentials.py --scan        # Scan for files with hardcoded credentials
    python migrate_credentials.py --migrate     # Migrate files automatically
    python migrate_credentials.py --verify      # Verify migration
"""

import os
import re
import argparse
from pathlib import Path
from typing import List, Tuple


def scan_files_with_hardcoded_credentials(root_dir: str = ".") -> List[Tuple[str, int]]:
    """
    Scan for Python files with hardcoded credentials.

    Returns:
        List of (filepath, line_number) tuples
    """
    results = []
    patterns = [
        r'api_key\s*=\s*["\'][^"\']*["\']',
        r'api_secret\s*=\s*["\'][^"\']*["\']',
    ]

    exclude_dirs = {'.venv', 'venv', 'env', '.git', '__pycache__', 'build', 'dist', 'utils'}

    for root, dirs, files in os.walk(root_dir):
        # Filter out excluded directories
        dirs[:] = [d for d in dirs if d not in exclude_dirs]

        for file in files:
            if not file.endswith('.py'):
                continue

            filepath = os.path.join(root, file)

            # Skip utility files and example files
            if 'credentials.py' in filepath or 'example' in filepath.lower():
                continue

            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    for line_num, line in enumerate(f, 1):
                        for pattern in patterns:
                            if re.search(pattern, line):
                                results.append((filepath, line_num))
                                break
            except Exception as e:
                print(f"Error reading {filepath}: {e}")

    return results


def add_env_imports(content: str) -> str:
    """Add necessary imports for environment variable support."""
    lines = content.split('\n')

    # Check if imports already exist
    has_os = any('import os' in line for line in lines)
    has_dotenv = any('from dotenv import load_dotenv' in line or 'import dotenv' in line for line in lines)

    # Find where to insert imports (after other imports)
    import_end_idx = 0
    for i, line in enumerate(lines):
        if line.startswith('import ') or line.startswith('from '):
            import_end_idx = i + 1

    # Add missing imports
    new_imports = []
    if not has_os:
        new_imports.append('import os')
    if not has_dotenv:
        new_imports.append('from dotenv import load_dotenv')

    if new_imports:
        # Add a blank line before new imports if needed
        if import_end_idx > 0:
            new_imports.insert(0, '')

        lines = lines[:import_end_idx] + new_imports + lines[import_end_idx:]

        # Add load_dotenv() call after imports
        load_dotenv_idx = import_end_idx + len(new_imports)
        lines.insert(load_dotenv_idx, '')
        lines.insert(load_dotenv_idx + 1, '# Load environment variables from .env file')
        lines.insert(load_dotenv_idx + 2, 'load_dotenv()')

    return '\n'.join(lines)


def migrate_credential_lines(content: str) -> str:
    """Migrate hardcoded credential assignments to environment variables."""

    # Replace api_key assignments
    content = re.sub(
        r'api_key\s*=\s*["\'][^"\']*["\']',
        'api_key = os.getenv(\'ZERODHA_API_KEY\')',
        content
    )

    # Replace api_secret assignments
    content = re.sub(
        r'api_secret\s*=\s*["\'][^"\']*["\']',
        'api_secret = os.getenv(\'ZERODHA_API_SECRET\')',
        content
    )

    # Replace access_token file reads
    content = re.sub(
        r'access_token\s*=\s*open\([^)]+\)\.read\(\)',
        'access_token = os.getenv(\'ZERODHA_ACCESS_TOKEN\')',
        content
    )

    return content


def add_validation_warning(content: str) -> str:
    """Add validation and warning for missing credentials."""
    lines = content.split('\n')

    # Find where credentials are loaded
    credential_idx = -1
    for i, line in enumerate(lines):
        if 'api_key = os.getenv' in line:
            credential_idx = i
            break

    if credential_idx == -1:
        return content

    # Find the end of credential loading (after access_token or api_secret)
    end_idx = credential_idx
    for i in range(credential_idx, min(credential_idx + 10, len(lines))):
        if 'access_token' in lines[i] or 'api_secret' in lines[i]:
            end_idx = i

    # Add validation code after credentials
    validation_code = [
        '',
        '# Validate credentials are loaded',
        'if not api_key or not api_secret or not access_token:',
        '    print("⚠️  ERROR: Credentials not found in environment variables")',
        '    print("Please ensure your .env file contains:")',
        '    print("  - ZERODHA_API_KEY")',
        '    print("  - ZERODHA_API_SECRET")',
        '    print("  - ZERODHA_ACCESS_TOKEN")',
        '    print("")',
        '    print("Run: python zerodha_manual_auth.py to authenticate")',
        '    print("See AUTHENTICATION.md for setup instructions")',
        '    exit(1)',
        ''
    ]

    lines = lines[:end_idx + 1] + validation_code + lines[end_idx + 1:]

    return '\n'.join(lines)


def migrate_file(filepath: str, dry_run: bool = True) -> bool:
    """
    Migrate a single file to use environment variables.

    Args:
        filepath: Path to the file to migrate
        dry_run: If True, only show what would be changed

    Returns:
        True if migration was successful
    """
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            original_content = f.read()

        # Apply migrations
        content = original_content
        content = add_env_imports(content)
        content = migrate_credential_lines(content)
        content = add_validation_warning(content)

        if content == original_content:
            return False  # No changes needed

        if dry_run:
            print(f"\n{'='*70}")
            print(f"Would migrate: {filepath}")
            print(f"{'='*70}")
            # Show diff (simplified)
            print("Changes would include:")
            print("  ✅ Add: import os, from dotenv import load_dotenv")
            print("  ✅ Add: load_dotenv()")
            print("  ✅ Replace: api_key = \"\" → api_key = os.getenv('ZERODHA_API_KEY')")
            print("  ✅ Replace: api_secret = \"\" → api_secret = os.getenv('ZERODHA_API_SECRET')")
            print("  ✅ Add: Credential validation with helpful error message")
            return True
        else:
            # Create backup
            backup_path = filepath + '.backup'
            with open(backup_path, 'w', encoding='utf-8') as f:
                f.write(original_content)

            # Write migrated content
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)

            print(f"✅ Migrated: {filepath}")
            print(f"   Backup created: {backup_path}")
            return True

    except Exception as e:
        print(f"❌ Error migrating {filepath}: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(description='Migrate credentials to environment variables')
    parser.add_argument('--scan', action='store_true', help='Scan for files with hardcoded credentials')
    parser.add_argument('--migrate', action='store_true', help='Migrate files (creates backups)')
    parser.add_argument('--dry-run', action='store_true', help='Show what would be changed without modifying files')
    parser.add_argument('--verify', action='store_true', help='Verify no hardcoded credentials remain')

    args = parser.parse_args()

    if args.scan or args.dry_run:
        print("🔍 Scanning for files with hardcoded credentials...")
        print()
        results = scan_files_with_hardcoded_credentials()

        if not results:
            print("✅ No files with hardcoded credentials found!")
            return

        # Group by file
        files = {}
        for filepath, line_num in results:
            if filepath not in files:
                files[filepath] = []
            files[filepath].append(line_num)

        print(f"Found {len(files)} files with hardcoded credentials:\n")
        for filepath, line_nums in sorted(files.items()):
            print(f"  📄 {filepath}")
            print(f"     Lines: {', '.join(map(str, sorted(set(line_nums))))}")

        print(f"\nTotal: {len(files)} files need migration")

        if args.dry_run:
            print("\n" + "="*70)
            print("DRY RUN - Showing what would be changed")
            print("="*70)
            for filepath in files.keys():
                migrate_file(filepath, dry_run=True)

    elif args.migrate:
        print("🔄 Migrating files to use environment variables...")
        print()
        results = scan_files_with_hardcoded_credentials()

        if not results:
            print("✅ No files need migration!")
            return

        # Group by file
        files = {}
        for filepath, line_num in results:
            if filepath not in files:
                files[filepath] = []
            files[filepath].append(line_num)

        migrated = 0
        failed = 0

        for filepath in files.keys():
            if migrate_file(filepath, dry_run=False):
                migrated += 1
            else:
                failed += 1

        print()
        print("="*70)
        print(f"Migration complete!")
        print(f"  ✅ Migrated: {migrated} files")
        if failed > 0:
            print(f"  ❌ Failed: {failed} files")
        print()
        print("Next steps:")
        print("  1. Review the changes in migrated files")
        print("  2. Ensure your .env file has credentials")
        print("  3. Run: python zerodha_manual_auth.py")
        print("  4. Test your strategies")
        print("="*70)

    elif args.verify:
        print("✓ Verifying migration...")
        results = scan_files_with_hardcoded_credentials()

        if not results:
            print("✅ Verification passed! No hardcoded credentials found.")
        else:
            files = set(filepath for filepath, _ in results)
            print(f"⚠️  Found {len(files)} files still with hardcoded credentials:")
            for filepath in sorted(files):
                print(f"   {filepath}")

    else:
        parser.print_help()


if __name__ == '__main__':
    main()
