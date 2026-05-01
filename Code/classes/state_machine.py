"""
State Machine - Manages application states and transitions
"""

import time


class StateMachine:
    """Manages application state transitions"""
    
    # Valid states
    INIT = "INIT"
    MENU = "MENU"
    MEASURING = "MEASURING"
    HRV_ANALYSIS = "HRV_ANALYSIS"
    KUBIOS = "KUBIOS"
    HISTORY = "HISTORY"
    COMPARING = "COMPARING"
    SHUTDOWN = "SHUTDOWN"
    
    VALID_STATES = [INIT, MENU, MEASURING, HRV_ANALYSIS, KUBIOS, HISTORY, COMPARING, SHUTDOWN]
    
    def __init__(self):
        """Initialize state machine"""
        self.current_state = self.INIT
        self.previous_state = None
        self.state_changed = True
        self.state_enter_time = time.time()
        self.state_history = []
        self.max_history = 10
        
        print(f"[STATE] State machine initialized. Current state: {self.current_state}")
    
    def change_state(self, new_state):
        """
        Change to new state with validation
        Only allows valid state transitions
        """
        if new_state not in self.VALID_STATES:
            print(f"[STATE] Invalid state: {new_state}")
            return False
        
        if new_state == self.current_state:
            print(f"[STATE] Already in state: {new_state}")
            return False
        
        previous_state = self.current_state
        self.current_state = new_state
        self.previous_state = previous_state
        self.state_changed = True
        self.state_enter_time = time.time()
        
        # Record state transition in history
        self._record_transition(previous_state, new_state)
        
        print(f"[STATE] Transition: {previous_state} -> {new_state}")
        return True
    
    def update(self):
        """
        Update state machine 
        Called periodically from main loop
        """
        pass  # Can be used for state timeouts, auto-transitions, etc.
    
    def get_state_duration(self):
        """Get how long we've been in current state"""
        return time.time() - self.state_enter_time
    
    def _record_transition(self, from_state, to_state):
        """Record state transition in history"""
        transition = {
            "from": from_state,
            "to": to_state,
            "timestamp": time.time()
        }
        
        self.state_history.append(transition)
        
        # Keep history size manageable
        if len(self.state_history) > self.max_history:
            self.state_history.pop(0)
    
    def get_state_history(self):
        """Get list of recent state transitions"""
        return self.state_history
    
    def is_in_measurement_state(self):
        """Check if currently measuring"""
        return self.current_state in [self.MEASURING, self.HRV_ANALYSIS, self.KUBIOS]
    
    def is_menu_state(self):
        """Check if in menu"""
        return self.current_state == self.MENU
    
    def __str__(self):
        """String representation"""
        return f"State({self.current_state}, duration={self.get_state_duration():.1f}s)"
