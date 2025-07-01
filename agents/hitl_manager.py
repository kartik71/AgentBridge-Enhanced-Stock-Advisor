"""
HITL Manager - Human-in-the-Loop Management for LangGraph Agents
Provides centralized HITL functionality for agent decision approval
"""

import asyncio
import json
import uuid
from datetime import datetime
from typing import Dict, List, Any, Optional, Callable
from enum import Enum
import os

class HITLStatus(str, Enum):
    """Status of HITL decision"""
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    TIMEOUT = "timeout"
    BYPASSED = "bypassed"  # When autonomous mode is enabled

class HITLDecision:
    """Represents a decision requiring human approval"""
    def __init__(
        self,
        decision_id: str,
        agent_id: str,
        decision_type: str,
        decision_data: Dict[str, Any],
        description: str,
        created_at: datetime = None,
        status: HITLStatus = HITLStatus.PENDING,
        user_id: str = "default_user",
        timeout_seconds: int = 300,  # 5 minute default timeout
        callback: Optional[Callable] = None
    ):
        self.decision_id = decision_id
        self.agent_id = agent_id
        self.decision_type = decision_type
        self.decision_data = decision_data
        self.description = description
        self.created_at = created_at or datetime.now()
        self.status = status
        self.user_id = user_id
        self.timeout_seconds = timeout_seconds
        self.callback = callback
        self.resolved_at: Optional[datetime] = None
        self.resolution_reason: Optional[str] = None
        self.user_comments: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            "decision_id": self.decision_id,
            "agent_id": self.agent_id,
            "decision_type": self.decision_type,
            "decision_data": self.decision_data,
            "description": self.description,
            "created_at": self.created_at.isoformat(),
            "status": self.status,
            "user_id": self.user_id,
            "timeout_seconds": self.timeout_seconds,
            "resolved_at": self.resolved_at.isoformat() if self.resolved_at else None,
            "resolution_reason": self.resolution_reason,
            "user_comments": self.user_comments
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'HITLDecision':
        """Create from dictionary"""
        decision = cls(
            decision_id=data["decision_id"],
            agent_id=data["agent_id"],
            decision_type=data["decision_type"],
            decision_data=data["decision_data"],
            description=data["description"],
            created_at=datetime.fromisoformat(data["created_at"]),
            status=data["status"],
            user_id=data["user_id"],
            timeout_seconds=data["timeout_seconds"]
        )
        
        if data.get("resolved_at"):
            decision.resolved_at = datetime.fromisoformat(data["resolved_at"])
        
        decision.resolution_reason = data.get("resolution_reason")
        decision.user_comments = data.get("user_comments")
        
        return decision

class HITLManager:
    """Manages HITL decisions across all agents"""
    
    _instance = None
    
    def __new__(cls):
        """Singleton pattern to ensure one HITL manager instance"""
        if cls._instance is None:
            cls._instance = super(HITLManager, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        """Initialize HITL manager"""
        if self._initialized:
            return
            
        self.pending_decisions: Dict[str, HITLDecision] = {}
        self.resolved_decisions: Dict[str, HITLDecision] = {}
        self.decision_history: List[Dict[str, Any]] = []
        self.global_autonomous_mode = False
        self.agent_hitl_overrides: Dict[str, bool] = {}
        self.data_dir = os.path.join("data", "hitl")
        self.decision_file = os.path.join(self.data_dir, "hitl_decisions.json")
        self.history_file = os.path.join(self.data_dir, "hitl_history.json")
        
        # Create data directory if it doesn't exist
        os.makedirs(self.data_dir, exist_ok=True)
        
        # Load existing data
        self._load_data()
        
        self._initialized = True
    
    def _load_data(self):
        """Load HITL data from files"""
        try:
            # Load pending decisions
            if os.path.exists(self.decision_file):
                with open(self.decision_file, 'r') as f:
                    decisions_data = json.load(f)
                    for decision_data in decisions_data:
                        decision = HITLDecision.from_dict(decision_data)
                        if decision.status == HITLStatus.PENDING:
                            self.pending_decisions[decision.decision_id] = decision
                        else:
                            self.resolved_decisions[decision.decision_id] = decision
            
            # Load decision history
            if os.path.exists(self.history_file):
                with open(self.history_file, 'r') as f:
                    self.decision_history = json.load(f)
                    
        except Exception as e:
            print(f"Error loading HITL data: {e}")
    
    def _save_data(self):
        """Save HITL data to files"""
        try:
            # Save all decisions
            all_decisions = list(self.pending_decisions.values()) + list(self.resolved_decisions.values())
            with open(self.decision_file, 'w') as f:
                json.dump([d.to_dict() for d in all_decisions], f, indent=2)
            
            # Save decision history
            with open(self.history_file, 'w') as f:
                json.dump(self.decision_history, f, indent=2)
                
        except Exception as e:
            print(f"Error saving HITL data: {e}")
    
    def set_global_autonomous_mode(self, enabled: bool):
        """Set global autonomous mode (bypass all HITL)"""
        self.global_autonomous_mode = enabled
    
    def set_agent_hitl_override(self, agent_id: str, override_enabled: bool):
        """Set HITL override for specific agent"""
        self.agent_hitl_overrides[agent_id] = override_enabled
    
    def is_hitl_required(self, agent_id: str) -> bool:
        """Check if HITL is required for an agent"""
        # Global autonomous mode bypasses all HITL
        if self.global_autonomous_mode:
            return False
        
        # Check agent-specific override
        return self.agent_hitl_overrides.get(agent_id, False)
    
    async def create_decision(
        self,
        agent_id: str,
        decision_type: str,
        decision_data: Dict[str, Any],
        description: str,
        user_id: str = "default_user",
        timeout_seconds: int = 300
    ) -> HITLDecision:
        """Create a new HITL decision"""
        # Check if HITL is required
        if not self.is_hitl_required(agent_id):
            # Create a bypassed decision for audit purposes
            decision = HITLDecision(
                decision_id=str(uuid.uuid4()),
                agent_id=agent_id,
                decision_type=decision_type,
                decision_data=decision_data,
                description=description,
                status=HITLStatus.BYPASSED,
                user_id=user_id,
                timeout_seconds=timeout_seconds
            )
            decision.resolved_at = datetime.now()
            decision.resolution_reason = "Autonomous mode enabled"
            
            # Store in resolved decisions
            self.resolved_decisions[decision.decision_id] = decision
            
            # Add to history
            self._add_to_history(decision)
            
            # Save data
            self._save_data()
            
            return decision
        
        # Create a pending decision
        decision = HITLDecision(
            decision_id=str(uuid.uuid4()),
            agent_id=agent_id,
            decision_type=decision_type,
            decision_data=decision_data,
            description=description,
            status=HITLStatus.PENDING,
            user_id=user_id,
            timeout_seconds=timeout_seconds
        )
        
        # Store in pending decisions
        self.pending_decisions[decision.decision_id] = decision
        
        # Save data
        self._save_data()
        
        # Start timeout task
        asyncio.create_task(self._handle_timeout(decision.decision_id, timeout_seconds))
        
        return decision
    
    async def _handle_timeout(self, decision_id: str, timeout_seconds: int):
        """Handle decision timeout"""
        await asyncio.sleep(timeout_seconds)
        
        # Check if decision is still pending
        if decision_id in self.pending_decisions:
            decision = self.pending_decisions[decision_id]
            
            # Mark as timed out
            decision.status = HITLStatus.TIMEOUT
            decision.resolved_at = datetime.now()
            decision.resolution_reason = f"Timed out after {timeout_seconds} seconds"
            
            # Move to resolved decisions
            self.resolved_decisions[decision_id] = decision
            del self.pending_decisions[decision_id]
            
            # Add to history
            self._add_to_history(decision)
            
            # Save data
            self._save_data()
            
            # Execute callback if provided
            if decision.callback:
                try:
                    decision.callback(decision)
                except Exception as e:
                    print(f"Error executing callback for timed out decision: {e}")
    
    def approve_decision(self, decision_id: str, user_comments: Optional[str] = None) -> bool:
        """Approve a pending HITL decision"""
        if decision_id not in self.pending_decisions:
            return False
        
        decision = self.pending_decisions[decision_id]
        decision.status = HITLStatus.APPROVED
        decision.resolved_at = datetime.now()
        decision.resolution_reason = "Approved by user"
        decision.user_comments = user_comments
        
        # Move to resolved decisions
        self.resolved_decisions[decision_id] = decision
        del self.pending_decisions[decision_id]
        
        # Add to history
        self._add_to_history(decision)
        
        # Save data
        self._save_data()
        
        # Execute callback if provided
        if decision.callback:
            try:
                decision.callback(decision)
            except Exception as e:
                print(f"Error executing callback for approved decision: {e}")
        
        return True
    
    def reject_decision(self, decision_id: str, user_comments: Optional[str] = None) -> bool:
        """Reject a pending HITL decision"""
        if decision_id not in self.pending_decisions:
            return False
        
        decision = self.pending_decisions[decision_id]
        decision.status = HITLStatus.REJECTED
        decision.resolved_at = datetime.now()
        decision.resolution_reason = "Rejected by user"
        decision.user_comments = user_comments
        
        # Move to resolved decisions
        self.resolved_decisions[decision_id] = decision
        del self.pending_decisions[decision_id]
        
        # Add to history
        self._add_to_history(decision)
        
        # Save data
        self._save_data()
        
        # Execute callback if provided
        if decision.callback:
            try:
                decision.callback(decision)
            except Exception as e:
                print(f"Error executing callback for rejected decision: {e}")
        
        return True
    
    def get_pending_decisions(self, agent_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get all pending decisions, optionally filtered by agent"""
        decisions = list(self.pending_decisions.values())
        
        if agent_id:
            decisions = [d for d in decisions if d.agent_id == agent_id]
        
        return [d.to_dict() for d in decisions]
    
    def get_decision(self, decision_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific decision by ID"""
        if decision_id in self.pending_decisions:
            return self.pending_decisions[decision_id].to_dict()
        elif decision_id in self.resolved_decisions:
            return self.resolved_decisions[decision_id].to_dict()
        return None
    
    def get_decision_history(
        self, 
        agent_id: Optional[str] = None,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """Get decision history, optionally filtered by agent"""
        history = self.decision_history
        
        if agent_id:
            history = [h for h in history if h.get("agent_id") == agent_id]
        
        return history[:limit]
    
    def _add_to_history(self, decision: HITLDecision):
        """Add decision to history"""
        history_entry = decision.to_dict()
        history_entry["timestamp"] = datetime.now().isoformat()
        
        self.decision_history.insert(0, history_entry)
        
        # Keep history at reasonable size
        if len(self.decision_history) > 1000:
            self.decision_history = self.decision_history[:1000]

# Global HITL manager instance
hitl_manager = HITLManager()