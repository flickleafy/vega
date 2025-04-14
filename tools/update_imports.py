#!/usr/bin/env python3
"""
Import Migration Script for Vega Project

This script automatically updates import statements across the Vega codebase
to use the new vega_common shared library instead of local utility modules.

Usage:
    python update_imports.py

Author: Vega Team
"""
import os
import re
from pathlib import Path
import argparse
from typing import Dict, List, Optional


# Define mapping of old imports to new imports
IMPORT_MAPPING = {
    r'from utils\.filesManipulation import (.+)': r'from vega_common.utils.files_manipulation import \1',
    r'from utils\.listProcess import (.+)': r'from vega_common.utils.list_process import \1',
    r'from utils\.datetime import (.+)': r'from vega_common.utils.datetime_utils import \1',
    r'from utils\.subProcess import (.+)': r'from vega_common.utils.sub_process import \1',
    r'import utils\.filesManipulation': r'import vega_common.utils.files_manipulation',
    r'import utils\.listProcess': r'import vega_common.utils.list_process',
    r'import utils\.datetime': r'import vega_common.utils.datetime_utils',
    r'import utils\.subProcess': r'import vega_common.utils.sub_process',
    # Handle aliased imports
    r'from utils\.filesManipulation import (.+) as (.+)': r'from vega_common.utils.files_manipulation import \1 as \2',
    r'from utils\.listProcess import (.+) as (.+)': r'from vega_common.utils.list_process import \1 as \2',
    r'from utils\.datetime import (.+) as (.+)': r'from vega_common.utils.datetime_utils import \1 as \2',
    r'from utils\.subProcess import (.+) as (.+)': r'from vega_common.utils.sub_process import \1 as \2',
}

# Project directories to update
PROJECT_DIRS = [
    "vega_server/rootspace",
    "vega_server/userspace", 
    "vega_server/gateway",
    "vega_client"
]


def update_imports(file_path: str, dry_run: bool = False) -> bool:
    """
    Update imports in a Python file.
    
    Args:
        file_path (str): Path to the Python file to update
        dry_run (bool, optional): If True, only prints changes without modifying files
        
    Returns:
        bool: True if file was modified, False otherwise
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except UnicodeDecodeError:
        print(f"Warning: Could not read {file_path} as text. Skipping...")
        return False
        
    modified = False
    new_content = content
    
    for old_pattern, new_pattern in IMPORT_MAPPING.items():
        if re.search(old_pattern, new_content):
            new_content = re.sub(old_pattern, new_pattern, new_content)
            modified = True
    
    if modified:
        if dry_run:
            print(f"Would update imports in {file_path}")
        else:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(new_content)
            print(f"Updated imports in {file_path}")
    
    return modified


def process_directory(dir_path: str, dry_run: bool = False) -> int:
    """
    Process all Python files in a directory.
    
    Args:
        dir_path (str): Directory path to recursively process
        dry_run (bool, optional): If True, only prints changes without modifying files
        
    Returns:
        int: Number of files modified
    """
    modified_count = 0
    for root, _, files in os.walk(dir_path):
        for file in files:
            if file.endswith(".py"):
                file_path = os.path.join(root, file)
                if update_imports(file_path, dry_run):
                    modified_count += 1
    
    return modified_count


def main() -> None:
    """Main execution function."""
    parser = argparse.ArgumentParser(
        description='Update import statements in Vega project to use vega_common shared library'
    )
    parser.add_argument(
        '--dry-run', 
        action='store_true',
        help='Show changes without modifying files'
    )
    parser.add_argument(
        '--project-dir',
        type=str,
        default=None,
        help='Specify a single project directory to update (relative to repository root)'
    )
    
    args = parser.parse_args()
    
    base_dir = Path(__file__).parent.parent
    
    total_modified = 0
    
    if args.project_dir:
        # Process a single specified directory
        target_dir = base_dir / args.project_dir
        if not target_dir.exists() or not target_dir.is_dir():
            print(f"Error: Directory {target_dir} does not exist.")
            return
        
        print(f"\nProcessing directory: {target_dir}\n")
        modified = process_directory(str(target_dir), args.dry_run)
        total_modified += modified
    else:
        # Process all project directories
        for project_dir in PROJECT_DIRS:
            target_dir = base_dir / project_dir
            if not target_dir.exists():
                print(f"Warning: Directory {target_dir} does not exist. Skipping...")
                continue
                
            print(f"\nProcessing directory: {target_dir}\n")
            modified = process_directory(str(target_dir), args.dry_run)
            total_modified += modified
    
    if args.dry_run:
        print(f"\nDry run completed. {total_modified} files would be modified.")
    else:
        print(f"\nMigration completed. {total_modified} files were modified.")


if __name__ == "__main__":
    main()