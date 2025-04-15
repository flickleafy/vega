#!/bin/bash
# Code quality checks script for Vega project
# This script runs code quality tools like flake8 and mypy

set -e  # Exit on error

echo "=== Running Vega Code Quality Checks ==="
echo "Python version: $(python --version)"

# Move to project root directory
SCRIPT_DIR=$(dirname "$(readlink -f "$0")")
cd "$SCRIPT_DIR/.."

# Run mypy type checking
echo "Running mypy static type checking..."
python -m mypy vega_common vega_server vega_client --ignore-missing-imports

# Run flake8 style and error checks
echo "Running flake8 style and error checks..."
python -m flake8 vega_common vega_server vega_client --max-line-length=100 --statistics

# Print success message if everything passes
if [ $? -eq 0 ]; then
    echo -e "\n✅ All code quality checks passed!"
else
    echo -e "\n❌ Code quality checks failed!"
    exit 1
fi

echo "=== Code quality checks completed ==="