"""
Index Scraper Agent - LangGraph Agent for Market Data Collection
Collects and processes market index data from various sources
"""

import asyncio
import json
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
import sys
import os

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from mcp_servers.index_server import index_server

@dataclass
class AgentState:
    """State management for Index Scraper Agent"""
    status: str = "idle"
    last_update: Optional[datetime] = None
    data_sources: List[str] = None
    error_count: int = 0
    performance_metrics: Dict[str, float] = None
    
    def __post_init__(self):
        if self.data_sources is None:
            self.data_sources = ["yahoo_finance", "alpha_vantage", "iex_cloud"]
        if self.performance_metrics is None:
            self.performance_metrics = {"success_rate": 0.0, "avg_response_time": 0.0}

class IndexScraperAgent:
    """LangGraph Agent for scraping market index data"""
    
    def __init__(self, agent_id: str = "index_scraper"):
        self.agent_id = agent_id
        self.name = "Index Scraper"
        self.type = "Data Collection"
        self.version = "1.0.0"
        self.state = AgentState()
        self.mcp_server = index_server
        
    async def initialize(self):
        """Initialize the agent and its MCP server connection"""
        try:
            await self.mcp_server.initialize()
            self.state.status = "connected"
            print(f"[{self.name}] Agent initialized successfully")
            return True
        except Exception as e:
            self.state.status = "error"
            self.state.error_count += 1
            print(f"[{self.name}] Initialization failed: {e}")
            return False
    
    async def collect_market_data(self) -> Dict[str, Any]:
        """Main data collection workflow"""
        try:
            self.state.status = "processing"
            start_time = datetime.now()
            
            # Collect current market indices
            current_data = await self.mcp_server.get_current_indices()
            
            # Collect historical data for trend analysis
            historical_data = {}
            for index in ['S&P 500', 'DOW', 'NASDAQ', 'RUSSELL', 'VIX']:
                hist_data = await self.mcp_server.get_historical_data(index, days=30)
                historical_data[index] = hist_data
            
            # Calculate performance metrics
            end_time = datetime.now()
            response_time = (end_time - start_time).total_seconds()
            
            self.state.performance_metrics["avg_response_time"] = response_time
            self.state.performance_metrics["success_rate"] = 100.0  # Successful collection
            self.state.last_update = end_time
            self.state.status = "connected"
            
            result = {
                "status": "success",
                "agent_id": self.agent_id,
                "timestamp": end_time.isoformat(),
                "current_data": current_data,
                "historical_data": historical_data,
                "performance": {
                    "response_time": response_time,
                    "data_points_collected": len(current_data.get("data", [])),
                    "sources_active": len(self.state.data_sources)
                }
            }
            
            return result
            
        except Exception as e:
            self.state.status = "error"
            self.state.error_count += 1
            self.state.performance_metrics["success_rate"] = max(0, 
                self.state.performance_metrics["success_rate"] - 10)
            
            return {
                "status": "error",
                "agent_id": self.agent_id,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    async def analyze_market_trends(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze market trends from collected data"""
        try:
            trends = {}
            current_indices = data.get("current_data", {}).get("data", [])
            
            for index_data in current_indices:
                symbol = index_data["symbol"]
                change_percent = index_data["changePercent"]
                
                # Simple trend analysis
                if change_percent > 1.0:
                    trend = "strong_bullish"
                elif change_percent > 0.2:
                    trend = "bullish"
                elif change_percent < -1.0:
                    trend = "strong_bearish"
                elif change_percent < -0.2:
                    trend = "bearish"
                else:
                    trend = "neutral"
                
                trends[symbol] = {
                    "trend": trend,
                    "change_percent": change_percent,
                    "confidence": min(95, abs(change_percent) * 20 + 60)
                }
            
            return {
                "status": "success",
                "trends": trends,
                "analysis_timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    async def get_agent_status(self) -> Dict[str, Any]:
        """Get current agent status and metrics"""
        return {
            "agent_id": self.agent_id,
            "name": self.name,
            "type": self.type,
            "version": self.version,
            "status": self.state.status,
            "last_update": self.state.last_update.isoformat() if self.state.last_update else None,
            "error_count": self.state.error_count,
            "performance_metrics": self.state.performance_metrics,
            "data_sources": self.state.data_sources,
            "mcp_server_status": await self.mcp_server.get_server_status()
        }
    
    async def run_continuous_collection(self, interval_seconds: int = 30):
        """Run continuous data collection at specified intervals"""
        print(f"[{self.name}] Starting continuous collection (interval: {interval_seconds}s)")
        
        while True:
            try:
                result = await self.collect_market_data()
                if result["status"] == "success":
                    print(f"[{self.name}] Data collection successful at {result['timestamp']}")
                else:
                    print(f"[{self.name}] Data collection failed: {result.get('error', 'Unknown error')}")
                
                await asyncio.sleep(interval_seconds)
                
            except KeyboardInterrupt:
                print(f"[{self.name}] Stopping continuous collection")
                break
            except Exception as e:
                print(f"[{self.name}] Unexpected error in continuous collection: {e}")
                await asyncio.sleep(interval_seconds)

# Global agent instance
index_scraper_agent = IndexScraperAgent()

# CLI interface for testing
if __name__ == "__main__":
    async def main():
        agent = IndexScraperAgent()
        await agent.initialize()
        
        # Test data collection
        result = await agent.collect_market_data()
        print("Data Collection Result:")
        print(json.dumps(result, indent=2))
        
        # Test trend analysis
        if result["status"] == "success":
            trends = await agent.analyze_market_trends(result)
            print("\nTrend Analysis:")
            print(json.dumps(trends, indent=2))
        
        # Show agent status
        status = await agent.get_agent_status()
        print("\nAgent Status:")
        print(json.dumps(status, indent=2))
    
    asyncio.run(main())