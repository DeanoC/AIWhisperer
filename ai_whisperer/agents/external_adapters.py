"""
External Agent Adapters for Agent E.
Provides adapters to format tasks for different external AI coding assistants.
"""
import json
import os
from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path

from .decomposed_task import DecomposedTask
from .agent_e_exceptions import ExternalAgentError
from .external_agent_result import ExternalAgentResult


class ExternalAgentAdapter(ABC):
    """Base class for external agent adapters."""
    
    @abstractmethod
    def format_task(self, task: DecomposedTask) -> Dict[str, Any]:
        """Format a task for the external agent.
        
        Args:
            task: The decomposed task
            
        Returns:
            Dictionary with agent-specific formatting
        """
        pass
    
    @abstractmethod
    def parse_result(self, output: str, error: str = "") -> ExternalAgentResult:
        """Parse the result from external agent execution.
        
        Args:
            output: Standard output from the agent
            error: Standard error from the agent
            
        Returns:
            Parsed result object
        """
        pass
    
    @abstractmethod
    def get_execution_instructions(self, task: DecomposedTask) -> str:
        """Get human-readable instructions for executing the task.
        
        Args:
            task: The decomposed task
            
        Returns:
            Instructions for the human operator
        """
        pass
    
    @abstractmethod
    def validate_environment(self) -> Tuple[bool, str]:
        """Validate that the external agent is available.
        
        Returns:
            Tuple of (is_valid, message)
        """
        pass


class ClaudeCodeAdapter(ExternalAgentAdapter):
    """Adapter for Claude Code CLI (REPL mode)."""
    
    def format_task(self, task: DecomposedTask) -> Dict[str, Any]:
        """Format task for Claude (cut-and-paste approach)."""
        # Import here to avoid circular imports
        from .task_decomposer import TaskDecomposer
        
        # Generate enhanced prompt using TaskDecomposer
        decomposer = TaskDecomposer()
        claude_prompt_data = decomposer.generate_claude_code_prompt(task)
        prompt = claude_prompt_data.get('prompt', task.description)
        
        # Get context files
        context_files = task.context.get('files_to_read', [])
        
        # Expected output based on acceptance criteria
        expected_output = []
        for criterion in task.acceptance_criteria:
            if isinstance(criterion, dict):
                expected_output.append(criterion.get('criterion', ''))
            else:
                expected_output.append(str(criterion))
        
        return {
            'prompt': prompt,
            'context_files': context_files,
            'expected_output': expected_output,
            'working_directory': os.getcwd(),
            'files_to_modify': task.context.get('files_to_modify', [])
        }
    
    def parse_result(self, output: str, error: str = "") -> ExternalAgentResult:
        """Parse Claude Code output."""
        if error and "error" in error.lower():
            return ExternalAgentResult(
                success=False,
                files_changed=[],
                output=output,
                error=error
            )
        
        # Try to parse JSON output
        try:
            if output.strip().startswith('{'):
                result_data = json.loads(output)
                return ExternalAgentResult(
                    success=result_data.get('success', True),
                    files_changed=result_data.get('files_changed', []),
                    output=result_data.get('output', output),
                    metadata=result_data
                )
        except json.JSONDecodeError:
            pass
        
        # Fallback to text parsing
        files_changed = []
        lines = output.split('\n')
        for line in lines:
            if 'modified:' in line or 'created:' in line:
                # Extract filename
                parts = line.split(':', 1)
                if len(parts) > 1:
                    files_changed.append(parts[1].strip())
        
        return ExternalAgentResult(
            success=True,
            files_changed=files_changed,
            output=output
        )
    
    def get_execution_instructions(self, task: DecomposedTask) -> str:
        """Get instructions for using Claude Code CLI in REPL mode."""
        formatted = self.format_task(task)
        
        instructions = [
            "=== Claude Code CLI Instructions (REPL Mode) ===",
            f"Task: {task.title}",
            "",
            "1. Open a terminal in the project directory:",
            f"   cd {formatted['working_directory']}",
            "",
            "2. Start Claude Code CLI in REPL mode:",
            "   claude",
            "",
            "3. Copy and paste the following prompt into the Claude REPL:",
            "",
            "--- PROMPT START ---",
            formatted['prompt'],
            "--- PROMPT END ---",
            "",
            "4. Claude should:",
        ]
        
        # Add specific expectations
        if task.context.get('files_to_read'):
            instructions.append(f"   - Read: {', '.join(task.context['files_to_read'])}")
        if formatted['files_to_modify']:
            instructions.append(f"   - Modify: {', '.join(formatted['files_to_modify'])}")
        
        instructions.extend([
            "",
            "5. Expected outcomes:",
        ])
        
        for outcome in formatted['expected_output']:
            instructions.append(f"   - {outcome}")
        
        instructions.extend([
            "",
            "6. After Claude completes the task:",
            "   - Review the generated code in the output",
            "   - Claude will have made the changes to your local files",
            "   - Verify all tests pass",
            "   - Check code changes are correct",
            "",
            "7. Report results back to Agent E:",
            "   - List which files were modified",
            "   - Confirm if tests pass",
            "   - Note any issues or deviations",
            "",
            "Note: Claude Code CLI has full access to your project files in the current directory."
        ])
        
        return '\n'.join(instructions)
    
    def validate_environment(self) -> Tuple[bool, str]:
        """Check if Claude Code CLI is available."""
        # Check if claude command exists
        claude_path = os.environ.get('CLAUDE_CLI_PATH', 'claude')
        
        # Try to run claude --version
        try:
            import subprocess
            result = subprocess.run(
                [claude_path, '--version'],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                return True, f"Claude Code CLI available: {result.stdout.strip()}"
            else:
                return False, "Claude Code CLI not found. Please install: https://claude.ai/code"
        except Exception as e:
            return False, f"Error checking Claude Code CLI: {str(e)}"


class RooCodeAdapter(ExternalAgentAdapter):
    """Adapter for RooCode in VS Code."""
    
    def format_task(self, task: DecomposedTask) -> Dict[str, Any]:
        """Format task for RooCode."""
        # Get RooCode prompt from task
        roocode_prompt_data = task.external_agent_prompts.get('roocode', {})
        prompt = roocode_prompt_data.get('prompt', task.description)
        
        # RooCode configuration hints
        config_hints = roocode_prompt_data.get('configuration_hints', 
                                             'Use Claude 3.5 Sonnet for best results')
        
        # Build workspace context
        workspace_files = []
        workspace_files.extend(task.context.get('files_to_read', []))
        workspace_files.extend(task.context.get('files_to_modify', []))
        
        # Create RooCode-specific format
        return {
            'prompt': prompt,
            'workspace_files': list(set(workspace_files)),  # Remove duplicates
            'configuration': {
                'model_hint': config_hints,
                'multi_file_edit': len(task.context.get('files_to_modify', [])) > 1
            },
            'vs_code_commands': [
                'Open VS Code in project directory',
                'Ensure RooCode extension is active',
                'Open relevant files in editor'
            ],
            'expected_changes': task.context.get('files_to_modify', [])
        }
    
    def parse_result(self, output: str, error: str = "") -> ExternalAgentResult:
        """Parse RooCode execution result."""
        # RooCode results are typically reported through VS Code UI
        # This is a placeholder for manual reporting
        
        if "error" in output.lower() or error:
            return ExternalAgentResult(
                success=False,
                files_changed=[],
                output=output,
                error=error or "RooCode execution failed"
            )
        
        # Parse files changed from output
        files_changed = []
        if "files modified:" in output.lower():
            lines = output.split('\n')
            for line in lines:
                if line.strip().startswith('-') or line.strip().startswith('*'):
                    file_path = line.strip().lstrip('-*').strip()
                    if file_path:
                        files_changed.append(file_path)
        
        return ExternalAgentResult(
            success=True,
            files_changed=files_changed,
            output=output,
            metadata={'tool': 'roocode', 'vs_code': True}
        )
    
    def get_execution_instructions(self, task: DecomposedTask) -> str:
        """Get instructions for using RooCode."""
        formatted = self.format_task(task)
        
        instructions = [
            "=== RooCode Execution Instructions ===",
            f"Task: {task.title}",
            "",
            "1. Setup VS Code:",
        ]
        
        for cmd in formatted['vs_code_commands']:
            instructions.append(f"   - {cmd}")
        
        instructions.extend([
            "",
            "2. Open these files in the editor:"
        ])
        
        for file in formatted['workspace_files']:
            instructions.append(f"   - {file}")
        
        instructions.extend([
            "",
            "3. In RooCode chat, paste this prompt:",
            "",
            formatted['prompt'],
            "",
            "4. Configuration tips:",
            f"   - {formatted['configuration']['model_hint']}",
        ])
        
        if formatted['configuration']['multi_file_edit']:
            instructions.append("   - Enable multi-file editing mode")
        
        instructions.extend([
            "",
            "5. Expected file changes:"
        ])
        
        for file in formatted['expected_changes']:
            instructions.append(f"   - {file}")
        
        instructions.extend([
            "",
            "6. After RooCode completes:",
            "   - Review all changes in VS Code",
            "   - Run tests to verify",
            "   - Commit if satisfied"
        ])
        
        return '\n'.join(instructions)
    
    def validate_environment(self) -> Tuple[bool, str]:
        """Check if RooCode is available."""
        # Check for VS Code
        vscode_paths = [
            'code',  # Standard command
            '/usr/local/bin/code',
            'C:\\Program Files\\Microsoft VS Code\\Code.exe',
            '/Applications/Visual Studio Code.app/Contents/Resources/app/bin/code'
        ]
        
        for vscode_path in vscode_paths:
            if Path(vscode_path).exists() or os.system(f'which {vscode_path} > /dev/null 2>&1') == 0:
                return True, f"VS Code found. Ensure RooCode extension is installed."
        
        return False, "VS Code not found. RooCode requires VS Code with the RooCode extension."


class GitHubCopilotAdapter(ExternalAgentAdapter):
    """Adapter for GitHub Copilot in agent mode."""
    
    def format_task(self, task: DecomposedTask) -> Dict[str, Any]:
        """Format task for GitHub Copilot."""
        # Get Copilot prompt from task
        copilot_prompt_data = task.external_agent_prompts.get('github_copilot', {})
        prompt = copilot_prompt_data.get('prompt', task.description)
        
        # Copilot agent mode instructions
        agent_mode_setup = [
            "Enable GitHub Copilot agent mode",
            "Set iteration depth based on complexity"
        ]
        
        if task.estimated_complexity in ['complex', 'very_complex']:
            agent_mode_setup.append("Enable deep iteration mode")
        
        return {
            'prompt': prompt,
            'mode': 'agent',
            'agent_mode_setup': agent_mode_setup,
            'complexity': task.estimated_complexity,
            'iteration_hints': [
                "Let Copilot iterate until all tests pass",
                "Allow autonomous refinement",
                "Monitor for convergence"
            ],
            'context_files': task.context.get('files_to_read', []),
            'target_files': task.context.get('files_to_modify', [])
        }
    
    def parse_result(self, output: str, error: str = "") -> ExternalAgentResult:
        """Parse GitHub Copilot execution result."""
        if error:
            return ExternalAgentResult(
                success=False,
                files_changed=[],
                output=output,
                error=error
            )
        
        # Parse iteration results
        iterations = output.count("Iteration") or output.count("iteration")
        
        # Extract files changed
        files_changed = []
        lines = output.split('\n')
        for line in lines:
            if 'modified' in line.lower() or 'updated' in line.lower():
                # Try to extract filename
                words = line.split()
                for word in words:
                    if '.' in word and ('/' in word or '\\' in word):
                        files_changed.append(word.strip(',:'))
        
        return ExternalAgentResult(
            success="error" not in output.lower(),
            files_changed=files_changed,
            output=output,
            metadata={
                'iterations': iterations,
                'agent_mode': True
            }
        )
    
    def get_execution_instructions(self, task: DecomposedTask) -> str:
        """Get instructions for using GitHub Copilot agent mode."""
        formatted = self.format_task(task)
        
        instructions = [
            "=== GitHub Copilot Agent Mode Instructions ===",
            f"Task: {task.title}",
            f"Complexity: {formatted['complexity']}",
            "",
            "1. Setup Copilot agent mode:"
        ]
        
        for setup in formatted['agent_mode_setup']:
            instructions.append(f"   - {setup}")
        
        instructions.extend([
            "",
            "2. Context files to open:"
        ])
        
        for file in formatted['context_files']:
            instructions.append(f"   - {file}")
        
        instructions.extend([
            "",
            "3. Provide this prompt to Copilot:",
            "",
            formatted['prompt'],
            "",
            "4. Agent mode behavior:"
        ])
        
        for hint in formatted['iteration_hints']:
            instructions.append(f"   - {hint}")
        
        instructions.extend([
            "",
            "5. Files that should be modified:"
        ])
        
        for file in formatted['target_files']:
            instructions.append(f"   - {file}")
        
        instructions.extend([
            "",
            "6. Success criteria:",
            "   - All tests pass",
            "   - Code meets acceptance criteria",
            "   - No excessive iterations (stop if > 10)",
            "",
            "7. After completion:",
            "   - Review all changes",
            "   - Run full test suite",
            "   - Check for unintended side effects"
        ])
        
        return '\n'.join(instructions)
    
    def validate_environment(self) -> Tuple[bool, str]:
        """Check if GitHub Copilot is available."""
        # Check for VS Code (most common Copilot environment)
        try:
            import subprocess
            result = subprocess.run(
                ['code', '--list-extensions'],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if result.returncode == 0:
                extensions = result.stdout
                if 'github.copilot' in extensions.lower():
                    return True, "GitHub Copilot extension found in VS Code"
                else:
                    return False, "GitHub Copilot extension not found. Install from VS Code marketplace."
            
        except Exception:
            pass
        
        return False, "Unable to verify GitHub Copilot. Ensure VS Code and Copilot extension are installed."


class AdapterRegistry:
    """Registry for external agent adapters."""
    
    def __init__(self):
        """Initialize the registry."""
        self._adapters: Dict[str, ExternalAgentAdapter] = {}
        
        # Register default adapters
        self._register_defaults()
    
    def _register_defaults(self):
        """Register default adapters."""
        self.register('claude_code', ClaudeCodeAdapter())
        self.register('roocode', RooCodeAdapter())
        self.register('github_copilot', GitHubCopilotAdapter())
    
    def cleanup_all(self):
        """Clean up all adapters that have cleanup methods."""
        for adapter in self._adapters.values():
            if hasattr(adapter, 'cleanup'):
                adapter.cleanup()
    
    def register(self, name: str, adapter: ExternalAgentAdapter):
        """Register an adapter.
        
        Args:
            name: Name of the adapter
            adapter: The adapter instance
        """
        if not isinstance(adapter, ExternalAgentAdapter):
            raise ValueError(f"Adapter must inherit from ExternalAgentAdapter")
        
        self._adapters[name] = adapter
    
    def get_adapter(self, name: str) -> Optional[ExternalAgentAdapter]:
        """Get an adapter by name.
        
        Args:
            name: Name of the adapter
            
        Returns:
            The adapter or None if not found
        """
        return self._adapters.get(name)
    
    def list_adapters(self) -> List[str]:
        """List all registered adapter names.
        
        Returns:
            List of adapter names
        """
        return list(self._adapters.keys())
    
    def validate_all(self) -> Dict[str, Tuple[bool, str]]:
        """Validate all registered adapters.
        
        Returns:
            Dictionary of adapter name to validation result
        """
        results = {}
        for name, adapter in self._adapters.items():
            results[name] = adapter.validate_environment()
        return results
    
    def recommend_adapters(self, task) -> List[Tuple[str, float]]:
        """Recommend adapters for a task based on suitability.
        
        Args:
            task: The task to get recommendations for
            
        Returns:
            List of (adapter_name, score) tuples, sorted by score descending
        """
        recommendations = []
        
        # Score each adapter
        for name, adapter in self._adapters.items():
            score = self._score_adapter_for_task(name, adapter, task)
            recommendations.append((name, score))
        
        # Sort by score descending
        recommendations.sort(key=lambda x: x[1], reverse=True)
        
        return recommendations
    
    def _score_adapter_for_task(self, adapter_name: str, adapter: ExternalAgentAdapter, task) -> float:
        """Score an adapter's suitability for a task.
        
        Args:
            adapter_name: Name of the adapter
            adapter: The adapter instance
            task: The task to score for
            
        Returns:
            Score from 0.0 to 1.0
        """
        score = 0.5  # Base score
        
        # Check task characteristics
        task_name = getattr(task, 'parent_task_name', '').lower()
        complexity = getattr(task, 'estimated_complexity', 'moderate')
        context = getattr(task, 'context', {})
        
        # Claude Code scoring
        if adapter_name == 'claude_code':
            if 'test' in task_name or 'tdd' in str(context.get('constraints', [])).lower():
                score += 0.3  # Claude is good for TDD
            if len(context.get('files_to_modify', [])) <= 2:
                score += 0.2  # Claude is good for focused tasks
            if 'git' in task_name:
                score += 0.1  # Claude has good git integration
        
        # RooCode scoring
        elif adapter_name == 'roocode':
            if len(context.get('files_to_modify', [])) > 2:
                score += 0.3  # RooCode excels at multi-file edits
            if 'refactor' in task_name:
                score += 0.2  # RooCode is great for refactoring
            if complexity in ['complex', 'very_complex']:
                score += 0.1  # RooCode handles complexity well
        
        # GitHub Copilot scoring
        elif adapter_name == 'github_copilot':
            if complexity in ['complex', 'very_complex']:
                score += 0.3  # Copilot's agent mode handles iteration well
            if 'optimize' in task_name or 'performance' in task_name:
                score += 0.2  # Copilot is good at optimization
            if 'iterate' in getattr(task, 'description', '').lower():
                score += 0.2  # Copilot excels at iterative refinement
        
        # Cap score at 1.0
        return min(score, 1.0)