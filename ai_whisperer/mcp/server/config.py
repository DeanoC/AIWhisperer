"""Configuration for MCP server."""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from enum import Enum


class TransportType(str, Enum):
    """Supported transport types for MCP server."""
    STDIO = "stdio"
    WEBSOCKET = "websocket"
    SSE = "sse"


@dataclass
class ResourcePermission:
    """Permission configuration for resources."""
    pattern: str
    operations: List[str]  # ["read", "write"]
    

@dataclass
class MCPServerConfig:
    """Configuration for MCP server."""
    # Transport settings
    transport: TransportType = TransportType.STDIO
    host: str = "localhost"
    port: int = 3000
    
    # WebSocket settings
    ws_max_connections: int = 100
    ws_heartbeat_interval: float = 30.0
    ws_heartbeat_timeout: float = 60.0
    ws_request_timeout: float = 300.0
    ws_max_queue_size: int = 1000
    ws_enable_compression: bool = True
    
    # SSE settings
    sse_heartbeat_interval: float = 30.0
    sse_max_connections: int = 100
    sse_cors_origins: Optional[List[str]] = None
    
    # Tool exposure settings
    exposed_tools: List[str] = field(default_factory=lambda: [
        "read_file",
        "write_file", 
        "list_directory",
        "search_files",
        "get_file_content",
        "execute_command",
    ])
    
    # Resource permissions
    resource_permissions: List[ResourcePermission] = field(default_factory=lambda: [
        ResourcePermission(pattern="**/*.py", operations=["read"]),
        ResourcePermission(pattern="**/*.md", operations=["read"]),
        ResourcePermission(pattern="output/**/*", operations=["read", "write"]),
    ])
    
    # Security settings
    require_auth: bool = False
    auth_token: Optional[str] = None
    
    # Server info
    server_name: str = "aiwhisperer-mcp"
    server_version: str = "1.0.0"
    
    # Monitoring and logging settings
    enable_metrics: bool = True
    enable_audit_log: bool = True
    metrics_retention_minutes: int = 60
    slow_request_threshold_ms: float = 5000.0
    max_recent_errors: int = 100
    
    # Logging settings
    log_level: str = "INFO"
    log_file: Optional[str] = None
    enable_json_logging: bool = False
    audit_log_file: Optional[str] = None
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "MCPServerConfig":
        """Create config from dictionary."""
        config = cls()
        
        if "transport" in data:
            config.transport = TransportType(data["transport"])
        if "host" in data:
            config.host = data["host"]
        if "port" in data:
            config.port = data["port"]
        if "exposed_tools" in data:
            config.exposed_tools = data["exposed_tools"]
        if "resource_permissions" in data:
            config.resource_permissions = [
                ResourcePermission(**perm) for perm in data["resource_permissions"]
            ]
        if "require_auth" in data:
            config.require_auth = data["require_auth"]
        if "auth_token" in data:
            config.auth_token = data["auth_token"]
        
        # Monitoring settings
        if "enable_metrics" in data:
            config.enable_metrics = data["enable_metrics"]
        if "enable_audit_log" in data:
            config.enable_audit_log = data["enable_audit_log"]
        if "metrics_retention_minutes" in data:
            config.metrics_retention_minutes = data["metrics_retention_minutes"]
        if "slow_request_threshold_ms" in data:
            config.slow_request_threshold_ms = data["slow_request_threshold_ms"]
        if "max_recent_errors" in data:
            config.max_recent_errors = data["max_recent_errors"]
            
        # Logging settings
        if "log_level" in data:
            config.log_level = data["log_level"]
        if "log_file" in data:
            config.log_file = data["log_file"]
        if "enable_json_logging" in data:
            config.enable_json_logging = data["enable_json_logging"]
        if "audit_log_file" in data:
            config.audit_log_file = data["audit_log_file"]
            
        return config