"""
FastAPI IndexServer - Market Data API Server
Provides real-time market index data, stock information, and synthetic fallback data
"""

import json
import random
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from pathlib import Path

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn

# Initialize FastAPI app
app = FastAPI(
    title="IndexServer API",
    description="Market Data API for Stock Advisor Application",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify actual origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Data storage
class DataStore:
    def __init__(self):
        self.indices_data = {}
        self.stocks_data = {}
        self.synthetic_data = {}
        self.last_update = None
        self.data_dir = Path("data")
        self.data_dir.mkdir(exist_ok=True)
        
    async def initialize(self):
        """Initialize data store with synthetic data"""
        await self.generate_synthetic_data()
        await self.save_synthetic_data()
        
    async def generate_synthetic_data(self):
        """Generate comprehensive synthetic market data"""
        current_time = datetime.now()
        
        # Generate index data
        self.indices_data = {
            "S&P 500": {
                "symbol": "SPX",
                "name": "S&P 500",
                "current_price": 4847.88 + random.uniform(-50, 50),
                "change": random.uniform(-30, 30),
                "change_percent": random.uniform(-1.5, 1.5),
                "volume": f"{random.uniform(2.0, 4.0):.1f}B",
                "52_week_high": 4818.62,
                "52_week_low": 3491.58,
                "market_cap": "39.1T",
                "timestamp": current_time.isoformat()
            },
            "NASDAQ": {
                "symbol": "IXIC",
                "name": "NASDAQ Composite",
                "current_price": 15181.92 + random.uniform(-100, 100),
                "change": random.uniform(-80, 80),
                "change_percent": random.uniform(-2.0, 2.0),
                "volume": f"{random.uniform(2.5, 4.5):.1f}B",
                "52_week_high": 16057.44,
                "52_week_low": 10088.83,
                "market_cap": "18.7T",
                "timestamp": current_time.isoformat()
            },
            "DOW": {
                "symbol": "DJI",
                "name": "Dow Jones Industrial Average",
                "current_price": 37753.31 + random.uniform(-200, 200),
                "change": random.uniform(-150, 150),
                "change_percent": random.uniform(-1.0, 1.0),
                "volume": f"{random.uniform(1.5, 2.5):.1f}B",
                "52_week_high": 37952.54,
                "52_week_low": 28660.94,
                "market_cap": "13.2T",
                "timestamp": current_time.isoformat()
            },
            "RUSSELL 2000": {
                "symbol": "RUT",
                "name": "Russell 2000",
                "current_price": 2089.44 + random.uniform(-50, 50),
                "change": random.uniform(-25, 25),
                "change_percent": random.uniform(-1.2, 1.2),
                "volume": f"{random.uniform(1.0, 2.0):.1f}B",
                "52_week_high": 2442.74,
                "52_week_low": 1636.93,
                "market_cap": "1.4T",
                "timestamp": current_time.isoformat()
            },
            "VIX": {
                "symbol": "VIX",
                "name": "CBOE Volatility Index",
                "current_price": 13.22 + random.uniform(-2, 5),
                "change": random.uniform(-1, 2),
                "change_percent": random.uniform(-8, 15),
                "volume": f"{random.uniform(0.5, 1.5):.1f}B",
                "52_week_high": 65.73,
                "52_week_low": 12.07,
                "market_cap": "N/A",
                "timestamp": current_time.isoformat()
            }
        }
        
        # Generate stocks data for each index
        self.stocks_data = {
            "S&P 500": await self._generate_sp500_stocks(),
            "NASDAQ": await self._generate_nasdaq_stocks(),
            "DOW": await self._generate_dow_stocks(),
            "RUSSELL 2000": await self._generate_russell_stocks(),
            "VIX": []  # VIX doesn't have constituent stocks
        }
        
        # Create comprehensive synthetic dataset
        self.synthetic_data = {
            "indices": self.indices_data,
            "stocks": self.stocks_data,
            "market_sentiment": {
                "fear_greed_index": random.randint(20, 80),
                "vix_level": self.indices_data["VIX"]["current_price"],
                "put_call_ratio": random.uniform(0.7, 1.3),
                "insider_buying": random.choice(["Low", "Moderate", "High"]),
                "analyst_sentiment": random.choice(["Bearish", "Neutral", "Bullish"]),
                "market_breadth": {
                    "advancing_stocks": random.randint(1800, 2800),
                    "declining_stocks": random.randint(1200, 2200),
                    "unchanged_stocks": random.randint(200, 400)
                }
            },
            "economic_indicators": {
                "fed_funds_rate": 5.25 + random.uniform(-0.25, 0.25),
                "10_year_treasury": 4.325 + random.uniform(-0.2, 0.2),
                "unemployment_rate": 3.7 + random.uniform(-0.3, 0.3),
                "inflation_rate": 3.2 + random.uniform(-0.5, 0.5),
                "gdp_growth": 2.4 + random.uniform(-0.5, 0.5)
            },
            "metadata": {
                "generated_at": current_time.isoformat(),
                "data_source": "synthetic",
                "update_frequency": "real-time",
                "coverage": "US Markets"
            }
        }
        
        self.last_update = current_time
        
    async def _generate_sp500_stocks(self) -> List[Dict]:
        """Generate S&P 500 constituent stocks with momentum data"""
        sp500_stocks = [
            "AAPL", "MSFT", "GOOGL", "AMZN", "NVDA", "TSLA", "META", "BRK.B", "UNH", "JNJ",
            "V", "PG", "JPM", "HD", "CVX", "MA", "PFE", "ABBV", "BAC", "KO",
            "AVGO", "PEP", "TMO", "COST", "DIS", "ABT", "WMT", "CRM", "LIN", "ACN"
        ]
        
        stocks = []
        for symbol in sp500_stocks:
            momentum_score = random.uniform(-10, 10)
            price = random.uniform(50, 500)
            
            stocks.append({
                "symbol": symbol,
                "name": f"{symbol} Inc.",
                "current_price": round(price, 2),
                "change": round(price * random.uniform(-0.05, 0.05), 2),
                "change_percent": round(random.uniform(-5, 5), 2),
                "volume": f"{random.uniform(1, 50):.1f}M",
                "momentum_score": round(momentum_score, 2),
                "market_cap": f"{random.uniform(10, 3000):.1f}B",
                "sector": random.choice([
                    "Technology", "Healthcare", "Finance", "Consumer Discretionary",
                    "Communication Services", "Industrials", "Consumer Staples", "Energy"
                ]),
                "pe_ratio": round(random.uniform(10, 50), 1),
                "dividend_yield": round(random.uniform(0, 5), 2),
                "52_week_high": round(price * random.uniform(1.1, 1.5), 2),
                "52_week_low": round(price * random.uniform(0.6, 0.9), 2)
            })
        
        # Sort by momentum score (descending)
        return sorted(stocks, key=lambda x: x["momentum_score"], reverse=True)
    
    async def _generate_nasdaq_stocks(self) -> List[Dict]:
        """Generate NASDAQ constituent stocks"""
        nasdaq_stocks = [
            "AAPL", "MSFT", "GOOGL", "AMZN", "NVDA", "TSLA", "META", "AVGO", "COST", "PEP",
            "ADBE", "NFLX", "CMCSA", "INTC", "QCOM", "TXN", "AMGN", "HON", "SBUX", "GILD"
        ]
        
        stocks = []
        for symbol in nasdaq_stocks:
            momentum_score = random.uniform(-8, 12)  # NASDAQ tends to be more volatile
            price = random.uniform(30, 600)
            
            stocks.append({
                "symbol": symbol,
                "name": f"{symbol} Corporation",
                "current_price": round(price, 2),
                "change": round(price * random.uniform(-0.06, 0.06), 2),
                "change_percent": round(random.uniform(-6, 6), 2),
                "volume": f"{random.uniform(5, 100):.1f}M",
                "momentum_score": round(momentum_score, 2),
                "market_cap": f"{random.uniform(5, 2500):.1f}B",
                "sector": random.choice([
                    "Technology", "Communication Services", "Consumer Discretionary",
                    "Healthcare", "Consumer Staples"
                ]),
                "pe_ratio": round(random.uniform(15, 80), 1),
                "dividend_yield": round(random.uniform(0, 3), 2),
                "beta": round(random.uniform(0.8, 2.0), 2)
            })
        
        return sorted(stocks, key=lambda x: x["momentum_score"], reverse=True)
    
    async def _generate_dow_stocks(self) -> List[Dict]:
        """Generate Dow Jones constituent stocks"""
        dow_stocks = [
            "AAPL", "MSFT", "UNH", "GS", "HD", "CAT", "CRM", "V", "BA", "WMT",
            "JNJ", "PG", "JPM", "CVX", "MCD", "DIS", "AXP", "IBM", "MMM", "NKE",
            "KO", "DOW", "VZ", "CSCO", "HON", "INTC", "WBA", "TRV", "MRK", "AMGN"
        ]
        
        stocks = []
        for symbol in dow_stocks:
            momentum_score = random.uniform(-6, 8)  # Dow tends to be more stable
            price = random.uniform(40, 400)
            
            stocks.append({
                "symbol": symbol,
                "name": f"{symbol} Company",
                "current_price": round(price, 2),
                "change": round(price * random.uniform(-0.03, 0.03), 2),
                "change_percent": round(random.uniform(-3, 3), 2),
                "volume": f"{random.uniform(2, 30):.1f}M",
                "momentum_score": round(momentum_score, 2),
                "market_cap": f"{random.uniform(20, 1000):.1f}B",
                "sector": random.choice([
                    "Industrials", "Technology", "Healthcare", "Finance",
                    "Consumer Discretionary", "Consumer Staples", "Energy"
                ]),
                "pe_ratio": round(random.uniform(8, 35), 1),
                "dividend_yield": round(random.uniform(1, 6), 2),
                "dow_weight": round(random.uniform(0.5, 12), 2)
            })
        
        return sorted(stocks, key=lambda x: x["momentum_score"], reverse=True)
    
    async def _generate_russell_stocks(self) -> List[Dict]:
        """Generate Russell 2000 small-cap stocks"""
        russell_stocks = [
            "SMCI", "SOLV", "RYAN", "KENVUE", "TPG", "KVUE", "CAVA", "ARM", "FBIN", "RKLB",
            "PCVX", "IREN", "GDYN", "TMDX", "ALKT", "DOCS", "CRWD", "ZS", "OKTA", "DDOG"
        ]
        
        stocks = []
        for symbol in russell_stocks:
            momentum_score = random.uniform(-15, 15)  # Small caps more volatile
            price = random.uniform(10, 200)
            
            stocks.append({
                "symbol": symbol,
                "name": f"{symbol} Inc.",
                "current_price": round(price, 2),
                "change": round(price * random.uniform(-0.08, 0.08), 2),
                "change_percent": round(random.uniform(-8, 8), 2),
                "volume": f"{random.uniform(0.5, 20):.1f}M",
                "momentum_score": round(momentum_score, 2),
                "market_cap": f"{random.uniform(0.1, 10):.1f}B",
                "sector": random.choice([
                    "Technology", "Healthcare", "Industrials", "Consumer Discretionary",
                    "Real Estate", "Materials", "Energy", "Utilities"
                ]),
                "pe_ratio": round(random.uniform(5, 100), 1),
                "dividend_yield": round(random.uniform(0, 8), 2),
                "float_shares": f"{random.uniform(10, 500):.1f}M"
            })
        
        return sorted(stocks, key=lambda x: x["momentum_score"], reverse=True)
    
    async def save_synthetic_data(self):
        """Save synthetic data to JSON files"""
        try:
            # Save complete synthetic dataset
            with open(self.data_dir / "synthetic_market_data.json", "w") as f:
                json.dump(self.synthetic_data, f, indent=2)
            
            # Save indices data separately
            with open(self.data_dir / "synthetic_indices.json", "w") as f:
                json.dump(self.indices_data, f, indent=2)
            
            # Save stocks data separately
            with open(self.data_dir / "synthetic_stocks.json", "w") as f:
                json.dump(self.stocks_data, f, indent=2)
                
            print(f"✅ Synthetic data saved to {self.data_dir}/")
            
        except Exception as e:
            print(f"❌ Error saving synthetic data: {e}")
    
    async def update_real_time_data(self):
        """Simulate real-time data updates"""
        current_time = datetime.now()
        
        # Update indices with small random movements
        for index_name, index_data in self.indices_data.items():
            if index_name != "VIX":
                price_change = random.uniform(-0.005, 0.005) * index_data["current_price"]
            else:
                price_change = random.uniform(-0.02, 0.02) * index_data["current_price"]
            
            new_price = max(0, index_data["current_price"] + price_change)
            new_change = index_data["change"] + price_change
            new_change_percent = (new_change / (new_price - new_change)) * 100
            
            index_data.update({
                "current_price": round(new_price, 2),
                "change": round(new_change, 2),
                "change_percent": round(new_change_percent, 2),
                "timestamp": current_time.isoformat()
            })
        
        # Update stocks with momentum-based movements
        for index_name, stocks in self.stocks_data.items():
            for stock in stocks:
                momentum_factor = stock["momentum_score"] / 100
                price_change = random.uniform(-0.01, 0.01) * stock["current_price"] * (1 + momentum_factor)
                
                new_price = max(0.01, stock["current_price"] + price_change)
                new_change = stock["change"] + price_change
                new_change_percent = (new_change / (new_price - new_change)) * 100
                
                stock.update({
                    "current_price": round(new_price, 2),
                    "change": round(new_change, 2),
                    "change_percent": round(new_change_percent, 2)
                })
        
        self.last_update = current_time

# Initialize data store
data_store = DataStore()

@app.on_event("startup")
async def startup_event():
    """Initialize data on startup"""
    await data_store.initialize()
    print("🚀 IndexServer API started successfully")
    print("📊 Synthetic market data generated and saved")

# Background task for real-time updates
async def update_data_periodically():
    """Update data every 30 seconds"""
    while True:
        await asyncio.sleep(30)
        await data_store.update_real_time_data()

@app.on_event("startup")
async def start_background_tasks():
    """Start background data updates"""
    asyncio.create_task(update_data_periodically())

# API Routes

@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "name": "IndexServer API",
        "version": "1.0.0",
        "description": "Market Data API for Stock Advisor Application",
        "endpoints": {
            "indices": "/get_indices",
            "stocks": "/get_stocks?index={index_name}&limit={limit}",
            "synthetic_data": "/get_synthetic_data",
            "health": "/health"
        },
        "status": "operational",
        "last_update": data_store.last_update.isoformat() if data_store.last_update else None
    }

@app.get("/get_indices")
async def get_indices():
    """
    Get latest index prices for major market indices
    Returns: S&P 500, NASDAQ, Dow Jones, Russell 2000, VIX
    """
    try:
        return JSONResponse(
            status_code=200,
            content={
                "status": "success",
                "data": list(data_store.indices_data.values()),
                "count": len(data_store.indices_data),
                "last_update": data_store.last_update.isoformat() if data_store.last_update else None,
                "timestamp": datetime.now().isoformat()
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving indices: {str(e)}")

@app.get("/get_stocks")
async def get_stocks(
    index: str = Query(..., description="Index name (S&P 500, NASDAQ, DOW, RUSSELL 2000)"),
    limit: int = Query(10, ge=1, le=50, description="Number of stocks to return (1-50)")
):
    """
    Get top stocks by momentum for a specific index
    
    Args:
        index: Index name (case-insensitive)
        limit: Number of stocks to return (default: 10, max: 50)
    
    Returns:
        List of stocks sorted by momentum score (highest first)
    """
    try:
        # Normalize index name
        index_normalized = index.upper().replace("_", " ")
        
        # Handle common variations
        index_mapping = {
            "SP500": "S&P 500",
            "S&P500": "S&P 500",
            "SPX": "S&P 500",
            "NASDAQ": "NASDAQ",
            "IXIC": "NASDAQ",
            "DOW": "DOW",
            "DOWJONES": "DOW",
            "DJI": "DOW",
            "RUSSELL": "RUSSELL 2000",
            "RUSSELL2000": "RUSSELL 2000",
            "RUT": "RUSSELL 2000",
            "VIX": "VIX"
        }
        
        final_index = index_mapping.get(index_normalized, index_normalized)
        
        if final_index not in data_store.stocks_data:
            available_indices = list(data_store.stocks_data.keys())
            raise HTTPException(
                status_code=404, 
                detail=f"Index '{index}' not found. Available indices: {available_indices}"
            )
        
        stocks = data_store.stocks_data[final_index][:limit]
        
        if not stocks:
            return JSONResponse(
                status_code=200,
                content={
                    "status": "success",
                    "data": [],
                    "message": f"No stocks available for index '{final_index}'",
                    "index": final_index,
                    "count": 0
                }
            )
        
        return JSONResponse(
            status_code=200,
            content={
                "status": "success",
                "data": stocks,
                "index": final_index,
                "count": len(stocks),
                "limit": limit,
                "sorted_by": "momentum_score",
                "last_update": data_store.last_update.isoformat() if data_store.last_update else None,
                "timestamp": datetime.now().isoformat()
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving stocks: {str(e)}")

@app.get("/get_synthetic_data")
async def get_synthetic_data():
    """
    Get complete synthetic fallback dataset
    
    Returns:
        Complete synthetic market data including indices, stocks, sentiment, and economic indicators
    """
    try:
        return JSONResponse(
            status_code=200,
            content={
                "status": "success",
                "data": data_store.synthetic_data,
                "metadata": {
                    "total_indices": len(data_store.indices_data),
                    "total_stock_lists": len(data_store.stocks_data),
                    "total_stocks": sum(len(stocks) for stocks in data_store.stocks_data.values()),
                    "data_source": "synthetic",
                    "generated_at": data_store.synthetic_data["metadata"]["generated_at"],
                    "last_update": data_store.last_update.isoformat() if data_store.last_update else None
                },
                "timestamp": datetime.now().isoformat()
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving synthetic data: {str(e)}")

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "IndexServer API",
        "version": "1.0.0",
        "uptime": datetime.now().isoformat(),
        "data_status": {
            "indices_loaded": len(data_store.indices_data) > 0,
            "stocks_loaded": len(data_store.stocks_data) > 0,
            "last_update": data_store.last_update.isoformat() if data_store.last_update else None
        }
    }

# Additional utility endpoints

@app.get("/indices/{index_name}")
async def get_single_index(index_name: str):
    """Get data for a specific index"""
    index_normalized = index_name.upper().replace("_", " ")
    
    # Handle variations
    if index_normalized in ["SP500", "S&P500", "SPX"]:
        index_normalized = "S&P 500"
    elif index_normalized in ["DOWJONES", "DJI"]:
        index_normalized = "DOW"
    elif index_normalized in ["RUSSELL", "RUSSELL2000", "RUT"]:
        index_normalized = "RUSSELL 2000"
    
    if index_normalized not in data_store.indices_data:
        raise HTTPException(status_code=404, detail=f"Index '{index_name}' not found")
    
    return JSONResponse(
        status_code=200,
        content={
            "status": "success",
            "data": data_store.indices_data[index_normalized],
            "timestamp": datetime.now().isoformat()
        }
    )

@app.get("/market_sentiment")
async def get_market_sentiment():
    """Get current market sentiment indicators"""
    return JSONResponse(
        status_code=200,
        content={
            "status": "success",
            "data": data_store.synthetic_data["market_sentiment"],
            "timestamp": datetime.now().isoformat()
        }
    )

@app.get("/economic_indicators")
async def get_economic_indicators():
    """Get current economic indicators"""
    return JSONResponse(
        status_code=200,
        content={
            "status": "success",
            "data": data_store.synthetic_data["economic_indicators"],
            "timestamp": datetime.now().isoformat()
        }
    )

# Error handlers
@app.exception_handler(404)
async def not_found_handler(request, exc):
    return JSONResponse(
        status_code=404,
        content={
            "status": "error",
            "error": "Not Found",
            "message": "The requested resource was not found",
            "timestamp": datetime.now().isoformat()
        }
    )

@app.exception_handler(500)
async def internal_error_handler(request, exc):
    return JSONResponse(
        status_code=500,
        content={
            "status": "error",
            "error": "Internal Server Error",
            "message": "An internal server error occurred",
            "timestamp": datetime.now().isoformat()
        }
    )

# Run server
if __name__ == "__main__":
    print("🚀 Starting IndexServer API...")
    print("📊 Generating synthetic market data...")
    
    uvicorn.run(
        "index_server:app",
        host="0.0.0.0",
        port=8001,
        reload=True,
        log_level="info",
        access_log=True
    )