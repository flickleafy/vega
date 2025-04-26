#!/bin/bash
# Setup script for Vega project
# This script sets up the virtual environment and installs all dependencies

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

echo -e "${GREEN}=== Vega Project Setup ===${NC}"
echo

# Check if virtual environment exists
if [ -d "vega_env" ]; then
    echo -e "${YELLOW}Virtual environment already exists.${NC}"
    read -p "Do you want to recreate it? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo -e "${YELLOW}Removing existing virtual environment...${NC}"
        rm -rf vega_env
    fi
fi

# Create virtual environment if it doesn't exist
if [ ! -d "vega_env" ]; then
    echo -e "${GREEN}Creating virtual environment...${NC}"
    python3 -m venv vega_env
    if [ $? -ne 0 ]; then
        echo -e "${RED}Failed to create virtual environment${NC}"
        exit 1
    fi
    echo -e "${GREEN}✓ Virtual environment created${NC}"
fi

# Activate virtual environment
echo -e "${GREEN}Activating virtual environment...${NC}"
source vega_env/bin/activate

# Upgrade pip, setuptools, and wheel
echo -e "${GREEN}Upgrading pip, setuptools, and wheel...${NC}"
pip install --upgrade pip setuptools wheel
echo -e "${GREEN}✓ Build tools upgraded${NC}"

# Install project dependencies
echo -e "${GREEN}Installing project dependencies from requirements.txt...${NC}"
pip install -r requirements.txt
if [ $? -ne 0 ]; then
    echo -e "${RED}Failed to install dependencies from requirements.txt${NC}"
    exit 1
fi
echo -e "${GREEN}✓ Dependencies installed${NC}"

# Install vega_common in editable mode
echo -e "${GREEN}Installing vega_common in editable mode...${NC}"
pip install -e ./vega_common
if [ $? -ne 0 ]; then
    echo -e "${RED}Failed to install vega_common${NC}"
    exit 1
fi
echo -e "${GREEN}✓ vega_common installed${NC}"

echo
echo -e "${GREEN}=== Setup Complete ===${NC}"
echo
echo -e "To activate the virtual environment, run:"
echo -e "  ${YELLOW}source activate.sh${NC}"
echo
echo -e "Or manually:"
echo -e "  ${YELLOW}source vega_env/bin/activate${NC}"
echo
