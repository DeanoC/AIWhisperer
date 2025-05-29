"""Tests for tool sets functionality."""
import pytest
from pathlib import Path
import tempfile
import yaml
from typing import List
from unittest.mock import Mock, patch

from ai_whisperer.tools.tool_set import ToolSet, ToolSetManager
from ai_whisperer.tools.tool_registry import ToolRegistry, get_tool_registry
from ai_whisperer.tools.base_tool import AITool


class MockTool(AITool):
    """Mock tool for testing."""
    def __init__(self, tool_name: str, tags: list = None):
        self._name = tool_name
        self._tags = tags or []
        self._description = f"Mock tool {tool_name}"
        
    @property
    def name(self) -> str:
        return self._name
        
    @property
    def description(self) -> str:
        return self._description
        
    @property
    def parameters_schema(self) -> dict:
        return {
            "type": "object",
            "properties": {},
            "required": []
        }
        
    @property
    def tags(self) -> List[str]:
        return self._tags
        
    def execute(self, **kwargs):
        return {"result": f"Executed {self.name}"}
    
    def get_openrouter_tool_definition(self):
        return {"name": self.name}
    
    def get_ai_prompt_instructions(self):
        return f"Use {self.name} for testing"


class TestToolSet:
    """Test the ToolSet class."""
    
    def test_tool_set_creation(self):
        """Test creating a tool set from config."""
        config = {
            'description': 'Test tool set',
            'inherits': ['base_set'],
            'tools': ['tool1', 'tool2'],
            'tags': ['tag1', 'tag2'],
            'deny_tags': ['bad_tag']
        }
        
        tool_set = ToolSet('test_set', config)
        
        assert tool_set.name == 'test_set'
        assert tool_set.description == 'Test tool set'
        assert tool_set.inherits == ['base_set']
        assert tool_set.tools == {'tool1', 'tool2'}
        assert tool_set.tags == {'tag1', 'tag2'}
        assert tool_set.deny_tags == {'bad_tag'}
        
    def test_tool_set_minimal_config(self):
        """Test creating a tool set with minimal config."""
        config = {}
        
        tool_set = ToolSet('minimal', config)
        
        assert tool_set.name == 'minimal'
        assert tool_set.description == ''
        assert tool_set.inherits == []
        assert tool_set.tools == set()
        assert tool_set.tags == set()
        assert tool_set.deny_tags == set()


class TestToolSetManager:
    """Test the ToolSetManager class."""
    
    def test_load_config(self, tmp_path):
        """Test loading tool sets from YAML config."""
        # Create test config
        config_data = {
            'base_sets': {
                'readonly': {
                    'description': 'Read-only tools',
                    'tools': ['read_file'],
                    'tags': ['filesystem', 'readonly']
                }
            },
            'agent_sets': {
                'analyst': {
                    'description': 'Analyst tools',
                    'inherits': ['readonly'],
                    'tools': ['analyze'],
                    'tags': ['analysis']
                }
            },
            'specialized_sets': {
                'secure': {
                    'description': 'Secure tools',
                    'inherits': ['readonly'],
                    'deny_tags': ['dangerous']
                }
            }
        }
        
        config_path = tmp_path / 'tool_sets.yaml'
        with open(config_path, 'w') as f:
            yaml.dump(config_data, f)
        
        manager = ToolSetManager(config_path)
        
        # Check loaded sets
        assert len(manager.tool_sets) == 3
        assert 'readonly' in manager.tool_sets
        assert 'analyst' in manager.tool_sets
        assert 'secure' in manager.tool_sets
        
        # Check readonly set
        readonly = manager.get_tool_set('readonly')
        assert readonly.description == 'Read-only tools'
        assert readonly.tools == {'read_file'}
        assert readonly.tags == {'filesystem', 'readonly'}
        
    def test_inheritance_resolution(self, tmp_path):
        """Test that inheritance is properly resolved."""
        # Create test config with inheritance
        config_data = {
            'base_sets': {
                'base': {
                    'tools': ['tool1', 'tool2'],
                    'tags': ['tag1']
                },
                'secondary': {
                    'inherits': ['base'],
                    'tools': ['tool3'],
                    'tags': ['tag2']
                }
            },
            'agent_sets': {
                'complex': {
                    'inherits': ['secondary'],
                    'tools': ['tool4'],
                    'tags': ['tag3'],
                    'deny_tags': ['bad']
                }
            }
        }
        
        config_path = tmp_path / 'tool_sets.yaml'
        with open(config_path, 'w') as f:
            yaml.dump(config_data, f)
        
        manager = ToolSetManager(config_path)
        
        # Check base set
        base_tools = manager.get_tools_for_set('base')
        base_tags = manager.get_tags_for_set('base')
        assert base_tools == {'tool1', 'tool2'}
        assert base_tags == {'tag1'}
        
        # Check secondary set (inherits from base)
        secondary_tools = manager.get_tools_for_set('secondary')
        secondary_tags = manager.get_tags_for_set('secondary')
        assert secondary_tools == {'tool1', 'tool2', 'tool3'}
        assert secondary_tags == {'tag1', 'tag2'}
        
        # Check complex set (inherits from secondary)
        complex_tools = manager.get_tools_for_set('complex')
        complex_tags = manager.get_tags_for_set('complex')
        complex_deny_tags = manager.get_deny_tags_for_set('complex')
        assert complex_tools == {'tool1', 'tool2', 'tool3', 'tool4'}
        assert complex_tags == {'tag1', 'tag2', 'tag3'}
        assert complex_deny_tags == {'bad'}
        
    def test_circular_inheritance_detection(self, tmp_path):
        """Test that circular inheritance is detected."""
        # Create config with circular inheritance
        config_data = {
            'base_sets': {
                'set1': {
                    'inherits': ['set2'],
                    'tools': ['tool1']
                },
                'set2': {
                    'inherits': ['set3'],
                    'tools': ['tool2']
                },
                'set3': {
                    'inherits': ['set1'],  # Circular!
                    'tools': ['tool3']
                }
            }
        }
        
        config_path = tmp_path / 'tool_sets.yaml'
        with open(config_path, 'w') as f:
            yaml.dump(config_data, f)
        
        # Should raise ValueError for circular inheritance
        with pytest.raises(ValueError, match="Circular inheritance"):
            ToolSetManager(config_path)
            
    def test_get_tool_set_info(self, tmp_path):
        """Test getting detailed info about a tool set."""
        config_data = {
            'base_sets': {
                'base': {
                    'description': 'Base set',
                    'tools': ['tool1'],
                    'tags': ['tag1']
                }
            },
            'agent_sets': {
                'derived': {
                    'description': 'Derived set',
                    'inherits': ['base'],
                    'tools': ['tool2'],
                    'tags': ['tag2'],
                    'deny_tags': ['bad']
                }
            }
        }
        
        config_path = tmp_path / 'tool_sets.yaml'
        with open(config_path, 'w') as f:
            yaml.dump(config_data, f)
        
        manager = ToolSetManager(config_path)
        
        # Get info for derived set
        info = manager.get_tool_set_info('derived')
        
        assert info['name'] == 'derived'
        assert info['description'] == 'Derived set'
        assert info['inherits'] == ['base']
        assert info['direct_tools'] == ['tool2']
        assert info['direct_tags'] == ['tag2']
        assert info['direct_deny_tags'] == ['bad']
        assert set(info['resolved_tools']) == {'tool1', 'tool2'}
        assert set(info['resolved_tags']) == {'tag1', 'tag2'}
        assert info['resolved_deny_tags'] == ['bad']


class TestToolRegistryWithSets:
    """Test tool registry integration with tool sets."""
    
    @pytest.fixture
    def registry_with_tools(self):
        """Create a registry with some mock tools."""
        registry = ToolRegistry()
        registry.reset_tools()
        
        # Register some tools
        registry.register_tool(MockTool('read_file', ['filesystem', 'file_read']))
        registry.register_tool(MockTool('write_file', ['filesystem', 'file_write']))
        registry.register_tool(MockTool('list_directory', ['filesystem', 'directory_browse']))
        registry.register_tool(MockTool('execute_command', ['code_execution', 'dangerous']))
        registry.register_tool(MockTool('analyze_code', ['analysis']))
        
        return registry
        
    def test_get_tools_by_set(self, registry_with_tools, tmp_path):
        """Test getting tools by tool set."""
        # Create test config
        config_data = {
            'base_sets': {
                'readonly': {
                    'tools': ['read_file', 'list_directory'],
                    'tags': ['analysis']
                }
            }
        }
        
        config_path = tmp_path / 'tool_sets.yaml'
        with open(config_path, 'w') as f:
            yaml.dump(config_data, f)
        
        registry_with_tools.initialize_tool_sets(str(config_path))
        
        # Get tools for readonly set
        tools = registry_with_tools.get_tools_by_set('readonly')
        tool_names = {tool.name for tool in tools}
        
        # Should include explicit tools and tag-based tools
        assert 'read_file' in tool_names
        assert 'list_directory' in tool_names
        assert 'analyze_code' in tool_names  # Has 'analysis' tag
        assert 'write_file' not in tool_names
        assert 'execute_command' not in tool_names
        
    def test_get_tools_by_set_with_deny_tags(self, registry_with_tools, tmp_path):
        """Test that deny_tags filter out tools."""
        # Create test config
        config_data = {
            'base_sets': {
                'secure': {
                    'tags': ['filesystem'],
                    'deny_tags': ['dangerous', 'file_write']
                }
            }
        }
        
        config_path = tmp_path / 'tool_sets.yaml'
        with open(config_path, 'w') as f:
            yaml.dump(config_data, f)
        
        registry_with_tools.initialize_tool_sets(str(config_path))
        
        # Get tools for secure set
        tools = registry_with_tools.get_tools_by_set('secure')
        tool_names = {tool.name for tool in tools}
        
        # Should include filesystem tools except dangerous/write ones
        assert 'read_file' in tool_names
        assert 'list_directory' in tool_names
        assert 'write_file' not in tool_names  # Has file_write tag
        assert 'execute_command' not in tool_names  # Has dangerous tag
        
    def test_get_tools_for_agent(self, registry_with_tools, tmp_path):
        """Test getting tools for an agent with all filtering options."""
        # Create test config
        config_data = {
            'base_sets': {
                'basic': {
                    'tools': ['read_file', 'write_file']
                }
            }
        }
        
        config_path = tmp_path / 'tool_sets.yaml'
        with open(config_path, 'w') as f:
            yaml.dump(config_data, f)
        
        registry_with_tools.initialize_tool_sets(str(config_path))
        
        # Test with tool sets and tags
        tools = registry_with_tools.get_tools_for_agent(
            tool_sets=['basic'],
            tags=['analysis']
        )
        tool_names = {tool.name for tool in tools}
        assert tool_names == {'read_file', 'write_file', 'analyze_code'}
        
        # Test with allow list
        tools = registry_with_tools.get_tools_for_agent(
            tool_sets=['basic'],
            tags=['analysis'],
            allow_tools=['read_file', 'analyze_code']
        )
        tool_names = {tool.name for tool in tools}
        assert tool_names == {'read_file', 'analyze_code'}  # write_file filtered out
        
        # Test with deny list (overrides everything)
        tools = registry_with_tools.get_tools_for_agent(
            tool_sets=['basic'],
            tags=['analysis'],
            allow_tools=['read_file', 'analyze_code'],
            deny_tools=['analyze_code']
        )
        tool_names = {tool.name for tool in tools}
        assert tool_names == {'read_file'}  # analyze_code denied
        
    def test_tool_filtering_precedence(self, registry_with_tools):
        """Test that deny > allow > tool_sets/tags precedence is respected."""
        # No initialization needed for this test
        
        # Start with all tools via tags
        tools = registry_with_tools.get_tools_for_agent(
            tags=['filesystem', 'analysis', 'code_execution']
        )
        assert len(tools) == 5  # All tools
        
        # Apply allow list
        tools = registry_with_tools.get_tools_for_agent(
            tags=['filesystem', 'analysis', 'code_execution'],
            allow_tools=['read_file', 'write_file', 'execute_command']
        )
        tool_names = {tool.name for tool in tools}
        assert tool_names == {'read_file', 'write_file', 'execute_command'}
        
        # Apply deny list (overrides allow)
        tools = registry_with_tools.get_tools_for_agent(
            tags=['filesystem', 'analysis', 'code_execution'],
            allow_tools=['read_file', 'write_file', 'execute_command'],
            deny_tools=['execute_command']
        )
        tool_names = {tool.name for tool in tools}
        assert tool_names == {'read_file', 'write_file'}


def test_registry_singleton_with_tool_sets():
    """Test that tool set manager is preserved in singleton."""
    registry1 = get_tool_registry()
    registry1.initialize_tool_sets()
    
    registry2 = get_tool_registry()
    
    # Should be same instance and have tool set manager
    assert registry1 is registry2
    assert registry2._tool_set_manager is not None