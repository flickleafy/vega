#!/bin/bash
# Basic test runner script for Vega project
# This script runs the entire test suite with a clean environment

set -e  # Exit on error

echo "=== Running Vega Test Suite ==="
echo "Python version: $(python --version)"

# Move to project root directory
SCRIPT_DIR=$(dirname "$(readlink -f "$0")")
cd "$SCRIPT_DIR/.."

# Clean up any previous test artifacts
echo "Cleaning up previous test artifacts..."
find . -type d -name "__pycache__" -exec rm -rf {} +
find . -name "*.pyc" -delete
find . -name "*.pyo" -delete

# Run the tests
echo "Running tests..."
python -m pytest --runperf "$@"

echo "=== Test execution completed ==="