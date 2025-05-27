import threading
import logging
from typing import Callable, Dict, Set, Any, Optional
import asyncio # Import asyncio
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
        
        # Dictionary to store the active delegate for each event type
        self._active_delegate: Dict[str, Callable] = {}

        # Dictionary to store shared state/events
        self._shared_state: Dict[str, Any] = {}

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

    def set_active_delegate(self, event_type: str, delegate: Callable) -> None:
        """
        Set the active delegate for a specific event type, replacing any existing ones.
        """
        with self._lock:
            self._active_delegate[event_type] = delegate

    def get_active_delegate(self, event_type: str) -> Optional[Callable]:
        """
        Get the active delegate for a specific event type.
        Returns the active delegate or None if no active delegate is set.
        """
        with self._lock:
            return self._active_delegate.get(event_type)

    def set_shared_state(self, key: str, value: Any) -> None:
        """
        Set a value in the shared state dictionary.
        """
        with self._lock:
            self._shared_state[key] = value

    def get_shared_state(self, key: str, default: Any = None) -> Any:
        """
        Get a value from the shared state dictionary.
        Returns the value or the default if the key is not found.
        """
        with self._lock:
            return self._shared_state.get(key, default)

    async def invoke_notification(self, sender: Any, event_type: str, event_data: Any = None, **kwargs) -> None:
        """
        Invoke the active notification delegate for the given event type.
        If no active delegate is set, fall back to invoking all registered delegates.
        Delegates are called with (sender, event_type, event_data) and any extra kwargs.
        """
        delegate_to_invoke = None
        with self._lock: # Keep lock for accessing _active_delegate
            delegate_to_invoke = self._active_delegate.get(event_type)

        if delegate_to_invoke:
            try:
                if asyncio.iscoroutinefunction(delegate_to_invoke):
                    await delegate_to_invoke(sender=sender, event_type=event_type, event_data=event_data, **kwargs)
                else:
                    delegate_to_invoke(sender=sender, event_type=event_type, event_data=event_data, **kwargs)
            except Exception as e:
                logger.error(traceback.format_exc())
                logger.error(f"Error invoking active notification delegate for {event_type}: {e}", exc_info=True)
        else:
            # Fallback to old behavior if no active delegate is set
            delegates_to_invoke = set()
            with self._lock: # Keep lock for accessing _notification_delegates
                if event_type in self._notification_delegates:
                    delegates_to_invoke = set(self._notification_delegates[event_type]) # Make a copy
            
            if not delegates_to_invoke: # If still no delegates, log and return
                logger.debug(f"No delegates registered or active for notification event: {event_type}")
                return

            for delegate in delegates_to_invoke:
                try:
                    if asyncio.iscoroutinefunction(delegate):
                        await delegate(sender=sender, event_type=event_type, event_data=event_data, **kwargs)
                    else:
                        delegate(sender=sender, event_type=event_type, event_data=event_data, **kwargs)
                except Exception as e:
                    logger.error(traceback.format_exc())
                    logger.error(f"Error invoking notification delegate for {event_type}: {e}", exc_info=True)

    def restore_original_delegate(self, event_type: str = "user_message_display") -> None:
        """
        Restores the original delegate for a given event type from shared state.
        """
        original_delegate = self.get_shared_state(f"original_delegate_{event_type}")
        if original_delegate and callable(original_delegate):
            self.set_active_delegate(event_type, original_delegate)
            logger.debug(f"Restored original delegate for event type: {event_type}")
        else:
            logger.warning(f"No original delegate found in shared state for event type: {event_type}")


    async def invoke_control(self, sender: Any, control_type: str, **kwargs: Any) -> bool: # Added **kwargs and async
        """
        Invoke all control delegates registered for the given control type.
        Returns True if any delegate returns True, False otherwise.
        """
        delegates_to_invoke = set()
        with self._lock:
            if control_type in self._control_delegates:
                delegates_to_invoke = set(self._control_delegates[control_type])
        
        if not delegates_to_invoke:
            logger.debug(f"No delegates registered for control event: {control_type}")
            return False
            
        for delegate in delegates_to_invoke:
            try:
                # Pass sender as a positional argument if the delegate expects it,
                # and the rest as keyword arguments.
                # AILoop's handlers expect kwargs.
                if asyncio.iscoroutinefunction(delegate):
                    if await delegate(sender=sender, **kwargs): # Pass kwargs
                        return True
                else:
                    if delegate(sender=sender, **kwargs): # Pass kwargs
                        return True
            except Exception as e:
                logger.error(f"Error invoking control delegate for {control_type}: {e}", exc_info=True)
        return False
