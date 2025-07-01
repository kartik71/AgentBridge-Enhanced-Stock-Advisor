#!/bin/bash
# Enhanced startup script for Azure Container Apps deployment

# Exit immediately if a command exits with a non-zero status
set -e

# Print commands and their arguments as they are executed (for better logs)
set -x

# Function to log with timestamp
log_message() {
    echo "[$(date -Iseconds)] $1"
}

# Set PORT from environment or use default
PORT=${PORT:-8000}
log_message "PORT set to $PORT"

# Set reasonable timeouts for Azure environment
TIMEOUT=120
MAX_WORKERS=4

# Log startup
log_message "Starting Stock Advisor Application in $APP_ENV mode..."
log_message "Python version: $(python --version)"
log_message "Current directory: $(pwd)"
log_message "Directory contents: $(ls -la)"

# Verify main.py exists
if [ ! -f "main.py" ]; then
    log_message "ERROR: main.py not found in $(pwd)!"
    exit 1
fi

# Start MCP servers with proper error handling
log_message "Starting MCP servers..."

# Function to start a server with error handling
start_server() {
    local server_module=$1
    local server_name=$2
    local log_file="/tmp/${server_name}.log"
    
    log_message "Starting $server_name on $server_module"
    python -m "$server_module" > "$log_file" 2>&1 &
    local pid=$!
    
    # Check if process is running after a short delay
    sleep 2
    if ps -p $pid > /dev/null; then
        log_message "✅ $server_name started successfully (PID: $pid)"
    else
        log_message "❌ Failed to start $server_name. Check logs: $log_file"
        cat "$log_file"
    fi
}

# Start individual servers
start_server "mcp_servers.index_server" "IndexServer"
start_server "mcp_servers.recommendation_server" "RecommendationServer"
start_server "mcp_servers.trading_server" "TradingServer"

# Wait longer for servers to initialize (Azure cold starts can be slow)
log_message "Waiting for servers to initialize..."
sleep 10

# Start the main application
log_message "Starting main FastAPI application..."

# Use the PORT environment variable as required by Azure
if [ "$APP_ENV" = "production" ]; then
    log_message "Starting in PRODUCTION mode with $MAX_WORKERS workers"
    # Use the PORT environment variable (Azure expects this)
    exec uvicorn main:app --host 0.0.0.0 --port "$PORT" --workers "$MAX_WORKERS" --timeout-keep-alive "$TIMEOUT"
else
    log_message "Starting in DEVELOPMENT mode with hot reload"
    exec uvicorn main:app --host 0.0.0.0 --port "$PORT" --reload
fi