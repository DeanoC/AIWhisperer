import pytest
from abc import ABC, abstractmethod
from ai_whisperer.context.provider import ContextProvider

class DummyProvider(ContextProvider):
    def __init__(self):
        self._messages = []
        self._metadata = {}

    def store_message(self, message):
        self._messages.append(message)

    def retrieve_messages(self):
        return list(self._messages)

    def set_metadata(self, key, value):
        self._metadata[key] = value

    def get_metadata(self, key, default=None):
        return self._metadata.get(key, default)

def test_context_provider_is_abstract():
    with pytest.raises(TypeError):
        ContextProvider()

def test_dummy_provider_implements_interface():
    provider = DummyProvider()
    provider.store_message("hello")
    provider.store_message("world")
    assert provider.retrieve_messages() == ["hello", "world"]

def test_metadata_support():
    provider = DummyProvider()
    provider.set_metadata("user", "alice")
    provider.set_metadata("session", "xyz")
    assert provider.get_metadata("user") == "alice"
    assert provider.get_metadata("session") == "xyz"
    assert provider.get_metadata("missing", "default") == "default"

def test_interface_contract_methods_exist():
    # Ensure all required methods are present in the interface
    required_methods = [
        "store_message",
        "retrieve_messages",
        "set_metadata",
        "get_metadata",
    ]
    for method in required_methods:
        assert hasattr(ContextProvider, method)
        assert callable(getattr(ContextProvider, method, None))