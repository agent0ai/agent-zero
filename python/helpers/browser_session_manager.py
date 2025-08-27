"""
Browser Session State Management
Manages browser session states and transitions for agent/human control handoff
"""

import time
import json
import logging
from enum import Enum
from typing import Dict, Any, Optional, List, Callable
from dataclasses import dataclass, asdict
from threading import Lock


class SessionState(Enum):
    """Browser session states"""
    IDLE = "idle"
    AGENT_ACTIVE = "agent_active"
    AGENT_PAUSED = "agent_paused"
    HUMAN_CONTROL = "human_control"
    HANDOFF_PENDING = "handoff_pending"
    ERROR = "error"


@dataclass
class SessionContext:
    """Session context data"""
    session_id: str
    current_url: str
    page_title: str
    cookies: List[Dict[str, Any]]
    local_storage: Dict[str, str]
    session_storage: Dict[str, str]
    viewport: Dict[str, int]
    user_agent: str
    timestamp: float
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SessionContext':
        """Create from dictionary"""
        return cls(**data)


@dataclass
class StateTransition:
    """Represents a state transition"""
    from_state: SessionState
    to_state: SessionState
    timestamp: float
    trigger: str
    context: Optional[Dict[str, Any]] = None


class BrowserSessionManager:
    """Manages browser session state and context"""
    
    def __init__(self):
        self.current_state = SessionState.IDLE
        self.session_context: Optional[SessionContext] = None
        self.state_history: List[StateTransition] = []
        self.state_handlers: Dict[SessionState, List[Callable]] = {}
        self.transition_handlers: Dict[tuple, List[Callable]] = {}
        self.logger = logging.getLogger(__name__)
        self._lock = Lock()
        
        # Define valid state transitions
        self.valid_transitions = {
            SessionState.IDLE: [
                SessionState.AGENT_ACTIVE,
                SessionState.HUMAN_CONTROL,
                SessionState.ERROR
            ],
            SessionState.AGENT_ACTIVE: [
                SessionState.AGENT_PAUSED,
                SessionState.HANDOFF_PENDING,
                SessionState.IDLE,
                SessionState.ERROR
            ],
            SessionState.AGENT_PAUSED: [
                SessionState.AGENT_ACTIVE,
                SessionState.HANDOFF_PENDING,
                SessionState.IDLE,
                SessionState.ERROR
            ],
            SessionState.HUMAN_CONTROL: [
                SessionState.HANDOFF_PENDING,
                SessionState.IDLE,
                SessionState.ERROR
            ],
            SessionState.HANDOFF_PENDING: [
                SessionState.AGENT_ACTIVE,
                SessionState.HUMAN_CONTROL,
                SessionState.IDLE,
                SessionState.ERROR
            ],
            SessionState.ERROR: [
                SessionState.IDLE,
                SessionState.AGENT_ACTIVE,
                SessionState.HUMAN_CONTROL
            ]
        }
    
    def get_state(self) -> str:
        """Get current session state"""
        return self.current_state.value
    
    def can_transition_to(self, new_state: SessionState) -> bool:
        """Check if transition to new state is valid"""
        return new_state in self.valid_transitions.get(self.current_state, [])
    
    def set_state(self, new_state: SessionState, trigger: str = "manual", context: Dict[str, Any] = None) -> bool:
        """Set new session state with validation"""
        with self._lock:
            if not self.can_transition_to(new_state):
                self.logger.warning(f"Invalid state transition: {self.current_state.value} -> {new_state.value}")
                return False
            
            old_state = self.current_state
            self.current_state = new_state
            
            # Record transition
            transition = StateTransition(
                from_state=old_state,
                to_state=new_state,
                timestamp=time.time(),
                trigger=trigger,
                context=context
            )
            self.state_history.append(transition)
            
            self.logger.info(f"State transition: {old_state.value} -> {new_state.value} (trigger: {trigger})")
            
            # Trigger state handlers
            self._trigger_state_handlers(new_state)
            self._trigger_transition_handlers(old_state, new_state, transition)
            
            return True
    
    def get_valid_transitions(self) -> List[str]:
        """Get valid transitions from current state"""
        return [state.value for state in self.valid_transitions.get(self.current_state, [])]
    
    def set_context(self, context: Dict[str, Any]):
        """Set session context"""
        try:
            if isinstance(context, dict):
                # Convert dict to SessionContext if needed
                if "session_id" in context:
                    self.session_context = SessionContext.from_dict(context)
                else:
                    # Create context with defaults
                    self.session_context = SessionContext(
                        session_id=context.get("session_id", "unknown"),
                        current_url=context.get("current_url", ""),
                        page_title=context.get("page_title", ""),
                        cookies=context.get("cookies", []),
                        local_storage=context.get("local_storage", {}),
                        session_storage=context.get("session_storage", {}),
                        viewport=context.get("viewport", {"width": 1920, "height": 1080}),
                        user_agent=context.get("user_agent", ""),
                        timestamp=time.time()
                    )
            else:
                self.session_context = context
                
        except Exception as e:
            self.logger.error(f"Failed to set session context: {e}")
    
    def get_context(self) -> Dict[str, Any]:
        """Get current session context"""
        if self.session_context:
            return self.session_context.to_dict()
        return {}
    
    def add_state_handler(self, state: SessionState, handler: Callable[[SessionState], None]):
        """Add handler for state entry"""
        if state not in self.state_handlers:
            self.state_handlers[state] = []
        self.state_handlers[state].append(handler)
    
    def add_transition_handler(self, from_state: SessionState, to_state: SessionState, 
                             handler: Callable[[StateTransition], None]):
        """Add handler for state transition"""
        key = (from_state, to_state)
        if key not in self.transition_handlers:
            self.transition_handlers[key] = []
        self.transition_handlers[key].append(handler)
    
    def _trigger_state_handlers(self, state: SessionState):
        """Trigger handlers for state entry"""
        if state in self.state_handlers:
            for handler in self.state_handlers[state]:
                try:
                    handler(state)
                except Exception as e:
                    self.logger.error(f"State handler error for {state.value}: {e}")
    
    def _trigger_transition_handlers(self, from_state: SessionState, to_state: SessionState, 
                                   transition: StateTransition):
        """Trigger handlers for state transition"""
        key = (from_state, to_state)
        if key in self.transition_handlers:
            for handler in self.transition_handlers[key]:
                try:
                    handler(transition)
                except Exception as e:
                    self.logger.error(f"Transition handler error for {from_state.value} -> {to_state.value}: {e}")
    
    def get_state_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent state history"""
        recent_transitions = self.state_history[-limit:]
        return [
            {
                "from_state": t.from_state.value,
                "to_state": t.to_state.value,
                "timestamp": t.timestamp,
                "trigger": t.trigger,
                "context": t.context
            }
            for t in recent_transitions
        ]
    
    def get_session_info(self) -> Dict[str, Any]:
        """Get comprehensive session information"""
        return {
            "current_state": self.current_state.value,
            "valid_transitions": self.get_valid_transitions(),
            "session_context": self.get_context(),
            "state_history": self.get_state_history(5),
            "session_duration": time.time() - (
                self.state_history[0].timestamp if self.state_history else time.time()
            )
        }
    
    def reset_session(self):
        """Reset session to idle state"""
        with self._lock:
            self.current_state = SessionState.IDLE
            self.session_context = None
            self.state_history.clear()
            self.logger.info("Session reset to idle state")


class SessionHandoffManager:
    """Manages handoffs between agent and human control"""
    
    def __init__(self, session_manager: BrowserSessionManager):
        self.session_manager = session_manager
        self.logger = logging.getLogger(__name__)
        self.handoff_data: Dict[str, Any] = {}
    
    def prepare_handoff(self, handoff_type: str) -> Dict[str, Any]:
        """Prepare handoff data for agent->human or human->agent transition"""
        
        current_context = self.session_manager.get_context()
        
        handoff_data = {
            "handoff_id": f"handoff_{int(time.time())}",
            "handoff_type": handoff_type,
            "timestamp": time.time(),
            "session_id": current_context.get("session_id", "unknown"),
            "current_url": current_context.get("current_url", ""),
            "page_title": current_context.get("page_title", ""),
            "browser_state": current_context,
            "previous_state": self.session_manager.current_state.value
        }
        
        # Store handoff data
        self.handoff_data[handoff_data["handoff_id"]] = handoff_data
        
        self.logger.info(f"Prepared handoff: {handoff_type} (ID: {handoff_data['handoff_id']})")
        return handoff_data
    
    def execute_handoff(self, handoff_data: Dict[str, Any]) -> Dict[str, bool]:
        """Execute handoff transition"""
        try:
            handoff_type = handoff_data.get("handoff_type", "")
            
            # Set to handoff pending state first
            if not self.session_manager.set_state(
                SessionState.HANDOFF_PENDING, 
                trigger=f"handoff_{handoff_type}",
                context=handoff_data
            ):
                return {"success": False, "error": "Failed to enter handoff pending state"}
            
            # Determine target state based on handoff type
            if handoff_type == "agent_to_human":
                target_state = SessionState.HUMAN_CONTROL
            elif handoff_type == "human_to_agent":
                target_state = SessionState.AGENT_ACTIVE
            else:
                return {"success": False, "error": f"Invalid handoff type: {handoff_type}"}
            
            # Execute the final transition
            success = self.session_manager.set_state(
                target_state,
                trigger=f"handoff_complete_{handoff_type}",
                context=handoff_data
            )
            
            if success:
                self.logger.info(f"Handoff completed: {handoff_type}")
                return {"success": True, "new_state": target_state.value}
            else:
                return {"success": False, "error": "Failed to complete handoff transition"}
                
        except Exception as e:
            self.logger.error(f"Handoff execution failed: {e}")
            # Try to recover to error state
            self.session_manager.set_state(SessionState.ERROR, trigger="handoff_error")
            return {"success": False, "error": str(e)}
    
    def get_handoff_status(self, handoff_id: str) -> Optional[Dict[str, Any]]:
        """Get status of handoff operation"""
        return self.handoff_data.get(handoff_id)
    
    def cleanup_old_handoffs(self, max_age_seconds: int = 3600):
        """Clean up old handoff data"""
        current_time = time.time()
        expired_ids = [
            hid for hid, data in self.handoff_data.items()
            if current_time - data["timestamp"] > max_age_seconds
        ]
        
        for hid in expired_ids:
            del self.handoff_data[hid]
        
        if expired_ids:
            self.logger.info(f"Cleaned up {len(expired_ids)} expired handoff records")


# Global session manager instance
_session_manager_instance: Optional[BrowserSessionManager] = None
_handoff_manager_instance: Optional[SessionHandoffManager] = None


def get_session_manager() -> BrowserSessionManager:
    """Get global session manager instance"""
    global _session_manager_instance
    if _session_manager_instance is None:
        _session_manager_instance = BrowserSessionManager()
    return _session_manager_instance


def get_handoff_manager() -> SessionHandoffManager:
    """Get global handoff manager instance"""
    global _handoff_manager_instance
    if _handoff_manager_instance is None:
        _handoff_manager_instance = SessionHandoffManager(get_session_manager())
    return _handoff_manager_instance