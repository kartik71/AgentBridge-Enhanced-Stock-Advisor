"""
Server runner script for IndexServer API
"""

import uvicorn
import asyncio
from pathlib import Path
import sys

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from api.index_server import app

def run_server():
    """Run the IndexServer API with uvicorn"""
    print("🚀 Starting IndexServer API...")
    print("📊 Server will generate synthetic market data on startup")
    print("🌐 API Documentation available at: http://localhost:8001/docs")
    print("📈 Health check available at: http://localhost:8001/health")
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8001,
        reload=True,
        log_level="info",
        access_log=True
    )

if __name__ == "__main__":
    run_server()