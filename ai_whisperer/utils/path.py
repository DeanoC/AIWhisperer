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
        if getattr(self, '_initialized', False):
            return
        self._app_path = None
        self._project_path = None
        self._output_path = None
        self._workspace_path = None
        self._prompt_path = None
        self._whisper_path = None
        self._initialized = False

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
            cls._instance._prompt_path = None
            cls._instance._whisper_path = None
            cls._instance._initialized = False
        cls._instance = None
        cls._initialized = False

    def initialize_with_project_json(self, project_json: dict):
        """
        Initialize PathManager using values from a project.json dict.
        Recognized keys: path (project_path), output_path, workspace_path, prompt_path
        """
        project_path = project_json.get("path")
        if not project_path:
            raise ValueError("project.json must contain a 'path' entry")
        self._project_path = Path(str(project_path)).resolve()

        output_path = project_json.get("output_path")
        self._output_path = Path(str(output_path)).resolve() if output_path else (self._project_path / "output").resolve()

        workspace_path = project_json.get("workspace_path")
        self._workspace_path = Path(str(workspace_path)).resolve() if workspace_path else self._project_path

        prompt_path = project_json.get("prompt_path")
        self._prompt_path = Path(str(prompt_path)).resolve() if prompt_path else self._project_path

        whisper_path = project_json.get("whisper_path")
        self._whisper_path = Path(str(whisper_path)).resolve() if whisper_path else None

        self._app_path = Path(__file__).parent.parent.resolve()
        self._initialized = True

    def initialize(self, config_values=None, cli_args=None):
        config_values = config_values or {}
        cli_args = cli_args or {}

        if 'project_path' in config_values and config_values['project_path'] is not None:
            self._project_path = config_values['project_path']
        if 'output_path' in config_values and config_values['output_path'] is not None:
            self._output_path = config_values['output_path']
        if 'workspace_path' in config_values and config_values['workspace_path'] is not None:
            self._workspace_path = config_values['workspace_path']
        if 'prompt_path' in config_values and config_values['prompt_path'] is not None:
            self._prompt_path = config_values['prompt_path']

        if 'project_path' in cli_args and cli_args['project_path'] is not None:
            self._project_path = cli_args['project_path']
        if 'output_path' in cli_args and cli_args['output_path'] is not None:
            self._output_path = cli_args['output_path']
        if 'workspace_path' in cli_args and cli_args['workspace_path'] is not None:
            self._workspace_path = cli_args['workspace_path']
        if 'prompt_path' in cli_args and cli_args['prompt_path'] is not None:
            self._prompt_path = cli_args['prompt_path']

        if self._project_path is None:
            self._project_path = os.getcwd()
        if self._output_path is None and self._project_path is not None:
            self._output_path = os.path.join(self._project_path, "output")
        if self._workspace_path is None and self._project_path is not None:
            self._workspace_path = self._project_path
        if self._prompt_path is None and self._project_path is not None:
            self._prompt_path = self._project_path

        # Ensure all are Path objects and not None
        if self._project_path is not None and not isinstance(self._project_path, Path):
            self._project_path = Path(self._project_path)
        if self._output_path is not None and not isinstance(self._output_path, Path):
            self._output_path = Path(self._output_path)
        if self._workspace_path is not None and not isinstance(self._workspace_path, Path):
            self._workspace_path = Path(self._workspace_path)
        if self._prompt_path is not None and not isinstance(self._prompt_path, Path):
            self._prompt_path = Path(self._prompt_path)

        if self._project_path is not None:
            self._project_path = self._project_path.resolve()
        if self._output_path is not None:
            self._output_path = self._output_path.resolve()
        if self._workspace_path is not None:
            self._workspace_path = self._workspace_path.resolve()
        if self._prompt_path is not None:
            self._prompt_path = self._prompt_path.resolve()
        self._app_path = Path(__file__).parent.parent.resolve()
        self._initialized = True

    @property
    def prompt_path(self):
        if not self._initialized:
            raise RuntimeError("PathManager not initialized.")
        return self._prompt_path

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
    
    @property
    def whisper_path(self):
        if not self._initialized:
            raise RuntimeError("PathManager not initialized.")
        return self._whisper_path

    def resolve_path(self, template_string):
        if not self._initialized:
            raise RuntimeError("PathManager not initialized.")

        resolved = template_string
        resolved = resolved.replace("{app_path}", str(self._app_path if self._app_path is not None else ""))
        resolved = resolved.replace("{project_path}", str(self._project_path if self._project_path is not None else ""))
        resolved = resolved.replace("{output_path}", str(self._output_path if self._output_path is not None else ""))
        resolved = resolved.replace("{workspace_path}", str(self._workspace_path if self._workspace_path is not None else ""))
        resolved = resolved.replace("{prompt_path}", str(self._prompt_path if self._prompt_path is not None else ""))
        resolved = resolved.replace("{whisper_path}", str(self._whisper_path if self._whisper_path is not None else ""))
        return resolved

    def is_path_within_workspace(self, path):
        if not self._initialized:
            raise RuntimeError("PathManager not initialized.")
        try:
            resolved_path = Path(path).resolve()
            if self._workspace_path is None:
                return False
            resolved_workspace_path = self._workspace_path if isinstance(self._workspace_path, Path) else Path(self._workspace_path)
            resolved_workspace_path = resolved_workspace_path.resolve()
            return resolved_path.is_relative_to(resolved_workspace_path)
        except Exception:
            return False

    def is_path_within_output(self, path):
        if not self._initialized:
            raise RuntimeError("PathManager not initialized.")
        try:
            resolved_path = Path(path).resolve()
            if self._output_path is None:
                return False
            resolved_output_path = self._output_path if isinstance(self._output_path, Path) else Path(self._output_path)
            resolved_output_path = resolved_output_path.resolve()
            return resolved_path.is_relative_to(resolved_output_path)
        except Exception:
            return False
    
    def is_path_within_whisper(self, path):
        """Check if path is within the .WHISPER directory."""
        if not self._initialized:
            raise RuntimeError("PathManager not initialized.")
        try:
            resolved_path = Path(path).resolve()
            if self._whisper_path is None:
                return False
            resolved_whisper_path = self._whisper_path if isinstance(self._whisper_path, Path) else Path(self._whisper_path)
            resolved_whisper_path = resolved_whisper_path.resolve()
            return resolved_path.is_relative_to(resolved_whisper_path)
        except Exception:
            return False
    
    def is_path_allowed(self, path):
        """Check if path is allowed for file operations (workspace, output, or whisper)."""
        return (self.is_path_within_workspace(path) or 
                self.is_path_within_output(path) or 
                self.is_path_within_whisper(path))