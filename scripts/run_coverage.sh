#!/bin/bash
# Test coverage script for Vega project
# This script generates coverage reports for the codebase

set -e  # Exit on error

echo "=== Running Vega Test Coverage Analysis ==="
echo "Python version: $(python --version)"

# Move to project root directory
SCRIPT_DIR=$(dirname "$(readlink -f "$0")")
cd "$SCRIPT_DIR/.."

# Clean up any previous coverage data
echo "Cleaning up previous coverage data..."
rm -f .coverage
rm -rf htmlcov/

# Run tests with coverage
echo "Running tests with coverage analysis..."
python -m pytest --cov=vega_common --cov=vega_server --cov=vega_client --cov-report=term-missing "$@"

# Generate HTML report if no arguments provided
if [ $# -eq 0 ]; then
    echo "Generating HTML coverage report..."
    python -m pytest --cov=vega_common --cov=vega_server --cov=vega_client --cov-report=html
    echo "HTML coverage report generated in htmlcov/ directory"
fi

echo "=== Coverage analysis completed ==="