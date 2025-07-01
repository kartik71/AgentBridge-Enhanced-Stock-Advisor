"""
HITL-Enhanced Compliance Logger Agent
Adds Human-in-the-Loop capabilities to the Compliance Logger
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
from .compliance_logger_react.agent import ComplianceLoggerReActAgent

# State definition for the agent
class ComplianceLoggerState(TypedDict):
    messages: Annotated[List[BaseMessage], "The conversation messages"]
    compliance_rules: Dict[str, Any]
    monitoring_scope: str
    portfolio_data: Dict[str, Any]
    trade_orders: List[Dict[str, Any]]
    compliance_violations: List[Dict[str, Any]]
    risk_assessment: Dict[str, Any]
    reasoning_trace: List[str]
    hitl_approval_required: bool
    hitl_approval_status: str  # pending, approved, rejected, bypassed
    hitl_decision_id: Optional[str]
    final_compliance_report: Dict[str, Any]
    audit_log: List[Dict[str, Any]]

class HITLComplianceLoggerAgent(HITLEnhancedAgent[ComplianceLoggerState]):
    """Compliance Logger with HITL capabilities"""
    
    def __init__(self, agent_id: str = "hitl_compliance_logger"):
        super().__init__(agent_id, "HITL Compliance Logger")
        
        # Initialize base agent
        self.base_agent = ComplianceLoggerReActAgent()
        
        # Create enhanced StateGraph with HITL
        self.graph = self._create_hitl_graph()
    
    def _create_hitl_graph(self) -> StateGraph:
        """Create StateGraph with HITL decision points"""
        
        workflow = StateGraph(ComplianceLoggerState)
        
        # Add nodes from base agent
        workflow.add_node("load_compliance_rules", self._load_compliance_rules)
        workflow.add_node("collect_portfolio_data", self._collect_portfolio_data)
        workflow.add_node("analyze_trade_orders", self._analyze_trade_orders)
        workflow.add_node("check_position_limits", self._check_position_limits)
        workflow.add_node("assess_risk_compliance", self._assess_risk_compliance)
        workflow.add_node("detect_violations", self._detect_violations)
        workflow.add_node("reason_about_compliance", self._reason_about_compliance)
        
        # Add HITL-specific nodes
        workflow.add_node("request_hitl_approval", self._request_hitl_approval)
        workflow.add_node("wait_for_hitl_decision", self._wait_for_hitl_decision)
        workflow.add_node("process_hitl_decision", self._process_hitl_decision)
        
        # Add remaining nodes
        workflow.add_node("finalize_compliance_report", self._finalize_compliance_report)
        workflow.add_node("log_compliance_check", self._log_compliance_check)
        
        # Define the flow
        workflow.set_entry_point("load_compliance_rules")
        
        workflow.add_edge("load_compliance_rules", "collect_portfolio_data")
        workflow.add_edge("collect_portfolio_data", "analyze_trade_orders")
        workflow.add_edge("analyze_trade_orders", "check_position_limits")
        workflow.add_edge("check_position_limits", "assess_risk_compliance")
        workflow.add_edge("assess_risk_compliance", "detect_violations")
        workflow.add_edge("detect_violations", "reason_about_compliance")
        
        # Conditional edge for HITL
        workflow.add_conditional_edges(
            "reason_about_compliance",
            self._should_request_hitl_approval,
            {
                "hitl_required": "request_hitl_approval",
                "no_hitl": "finalize_compliance_report"
            }
        )
        
        workflow.add_edge("request_hitl_approval", "wait_for_hitl_decision")
        
        workflow.add_conditional_edges(
            "wait_for_hitl_decision",
            self._check_hitl_decision,
            {
                "approved": "finalize_compliance_report",
                "rejected": "detect_violations",  # Go back to violation detection
                "pending": END  # Wait for human input
            }
        )
        
        workflow.add_edge("process_hitl_decision", "finalize_compliance_report")
        workflow.add_edge("finalize_compliance_report", "log_compliance_check")
        workflow.add_edge("log_compliance_check", END)
        
        return workflow.compile()
    
    async def _load_compliance_rules(self, state: ComplianceLoggerState) -> ComplianceLoggerState:
        """Load and validate compliance rules"""
        # Delegate to base agent
        base_state = await self.base_agent._load_compliance_rules(state)
        
        # Add HITL-specific reasoning
        reasoning = f"🔍 HITL STATUS: HITL override is {'enabled' if self.hitl_enabled else 'disabled'}"
        reasoning += f", Autonomous mode is {'enabled' if self.autonomous_mode else 'disabled'}"
        
        if self.hitl_enabled and not self.autonomous_mode:
            reasoning += "\n⚠️ Human approval will be required for compliance violations"
        else:
            reasoning += "\n✅ Autonomous mode will bypass human approval"
        
        base_state['reasoning_trace'].append(reasoning)
        base_state['messages'].append(AIMessage(content=reasoning))
        
        return base_state
    
    async def _collect_portfolio_data(self, state: ComplianceLoggerState) -> ComplianceLoggerState:
        """Collect current portfolio data for compliance analysis"""
        # Delegate to base agent
        return await self.base_agent._collect_portfolio_data(state)
    
    async def _analyze_trade_orders(self, state: ComplianceLoggerState) -> ComplianceLoggerState:
        """Analyze recent trade orders for compliance"""
        # Delegate to base agent
        return await self.base_agent._analyze_trade_orders(state)
    
    async def _check_position_limits(self, state: ComplianceLoggerState) -> ComplianceLoggerState:
        """Check portfolio positions against compliance limits"""
        # Delegate to base agent
        return await self.base_agent._check_position_limits(state)
    
    async def _assess_risk_compliance(self, state: ComplianceLoggerState) -> ComplianceLoggerState:
        """Assess portfolio risk compliance"""
        # Delegate to base agent
        return await self.base_agent._assess_risk_compliance(state)
    
    async def _detect_violations(self, state: ComplianceLoggerState) -> ComplianceLoggerState:
        """Detect and categorize all compliance violations"""
        # Delegate to base agent
        return await self.base_agent._detect_violations(state)
    
    async def _reason_about_compliance(self, state: ComplianceLoggerState) -> ComplianceLoggerState:
        """Apply ReAct reasoning about compliance status"""
        # Delegate to base agent
        base_state = await self.base_agent._reason_about_compliance(state)
        
        # Determine if HITL should be requested
        should_request_hitl = await self.should_request_hitl(base_state)
        base_state['hitl_approval_required'] = should_request_hitl
        
        return base_state
    
    def _should_request_hitl_approval(self, state: ComplianceLoggerState) -> str:
        """Determine if HITL approval should be requested"""
        if state['hitl_approval_required']:
            return "hitl_required"
        else:
            return "no_hitl"
    
    async def _request_hitl_approval(self, state: ComplianceLoggerState) -> ComplianceLoggerState:
        """Request HITL approval for compliance report"""
        reasoning = "👤 HITL: Requesting human approval for compliance report"
        
        violations = state['compliance_violations']
        compliance_score = state.get('compliance_score', 100)
        
        # Prepare decision data
        decision_data = {
            "violations": violations,
            "compliance_score": compliance_score,
            "risk_assessment": state.get('risk_assessment', {}),
            "compliance_analysis": state.get('compliance_analysis', {}),
            "reasoning_trace": state['reasoning_trace']
        }
        
        # Create description for human reviewer
        description = (
            f"Compliance report with score {compliance_score:.1f}/100. "
            f"Contains {len(violations)} violations. "
            f"Risk level: {state.get('compliance_analysis', {}).get('risk_level', 'MEDIUM')}."
        )
        
        # Request HITL approval
        decision = await self.request_hitl_approval(
            decision_type="compliance_approval",
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
    
    async def _wait_for_hitl_decision(self, state: ComplianceLoggerState) -> ComplianceLoggerState:
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
                    reasoning += f" ✅ Compliance report approved by human reviewer"
                    if decision.user_comments:
                        reasoning += f" 💬 Comments: {decision.user_comments}"
                elif decision.status == HITLStatus.REJECTED:
                    reasoning += f" ❌ Compliance report rejected by human reviewer"
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
    
    def _check_hitl_decision(self, state: ComplianceLoggerState) -> str:
        """Check HITL decision status"""
        status = state['hitl_approval_status']
        
        if status == HITLStatus.APPROVED or status == HITLStatus.BYPASSED:
            return "approved"
        elif status == HITLStatus.REJECTED:
            return "rejected"
        else:
            return "pending"
    
    async def _process_hitl_decision(self, state: ComplianceLoggerState) -> ComplianceLoggerState:
        """Process the HITL decision"""
        # This node is called when a decision transitions from pending to approved/rejected
        reasoning = "👤 HITL: Processing human decision"
        
        decision_dict = hitl_manager.get_decision(state['hitl_decision_id'])
        if decision_dict:
            decision = HITLDecision.from_dict(decision_dict)
            
            if decision.status == HITLStatus.APPROVED:
                reasoning += " ✅ Compliance report approved - proceeding with finalization"
            elif decision.status == HITLStatus.REJECTED:
                reasoning += " ❌ Compliance report rejected - returning to violation detection"
                # Could modify state here based on user feedback
            else:
                reasoning += f" ⚠️ Unexpected decision status: {decision.status}"
        else:
            reasoning += " ❌ Error: Decision not found"
        
        state['reasoning_trace'].append(reasoning)
        state['messages'].append(AIMessage(content=reasoning))
        
        return state
    
    async def _finalize_compliance_report(self, state: ComplianceLoggerState) -> ComplianceLoggerState:
        """Finalize the compliance report"""
        # Delegate to base agent
        base_state = await self.base_agent._finalize_compliance_report(state)
        
        # Add HITL-specific information
        if state.get('hitl_approval_required', False):
            reasoning = f"👤 HITL: Compliance report finalized with human oversight"
            reasoning += f" - Status: {state.get('hitl_approval_status', 'unknown')}"
            
            base_state['reasoning_trace'].append(reasoning)
            base_state['messages'].append(AIMessage(content=reasoning))
        
        return base_state
    
    async def _log_compliance_check(self, state: ComplianceLoggerState) -> ComplianceLoggerState:
        """Log the compliance check to audit files"""
        # Delegate to base agent
        base_state = await self.base_agent._log_compliance_check(state)
        
        # Add HITL-specific logging
        if state.get('hitl_decision_id'):
            # Add HITL information to audit log
            for audit_entry in base_state['audit_log']:
                audit_entry['hitl_enabled'] = self.hitl_enabled
                audit_entry['hitl_required'] = state.get('hitl_approval_required', False)
                audit_entry['hitl_status'] = state.get('hitl_approval_status', 'none')
                audit_entry['hitl_decision_id'] = state.get('hitl_decision_id')
        
        return base_state
    
    async def should_request_hitl(self, state: ComplianceLoggerState) -> bool:
        """Determine if HITL should be requested"""
        # Check if HITL is enabled for this agent
        if not self.hitl_enabled or self.autonomous_mode:
            return False
        
        # Check compliance criteria that would require human review
        violations = state.get('compliance_violations', [])
        compliance_score = state.get('compliance_score', 100)
        
        # High severity violations
        high_severity_violations = [v for v in violations if v.get('severity') == 'HIGH']
        if len(high_severity_violations) > 0:
            return True
        
        # Low compliance score
        if compliance_score < 80:
            return True
        
        # Multiple violation types
        violation_types = set(v.get('type', '') for v in violations)
        if len(violation_types) > 3:
            return True
        
        return False
    
    async def process_hitl_decision(self, decision: HITLDecision, state: ComplianceLoggerState) -> ComplianceLoggerState:
        """Process a HITL decision"""
        if decision.status == HITLStatus.APPROVED:
            # Proceed with original compliance report
            state['hitl_approval_status'] = HITLStatus.APPROVED
        elif decision.status == HITLStatus.REJECTED:
            # Could modify compliance report based on feedback
            state['hitl_approval_status'] = HITLStatus.REJECTED
        elif decision.status == HITLStatus.BYPASSED:
            # Autonomous mode, proceed with original report
            state['hitl_approval_status'] = HITLStatus.BYPASSED
        else:
            # Decision still pending or timed out
            state['hitl_approval_status'] = decision.status
        
        return state
    
    async def monitor_compliance(
        self,
        monitoring_scope: str = "full",
        hitl_enabled: bool = False,
        autonomous_mode: bool = True
    ) -> Dict[str, Any]:
        """Main entry point for HITL-enhanced compliance monitoring"""
        
        # Update HITL settings
        self.set_hitl_enabled(hitl_enabled)
        self.set_autonomous_mode(autonomous_mode)
        
        # Initialize state
        initial_state = ComplianceLoggerState(
            messages=[HumanMessage(content=f"Monitor compliance with HITL capabilities")],
            compliance_rules={},
            monitoring_scope=monitoring_scope,
            portfolio_data={},
            trade_orders=[],
            compliance_violations=[],
            risk_assessment={},
            reasoning_trace=[],
            hitl_approval_required=False,
            hitl_approval_status="none",
            hitl_decision_id=None,
            final_compliance_report={},
            audit_log=[]
        )
        
        try:
            # Run the HITL-enhanced workflow
            final_state = await self.graph.ainvoke(initial_state)
            
            return {
                'status': 'success',
                'compliance_report': final_state['final_compliance_report'],
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
hitl_compliance_logger = HITLComplianceLoggerAgent()