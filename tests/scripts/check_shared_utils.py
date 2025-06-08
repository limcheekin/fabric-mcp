#!/usr/bin/env python3
"""
Script to find unused files in tests/shared/ directory.
Files that are not imported by other test files are considered unused.
"""

import os
import re
import sys
from pathlib import Path


def find_python_files(directory: str) -> list[str]:
    """Find all Python files in a directory, excluding __init__.py and __pycache__."""
    python_files: list[str] = []
    for root, dirs, files in os.walk(directory):
        # Skip __pycache__ directories
        dirs[:] = [d for d in dirs if d != "__pycache__"]

        for file in files:
            if file.endswith(".py") and file != "__init__.py":
                python_files.append(os.path.join(root, file))
    return python_files


def get_import_name(file_path: str, base_dir: str) -> str:
    """Convert file path to import name."""
    rel_path = os.path.relpath(file_path, base_dir)
    import_name = rel_path.replace(os.sep, ".").replace(".py", "")
    return import_name


def is_file_imported(import_name: str, search_directory: str) -> bool:
    """Check if a file is imported anywhere in the search directory."""
    # Create regex patterns for different import styles
    patterns = [
        # Direct imports from relative path
        rf"from\s+{re.escape(import_name)}\s+import",
        rf"import\s+{re.escape(import_name)}",
        # Imports with full tests.shared prefix
        rf"from\s+tests\.shared\.{re.escape(import_name)}\s+import",
        rf"import\s+tests\.shared\.{re.escape(import_name)}",
        # Imports with just the module name (last part)
        rf"from\s+tests\.shared\.{re.escape(import_name.split('.')[-1])}\s+import",
        rf"import\s+tests\.shared\.{re.escape(import_name.split('.')[-1])}",
    ]

    for root, dirs, files in os.walk(search_directory):
        # Skip __pycache__ directories
        dirs[:] = [d for d in dirs if d != "__pycache__"]

        for file in files:
            if file.endswith(".py"):
                file_path = os.path.join(root, file)
                try:
                    with open(file_path, encoding="utf-8") as f:
                        content = f.read()
                        for pattern in patterns:
                            if re.search(pattern, content):
                                return True
                except (UnicodeDecodeError, PermissionError):
                    continue
    return False


def main() -> None:
    """Main function to find unused files in tests/shared/."""
    script_dir = Path(__file__).parent
    project_root = script_dir.parent.parent
    shared_dir = project_root / "tests" / "shared"
    tests_dir = project_root / "tests"

    if not shared_dir.exists():
        print(f"Directory {shared_dir} does not exist")
        return

    # Find all Python files in tests/shared/
    shared_files = find_python_files(str(shared_dir))

    if not shared_files:
        print("No Python files found in tests/shared/")
        return

    unused_files: list[str] = []

    for file_path in shared_files:
        import_name = get_import_name(file_path, str(shared_dir))

        # Check if this file is imported anywhere in tests/
        if not is_file_imported(import_name, str(tests_dir)):
            unused_files.append(file_path)

    # Report results
    if unused_files:
        print("Unused files in tests/shared/:")
        for file_path in unused_files:
            rel_path = os.path.relpath(file_path, project_root)
            print(f"  - {rel_path}")
        print(f"\nFound {len(unused_files)} unused file(s)")
        sys.exit(1)
    else:
        print("All files in tests/shared/ are being used")


if __name__ == "__main__":
    main()
