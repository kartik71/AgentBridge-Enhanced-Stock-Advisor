"""
Run all FastAPI servers for the Stock Advisor Application
Starts IndexServer, RecommendationServer, TradingServer, and ComplianceServer
"""

import asyncio
import uvicorn
import multiprocessing
from pathlib import Path
import sys

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

def run_index_server():
    """Run IndexServer on port 8001"""
    from api.index_server import app
    uvicorn.run(app, host="0.0.0.0", port=8001, log_level="info")

def run_recommendation_server():
    """Run RecommendationServer on port 8002"""
    from api.recommendation_server import app
    uvicorn.run(app, host="0.0.0.0", port=8002, log_level="info")

def run_trading_server():
    """Run TradingServer on port 8003"""
    from api.trading_server import app
    uvicorn.run(app, host="0.0.0.0", port=8003, log_level="info")

def run_compliance_server():
    """Run ComplianceServer on port 8004"""
    from api.compliance_server import app
    uvicorn.run(app, host="0.0.0.0", port=8004, log_level="info")

def main():
    """Start all servers in parallel"""
    print("🚀 Starting Stock Advisor API Servers...")
    print("=" * 60)
    print("📊 IndexServer:         http://localhost:8001")
    print("🤖 RecommendationServer: http://localhost:8002")
    print("💼 TradingServer:       http://localhost:8003")
    print("🛡️ ComplianceServer:    http://localhost:8004")
    print("=" * 60)
    print("📚 API Documentation:")
    print("   IndexServer:         http://localhost:8001/docs")
    print("   RecommendationServer: http://localhost:8002/docs")
    print("   TradingServer:       http://localhost:8003/docs")
    print("   ComplianceServer:    http://localhost:8004/docs")
    print("=" * 60)
    
    # Create processes for each server
    processes = [
        multiprocessing.Process(target=run_index_server, name="IndexServer"),
        multiprocessing.Process(target=run_recommendation_server, name="RecommendationServer"),
        multiprocessing.Process(target=run_trading_server, name="TradingServer"),
        multiprocessing.Process(target=run_compliance_server, name="ComplianceServer")
    ]
    
    try:
        # Start all processes
        for process in processes:
            process.start()
            print(f"✅ Started {process.name}")
        
        print("\n🎉 All servers started successfully!")
        print("Press Ctrl+C to stop all servers")
        
        # Wait for all processes
        for process in processes:
            process.join()
            
    except KeyboardInterrupt:
        print("\n🛑 Stopping all servers...")
        
        # Terminate all processes
        for process in processes:
            if process.is_alive():
                process.terminate()
                print(f"🔴 Stopped {process.name}")
        
        # Wait for processes to terminate
        for process in processes:
            process.join(timeout=5)
        
        print("✅ All servers stopped successfully")

if __name__ == "__main__":
    # Required for multiprocessing on Windows
    multiprocessing.freeze_support()
    main()