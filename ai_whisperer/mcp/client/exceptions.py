"""Exception types for MCP client."""


class MCPError(Exception):
    """Base exception for MCP-related errors."""
    
    def __init__(self, message: str, code: int = None, data: dict = None):
        super().__init__(message)
        self.message = message
        self.code = code
        self.data = data or {}


class MCPConnectionError(MCPError):
    """Raised when connection to MCP server fails."""
    pass


class MCPToolError(MCPError):
    """Raised when MCP tool execution fails."""
    pass


class MCPTimeoutError(MCPError):
    """Raised when MCP operation times out."""
    pass


class MCPProtocolError(MCPError):
    """Raised when MCP protocol violation occurs."""
    pass