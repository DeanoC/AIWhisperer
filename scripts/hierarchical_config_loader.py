#!/usr/bin/env python3
"""
Hierarchical Configuration Loader

This module provides a configuration loader that supports the new hierarchical
configuration structure with environment-specific overrides.

Example usage:
    from hierarchical_config_loader import HierarchicalConfigLoader
    
    loader = HierarchicalConfigLoader()
    config = loader.load_config(environment='development')
"""

import os
import yaml
from pathlib import Path
from typing import Dict, Any, Optional, List
from collections import ChainMap
import logging
from dotenv import load_dotenv

logger = logging.getLogger(__name__)


class HierarchicalConfigLoader:
    """
    Loads configuration from a hierarchical structure with support for:
    - Base configurations
    - Environment-specific overrides
    - Local overrides
    - Environment variables
    """
    
    def __init__(self, config_dir: Optional[Path] = None):
        """
        Initialize the config loader.
        
        Args:
            config_dir: Path to the configuration directory (default: config/)
        """
        self.root_path = Path.cwd()
        self.config_dir = config_dir or self.root_path / "config"
        
        # Load environment variables
        load_dotenv()
        
    def load_yaml_file(self, file_path: Path) -> Dict[str, Any]:
        """Load a YAML file and return its contents"""
        if not file_path.exists():
            logger.debug(f"Config file not found: {file_path}")
            return {}
            
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = yaml.safe_load(f)
                return content if isinstance(content, dict) else {}
        except Exception as e:
            logger.error(f"Error loading {file_path}: {e}")
            return {}
    
    def merge_configs(self, configs: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Merge multiple configuration dictionaries.
        Later configs override earlier ones.
        """
        if not configs:
            return {}
            
        # Use ChainMap for efficient merging (last map takes precedence)
        # But we need to reverse the order since ChainMap gives precedence to first map
        chain = ChainMap(*reversed(configs))
        
        # Convert to regular dict for deep merging
        result = {}
        for config in configs:
            self._deep_merge(result, config)
            
        return result
    
    def _deep_merge(self, base: Dict[str, Any], override: Dict[str, Any]) -> None:
        """
        Deep merge override dictionary into base dictionary.
        Modifies base in-place.
        """
        for key, value in override.items():
            if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                self._deep_merge(base[key], value)
            else:
                base[key] = value
    
    def load_config(self, 
                   environment: Optional[str] = None,
                   include_local: bool = True,
                   cli_args: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Load configuration with hierarchical overrides.
        
        Loading order (later overrides earlier):
        1. Main configuration (config/main.yaml)
        2. Agent configurations (config/agents/)
        3. Model configurations (config/models/)
        4. Environment-specific config (e.g., config/development/test.yaml)
        5. Local overrides (config/development/local.yaml) if include_local=True
        6. Environment variables
        7. CLI arguments
        
        Args:
            environment: Environment name (e.g., 'test', 'production')
            include_local: Whether to include local.yaml overrides
            cli_args: Command-line arguments that override config values
            
        Returns:
            Merged configuration dictionary
        """
        configs = []
        
        # 1. Load main configuration
        main_config = self.load_yaml_file(self.config_dir / "main.yaml")
        if main_config:
            configs.append(main_config)
            logger.info("Loaded main configuration")
        
        # 2. Load agent configurations
        agents_dir = self.config_dir / "agents"
        if agents_dir.exists():
            agent_config = {}
            
            # Load agents.yaml
            agents_file = agents_dir / "agents.yaml"
            if agents_file.exists():
                agent_config['agents'] = self.load_yaml_file(agents_file).get('agents', {})
                
            # Load tools.yaml
            tools_file = agents_dir / "tools.yaml"
            if tools_file.exists():
                tools_data = self.load_yaml_file(tools_file)
                agent_config['tool_sets'] = tools_data
                
            if agent_config:
                configs.append(agent_config)
                logger.info("Loaded agent configurations")
        
        # 3. Load model configurations
        models_dir = self.config_dir / "models"
        if models_dir.exists():
            model_config = {}
            
            # Load default.yaml
            default_model = self.load_yaml_file(models_dir / "default.yaml")
            if default_model:
                model_config.update(default_model)
                
            # Load tasks.yaml
            tasks_model = self.load_yaml_file(models_dir / "tasks.yaml")
            if tasks_model:
                model_config.update(tasks_model)
                
            if model_config:
                configs.append(model_config)
                logger.info("Loaded model configurations")
        
        # 4. Load environment-specific configuration
        if environment:
            env_file = self.config_dir / "development" / f"{environment}.yaml"
            env_config = self.load_yaml_file(env_file)
            if env_config:
                configs.append(env_config)
                logger.info(f"Loaded {environment} environment configuration")
        
        # 5. Load local overrides
        if include_local:
            local_file = self.config_dir / "development" / "local.yaml"
            local_config = self.load_yaml_file(local_file)
            if local_config:
                configs.append(local_config)
                logger.info("Loaded local configuration overrides")
        
        # Merge all configurations
        merged_config = self.merge_configs(configs)
        
        # 6. Apply environment variable overrides
        self._apply_env_overrides(merged_config)
        
        # 7. Apply CLI argument overrides
        if cli_args:
            self._apply_cli_overrides(merged_config, cli_args)
            
        # Add metadata about configuration sources
        merged_config['_config_metadata'] = {
            'config_dir': str(self.config_dir),
            'environment': environment,
            'included_local': include_local,
            'sources': [str(self.config_dir / "main.yaml")]  # Add other sources as needed
        }
        
        return merged_config
    
    def _apply_env_overrides(self, config: Dict[str, Any]) -> None:
        """Apply environment variable overrides to configuration"""
        # Check for OPENROUTER_API_KEY
        api_key = os.getenv('OPENROUTER_API_KEY')
        if api_key:
            if 'openrouter' not in config:
                config['openrouter'] = {}
            config['openrouter']['api_key'] = api_key
            logger.debug("Applied OPENROUTER_API_KEY from environment")
            
        # Add other environment variable mappings as needed
        # Example: AIWHISPERER_MODEL -> config['openrouter']['model']
        model = os.getenv('AIWHISPERER_MODEL')
        if model:
            if 'openrouter' not in config:
                config['openrouter'] = {}
            config['openrouter']['model'] = model
            logger.debug("Applied AIWHISPERER_MODEL from environment")
    
    def _apply_cli_overrides(self, config: Dict[str, Any], cli_args: Dict[str, Any]) -> None:
        """Apply CLI argument overrides to configuration"""
        # Map CLI args to config paths
        cli_mappings = {
            'output_path': ['output_dir'],
            'project_path': ['project_path'],
            'workspace_path': ['workspace_path'],
            # Add more mappings as needed
        }
        
        for cli_key, cli_value in cli_args.items():
            if cli_value is not None and cli_key in cli_mappings:
                config_path = cli_mappings[cli_key]
                self._set_nested_value(config, config_path, cli_value)
                logger.debug(f"Applied CLI override: {cli_key} = {cli_value}")
    
    def _set_nested_value(self, config: Dict[str, Any], path: List[str], value: Any) -> None:
        """Set a value in a nested dictionary using a path"""
        current = config
        for key in path[:-1]:
            if key not in current:
                current[key] = {}
            current = current[key]
        current[path[-1]] = value
    
    def get_schema_path(self, schema_name: str) -> Optional[Path]:
        """Get the path to a schema file"""
        schema_file = self.config_dir / "schemas" / f"{schema_name}.json"
        return schema_file if schema_file.exists() else None
    
    def list_available_schemas(self) -> List[str]:
        """List all available schema files"""
        schemas_dir = self.config_dir / "schemas"
        if not schemas_dir.exists():
            return []
            
        return [f.stem for f in schemas_dir.glob("*.json")]


# Compatibility function to replace the old load_config
def load_config(config_path: str, cli_args: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Compatibility wrapper for the old load_config function.
    
    This function provides backward compatibility while using the new
    hierarchical configuration system.
    """
    # Determine environment from config_path
    environment = None
    if 'test' in config_path.lower():
        environment = 'test'
    
    # Initialize the hierarchical loader
    loader = HierarchicalConfigLoader()
    
    # Check if we're using the old config structure
    old_config_path = Path(config_path)
    if old_config_path.exists() and old_config_path.name == 'config.yaml':
        # For backward compatibility, load the old config file directly
        logger.warning(f"Using legacy configuration file: {config_path}")
        logger.warning("Consider migrating to the new hierarchical structure")
        
        # Use the old loading logic here if needed
        # For now, we'll just use the new loader with the old file
        config = loader.load_yaml_file(old_config_path)
        
        # Apply the same post-processing as the old loader
        if cli_args:
            loader._apply_cli_overrides(config, cli_args)
        loader._apply_env_overrides(config)
        
        return config
    
    # Use the new hierarchical loading
    return loader.load_config(environment=environment, cli_args=cli_args)


# Example usage and testing
if __name__ == '__main__':
    # Set up logging
    logging.basicConfig(level=logging.INFO)
    
    # Test the loader
    loader = HierarchicalConfigLoader()
    
    print("Loading configuration...")
    config = loader.load_config(environment='test', include_local=True)
    
    print("\nConfiguration loaded:")
    print(f"- OpenRouter model: {config.get('openrouter', {}).get('model', 'NOT SET')}")
    print(f"- Config sources: {config.get('_config_metadata', {}).get('sources', [])}")
    
    print("\nAvailable schemas:")
    for schema in loader.list_available_schemas():
        print(f"  - {schema}")