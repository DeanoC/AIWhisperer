"""
BatchCommandTool - Interprets and executes batch script commands.
Part of Debbie's batch processing capabilities.
"""

import re
from typing import Dict, Any, List, Optional, Callable, Union
from dataclasses import dataclass
import logging
from collections import OrderedDict

from .base_tool import AITool
from .script_parser_tool import ParsedScript, ScriptFormat


logger = logging.getLogger(__name__)


class CommandInterpreter:
    """Interprets natural language commands into structured actions"""
    
    # Command patterns for different actions (order matters!)
    PATTERNS = OrderedDict([
        ('execute_command', [
            r'run\s+command\s+["\'](.+?)["\']',
            r'execute\s+command\s+["\'](.+?)["\']',
            r'execute\s+["\'](.+?)["\']',
            r'exec\s+["\'](.+?)["\']',
            r'run\s+["\'](.+?)["\']',
        ]),
        ('read_file', [
            r'read\s+file\s+(.+)',
            r'show\s+content\s+of\s+(.+)',
            r'cat\s+(.+)',
            r'display\s+file\s+(.+)',
            r'view\s+(.+)',
        ]),
        ('list_files', [
            r'list\s+files?\s+in\s+(.+)',
            r'ls\s+(.+)',
            r'show\s+files?\s+in\s+(.+)',
            r'show\s+directory\s+(.+)',
            r'dir(?:ectory)?\s+(.+)',
            r'show\s+(.+)',  # Generic show path - must be last
        ]),
        ('create_file', [
            r'create\s+file\s+(.+?)\s+with\s+content?\s*["\'](.+?)["\']',
            r'create\s+file\s+(.+?)\s+with\s+["\'](.+?)["\']',
            r'create\s+file\s+(.+?)$',  # Just path, no content
            r'create\s+file\s+with\s+["\'](.+?)["\']',  # No path specified
            r'write\s+["\'](.+?)["\']\s+to\s+(.+)',
            r'save\s+file\s+(.+?)\s+containing\s+["\'](.+?)["\']',
            r'save\s+["`](.+?)["`]\s+to\s+(.+)',  # Backtick support
            r'make\s+file\s+(.+?)\s+with\s+["\'](.+?)["\']',
        ]),
        ('write_file', [
            r'write\s+["\'](.+?)["\']\s+to\s+(.+)',
            r'update\s+file\s+(.+?)\s+with\s+["\'](.+?)["\']',
        ]),
        ('switch_agent', [
            r'switch\s+to\s+agent\s+([\w_]+)',
            r'change\s+agent\s+to\s+([\w_]+)',
            r'change\s+to\s+agent\s+([\w_]+)',
            r'use\s+agent\s+([\w_]+)',
            r'activate\s+agent\s+([\w_]+)',
        ]),
        ('search_files', [
            r'search\s+for\s+["\'](.+?)["\']\s+in\s+(.+)',
            r'find\s+["\'](.+?)["\']\s+in\s+(.+)',
            r'grep\s+["\'](.+?)["\']\s+(.+)',
        ]),
        ('list_rfcs', [
            r'list\s+(?:all\s+)?rfcs?',
            r'show\s+(?:all\s+)?rfcs?',
        ]),
        ('create_rfc', [
            r'create\s+rfc\s+["\'](.+?)["\']\s+with\s+["\'](.+?)["\']',
            r'new\s+rfc\s+["\'](.+?)["\']',
        ]),
    ])
    
    def interpret(self, command: str) -> Optional[Dict[str, Any]]:
        """
        Interpret a natural language command into a structured action.
        
        Args:
            command: Natural language command string
            
        Returns:
            Dictionary with action and parameters, or None if not understood
        """
        if not command or not command.strip():
            return None
        
        # Normalize command
        command = command.strip()
        
        # Try each action pattern
        for action, patterns in self.PATTERNS.items():
            for pattern in patterns:
                # Use IGNORECASE flag instead of lowering the whole command
                match = re.search(pattern, command, re.IGNORECASE)
                if match:
                    return self._build_action(action, match, command)
        
        # No pattern matched
        return None
    
    def _build_action(self, action: str, match: re.Match, original_command: str) -> Dict[str, Any]:
        """Build action dictionary from regex match"""
        result = {'action': action}
        
        if action == 'list_files':
            result['path'] = match.group(1).strip()
            
        elif action == 'read_file':
            result['path'] = match.group(1).strip()
            
        elif action == 'create_file':
            # Handle different capture group orders and counts
            if match.lastindex == 1:
                # Check if it's a path-only pattern or content-only
                if r'\.+\s*$' in match.re.pattern or not any(q in match.group(1) for q in ['"', "'", '`']):
                    # Path only
                    result['path'] = match.group(1).strip()
                    result['content'] = ''  # Empty content
                else:
                    # Content only
                    result['content'] = match.group(1)
                    result['path'] = 'unnamed.txt'  # Default path
            elif 'write' in match.re.pattern or ('save' in match.re.pattern and 'to' in match.re.pattern):
                # write/save 'content' to path
                result['content'] = match.group(1)
                result['path'] = match.group(2).strip()
            else:
                # create file path with 'content'
                result['path'] = match.group(1).strip()
                result['content'] = match.group(2)
            
        elif action == 'write_file':
            result['content'] = match.group(1)
            result['path'] = match.group(2).strip()
            
        elif action == 'switch_agent':
            result['agent'] = match.group(1).strip()
            
        elif action == 'execute_command':
            result['command'] = match.group(1)
            
        elif action == 'search_files':
            result['pattern'] = match.group(1)
            result['path'] = match.group(2).strip()
            
        elif action == 'create_rfc':
            result['title'] = match.group(1)
            if match.lastindex > 1:
                result['description'] = match.group(2)
        
        # Extract quoted content from original command if needed
        if action in ['create_file', 'write_file'] and 'content' in result:
            # Try to get the exact quoted content from original command
            quoted_content = self._extract_quoted_content(original_command)
            if quoted_content:
                result['content'] = quoted_content
        
        return result
    
    def _extract_quoted_content(self, command: str) -> Optional[str]:
        """Extract content between quotes, handling mixed quote types"""
        # Try different quote patterns
        patterns = [
            r'"([^"]*)"',  # Double quotes
            r"'([^']*)'",  # Single quotes  
            r'`([^`]*)`',  # Backticks
        ]
        
        for pattern in patterns:
            match = re.search(pattern, command)
            if match:
                return match.group(1)
        
        return None


class BatchCommandTool(AITool):
    """
    Tool for interpreting and executing batch script commands.
    Supports both structured (JSON/YAML) and natural language (text) commands.
    """
    
    def __init__(self):
        """Initialize the batch command tool"""
        super().__init__()
        self._name = "batch_command"
        self._description = "Execute batch scripts with multiple commands in sequence"
        self.interpreter = CommandInterpreter()
        self.tool_registry = None
    
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
                "script": {
                    "type": "object",
                    "description": "Parsed script object from ScriptParserTool"
                },
                "script_path": {
                    "type": "string",
                    "description": "Path to script file (will be parsed first)"
                },
                "stop_on_error": {
                    "type": "boolean",
                    "description": "Stop execution on first error",
                    "default": False
                },
                "dry_run": {
                    "type": "boolean",
                    "description": "Simulate execution without running tools",
                    "default": False
                },
                "pass_context": {
                    "type": "boolean",
                    "description": "Pass context between steps",
                    "default": False
                }
            },
            "required": []
        }
    
    @property
    def category(self) -> str:
        """Tool category"""
        return "Batch Processing"
    
    @property
    def tags(self) -> List[str]:
        """Tool tags"""
        return ["batch", "execution", "script", "automation"]
    
    def get_ai_prompt_instructions(self) -> str:
        """Instructions for AI on how to use this tool"""
        return """
Use this tool to execute batch scripts that have been parsed by ScriptParserTool.
The tool can execute scripts in JSON, YAML, or text format with multiple commands.

Parameters:
- script: A ParsedScript object from ScriptParserTool
- script_path: Alternative - provide path to parse and execute
- stop_on_error: Stop execution if any step fails (default: False)
- dry_run: Simulate execution without running tools (default: False)
- pass_context: Pass results between steps as context (default: False)

The tool will:
1. Take a parsed script with multiple steps
2. Execute each step in sequence using appropriate tools
3. Handle both structured actions and natural language commands
4. Track success/failure of each step
5. Return comprehensive execution results

Example usage:
{
    "script": parsed_script_object,
    "stop_on_error": true
}

Features:
- Executes tools from the tool registry
- Interprets natural language commands
- Tracks execution progress
- Supports dry run mode for testing
- Can pass context between steps
"""
    
    def set_tool_registry(self, registry):
        """Set the tool registry for executing actions"""
        self.tool_registry = registry
    
    def interpret_command(self, command: str) -> Optional[Dict[str, Any]]:
        """
        Interpret a natural language command.
        
        Args:
            command: Natural language command
            
        Returns:
            Action dictionary or None
        """
        return self.interpreter.interpret(command)
    
    def execute_script(
        self,
        script: ParsedScript,
        stop_on_error: bool = False,
        dry_run: bool = False,
        pass_context: bool = False,
        progress_callback: Optional[Callable] = None,
        validate_first: bool = False
    ) -> Dict[str, Any]:
        """
        Execute a parsed script.
        
        Args:
            script: ParsedScript object to execute
            stop_on_error: Stop execution on first error
            dry_run: Simulate execution without running tools
            pass_context: Pass context between steps
            progress_callback: Called after each step with (step_num, total_steps, result)
            validate_first: Validate script before execution
            
        Returns:
            Execution results dictionary
        """
        # Check tool registry
        if not self.tool_registry and not dry_run:
            return {
                'success': False,
                'error': 'Tool registry not set',
                'results': []
            }
        
        # Validate if requested
        if validate_first:
            validation_errors = self._validate_script(script)
            if validation_errors:
                return {
                    'success': False,
                    'error': f'Script validation failed: {"; ".join(validation_errors)}',
                    'results': []
                }
        
        # Initialize execution
        results = []
        context = {} if pass_context else None
        completed_steps = 0
        failed_steps = 0
        
        # Execute each step
        for i, step in enumerate(script.steps):
            step_num = i + 1
            
            try:
                # Execute the step
                if 'action' in step:
                    step_result = self._execute_action_step(
                        step, context, dry_run, results
                    )
                elif 'command' in step:
                    step_result = self._execute_command_step(
                        step, context, dry_run, results
                    )
                else:
                    step_result = {
                        'success': False,
                        'error': 'Step missing action or command',
                        'step': step
                    }
                
                # Track results
                if step_result['success']:
                    completed_steps += 1
                else:
                    failed_steps += 1
                
                results.append(step_result)
                
                # Update context if enabled
                if pass_context and context is not None and 'data' in step_result:
                    if '_context' in step_result['data']:
                        context.update(step_result['data']['_context'])
                
                # Progress callback
                if progress_callback:
                    progress_callback(step_num, len(script.steps), step_result)
                
                # Stop on error if requested
                if not step_result['success'] and stop_on_error:
                    break
                    
            except Exception as e:
                logger.exception(f"Error executing step {step_num}")
                step_result = {
                    'success': False,
                    'error': str(e),
                    'step': step
                }
                results.append(step_result)
                failed_steps += 1
                
                if stop_on_error:
                    break
        
        # Return results
        result = {
            'success': failed_steps == 0,
            'completed_steps': completed_steps,
            'failed_steps': failed_steps,
            'total_steps': len(script.steps),
            'results': results
        }
        
        if dry_run:
            result['dry_run'] = True
        
        return result
    
    def _execute_action_step(
        self,
        step: Dict[str, Any],
        context: Optional[Dict[str, Any]],
        dry_run: bool,
        previous_results: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Execute a structured action step"""
        action = step['action']
        
        # Get the tool
        if not dry_run:
            tool = self.tool_registry.get_tool_by_name(action)
            if not tool:
                return {
                    'success': False,
                    'error': f"Tool '{action}' not found",
                    'action': action,
                    'step': step
                }
        else:
            tool = None
        
        # Prepare parameters
        params = {k: v for k, v in step.items() if k != 'action'}
        
        # Handle parameter interpolation
        params = self._interpolate_parameters(params, previous_results)
        
        # Add context if enabled
        if context is not None:
            params['_context'] = context
        
        # Execute or simulate
        if dry_run:
            return {
                'success': True,
                'action': action,
                'params': params,
                'dry_run': True,
                'data': {'simulated': True}
            }
        else:
            try:
                result_data = tool.execute(**params)
                return {
                    'success': True,
                    'action': action,
                    'data': result_data
                }
            except Exception as e:
                return {
                    'success': False,
                    'error': str(e),
                    'action': action
                }
    
    def _execute_command_step(
        self,
        step: Dict[str, Any],
        context: Optional[Dict[str, Any]],
        dry_run: bool,
        previous_results: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Execute a natural language command step"""
        command = step['command']
        
        # Interpret the command
        interpreted = self.interpreter.interpret(command)
        if not interpreted:
            return {
                'success': False,
                'error': f"Could not interpret command: {command}",
                'command': command
            }
        
        # Execute as action
        action_step = interpreted
        return self._execute_action_step(
            action_step, context, dry_run, previous_results
        )
    
    def _interpolate_parameters(
        self,
        params: Dict[str, Any],
        previous_results: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Interpolate parameters using results from previous steps"""
        interpolated = {}
        
        for key, value in params.items():
            if isinstance(value, str) and '{{' in value and '}}' in value:
                # Simple interpolation - extract variable references
                import re
                pattern = r'\{\{results\[(\d+)\]\.([^}]+)\}\}'
                
                def replace_ref(match):
                    step_idx = int(match.group(1))
                    path = match.group(2)
                    
                    if 0 <= step_idx < len(previous_results):
                        result = previous_results[step_idx].get('data', {})
                        # Navigate path (simple version)
                        for part in path.split('.'):
                            if '[' in part and ']' in part:
                                # Array index
                                name, idx = part.split('[')
                                idx = int(idx.rstrip(']'))
                                result = result.get(name, [])[idx]
                            else:
                                result = result.get(part, '')
                        return str(result)
                    return match.group(0)
                
                interpolated[key] = re.sub(pattern, replace_ref, value)
            else:
                interpolated[key] = value
        
        return interpolated
    
    def _validate_script(self, script: ParsedScript) -> List[str]:
        """Validate script before execution"""
        errors = []
        
        for i, step in enumerate(script.steps):
            if 'action' not in step and 'command' not in step:
                errors.append(f"Step {i+1}: Missing action or command")
            
            if 'action' in step:
                action = step['action']
                # Check for required parameters
                if action in ['read_file', 'write_file', 'create_file']:
                    if 'path' not in step and 'name' not in step:
                        errors.append(f"Step {i+1}: Action '{action}' requires 'path' parameter")
                
                if action in ['create_file', 'write_file']:
                    if 'content' not in step:
                        errors.append(f"Step {i+1}: Action '{action}' requires 'content' parameter")
        
        return errors
    
    def execute(self, **kwargs) -> Dict[str, Any]:
        """Execute the batch command tool"""
        # Get script
        script = kwargs.get('script')
        script_path = kwargs.get('script_path')
        
        if not script and not script_path:
            return {
                'success': False,
                'error': 'Either script or script_path must be provided'
            }
        
        # Parse script if path provided
        if script_path and not script:
            # Would need ScriptParserTool instance here
            return {
                'success': False,
                'error': 'script_path parsing not implemented - provide parsed script'
            }
        
        # Get execution options
        stop_on_error = kwargs.get('stop_on_error', False)
        dry_run = kwargs.get('dry_run', False)
        pass_context = kwargs.get('pass_context', False)
        
        # Execute the script
        return self.execute_script(
            script,
            stop_on_error=stop_on_error,
            dry_run=dry_run,
            pass_context=pass_context
        )