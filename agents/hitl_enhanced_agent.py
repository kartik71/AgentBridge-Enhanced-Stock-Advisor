"""
HITL Enhanced Agent - Base class for agents with HITL capabilities
Provides common HITL functionality for LangGraph agents
"""

import asyncio
from datetime import datetime
from typing import Dict, List, Any, Optional, Callable, TypeVar, Generic
from abc import ABC, abstractmethod

from .hitl_manager import hitl_manager, HITLStatus, HITLDecision

# Generic type for agent state
T = TypeVar('T')

class HITLEnhancedAgent(Generic[T], ABC):
    """Base class for agents with HITL capabilities"""
    
    def __init__(self, agent_id: str, agent_name: str):
        self.agent_id = agent_id
        self.agent_name = agent_name
        self.hitl_enabled = False
        self.autonomous_mode = True
        self.hitl_timeout_seconds = 300  # 5 minutes default
        
        # Register with HITL manager
        hitl_manager.set_agent_hitl_override(agent_id, self.hitl_enabled)
    
    def set_hitl_enabled(self, enabled: bool):
        """Enable or disable HITL for this agent"""
        self.hitl_enabled = enabled
        hitl_manager.set_agent_hitl_override(self.agent_id, enabled)
    
    def set_autonomous_mode(self, enabled: bool):
        """Set autonomous mode (bypasses HITL when enabled)"""
        self.autonomous_mode = enabled
        # Global setting is managed separately by the HITL manager
    
    def set_hitl_timeout(self, timeout_seconds: int):
        """Set HITL decision timeout in seconds"""
        self.hitl_timeout_seconds = max(30, timeout_seconds)  # Minimum 30 seconds
    
    async def request_hitl_approval(
        self,
        decision_type: str,
        decision_data: Dict[str, Any],
        description: str,
        user_id: str = "default_user",
        callback: Optional[Callable] = None
    ) -> HITLDecision:
        """Request human approval for a decision"""
        # Check if HITL is enabled for this agent
        if not self.hitl_enabled or self.autonomous_mode:
            # Create a bypassed decision for audit purposes
            return await hitl_manager.create_decision(
                agent_id=self.agent_id,
                decision_type=decision_type,
                decision_data=decision_data,
                description=description,
                user_id=user_id,
                timeout_seconds=self.hitl_timeout_seconds
            )
        
        # Create a pending decision
        decision = await hitl_manager.create_decision(
            agent_id=self.agent_id,
            decision_type=decision_type,
            decision_data=decision_data,
            description=description,
            user_id=user_id,
            timeout_seconds=self.hitl_timeout_seconds
        )
        
        return decision
    
    async def wait_for_hitl_decision(
        self, 
        decision: HITLDecision,
        timeout_seconds: Optional[int] = None
    ) -> HITLDecision:
        """Wait for human decision on a HITL request"""
        if decision.status != HITLStatus.PENDING:
            return decision
        
        timeout = timeout_seconds or self.hitl_timeout_seconds
        poll_interval = 1.0  # Poll every second
        elapsed = 0
        
        while elapsed < timeout:
            # Check current status
            current_decision = hitl_manager.get_decision(decision.decision_id)
            if current_decision and current_decision["status"] != HITLStatus.PENDING:
                # Decision has been resolved
                return HITLDecision.from_dict(current_decision)
            
            # Wait before polling again
            await asyncio.sleep(poll_interval)
            elapsed += poll_interval
        
        # Timeout reached, decision still pending
        return decision
    
    def get_pending_decisions(self) -> List[Dict[str, Any]]:
        """Get all pending decisions for this agent"""
        return hitl_manager.get_pending_decisions(self.agent_id)
    
    def get_decision_history(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get decision history for this agent"""
        return hitl_manager.get_decision_history(self.agent_id, limit)
    
    @abstractmethod
    async def process_hitl_decision(self, decision: HITLDecision, state: T) -> T:
        """Process a HITL decision (to be implemented by subclasses)"""
        pass
    
    @abstractmethod
    async def should_request_hitl(self, state: T) -> bool:
        """Determine if HITL should be requested (to be implemented by subclasses)"""
        pass