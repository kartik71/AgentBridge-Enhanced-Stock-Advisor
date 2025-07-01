"""
Main entry point for the Stock Advisor Application
Serves the web frontend and starts API servers
"""

import os
from fastapi import FastAPI, HTTPException, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from pathlib import Path
import threading
import sys
import uvicorn

# Import and run API servers in background threads
from api.index_server import app as index_app
from api.recommendation_server import app as recommendation_app  
from api.trading_server import app as trading_app
from api.compliance_server import app as compliance_app

# Create FastAPI app
app = FastAPI(
    title="Stock Advisor Application",
    description="Enhanced Stock Advisor with Agent Bridge",
    version="1.0.0"
)

# Define paths
STATIC_DIR = Path(__file__).parent / "static"
if not STATIC_DIR.exists():
    os.makedirs(STATIC_DIR, exist_ok=True)

# Mount static files
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

# Health check endpoint
@app.get("/health")
async def health_check():
    return {"status": "healthy", "message": "Stock Advisor Application is running"}

# Serve index.html for all other routes to support SPA routing
@app.get("/{full_path:path}")
async def serve_app(full_path: str):
    # If path points to a static file that exists, serve it
    requested_path = STATIC_DIR / full_path
    if requested_path.exists() and requested_path.is_file():
        return FileResponse(requested_path)
    
    # Otherwise serve index.html for SPA routing
    index_path = STATIC_DIR / "index.html"
    if index_path.exists():
        return FileResponse(index_path)
    else:
        # Fallback if index.html doesn't exist
        return JSONResponse(
            status_code=200,
            content={
                "message": "Welcome to Stock Advisor API",
                "endpoints": {
                    "index_api": "http://localhost:8001",
                    "recommendation_api": "http://localhost:8002",
                    "trading_api": "http://localhost:8003",
                    "compliance_api": "http://localhost:8004"
                }
            }
        )

# Error handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={"message": f"An error occurred: {str(exc)}"}
    )

def run_server(app_instance, host, port):
    """Run a FastAPI server in a separate thread"""
    uvicorn.run(app_instance, host=host, port=port, log_level="info")

def start_api_servers():
    """Start all API servers in background threads"""
    # Start the API servers in separate threads
    threading.Thread(target=run_server, args=(index_app, "0.0.0.0", 8001), daemon=True).start()
    threading.Thread(target=run_server, args=(recommendation_app, "0.0.0.0", 8002), daemon=True).start()
    threading.Thread(target=run_server, args=(trading_app, "0.0.0.0", 8003), daemon=True).start()
    threading.Thread(target=run_server, args=(compliance_app, "0.0.0.0", 8004), daemon=True).start()

if __name__ == "__main__":
    # Start API servers in background
    start_api_servers()
    
    # Start the main application
    uvicorn.run(app, host="0.0.0.0", port=8000)
else:
    # When imported by uvicorn, start API servers
    start_api_servers()
