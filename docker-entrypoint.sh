#!/bin/bash
set -e

echo "Starting Stock Advisor Application..."

# Wait for dependencies (if any)
echo "Checking dependencies..."

# Initialize MCP servers in background
echo "Starting MCP servers..."
python -m mcp_servers.index_server &
python -m mcp_servers.recommendation_server &
python -m mcp_servers.trading_server &

# Wait a moment for servers to start
sleep 5

# Start the main application
echo "Starting main application..."
if [ "$APP_ENV" = "production" ]; then
    # Production mode
    uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
else
    # Development mode
    uvicorn main:app --host 0.0.0.0 --port 8000 --reload
fi