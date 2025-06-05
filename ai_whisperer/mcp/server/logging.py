"""Structured logging for MCP server."""

import json
import logging
import sys
import traceback
from datetime import datetime, timezone
from typing import Dict, Any, Optional


class JSONFormatter(logging.Formatter):
    """JSON formatter for structured logging."""
    
    def __init__(
        self,
        server_name: str = "aiwhisperer-mcp",
        include_timestamp: bool = True,
        include_location: bool = True
    ):
        super().__init__()
        self.server_name = server_name
        self.include_timestamp = include_timestamp
        self.include_location = include_location
        
    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON."""
        log_data = {
            "server": self.server_name,
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage()
        }
        
        if self.include_timestamp:
            log_data["timestamp"] = datetime.now(timezone.utc).isoformat()
            
        if self.include_location:
            log_data["location"] = {
                "file": record.pathname,
                "line": record.lineno,
                "function": record.funcName
            }
            
        # Add extra fields
        if hasattr(record, "extra_fields"):
            log_data.update(record.extra_fields)
            
        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = {
                "type": record.exc_info[0].__name__,
                "message": str(record.exc_info[1]),
                "traceback": traceback.format_exception(*record.exc_info)
            }
            
        return json.dumps(log_data)
        

class MCPLogger:
    """Enhanced logger for MCP server."""
    
    def __init__(
        self,
        name: str,
        server_name: str = "aiwhisperer-mcp",
        level: int = logging.INFO,
        enable_json: bool = True,
        enable_console: bool = True,
        log_file: Optional[str] = None
    ):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(level)
        self.server_name = server_name
        
        # Remove existing handlers
        self.logger.handlers = []
        
        # Add JSON handler for structured logs
        if enable_json and log_file:
            json_handler = logging.FileHandler(log_file)
            json_handler.setFormatter(JSONFormatter(server_name))
            self.logger.addHandler(json_handler)
            
        # Add console handler for human-readable logs
        if enable_console:
            console_handler = logging.StreamHandler(sys.stderr)
            console_handler.setFormatter(
                logging.Formatter(
                    '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
                )
            )
            self.logger.addHandler(console_handler)
            
    def log_request(
        self,
        level: int,
        message: str,
        method: Optional[str] = None,
        request_id: Optional[str] = None,
        duration_ms: Optional[float] = None,
        **kwargs
    ):
        """Log a request with structured data."""
        extra = {
            "extra_fields": {
                "type": "request",
                "method": method,
                "request_id": request_id,
                "duration_ms": duration_ms,
                **kwargs
            }
        }
        self.logger.log(level, message, extra=extra)
        
    def log_transport(
        self,
        level: int,
        message: str,
        transport: str,
        connection_id: Optional[str] = None,
        event: Optional[str] = None,
        **kwargs
    ):
        """Log transport events."""
        extra = {
            "extra_fields": {
                "type": "transport",
                "transport": transport,
                "connection_id": connection_id,
                "event": event,
                **kwargs
            }
        }
        self.logger.log(level, message, extra=extra)
        
    def log_tool(
        self,
        level: int,
        message: str,
        tool_name: str,
        duration_ms: Optional[float] = None,
        success: Optional[bool] = None,
        **kwargs
    ):
        """Log tool execution."""
        extra = {
            "extra_fields": {
                "type": "tool",
                "tool_name": tool_name,
                "duration_ms": duration_ms,
                "success": success,
                **kwargs
            }
        }
        self.logger.log(level, message, extra=extra)
        
    def log_error(
        self,
        message: str,
        error: Exception,
        method: Optional[str] = None,
        request_id: Optional[str] = None,
        **kwargs
    ):
        """Log an error with context."""
        extra = {
            "extra_fields": {
                "type": "error",
                "error_type": type(error).__name__,
                "error_message": str(error),
                "method": method,
                "request_id": request_id,
                **kwargs
            }
        }
        self.logger.error(message, exc_info=error, extra=extra)
        

def setup_mcp_logging(
    server_name: str = "aiwhisperer-mcp",
    log_level: str = "INFO",
    log_file: Optional[str] = None,
    enable_json: bool = True,
    enable_console: bool = True,
    transport: Optional[str] = None
) -> MCPLogger:
    """Setup MCP logging configuration."""
    # Convert string level to int
    level = getattr(logging, log_level.upper(), logging.INFO)
    
    # For STDIO transport, only log to stderr and disable most logging
    if transport == "stdio":
        enable_console = True
        enable_json = False
        level = max(level, logging.WARNING)  # Only warnings and above
        
    # Create logger
    mcp_logger = MCPLogger(
        name="ai_whisperer.mcp",
        server_name=server_name,
        level=level,
        enable_json=enable_json,
        enable_console=enable_console,
        log_file=log_file
    )
    
    return mcp_logger