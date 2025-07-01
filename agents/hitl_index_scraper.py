"""
HITL-Enhanced Index Scraper Agent
Adds Human-in-the-Loop capabilities to the Index Scraper
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
from .index_scraper_react.agent import IndexScraperReActAgent

# State definition for the agent
class IndexScraperState(TypedDict):
    messages: Annotated[List[BaseMessage], "The conversation messages"]
    data_sources: List[str]
    collection_frequency: int  # seconds
    market_indices: List[Dict[str, Any]]
    historical_data: Dict[str, Any]
    market_sentiment: Dict[str, Any]
    reasoning_trace: List[str]
    hitl_approval_required: bool
    hitl_approval_status: str  # pending, approved, rejected, bypassed
    hitl_decision_id: Optional[str]
    final_data: Dict[str, Any]
    audit_log: List[Dict[str, Any]]

class HITLIndexScraperAgent(HITLEnhancedAgent[IndexScraperState]):
    """Index Scraper with HITL capabilities"""
    
    def __init__(self, agent_id: str = "hitl_index_scraper"):
        super().__init__(agent_id, "HITL Index Scraper")
        
        # Initialize base agent
        self.base_agent = IndexScraperReActAgent()
        
        # Create enhanced StateGraph with HITL
        self.graph = self._create_hitl_graph()
    
    def _create_hitl_graph(self) -> StateGraph:
        """Create StateGraph with HITL decision points"""
        
        workflow = StateGraph(IndexScraperState)
        
        # Add nodes from base agent
        workflow.add_node("analyze_sources", self._analyze_sources)
        workflow.add_node("validate_connections", self._validate_connections)
        workflow.add_node("collect_current_data", self._collect_current_data)
        workflow.add_node("fetch_historical_data", self._fetch_historical_data)
        workflow.add_node("analyze_market_sentiment", self._analyze_market_sentiment)
        
        # Add HITL-specific nodes
        workflow.add_node("request_hitl_approval", self._request_hitl_approval)
        workflow.add_node("wait_for_hitl_decision", self._wait_for_hitl_decision)
        workflow.add_node("process_hitl_decision", self._process_hitl_decision)
        
        # Add remaining nodes
        workflow.add_node("finalize_data", self._finalize_data)
        workflow.add_node("log_collection", self._log_collection)
        
        # Define the flow
        workflow.set_entry_point("analyze_sources")
        
        workflow.add_edge("analyze_sources", "validate_connections")
        workflow.add_edge("validate_connections", "collect_current_data")
        workflow.add_edge("collect_current_data", "fetch_historical_data")
        workflow.add_edge("fetch_historical_data", "analyze_market_sentiment")
        
        # Conditional edge for HITL
        workflow.add_conditional_edges(
            "analyze_market_sentiment",
            self._should_request_hitl_approval,
            {
                "hitl_required": "request_hitl_approval",
                "no_hitl": "finalize_data"
            }
        )
        
        workflow.add_edge("request_hitl_approval", "wait_for_hitl_decision")
        
        workflow.add_conditional_edges(
            "wait_for_hitl_decision",
            self._check_hitl_decision,
            {
                "approved": "finalize_data",
                "rejected": "collect_current_data",  # Go back to data collection
                "pending": END  # Wait for human input
            }
        )
        
        workflow.add_edge("process_hitl_decision", "finalize_data")
        workflow.add_edge("finalize_data", "log_collection")
        workflow.add_edge("log_collection", END)
        
        return workflow.compile()
    
    async def _analyze_sources(self, state: IndexScraperState) -> IndexScraperState:
        """Analyze and validate data sources"""
        # Delegate to base agent
        base_state = await self.base_agent._analyze_sources(state)
        
        # Add HITL-specific reasoning
        reasoning = f"🔍 HITL STATUS: HITL override is {'enabled' if self.hitl_enabled else 'disabled'}"
        reasoning += f", Autonomous mode is {'enabled' if self.autonomous_mode else 'disabled'}"
        
        if self.hitl_enabled and not self.autonomous_mode:
            reasoning += "\n⚠️ Human approval will be required for market data quality issues"
        else:
            reasoning += "\n✅ Autonomous mode will bypass human approval"
        
        base_state['reasoning_trace'].append(reasoning)
        base_state['messages'].append(AIMessage(content=reasoning))
        
        return base_state
    
    async def _validate_connections(self, state: IndexScraperState) -> IndexScraperState:
        """Validate connections to data sources"""
        # Delegate to base agent
        return await self.base_agent._validate_connections(state)
    
    async def _collect_current_data(self, state: IndexScraperState) -> IndexScraperState:
        """Collect current market index data"""
        # Delegate to base agent
        return await self.base_agent._collect_current_data(state)
    
    async def _fetch_historical_data(self, state: IndexScraperState) -> IndexScraperState:
        """Fetch historical data for trend analysis"""
        # Delegate to base agent
        return await self.base_agent._fetch_historical_data(state)
    
    async def _analyze_market_sentiment(self, state: IndexScraperState) -> IndexScraperState:
        """Analyze market sentiment indicators"""
        # Delegate to base agent
        base_state = await self.base_agent._analyze_market_sentiment(state)
        
        # Determine if HITL should be requested
        should_request_hitl = await self.should_request_hitl(base_state)
        base_state['hitl_approval_required'] = should_request_hitl
        
        return base_state
    
    def _should_request_hitl_approval(self, state: IndexScraperState) -> str:
        """Determine if HITL approval should be requested"""
        if state['hitl_approval_required']:
            return "hitl_required"
        else:
            return "no_hitl"
    
    async def _request_hitl_approval(self, state: IndexScraperState) -> IndexScraperState:
        """Request HITL approval for market data"""
        reasoning = "👤 HITL: Requesting human approval for market data"
        
        sentiment = state.get('market_sentiment', {})
        data_quality = state.get('data_completeness', {})
        
        # Prepare decision data
        decision_data = {
            "market_indices": state.get('market_indices', []),
            "market_sentiment": sentiment,
            "historical_data": state.get('historical_data', {}),
            "data_quality": data_quality,
            "reasoning_trace": state['reasoning_trace']
        }
        
        # Create description for human reviewer
        description = (
            f"Market data collection with {len(state.get('market_indices', []))} indices. "
            f"Data quality: {data_quality.get('score', 0)}/100. "
            f"Market sentiment: {state.get('sentiment_level', 'unknown')}."
        )
        
        # Request HITL approval
        decision = await self.request_hitl_approval(
            decision_type="market_data_approval",
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
    
    async def _wait_for_hitl_decision(self, state: IndexScraperState) -> IndexScraperState:
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
                    reasoning += f" ✅ Market data approved by human reviewer"
                    if decision.user_comments:
                        reasoning += f" 💬 Comments: {decision.user_comments}"
                elif decision.status == HITLStatus.REJECTED:
                    reasoning += f" ❌ Market data rejected by human reviewer"
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
    
    def _check_hitl_decision(self, state: IndexScraperState) -> str:
        """Check HITL decision status"""
        status = state['hitl_approval_status']
        
        if status == HITLStatus.APPROVED or status == HITLStatus.BYPASSED:
            return "approved"
        elif status == HITLStatus.REJECTED:
            return "rejected"
        else:
            return "pending"
    
    async def _process_hitl_decision(self, state: IndexScraperState) -> IndexScraperState:
        """Process the HITL decision"""
        # This node is called when a decision transitions from pending to approved/rejected
        reasoning = "👤 HITL: Processing human decision"
        
        decision_dict = hitl_manager.get_decision(state['hitl_decision_id'])
        if decision_dict:
            decision = HITLDecision.from_dict(decision_dict)
            
            if decision.status == HITLStatus.APPROVED:
                reasoning += " ✅ Market data approved - proceeding with finalization"
            elif decision.status == HITLStatus.REJECTED:
                reasoning += " ❌ Market data rejected - returning to data collection"
                # Could modify state here based on user feedback
            else:
                reasoning += f" ⚠️ Unexpected decision status: {decision.status}"
        else:
            reasoning += " ❌ Error: Decision not found"
        
        state['reasoning_trace'].append(reasoning)
        state['messages'].append(AIMessage(content=reasoning))
        
        return state
    
    async def _finalize_data(self, state: IndexScraperState) -> IndexScraperState:
        """Finalize the collected market data"""
        # Delegate to base agent
        base_state = await self.base_agent._finalize_data(state)
        
        # Add HITL-specific information
        if state.get('hitl_approval_required', False):
            reasoning = f"👤 HITL: Market data finalized with human oversight"
            reasoning += f" - Status: {state.get('hitl_approval_status', 'unknown')}"
            
            base_state['reasoning_trace'].append(reasoning)
            base_state['messages'].append(AIMessage(content=reasoning))
        
        return base_state
    
    async def _log_collection(self, state: IndexScraperState) -> IndexScraperState:
        """Log the data collection to audit files"""
        # Delegate to base agent
        base_state = await self.base_agent._log_collection(state)
        
        # Add HITL-specific logging
        if state.get('hitl_decision_id'):
            # Add HITL information to audit log
            for audit_entry in base_state['audit_log']:
                audit_entry['hitl_enabled'] = self.hitl_enabled
                audit_entry['hitl_required'] = state.get('hitl_approval_required', False)
                audit_entry['hitl_status'] = state.get('hitl_approval_status', 'none')
                audit_entry['hitl_decision_id'] = state.get('hitl_decision_id')
        
        return base_state
    
    async def should_request_hitl(self, state: IndexScraperState) -> bool:
        """Determine if HITL should be requested"""
        # Check if HITL is enabled for this agent
        if not self.hitl_enabled or self.autonomous_mode:
            return False
        
        # Check data criteria that would require human review
        sentiment = state.get('market_sentiment', {})
        data_quality = state.get('data_completeness', {})
        trend_analysis = state.get('trend_analysis', {})
        
        # Extreme market sentiment
        fear_greed = sentiment.get('fear_greed_index', 50)
        if fear_greed > 80 or fear_greed < 20:
            return True
        
        # Data quality issues
        data_quality_score = data_quality.get('score', 100)
        if data_quality_score < 70:
            return True
        
        # High volatility
        volatility = trend_analysis.get('volatility_level', 'normal')
        if volatility == 'high':
            return True
        
        return False
    
    async def process_hitl_decision(self, decision: HITLDecision, state: IndexScraperState) -> IndexScraperState:
        """Process a HITL decision"""
        if decision.status == HITLStatus.APPROVED:
            # Proceed with original data
            state['hitl_approval_status'] = HITLStatus.APPROVED
        elif decision.status == HITLStatus.REJECTED:
            # Could modify data collection based on feedback
            state['hitl_approval_status'] = HITLStatus.REJECTED
        elif decision.status == HITLStatus.BYPASSED:
            # Autonomous mode, proceed with original data
            state['hitl_approval_status'] = HITLStatus.BYPASSED
        else:
            # Decision still pending or timed out
            state['hitl_approval_status'] = decision.status
        
        return state
    
    async def collect_market_data(
        self,
        data_sources: List[str],
        collection_frequency: int = 30,
        hitl_enabled: bool = False,
        autonomous_mode: bool = True
    ) -> Dict[str, Any]:
        """Main entry point for HITL-enhanced market data collection"""
        
        # Update HITL settings
        self.set_hitl_enabled(hitl_enabled)
        self.set_autonomous_mode(autonomous_mode)
        
        # Initialize state
        initial_state = IndexScraperState(
            messages=[HumanMessage(content=f"Collect market data with HITL capabilities")],
            data_sources=data_sources,
            collection_frequency=collection_frequency,
            market_indices=[],
            historical_data={},
            market_sentiment={},
            reasoning_trace=[],
            hitl_approval_required=False,
            hitl_approval_status="none",
            hitl_decision_id=None,
            final_data={},
            audit_log=[]
        )
        
        try:
            # Run the HITL-enhanced workflow
            final_state = await self.graph.ainvoke(initial_state)
            
            return {
                'status': 'success',
                'data': final_state['final_data'],
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
hitl_index_scraper = HITLIndexScraperAgent()