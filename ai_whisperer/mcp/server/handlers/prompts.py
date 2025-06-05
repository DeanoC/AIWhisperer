"""Prompt template handler for MCP server."""

import os
import logging
from typing import Dict, Any, List
from pathlib import Path
import yaml

from ..config import MCPServerConfig

logger = logging.getLogger(__name__)


class PromptHandler:
    """Handles MCP prompt-related requests."""
    
    def __init__(self, config: MCPServerConfig):
        self.config = config
        self.prompts_dir = Path(__file__).parent.parent.parent.parent.parent / "prompts"
        self._prompt_cache: Dict[str, Dict[str, Any]] = {}
        self._load_prompts()
        
    def _load_prompts(self):
        """Load available prompts from the prompts directory."""
        try:
            # Load agent prompts
            agents_dir = self.prompts_dir / "agents"
            if agents_dir.exists():
                for prompt_file in agents_dir.glob("*.prompt.md"):
                    if not prompt_file.name.startswith("_"):  # Skip private prompts
                        prompt_name = prompt_file.stem.replace(".prompt", "")
                        self._load_prompt_file(prompt_name, prompt_file, "agent")
                        
            # Load core prompts
            core_dir = self.prompts_dir / "core"
            if core_dir.exists():
                for prompt_file in core_dir.glob("*.prompt.md"):
                    prompt_name = f"core/{prompt_file.stem.replace('.prompt', '')}"
                    self._load_prompt_file(prompt_name, prompt_file, "core")
                    
            logger.info(f"Loaded {len(self._prompt_cache)} prompt templates")
            
        except Exception as e:
            logger.error(f"Error loading prompts: {e}")
            
    def _load_prompt_file(self, name: str, path: Path, category: str):
        """Load a single prompt file."""
        try:
            content = path.read_text(encoding='utf-8')
            
            # Extract metadata from content if available
            metadata = self._extract_metadata(content)
            
            # Create prompt definition
            prompt_def = {
                "name": name,
                "description": metadata.get("description", f"{category.title()} prompt: {name}"),
                "category": category,
                "arguments": metadata.get("arguments", []),
                "content": content,
                "file_path": str(path.relative_to(self.prompts_dir))
            }
            
            self._prompt_cache[name] = prompt_def
            
        except Exception as e:
            logger.error(f"Error loading prompt {name} from {path}: {e}")
            
    def _extract_metadata(self, content: str) -> Dict[str, Any]:
        """Extract metadata from prompt content."""
        metadata = {}
        
        # Look for YAML frontmatter
        if content.startswith("---"):
            try:
                end_index = content.find("---", 3)
                if end_index > 0:
                    yaml_content = content[3:end_index].strip()
                    metadata = yaml.safe_load(yaml_content) or {}
            except Exception:
                pass
                
        # Extract description from first paragraph if not in metadata
        if "description" not in metadata:
            lines = content.split('\n')
            for line in lines:
                line = line.strip()
                if line and not line.startswith('#') and not line.startswith('---'):
                    metadata["description"] = line[:100] + "..." if len(line) > 100 else line
                    break
                    
        # Define common arguments based on prompt type
        if "arguments" not in metadata:
            # Default arguments that most prompts accept
            metadata["arguments"] = [
                {
                    "name": "task",
                    "description": "The task or question to process",
                    "required": True
                },
                {
                    "name": "context",
                    "description": "Additional context for the prompt",
                    "required": False
                }
            ]
            
        return metadata
        
    async def list_prompts(self, params: Dict[str, Any]) -> List[Dict[str, Any]]:
        """List available prompt templates."""
        prompts = []
        
        # Filter by category if specified
        category_filter = params.get("category")
        
        for name, prompt_def in self._prompt_cache.items():
            if category_filter and prompt_def["category"] != category_filter:
                continue
                
            # Return summary for list
            prompt_summary = {
                "name": name,
                "description": prompt_def["description"],
                "category": prompt_def["category"],
                "arguments": prompt_def["arguments"]
            }
            
            prompts.append(prompt_summary)
            
        logger.debug(f"Returning {len(prompts)} prompts")
        return prompts
        
    async def get_prompt(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get a specific prompt template."""
        name = params.get("name")
        if not name:
            raise ValueError("Missing required field: name")
            
        prompt_def = self._prompt_cache.get(name)
        if not prompt_def:
            raise ValueError(f"Prompt '{name}' not found")
            
        # Build the prompt with provided arguments
        arguments = params.get("arguments", {})
        
        # Simple template substitution
        content = prompt_def["content"]
        for arg_name, arg_value in arguments.items():
            # Replace {{arg_name}} with the value
            placeholder = f"{{{{{arg_name}}}}}"
            content = content.replace(placeholder, str(arg_value))
            
        # Return prompt with metadata
        return {
            "name": name,
            "description": prompt_def["description"],
            "category": prompt_def["category"],
            "content": content,
            "arguments": prompt_def["arguments"],
            "raw_content": prompt_def["content"]  # Original without substitution
        }
        
    def get_available_categories(self) -> List[str]:
        """Get list of available prompt categories."""
        categories = set()
        for prompt_def in self._prompt_cache.values():
            categories.add(prompt_def["category"])
        return sorted(list(categories))