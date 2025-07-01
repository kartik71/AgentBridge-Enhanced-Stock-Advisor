"""
HITL-Enhanced Timing Advisor Agent
Adds Human-in-the-Loop capabilities to the Timing Advisor
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
from .timing_advisor_react.agent import TimingAdvisorReActAgent

# State definition for the agent
class TimingAdvisorState(TypedDict):
    messages: Annotated[List[BaseMessage], "The conversation messages"]
    timeframe: str
    analysis_depth: str
    market_data: Dict[str, Any]
    technical_indicators: Dict[str, Any]
    timing_signals: Dict[str, Any]
    market_regime: Dict[str, Any]
    reasoning_trace: List[str]
    hitl_approval_required: bool
    hitl_approval_status: str  # pending, approved, rejected, bypassed
    hitl_decision_id: Optional[str]
    final_recommendations: Dict[str, Any]
    audit_log: List[Dict[str, Any]]

class HITLTimingAdvisorAgent(HITLEnhancedAgent[TimingAdvisorState]):
    """Timing Advisor with HITL capabilities"""
    
    def __init__(self, agent_id: str = "hitl_timing_advisor"):
        super().__init__(agent_id, "HITL Timing Advisor")
        
        # Initialize base agent
        self.base_agent = TimingAdvisorReActAgent()
        
        # Create enhanced StateGraph with HITL
        self.graph = self._create_hitl_graph()
    
    def _create_hitl_graph(self) -> StateGraph:
        """Create StateGraph with HITL decision points"""
        
        workflow = StateGraph(TimingAdvisorState)
        
        # Add nodes from base agent
        workflow.add_node("analyze_timeframe", self._analyze_timeframe)
        workflow.add_node("collect_market_data", self._collect_market_data)
        workflow.add_node("calculate_technical_indicators", self._calculate_technical_indicators)
        workflow.add_node("generate_timing_signals", self._generate_timing_signals)
        workflow.add_node("determine_market_regime", self._determine_market_regime)
        workflow.add_node("reason_about_timing", self._reason_about_timing)
        
        # Add HITL-specific nodes
        workflow.add_node("request_hitl_approval", self._request_hitl_approval)
        workflow.add_node("wait_for_hitl_decision", self._wait_for_hitl_decision)
        workflow.add_node("process_hitl_decision", self._process_hitl_decision)
        
        # Add remaining nodes
        workflow.add_node("finalize_recommendations", self._finalize_recommendations)
        workflow.add_node("log_analysis", self._log_analysis)
        
        # Define the flow
        workflow.set_entry_point("analyze_timeframe")
        
        workflow.add_edge("analyze_timeframe", "collect_market_data")
        workflow.add_edge("collect_market_data", "calculate_technical_indicators")
        workflow.add_edge("calculate_technical_indicators", "generate_timing_signals")
        workflow.add_edge("generate_timing_signals", "determine_market_regime")
        workflow.add_edge("determine_market_regime", "reason_about_timing")
        
        # Conditional edge for HITL
        workflow.add_conditional_edges(
            "reason_about_timing",
            self._should_request_hitl_approval,
            {
                "hitl_required": "request_hitl_approval",
                "no_hitl": "finalize_recommendations"
            }
        )
        
        workflow.add_edge("request_hitl_approval", "wait_for_hitl_decision")
        
        workflow.add_conditional_edges(
            "wait_for_hitl_decision",
            self._check_hitl_decision,
            {
                "approved": "finalize_recommendations",
                "rejected": "generate_timing_signals",  # Go back to signal generation
                "pending": END  # Wait for human input
            }
        )
        
        workflow.add_edge("process_hitl_decision", "finalize_recommendations")
        workflow.add_edge("finalize_recommendations", "log_analysis")
        workflow.add_edge("log_analysis", END)
        
        return workflow.compile()
    
    async def _analyze_timeframe(self, state: TimingAdvisorState) -> TimingAdvisorState:
        """Analyze and validate timeframe parameters"""
        # Delegate to base agent
        base_state = await self.base_agent._analyze_timeframe(state)
        
        # Add HITL-specific reasoning
        reasoning = f"🔍 HITL STATUS: HITL override is {'enabled' if self.hitl_enabled else 'disabled'}"
        reasoning += f", Autonomous mode is {'enabled' if self.autonomous_mode else 'disabled'}"
        
        if self.hitl_enabled and not self.autonomous_mode:
            reasoning += "\n⚠️ Human approval will be required for timing recommendations"
        else:
            reasoning += "\n✅ Autonomous mode will bypass human approval"
        
        base_state['reasoning_trace'].append(reasoning)
        base_state['messages'].append(AIMessage(content=reasoning))
        
        return base_state
    
    async def _collect_market_data(self, state: TimingAdvisorState) -> TimingAdvisorState:
        """Collect market data for timing analysis"""
        # Delegate to base agent
        return await self.base_agent._collect_market_data(state)
    
    async def _calculate_technical_indicators(self, state: TimingAdvisorState) -> TimingAdvisorState:
        """Calculate technical indicators for timing analysis"""
        # Delegate to base agent
        return await self.base_agent._calculate_technical_indicators(state)
    
    async def _generate_timing_signals(self, state: TimingAdvisorState) -> TimingAdvisorState:
        """Generate timing signals based on technical indicators"""
        # Delegate to base agent
        return await self.base_agent._generate_timing_signals(state)
    
    async def _determine_market_regime(self, state: TimingAdvisorState) -> TimingAdvisorState:
        """Determine current market regime"""
        # Delegate to base agent
        return await self.base_agent._determine_market_regime(state)
    
    async def _reason_about_timing(self, state: TimingAdvisorState) -> TimingAdvisorState:
        """Apply ReAct reasoning about market timing"""
        # Delegate to base agent
        base_state = await self.base_agent._reason_about_timing(state)
        
        # Determine if HITL should be requested
        should_request_hitl = await self.should_request_hitl(base_state)
        base_state['hitl_approval_required'] = should_request_hitl
        
        return base_state
    
    def _should_request_hitl_approval(self, state: TimingAdvisorState) -> str:
        """Determine if HITL approval should be requested"""
        if state['hitl_approval_required']:
            return "hitl_required"
        else:
            return "no_hitl"
    
    async def _request_hitl_approval(self, state: TimingAdvisorState) -> TimingAdvisorState:
        """Request HITL approval for timing recommendations"""
        reasoning = "👤 HITL: Requesting human approval for timing recommendations"
        
        timing_analysis = state['timing_analysis']
        market_regime = state['market_regime']
        
        # Prepare decision data
        decision_data = {
            "timing_analysis": timing_analysis,
            "market_regime": market_regime,
            "timeframe": state['timeframe'],
            "reasoning_trace": state['reasoning_trace']
        }
        
        # Create description for human reviewer
        description = (
            f"Market timing analysis for {state['timeframe']} timeframe. "
            f"Market regime: {market_regime.get('description', 'unknown')}. "
            f"Overall timing: {timing_analysis.get('overall_timing', 'NEUTRAL')} "
            f"with {timing_analysis.get('timing_confidence', 0)}% confidence."
        )
        
        # Request HITL approval
        decision = await self.request_hitl_approval(
            decision_type="timing_approval",
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
    
    async def _wait_for_hitl_decision(self, state: TimingAdvisorState) -> TimingAdvisorState:
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
                    reasoning += f" ✅ Timing recommendations approved by human reviewer"
                    if decision.user_comments:
                        reasoning += f" 💬 Comments: {decision.user_comments}"
                elif decision.status == HITLStatus.REJECTED:
                    reasoning += f" ❌ Timing recommendations rejected by human reviewer"
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
    
    def _check_hitl_decision(self, state: TimingAdvisorState) -> str:
        """Check HITL decision status"""
        status = state['hitl_approval_status']
        
        if status == HITLStatus.APPROVED or status == HITLStatus.BYPASSED:
            return "approved"
        elif status == HITLStatus.REJECTED:
            return "rejected"
        else:
            return "pending"
    
    async def _process_hitl_decision(self, state: TimingAdvisorState) -> TimingAdvisorState:
        """Process the HITL decision"""
        # This node is called when a decision transitions from pending to approved/rejected
        reasoning = "👤 HITL: Processing human decision"
        
        decision_dict = hitl_manager.get_decision(state['hitl_decision_id'])
        if decision_dict:
            decision = HITLDecision.from_dict(decision_dict)
            
            if decision.status == HITLStatus.APPROVED:
                reasoning += " ✅ Timing recommendations approved - proceeding with finalization"
            elif decision.status == HITLStatus.REJECTED:
                reasoning += " ❌ Timing recommendations rejected - returning to signal generation"
                # Could modify state here based on user feedback
            else:
                reasoning += f" ⚠️ Unexpected decision status: {decision.status}"
        else:
            reasoning += " ❌ Error: Decision not found"
        
        state['reasoning_trace'].append(reasoning)
        state['messages'].append(AIMessage(content=reasoning))
        
        return state
    
    async def _finalize_recommendations(self, state: TimingAdvisorState) -> TimingAdvisorState:
        """Finalize timing recommendations"""
        # Delegate to base agent
        base_state = await self.base_agent._finalize_recommendations(state)
        
        # Add HITL-specific information
        if state.get('hitl_approval_required', False):
            reasoning = f"👤 HITL: Recommendations finalized with human oversight"
            reasoning += f" - Status: {state.get('hitl_approval_status', 'unknown')}"
            
            base_state['reasoning_trace'].append(reasoning)
            base_state['messages'].append(AIMessage(content=reasoning))
        
        return base_state
    
    async def _log_analysis(self, state: TimingAdvisorState) -> TimingAdvisorState:
        """Log the timing analysis to audit files"""
        # Delegate to base agent
        base_state = await self.base_agent._log_analysis(state)
        
        # Add HITL-specific logging
        if state.get('hitl_decision_id'):
            # Add HITL information to audit log
            for audit_entry in base_state['audit_log']:
                audit_entry['hitl_enabled'] = self.hitl_enabled
                audit_entry['hitl_required'] = state.get('hitl_approval_required', False)
                audit_entry['hitl_status'] = state.get('hitl_approval_status', 'none')
                audit_entry['hitl_decision_id'] = state.get('hitl_decision_id')
        
        return base_state
    
    async def should_request_hitl(self, state: TimingAdvisorState) -> bool:
        """Determine if HITL should be requested"""
        # Check if HITL is enabled for this agent
        if not self.hitl_enabled or self.autonomous_mode:
            return False
        
        # Check timing criteria that would require human review
        timing_analysis = state.get('timing_analysis', {})
        market_regime = state.get('market_regime', {})
        
        # Strong signals in either direction
        overall_timing = timing_analysis.get('overall_timing', 'NEUTRAL')
        if 'STRONG' in overall_timing:
            return True
        
        # Extreme market conditions
        sentiment_regime = market_regime.get('sentiment_regime', 'neutral')
        if sentiment_regime in ['extreme_fear', 'extreme_greed']:
            return True
        
        # Low confidence in analysis
        timing_confidence = timing_analysis.get('timing_confidence', 80)
        if timing_confidence < 60:
            return True
        
        # High volatility regime
        volatility_regime = market_regime.get('volatility_regime', 'normal_volatility')
        if volatility_regime == 'high_volatility':
            return True
        
        return False
    
    async def process_hitl_decision(self, decision: HITLDecision, state: TimingAdvisorState) -> TimingAdvisorState:
        """Process a HITL decision"""
        if decision.status == HITLStatus.APPROVED:
            # Proceed with original recommendations
            state['hitl_approval_status'] = HITLStatus.APPROVED
        elif decision.status == HITLStatus.REJECTED:
            # Could modify recommendations based on feedback
            state['hitl_approval_status'] = HITLStatus.REJECTED
        elif decision.status == HITLStatus.BYPASSED:
            # Autonomous mode, proceed with original recommendations
            state['hitl_approval_status'] = HITLStatus.BYPASSED
        else:
            # Decision still pending or timed out
            state['hitl_approval_status'] = decision.status
        
        return state
    
    async def analyze_market_timing(
        self,
        timeframe: str = "medium",
        analysis_depth: str = "advanced",
        hitl_enabled: bool = False,
        autonomous_mode: bool = True
    ) -> Dict[str, Any]:
        """Main entry point for HITL-enhanced market timing analysis"""
        
        # Update HITL settings
        self.set_hitl_enabled(hitl_enabled)
        self.set_autonomous_mode(autonomous_mode)
        
        # Initialize state
        initial_state = TimingAdvisorState(
            messages=[HumanMessage(content=f"Analyze market timing with HITL capabilities")],
            timeframe=timeframe,
            analysis_depth=analysis_depth,
            market_data={},
            technical_indicators={},
            timing_signals={},
            market_regime={},
            reasoning_trace=[],
            hitl_approval_required=False,
            hitl_approval_status="none",
            hitl_decision_id=None,
            final_recommendations={},
            audit_log=[]
        )
        
        try:
            # Run the HITL-enhanced workflow
            final_state = await self.graph.ainvoke(initial_state)
            
            return {
                'status': 'success',
                'recommendations': final_state['final_recommendations'],
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
hitl_timing_advisor = HITLTimingAdvisorAgent()