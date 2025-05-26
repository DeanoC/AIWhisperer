import pytest
import threading
from ai_whisperer.ai_service.openrouter_ai_service import OpenRouterAIService

@pytest.fixture(autouse=True)
def patch_openrouter_shutdown(monkeypatch):
    """
    Patch OpenRouterAIService to always use a shutdown_event and set it after each test.
    """
    orig_init = OpenRouterAIService.__init__
    def patched_init(self, config, shutdown_event=None):
        if shutdown_event is None:
            shutdown_event = threading.Event()
        self._test_shutdown_event = shutdown_event
        orig_init(self, config, shutdown_event=shutdown_event)
    monkeypatch.setattr(OpenRouterAIService, "__init__", patched_init)
    yield
    # After each test, set the shutdown_event for all OpenRouterAIService instances
    # (This is a best-effort; in real code, you'd track instances more robustly)
    for obj in list(globals().values()):
        if isinstance(obj, OpenRouterAIService) and hasattr(obj, "_test_shutdown_event"):
            obj._test_shutdown_event.set()
