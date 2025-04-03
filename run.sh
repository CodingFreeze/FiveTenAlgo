#!/bin/bash

# FiveTenAlgo Application Runner Script
# This script runs the Flask application with proper environment setup

# Colors for better visibility
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${YELLOW}Starting FiveTenAlgo Trading Dashboard...${NC}"

# Check if virtual environment exists
if [ -d "venv" ]; then
    echo -e "${GREEN}Found virtual environment. Activating...${NC}"
    source venv/bin/activate
else
    echo -e "${YELLOW}Virtual environment not found. Creating one...${NC}"
    python3 -m venv venv
    source venv/bin/activate
    
    echo -e "${YELLOW}Installing required packages...${NC}"
    pip install -r requirements.txt
fi

# Create data directory if it doesn't exist
if [ ! -d "data" ]; then
    echo -e "${YELLOW}Creating data directory...${NC}"
    mkdir -p data
fi

# Check if precomputed data exists
if [ ! -f "data/precomputed_simulation.json" ]; then
    echo "Generating precomputed data (this may take several minutes)..."
    python cli.py run
fi

# Run the Flask application
echo -e "${GREEN}Starting Flask application...${NC}"
echo -e "${YELLOW}Application will be available at http://localhost:8080${NC}"
python app.py

# Capture exit code
EXIT_CODE=$?

# Deactivate virtual environment
deactivate

# Check if application exited with an error
if [ $EXIT_CODE -ne 0 ]; then
    echo -e "${RED}Application exited with error code $EXIT_CODE${NC}"
    echo -e "${YELLOW}Check the logs above for details${NC}"
    exit $EXIT_CODE
fi

echo -e "${GREEN}Application terminated successfully${NC}" 