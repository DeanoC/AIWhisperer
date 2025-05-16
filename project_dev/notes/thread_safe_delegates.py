import threading
import time
from typing import Callable, Dict, List, Any, Optional, Set


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
        
        Args:
            event_type: The type of event to register for
            delegate: The callable to invoke when the event occurs
        """
        with self._lock:
            if event_type not in self._notification_delegates:
                self._notification_delegates[event_type] = set()
            self._notification_delegates[event_type].add(delegate)
    
    def unregister_notification(self, event_type: str, delegate: Callable) -> bool:
        """
        Unregister a notification delegate.
        
        Args:
            event_type: The type of event to unregister from
            delegate: The delegate to remove
            
        Returns:
            True if the delegate was removed, False if it wasn't registered
        """
        with self._lock:
            if event_type in self._notification_delegates:
                delegates = self._notification_delegates[event_type]
                if delegate in delegates:
                    delegates.remove(delegate)
                    # Clean up empty sets
                    if not delegates:
                        del self._notification_delegates[event_type]
                    return True
        return False
    
    def register_control(self, control_type: str, delegate: Callable) -> None:
        """
        Register a control delegate for a specific control type.
        
        Args:
            control_type: The type of control to register for
            delegate: The callable to invoke when control is requested
        """
        with self._lock:
            if control_type not in self._control_delegates:
                self._control_delegates[control_type] = set()
            self._control_delegates[control_type].add(delegate)
    
    def unregister_control(self, control_type: str, delegate: Callable) -> bool:
        """
        Unregister a control delegate.
        
        Args:
            control_type: The type of control to unregister from
            delegate: The delegate to remove
            
        Returns:
            True if the delegate was removed, False if it wasn't registered
        """
        with self._lock:
            if control_type in self._control_delegates:
                delegates = self._control_delegates[control_type]
                if delegate in delegates:
                    delegates.remove(delegate)
                    # Clean up empty sets
                    if not delegates:
                        del self._control_delegates[control_type]
                    return True
        return False
    
    def invoke_notification(self, sender: Any, event_type: str, event_data: Any = None) -> None:
        """
        Invoke all notification delegates registered for the given event type.
        
        Args:
            sender: The object sending the notification
            event_type: The type of event that occurred
            event_data: Optional data associated with the event
        """
        # Get a thread-safe copy of the delegates to invoke
        delegates_to_invoke = set()
        with self._lock:
            if event_type in self._notification_delegates:
                delegates_to_invoke = set(self._notification_delegates[event_type])
        
        # Invoke each delegate
        for delegate in delegates_to_invoke:
            try:
                delegate(sender, event_type, event_data)
            except Exception as e:
                # In a real system, you might want to log this or handle it differently
                print(f"Error invoking notification delegate: {e}")
    
    def invoke_control(self, sender: Any, control_type: str) -> bool:
        """
        Invoke all control delegates registered for the given control type.
        
        Args:
            sender: The object requesting control
            control_type: The type of control requested
            
        Returns:
            True if any delegate returns True, False otherwise
        """
        # Get a thread-safe copy of the delegates to invoke
        delegates_to_invoke = set()
        with self._lock:
            if control_type in self._control_delegates:
                delegates_to_invoke = set(self._control_delegates[control_type])
        
        # If no delegates are registered, return False by default
        if not delegates_to_invoke:
            return False
        
        # Invoke each delegate and collect results
        for delegate in delegates_to_invoke:
            try:
                if delegate(sender, control_type):
                    return True
            except Exception as e:
                # In a real system, you might want to log this or handle it differently
                print(f"Error invoking control delegate: {e}")
        
        return False


class ExecutionLoop:
    """
    Example class that runs an execution loop and provides delegate hooks
    for monitoring and control.
    """
    
    def __init__(self):
        self.delegates = DelegateManager()
        self._should_stop = False
        self._thread = None
        self._step_count = 0
    
    def start(self):
        """Start the execution loop in a separate thread."""
        if self._thread is not None and self._thread.is_alive():
            return  # Already running
        
        self._should_stop = False
        self._thread = threading.Thread(target=self._run)
        self._thread.daemon = True
        self._thread.start()
    
    def stop(self):
        """Signal the execution loop to stop."""
        self._should_stop = True
        if self._thread is not None:
            self._thread.join(timeout=1.0)  # Wait for thread to finish
    
    def _run(self):
        """Main execution loop."""
        while not self._should_stop:
            # Check if should pause
            if self.delegates.invoke_control(self, "pause"):
                # Notify that we're paused
                self.delegates.invoke_notification(self, "paused", None)
                time.sleep(0.1)  # Small delay when paused
                continue
            
            # Perform execution step
            self._step_count += 1
            result = f"Step {self._step_count} completed"
            
            # Simulate some work
            time.sleep(0.2)
            
            # Notify observers
            self.delegates.invoke_notification(self, "step_completed", result)
            
            # Every 5 steps, send a different notification
            if self._step_count % 5 == 0:
                self.delegates.invoke_notification(self, "milestone", self._step_count)


class Observer:
    """
    Example observer class that hooks into the execution loop.
    """
    
    def __init__(self, name):
        self.name = name
        self._pause_requested = False
        self._pause_lock = threading.Lock()
    
    def connect_to_loop(self, loop: ExecutionLoop):
        """Connect this observer to an execution loop."""
        # Register for notifications
        loop.delegates.register_notification("step_completed", self.on_step_completed)
        loop.delegates.register_notification("milestone", self.on_milestone)
        loop.delegates.register_notification("paused", self.on_paused)
        
        # Register for control
        loop.delegates.register_control("pause", self.should_pause)
    
    def disconnect_from_loop(self, loop: ExecutionLoop):
        """Disconnect this observer from an execution loop."""
        # Unregister notifications
        loop.delegates.unregister_notification("step_completed", self.on_step_completed)
        loop.delegates.unregister_notification("milestone", self.on_milestone)
        loop.delegates.unregister_notification("paused", self.on_paused)
        
        # Unregister control
        loop.delegates.unregister_control("pause", self.should_pause)
    
    def request_pause(self, pause: bool = True):
        """Request the execution loop to pause or resume."""
        with self._pause_lock:
            self._pause_requested = pause
    
    def on_step_completed(self, sender, event_type, event_data):
        """Handle step completed notification."""
        print(f"[{self.name}] Received step notification: {event_data}")
    
    def on_milestone(self, sender, event_type, event_data):
        """Handle milestone notification."""
        print(f"[{self.name}] Milestone reached: {event_data}")
    
    def on_paused(self, sender, event_type, event_data):
        """Handle paused notification."""
        print(f"[{self.name}] Execution loop is paused")
    
    def should_pause(self, sender, control_type):
        """Control delegate for pause requests."""
        with self._pause_lock:
            return self._pause_requested


def example():
    """Run an example demonstrating the thread-safe delegates."""
    # Create execution loop
    loop = ExecutionLoop()
    
    # Create observers
    observer1 = Observer("Observer 1")
    observer2 = Observer("Observer 2")
    
    # Connect observers to loop
    observer1.connect_to_loop(loop)
    observer2.connect_to_loop(loop)
    
    # Start the execution loop
    print("Starting execution loop...")
    loop.start()
    
    # Let it run for a bit
    time.sleep(2)
    
    # Request a pause from observer1
    print("\nObserver 1 requesting pause...")
    observer1.request_pause(True)
    
    # Wait while paused
    time.sleep(2)
    
    # Resume execution
    print("\nObserver 1 releasing pause...")
    observer1.request_pause(False)
    
    # Let it run a bit more
    time.sleep(2)
    
    # Disconnect observer1
    print("\nDisconnecting Observer 1...")
    observer1.disconnect_from_loop(loop)
    
    # Let it run a bit more
    time.sleep(2)
    
    # Request a pause from observer2
    print("\nObserver 2 requesting pause...")
    observer2.request_pause(True)
    
    # Wait while paused
    time.sleep(1)
    
    # Resume and stop
    print("\nStopping execution loop...")
    observer2.request_pause(False)
    loop.stop()
    
    print("\nExample completed.")


if __name__ == "__main__":
    example()
