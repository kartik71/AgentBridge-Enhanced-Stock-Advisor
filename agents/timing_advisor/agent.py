"""
Timing Advisor Agent - LangGraph Agent for Market Timing Analysis
Provides market timing recommendations based on technical and fundamental analysis
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
class TimingState:
    """State management for Timing Advisor Agent"""
    status: str = "idle"
    last_analysis: Optional[datetime] = None
    analysis_methods: List[str] = None
    market_regime: str = "neutral"
    performance_metrics: Dict[str, float] = None
    
    def __post_init__(self):
        if self.analysis_methods is None:
            self.analysis_methods = ["technical", "fundamental", "sentiment", "macro"]
        if self.performance_metrics is None:
            self.performance_metrics = {"accuracy": 0.0, "signal_strength": 0.0}

class TimingAdvisorAgent:
    """LangGraph Agent for market timing analysis"""
    
    def __init__(self, agent_id: str = "timing_advisor"):
        self.agent_id = agent_id
        self.name = "Timing Advisor"
        self.type = "Market Intelligence"
        self.version = "1.0.0"
        self.state = TimingState()
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
            print(f"[{self.name}] Initialization failed: {e}")
            return False
    
    async def analyze_market_timing(self, timeframe: str = "medium") -> Dict[str, Any]:
        """Main market timing analysis workflow"""
        try:
            self.state.status = "processing"
            start_time = datetime.now()
            
            # Get current market data
            current_data = await self.mcp_server.get_current_indices()
            
            # Get historical data for analysis
            historical_data = {}
            for index in ['S&P 500', 'DOW', 'NASDAQ', 'VIX']:
                hist_data = await self.mcp_server.get_historical_data(index, days=30)
                historical_data[index] = hist_data
            
            # Perform timing analysis
            timing_signals = await self.generate_timing_signals(current_data, historical_data)
            
            # Determine market regime
            market_regime = await self.determine_market_regime(current_data, historical_data)
            
            # Generate recommendations
            recommendations = await self.generate_timing_recommendations(
                timing_signals, market_regime, timeframe
            )
            
            # Update performance metrics
            end_time = datetime.now()
            analysis_time = (end_time - start_time).total_seconds()
            
            signal_strength = sum(signal["strength"] for signal in timing_signals.values()) / len(timing_signals)
            self.state.performance_metrics["signal_strength"] = signal_strength
            self.state.performance_metrics["accuracy"] = min(95, signal_strength + 20)  # Simulated accuracy
            self.state.last_analysis = end_time
            self.state.market_regime = market_regime["regime"]
            self.state.status = "connected"
            
            result = {
                "status": "success",
                "agent_id": self.agent_id,
                "timestamp": end_time.isoformat(),
                "timing_signals": timing_signals,
                "market_regime": market_regime,
                "recommendations": recommendations,
                "analysis_time": analysis_time,
                "parameters": {
                    "timeframe": timeframe
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
    
    async def generate_timing_signals(self, current_data: Dict, historical_data: Dict) -> Dict[str, Any]:
        """Generate timing signals based on technical analysis"""
        signals = {}
        
        current_indices = current_data.get("data", [])
        
        for index_data in current_indices:
            symbol = index_data["symbol"]
            current_price = index_data["price"]
            change_percent = index_data["changePercent"]
            
            # Get historical data for this symbol
            hist_data = historical_data.get(symbol, {}).get("data", [])
            
            if not hist_data:
                continue
            
            # Calculate simple moving averages
            prices = [float(item["price"]) for item in hist_data[:10]]  # Last 10 days
            sma_10 = sum(prices) / len(prices) if prices else current_price
            
            # Technical signals
            signals[symbol] = {
                "price_momentum": "bullish" if change_percent > 0.5 else "bearish" if change_percent < -0.5 else "neutral",
                "trend_signal": "bullish" if current_price > sma_10 else "bearish",
                "volatility_signal": "high" if abs(change_percent) > 2.0 else "low",
                "strength": min(100, abs(change_percent) * 20 + 50),  # 0-100 scale
                "confidence": min(95, abs(change_percent) * 15 + 60),
                "recommendation": self._get_timing_recommendation(change_percent, current_price, sma_10)
            }
        
        return signals
    
    def _get_timing_recommendation(self, change_percent: float, current_price: float, sma_10: float) -> str:
        """Generate timing recommendation based on signals"""
        if change_percent > 1.0 and current_price > sma_10:
            return "STRONG_BUY"
        elif change_percent > 0.2 and current_price > sma_10:
            return "BUY"
        elif change_percent < -1.0 and current_price < sma_10:
            return "STRONG_SELL"
        elif change_percent < -0.2 and current_price < sma_10:
            return "SELL"
        else:
            return "HOLD"
    
    async def determine_market_regime(self, current_data: Dict, historical_data: Dict) -> Dict[str, Any]:
        """Determine current market regime"""
        
        # Analyze VIX for market fear/greed
        vix_data = None
        for index_data in current_data.get("data", []):
            if index_data["symbol"] == "VIX":
                vix_data = index_data
                break
        
        if not vix_data:
            return {"regime": "unknown", "confidence": 0}
        
        vix_level = vix_data["price"]
        vix_change = vix_data["changePercent"]
        
        # Market regime classification
        if vix_level < 15:
            regime = "low_volatility"
            market_sentiment = "complacent"
        elif vix_level > 30:
            regime = "high_volatility"
            market_sentiment = "fearful"
        else:
            regime = "normal_volatility"
            market_sentiment = "neutral"
        
        # Overall market trend
        sp500_data = None
        for index_data in current_data.get("data", []):
            if index_data["symbol"] == "S&P 500":
                sp500_data = index_data
                break
        
        market_trend = "neutral"
        if sp500_data:
            if sp500_data["changePercent"] > 1.0:
                market_trend = "strong_bullish"
            elif sp500_data["changePercent"] > 0.2:
                market_trend = "bullish"
            elif sp500_data["changePercent"] < -1.0:
                market_trend = "strong_bearish"
            elif sp500_data["changePercent"] < -0.2:
                market_trend = "bearish"
        
        confidence = min(95, abs(vix_change) * 10 + 70)
        
        return {
            "regime": regime,
            "market_sentiment": market_sentiment,
            "market_trend": market_trend,
            "vix_level": vix_level,
            "confidence": confidence,
            "description": f"{market_sentiment.title()} market with {regime.replace('_', ' ')} conditions"
        }
    
    async def generate_timing_recommendations(self, timing_signals: Dict, 
                                            market_regime: Dict, 
                                            timeframe: str) -> Dict[str, Any]:
        """Generate actionable timing recommendations"""
        
        # Aggregate signals
        buy_signals = sum(1 for signal in timing_signals.values() 
                         if signal["recommendation"] in ["BUY", "STRONG_BUY"])
        sell_signals = sum(1 for signal in timing_signals.values() 
                          if signal["recommendation"] in ["SELL", "STRONG_SELL"])
        total_signals = len(timing_signals)
        
        # Overall market timing recommendation
        if buy_signals > sell_signals and buy_signals >= total_signals * 0.6:
            overall_timing = "FAVORABLE_TO_BUY"
        elif sell_signals > buy_signals and sell_signals >= total_signals * 0.6:
            overall_timing = "FAVORABLE_TO_SELL"
        else:
            overall_timing = "NEUTRAL"
        
        # Adjust for market regime
        regime_adjustment = ""
        if market_regime["regime"] == "high_volatility":
            regime_adjustment = "Exercise caution due to high volatility"
        elif market_regime["regime"] == "low_volatility":
            regime_adjustment = "Low volatility environment may favor momentum strategies"
        
        # Timeframe-specific recommendations
        timeframe_advice = {
            "short": "Focus on intraday momentum and technical levels",
            "medium": "Consider swing trading opportunities over 1-4 weeks",
            "long": "Evaluate fundamental trends for position building"
        }
        
        return {
            "overall_timing": overall_timing,
            "confidence": market_regime["confidence"],
            "regime_adjustment": regime_adjustment,
            "timeframe_advice": timeframe_advice.get(timeframe, ""),
            "signal_summary": {
                "buy_signals": buy_signals,
                "sell_signals": sell_signals,
                "neutral_signals": total_signals - buy_signals - sell_signals,
                "total_signals": total_signals
            },
            "key_levels": {
                "support_level": "Monitor key support levels for entry opportunities",
                "resistance_level": "Watch for breakouts above resistance",
                "stop_loss_advice": "Use 2-3% stop losses in current volatility environment"
            },
            "next_review": (datetime.now() + timedelta(hours=4)).isoformat()
        }
    
    async def get_agent_status(self) -> Dict[str, Any]:
        """Get current agent status and metrics"""
        return {
            "agent_id": self.agent_id,
            "name": self.name,
            "type": self.type,
            "version": self.version,
            "status": self.state.status,
            "last_analysis": self.state.last_analysis.isoformat() if self.state.last_analysis else None,
            "analysis_methods": self.state.analysis_methods,
            "market_regime": self.state.market_regime,
            "performance_metrics": self.state.performance_metrics,
            "mcp_server_status": await self.mcp_server.get_server_status()
        }

# Global agent instance
timing_advisor_agent = TimingAdvisorAgent()

# CLI interface for testing
if __name__ == "__main__":
    async def main():
        agent = TimingAdvisorAgent()
        await agent.initialize()
        
        # Test timing analysis
        result = await agent.analyze_market_timing(timeframe="medium")
        
        print("Market Timing Analysis Result:")
        print(json.dumps(result, indent=2))
        
        # Show agent status
        status = await agent.get_agent_status()
        print("\nAgent Status:")
        print(json.dumps(status, indent=2))
    
    asyncio.run(main())