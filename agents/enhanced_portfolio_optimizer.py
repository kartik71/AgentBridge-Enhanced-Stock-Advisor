"""
Enhanced PortfolioOptimizerAgent with A2A Communication
Queries IndexScraperAgent for real-time prices and TimingAdvisorAgent for optimal timing
"""

import asyncio
import json
from datetime import datetime
from typing import Dict, List, Any, Optional
from dataclasses import dataclass

from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolExecutor
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage

# Import other agents for A2A communication
from .index_scraper_agent import IndexScraperAgent
from .timing_advisor_agent import TimingAdvisorAgent
from .compliance_logger_agent import ComplianceLoggerAgent

@dataclass
class A2AState:
    """State for Agent-to-Agent communication"""
    messages: List[BaseMessage]
    user_config: Dict[str, Any]
    market_data: Dict[str, Any] = None
    timing_analysis: Dict[str, Any] = None
    compliance_check: Dict[str, Any] = None
    portfolio_recommendations: List[Dict[str, Any]] = None
    a2a_enabled: bool = True
    reasoning_trace: List[str] = None
    
    def __post_init__(self):
        if self.reasoning_trace is None:
            self.reasoning_trace = []

class EnhancedPortfolioOptimizerAgent:
    """Enhanced Portfolio Optimizer with A2A Communication"""
    
    def __init__(self, agent_id: str = "enhanced_portfolio_optimizer"):
        self.agent_id = agent_id
        self.name = "Enhanced Portfolio Optimizer"
        self.version = "2.0.0"
        
        # Initialize connected agents
        self.index_scraper = IndexScraperAgent()
        self.timing_advisor = TimingAdvisorAgent()
        self.compliance_logger = ComplianceLoggerAgent()
        
        # Create StateGraph with A2A communication
        self.graph = self._create_a2a_graph()
        
    def _create_a2a_graph(self) -> StateGraph:
        """Create StateGraph with A2A communication flow"""
        
        workflow = StateGraph(A2AState)
        
        # Add nodes for A2A workflow
        workflow.add_node("validate_inputs", self._validate_inputs)
        workflow.add_node("query_market_data", self._query_market_data)
        workflow.add_node("analyze_timing", self._analyze_timing)
        workflow.add_node("generate_portfolio", self._generate_portfolio)
        workflow.add_node("check_compliance", self._check_compliance)
        workflow.add_node("finalize_recommendations", self._finalize_recommendations)
        
        # Define A2A communication flow
        workflow.set_entry_point("validate_inputs")
        
        # Sequential A2A communication
        workflow.add_conditional_edges(
            "validate_inputs",
            self._should_use_a2a,
            {
                "use_a2a": "query_market_data",
                "skip_a2a": "generate_portfolio"
            }
        )
        
        workflow.add_edge("query_market_data", "analyze_timing")
        workflow.add_edge("analyze_timing", "generate_portfolio")
        workflow.add_edge("generate_portfolio", "check_compliance")
        workflow.add_edge("check_compliance", "finalize_recommendations")
        workflow.add_edge("finalize_recommendations", END)
        
        return workflow.compile()
    
    def _should_use_a2a(self, state: A2AState) -> str:
        """Determine if A2A communication should be used"""
        return "use_a2a" if state.a2a_enabled else "skip_a2a"
    
    async def _validate_inputs(self, state: A2AState) -> A2AState:
        """Validate user inputs and configuration"""
        reasoning = "🔍 VALIDATE: Checking user configuration and A2A settings"
        
        config = state.user_config
        
        # Validate required fields
        required_fields = ['budget', 'timeframe', 'riskLevel']
        for field in required_fields:
            if field not in config:
                reasoning += f" ❌ Missing required field: {field}"
                state.reasoning_trace.append(reasoning)
                return state
        
        reasoning += f" ✅ Configuration valid - Budget: ${config['budget']:,}, Risk: {config['riskLevel']}, Timeframe: {config['timeframe']}"
        
        if state.a2a_enabled:
            reasoning += " 🔗 A2A communication enabled - will query other agents"
        else:
            reasoning += " 🚫 A2A communication disabled - using standalone mode"
        
        state.reasoning_trace.append(reasoning)
        state.messages.append(AIMessage(content=reasoning))
        
        return state
    
    async def _query_market_data(self, state: A2AState) -> A2AState:
        """Query IndexScraperAgent for real-time market data"""
        reasoning = "📊 A2A QUERY: Requesting real-time market data from IndexScraperAgent"
        
        try:
            # Initialize IndexScraperAgent if needed
            await self.index_scraper.initialize()
            
            # Query for current market data
            market_result = await self.index_scraper.collect_market_data()
            
            if market_result["status"] == "success":
                state.market_data = market_result
                reasoning += f" ✅ Received market data: {len(market_result['current_data']['data'])} indices"
                
                # Extract key market metrics
                indices = market_result['current_data']['data']
                for index in indices[:3]:  # Show top 3
                    change_icon = "📈" if index.get('change_percent', 0) >= 0 else "📉"
                    reasoning += f" {change_icon} {index['symbol']}: {index.get('change_percent', 0):+.2f}%"
                
                # Market sentiment
                sentiment = market_result.get('sentiment_data', {}).get('sentiment', {})
                if sentiment:
                    fear_greed = sentiment.get('fear_greed_index', 50)
                    reasoning += f" 🧠 Market sentiment: Fear/Greed Index = {fear_greed}"
            else:
                reasoning += f" ❌ Failed to get market data: {market_result.get('error', 'Unknown error')}"
                
        except Exception as e:
            reasoning += f" ❌ Error querying IndexScraperAgent: {str(e)}"
            # Continue with fallback data
            state.market_data = {"status": "error", "error": str(e)}
        
        state.reasoning_trace.append(reasoning)
        state.messages.append(AIMessage(content=reasoning))
        
        return state
    
    async def _analyze_timing(self, state: A2AState) -> A2AState:
        """Query TimingAdvisorAgent for optimal market timing"""
        reasoning = "⏰ A2A QUERY: Requesting timing analysis from TimingAdvisorAgent"
        
        try:
            # Initialize TimingAdvisorAgent if needed
            await self.timing_advisor.initialize()
            
            # Query for timing analysis
            timeframe = state.user_config.get('timeframe', 'Medium').lower()
            timing_result = await self.timing_advisor.analyze_market_timing(timeframe)
            
            if timing_result["status"] == "success":
                state.timing_analysis = timing_result
                
                # Extract timing recommendations
                timing_signals = timing_result.get('timing_signals', {})
                market_regime = timing_result.get('market_regime', {})
                recommendations = timing_result.get('recommendations', {})
                
                reasoning += f" ✅ Timing analysis complete"
                reasoning += f" 🎯 Market regime: {market_regime.get('description', 'Unknown')}"
                reasoning += f" 📊 Overall timing: {recommendations.get('overall_timing', 'NEUTRAL')}"
                
                # Show key signals
                for index, signals in list(timing_signals.items())[:2]:
                    signal_strength = signals.get('strength', 0)
                    confidence = signals.get('confidence', 0)
                    reasoning += f" 📈 {index}: {signal_strength:.0f}% strength, {confidence:.0f}% confidence"
                
            else:
                reasoning += f" ❌ Failed to get timing analysis: {timing_result.get('error', 'Unknown error')}"
                
        except Exception as e:
            reasoning += f" ❌ Error querying TimingAdvisorAgent: {str(e)}"
            state.timing_analysis = {"status": "error", "error": str(e)}
        
        state.reasoning_trace.append(reasoning)
        state.messages.append(AIMessage(content=reasoning))
        
        return state
    
    async def _generate_portfolio(self, state: A2AState) -> A2AState:
        """Generate portfolio recommendations using A2A data"""
        reasoning = "💼 GENERATE: Creating portfolio recommendations with A2A insights"
        
        config = state.user_config
        
        # Use market data from A2A if available
        market_data = state.market_data
        timing_analysis = state.timing_analysis
        
        # Generate enhanced recommendations using A2A data
        recommendations = await self._create_enhanced_recommendations(config, market_data, timing_analysis)
        
        state.portfolio_recommendations = recommendations
        
        reasoning += f" ✅ Generated {len(recommendations)} recommendations"
        reasoning += f" 💰 Total allocation: {sum(rec['allocation'] for rec in recommendations)}%"
        
        # Show top recommendations
        for i, rec in enumerate(recommendations[:3]):
            reasoning += f" 🏆 #{i+1}: {rec['symbol']} ({rec['allocation']}%) - {rec['action']}"
        
        # A2A enhancement notes
        if state.a2a_enabled and market_data and market_data.get("status") == "success":
            reasoning += " 🔗 Enhanced with real-time market data from IndexScraperAgent"
        
        if state.a2a_enabled and timing_analysis and timing_analysis.get("status") == "success":
            timing_rec = timing_analysis.get('recommendations', {}).get('overall_timing', 'NEUTRAL')
            reasoning += f" ⏰ Timing guidance from TimingAdvisorAgent: {timing_rec}"
        
        state.reasoning_trace.append(reasoning)
        state.messages.append(AIMessage(content=reasoning))
        
        return state
    
    async def _check_compliance(self, state: A2AState) -> A2AState:
        """Query ComplianceLoggerAgent for compliance check"""
        reasoning = "🛡️ A2A QUERY: Requesting compliance check from ComplianceLoggerAgent"
        
        try:
            # Initialize ComplianceLoggerAgent if needed
            await self.compliance_logger.initialize()
            
            # Prepare portfolio data for compliance check
            portfolio_data = {
                "recommendations": state.portfolio_recommendations,
                "user_config": state.user_config,
                "total_budget": state.user_config.get('budget', 50000)
            }
            
            # Query for compliance check
            compliance_result = await self.compliance_logger.check_portfolio_compliance(
                portfolio_data, state.user_config.get('user_id', 'default_user')
            )
            
            if compliance_result["status"] == "success":
                state.compliance_check = compliance_result
                
                compliance_score = compliance_result.get('compliance_result', {}).get('compliance_score', 100)
                violations = compliance_result.get('compliance_result', {}).get('total_violations', 0)
                
                reasoning += f" ✅ Compliance check complete"
                reasoning += f" 📊 Compliance score: {compliance_score:.1f}/100"
                reasoning += f" 🚨 Violations: {violations}"
                
                if violations == 0:
                    reasoning += " ✅ Portfolio fully compliant"
                else:
                    reasoning += f" ⚠️ {violations} compliance issues detected"
                
            else:
                reasoning += f" ❌ Compliance check failed: {compliance_result.get('error', 'Unknown error')}"
                
        except Exception as e:
            reasoning += f" ❌ Error querying ComplianceLoggerAgent: {str(e)}"
            state.compliance_check = {"status": "error", "error": str(e)}
        
        state.reasoning_trace.append(reasoning)
        state.messages.append(AIMessage(content=reasoning))
        
        return state
    
    async def _finalize_recommendations(self, state: A2AState) -> A2AState:
        """Finalize portfolio recommendations with A2A insights"""
        reasoning = "✅ FINALIZE: Portfolio optimization complete with A2A enhancements"
        
        # Calculate final metrics
        total_budget = state.user_config.get('budget', 50000)
        recommendations = state.portfolio_recommendations or []
        
        total_investment = sum(
            (rec['allocation'] / 100) * total_budget 
            for rec in recommendations
        )
        
        expected_return = sum(
            (rec['allocation'] / 100) * rec.get('expected_return', 8)
            for rec in recommendations
        )
        
        reasoning += f" 📊 Final Portfolio Summary:"
        reasoning += f" - Recommendations: {len(recommendations)}"
        reasoning += f" - Total Investment: ${total_investment:,.2f}"
        reasoning += f" - Expected Return: {expected_return:.1f}%"
        reasoning += f" - Cash Remaining: ${total_budget - total_investment:,.2f}"
        
        # A2A enhancement summary
        if state.a2a_enabled:
            reasoning += " 🔗 A2A Enhancements Applied:"
            
            if state.market_data and state.market_data.get("status") == "success":
                reasoning += " ✅ Real-time market data integrated"
            
            if state.timing_analysis and state.timing_analysis.get("status") == "success":
                reasoning += " ✅ Market timing analysis integrated"
            
            if state.compliance_check and state.compliance_check.get("status") == "success":
                compliance_score = state.compliance_check.get('compliance_result', {}).get('compliance_score', 100)
                reasoning += f" ✅ Compliance validated ({compliance_score:.0f}/100)"
        else:
            reasoning += " 🚫 A2A communication was disabled - used standalone mode"
        
        state.reasoning_trace.append(reasoning)
        state.messages.append(AIMessage(content=reasoning))
        
        return state
    
    async def _create_enhanced_recommendations(self, config: Dict, market_data: Dict, timing_analysis: Dict) -> List[Dict]:
        """Create enhanced recommendations using A2A data"""
        
        # Base stock universe
        stocks = [
            {"symbol": "AAPL", "sector": "Technology", "base_score": 8.5, "current_price": 192.35},
            {"symbol": "MSFT", "sector": "Technology", "base_score": 8.8, "current_price": 398.75},
            {"symbol": "GOOGL", "sector": "Technology", "base_score": 8.0, "current_price": 142.50},
            {"symbol": "NVDA", "sector": "Technology", "base_score": 9.2, "current_price": 465.20},
            {"symbol": "JNJ", "sector": "Healthcare", "base_score": 7.5, "current_price": 165.20},
            {"symbol": "JPM", "sector": "Finance", "base_score": 7.8, "current_price": 168.45}
        ]
        
        recommendations = []
        
        for stock in stocks[:5]:  # Top 5 recommendations
            # Base allocation
            base_allocation = 20  # Equal weight starting point
            
            # Enhance with market data
            if market_data and market_data.get("status") == "success":
                # Adjust based on market sentiment
                sentiment = market_data.get('sentiment_data', {}).get('sentiment', {})
                fear_greed = sentiment.get('fear_greed_index', 50)
                
                if fear_greed > 70:  # Greedy market
                    base_allocation *= 0.9  # Be more conservative
                elif fear_greed < 30:  # Fearful market
                    base_allocation *= 1.1  # Opportunity to buy
            
            # Enhance with timing analysis
            if timing_analysis and timing_analysis.get("status") == "success":
                timing_rec = timing_analysis.get('recommendations', {}).get('overall_timing', 'NEUTRAL')
                
                if timing_rec == "FAVORABLE_TO_BUY":
                    base_allocation *= 1.2
                elif timing_rec == "FAVORABLE_TO_SELL":
                    base_allocation *= 0.8
            
            # Risk adjustment
            risk_level = config.get('riskLevel', 'Medium')
            if risk_level == 'Low':
                base_allocation *= 0.8
            elif risk_level == 'High':
                base_allocation *= 1.2
            
            # Ensure reasonable bounds
            allocation = max(5, min(35, base_allocation))
            
            recommendation = {
                "symbol": stock["symbol"],
                "allocation": round(allocation, 1),
                "current_price": stock["current_price"],
                "target_price": round(stock["current_price"] * 1.15, 2),
                "action": "BUY",
                "confidence": min(95, max(70, int(stock["base_score"] * 10))),
                "sector": stock["sector"],
                "expected_return": round(stock["base_score"] + 2, 1),
                "a2a_enhanced": True
            }
            
            recommendations.append(recommendation)
        
        # Normalize allocations to 100%
        total_allocation = sum(rec["allocation"] for rec in recommendations)
        if total_allocation != 100:
            factor = 100 / total_allocation
            for rec in recommendations:
                rec["allocation"] = round(rec["allocation"] * factor, 1)
        
        return recommendations
    
    async def optimize_portfolio_with_a2a(self, user_config: Dict, a2a_enabled: bool = True) -> Dict[str, Any]:
        """Main entry point for A2A-enhanced portfolio optimization"""
        
        # Initialize state
        initial_state = A2AState(
            messages=[HumanMessage(content="Optimize portfolio with A2A communication")],
            user_config=user_config,
            a2a_enabled=a2a_enabled,
            reasoning_trace=[]
        )
        
        try:
            # Run the A2A workflow
            final_state = await self.graph.ainvoke(initial_state)
            
            return {
                "status": "success",
                "portfolio_recommendations": final_state.portfolio_recommendations,
                "market_data": final_state.market_data,
                "timing_analysis": final_state.timing_analysis,
                "compliance_check": final_state.compliance_check,
                "reasoning_trace": final_state.reasoning_trace,
                "a2a_enabled": final_state.a2a_enabled,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }

# Global enhanced agent instance
enhanced_portfolio_optimizer = EnhancedPortfolioOptimizerAgent()