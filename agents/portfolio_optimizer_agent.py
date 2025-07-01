"""
PortfolioOptimizerAgent - LangGraph Agent for Portfolio Optimization
Optimizes portfolio allocation based on Modern Portfolio Theory and user preferences
"""

import asyncio
import json
import random
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
import sys
import os

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

try:
    from mcp_servers.recommendation_server import recommendation_server
except ImportError:
    print("Warning: MCP server not available, using mock data")
    recommendation_server = None

@dataclass
class OptimizationState:
    """State management for PortfolioOptimizerAgent"""
    status: str = "idle"
    last_optimization: Optional[datetime] = None
    optimization_method: str = "modern_portfolio_theory"
    risk_models: List[str] = None
    performance_metrics: Dict[str, float] = None
    
    def __post_init__(self):
        if self.risk_models is None:
            self.risk_models = ["var", "cvar", "sharpe_ratio"]
        if self.performance_metrics is None:
            self.performance_metrics = {"optimization_score": 94.2, "risk_adjusted_return": 0.0}

class PortfolioOptimizerAgent:
    """LangGraph Agent for portfolio optimization"""
    
    def __init__(self, agent_id: str = "portfolio_optimizer"):
        self.agent_id = agent_id
        self.name = "PortfolioOptimizerAgent"
        self.type = "Strategy & Optimization"
        self.version = "1.0.0"
        self.state = OptimizationState()
        self.mcp_server = recommendation_server
        
    async def initialize(self):
        """Initialize the agent and its MCP server connection"""
        try:
            if self.mcp_server:
                await self.mcp_server.initialize()
            self.state.status = "connected"
            print(f"[{self.name}] Agent initialized successfully")
            return True
        except Exception as e:
            self.state.status = "error"
            print(f"[{self.name}] Initialization failed: {e}")
            return False
    
    async def optimize_portfolio(self, user_config: Dict[str, Any]) -> Dict[str, Any]:
        """Main portfolio optimization workflow"""
        try:
            self.state.status = "processing"
            start_time = datetime.now()
            
            if self.mcp_server:
                # Get recommendations from MCP server
                recommendations_result = await self.mcp_server.generate_recommendations(user_config)
                
                if recommendations_result["status"] != "success":
                    raise Exception("Failed to get recommendations from MCP server")
                
                recommendations = recommendations_result["recommendations"]
                portfolio_metrics = recommendations_result.get("portfolio_metrics", {})
            else:
                # Generate mock recommendations
                recommendations = self.generate_mock_recommendations(user_config)
                portfolio_metrics = self.calculate_mock_metrics(recommendations)
            
            # Perform advanced optimization
            optimized_portfolio = await self.perform_optimization(recommendations, user_config)
            
            # Calculate risk metrics
            risk_metrics = await self.calculate_risk_metrics(optimized_portfolio)
            
            # Update performance metrics
            end_time = datetime.now()
            optimization_time = (end_time - start_time).total_seconds()
            
            self.state.performance_metrics["optimization_score"] = optimized_portfolio["optimization_score"]
            self.state.performance_metrics["risk_adjusted_return"] = risk_metrics.get("sharpe_ratio", 0)
            self.state.last_optimization = end_time
            self.state.status = "connected"
            
            result = {
                "status": "success",
                "agent_id": self.agent_id,
                "timestamp": end_time.isoformat(),
                "optimized_portfolio": optimized_portfolio,
                "risk_metrics": risk_metrics,
                "portfolio_metrics": portfolio_metrics,
                "original_recommendations": recommendations,
                "optimization_time": optimization_time,
                "user_config": user_config
            }
            
            return result
            
        except Exception as e:
            self.state.status = "error"
            return {
                "status": "error",
                "agent_id": self.agent_id,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    def generate_mock_recommendations(self, user_config: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate mock recommendations when MCP server is unavailable"""
        mock_stocks = [
            {"symbol": "AAPL", "sector": "Technology", "risk": "Low", "current_price": 192.35},
            {"symbol": "MSFT", "sector": "Technology", "risk": "Low", "current_price": 398.75},
            {"symbol": "GOOGL", "sector": "Technology", "risk": "Medium", "current_price": 142.50},
            {"symbol": "JNJ", "sector": "Healthcare", "risk": "Low", "current_price": 165.20},
            {"symbol": "JPM", "sector": "Finance", "risk": "Medium", "current_price": 168.45}
        ]
        
        recommendations = []
        for stock in mock_stocks:
            target_price = stock["current_price"] * (0.95 + random.random() * 0.2)
            recommendations.append({
                "symbol": stock["symbol"],
                "current_price": stock["current_price"],
                "target_price": target_price,
                "confidence": random.randint(70, 95),
                "risk": stock["risk"],
                "sector": stock["sector"],
                "action": "BUY" if target_price > stock["current_price"] * 1.05 else "HOLD",
                "allocation": random.randint(15, 25)
            })
        
        return recommendations
    
    def calculate_mock_metrics(self, recommendations: List[Dict]) -> Dict[str, Any]:
        """Calculate mock portfolio metrics"""
        return {
            "expected_return": random.uniform(8, 15),
            "average_confidence": sum(r["confidence"] for r in recommendations) / len(recommendations),
            "risk_score": random.uniform(1.5, 2.5),
            "diversification_score": len(set(r["sector"] for r in recommendations)) * 20
        }
    
    async def perform_optimization(self, recommendations: List[Dict], 
                                 user_config: Dict[str, Any]) -> Dict[str, Any]:
        """Perform portfolio optimization using Modern Portfolio Theory principles"""
        
        budget = user_config.get("budget", 50000)
        risk_level = user_config.get("riskLevel", "Medium")
        timeframe = user_config.get("timeframe", "Medium")
        goals = user_config.get("goals", "Growth")
        
        # Risk multipliers based on user preferences
        risk_multipliers = {
            "Low": 0.7,
            "Medium": 1.0,
            "High": 1.3
        }
        
        risk_multiplier = risk_multipliers.get(risk_level, 1.0)
        
        # Calculate optimal allocations using enhanced logic
        optimized_allocations = []
        total_confidence = sum(rec["confidence"] for rec in recommendations)
        
        for rec in recommendations:
            # Base allocation on confidence and risk adjustment
            base_allocation = (rec["confidence"] / total_confidence) * 100
            
            # Adjust for risk appetite
            if risk_level == "Low":
                risk_adjustment = 1.3 if rec["risk"] == "Low" else 0.7 if rec["risk"] == "High" else 1.0
            elif risk_level == "High":
                risk_adjustment = 0.8 if rec["risk"] == "Low" else 1.2 if rec["risk"] == "High" else 1.0
            else:
                risk_adjustment = 1.0
            
            # Adjust for investment goals
            if goals == "Income" and rec.get("dividend_yield", 0) > 2.0:
                risk_adjustment *= 1.2
            elif goals == "Aggressive Growth" and rec["risk"] == "High":
                risk_adjustment *= 1.3
            
            # Adjust for timeframe
            if timeframe == "Long" and rec["risk"] == "Low":
                risk_adjustment *= 1.1
            elif timeframe == "Short" and rec["risk"] == "High":
                risk_adjustment *= 0.9
            
            adjusted_allocation = base_allocation * risk_adjustment
            
            # Calculate number of shares and actual allocation
            shares = int((adjusted_allocation / 100) * budget / rec["current_price"])
            actual_allocation = shares * rec["current_price"]
            allocation_percent = (actual_allocation / budget) * 100 if budget > 0 else 0
            
            optimized_allocations.append({
                "symbol": rec["symbol"],
                "shares": shares,
                "allocation_amount": actual_allocation,
                "allocation_percent": allocation_percent,
                "current_price": rec["current_price"],
                "target_price": rec.get("target_price", rec["current_price"] * 1.1),
                "expected_return": ((rec.get("target_price", rec["current_price"] * 1.1) - rec["current_price"]) / rec["current_price"]) * 100,
                "risk_level": rec["risk"],
                "confidence": rec["confidence"],
                "sector": rec["sector"]
            })
        
        # Calculate portfolio metrics
        total_allocated = sum(alloc["allocation_amount"] for alloc in optimized_allocations)
        cash_remaining = budget - total_allocated
        
        # Calculate expected portfolio return
        expected_return = sum(
            (alloc["allocation_amount"] / total_allocated) * alloc["expected_return"]
            for alloc in optimized_allocations
        ) if total_allocated > 0 else 0
        
        # Calculate optimization score
        diversification_score = min(100, len(set(alloc["sector"] for alloc in optimized_allocations)) * 25)
        confidence_score = sum(alloc["confidence"] for alloc in optimized_allocations) / len(optimized_allocations)
        allocation_efficiency = (total_allocated / budget) * 100 if budget > 0 else 0
        optimization_score = (diversification_score + confidence_score + allocation_efficiency) / 3
        
        return {
            "allocations": optimized_allocations,
            "total_allocated": total_allocated,
            "cash_remaining": cash_remaining,
            "allocation_efficiency": allocation_efficiency,
            "expected_return": expected_return,
            "optimization_score": optimization_score,
            "diversification_score": diversification_score,
            "number_of_positions": len(optimized_allocations),
            "risk_level": risk_level,
            "investment_goals": goals
        }
    
    async def calculate_risk_metrics(self, portfolio: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate comprehensive portfolio risk metrics"""
        allocations = portfolio["allocations"]
        
        if not allocations:
            return {"error": "No allocations to analyze"}
        
        # Simulate risk calculations
        portfolio_volatility = 0
        portfolio_return = portfolio.get("expected_return", 0) / 100
        
        # Calculate weighted risk based on individual stock risks
        risk_weights = {"Low": 0.15, "Medium": 0.25, "High": 0.35}
        for alloc in allocations:
            weight = alloc["allocation_percent"] / 100
            risk_contrib = risk_weights.get(alloc["risk_level"], 0.25) * weight
            portfolio_volatility += risk_contrib
        
        # Sharpe ratio calculation (assuming 2% risk-free rate)
        risk_free_rate = 0.02
        sharpe_ratio = (portfolio_return - risk_free_rate) / portfolio_volatility if portfolio_volatility > 0 else 0
        
        # Value at Risk (simplified)
        var_95 = portfolio_volatility * 1.65  # 95% confidence interval
        
        # Maximum Drawdown (estimated)
        max_drawdown = portfolio_volatility * 1.5
        
        # Beta calculation (simplified, assuming market beta of 1.0)
        portfolio_beta = sum(
            (alloc["allocation_percent"] / 100) * (1.2 if alloc["risk_level"] == "High" else 0.8 if alloc["risk_level"] == "Low" else 1.0)
            for alloc in allocations
        )
        
        return {
            "portfolio_volatility": round(portfolio_volatility * 100, 2),
            "expected_annual_return": round(portfolio_return * 100, 2),
            "sharpe_ratio": round(sharpe_ratio, 2),
            "value_at_risk_95": round(var_95 * 100, 2),
            "max_drawdown": round(max_drawdown * 100, 2),
            "portfolio_beta": round(portfolio_beta, 2),
            "risk_score": min(100, max(0, 50 + (sharpe_ratio * 25))),
            "risk_level": "LOW" if portfolio_volatility < 0.15 else "HIGH" if portfolio_volatility > 0.25 else "MEDIUM"
        }
    
    async def rebalance_portfolio(self, current_positions: Dict[str, Any], 
                                target_allocations: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate rebalancing recommendations"""
        try:
            rebalancing_actions = []
            
            for target in target_allocations:
                symbol = target["symbol"]
                target_shares = target["shares"]
                current_shares = current_positions.get(symbol, {}).get("shares", 0)
                
                if target_shares != current_shares:
                    action = "BUY" if target_shares > current_shares else "SELL"
                    quantity = abs(target_shares - current_shares)
                    
                    rebalancing_actions.append({
                        "symbol": symbol,
                        "action": action,
                        "quantity": quantity,
                        "current_shares": current_shares,
                        "target_shares": target_shares,
                        "reason": f"Rebalance to target allocation of {target['allocation_percent']:.1f}%"
                    })
            
            return {
                "status": "success",
                "rebalancing_actions": rebalancing_actions,
                "total_actions": len(rebalancing_actions),
                "timestamp": datetime.now().isoformat()
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
            "last_optimization": self.state.last_optimization.isoformat() if self.state.last_optimization else None,
            "optimization_method": self.state.optimization_method,
            "risk_models": self.state.risk_models,
            "performance_metrics": self.state.performance_metrics,
            "mcp_server_status": "connected" if self.mcp_server else "unavailable"
        }

# Global agent instance
portfolio_optimizer_agent = PortfolioOptimizerAgent()