
from pathlib import Path
from typing import Optional, List, Tuple, Dict
from .exceptions import PromptNotFoundError
from src.ai_whisperer.path_management import PathManager
import logging
logger = logging.getLogger(__name__)
# Placeholder classes for testing purposes
class Prompt:
    """Represents a loaded prompt with lazy content loading."""
    def __init__(self, category: str, name: str, path: Path, metadata: Optional[Dict] = None):
        self.category = category
        self.name = name
        self.path = path
        self._content: Optional[str] = None
        self.metadata = metadata or {}
        self._loader: Optional[PromptLoader] = None # Will be set by PromptSystem

    @property
    def content(self) -> str:
        """Lazily loads and returns the prompt content."""
        if self._content is None and self._loader:
            self._content = self._loader.load_prompt_content(self.path)
        # In a real implementation, templating would happen here or in get_prompt_content
        return self._content

    def set_loader(self, loader: 'PromptLoader'):
        """Sets the loader for lazy content loading."""
        self._loader = loader

class PromptConfiguration:
    """Manages the configuration for the prompt system."""
    def __init__(self, config_data: Optional[Dict] = None):
        self._config = config_data or {}

    def get_override_path(self, category: str, name: str) -> Optional[str]:
        """Gets a direct override path from configuration."""
        key = f"{category}.{name}"
        return self._config.get("prompt_settings", {}).get("overrides", {}).get(key)

    def get_base_path(self, base_name: str) -> Optional[str]:
        """Gets a base path override from configuration."""
        return self._config.get("prompt_settings", {}).get("base_paths", {}).get(base_name)

    def get_definition_path(self, category: str, name: str) -> Optional[str]:
        """Gets a path for a defined prompt not following standard structure."""
        key = f"{category}.{name}"
        return self._config.get("prompt_settings", {}).get("definitions", {}).get(key)


class PromptLoader:
    """Handles the actual reading of prompt content from a file."""
    def load_prompt_content(self, path: Path) -> str:
        """Reads and returns the content of the prompt file."""
        if not path.exists():
            raise FileNotFoundError(f"Prompt file not found at {path}")
        with open(path, 'r', encoding='utf-8') as f:
            return f.read()


class PromptResolver:
    """Determines the correct file path for a requested prompt based on a hierarchy."""
    def __init__(self, prompt_config: PromptConfiguration):
        self._prompt_config = prompt_config

    def resolve_prompt_path(self, category: str, name: str) -> Path:
        """
        Resolves the file path for a prompt based on the defined hierarchy.
        1. Project-relative (project_path) for overrides, definitions, custom, agents, core
        2. Fallback to app_path (codebase) for agents/core if not found in project
        """

        prompt_path = PathManager.get_instance().prompt_path
        app_path = PathManager.get_instance().app_path


        # 1. User-Defined Path (via PromptConfiguration overrides)
        override_path_str = self._prompt_config.get_override_path(category, name)
        if override_path_str:
            resolved_override = Path(PathManager.get_instance().resolve_path(override_path_str))
            if resolved_override.exists():
                return resolved_override

        # 2. User-Defined Path (via PromptConfiguration definitions)
        definition_path_str = self._prompt_config.get_definition_path(category, name)
        if definition_path_str:
            resolved_definition = Path(PathManager.get_instance().resolve_path(definition_path_str))
            if resolved_definition.exists():
                return resolved_definition

        # 3. Custom Directory (project)
        custom_base = self._prompt_config.get_base_path("custom") or "prompts/custom"

        custom_base_path = Path(PathManager.get_instance().resolve_path(custom_base))
        custom_path = custom_base_path / category / f"{name}.prompt.md"
        if custom_path.exists():
            return custom_path

        # 4. Agent-Specific Directory (prompt_path)
        if category == "agents":
            agent_path = prompt_path / "prompts" / "agents" / f"{name}.prompt.md"
            if agent_path.exists():
                return agent_path

        # 5. Core Directory (prompt_path)
        core_path = prompt_path / "prompts" / "core" / f"{name}.prompt.md"
        if core_path.exists():
            return core_path

        # 6. Fallback to app_path (codebase prompts)
        if category == "agents":
            agent_path_app = app_path / "prompts" / "agents" / f"{name}.prompt.md"
            if agent_path_app.exists():
                return agent_path_app
        core_path_app = app_path / "prompts" / "core" / f"{name}.prompt.md"
        if core_path_app.exists():
            return core_path_app

        raise PromptNotFoundError(f"Prompt '{category}.{name}' not found in project or codebase prompts.")



from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from src.ai_whisperer.tools.tool_registry import ToolRegistry

class PromptSystem:
    """The central service for accessing and managing prompts."""
    def __init__(self, prompt_config: PromptConfiguration, tool_registry: Optional['ToolRegistry'] = None):
        self._prompt_config = prompt_config
        self._resolver = PromptResolver(prompt_config)
        self._loader = PromptLoader() # Use the actual loader for integration
        self._tool_registry = tool_registry # Store the optional ToolRegistry instance

    def get_prompt(self, category: str, name: str) -> Prompt:
        """
        Retrieves a Prompt object, with content loaded lazily.
        Raises PromptNotFoundError if not found after checking hierarchy.
        """
        try:
            prompt_path = self._resolver.resolve_prompt_path(category, name)
            prompt = Prompt(category=category, name=name, path=prompt_path)
            prompt.set_loader(self._loader) # Inject loader for lazy loading
            return prompt
        except PromptNotFoundError:
            raise

    def get_formatted_prompt(self, category: str, name: str, include_tools: bool = False, **kwargs) -> str:
        """
        Retrieves the processed and formatted content of a prompt, optionally including tool instructions.
        Handles parameter injection if templating is supported.
        Raises PromptNotFoundError.
        """
        prompt = self.get_prompt(category, name)
        # Assuming Prompt.content handles lazy loading
        content = prompt.content

        # Include tool instructions if requested and tool registry is available
        if include_tools and self._tool_registry:
            tool_instructions = self._tool_registry.get_all_ai_prompt_instructions()
            if tool_instructions:
                content += "\n\n## AVAILABLE TOOLS\n" + tool_instructions

        # Add simple placeholder for templating if kwargs are provided
        # Only replace {{{key}}} to avoid accidental formatting of JSON/code blocks
        if kwargs:
            import re
            for key, value in kwargs.items():
                pattern = r"{{{" + re.escape(key) + r"}}}"
                content = re.sub(pattern, str(value), content)
        return content

    def list_prompts(self, category: Optional[str] = None) -> List[Tuple[str, str]]:
        """
        Lists available prompts, optionally filtered by category.
        Returns a list of (category, name) tuples.
        Note: This is a simplified listing and does not fully scan directories.
        A real implementation would scan directories based on config and resolution.
        """
        available = []
        # Simulate finding some prompts based on standard structure
        # This would need to be more sophisticated to respect config and resolution hierarchy
        standard_prompts = [
            ("core", "initial_plan"),
            ("core", "subtask_generator"),
            ("agents", "code_generation"),
            # Add other standard prompts here
        ]

        for cat, nm in standard_prompts:
            if category is None or category == cat:
                # In a real implementation, we'd check if this prompt is resolvable
                available.append((cat, nm))

        # Add prompts from definitions in config (simplified)
        definitions = self._prompt_config._config.get("prompt_settings", {}).get("definitions", {})
        for key in definitions:
             cat, nm = key.split(".", 1)
             if category is None or category == cat:
                 available.append((cat, nm))

        # Remove duplicates and sort
        available = sorted(list(set(available)))

        return available
    