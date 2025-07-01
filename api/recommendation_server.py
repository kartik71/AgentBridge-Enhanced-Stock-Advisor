"""
FastAPI RecommendationServer - Portfolio Suggestions API
Provides AI-powered portfolio recommendations based on user profiles and market conditions
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
from pydantic import BaseModel, Field
import uvicorn

# Pydantic models for request/response validation
class UserProfile(BaseModel):
    user_id: str = Field(..., description="Unique user identifier")
    budget: float = Field(..., ge=1000, le=10000000, description="Investment budget in USD")
    timeframe: str = Field(..., description="Investment timeframe: Short, Medium, Long")
    risk_level: str = Field(..., description="Risk tolerance: Low, Medium, High")
    goals: str = Field(default="Growth", description="Investment goals")
    sectors: Optional[List[str]] = Field(default=None, description="Preferred sectors")
    exclude_sectors: Optional[List[str]] = Field(default=None, description="Sectors to exclude")

class RecommendationRequest(BaseModel):
    user_profile: UserProfile
    max_recommendations: int = Field(default=5, ge=1, le=20, description="Maximum number of recommendations")
    include_reasoning: bool = Field(default=True, description="Include AI reasoning for recommendations")

class StockRecommendation(BaseModel):
    symbol: str
    action: str  # BUY, SELL, HOLD
    current_price: float
    target_price: float
    confidence: int  # 0-100
    allocation_percent: float
    investment_amount: float
    shares: int
    reason: str
    risk_level: str
    sector: str
    pe_ratio: Optional[float] = None
    dividend_yield: Optional[float] = None
    analyst_rating: Optional[str] = None

# Initialize FastAPI app
app = FastAPI(
    title="RecommendationServer API",
    description="AI-Powered Portfolio Recommendation Engine",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Data storage and AI engine
class RecommendationEngine:
    def __init__(self):
        self.stock_universe = {}
        self.user_profiles = {}
        self.recommendation_cache = {}
        self.data_dir = Path("data")
        self.data_dir.mkdir(exist_ok=True)
        
    async def initialize(self):
        """Initialize recommendation engine with stock universe"""
        await self.load_stock_universe()
        await self.load_user_profiles()
        
    async def load_stock_universe(self):
        """Load comprehensive stock universe for recommendations"""
        self.stock_universe = {
            # Technology Stocks
            "AAPL": {
                "name": "Apple Inc.",
                "sector": "Technology",
                "current_price": 192.35,
                "pe_ratio": 28.5,
                "dividend_yield": 0.44,
                "market_cap": 3000,
                "risk_level": "Low",
                "analyst_rating": "BUY",
                "growth_score": 8.5,
                "value_score": 6.2,
                "momentum_score": 7.8
            },
            "MSFT": {
                "name": "Microsoft Corporation",
                "sector": "Technology",
                "current_price": 398.75,
                "pe_ratio": 32.1,
                "dividend_yield": 0.68,
                "market_cap": 2900,
                "risk_level": "Low",
                "analyst_rating": "BUY",
                "growth_score": 8.8,
                "value_score": 6.5,
                "momentum_score": 8.2
            },
            "GOOGL": {
                "name": "Alphabet Inc.",
                "sector": "Technology",
                "current_price": 142.50,
                "pe_ratio": 25.8,
                "dividend_yield": 0.0,
                "market_cap": 1800,
                "risk_level": "Medium",
                "analyst_rating": "BUY",
                "growth_score": 8.0,
                "value_score": 7.2,
                "momentum_score": 6.8
            },
            "NVDA": {
                "name": "NVIDIA Corporation",
                "sector": "Technology",
                "current_price": 465.20,
                "pe_ratio": 65.2,
                "dividend_yield": 0.03,
                "market_cap": 1100,
                "risk_level": "High",
                "analyst_rating": "HOLD",
                "growth_score": 9.5,
                "value_score": 4.2,
                "momentum_score": 9.2
            },
            "TSLA": {
                "name": "Tesla, Inc.",
                "sector": "Automotive",
                "current_price": 198.50,
                "pe_ratio": 58.9,
                "dividend_yield": 0.0,
                "market_cap": 630,
                "risk_level": "High",
                "analyst_rating": "SELL",
                "growth_score": 7.5,
                "value_score": 3.8,
                "momentum_score": 5.2
            },
            # Healthcare Stocks
            "JNJ": {
                "name": "Johnson & Johnson",
                "sector": "Healthcare",
                "current_price": 165.20,
                "pe_ratio": 15.2,
                "dividend_yield": 2.98,
                "market_cap": 435,
                "risk_level": "Low",
                "analyst_rating": "BUY",
                "growth_score": 6.5,
                "value_score": 8.2,
                "momentum_score": 6.8
            },
            "PFE": {
                "name": "Pfizer Inc.",
                "sector": "Healthcare",
                "current_price": 28.90,
                "pe_ratio": 12.5,
                "dividend_yield": 5.85,
                "market_cap": 162,
                "risk_level": "Medium",
                "analyst_rating": "HOLD",
                "growth_score": 5.2,
                "value_score": 8.8,
                "momentum_score": 4.5
            },
            # Financial Stocks
            "JPM": {
                "name": "JPMorgan Chase & Co.",
                "sector": "Finance",
                "current_price": 168.45,
                "pe_ratio": 11.2,
                "dividend_yield": 2.35,
                "market_cap": 485,
                "risk_level": "Medium",
                "analyst_rating": "BUY",
                "growth_score": 7.2,
                "value_score": 7.8,
                "momentum_score": 7.5
            },
            "BAC": {
                "name": "Bank of America Corp",
                "sector": "Finance",
                "current_price": 32.15,
                "pe_ratio": 12.8,
                "dividend_yield": 2.85,
                "market_cap": 258,
                "risk_level": "Medium",
                "analyst_rating": "BUY",
                "growth_score": 6.8,
                "value_score": 8.0,
                "momentum_score": 7.2
            },
            # Consumer Staples
            "KO": {
                "name": "The Coca-Cola Company",
                "sector": "Consumer Staples",
                "current_price": 58.75,
                "pe_ratio": 24.5,
                "dividend_yield": 3.12,
                "market_cap": 254,
                "risk_level": "Low",
                "analyst_rating": "HOLD",
                "growth_score": 4.5,
                "value_score": 7.5,
                "momentum_score": 5.8
            }
        }
        
    async def load_user_profiles(self):
        """Load user profiles from storage"""
        try:
            profile_file = self.data_dir / "user_profiles.json"
            if profile_file.exists():
                with open(profile_file, 'r') as f:
                    self.user_profiles = json.load(f)
        except Exception as e:
            print(f"Warning: Could not load user profiles: {e}")
            self.user_profiles = {}
    
    async def save_user_profile(self, profile: UserProfile):
        """Save user profile to storage"""
        try:
            self.user_profiles[profile.user_id] = profile.dict()
            profile_file = self.data_dir / "user_profiles.json"
            with open(profile_file, 'w') as f:
                json.dump(self.user_profiles, f, indent=2)
        except Exception as e:
            print(f"Warning: Could not save user profile: {e}")
    
    async def generate_recommendations(self, request: RecommendationRequest) -> List[StockRecommendation]:
        """Generate AI-powered portfolio recommendations"""
        profile = request.user_profile
        
        # Save user profile
        await self.save_user_profile(profile)
        
        # Filter stocks based on user preferences
        filtered_stocks = await self._filter_stocks(profile)
        
        # Score and rank stocks
        scored_stocks = await self._score_stocks(filtered_stocks, profile)
        
        # Select top recommendations
        top_stocks = scored_stocks[:request.max_recommendations]
        
        # Generate allocations
        recommendations = await self._generate_allocations(top_stocks, profile)
        
        return recommendations
    
    async def _filter_stocks(self, profile: UserProfile) -> List[Dict]:
        """Filter stocks based on user preferences"""
        filtered = []
        
        for symbol, stock_data in self.stock_universe.items():
            # Filter by preferred sectors
            if profile.sectors and stock_data["sector"] not in profile.sectors:
                continue
                
            # Exclude unwanted sectors
            if profile.exclude_sectors and stock_data["sector"] in profile.exclude_sectors:
                continue
            
            # Filter by risk level
            if profile.risk_level == "Low" and stock_data["risk_level"] == "High":
                continue
            elif profile.risk_level == "High" and stock_data["risk_level"] == "Low":
                # Allow but with lower weight
                pass
            
            stock_data["symbol"] = symbol
            filtered.append(stock_data)
        
        return filtered
    
    async def _score_stocks(self, stocks: List[Dict], profile: UserProfile) -> List[Dict]:
        """Score stocks based on user profile and market conditions"""
        for stock in stocks:
            score = 0
            
            # Base scoring factors
            growth_weight = 0.4 if profile.goals in ["Growth", "Aggressive Growth"] else 0.2
            value_weight = 0.3 if profile.goals in ["Value", "Income"] else 0.2
            momentum_weight = 0.3 if profile.timeframe == "Short" else 0.1
            
            # Calculate composite score
            score += stock["growth_score"] * growth_weight
            score += stock["value_score"] * value_weight
            score += stock["momentum_score"] * momentum_weight
            
            # Risk adjustment
            if profile.risk_level == "Low":
                if stock["risk_level"] == "Low":
                    score *= 1.2
                elif stock["risk_level"] == "High":
                    score *= 0.7
            elif profile.risk_level == "High":
                if stock["risk_level"] == "High":
                    score *= 1.3
                elif stock["risk_level"] == "Low":
                    score *= 0.8
            
            # Timeframe adjustment
            if profile.timeframe == "Long":
                score += stock["dividend_yield"] * 0.5
            elif profile.timeframe == "Short":
                score += stock["momentum_score"] * 0.3
            
            # Add some randomness for variety
            score += random.uniform(-0.5, 0.5)
            
            stock["ai_score"] = round(score, 2)
        
        # Sort by AI score (descending)
        return sorted(stocks, key=lambda x: x["ai_score"], reverse=True)
    
    async def _generate_allocations(self, stocks: List[Dict], profile: UserProfile) -> List[StockRecommendation]:
        """Generate portfolio allocations and recommendations"""
        recommendations = []
        total_score = sum(stock["ai_score"] for stock in stocks)
        
        for i, stock in enumerate(stocks):
            # Calculate base allocation
            if total_score > 0:
                base_allocation = (stock["ai_score"] / total_score) * 100
            else:
                base_allocation = 100 / len(stocks)
            
            # Ensure reasonable allocation bounds
            allocation_percent = max(5, min(35, base_allocation))
            
            # Calculate investment amounts
            investment_amount = (allocation_percent / 100) * profile.budget
            shares = int(investment_amount / stock["current_price"])
            actual_investment = shares * stock["current_price"]
            
            # Generate target price (5-25% upside based on score)
            upside_potential = 0.05 + (stock["ai_score"] / 10) * 0.20
            target_price = stock["current_price"] * (1 + upside_potential)
            
            # Determine action
            if stock["analyst_rating"] == "BUY" and stock["ai_score"] > 7:
                action = "BUY"
            elif stock["analyst_rating"] == "SELL" or stock["ai_score"] < 5:
                action = "SELL"
            else:
                action = "HOLD"
            
            # Generate confidence score
            confidence = min(95, max(60, int(stock["ai_score"] * 10 + random.uniform(-5, 5))))
            
            # Generate reasoning
            reason = await self._generate_reasoning(stock, profile, action)
            
            recommendation = StockRecommendation(
                symbol=stock["symbol"],
                action=action,
                current_price=stock["current_price"],
                target_price=round(target_price, 2),
                confidence=confidence,
                allocation_percent=round(allocation_percent, 1),
                investment_amount=round(actual_investment, 2),
                shares=shares,
                reason=reason,
                risk_level=stock["risk_level"],
                sector=stock["sector"],
                pe_ratio=stock["pe_ratio"],
                dividend_yield=stock["dividend_yield"],
                analyst_rating=stock["analyst_rating"]
            )
            
            recommendations.append(recommendation)
        
        # Normalize allocations to sum to 100%
        total_allocation = sum(rec.allocation_percent for rec in recommendations)
        if total_allocation != 100:
            factor = 100 / total_allocation
            for rec in recommendations:
                rec.allocation_percent = round(rec.allocation_percent * factor, 1)
                rec.investment_amount = round((rec.allocation_percent / 100) * profile.budget, 2)
                rec.shares = int(rec.investment_amount / rec.current_price)
        
        return recommendations
    
    async def _generate_reasoning(self, stock: Dict, profile: UserProfile, action: str) -> str:
        """Generate AI reasoning for recommendation"""
        reasons = []
        
        # Performance-based reasoning
        if stock["growth_score"] > 8:
            reasons.append("strong growth prospects")
        if stock["value_score"] > 7:
            reasons.append("attractive valuation")
        if stock["momentum_score"] > 7:
            reasons.append("positive momentum")
        
        # Risk-based reasoning
        if profile.risk_level == "Low" and stock["risk_level"] == "Low":
            reasons.append("low-risk profile match")
        elif profile.risk_level == "High" and stock["risk_level"] == "High":
            reasons.append("high-growth potential")
        
        # Dividend reasoning
        if stock["dividend_yield"] > 2 and profile.goals == "Income":
            reasons.append(f"{stock['dividend_yield']:.1f}% dividend yield")
        
        # Sector reasoning
        if stock["sector"] == "Technology" and profile.timeframe == "Long":
            reasons.append("technology sector leadership")
        elif stock["sector"] == "Healthcare" and profile.risk_level == "Low":
            reasons.append("defensive healthcare exposure")
        
        # Analyst reasoning
        if stock["analyst_rating"] == "BUY":
            reasons.append("positive analyst consensus")
        
        if not reasons:
            reasons = ["balanced risk-return profile", "portfolio diversification"]
        
        return f"{action.title()} recommendation based on " + ", ".join(reasons[:3])

# Initialize recommendation engine
recommendation_engine = RecommendationEngine()

@app.on_event("startup")
async def startup_event():
    """Initialize recommendation engine on startup"""
    await recommendation_engine.initialize()
    print("🚀 RecommendationServer API started successfully")
    print("🤖 AI recommendation engine initialized")

# API Routes

@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "name": "RecommendationServer API",
        "version": "1.0.0",
        "description": "AI-Powered Portfolio Recommendation Engine",
        "endpoints": {
            "recommendations": "/generate_recommendations",
            "user_profile": "/user_profile/{user_id}",
            "stock_universe": "/stock_universe",
            "health": "/health"
        },
        "status": "operational",
        "stock_universe_size": len(recommendation_engine.stock_universe),
        "user_profiles_loaded": len(recommendation_engine.user_profiles)
    }

@app.post("/generate_recommendations")
async def generate_recommendations(request: RecommendationRequest):
    """
    Generate AI-powered portfolio recommendations
    
    Args:
        request: RecommendationRequest with user profile and preferences
    
    Returns:
        List of stock recommendations with allocations and reasoning
    """
    try:
        recommendations = await recommendation_engine.generate_recommendations(request)
        
        # Calculate portfolio metrics
        total_investment = sum(rec.investment_amount for rec in recommendations)
        avg_confidence = sum(rec.confidence for rec in recommendations) / len(recommendations)
        
        # Risk distribution
        risk_distribution = {}
        for rec in recommendations:
            risk_distribution[rec.risk_level] = risk_distribution.get(rec.risk_level, 0) + rec.allocation_percent
        
        # Sector distribution
        sector_distribution = {}
        for rec in recommendations:
            sector_distribution[rec.sector] = sector_distribution.get(rec.sector, 0) + rec.allocation_percent
        
        return JSONResponse(
            status_code=200,
            content={
                "status": "success",
                "recommendations": [rec.dict() for rec in recommendations],
                "portfolio_metrics": {
                    "total_recommendations": len(recommendations),
                    "total_investment": round(total_investment, 2),
                    "cash_remaining": round(request.user_profile.budget - total_investment, 2),
                    "average_confidence": round(avg_confidence, 1),
                    "risk_distribution": risk_distribution,
                    "sector_distribution": sector_distribution,
                    "expected_return": round(sum(
                        (rec.allocation_percent / 100) * 
                        ((rec.target_price - rec.current_price) / rec.current_price * 100)
                        for rec in recommendations
                    ), 2)
                },
                "user_profile": request.user_profile.dict(),
                "generated_at": datetime.now().isoformat()
            }
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating recommendations: {str(e)}")

@app.get("/user_profile/{user_id}")
async def get_user_profile(user_id: str):
    """Get stored user profile"""
    if user_id not in recommendation_engine.user_profiles:
        raise HTTPException(status_code=404, detail=f"User profile '{user_id}' not found")
    
    return JSONResponse(
        status_code=200,
        content={
            "status": "success",
            "user_profile": recommendation_engine.user_profiles[user_id],
            "timestamp": datetime.now().isoformat()
        }
    )

@app.get("/stock_universe")
async def get_stock_universe():
    """Get available stock universe for recommendations"""
    return JSONResponse(
        status_code=200,
        content={
            "status": "success",
            "stock_universe": recommendation_engine.stock_universe,
            "total_stocks": len(recommendation_engine.stock_universe),
            "sectors": list(set(stock["sector"] for stock in recommendation_engine.stock_universe.values())),
            "timestamp": datetime.now().isoformat()
        }
    )

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "RecommendationServer API",
        "version": "1.0.0",
        "uptime": datetime.now().isoformat(),
        "engine_status": {
            "stock_universe_loaded": len(recommendation_engine.stock_universe) > 0,
            "user_profiles_count": len(recommendation_engine.user_profiles),
            "cache_size": len(recommendation_engine.recommendation_cache)
        }
    }

# Run server
if __name__ == "__main__":
    print("🚀 Starting RecommendationServer API...")
    print("🤖 Initializing AI recommendation engine...")
    
    uvicorn.run(
        "recommendation_server:app",
        host="0.0.0.0",
        port=8002,
        reload=True,
        log_level="info"
    )