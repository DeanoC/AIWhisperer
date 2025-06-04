"""Tests for MCP configuration loader."""

import pytest
import os
from unittest.mock import patch, mock_open

from ai_whisperer.mcp.client.config_loader import MCPConfigLoader
from ai_whisperer.mcp.common.types import MCPServerConfig, MCPTransport


class TestMCPConfigLoader:
    """Test MCP configuration loading."""
    
    def test_load_server_configs_disabled(self):
        """Test loading when MCP is disabled."""
        config_data = {
            "mcp": {
                "client": {
                    "enabled": False,
                    "servers": [{"name": "test"}]
                }
            }
        }
        
        configs = MCPConfigLoader.load_server_configs(config_data)
        assert len(configs) == 0
        
    def test_load_server_configs_enabled(self):
        """Test loading server configurations."""
        config_data = {
            "mcp": {
                "client": {
                    "enabled": True,
                    "servers": [
                        {
                            "name": "filesystem",
                            "transport": "stdio",
                            "command": ["mcp-fs", "--root", "/tmp"],
                            "timeout": 45.0
                        },
                        {
                            "name": "github",
                            "transport": "stdio",
                            "command": ["mcp-github"],
                            "env": {"GITHUB_TOKEN": "test_token"}
                        }
                    ]
                }
            }
        }
        
        configs = MCPConfigLoader.load_server_configs(config_data)
        
        assert len(configs) == 2
        
        # Check first server
        fs_config = configs[0]
        assert fs_config.name == "filesystem"
        assert fs_config.transport == MCPTransport.STDIO
        assert fs_config.command == ["mcp-fs", "--root", "/tmp"]
        assert fs_config.timeout == 45.0
        
        # Check second server
        gh_config = configs[1]
        assert gh_config.name == "github"
        assert gh_config.env == {"GITHUB_TOKEN": "test_token"}
        
    def test_env_var_expansion(self):
        """Test environment variable expansion."""
        with patch.dict(os.environ, {"MY_TOKEN": "secret123"}):
            config_data = {
                "mcp": {
                    "client": {
                        "enabled": True,
                        "servers": [{
                            "name": "test",
                            "transport": "stdio",
                            "command": ["test"],
                            "env": {
                                "TOKEN": "${MY_TOKEN}",
                                "PATH": "$PATH",
                                "LITERAL": "literal_value"
                            }
                        }]
                    }
                }
            }
            
            configs = MCPConfigLoader.load_server_configs(config_data)
            
            assert len(configs) == 1
            assert configs[0].env["TOKEN"] == "secret123"
            assert configs[0].env["PATH"] == os.environ.get("PATH", "")
            assert configs[0].env["LITERAL"] == "literal_value"
            
    def test_invalid_server_config(self):
        """Test handling of invalid server configurations."""
        config_data = {
            "mcp": {
                "client": {
                    "enabled": True,
                    "servers": [
                        {
                            "name": "valid",
                            "transport": "stdio",
                            "command": ["test"]
                        },
                        {
                            "name": "missing_command",
                            "transport": "stdio"
                            # Missing required 'command' for stdio
                        },
                        {
                            # Missing 'name'
                            "transport": "stdio",
                            "command": ["test"]
                        }
                    ]
                }
            }
        }
        
        configs = MCPConfigLoader.load_server_configs(config_data)
        
        # Only valid config should be loaded
        assert len(configs) == 1
        assert configs[0].name == "valid"
        
    def test_get_agent_permissions(self):
        """Test getting agent permissions."""
        config_data = {
            "mcp": {
                "client": {
                    "agent_permissions": {
                        "alice": {
                            "allowed_servers": ["filesystem"],
                            "custom_setting": True
                        },
                        "bob": {
                            "allowed_servers": ["github", "filesystem"]
                        }
                    }
                }
            }
        }
        
        alice_perms = MCPConfigLoader.get_agent_permissions(config_data, "alice")
        assert alice_perms["allowed_servers"] == ["filesystem"]
        assert alice_perms["custom_setting"] is True
        
        bob_perms = MCPConfigLoader.get_agent_permissions(config_data, "bob")
        assert bob_perms["allowed_servers"] == ["github", "filesystem"]
        
        # Non-existent agent
        unknown_perms = MCPConfigLoader.get_agent_permissions(config_data, "unknown")
        assert unknown_perms == {}
        
    def test_get_allowed_servers_for_agent(self):
        """Test getting allowed servers for an agent."""
        config_data = {
            "mcp": {
                "client": {
                    "agent_permissions": {
                        "alice": {
                            "allowed_servers": ["filesystem", "github"]
                        }
                    }
                }
            }
        }
        
        servers = MCPConfigLoader.get_allowed_servers_for_agent(config_data, "alice")
        assert servers == ["filesystem", "github"]
        
        # Non-existent agent
        servers = MCPConfigLoader.get_allowed_servers_for_agent(config_data, "unknown")
        assert servers == []