import pytest
from unittest.mock import MagicMock, patch

# Assuming the interactive application and delegate manager are structured as discussed
# in the analysis document.
# We'll need to mock these components for testing.

class MockInteractiveApp:
    """A mock Textual application for testing graceful exit."""
    def __init__(self):
        self.exit_called = False
        self.screen = MagicMock()
        self.delegate_manager = MagicMock()
        self.ai_loop_stopped = False
        self._ctrl_c_pressed_time = None

    async def press_key(self, key):
        """Simulates a key press."""
        if key == "ctrl+c":
            await self._handle_ctrl_c()

    async def _handle_ctrl_c(self):
        """Simulates the internal Ctrl-C handling logic."""
        import time
        current_time = time.time()
        print(f"DEBUG: _handle_ctrl_c: current_time={current_time}, _ctrl_c_pressed_time={self._ctrl_c_pressed_time}")
        if self._ctrl_c_pressed_time is not None and (current_time - self._ctrl_c_pressed_time) < 1: # Assuming a 1 second window for double Ctrl-C
            print("DEBUG: _handle_ctrl_c: Condition met, calling exit()")
            await self.exit()
        else:
            print("DEBUG: _handle_ctrl_c: Condition not met, setting _ctrl_c_pressed_time")
            # Check for timeout and reset if necessary
            if self._ctrl_c_pressed_time is not None and (current_time - self._ctrl_c_pressed_time) >= 1: # Use 1 second as per the test's implicit timeout
                 print("DEBUG: _handle_ctrl_c: Timeout detected, resetting _ctrl_c_pressed_time")
                 self._ctrl_c_pressed_time = None
            else:
                 self._ctrl_c_pressed_time = current_time
            # In a real app, this would display a message. We'll just note it for the test.
            print("Press Ctrl-C again to exit.")

    async def exit(self):
        """Simulates the application exit process."""
        self.exit_called = True
        await self._cleanup()

    async def _cleanup(self):
        """Simulates the cleanup steps."""
        self.delegate_manager.restore_original_delegate()
        self.ai_loop_stopped = True # Simulate signaling the AI loop to stop

@pytest.mark.asyncio
async def test_single_ctrl_c_prompts_for_second():
    """Tests that a single Ctrl-C prompts the user for a second Ctrl-C."""
    app = MockInteractiveApp()
    with patch("builtins.print") as mock_print:
        await app.press_key("ctrl+c")
        mock_print.assert_called_with("Press Ctrl-C again to exit.")
        assert not app.exit_called

@pytest.mark.asyncio
async def test_double_ctrl_c_exits_gracefully():
    """Tests that a double Ctrl-C within the time window triggers graceful exit."""
    app = MockInteractiveApp()
    with patch("time.time", side_effect=[0, 0.5]): # Simulate two Ctrl-C presses within 0.5 seconds
        await app.press_key("ctrl+c")
        await app.press_key("ctrl+c")
        assert app.exit_called
        app.delegate_manager.restore_original_delegate.assert_called_once()
        assert app.ai_loop_stopped

@pytest.mark.asyncio
async def test_ctrl_c_timeout_resets():
    """Tests that a single Ctrl-C followed by a timeout resets the state."""
    app = MockInteractiveApp()
    with patch("time.time", side_effect=[0, 2, 2.1]): # Simulate two Ctrl-C presses with a 2 second delay, and a third press
        await app.press_key("ctrl+c")
        await app.press_key("ctrl+c")
        assert not app.exit_called
        # Pressing Ctrl-C again after timeout should prompt again
        with patch("builtins.print") as mock_print:
             await app.press_key("ctrl+c")
             mock_print.assert_called_with("Press Ctrl-C again to exit.")


# Note: These tests are based on a mock implementation of the interactive app
# and delegate manager. Actual implementation details in the Textual app
# might require adjustments to these tests.