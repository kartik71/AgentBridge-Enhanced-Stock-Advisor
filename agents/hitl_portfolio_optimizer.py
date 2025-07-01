"""
HITL-Enhanced Portfolio Optimizer Agent
Adds Human-in-the-Loop capabilities to the Portfolio Optimizer
"""

import asyncio
import json
from datetime import datetime
from typing import Dict, List, Any, Optional, TypedDict, Annotated
from dataclasses import dataclass

from langgraph.graph import StateGraph, END
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage

from .hitl_enhanced_agent import HITLEnhancedAgent
from .hitl_manager import HITLStatus, HITLDecision
from .portfolio_optimizer_react.agent import PortfolioOptimizerReActAgent

# State definition for the agent
class PortfolioOptimizerState(TypedDict):
    messages: Annotated[List[BaseMessage], "The conversation messages"]
    budget: float
    timeframe: str
    risk_level: str
    market_data: Dict[str, Any]
    stock_recommendations: List[Dict[str, Any]]
    reasoning_trace: List[str]
    hitl_approval_required: bool
    hitl_approval_status: str  # pending, approved, rejected, bypassed
    hitl_decision_id: Optional[str]
    final_portfolio: Dict[str, Any]
    audit_log: List[Dict[str, Any]]

class HITLPortfolioOptimizerAgent(HITLEnhancedAgent[PortfolioOptimizerState]):
    """Portfolio Optimizer with HITL capabilities"""
    
    def __init__(self, agent_id: str = "hitl_portfolio_optimizer"):
        super().__init__(agent_id, "HITL Portfolio Optimizer")
        
        # Initialize base agent
        self.base_agent = PortfolioOptimizerReActAgent()
        
        # Create enhanced StateGraph with HITL
        self.graph = self._create_hitl_graph()
    
    def _create_hitl_graph(self) -> StateGraph:
        """Create StateGraph with HITL decision points"""
        
        workflow = StateGraph(PortfolioOptimizerState)
        
        # Add nodes from base agent
        workflow.add_node("analyze_inputs", self._analyze_inputs)
        workflow.add_node("fetch_market_data", self._fetch_market_data)
        workflow.add_node("reason_about_strategy", self._reason_about_strategy)
        workflow.add_node("generate_recommendations", self._generate_recommendations)
        workflow.add_node("optimize_portfolio", self._optimize_portfolio)
        
        # Add HITL-specific nodes
        workflow.add_node("request_hitl_approval", self._request_hitl_approval)
        workflow.add_node("wait_for_hitl_decision", self._wait_for_hitl_decision)
        workflow.add_node("process_hitl_decision", self._process_hitl_decision)
        
        # Add remaining nodes
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
            self._should_request_hitl_approval,
            {
                "hitl_required": "request_hitl_approval",
                "no_hitl": "finalize_portfolio"
            }
        )
        
        workflow.add_edge("request_hitl_approval", "wait_for_hitl_decision")
        
        workflow.add_conditional_edges(
            "wait_for_hitl_decision",
            self._check_hitl_decision,
            {
                "approved": "finalize_portfolio",
                "rejected": "reason_about_strategy",  # Go back to reasoning
                "pending": END  # Wait for human input
            }
        )
        
        workflow.add_edge("process_hitl_decision", "finalize_portfolio")
        workflow.add_edge("finalize_portfolio", "log_decision")
        workflow.add_edge("log_decision", END)
        
        return workflow.compile()
    
    async def _analyze_inputs(self, state: PortfolioOptimizerState) -> PortfolioOptimizerState:
        """Analyze and validate input parameters"""
        # Delegate to base agent
        base_state = await self.base_agent._analyze_inputs(state)
        
        # Add HITL-specific reasoning
        reasoning = f"🔍 HITL STATUS: HITL override is {'enabled' if self.hitl_enabled else 'disabled'}"
        reasoning += f", Autonomous mode is {'enabled' if self.autonomous_mode else 'disabled'}"
        
        if self.hitl_enabled and not self.autonomous_mode:
            reasoning += "\n⚠️ Human approval will be required for final portfolio"
        else:
            reasoning += "\n✅ Autonomous mode will bypass human approval"
        
        base_state['reasoning_trace'].append(reasoning)
        base_state['messages'].append(AIMessage(content=reasoning))
        
        return base_state
    
    async def _fetch_market_data(self, state: PortfolioOptimizerState) -> PortfolioOptimizerState:
        """Fetch current market data"""
        # Delegate to base agent
        return await self.base_agent._fetch_market_data(state)
    
    async def _reason_about_strategy(self, state: PortfolioOptimizerState) -> PortfolioOptimizerState:
        """Apply ReAct reasoning about investment strategy"""
        # Delegate to base agent
        return await self.base_agent._reason_about_strategy(state)
    
    async def _generate_recommendations(self, state: PortfolioOptimizerState) -> PortfolioOptimizerState:
        """Generate stock recommendations"""
        # Delegate to base agent
        return await self.base_agent._generate_recommendations(state)
    
    async def _optimize_portfolio(self, state: PortfolioOptimizerState) -> PortfolioOptimizerState:
        """Optimize portfolio allocation"""
        # Delegate to base agent
        base_state = await self.base_agent._optimize_portfolio(state)
        
        # Determine if HITL should be requested
        should_request_hitl = await self.should_request_hitl(base_state)
        base_state['hitl_approval_required'] = should_request_hitl
        
        return base_state
    
    def _should_request_hitl_approval(self, state: PortfolioOptimizerState) -> str:
        """Determine if HITL approval should be requested"""
        if state['hitl_approval_required']:
            return "hitl_required"
        else:
            return "no_hitl"
    
    async def _request_hitl_approval(self, state: PortfolioOptimizerState) -> PortfolioOptimizerState:
        """Request HITL approval for portfolio"""
        reasoning = "👤 HITL: Requesting human approval for portfolio allocation"
        
        portfolio = state['final_portfolio']
        
        # Prepare decision data
        decision_data = {
            "portfolio": portfolio,
            "budget": state['budget'],
            "timeframe": state['timeframe'],
            "risk_level": state['risk_level'],
            "reasoning_trace": state['reasoning_trace']
        }
        
        # Create description for human reviewer
        description = (
            f"Portfolio allocation for ${state['budget']:,.2f} with {state['risk_level']} risk "
            f"and {state['timeframe']} timeframe. "
            f"Contains {len(portfolio['positions'])} positions with expected return of {portfolio['expected_return']:.1f}%."
        )
        
        # Request HITL approval
        decision = await self.request_hitl_approval(
            decision_type="portfolio_approval",
            decision_data=decision_data,
            description=description
        )
        
        # Update state with decision ID
        state['hitl_decision_id'] = decision.decision_id
        state['hitl_approval_status'] = decision.status
        
        if decision.status == HITLStatus.BYPASSED:
            reasoning += f" ⚠️ HITL bypassed due to autonomous mode"
        else:
            reasoning += f" ⏳ Waiting for human approval (Decision ID: {decision.decision_id})"
        
        state['reasoning_trace'].append(reasoning)
        state['messages'].append(AIMessage(content=reasoning))
        
        return state
    
    async def _wait_for_hitl_decision(self, state: PortfolioOptimizerState) -> PortfolioOptimizerState:
        """Wait for human decision"""
        reasoning = "⏳ HITL: Waiting for human decision..."
        
        if not state['hitl_decision_id']:
            reasoning += " ❌ Error: No decision ID found"
            state['hitl_approval_status'] = "error"
        else:
            # Get current decision
            decision_dict = hitl_manager.get_decision(state['hitl_decision_id'])
            
            if not decision_dict:
                reasoning += f" ❌ Error: Decision {state['hitl_decision_id']} not found"
                state['hitl_approval_status'] = "error"
            else:
                decision = HITLDecision.from_dict(decision_dict)
                state['hitl_approval_status'] = decision.status
                
                if decision.status == HITLStatus.APPROVED:
                    reasoning += f" ✅ Portfolio approved by human reviewer"
                    if decision.user_comments:
                        reasoning += f" 💬 Comments: {decision.user_comments}"
                elif decision.status == HITLStatus.REJECTED:
                    reasoning += f" ❌ Portfolio rejected by human reviewer"
                    if decision.user_comments:
                        reasoning += f" 💬 Comments: {decision.user_comments}"
                elif decision.status == HITLStatus.TIMEOUT:
                    reasoning += f" ⏰ Decision timed out after {decision.timeout_seconds} seconds"
                    state['hitl_approval_status'] = "timeout"
                elif decision.status == HITLStatus.BYPASSED:
                    reasoning += f" 🔄 Decision bypassed due to autonomous mode"
                else:
                    reasoning += f" ⏳ Still waiting for human decision"
        
        state['reasoning_trace'].append(reasoning)
        state['messages'].append(AIMessage(content=reasoning))
        
        return state
    
    def _check_hitl_decision(self, state: PortfolioOptimizerState) -> str:
        """Check HITL decision status"""
        status = state['hitl_approval_status']
        
        if status == HITLStatus.APPROVED or status == HITLStatus.BYPASSED:
            return "approved"
        elif status == HITLStatus.REJECTED:
            return "rejected"
        else:
            return "pending"
    
    async def _process_hitl_decision(self, state: PortfolioOptimizerState) -> PortfolioOptimizerState:
        """Process the HITL decision"""
        # This node is called when a decision transitions from pending to approved/rejected
        reasoning = "👤 HITL: Processing human decision"
        
        decision_dict = hitl_manager.get_decision(state['hitl_decision_id'])
        if decision_dict:
            decision = HITLDecision.from_dict(decision_dict)
            
            if decision.status == HITLStatus.APPROVED:
                reasoning += " ✅ Portfolio approved - proceeding with implementation"
            elif decision.status == HITLStatus.REJECTED:
                reasoning += " ❌ Portfolio rejected - returning to strategy phase"
                # Could modify state here based on user feedback
            else:
                reasoning += f" ⚠️ Unexpected decision status: {decision.status}"
        else:
            reasoning += " ❌ Error: Decision not found"
        
        state['reasoning_trace'].append(reasoning)
        state['messages'].append(AIMessage(content=reasoning))
        
        return state
    
    async def _finalize_portfolio(self, state: PortfolioOptimizerState) -> PortfolioOptimizerState:
        """Finalize the portfolio recommendation"""
        # Delegate to base agent
        base_state = await self.base_agent._finalize_portfolio(state)
        
        # Add HITL-specific information
        if state.get('hitl_approval_required', False):
            reasoning = f"👤 HITL: Portfolio finalized with human oversight"
            reasoning += f" - Status: {state.get('hitl_approval_status', 'unknown')}"
            
            base_state['reasoning_trace'].append(reasoning)
            base_state['messages'].append(AIMessage(content=reasoning))
        
        return base_state
    
    async def _log_decision(self, state: PortfolioOptimizerState) -> PortfolioOptimizerState:
        """Log the decision to audit files"""
        # Delegate to base agent
        base_state = await self.base_agent._log_decision(state)
        
        # Add HITL-specific logging
        if state.get('hitl_decision_id'):
            # Add HITL information to audit log
            for audit_entry in base_state['audit_log']:
                audit_entry['hitl_enabled'] = self.hitl_enabled
                audit_entry['hitl_required'] = state.get('hitl_approval_required', False)
                audit_entry['hitl_status'] = state.get('hitl_approval_status', 'none')
                audit_entry['hitl_decision_id'] = state.get('hitl_decision_id')
        
        return base_state
    
    async def should_request_hitl(self, state: PortfolioOptimizerState) -> bool:
        """Determine if HITL should be requested"""
        # Check if HITL is enabled for this agent
        if not self.hitl_enabled or self.autonomous_mode:
            return False
        
        # Check portfolio criteria that would require human review
        portfolio = state.get('final_portfolio', {})
        
        # High risk portfolio (risk score > 2.5)
        risk_score = portfolio.get('risk_score', 0)
        if risk_score > 2.5:
            return True
        
        # Large budget (> $100,000)
        budget = state.get('budget', 0)
        if budget > 100000:
            return True
        
        # Low diversification (< 3 sectors)
        diversification = portfolio.get('diversification_score', 100)
        if diversification < 60:
            return True
        
        # High expected return (potentially unrealistic)
        expected_return = portfolio.get('expected_return', 0)
        if expected_return > 20:
            return True
        
        return False
    
    async def process_hitl_decision(self, decision: HITLDecision, state: PortfolioOptimizerState) -> PortfolioOptimizerState:
        """Process a HITL decision"""
        if decision.status == HITLStatus.APPROVED:
            # Proceed with original portfolio
            state['hitl_approval_status'] = HITLStatus.APPROVED
        elif decision.status == HITLStatus.REJECTED:
            # Could modify portfolio based on feedback
            state['hitl_approval_status'] = HITLStatus.REJECTED
        elif decision.status == HITLStatus.BYPASSED:
            # Autonomous mode, proceed with original portfolio
            state['hitl_approval_status'] = HITLStatus.BYPASSED
        else:
            # Decision still pending or timed out
            state['hitl_approval_status'] = decision.status
        
        return state
    
    async def optimize_portfolio(
        self,
        budget: float,
        timeframe: str,
        risk_level: str,
        hitl_enabled: bool = False,
        autonomous_mode: bool = True
    ) -> Dict[str, Any]:
        """Main entry point for HITL-enhanced portfolio optimization"""
        
        # Update HITL settings
        self.set_hitl_enabled(hitl_enabled)
        self.set_autonomous_mode(autonomous_mode)
        
        # Initialize state
        initial_state = PortfolioOptimizerState(
            messages=[HumanMessage(content=f"Optimize portfolio with HITL capabilities")],
            budget=budget,
            timeframe=timeframe,
            risk_level=risk_level,
            market_data={},
            stock_recommendations=[],
            reasoning_trace=[],
            hitl_approval_required=False,
            hitl_approval_status="none",
            hitl_decision_id=None,
            final_portfolio={},
            audit_log=[]
        )
        
        try:
            # Run the HITL-enhanced workflow
            final_state = await self.graph.ainvoke(initial_state)
            
            return {
                'status': 'success',
                'portfolio': final_state['final_portfolio'],
                'reasoning_trace': final_state['reasoning_trace'],
                'hitl_required': final_state.get('hitl_approval_required', False),
                'hitl_status': final_state.get('hitl_approval_status', 'none'),
                'hitl_decision_id': final_state.get('hitl_decision_id'),
                'audit_log': final_state.get('audit_log', []),
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                'status': 'error',
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }

# Global agent instance
hitl_portfolio_optimizer = HITLPortfolioOptimizerAgent()