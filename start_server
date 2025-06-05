#!/bin/bash

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Load environment variables from .env file
if [ -f .env ]; then
    export $(cat .env | grep -E '^(API_HOST|API_PORT)=' | xargs)
fi

# Configuration (use env vars or defaults)
PORT=${API_PORT:-8000}
HOST=${API_HOST:-0.0.0.0}


# Start the env
source start_env

# Start the Server
echo -e "${YELLOW}Starting TKR News Gather Server...${NC}"
echo -e "${GREEN}Configuration: HOST=$HOST, PORT=$PORT${NC}"

# Check if port is in use
if lsof -Pi :$PORT -sTCP:LISTEN -t >/dev/null ; then
    echo -e "${YELLOW}Port $PORT is already in use. Killing existing process...${NC}"
    lsof -ti:$PORT | xargs kill -9 2>/dev/null
    sleep 1
fi

# Activate virtual environment if not already activated
if [[ "$VIRTUAL_ENV" == "" ]]; then
    echo -e "${YELLOW}Activating virtual environment...${NC}"
    source /Volumes/tkr-riffic/@tkr-projects/tkr-news-gather/tkr_env/project_env/bin/activate
fi

# Use the virtual environment's Python explicitly
PYTHON_PATH="/Volumes/tkr-riffic/@tkr-projects/tkr-news-gather/tkr_env/project_env/bin/python"

# Check if Python exists
if [ ! -f "$PYTHON_PATH" ]; then
    echo -e "${RED}Error: Python not found at $PYTHON_PATH${NC}"
    exit 1
fi

# Display Python version and location
echo -e "${GREEN}Using Python: $PYTHON_PATH${NC}"
$PYTHON_PATH --version

# Start the server
echo -e "${GREEN}Starting server on http://$HOST:$PORT${NC}"
echo -e "${YELLOW}Press Ctrl+C to stop the server${NC}"

# Run uvicorn with the virtual environment's Python
$PYTHON_PATH -m uvicorn src.main:app --reload --host $HOST --port $PORT