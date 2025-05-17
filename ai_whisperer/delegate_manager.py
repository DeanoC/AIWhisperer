import threading
import logging
from typing import Callable, Dict, Set, Any
import traceback

# Set up a module-level logger
logger = logging.getLogger(__name__)


class DelegateManager:
    """
    Thread-safe manager for delegates that allows registration, unregistration,
    and invocation of delegates across multiple threads.
    """
    
    def __init__(self):
        # Lock for thread-safe access to delegate collections
        self._lock = threading.RLock()
        
        # Dictionary to store notification delegates
        self._notification_delegates: Dict[str, Set[Callable]] = {}
        
        # Dictionary to store control delegates
        self._control_delegates: Dict[str, Set[Callable]] = {}
    
    def register_notification(self, event_type: str, delegate: Callable) -> None:
        """
        Register a notification delegate for a specific event type.
        """
        with self._lock:
            if event_type not in self._notification_delegates:
                self._notification_delegates[event_type] = set()
            self._notification_delegates[event_type].add(delegate)
    
    def unregister_notification(self, event_type: str, delegate: Callable) -> bool:
        """
        Unregister a notification delegate.
        """
        with self._lock:
            if event_type in self._notification_delegates:
                delegates = self._notification_delegates[event_type]
                if delegate in delegates:
                    delegates.remove(delegate)
                    if not delegates:
                        del self._notification_delegates[event_type]
                    return True
        return False
    
    def register_control(self, control_type: str, delegate: Callable) -> None:
        """
        Register a control delegate for a specific control type.
        """
        with self._lock:
            if control_type not in self._control_delegates:
                self._control_delegates[control_type] = set()
            self._control_delegates[control_type].add(delegate)
    
    def unregister_control(self, control_type: str, delegate: Callable) -> bool:
        """
        Unregister a control delegate.
        """
        with self._lock:
            if control_type in self._control_delegates:
                delegates = self._control_delegates[control_type]
                if delegate in delegates:
                    delegates.remove(delegate)
                    if not delegates:
                        del self._control_delegates[control_type]
                    return True
        return False
    
    def invoke_notification(self, sender: Any, event_type: str, event_data: Any = None) -> None:
        """
        Invoke all notification delegates registered for the given event type.
        Delegates are called with (sender, event_data)
        """
        delegates_to_invoke = set()
        with self._lock:
            if event_type in self._notification_delegates:
                delegates_to_invoke = set(self._notification_delegates[event_type])
        for delegate in delegates_to_invoke:
            try:
                delegate(sender, event_data)
            except Exception as e:
                logger.error(traceback.format_exc())
                logger.error(f"Error invoking notification delegate: {e}")
    
    def invoke_control(self, sender: Any, control_type: str) -> bool:
        """
        Invoke all control delegates registered for the given control type.
        Returns True if any delegate returns True, False otherwise.
        """
        delegates_to_invoke = set()
        with self._lock:
            if control_type in self._control_delegates:
                delegates_to_invoke = set(self._control_delegates[control_type])
        if not delegates_to_invoke:
            return False
        for delegate in delegates_to_invoke:
            try:
                if delegate(sender):
                    return True
            except Exception as e:
                logger.error(f"Error invoking control delegate: {e}")
        return False
