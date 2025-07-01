"""
Index Server - MCP Server for Market Index Data
Provides real-time and historical market index data with synthetic data generation
"""

import json
import asyncio
import random
from datetime import datetime, timedelta
from typing import Dict, List, Any
import os

class IndexServer:
    def __init__(self):
        self.name = "index_server"
        self.version = "1.0.0"
        self.description = "Market Index Data Provider"
        self.data_file = "data/synthetic_market_data.json"
        self.cache = {}
        self.last_update = None
        
    async def initialize(self):
        """Initialize the server and load data"""
        await self.load_market_data()
        print(f"[{self.name}] Server initialized successfully")
        
    async def load_market_data(self):
        """Load market data from JSON file"""
        try:
            if os.path.exists(self.data_file):
                with open(self.data_file, 'r') as file:
                    self.cache = json.load(file)
            else:
                # Generate synthetic data if file doesn't exist
                await self.generate_synthetic_data()
        except Exception as e:
            print(f"[{self.name}] Error loading data: {e}")
            await self.generate_synthetic_data()
    
    async def generate_synthetic_data(self):
        """Generate comprehensive synthetic market data"""
        synthetic_data = {
            "indices": {
                "SP500": {
                    "symbol": "S&P 500",
                    "current_price": 4847.88,
                    "change": random.uniform(-50, 50),
                    "change_percent": random.uniform(-1.5, 1.5),
                    "volume": f"{random.uniform(2.0, 4.0):.1f}B",
                    "52_week_high": 4818.62,
                    "52_week_low": 3491.58
                },
                "NASDAQ": {
                    "symbol": "NASDAQ",
                    "current_price": 15181.92,
                    "change": random.uniform(-100, 100),
                    "change_percent": random.uniform(-2.0, 2.0),
                    "volume": f"{random.uniform(2.5, 4.5):.1f}B",
                    "52_week_high": 16057.44,
                    "52_week_low": 10088.83
                },
                "DOW": {
                    "symbol": "DOW",
                    "current_price": 37753.31,
                    "change": random.uniform(-200, 200),
                    "change_percent": random.uniform(-1.0, 1.0),
                    "volume": f"{random.uniform(1.5, 2.5):.1f}B",
                    "52_week_high": 37952.54,
                    "52_week_low": 28660.94
                }
            },
            "market_sentiment": {
                "fear_greed_index": random.randint(20, 80),
                "vix": random.uniform(12, 25),
                "put_call_ratio": random.uniform(0.7, 1.2),
                "insider_buying": random.choice(["Low", "Moderate", "High"]),
                "analyst_sentiment": random.choice(["Bearish", "Neutral", "Bullish"])
            }
        }
        
        self.cache = synthetic_data
        
    async def get_current_indices(self) -> Dict[str, Any]:
        """Get current market index data with real-time simulation"""
        current_time = datetime.now()
        
        # Simulate real-time updates every 30 seconds
        if (self.last_update is None or 
            (current_time - self.last_update).seconds > 30):
            
            # Update prices with small random movements
            for index_key, index_data in self.cache.get("indices", {}).items():
                price_change = random.uniform(-10, 10)
                percent_change = random.uniform(-0.5, 0.5)
                
                index_data["change"] = round(index_data.get("change", 0) + price_change * 0.1, 2)
                index_data["change_percent"] = round(index_data.get("change_percent", 0) + percent_change, 2)
                index_data["current_price"] = round(index_data["current_price"] + price_change, 2)
                index_data["timestamp"] = current_time.isoformat()
            
            self.last_update = current_time
            
        return {
            'status': 'success',
            'data': list(self.cache.get("indices", {}).values()),
            'timestamp': current_time.isoformat(),
            'market_sentiment': self.cache.get("market_sentiment", {})
        }
    
    async def get_historical_data(self, symbol: str, days: int = 30) -> Dict[str, Any]:
        """Generate historical data for a specific index"""
        historical_data = []
        base_price = 4847.88 if symbol == "S&P 500" else 15181.92 if symbol == "NASDAQ" else 37753.31
        
        for i in range(days):
            date = (datetime.now() - timedelta(days=i)).strftime('%Y-%m-%d')
            price_change = random.uniform(-0.02, 0.02) * base_price
            price = base_price + price_change
            
            historical_data.append({
                'date': date,
                'symbol': symbol,
                'price': round(price, 2),
                'volume': random.randint(1000000, 5000000),
                'change': round(price_change, 2),
                'change_percent': round((price_change / base_price) * 100, 2)
            })
        
        return {
            'status': 'success',
            'symbol': symbol,
            'data': historical_data,
            'count': len(historical_data)
        }
    
    async def get_market_sentiment(self) -> Dict[str, Any]:
        """Get current market sentiment indicators"""
        return {
            'status': 'success',
            'sentiment': self.cache.get("market_sentiment", {}),
            'timestamp': datetime.now().isoformat()
        }
    
    async def get_server_status(self) -> Dict[str, Any]:
        """Get server health status"""
        return {
            'name': self.name,
            'version': self.version,
            'status': 'healthy',
            'uptime': datetime.now().isoformat(),
            'cache_size': len(self.cache),
            'last_update': self.last_update.isoformat() if self.last_update else None
        }

# Global server instance
index_server = IndexServer()