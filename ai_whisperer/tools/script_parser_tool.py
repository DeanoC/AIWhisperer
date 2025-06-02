"""
Module: ai_whisperer/tools/script_parser_tool.py
Purpose: AI tool implementation for script parser

ScriptParserTool - Parses and validates batch scripts in multiple formats.
Part of Debbie's batch processing capabilities.

Key Components:
- ScriptFormat: Supported script formats
- ParsedScript: Represents a parsed batch script
- ScriptParserTool: 

Usage:
    tool = ScriptFormat()
    result = await tool.execute(**parameters)

Dependencies:
- base_tool
- dataclasses
- enum

Related:
- See docs/batch-mode/PHASE2_TASKS.md
- See docs/batch-mode/PHASE2_CHECKLIST.md
- See docs/batch-mode/IMPLEMENTATION_PLAN.md

"""

import json
import yaml
import os
import signal
import threading
from pathlib import Path
from enum import Enum
from dataclasses import dataclass
import re

from ai_whisperer.tools.base_tool import AITool
from typing import Any, Dict, List, Optional

class ScriptFormat(Enum):
    """Supported script formats"""
    JSON = "json"
    YAML = "yaml"
    TEXT = "text"
    UNKNOWN = "unknown"

@dataclass
class ParsedScript:
    """Represents a parsed batch script"""
    format: ScriptFormat
    name: Optional[str]
    description: Optional[str] = None
    steps: List[Dict[str, Any]] = None
    raw_content: str = ""
    
    def __post_init__(self):
        if self.steps is None:
            self.steps = []

class ScriptParserTool(AITool):
    """
    Tool for parsing and validating batch scripts in multiple formats.
    Supports JSON, YAML, and plain text formats with security validation.
    """
    
    # File size limit (1MB)
    MAX_FILE_SIZE = 1024 * 1024
    
    # Maximum number of steps
    MAX_STEPS = 1000
    
    # Maximum nesting depth for JSON/YAML
    MAX_NESTING_DEPTH = 10
    
    # Maximum parsing time (seconds)
    MAX_PARSING_TIME = 5
    
    # Allowed file extensions
    ALLOWED_EXTENSIONS = {'.json', '.yaml', '.yml', '.txt', '.script'}
    
    # Allowed actions
    ALLOWED_ACTIONS = {
        'list_files', 'read_file', 'create_file', 'write_file',
        'switch_agent', 'list_rfcs', 'create_rfc', 'update_rfc',
        'execute_command', 'search_files', 'analyze_code',
        'get_file_content', 'find_pattern', 'workspace_stats',
        'test'  # For testing purposes
    }
    
    # Dangerous patterns in paths
    DANGEROUS_PATH_PATTERNS = [
        r'\.\./',  # Path traversal
        r'^/etc/',  # System files
        r'^/root/',  # Root directory
        r'^/sys/',  # System files
        r'^/proc/',  # Process files
        r'~/',  # Home directory expansion
        r'\$\{',  # Variable expansion
        r'\$\(',  # Command substitution
        r'`',  # Command substitution
        r';',  # Command separator
        r'\|',  # Pipe
        r'&',  # Background execution
        r'\x00',  # Null byte
        r'\\\\',  # UNC paths
    ]
    
    # Dangerous command patterns for text scripts
    DANGEROUS_COMMANDS = [
        r'\brm\s+-rf',
        r'\bformat\b',
        r'\bdd\s+if=',
        r'\bmkfs\b',
        r'\beval\b',
        r'\bexec\b',
        r'>\s*/dev/',
    ]
    
    def __init__(self, workspace_path: Optional[str] = None):
        """Initialize the script parser tool"""
        super().__init__()
        self._name = "script_parser"
        self._description = "Parse and validate batch scripts in JSON, YAML, or text format"
        self.workspace_path = Path(workspace_path) if workspace_path else None
    
    @property
    def name(self) -> str:
        """Tool identifier"""
        return self._name
    
    @property
    def description(self) -> str:
        """Tool description"""
        return self._description
    
    @property
    def parameters_schema(self) -> Dict[str, Any]:
        """JSON schema for tool parameters"""
        return {
            "type": "object",
            "properties": {
                "file_path": {
                    "type": "string",
                    "description": "Path to the script file to parse"
                }
            },
            "required": ["file_path"]
        }
    
    @property
    def category(self) -> str:
        """Tool category"""
        return "Batch Processing"
    
    @property
    def tags(self) -> List[str]:
        """Tool tags"""
        return ["batch", "parsing", "script", "validation"]
    
    def get_ai_prompt_instructions(self) -> str:
        """Instructions for AI on how to use this tool"""
        return """
Use this tool to parse and validate batch scripts before execution.
The tool supports JSON, YAML, and plain text formats.

Parameters:
- file_path: The path to the script file to parse

The tool will:
1. Detect the script format (JSON, YAML, or text)
2. Parse the script and extract steps
3. Validate the script for security and correctness
4. Return the parsed script data or an error

Example usage:
{
    "file_path": "/workspace/scripts/deploy.json"
}

The tool enforces security restrictions:
- No path traversal or access to system files
- No dangerous commands or actions
- File size limits
- Valid UTF-8 encoding required
"""
    
    def set_workspace(self, workspace_path: str):
        """Set the workspace path for validation"""
        self.workspace_path = Path(workspace_path)
    
    def detect_format(self, file_path: str) -> ScriptFormat:
        """Detect the format of a script file based on extension and content"""
        path = Path(file_path)
        extension = path.suffix.lower()
        
        if extension == '.json':
            return ScriptFormat.JSON
        elif extension in ['.yaml', '.yml']:
            return ScriptFormat.YAML
        elif extension in ['.txt', '.script']:
            return ScriptFormat.TEXT
        
        # Try to detect by content
        try:
            content = path.read_text(encoding='utf-8')
            content = content.strip()
            
            # Try JSON
            if content.startswith('{') or content.startswith('['):
                try:
                    json.loads(content)
                    return ScriptFormat.JSON
                except json.JSONDecodeError:
                    pass
            
            # Try YAML
            try:
                yaml.safe_load(content)
                return ScriptFormat.YAML
            except yaml.YAMLError:
                pass
            
            # Default to text
            return ScriptFormat.TEXT
            
        except Exception:
            return ScriptFormat.UNKNOWN
    
    def parse_script(self, file_path: str) -> ParsedScript:
        """Parse a script file and return structured data"""
        path = Path(file_path)
        
        # Security checks
        self._validate_file_path(path)
        
        # Read file
        content = self._read_file_safely(path)
        
        # Detect format
        format_type = self.detect_format(file_path)
        
        # Parse based on format
        if format_type == ScriptFormat.JSON:
            return self._parse_json(content, path)
        elif format_type == ScriptFormat.YAML:
            return self._parse_yaml(content, path)
        elif format_type == ScriptFormat.TEXT:
            return self._parse_text(content, path)
        else:
            raise ValueError(f"Unknown script format for file: {file_path}")
    
    def _validate_file_path(self, path: Path):
        """Validate file path for security"""
        # Check extension
        if path.suffix.lower() not in self.ALLOWED_EXTENSIONS:
            raise ValueError(f"Unsupported file extension: {path.suffix}")
        
        # Check file exists
        if not path.exists():
            raise ValueError(f"Script file not found: {path}")
        
        # Check file size
        file_size = path.stat().st_size
        if file_size > self.MAX_FILE_SIZE:
            raise ValueError(f"Script file exceeds size limit ({self.MAX_FILE_SIZE} bytes)")
        
        # Check permissions (Unix-like systems)
        if os.name != 'nt':
            try:
                with open(str(path), 'r'):
                    pass
            except PermissionError:
                raise ValueError(f"Permission denied: {path}")
    
    def _read_file_safely(self, path: Path) -> str:
        """Read file with encoding validation"""
        try:
            return path.read_text(encoding='utf-8')
        except UnicodeDecodeError:
            raise ValueError(f"File is not valid UTF-8: {path}")
    
    def _parse_json(self, content: str, path: Path) -> ParsedScript:
        """Parse JSON format script"""
        try:
            data = json.loads(content)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in {path}: {str(e)}")
        
        # Check nesting depth
        if self._get_json_depth(data) > self.MAX_NESTING_DEPTH:
            raise ValueError(f"JSON nesting too deep in {path}")
        
        # Extract script data
        script = ParsedScript(
            format=ScriptFormat.JSON,
            name=data.get('name'),
            description=data.get('description'),
            steps=data.get('steps', []),
            raw_content=content
        )
        
        # Validate script
        self.validate_script(script)
        
        return script
    
    def _parse_yaml(self, content: str, path: Path) -> ParsedScript:
        """Parse YAML format script with timeout protection"""
        # Check for dangerous YAML tags
        if '!!' in content and 'python/' in content:
            raise ValueError(f"Unsafe YAML tags detected in {path}")
        
        # Check for complexity patterns that could cause slow parsing
        if content.count('&') > 100 or content.count('*') > 100:
            raise ValueError(f"YAML too complex (too many anchors/references) in {path}")
        
        # Parse with timeout protection
        try:
            data = self._parse_yaml_with_timeout(content, path)
        except yaml.YAMLError as e:
            raise ValueError(f"Invalid YAML in {path}: {str(e)}")
        
        # Extract script data
        script = ParsedScript(
            format=ScriptFormat.YAML,
            name=data.get('name') if isinstance(data, dict) else None,
            description=data.get('description') if isinstance(data, dict) else None,
            steps=data.get('steps', []) if isinstance(data, dict) else [],
            raw_content=content
        )
        
        # Validate script
        self.validate_script(script)
        
        return script
    
    def _parse_yaml_with_timeout(self, content: str, path: Path):
        """Parse YAML with timeout protection using threading"""
        result = [None]
        exception = [None]
        
        def parse_worker():
            try:
                result[0] = yaml.safe_load(content)
            except Exception as e:
                exception[0] = e
        
        thread = threading.Thread(target=parse_worker)
        thread.daemon = True
        thread.start()
        thread.join(timeout=self.MAX_PARSING_TIME)
        
        if thread.is_alive():
            # Thread is still running, parsing took too long
            raise ValueError(f"YAML parsing timeout ({self.MAX_PARSING_TIME}s) in {path}")
        
        if exception[0]:
            raise exception[0]
        
        return result[0]
    
    def _parse_text(self, content: str, path: Path) -> ParsedScript:
        """Parse plain text format script"""
        lines = content.strip().split('\n')
        steps = []
        
        for line in lines:
            line = line.strip()
            
            # Skip comments and empty lines
            if not line or line.startswith('#'):
                continue
            
            # Check for dangerous commands
            for pattern in self.DANGEROUS_COMMANDS:
                if re.search(pattern, line, re.IGNORECASE):
                    raise ValueError(f"Dangerous command detected: {line}")
            
            # Add as a command step
            steps.append({"command": line})
        
        script = ParsedScript(
            format=ScriptFormat.TEXT,
            name=path.stem,  # Use filename as name
            description=None,
            steps=steps,
            raw_content=content
        )
        
        # Validate script
        self.validate_script(script)
        
        return script
    
    def validate_script(self, script: ParsedScript) -> bool:
        """Validate a parsed script for security and correctness"""
        # Check for empty scripts
        if not script.steps:
            raise ValueError("No steps found in script")
        
        # Check step count
        if len(script.steps) > self.MAX_STEPS:
            raise ValueError(f"Too many steps ({len(script.steps)} > {self.MAX_STEPS})")
        
        # Format-specific validation
        if script.format == ScriptFormat.JSON and not script.name:
            raise ValueError("JSON scripts must have a name")
        
        if script.format == ScriptFormat.YAML:
            # Check for dangerous YAML content
            if '!!' in script.raw_content and 'python/' in script.raw_content:
                raise ValueError("Unsafe YAML content detected")
        
        # Validate each step
        for i, step in enumerate(script.steps):
            self._validate_step(step, i)
        
        # Check for expansion attacks
        total_size = len(json.dumps(script.steps))
        if total_size > self.MAX_FILE_SIZE:
            raise ValueError("Script expansion too large")
        
        return True
    
    def _validate_step(self, step: Dict[str, Any], index: int):
        """Validate a single step"""
        if 'action' in step:
            # Validate action-based step
            action = step['action']
            
            # Check allowed actions
            if action not in self.ALLOWED_ACTIONS:
                if action in ['delete_file', 'remove_directory', 'format_disk',
                            'execute_shell', 'eval', 'exec', 'run_script']:
                    raise ValueError(f"Action '{action}' is not allowed (dangerous)")
                raise ValueError(f"Action '{action}' is not allowed")
            
            # Validate parameters based on action
            if action in ['read_file', 'write_file', 'create_file']:
                # Accept 'name' as alias for 'path' in create_file
                path_param = 'path'
                if action == 'create_file' and 'name' in step and 'path' not in step:
                    path_param = 'name'
                
                if path_param not in step:
                    raise ValueError(f"Missing required parameter 'path' for action '{action}'")
                
                # Validate path type first
                if not isinstance(step[path_param], str):
                    raise ValueError(f"Invalid parameter type for 'path' (expected string, got {type(step[path_param]).__name__})")
                
                # Validate path
                self._validate_path(step[path_param])
            
            # Check content size for file creation
            if action in ['create_file', 'write_file'] and 'content' in step:
                if len(step.get('content', '')) > self.MAX_FILE_SIZE:
                    raise ValueError("Content too large")
        
        elif 'command' in step:
            # Validate text format commands
            command = step['command']
            for pattern in self.DANGEROUS_COMMANDS:
                if re.search(pattern, command, re.IGNORECASE):
                    raise ValueError(f"Dangerous command detected: {command}")
        else:
            raise ValueError(f"Step {index} missing 'action' or 'command'")
    
    def _validate_path(self, path: str):
        """Validate a file path for security"""
        # Check for forbidden paths first
        forbidden_paths = ['/etc/', '/root/', '/sys/', '/proc/', '~/.ssh/']
        for forbidden in forbidden_paths:
            if path.startswith(forbidden):
                raise ValueError(f"Path is forbidden: {path}")
            # Also check without trailing slash
            if path.startswith(forbidden.rstrip('/')):
                raise ValueError(f"Path is unsafe: {path}")
        
        # Check for Windows system paths
        if '\\' in path:  # Windows path
            path_lower = path.lower()
            windows_forbidden = ['c:\\windows\\system32', 'c:\\windows\\system', 'c:\\program files', 'c:\\programdata']
            for forbidden in windows_forbidden:
                if path_lower.startswith(forbidden):
                    raise ValueError(f"Path is unsafe: {path}")
        
        # Check for dangerous patterns
        for pattern in self.DANGEROUS_PATH_PATTERNS:
            if re.search(pattern, path):
                # Special message for path traversal
                if '..' in path:
                    raise ValueError(f"Path traversal detected: {path}")
                raise ValueError(f"Invalid path character or pattern: {path}")
        
        # Check for path traversal (redundant but explicit)
        if '..' in path:
            raise ValueError(f"Path traversal detected: {path}")
        
        # Check for invalid file names
        filename = Path(path).name
        if '\x00' in filename or '\n' in filename:
            raise ValueError(f"Invalid file name: {filename}")
        
        # Check Windows reserved names
        if os.name == 'nt':
            reserved = ['CON', 'PRN', 'AUX', 'NUL', 'COM1', 'LPT1']
            if filename.upper().split('.')[0] in reserved:
                raise ValueError(f"Invalid file name (reserved): {filename}")
        
        # If workspace is set, ensure path is within workspace
        if self.workspace_path:
            try:
                # Handle absolute paths
                if Path(path).is_absolute():
                    full_path = Path(path)
                else:
                    full_path = self.workspace_path / path
                
                # Resolve the path to check where it actually points
                resolved_path = full_path.resolve()
                workspace_resolved = self.workspace_path.resolve()
                
                # Check if resolved path is within workspace
                if not str(resolved_path).startswith(str(workspace_resolved)):
                    raise ValueError(f"Path outside workspace: {path}")
                
                # Check each component for symlinks that might escape
                current = Path(path) if Path(path).is_absolute() else self.workspace_path / path
                parts = current.parts
                check_path = Path(parts[0]) if parts else Path()
                
                for part in parts[1:]:
                    check_path = check_path / part
                    if check_path.exists() and check_path.is_symlink():
                        target = check_path.resolve()
                        if not str(target).startswith(str(workspace_resolved)):
                            raise ValueError(f"Symlink points outside workspace: {path}")
            except ValueError:
                # Re-raise ValueError as is
                raise
            except Exception:
                # If we can't resolve, it's probably invalid
                pass
    
    def _get_json_depth(self, obj, depth=0):
        """Get the maximum nesting depth of a JSON object"""
        if depth > self.MAX_NESTING_DEPTH:
            return depth
        
        if isinstance(obj, dict):
            return max([self._get_json_depth(v, depth + 1) for v in obj.values()] + [depth])
        elif isinstance(obj, list):
            return max([self._get_json_depth(v, depth + 1) for v in obj] + [depth])
        else:
            return depth
    
    def execute(self, **kwargs) -> Dict[str, Any]:
        """Execute the script parser tool"""
        file_path = kwargs.get('file_path')
        
        if not file_path:
            return {
                "success": False,
                "error": "No file_path provided"
            }
        
        try:
            # Parse the script
            parsed_script = self.parse_script(file_path)
            
            # Return parsed data
            return {
                "success": True,
                "parsed_script": {
                    "format": parsed_script.format.value,
                    "name": parsed_script.name,
                    "description": parsed_script.description,
                    "step_count": len(parsed_script.steps),
                    "steps": parsed_script.steps
                }
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
