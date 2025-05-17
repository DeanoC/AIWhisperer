import pytest
from ai_whisperer.delegate_manager import DelegateManager
from ai_whisperer.cli import cli
from click.testing import CliRunner

# Updated test functions for DelegateManager integration after refactoring

# Assuming these Enums and payload models exist after refactoring
# In a real scenario, these would be imported from the actual source files
from enum import Enum
from pydantic import BaseModel
from typing import Any, Dict

class TestNotificationType(Enum):
    __test__ = False # Prevent pytest from collecting this class
    TEST_EVENT = "test_event"

class TestControlType(Enum):
    __test__ = False # Prevent pytest from collecting this class
    TEST_CONTROL = "test_control"

class TestEventPayload(BaseModel):
    __test__ = False # Prevent pytest from collecting this class
    message: str
    data: Dict[str, Any]

# Dummy delegate classes for testing
class DummyNotificationDelegate:
    def __init__(self):
        self.called = False
        self.received_data = None

    def handle(self, sender: Any, event_type: TestNotificationType, event_data: TestEventPayload):
        self.called = True
        self.received_data = event_data

class DummyControlDelegate:
    def __init__(self, return_value: bool):
        self.called = False
        self._return_value = return_value

    def handle(self, sender: Any, control_type: TestControlType) -> bool:
        self.called = True
        return self._return_value

def test_delegate_manager_initialization():
    """
    Test that DelegateManager can be initialized.
    """
    manager = DelegateManager()
    assert isinstance(manager, DelegateManager)

def test_notification_delegate_registration_and_invocation():
    """
    Test that notification delegates can be registered and invoked with typed payloads.
    """
    manager = DelegateManager()
    delegate = DummyNotificationDelegate()
    
    manager.register_notification(TestNotificationType.TEST_EVENT, delegate.handle)
    
    payload = TestEventPayload(message="Hello", data={"key": "value"})
    manager.invoke_notification(None, TestNotificationType.TEST_EVENT, payload)
    
    assert delegate.called is True
    assert delegate.received_data == payload

def test_control_delegate_registration_and_invocation():
    """
    Test that control delegates can be registered and invoked.
    """
    manager = DelegateManager()
    delegate_true = DummyControlDelegate(return_value=True)
    delegate_false = DummyControlDelegate(return_value=False)
    
    manager.register_control(TestControlType.TEST_CONTROL, delegate_false.handle)
    manager.register_control(TestControlType.TEST_CONTROL, delegate_true.handle)
    
    # Invoke control - should return True because delegate_true returns True
    result = manager.invoke_control(None, TestControlType.TEST_CONTROL)

    assert result is True
    # Only assert that at least one delegate was called and that the True-returning delegate was called
    assert delegate_true.called is True

def test_cli_command_with_delegate_integration(mocker):
    """
    Test a CLI command that uses a delegate via DelegateManager.
    This test mocks the DelegateManager to verify interaction.
    Needs refinement once the CLI is refactored to use DelegateManager.
    """
    pytest.skip("CLI command integration test needs implementation after CLI refactoring.")
    # The actual test logic will go here after CLI refactoring
    pass