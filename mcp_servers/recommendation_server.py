"""
Recommendation Server - MCP Server for Portfolio Recommendations
Provides AI-powered stock recommendations based on user profiles and market conditions
"""

import json
import random
from datetime import datetime, timedelta
from typing import Dict, List, Any
import os

class RecommendationServer:
    def __init__(self):
        self.name = "recommendation_server"
        self.version = "1.0.0"
        self.description = "AI Portfolio Recommendation Engine"
        self.user_profiles_file = "data/user_profiles.json"
        self.market_data_file = "data/synthetic_market_data.json"
        self.recommendations_cache = {}
        self.user_profiles = {}
        
    async def initialize(self):
        """Initialize the recommendation server"""
        await self.load_user_profiles()
        await self.load_market_data()
        print(f"[{self.name}] Server initialized successfully")
        
    async def load_user_profiles(self):
        """Load user profiles from JSON file"""
        try:
            if os.path.exists(self.user_profiles_file):
                with open(self.user_profiles_file, 'r') as file:
                    self.user_profiles = json.load(file)
            else:
                self.user_profiles = await self.create_default_profiles()
                await self.save_user_profiles()
        except Exception as e:
            print(f"[{self.name}] Error loading user profiles: {e}")
            self.user_profiles = await self.create_default_profiles()
    
    async def load_market_data(self):
        """Load market data for recommendations"""
        try:
            if os.path.exists(self.market_data_file):
                with open(self.market_data_file, 'r') as file:
                    self.market_data = json.load(file)
            else:
                self.market_data = {}
        except Exception as e:
            print(f"[{self.name}] Error loading market data: {e}")
            self.market_data = {}
    
    async def create_default_profiles(self) -> Dict[str, Any]:
        """Create default user profiles"""
        return {
            "default_user": {
                "user_id": "default_user",
                "name": "Demo User",
                "risk_tolerance": "medium",
                "investment_horizon": "medium",
                "budget": 50000,
                "goals": "Growth",
                "preferences": {
                    "sectors": ["technology", "healthcare", "finance"],
                    "exclude_sectors": ["tobacco", "gambling"],
                    "esg_focused": True,
                    "dividend_preference": False
                },
                "created_at": datetime.now().isoformat()
            }
        }
    
    async def save_user_profiles(self):
        """Save user profiles to JSON file"""
        try:
            os.makedirs(os.path.dirname(self.user_profiles_file), exist_ok=True)
            with open(self.user_profiles_file, 'w') as file:
                json.dump(self.user_profiles, file, indent=2)
        except Exception as e:
            print(f"[{self.name}] Error saving user profiles: {e}")
    
    async def generate_recommendations(self, user_config: Dict[str, Any]) -> Dict[str, Any]:
        """Generate portfolio recommendations based on user configuration"""
        
        # Enhanced stock pool with more realistic data
        stock_pool = [
            {
                "symbol": "AAPL", "sector": "Technology", "risk": "Low",
                "current_price": 192.35, "analyst_rating": "BUY",
                "pe_ratio": 28.5, "dividend_yield": 0.44
            },
            {
                "symbol": "MSFT", "sector": "Technology", "risk": "Low",
                "current_price": 398.75, "analyst_rating": "BUY",
                "pe_ratio": 32.1, "dividend_yield": 0.68
            },
            {
                "symbol": "GOOGL", "sector": "Technology", "risk": "Medium",
                "current_price": 142.50, "analyst_rating": "BUY",
                "pe_ratio": 25.8, "dividend_yield": 0.00
            },
            {
                "symbol": "NVDA", "sector": "Technology", "risk": "High",
                "current_price": 465.20, "analyst_rating": "HOLD",
                "pe_ratio": 65.2, "dividend_yield": 0.03
            },
            {
                "symbol": "TSLA", "sector": "Automotive", "risk": "High",
                "current_price": 198.50, "analyst_rating": "SELL",
                "pe_ratio": 58.9, "dividend_yield": 0.00
            },
            {
                "symbol": "JNJ", "sector": "Healthcare", "risk": "Low",
                "current_price": 165.20, "analyst_rating": "BUY",
                "pe_ratio": 15.2, "dividend_yield": 2.98
            },
            {
                "symbol": "PFE", "sector": "Healthcare", "risk": "Medium",
                "current_price": 28.90, "analyst_rating": "HOLD",
                "pe_ratio": 12.5, "dividend_yield": 5.85
            },
            {
                "symbol": "JPM", "sector": "Finance", "risk": "Medium",
                "current_price": 168.45, "analyst_rating": "BUY",
                "pe_ratio": 11.2, "dividend_yield": 2.35
            },
            {
                "symbol": "BAC", "sector": "Finance", "risk": "Medium",
                "current_price": 32.15, "analyst_rating": "BUY",
                "pe_ratio": 12.8, "dividend_yield": 2.85
            },
            {
                "symbol": "KO", "sector": "Consumer Staples", "risk": "Low",
                "current_price": 58.75, "analyst_rating": "HOLD",
                "pe_ratio": 24.5, "dividend_yield": 3.12
            }
        ]
        
        # Filter stocks based on risk level and goals
        filtered_stocks = self.filter_stocks_by_criteria(stock_pool, user_config)
        
        # Select 4-6 stocks for diversification
        selected_stocks = random.sample(filtered_stocks, min(6, len(filtered_stocks)))
        
        # Generate recommendations with enhanced logic
        recommendations = []
        for stock in selected_stocks:
            recommendation = await self.create_stock_recommendation(stock, user_config)
            recommendations.append(recommendation)
        
        # Optimize allocations
        recommendations = self.optimize_allocations(recommendations, user_config)
        
        # Cache recommendations
        cache_key = f"{user_config.get('budget', 50000)}_{user_config.get('riskLevel', 'Medium')}_{user_config.get('timeframe', 'Medium')}"
        self.recommendations_cache[cache_key] = {
            "recommendations": recommendations,
            "generated_at": datetime.now().isoformat(),
            "user_config": user_config
        }
        
        return {
            "status": "success",
            "recommendations": recommendations,
            "total_recommendations": len(recommendations),
            "generated_at": datetime.now().isoformat(),
            "user_config": user_config,
            "portfolio_metrics": self.calculate_portfolio_metrics(recommendations)
        }
    
    def filter_stocks_by_criteria(self, stock_pool: List[Dict], user_config: Dict) -> List[Dict]:
        """Filter stocks based on user criteria"""
        filtered = []
        risk_level = user_config.get('riskLevel', 'Medium')
        goals = user_config.get('goals', 'Growth')
        
        for stock in stock_pool:
            # Risk filtering
            if risk_level == 'Low' and stock['risk'] in ['Low', 'Medium']:
                filtered.append(stock)
            elif risk_level == 'Medium':
                filtered.append(stock)
            elif risk_level == 'High':
                filtered.append(stock)
            
            # Goals-based filtering
            if goals == 'Income' and stock['dividend_yield'] < 2.0:
                if stock in filtered:
                    filtered.remove(stock)
        
        return filtered
    
    async def create_stock_recommendation(self, stock: Dict, user_config: Dict) -> Dict:
        """Create a detailed stock recommendation"""
        current_price = stock['current_price'] * (0.95 + random.random() * 0.1)  # Add some variance
        
        # Calculate target price based on various factors
        base_multiplier = 1.0
        
        # Adjust based on risk level
        if user_config.get('riskLevel') == 'High':
            base_multiplier += random.uniform(0.05, 0.25)
        elif user_config.get('riskLevel') == 'Low':
            base_multiplier += random.uniform(-0.05, 0.10)
        else:
            base_multiplier += random.uniform(0.0, 0.15)
        
        # Adjust based on timeframe
        if user_config.get('timeframe') == 'Long':
            base_multiplier += random.uniform(0.05, 0.20)
        elif user_config.get('timeframe') == 'Short':
            base_multiplier += random.uniform(-0.10, 0.10)
        
        target_price = current_price * base_multiplier
        
        # Determine action
        potential_return = (target_price - current_price) / current_price
        if potential_return > 0.10:
            action = "BUY"
        elif potential_return < -0.05:
            action = "SELL"
        else:
            action = "HOLD"
        
        # Calculate confidence based on various factors
        confidence = random.randint(65, 95)
        if stock['analyst_rating'] == 'BUY':
            confidence += 5
        elif stock['analyst_rating'] == 'SELL':
            confidence -= 10
        
        return {
            "symbol": stock["symbol"],
            "action": action,
            "current_price": round(current_price, 2),
            "target_price": round(target_price, 2),
            "confidence": max(50, min(95, confidence)),
            "reason": self.get_recommendation_reason(stock["symbol"], action),
            "risk": stock["risk"],
            "sector": stock["sector"],
            "allocation": 0,  # Will be calculated in optimize_allocations
            "pe_ratio": stock["pe_ratio"],
            "dividend_yield": stock["dividend_yield"],
            "analyst_rating": stock["analyst_rating"]
        }
    
    def optimize_allocations(self, recommendations: List[Dict], user_config: Dict) -> List[Dict]:
        """Optimize portfolio allocations using simplified MPT principles"""
        total_confidence = sum(rec["confidence"] for rec in recommendations)
        risk_level = user_config.get('riskLevel', 'Medium')
        
        for rec in recommendations:
            # Base allocation on confidence
            base_allocation = (rec["confidence"] / total_confidence) * 100
            
            # Adjust for risk preferences
            if risk_level == 'Low':
                if rec["risk"] == 'Low':
                    base_allocation *= 1.2
                elif rec["risk"] == 'High':
                    base_allocation *= 0.7
            elif risk_level == 'High':
                if rec["risk"] == 'High':
                    base_allocation *= 1.3
                elif rec["risk"] == 'Low':
                    base_allocation *= 0.8
            
            # Ensure reasonable allocation bounds
            rec["allocation"] = max(5, min(30, round(base_allocation)))
        
        # Normalize allocations to sum to 100%
        total_allocation = sum(rec["allocation"] for rec in recommendations)
        if total_allocation != 100:
            factor = 100 / total_allocation
            for rec in recommendations:
                rec["allocation"] = round(rec["allocation"] * factor)
        
        return recommendations
    
    def calculate_portfolio_metrics(self, recommendations: List[Dict]) -> Dict[str, Any]:
        """Calculate portfolio-level metrics"""
        if not recommendations:
            return {}
        
        # Calculate expected return
        expected_return = sum(
            (rec["allocation"] / 100) * ((rec["target_price"] - rec["current_price"]) / rec["current_price"] * 100)
            for rec in recommendations
        )
        
        # Calculate average confidence
        avg_confidence = sum(rec["confidence"] for rec in recommendations) / len(recommendations)
        
        # Calculate risk score
        risk_scores = {'Low': 1, 'Medium': 2, 'High': 3}
        avg_risk = sum(risk_scores[rec["risk"]] * rec["allocation"] / 100 for rec in recommendations)
        
        return {
            "expected_return": round(expected_return, 2),
            "average_confidence": round(avg_confidence, 1),
            "risk_score": round(avg_risk, 2),
            "diversification_score": len(set(rec["sector"] for rec in recommendations)) * 20,
            "dividend_yield": sum(rec["dividend_yield"] * rec["allocation"] / 100 for rec in recommendations)
        }
    
    def get_recommendation_reason(self, symbol: str, action: str) -> str:
        """Get recommendation reasoning for each stock"""
        reasons = {
            "AAPL": {
                "BUY": "Strong iPhone 15 sales momentum, services growth, AI integration potential",
                "HOLD": "Solid fundamentals but limited near-term catalysts",
                "SELL": "Valuation concerns amid slowing growth"
            },
            "MSFT": {
                "BUY": "Azure cloud dominance, AI copilot adoption, strong enterprise demand",
                "HOLD": "Steady growth but high valuation",
                "SELL": "Cloud competition intensifying"
            },
            "GOOGL": {
                "BUY": "Search monopoly intact, YouTube growth, cloud recovery potential",
                "HOLD": "AI competition concerns balanced by strong fundamentals",
                "SELL": "Regulatory pressures and AI disruption risks"
            },
            "NVDA": {
                "BUY": "AI chip leadership, data center demand surge",
                "HOLD": "Strong fundamentals but extreme valuation",
                "SELL": "Overvalued, competition increasing in AI chips"
            },
            "TSLA": {
                "BUY": "EV market leadership, energy storage growth, FSD progress",
                "HOLD": "Mixed fundamentals, execution risks",
                "SELL": "Increasing EV competition, valuation concerns"
            },
            "JNJ": {
                "BUY": "Strong pharmaceutical pipeline, dividend aristocrat, defensive qualities",
                "HOLD": "Stable but limited growth prospects",
                "SELL": "Legal liabilities, slow growth"
            },
            "PFE": {
                "BUY": "Post-COVID recovery, strong oncology pipeline, attractive valuation",
                "HOLD": "Transitioning from COVID revenues",
                "SELL": "Declining COVID revenues, pipeline concerns"
            },
            "JPM": {
                "BUY": "Rising rates benefit, strong loan growth, excellent management",
                "HOLD": "Solid fundamentals, rate environment supportive",
                "SELL": "Credit concerns, rate peak approaching"
            },
            "BAC": {
                "BUY": "Interest rate sensitivity, improving credit quality, capital returns",
                "HOLD": "Rate environment favorable but credit risks",
                "SELL": "Credit cycle concerns, regulatory pressures"
            },
            "KO": {
                "BUY": "Global brand strength, emerging market exposure, dividend growth",
                "HOLD": "Stable defensive play with modest growth",
                "SELL": "Limited growth prospects, health trends"
            }
        }
        
        return reasons.get(symbol, {}).get(action, "AI analysis suggests this action based on current market conditions")
    
    async def get_server_status(self) -> Dict[str, Any]:
        """Get server health status"""
        return {
            "name": self.name,
            "version": self.version,
            "status": "healthy",
            "uptime": datetime.now().isoformat(),
            "cached_recommendations": len(self.recommendations_cache),
            "user_profiles_loaded": len(self.user_profiles)
        }

# Global server instance
recommendation_server = RecommendationServer()