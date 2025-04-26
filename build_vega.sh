#!/bin/bash
# Vega Build Wrapper Script
# This script ensures the build runs in the correct virtual environment

set -e  # Exit on error

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="$SCRIPT_DIR/vega_env"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}=== Vega Build Script ===${NC}"

# Check if venv exists
if [ ! -d "$VENV_DIR" ]; then
    echo -e "${RED}Error: Virtual environment not found at $VENV_DIR${NC}"
    echo "Please run setup.sh first to create the virtual environment."
    exit 1
fi

# Check if venv has PyInstaller
if [ ! -f "$VENV_DIR/bin/pyinstaller" ]; then
    echo -e "${YELLOW}Warning: PyInstaller not found in venv. Installing...${NC}"
    source "$VENV_DIR/bin/activate"
    pip install pyinstaller
    deactivate
fi

# Activate venv and run build
echo -e "${GREEN}Activating virtual environment...${NC}"
source "$VENV_DIR/bin/activate"

echo -e "${GREEN}Python: $(which python)${NC}"
echo -e "${GREEN}NumPy version: $(python -c 'import numpy; print(numpy.__version__)')${NC}"
echo -e "${GREEN}PyInstaller: $(which pyinstaller)${NC}"

echo -e "${GREEN}Starting build...${NC}"
python "$SCRIPT_DIR/build.py"

BUILD_EXIT_CODE=$?

deactivate

if [ $BUILD_EXIT_CODE -eq 0 ]; then
    echo -e "${GREEN}=== Build completed successfully ===${NC}"
else
    echo -e "${RED}=== Build failed with exit code $BUILD_EXIT_CODE ===${NC}"
    exit $BUILD_EXIT_CODE
fi
