import pytest
import json
import tempfile
import os

from ai_whisperer.context.agent_context import AgentContext
from ai_whisperer.context.provider import ContextProvider

SERIALIZATION_VERSION = "1.0"

def create_sample_context():
    ctx = AgentContext()
    ctx.set("int", 42)
    ctx.set("float", 3.1415)
    ctx.set("str", "hello")
    ctx.set("list", [1, 2, 3])
    ctx.set("dict", {"a": 1, "b": 2})
    ctx.set("bool", True)
    ctx.set("none", None)
    return ctx

def test_context_save_and_load_basic(tmp_path):
    ctx = create_sample_context()
    file_path = tmp_path / "context.json"
    ctx.save_to_file(file_path)
    loaded_ctx = AgentContext.load_from_file(file_path)
    for key in ctx.keys():
        assert loaded_ctx.get(key) == ctx.get(key)
    assert loaded_ctx._version == SERIALIZATION_VERSION

def test_context_data_integrity(tmp_path):
    ctx = create_sample_context()
    file_path = tmp_path / "context.json"
    ctx.save_to_file(file_path)
    loaded_ctx = AgentContext.load_from_file(file_path)
    assert loaded_ctx.to_dict() == ctx.to_dict()

def test_context_version_compatibility(tmp_path):
    ctx = create_sample_context()
    file_path = tmp_path / "context.json"
    ctx.save_to_file(file_path)
    # Simulate older version
    with open(file_path, "r") as f:
        data = json.load(f)
    data["version"] = "0.9"
    with open(file_path, "w") as f:
        json.dump(data, f)
    loaded_ctx = AgentContext.load_from_file(file_path)
    assert hasattr(loaded_ctx, "_version")
    assert loaded_ctx._version == "0.9"

def test_context_handles_corrupted_data(tmp_path):
    file_path = tmp_path / "corrupt.json"
    with open(file_path, "w") as f:
        f.write("{not: valid json")
    with pytest.raises(Exception):
        AgentContext.load_from_file(file_path)
    # Missing required fields
    file_path2 = tmp_path / "missing.json"
    with open(file_path2, "w") as f:
        json.dump({"foo": "bar"}, f)
    with pytest.raises(Exception):
        AgentContext.load_from_file(file_path2)

def test_context_empty_context(tmp_path):
    ctx = AgentContext()
    file_path = tmp_path / "empty.json"
    ctx.save_to_file(file_path)
    loaded_ctx = AgentContext.load_from_file(file_path)
    assert loaded_ctx.to_dict() == {}

def test_context_large_context_performance(tmp_path):
    ctx = AgentContext()
    for i in range(100_000):
        ctx.set(f"key_{i}", i)
    file_path = tmp_path / "large.json"
    import time
    start = time.time()
    ctx.save_to_file(file_path)
    loaded_ctx = AgentContext.load_from_file(file_path)
    elapsed = time.time() - start
    assert loaded_ctx.get("key_99999") == 99999
    assert elapsed < 5  # Should serialize/deserialize in reasonable time

def test_context_json_serialization_interoperability(tmp_path):
    ctx = create_sample_context()
    file_path = tmp_path / "interop.json"
    ctx.save_to_file(file_path)
    with open(file_path, "r") as f:
        data = json.load(f)
    assert "version" in data
    assert "context" in data
    # Can reconstruct context from JSON dict
    loaded_ctx = AgentContext.from_dict(data["context"], version=data["version"])
    assert loaded_ctx.to_dict() == ctx.to_dict()