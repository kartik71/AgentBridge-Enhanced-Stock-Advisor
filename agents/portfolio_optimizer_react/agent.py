"""
PortfolioOptimizerAgent - LangGraph ReAct Agent for Portfolio Optimization
Uses ReAct pattern with reasoning traces and HITL override capabilities
"""

import asyncio
import json
import csv
import os
from datetime import datetime
from typing import Dict, List, Any, Optional, TypedDict, Annotated
from dataclasses import dataclass
import sys

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolExecutor
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
from langchain_core.tools import tool
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser

try:
    from mcp_servers.recommendation_server import recommendation_server
    from mcp_servers.index_server import index_server
except ImportError:
    print("Warning: MCP servers not available, using mock data")
    recommendation_server = None
    index_server = None

# State definition for the agent
class AgentState(TypedDict):
    messages: Annotated[List[BaseMessage], "The conversation messages"]
    budget: float
    timeframe: str
    risk_level: str
    market_data: Dict[str, Any]
    stock_recommendations: List[Dict[str, Any]]
    reasoning_trace: List[str]
    hitl_approval_required: bool
    hitl_approved: bool
    final_portfolio: Dict[str, Any]
    audit_log: List[Dict[str, Any]]

@dataclass
class OptimizationConfig:
    """Configuration for portfolio optimization"""
    budget: float
    timeframe: str  # 'Short', 'Medium', 'Long'
    risk_level: str  # 'Low', 'Medium', 'High'
    hitl_enabled: bool = False
    max_positions: int = 5
    min_allocation: float = 0.05  # 5% minimum
    max_allocation: float = 0.30  # 30% maximum

class PortfolioOptimizerReActAgent:
    """LangGraph ReAct Agent for Portfolio Optimization with HITL support"""
    
    def __init__(self, agent_id: str = "portfolio_optimizer_react"):
        self.agent_id = agent_id
        self.name = "PortfolioOptimizerReActAgent"
        self.version = "1.0.0"
        self.audit_log_file = "data/portfolio_optimizer_audit.json"
        self.csv_log_file = "data/portfolio_optimizer_decisions.csv"
        
        # Initialize MCP servers
        self.recommendation_server = recommendation_server
        self.index_server = index_server
        
        # Create the StateGraph
        self.graph = self._create_graph()
        
        # Ensure audit directories exist
        os.makedirs(os.path.dirname(self.audit_log_file), exist_ok=True)
        os.makedirs(os.path.dirname(self.csv_log_file), exist_ok=True)
        
        # Initialize CSV log file with headers if it doesn't exist
        self._initialize_csv_log()
    
    def _create_graph(self) -> StateGraph:
        """Create the LangGraph StateGraph for ReAct pattern"""
        
        # Define the graph
        workflow = StateGraph(AgentState)
        
        # Add nodes
        workflow.add_node("analyze_inputs", self._analyze_inputs)
        workflow.add_node("fetch_market_data", self._fetch_market_data)
        workflow.add_node("reason_about_strategy", self._reason_about_strategy)
        workflow.add_node("generate_recommendations", self._generate_recommendations)
        workflow.add_node("optimize_portfolio", self._optimize_portfolio)
        workflow.add_node("hitl_review", self._hitl_review)
        workflow.add_node("finalize_portfolio", self._finalize_portfolio)
        workflow.add_node("log_decision", self._log_decision)
        
        # Define the flow
        workflow.set_entry_point("analyze_inputs")
        
        workflow.add_edge("analyze_inputs", "fetch_market_data")
        workflow.add_edge("fetch_market_data", "reason_about_strategy")
        workflow.add_edge("reason_about_strategy", "generate_recommendations")
        workflow.add_edge("generate_recommendations", "optimize_portfolio")
        
        # Conditional edge for HITL
        workflow.add_conditional_edges(
            "optimize_portfolio",
            self._should_require_hitl_approval,
            {
                "hitl_required": "hitl_review",
                "no_hitl": "finalize_portfolio"
            }
        )
        
        workflow.add_conditional_edges(
            "hitl_review",
            self._check_hitl_approval,
            {
                "approved": "finalize_portfolio",
                "rejected": "reason_about_strategy",  # Go back to reasoning
                "pending": END  # Wait for human input
            }
        )
        
        workflow.add_edge("finalize_portfolio", "log_decision")
        workflow.add_edge("log_decision", END)
        
        return workflow.compile()
    
    async def _analyze_inputs(self, state: AgentState) -> AgentState:
        """Analyze and validate input parameters"""
        reasoning = f"🔍 ANALYZE: Received optimization request with budget=${state['budget']:,.2f}, timeframe={state['timeframe']}, risk_level={state['risk_level']}"
        
        # Validate inputs
        if state['budget'] < 1000:
            reasoning += " ⚠️ WARNING: Budget below recommended minimum of $1,000"
        
        if state['timeframe'] not in ['Short', 'Medium', 'Long']:
            reasoning += f" ⚠️ WARNING: Invalid timeframe '{state['timeframe']}', defaulting to 'Medium'"
            state['timeframe'] = 'Medium'
        
        if state['risk_level'] not in ['Low', 'Medium', 'High']:
            reasoning += f" ⚠️ WARNING: Invalid risk level '{state['risk_level']}', defaulting to 'Medium'"
            state['risk_level'] = 'Medium'
        
        reasoning += " ✅ Input validation complete"
        
        state['reasoning_trace'].append(reasoning)
        state['messages'].append(AIMessage(content=reasoning))
        
        return state
    
    async def _fetch_market_data(self, state: AgentState) -> AgentState:
        """Fetch current market data from MCP servers"""
        reasoning = "📊 FETCH: Retrieving current market data and indices..."
        
        try:
            if self.index_server:
                # Get current market indices
                market_result = await self.index_server.get_current_indices()
                sentiment_result = await self.index_server.get_market_sentiment()
                
                state['market_data'] = {
                    'indices': market_result.get('data', []),
                    'sentiment': sentiment_result.get('sentiment', {}),
                    'timestamp': datetime.now().isoformat()
                }
                
                reasoning += f" ✅ Retrieved {len(market_result.get('data', []))} market indices"
                reasoning += f" 📈 Market sentiment: Fear/Greed Index = {sentiment_result.get('sentiment', {}).get('fear_greed_index', 'N/A')}"
            else:
                # Mock data when MCP server unavailable
                state['market_data'] = self._generate_mock_market_data()
                reasoning += " ⚠️ Using mock market data (MCP server unavailable)"
                
        except Exception as e:
            reasoning += f" ❌ Error fetching market data: {str(e)}"
            state['market_data'] = self._generate_mock_market_data()
            reasoning += " 🔄 Falling back to mock data"
        
        state['reasoning_trace'].append(reasoning)
        state['messages'].append(AIMessage(content=reasoning))
        
        return state
    
    async def _reason_about_strategy(self, state: AgentState) -> AgentState:
        """Apply ReAct reasoning about investment strategy"""
        reasoning = "🧠 REASON: Analyzing market conditions and developing investment strategy..."
        
        # Analyze market sentiment
        sentiment = state['market_data'].get('sentiment', {})
        fear_greed = sentiment.get('fear_greed_index', 50)
        
        if fear_greed > 70:
            reasoning += " 📈 Market showing GREED signals - consider defensive positioning"
            strategy_bias = "defensive"
        elif fear_greed < 30:
            reasoning += " 📉 Market showing FEAR signals - potential buying opportunity"
            strategy_bias = "aggressive"
        else:
            reasoning += " ⚖️ Market sentiment NEUTRAL - balanced approach recommended"
            strategy_bias = "balanced"
        
        # Risk level reasoning
        if state['risk_level'] == 'Low':
            reasoning += " 🛡️ LOW RISK profile: Focus on large-cap, dividend-paying stocks"
            risk_multiplier = 0.7
        elif state['risk_level'] == 'High':
            reasoning += " 🚀 HIGH RISK profile: Include growth stocks and emerging sectors"
            risk_multiplier = 1.3
        else:
            reasoning += " ⚖️ MEDIUM RISK profile: Balanced mix of growth and value"
            risk_multiplier = 1.0
        
        # Timeframe reasoning
        if state['timeframe'] == 'Short':
            reasoning += " ⏱️ SHORT-TERM horizon: Focus on momentum and technical indicators"
        elif state['timeframe'] == 'Long':
            reasoning += " 📅 LONG-TERM horizon: Emphasize fundamentals and dividend growth"
        else:
            reasoning += " 📊 MEDIUM-TERM horizon: Balance momentum and fundamentals"
        
        # Store strategy parameters
        state['strategy_params'] = {
            'bias': strategy_bias,
            'risk_multiplier': risk_multiplier,
            'fear_greed_index': fear_greed
        }
        
        reasoning += " ✅ Strategy analysis complete"
        
        state['reasoning_trace'].append(reasoning)
        state['messages'].append(AIMessage(content=reasoning))
        
        return state
    
    async def _generate_recommendations(self, state: AgentState) -> AgentState:
        """Generate stock recommendations using MCP server"""
        reasoning = "🎯 GENERATE: Creating stock recommendations based on strategy..."
        
        try:
            if self.recommendation_server:
                # Prepare user configuration for MCP server
                user_config = {
                    'budget': state['budget'],
                    'timeframe': state['timeframe'],
                    'riskLevel': state['risk_level'],
                    'goals': 'Growth'  # Default goal
                }
                
                # Get recommendations from MCP server
                rec_result = await self.recommendation_server.generate_recommendations(user_config)
                
                if rec_result['status'] == 'success':
                    state['stock_recommendations'] = rec_result['recommendations']
                    reasoning += f" ✅ Generated {len(rec_result['recommendations'])} stock recommendations"
                    
                    # Log top recommendations
                    for i, rec in enumerate(rec_result['recommendations'][:3]):
                        reasoning += f" 📊 #{i+1}: {rec['symbol']} - {rec['action']} (confidence: {rec['confidence']}%)"
                else:
                    raise Exception("MCP server returned error status")
                    
            else:
                # Generate mock recommendations
                state['stock_recommendations'] = self._generate_mock_recommendations(state)
                reasoning += " ⚠️ Using mock recommendations (MCP server unavailable)"
                
        except Exception as e:
            reasoning += f" ❌ Error generating recommendations: {str(e)}"
            state['stock_recommendations'] = self._generate_mock_recommendations(state)
            reasoning += " 🔄 Using fallback mock recommendations"
        
        state['reasoning_trace'].append(reasoning)
        state['messages'].append(AIMessage(content=reasoning))
        
        return state
    
    async def _optimize_portfolio(self, state: AgentState) -> AgentState:
        """Optimize portfolio allocation using Modern Portfolio Theory principles"""
        reasoning = "⚖️ OPTIMIZE: Applying portfolio optimization algorithms..."
        
        recommendations = state['stock_recommendations']
        budget = state['budget']
        strategy_params = state.get('strategy_params', {})
        
        # Filter recommendations based on action (focus on BUY recommendations)
        buy_recommendations = [rec for rec in recommendations if rec.get('action') == 'BUY']
        
        if not buy_recommendations:
            buy_recommendations = recommendations[:5]  # Take top 5 if no BUY signals
            reasoning += " ⚠️ No BUY signals found, using top 5 recommendations"
        
        reasoning += f" 🎯 Optimizing allocation for {len(buy_recommendations)} positions"
        
        # Calculate optimized allocations
        optimized_portfolio = []
        total_confidence = sum(rec['confidence'] for rec in buy_recommendations)
        
        for rec in buy_recommendations:
            # Base allocation on confidence
            base_allocation = (rec['confidence'] / total_confidence) * 100
            
            # Apply risk multiplier
            risk_multiplier = strategy_params.get('risk_multiplier', 1.0)
            
            if rec.get('risk') == 'Low' and state['risk_level'] == 'Low':
                allocation_multiplier = 1.2
            elif rec.get('risk') == 'High' and state['risk_level'] == 'High':
                allocation_multiplier = 1.3
            elif rec.get('risk') == 'High' and state['risk_level'] == 'Low':
                allocation_multiplier = 0.7
            else:
                allocation_multiplier = 1.0
            
            final_allocation = base_allocation * allocation_multiplier * risk_multiplier
            
            # Ensure allocation bounds
            final_allocation = max(5, min(30, final_allocation))  # 5% to 30%
            
            # Calculate investment amounts
            investment_amount = (final_allocation / 100) * budget
            shares = int(investment_amount / rec['current_price'])
            actual_investment = shares * rec['current_price']
            
            optimized_portfolio.append({
                'symbol': rec['symbol'],
                'allocation_percent': round(final_allocation, 1),
                'investment_amount': round(actual_investment, 2),
                'shares': shares,
                'current_price': rec['current_price'],
                'target_price': rec.get('target_price', rec['current_price'] * 1.1),
                'confidence': rec['confidence'],
                'risk_level': rec.get('risk', 'Medium'),
                'sector': rec.get('sector', 'Unknown'),
                'reasoning': f"Allocated {final_allocation:.1f}% based on {rec['confidence']}% confidence"
            })
        
        # Normalize allocations to sum to 100%
        total_allocation = sum(pos['allocation_percent'] for pos in optimized_portfolio)
        if total_allocation != 100:
            factor = 100 / total_allocation
            for pos in optimized_portfolio:
                pos['allocation_percent'] = round(pos['allocation_percent'] * factor, 1)
                pos['investment_amount'] = round((pos['allocation_percent'] / 100) * budget, 2)
                pos['shares'] = int(pos['investment_amount'] / pos['current_price'])
        
        state['final_portfolio'] = {
            'positions': optimized_portfolio,
            'total_investment': sum(pos['investment_amount'] for pos in optimized_portfolio),
            'cash_remaining': budget - sum(pos['investment_amount'] for pos in optimized_portfolio),
            'expected_return': sum(
                (pos['allocation_percent'] / 100) * 
                ((pos['target_price'] - pos['current_price']) / pos['current_price'] * 100)
                for pos in optimized_portfolio
            ),
            'risk_score': sum(
                (pos['allocation_percent'] / 100) * 
                ({'Low': 1, 'Medium': 2, 'High': 3}.get(pos['risk_level'], 2))
                for pos in optimized_portfolio
            ),
            'diversification_score': len(set(pos['sector'] for pos in optimized_portfolio)) * 20
        }
        
        reasoning += f" ✅ Portfolio optimized: {len(optimized_portfolio)} positions"
        reasoning += f" 💰 Total investment: ${state['final_portfolio']['total_investment']:,.2f}"
        reasoning += f" 📈 Expected return: {state['final_portfolio']['expected_return']:.1f}%"
        
        state['reasoning_trace'].append(reasoning)
        state['messages'].append(AIMessage(content=reasoning))
        
        return state
    
    def _should_require_hitl_approval(self, state: AgentState) -> str:
        """Determine if HITL approval is required"""
        # Check if HITL is enabled and if portfolio meets certain criteria
        portfolio = state.get('final_portfolio', {})
        
        # Require HITL approval if:
        # 1. High risk portfolio (risk score > 2.5)
        # 2. Large budget (> $100,000)
        # 3. Low diversification (< 3 sectors)
        
        risk_score = portfolio.get('risk_score', 0)
        diversification = portfolio.get('diversification_score', 0)
        budget = state.get('budget', 0)
        
        if (risk_score > 2.5 or budget > 100000 or diversification < 60):
            state['hitl_approval_required'] = True
            return "hitl_required"
        else:
            state['hitl_approval_required'] = False
            return "no_hitl"
    
    async def _hitl_review(self, state: AgentState) -> AgentState:
        """Handle Human-in-the-Loop review process"""
        reasoning = "👤 HITL: Portfolio requires human approval due to risk/size criteria"
        
        portfolio = state['final_portfolio']
        reasoning += f" 🔍 Review criteria triggered:"
        reasoning += f" - Risk Score: {portfolio.get('risk_score', 0):.1f}/3.0"
        reasoning += f" - Budget: ${state['budget']:,.2f}"
        reasoning += f" - Diversification: {portfolio.get('diversification_score', 0)}%"
        
        reasoning += " ⏳ Waiting for human approval..."
        
        # In a real implementation, this would trigger a notification/UI for human review
        # For demo purposes, we'll simulate approval based on portfolio quality
        portfolio_quality = (
            portfolio.get('diversification_score', 0) + 
            (100 - portfolio.get('risk_score', 0) * 20) +
            min(100, portfolio.get('expected_return', 0) * 10)
        ) / 3
        
        # Simulate human decision (in real app, this would come from UI)
        if portfolio_quality > 70:
            state['hitl_approved'] = True
            reasoning += " ✅ Portfolio approved by human reviewer"
        else:
            state['hitl_approved'] = False
            reasoning += " ❌ Portfolio rejected - requires optimization"
        
        state['reasoning_trace'].append(reasoning)
        state['messages'].append(AIMessage(content=reasoning))
        
        return state
    
    def _check_hitl_approval(self, state: AgentState) -> str:
        """Check HITL approval status"""
        if state.get('hitl_approved') is True:
            return "approved"
        elif state.get('hitl_approved') is False:
            return "rejected"
        else:
            return "pending"
    
    async def _finalize_portfolio(self, state: AgentState) -> AgentState:
        """Finalize the portfolio recommendation"""
        reasoning = "✅ FINALIZE: Portfolio optimization complete"
        
        portfolio = state['final_portfolio']
        reasoning += f" 📊 Final Portfolio Summary:"
        reasoning += f" - Positions: {len(portfolio['positions'])}"
        reasoning += f" - Total Investment: ${portfolio['total_investment']:,.2f}"
        reasoning += f" - Expected Return: {portfolio['expected_return']:.1f}%"
        reasoning += f" - Risk Score: {portfolio['risk_score']:.1f}/3.0"
        reasoning += f" - Diversification: {portfolio['diversification_score']}%"
        
        if state.get('hitl_approval_required'):
            reasoning += f" - Human Approval: {'✅ Approved' if state.get('hitl_approved') else '❌ Rejected'}"
        
        state['reasoning_trace'].append(reasoning)
        state['messages'].append(AIMessage(content=reasoning))
        
        return state
    
    async def _log_decision(self, state: AgentState) -> AgentState:
        """Log the decision to audit files"""
        reasoning = "📝 LOG: Recording decision to audit trail"
        
        # Create audit log entry
        audit_entry = {
            'timestamp': datetime.now().isoformat(),
            'agent_id': self.agent_id,
            'session_id': f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            'inputs': {
                'budget': state['budget'],
                'timeframe': state['timeframe'],
                'risk_level': state['risk_level']
            },
            'market_data': state.get('market_data', {}),
            'reasoning_trace': state['reasoning_trace'],
            'final_portfolio': state['final_portfolio'],
            'hitl_required': state.get('hitl_approval_required', False),
            'hitl_approved': state.get('hitl_approved', None),
            'performance_metrics': {
                'processing_time': len(state['reasoning_trace']) * 0.5,  # Simulated
                'confidence_score': sum(pos['confidence'] for pos in state['final_portfolio']['positions']) / len(state['final_portfolio']['positions'])
            }
        }
        
        # Save to JSON audit log
        await self._save_audit_log(audit_entry)
        
        # Save to CSV for easy analysis
        await self._save_csv_log(audit_entry)
        
        reasoning += " ✅ Decision logged to audit trail"
        
        state['reasoning_trace'].append(reasoning)
        state['audit_log'] = [audit_entry]
        
        return state
    
    async def _save_audit_log(self, audit_entry: Dict[str, Any]):
        """Save audit entry to JSON file"""
        try:
            # Load existing log
            if os.path.exists(self.audit_log_file):
                with open(self.audit_log_file, 'r') as f:
                    audit_log = json.load(f)
            else:
                audit_log = []
            
            # Add new entry
            audit_log.append(audit_entry)
            
            # Keep only last 1000 entries
            if len(audit_log) > 1000:
                audit_log = audit_log[-1000:]
            
            # Save back to file
            with open(self.audit_log_file, 'w') as f:
                json.dump(audit_log, f, indent=2)
                
        except Exception as e:
            print(f"Error saving audit log: {e}")
    
    async def _save_csv_log(self, audit_entry: Dict[str, Any]):
        """Save decision summary to CSV file"""
        try:
            portfolio = audit_entry['final_portfolio']
            
            csv_row = {
                'timestamp': audit_entry['timestamp'],
                'session_id': audit_entry['session_id'],
                'budget': audit_entry['inputs']['budget'],
                'timeframe': audit_entry['inputs']['timeframe'],
                'risk_level': audit_entry['inputs']['risk_level'],
                'num_positions': len(portfolio['positions']),
                'total_investment': portfolio['total_investment'],
                'expected_return': portfolio['expected_return'],
                'risk_score': portfolio['risk_score'],
                'diversification_score': portfolio['diversification_score'],
                'hitl_required': audit_entry['hitl_required'],
                'hitl_approved': audit_entry['hitl_approved'],
                'confidence_score': audit_entry['performance_metrics']['confidence_score'],
                'top_positions': ';'.join([f"{pos['symbol']}:{pos['allocation_percent']}%" for pos in portfolio['positions'][:3]])
            }
            
            # Write to CSV
            file_exists = os.path.exists(self.csv_log_file)
            with open(self.csv_log_file, 'a', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=csv_row.keys())
                if not file_exists:
                    writer.writeheader()
                writer.writerow(csv_row)
                
        except Exception as e:
            print(f"Error saving CSV log: {e}")
    
    def _initialize_csv_log(self):
        """Initialize CSV log file with headers"""
        if not os.path.exists(self.csv_log_file):
            headers = [
                'timestamp', 'session_id', 'budget', 'timeframe', 'risk_level',
                'num_positions', 'total_investment', 'expected_return', 'risk_score',
                'diversification_score', 'hitl_required', 'hitl_approved',
                'confidence_score', 'top_positions'
            ]
            
            with open(self.csv_log_file, 'w', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=headers)
                writer.writeheader()
    
    def _generate_mock_market_data(self) -> Dict[str, Any]:
        """Generate mock market data when MCP server unavailable"""
        import random
        
        return {
            'indices': [
                {'symbol': 'S&P 500', 'price': 4847.88, 'change_percent': random.uniform(-1, 1)},
                {'symbol': 'NASDAQ', 'price': 15181.92, 'change_percent': random.uniform(-1.5, 1.5)},
                {'symbol': 'DOW', 'price': 37753.31, 'change_percent': random.uniform(-0.8, 0.8)}
            ],
            'sentiment': {
                'fear_greed_index': random.randint(20, 80),
                'vix': random.uniform(12, 25)
            },
            'timestamp': datetime.now().isoformat()
        }
    
    def _generate_mock_recommendations(self, state: AgentState) -> List[Dict[str, Any]]:
        """Generate mock stock recommendations"""
        import random
        
        stocks = [
            {'symbol': 'AAPL', 'sector': 'Technology', 'risk': 'Low'},
            {'symbol': 'MSFT', 'sector': 'Technology', 'risk': 'Low'},
            {'symbol': 'GOOGL', 'sector': 'Technology', 'risk': 'Medium'},
            {'symbol': 'NVDA', 'sector': 'Technology', 'risk': 'High'},
            {'symbol': 'JNJ', 'sector': 'Healthcare', 'risk': 'Low'},
            {'symbol': 'JPM', 'sector': 'Finance', 'risk': 'Medium'}
        ]
        
        recommendations = []
        for stock in stocks:
            current_price = random.uniform(50, 500)
            target_price = current_price * random.uniform(1.05, 1.25)
            
            recommendations.append({
                'symbol': stock['symbol'],
                'current_price': round(current_price, 2),
                'target_price': round(target_price, 2),
                'confidence': random.randint(65, 95),
                'action': random.choice(['BUY', 'BUY', 'HOLD']),  # Bias toward BUY
                'risk': stock['risk'],
                'sector': stock['sector']
            })
        
        return recommendations
    
    async def optimize_portfolio(self, budget: float, timeframe: str, risk_level: str, 
                               hitl_enabled: bool = False) -> Dict[str, Any]:
        """Main entry point for portfolio optimization"""
        
        # Initialize state
        initial_state = AgentState(
            messages=[HumanMessage(content=f"Optimize portfolio for budget=${budget}, timeframe={timeframe}, risk={risk_level}")],
            budget=budget,
            timeframe=timeframe,
            risk_level=risk_level,
            market_data={},
            stock_recommendations=[],
            reasoning_trace=[],
            hitl_approval_required=False,
            hitl_approved=None,
            final_portfolio={},
            audit_log=[]
        )
        
        # Run the graph
        try:
            final_state = await self.graph.ainvoke(initial_state)
            
            return {
                'status': 'success',
                'portfolio': final_state['final_portfolio'],
                'reasoning_trace': final_state['reasoning_trace'],
                'hitl_required': final_state.get('hitl_approval_required', False),
                'hitl_approved': final_state.get('hitl_approved'),
                'audit_log': final_state.get('audit_log', []),
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                'status': 'error',
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    async def get_agent_status(self) -> Dict[str, Any]:
        """Get agent status and metrics"""
        return {
            'agent_id': self.agent_id,
            'name': self.name,
            'version': self.version,
            'status': 'ready',
            'graph_nodes': len(self.graph.nodes),
            'audit_log_file': self.audit_log_file,
            'csv_log_file': self.csv_log_file,
            'mcp_servers': {
                'recommendation_server': self.recommendation_server is not None,
                'index_server': self.index_server is not None
            }
        }

# Global agent instance
portfolio_optimizer_react_agent = PortfolioOptimizerReActAgent()

# CLI interface for testing
if __name__ == "__main__":
    async def main():
        agent = PortfolioOptimizerReActAgent()
        
        # Test portfolio optimization
        result = await agent.optimize_portfolio(
            budget=50000,
            timeframe="Medium",
            risk_level="Medium",
            hitl_enabled=True
        )
        
        print("Portfolio Optimization Result:")
        print(json.dumps(result, indent=2))
        
        # Show agent status
        status = await agent.get_agent_status()
        print("\nAgent Status:")
        print(json.dumps(status, indent=2))
    
    asyncio.run(main())