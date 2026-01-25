#!/bin/bash
# Activation script for vega virtual environment
# Usage: source activate.sh

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Activate the virtual environment
source "${SCRIPT_DIR}/vega_env/bin/activate"

echo "Virtual environment activated: vega_env"
echo "Python: $(which python)"
echo "Python version: $(python --version)"
