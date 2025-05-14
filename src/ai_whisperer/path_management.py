import os
from pathlib import Path

class PathManager:
    _instance = None
    _initialized = False

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(PathManager, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        if self._initialized:
            return # Already initialized

        self._app_path = None
        self._project_path = None
        self._output_path = None
        self._workspace_path = None
        self._initialized = False # Use a flag to track initialization state

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    @classmethod
    def _reset_instance(cls):
        """Helper method to reset the singleton instance for testing."""
        if cls._instance is not None:
            cls._instance._app_path = None
            cls._instance._project_path = None
            cls._instance._output_path = None
            cls._instance._workspace_path = None
            cls._instance._initialized = False
        cls._instance = None
        cls._initialized = False

    def initialize(self, config_values=None, cli_args=None):
        # Always set paths from config/CLI/defaults, so each config load is independent
        config_values = config_values or {}
        cli_args = cli_args or {}

        # 1. Apply config values
        if 'project_path' in config_values and config_values['project_path'] is not None:
            self._project_path = config_values['project_path']
        if 'output_path' in config_values and config_values['output_path'] is not None:
            self._output_path = config_values['output_path']
        if 'workspace_path' in config_values and config_values['workspace_path'] is not None:
            self._workspace_path = config_values['workspace_path']

        # 2. Apply CLI arguments (override config)
        if 'project_path' in cli_args and cli_args['project_path'] is not None:
            self._project_path = cli_args['project_path']
        if 'output_path' in cli_args and cli_args['output_path'] is not None:
            self._output_path = cli_args['output_path']
        if 'workspace_path' in cli_args and cli_args['workspace_path'] is not None:
            self._workspace_path = cli_args['workspace_path']

        # 3. Apply defaults if not set by config or CLI
        if self._project_path is None:
            self._project_path = os.getcwd() # Default project path to current working directory
        if self._output_path is None and self._project_path is not None:
             self._output_path = os.path.join(self._project_path, "output") # Default output path
        if self._workspace_path is None and self._project_path is not None:
             self._workspace_path = self._project_path # Default workspace path

        self._project_path = Path(self._project_path).resolve()
        self._output_path = Path(self._output_path).resolve()
        self._workspace_path = Path(self._workspace_path).resolve()
        self._app_path = Path(__file__).parent.parent.resolve() # Assuming this file is in src/ai_whisperer

        self._initialized = True

    @property
    def app_path(self):
        if not self._initialized:
             raise RuntimeError("PathManager not initialized.")
        return self._app_path

    @property
    def project_path(self):
        if not self._initialized:
             raise RuntimeError("PathManager not initialized.")
        return self._project_path

    @property
    def output_path(self):
        if not self._initialized:
             raise RuntimeError("PathManager not initialized.")
        return self._output_path

    @property
    def workspace_path(self):
        if not self._initialized:
             raise RuntimeError("PathManager not initialized.")
        return self._workspace_path

    def resolve_path(self, template_string):
        if not self._initialized:
             raise RuntimeError("PathManager not initialized.")

        resolved = template_string
        resolved = resolved.replace("{app_path}", str(self._app_path if self._app_path is not None else ""))
        resolved = resolved.replace("{project_path}", str(self._project_path if self._project_path is not None else ""))
        resolved = resolved.replace("{output_path}", str(self._output_path if self._output_path is not None else ""))
        resolved = resolved.replace("{workspace_path}", str(self._workspace_path if self._workspace_path is not None else ""))

        return resolved