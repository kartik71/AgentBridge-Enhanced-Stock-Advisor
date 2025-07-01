"""
Portfolio Optimizer Agent - LangGraph Agent for Portfolio Optimization
Optimizes portfolio allocation based on risk tolerance and market conditions
"""

import asyncio
import json
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
import sys
import os

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from mcp_servers.recommendation_server import recommendation_server

@dataclass
class OptimizationState:
    """State management for Portfolio Optimizer Agent"""
    status: str = "idle"
    last_optimization: Optional[datetime] = None
    optimization_method: str = "modern_portfolio_theory"
    risk_models: List[str] = None
    performance_metrics: Dict[str, float] = None
    
    def __post_init__(self):
        if self.risk_models is None:
            self.risk_models = ["var", "cvar", "sharpe_ratio"]
        if self.performance_metrics is None:
            self.performance_metrics = {"optimization_score": 0.0, "risk_adjusted_return": 0.0}

class PortfolioOptimizerAgent:
    """LangGraph Agent for portfolio optimization"""
    
    def __init__(self, agent_id: str = "portfolio_optimizer"):
        self.agent_id = agent_id
        self.name = "Portfolio Optimizer"
        self.type = "Strategy"
        self.version = "1.0.0"
        self.state = OptimizationState()
        self.mcp_server = recommendation_server
        
    async def initialize(self):
        """Initialize the agent and its MCP server connection"""
        try:
            await self.mcp_server.initialize()
            self.state.status = "connected"
            print(f"[{self.name}] Agent initialized successfully")
            return True
        except Exception as e:
            self.state.status = "error"
            print(f"[{self.name}] Initialization failed: {e}")
            return False
    
    async def optimize_portfolio(self, user_id: str = "default_user", 
                               timeframe: str = "medium", 
                               risk_appetite: str = "medium",
                               budget: float = 50000) -> Dict[str, Any]:
        """Main portfolio optimization workflow"""
        try:
            self.state.status = "processing"
            start_time = datetime.now()
            
            # Get recommendations from MCP server
            recommendations_result = await self.mcp_server.generate_recommendations(
                user_id=user_id,
                timeframe=timeframe,
                risk_appetite=risk_appetite
            )
            
            if recommendations_result["status"] != "success":
                raise Exception("Failed to get recommendations from MCP server")
            
            recommendations = recommendations_result["recommendations"]
            
            # Perform portfolio optimization
            optimized_portfolio = await self.perform_optimization(
                recommendations, budget, risk_appetite
            )
            
            # Calculate risk metrics
            risk_metrics = await self.calculate_risk_metrics(optimized_portfolio)
            
            # Update performance metrics
            end_time = datetime.now()
            optimization_time = (end_time - start_time).total_seconds()
            
            self.state.performance_metrics["optimization_score"] = optimized_portfolio["optimization_score"]
            self.state.performance_metrics["risk_adjusted_return"] = risk_metrics["sharpe_ratio"]
            self.state.last_optimization = end_time
            self.state.status = "connected"
            
            result = {
                "status": "success",
                "agent_id": self.agent_id,
                "timestamp": end_time.isoformat(),
                "optimized_portfolio": optimized_portfolio,
                "risk_metrics": risk_metrics,
                "original_recommendations": recommendations,
                "optimization_time": optimization_time,
                "parameters": {
                    "user_id": user_id,
                    "timeframe": timeframe,
                    "risk_appetite": risk_appetite,
                    "budget": budget
                }
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
    
    async def perform_optimization(self, recommendations: List[Dict], 
                                 budget: float, risk_appetite: str) -> Dict[str, Any]:
        """Perform portfolio optimization using Modern Portfolio Theory principles"""
        
        # Risk multipliers based on risk appetite
        risk_multipliers = {
            "low": 0.5,
            "medium": 1.0,
            "high": 1.5
        }
        
        risk_multiplier = risk_multipliers.get(risk_appetite, 1.0)
        
        # Calculate optimal allocations
        total_confidence = sum(rec["confidence"] for rec in recommendations)
        optimized_allocations = []
        
        for rec in recommendations:
            # Base allocation on confidence and risk adjustment
            base_allocation = (rec["confidence"] / total_confidence) * budget
            
            # Adjust for risk appetite
            if risk_appetite == "low":
                # Favor lower risk stocks
                risk_adjustment = 1.2 if rec["risk"] == "LOW" else 0.8 if rec["risk"] == "HIGH" else 1.0
            elif risk_appetite == "high":
                # Favor higher risk stocks
                risk_adjustment = 0.8 if rec["risk"] == "LOW" else 1.2 if rec["risk"] == "HIGH" else 1.0
            else:
                risk_adjustment = 1.0
            
            adjusted_allocation = base_allocation * risk_adjustment
            
            # Calculate number of shares
            shares = int(adjusted_allocation / rec["current_price"])
            actual_allocation = shares * rec["current_price"]
            
            optimized_allocations.append({
                "symbol": rec["symbol"],
                "shares": shares,
                "allocation_amount": actual_allocation,
                "allocation_percent": (actual_allocation / budget) * 100,
                "current_price": rec["current_price"],
                "target_price": rec["target_price"],
                "expected_return": ((rec["target_price"] - rec["current_price"]) / rec["current_price"]) * 100,
                "risk_level": rec["risk"],
                "confidence": rec["confidence"]
            })
        
        # Calculate portfolio metrics
        total_allocated = sum(alloc["allocation_amount"] for alloc in optimized_allocations)
        cash_remaining = budget - total_allocated
        
        # Calculate expected portfolio return
        expected_return = sum(
            (alloc["allocation_amount"] / total_allocated) * alloc["expected_return"]
            for alloc in optimized_allocations
        ) if total_allocated > 0 else 0
        
        # Calculate optimization score (simplified)
        diversification_score = min(100, len(optimized_allocations) * 25)  # Max 100 for 4+ stocks
        confidence_score = sum(alloc["confidence"] for alloc in optimized_allocations) / len(optimized_allocations)
        optimization_score = (diversification_score + confidence_score) / 2
        
        return {
            "allocations": optimized_allocations,
            "total_allocated": total_allocated,
            "cash_remaining": cash_remaining,
            "allocation_efficiency": (total_allocated / budget) * 100,
            "expected_return": expected_return,
            "optimization_score": optimization_score,
            "diversification_score": diversification_score,
            "number_of_positions": len(optimized_allocations)
        }
    
    async def calculate_risk_metrics(self, portfolio: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate portfolio risk metrics"""
        allocations = portfolio["allocations"]
        
        if not allocations:
            return {"error": "No allocations to analyze"}
        
        # Simulate historical returns for risk calculation
        returns = []
        for alloc in allocations:
            # Simulate 30 days of returns based on expected return and volatility
            daily_return = alloc["expected_return"] / 365  # Annualized to daily
            volatility = 0.02 if alloc["risk_level"] == "LOW" else 0.04 if alloc["risk_level"] == "HIGH" else 0.03
            
            # Generate synthetic returns
            np.random.seed(42)  # For reproducible results
            stock_returns = np.random.normal(daily_return, volatility, 30)
            weighted_returns = stock_returns * (alloc["allocation_percent"] / 100)
            returns.append(weighted_returns)
        
        # Calculate portfolio returns
        portfolio_returns = np.sum(returns, axis=0)
        
        # Calculate risk metrics
        portfolio_volatility = np.std(portfolio_returns) * np.sqrt(252)  # Annualized
        portfolio_return = np.mean(portfolio_returns) * 252  # Annualized
        
        # Sharpe ratio (assuming 2% risk-free rate)
        risk_free_rate = 0.02
        sharpe_ratio = (portfolio_return - risk_free_rate) / portfolio_volatility if portfolio_volatility > 0 else 0
        
        # Value at Risk (95% confidence)
        var_95 = np.percentile(portfolio_returns, 5)
        
        # Maximum Drawdown (simplified)
        cumulative_returns = np.cumprod(1 + portfolio_returns)
        running_max = np.maximum.accumulate(cumulative_returns)
        drawdown = (cumulative_returns - running_max) / running_max
        max_drawdown = np.min(drawdown)
        
        return {
            "portfolio_volatility": round(portfolio_volatility * 100, 2),
            "expected_annual_return": round(portfolio_return * 100, 2),
            "sharpe_ratio": round(sharpe_ratio, 2),
            "value_at_risk_95": round(var_95 * 100, 2),
            "max_drawdown": round(max_drawdown * 100, 2),
            "risk_score": min(100, max(0, 50 + (sharpe_ratio * 25))),  # 0-100 scale
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
                        "reason": f"Rebalance to target allocation"
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
            "mcp_server_status": await self.mcp_server.get_server_status()
        }

# Global agent instance
portfolio_optimizer_agent = PortfolioOptimizerAgent()

# CLI interface for testing
if __name__ == "__main__":
    async def main():
        agent = PortfolioOptimizerAgent()
        await agent.initialize()
        
        # Test portfolio optimization
        result = await agent.optimize_portfolio(
            user_id="default_user",
            timeframe="medium",
            risk_appetite="medium",
            budget=50000
        )
        
        print("Portfolio Optimization Result:")
        print(json.dumps(result, indent=2))
        
        # Show agent status
        status = await agent.get_agent_status()
        print("\nAgent Status:")
        print(json.dumps(status, indent=2))
    
    asyncio.run(main())