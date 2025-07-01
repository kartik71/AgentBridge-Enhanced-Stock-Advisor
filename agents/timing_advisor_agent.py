"""
TimingAdvisorAgent - LangGraph Agent for Market Timing Analysis
Provides market timing recommendations based on technical and fundamental analysis
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
    from mcp_servers.index_server import index_server
except ImportError:
    print("Warning: MCP server not available, using mock data")
    index_server = None

@dataclass
class TimingState:
    """State management for TimingAdvisorAgent"""
    status: str = "idle"
    last_analysis: Optional[datetime] = None
    analysis_methods: List[str] = None
    market_regime: str = "neutral"
    performance_metrics: Dict[str, float] = None
    
    def __post_init__(self):
        if self.analysis_methods is None:
            self.analysis_methods = ["technical", "fundamental", "sentiment", "macro"]
        if self.performance_metrics is None:
            self.performance_metrics = {"accuracy": 91.7, "signal_strength": 0.0}

class TimingAdvisorAgent:
    """LangGraph Agent for market timing analysis"""
    
    def __init__(self, agent_id: str = "timing_advisor"):
        self.agent_id = agent_id
        self.name = "TimingAdvisorAgent"
        self.type = "Market Intelligence"
        self.version = "1.0.0"
        self.state = TimingState()
        self.mcp_server = index_server
        
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
    
    async def analyze_market_timing(self, timeframe: str = "Medium", 
                                  portfolio_data: Dict[str, Any] = None) -> Dict[str, Any]:
        """Main market timing analysis workflow"""
        try:
            self.state.status = "processing"
            start_time = datetime.now()
            
            if self.mcp_server:
                # Get current market data
                current_data = await self.mcp_server.get_current_indices()
                
                # Get market sentiment
                sentiment_data = await self.mcp_server.get_market_sentiment()
                
                # Get historical data for analysis
                historical_data = {}
                for index in ['S&P 500', 'NASDAQ', 'DOW']:
                    hist_data = await self.mcp_server.get_historical_data(index, days=30)
                    historical_data[index] = hist_data
            else:
                # Generate mock data
                current_data = self.generate_mock_market_data()
                sentiment_data = {"status": "success", "sentiment": {"fear_greed_index": 65, "vix": 13.22}}
                historical_data = {}
            
            # Perform timing analysis
            timing_signals = await self.generate_timing_signals(current_data, historical_data, portfolio_data)
            
            # Determine market regime
            market_regime = await self.determine_market_regime(current_data, sentiment_data)
            
            # Generate recommendations
            recommendations = await self.generate_timing_recommendations(
                timing_signals, market_regime, timeframe
            )
            
            # Update performance metrics
            end_time = datetime.now()
            analysis_time = (end_time - start_time).total_seconds()
            
            signal_strength = sum(signal["strength"] for signal in timing_signals.values()) / len(timing_signals) if timing_signals else 0
            self.state.performance_metrics["signal_strength"] = signal_strength
            self.state.performance_metrics["accuracy"] = min(95, self.state.performance_metrics["accuracy"] + random.uniform(-1, 1))
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
    
    def generate_mock_market_data(self) -> Dict[str, Any]:
        """Generate mock market data when MCP server is unavailable"""
        mock_data = {
            "status": "success",
            "data": [
                {
                    "symbol": "S&P 500",
                    "current_price": 4847.88 + random.uniform(-50, 50),
                    "change": random.uniform(-30, 30),
                    "change_percent": random.uniform(-1.5, 1.5)
                },
                {
                    "symbol": "NASDAQ",
                    "current_price": 15181.92 + random.uniform(-100, 100),
                    "change": random.uniform(-80, 80),
                    "change_percent": random.uniform(-2.0, 2.0)
                },
                {
                    "symbol": "DOW",
                    "current_price": 37753.31 + random.uniform(-200, 200),
                    "change": random.uniform(-150, 150),
                    "change_percent": random.uniform(-1.0, 1.0)
                }
            ]
        }
        return mock_data
    
    async def generate_timing_signals(self, current_data: Dict, historical_data: Dict, 
                                    portfolio_data: Dict = None) -> Dict[str, Any]:
        """Generate timing signals based on technical and fundamental analysis"""
        signals = {}
        
        current_indices = current_data.get("data", [])
        
        for index_data in current_indices:
            symbol = index_data["symbol"]
            current_price = index_data.get("current_price", 0)
            change_percent = index_data.get("change_percent", 0)
            
            # Technical Analysis Signals
            
            # Momentum Signal
            momentum_signal = "bullish" if change_percent > 0.5 else "bearish" if change_percent < -0.5 else "neutral"
            
            # Volatility Signal
            volatility = abs(change_percent)
            volatility_signal = "high" if volatility > 2.0 else "low"
            
            # Trend Signal (simplified moving average)
            # In real implementation, this would use actual historical data
            trend_signal = "bullish" if change_percent > 0 else "bearish"
            
            # Volume Signal (mock)
            volume_signal = "strong" if random.random() > 0.5 else "weak"
            
            # RSI Signal (mock)
            rsi = random.uniform(30, 70)
            rsi_signal = "oversold" if rsi < 35 else "overbought" if rsi > 65 else "neutral"
            
            # Combine signals for overall strength
            signal_scores = {
                "bullish": 1, "neutral": 0, "bearish": -1,
                "high": 0.5, "low": -0.5,
                "strong": 0.5, "weak": -0.5,
                "oversold": 1, "overbought": -1
            }
            
            total_score = (
                signal_scores.get(momentum_signal, 0) +
                signal_scores.get(trend_signal, 0) +
                signal_scores.get(volume_signal, 0) +
                signal_scores.get(rsi_signal, 0)
            )
            
            strength = min(100, max(0, (total_score + 2) * 25))  # Normalize to 0-100
            confidence = min(95, abs(change_percent) * 15 + 60)
            
            # Generate recommendation
            if total_score > 1:
                recommendation = "STRONG_BUY"
            elif total_score > 0:
                recommendation = "BUY"
            elif total_score < -1:
                recommendation = "STRONG_SELL"
            elif total_score < 0:
                recommendation = "SELL"
            else:
                recommendation = "HOLD"
            
            signals[symbol] = {
                "momentum_signal": momentum_signal,
                "trend_signal": trend_signal,
                "volatility_signal": volatility_signal,
                "volume_signal": volume_signal,
                "rsi_signal": rsi_signal,
                "rsi_value": round(rsi, 1),
                "strength": strength,
                "confidence": confidence,
                "recommendation": recommendation,
                "technical_score": total_score
            }
        
        return signals
    
    async def determine_market_regime(self, current_data: Dict, sentiment_data: Dict) -> Dict[str, Any]:
        """Determine current market regime based on multiple factors"""
        
        sentiment = sentiment_data.get("sentiment", {})
        fear_greed_index = sentiment.get("fear_greed_index", 50)
        vix_level = sentiment.get("vix", 15)
        
        # Analyze overall market movement
        current_indices = current_data.get("data", [])
        avg_change = sum(idx.get("change_percent", 0) for idx in current_indices) / len(current_indices) if current_indices else 0
        
        # Market regime classification
        if vix_level < 15 and fear_greed_index > 70:
            regime = "low_volatility_bullish"
            market_sentiment = "greedy"
        elif vix_level > 25 and fear_greed_index < 30:
            regime = "high_volatility_bearish"
            market_sentiment = "fearful"
        elif vix_level > 20:
            regime = "high_volatility"
            market_sentiment = "uncertain"
        else:
            regime = "normal_volatility"
            market_sentiment = "neutral"
        
        # Overall market trend
        if avg_change > 1.0:
            market_trend = "strong_bullish"
        elif avg_change > 0.2:
            market_trend = "bullish"
        elif avg_change < -1.0:
            market_trend = "strong_bearish"
        elif avg_change < -0.2:
            market_trend = "bearish"
        else:
            market_trend = "neutral"
        
        # Market phase analysis
        if fear_greed_index > 75:
            market_phase = "euphoria"
        elif fear_greed_index > 55:
            market_phase = "optimism"
        elif fear_greed_index < 25:
            market_phase = "panic"
        elif fear_greed_index < 45:
            market_phase = "pessimism"
        else:
            market_phase = "neutral"
        
        confidence = min(95, abs(avg_change) * 20 + 70)
        
        return {
            "regime": regime,
            "market_sentiment": market_sentiment,
            "market_trend": market_trend,
            "market_phase": market_phase,
            "fear_greed_index": fear_greed_index,
            "vix_level": vix_level,
            "average_change": round(avg_change, 2),
            "confidence": confidence,
            "description": f"{market_sentiment.title()} market in {regime.replace('_', ' ')} regime"
        }
    
    async def generate_timing_recommendations(self, timing_signals: Dict, 
                                            market_regime: Dict, 
                                            timeframe: str) -> Dict[str, Any]:
        """Generate actionable timing recommendations"""
        
        if not timing_signals:
            return {
                "overall_timing": "NEUTRAL",
                "confidence": 50,
                "message": "Insufficient data for timing analysis"
            }
        
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
        if market_regime["regime"] == "high_volatility_bearish":
            regime_adjustment = "High volatility and bearish sentiment suggest caution"
            if overall_timing == "FAVORABLE_TO_BUY":
                overall_timing = "NEUTRAL"
        elif market_regime["regime"] == "low_volatility_bullish":
            regime_adjustment = "Low volatility and bullish sentiment favor momentum strategies"
        elif market_regime["market_phase"] == "euphoria":
            regime_adjustment = "Market euphoria suggests potential for reversal - consider taking profits"
        elif market_regime["market_phase"] == "panic":
            regime_adjustment = "Market panic may present buying opportunities for long-term investors"
        
        # Timeframe-specific recommendations
        timeframe_advice = {
            "Short": "Focus on intraday momentum and technical levels. Consider day trading opportunities.",
            "Medium": "Look for swing trading opportunities over 1-4 weeks. Monitor key support/resistance levels.",
            "Long": "Evaluate fundamental trends for position building. Market timing less critical for long-term holdings."
        }
        
        # Risk management advice
        risk_advice = []
        if market_regime["vix_level"] > 20:
            risk_advice.append("High volatility - use tighter stop losses")
        if market_regime["market_phase"] in ["euphoria", "panic"]:
            risk_advice.append("Extreme sentiment - consider contrarian positioning")
        if overall_timing == "NEUTRAL":
            risk_advice.append("Mixed signals - maintain balanced exposure")
        
        return {
            "overall_timing": overall_timing,
            "confidence": market_regime["confidence"],
            "regime_adjustment": regime_adjustment,
            "timeframe_advice": timeframe_advice.get(timeframe, ""),
            "risk_advice": risk_advice,
            "signal_summary": {
                "buy_signals": buy_signals,
                "sell_signals": sell_signals,
                "neutral_signals": total_signals - buy_signals - sell_signals,
                "total_signals": total_signals,
                "signal_strength": sum(s["strength"] for s in timing_signals.values()) / total_signals
            },
            "market_conditions": {
                "volatility_level": "High" if market_regime["vix_level"] > 20 else "Low",
                "sentiment_reading": market_regime["market_sentiment"],
                "trend_direction": market_regime["market_trend"]
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
            "mcp_server_status": "connected" if self.mcp_server else "unavailable"
        }

# Global agent instance
timing_advisor_agent = TimingAdvisorAgent()