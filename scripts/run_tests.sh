#!/bin/bash
# Basic test runner script for Vega project
# This script runs the entire test suite with a clean environment

set -e  # Exit on error

echo "=== Running Vega Test Suite ==="

# Check Python version
PYTHON_VERSION=$(python --version 2>&1 | awk '{print $2}')
PYTHON_MAJOR=$(echo $PYTHON_VERSION | cut -d. -f1)
PYTHON_MINOR=$(echo $PYTHON_VERSION | cut -d. -f2)

echo "Python version: $PYTHON_VERSION"

# Verify Python 3.10
if [ "$PYTHON_MAJOR" -ne 3 ] || [ "$PYTHON_MINOR" -ne 10 ]; then
    echo "Warning: Tests are optimized for Python 3.10"
    echo "Current Python version: $PYTHON_VERSION"
    echo "Some tests may be skipped or fail on this version."
    
    # Uncomment the following lines to enforce Python 3.10 only
    # echo "Skipping tests. Please run with Python 3.10."
    # exit 0
fi

# Move to project root directory
SCRIPT_DIR=$(dirname "$(readlink -f "$0")")
cd "$SCRIPT_DIR/.."

# Clean up any previous test artifacts
echo "Cleaning up previous test artifacts..."
find . -type d -name "__pycache__" -exec rm -rf {} +
find . -name "*.pyc" -delete
find . -name "*.pyo" -delete

# Run pytest with any arguments passed to this script
python -m pytest "$@"

echo "=== Test execution completed ==="