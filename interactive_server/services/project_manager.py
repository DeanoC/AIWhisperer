"""Project management service for handling AIWhisperer projects."""

import os
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, List, Dict, Any
import logging
from contextlib import contextmanager

from ..models.project import (
    Project, ProjectCreate, ProjectJoin, ProjectCreateNew, ProjectUpdate, ProjectSummary,
    ProjectHistory, UISettings, ProjectSettings
)
from ai_whisperer.utils.path import PathManager


logger = logging.getLogger(__name__)


class ProjectManager:
    """Manages AIWhisperer projects and their associated data."""
    
    def __init__(self, data_dir: Path):
        """Initialize project manager with data directory."""
        self.data_dir = Path(data_dir)
        self.projects_file = self.data_dir / "projects.json"
        self.history_file = self.data_dir / "project_history.json"
        self.ui_settings_file = self.data_dir / "ui_settings.json"
        self.active_project: Optional[Project] = None
        
        # Ensure data directory exists
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        # Load existing data
        self._load_projects()
        self._load_history()
        self._load_ui_settings()
    
    def _load_projects(self) -> Dict[str, Project]:
        """Load projects from disk."""
        if not self.projects_file.exists():
            self.projects = {}
            return self.projects
            
        try:
            with open(self.projects_file, 'r') as f:
                data = json.load(f)
                self.projects = {
                    pid: Project(**pdata) for pid, pdata in data.items()
                }
        except Exception as e:
            logger.error(f"Failed to load projects: {e}")
            self.projects = {}
        
        return self.projects
    
    def _save_projects(self):
        """Save projects to disk."""
        try:
            data = {
                pid: proj.model_dump() for pid, proj in self.projects.items()
            }
            with open(self.projects_file, 'w') as f:
                json.dump(data, f, indent=2, default=str)
        except Exception as e:
            logger.error(f"Failed to save projects: {e}")
    
    def _load_history(self) -> ProjectHistory:
        """Load project history from disk."""
        if not self.history_file.exists():
            self.history = ProjectHistory()
            return self.history
            
        try:
            with open(self.history_file, 'r') as f:
                data = json.load(f)
                self.history = ProjectHistory(**data)
        except Exception as e:
            logger.error(f"Failed to load project history: {e}")
            self.history = ProjectHistory()
        
        return self.history
    
    def _save_history(self):
        """Save project history to disk."""
        try:
            with open(self.history_file, 'w') as f:
                json.dump(self.history.model_dump(), f, indent=2, default=str)
        except Exception as e:
            logger.error(f"Failed to save project history: {e}")
    
    def _load_ui_settings(self) -> UISettings:
        """Load UI settings from disk."""
        if not self.ui_settings_file.exists():
            self.ui_settings = UISettings()
            return self.ui_settings
            
        try:
            with open(self.ui_settings_file, 'r') as f:
                data = json.load(f)
                self.ui_settings = UISettings(**data)
        except Exception as e:
            logger.error(f"Failed to load UI settings: {e}")
            self.ui_settings = UISettings()
        
        return self.ui_settings
    
    def _save_ui_settings(self):
        """Save UI settings to disk."""
        try:
            with open(self.ui_settings_file, 'w') as f:
                json.dump(self.ui_settings.model_dump(), f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save UI settings: {e}")
    
    def _create_whisper_structure(self, project_path: Path, custom_whisper_path: Optional[Path] = None) -> Path:
        """Create .WHISPER directory structure for a project."""
        if custom_whisper_path:
            whisper_path = custom_whisper_path / f".WHISPER_{project_path.name}"
        else:
            whisper_path = project_path / ".WHISPER"
        
        # Create directory structure
        directories = [
            whisper_path,
            whisper_path / "plans" / "initial",
            whisper_path / "plans" / "refined",
            whisper_path / "sessions",
            whisper_path / "agents" / "alice",
            whisper_path / "agents" / "patricia",
            whisper_path / "agents" / "tessa",
            whisper_path / "artifacts"
        ]
        
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)
        
        return whisper_path
    
    def _setup_project_template(self, project_path: Path, template: str):
        """Set up project template files."""
        if template == "basic":
            # Create basic project structure
            (project_path / "src").mkdir(exist_ok=True)
            (project_path / "docs").mkdir(exist_ok=True)
            
            # Create README.md
            readme_content = f"""# {project_path.name}

Project created with AIWhisperer.

## Structure

- `src/` - Source code
- `docs/` - Documentation
- `.WHISPER/` - AIWhisperer project data

## Getting Started

1. Open this project in AIWhisperer
2. Start chatting with agents to develop your project
"""
            with open(project_path / "README.md", 'w') as f:
                f.write(readme_content)
                
        elif template == "python":
            # Python project template
            (project_path / "src").mkdir(exist_ok=True)
            (project_path / "tests").mkdir(exist_ok=True)
            (project_path / "docs").mkdir(exist_ok=True)
            
            # Create basic Python files
            with open(project_path / "src" / "__init__.py", 'w') as f:
                f.write("")
            
            with open(project_path / "requirements.txt", 'w') as f:
                f.write("# Add your dependencies here\n")
                
            with open(project_path / "README.md", 'w') as f:
                f.write(f"""# {project_path.name}

Python project created with AIWhisperer.

## Setup

```bash
pip install -r requirements.txt
```

## Usage

```python
# Add usage examples here
```
""")
                
        elif template == "web":
            # Web project template
            (project_path / "src").mkdir(exist_ok=True)
            (project_path / "public").mkdir(exist_ok=True)
            
            # Create basic HTML structure
            with open(project_path / "public" / "index.html", 'w') as f:
                f.write(f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{project_path.name}</title>
    <link rel="stylesheet" href="../src/style.css">
</head>
<body>
    <h1>Welcome to {project_path.name}</h1>
    <p>Web project created with AIWhisperer.</p>
    <script src="../src/script.js"></script>
</body>
</html>""")
                
            with open(project_path / "src" / "style.css", 'w') as f:
                f.write("""/* Add your styles here */
body {
    font-family: Arial, sans-serif;
    margin: 0;
    padding: 20px;
    background-color: #f5f5f5;
}

h1 {
    color: #333;
}
""")
                
            with open(project_path / "src" / "script.js", 'w') as f:
                f.write("""// Add your JavaScript here
console.log('Project loaded successfully!');
""")
                
            with open(project_path / "README.md", 'w') as f:
                f.write(f"""# {project_path.name}

Web project created with AIWhisperer.

## Structure

- `public/` - Static assets and HTML files  
- `src/` - Source code (CSS, JS)

## Development

Open `public/index.html` in your browser to view the project.
""")
    
    def _init_git_repository(self, project_path: Path):
        """Initialize Git repository in project directory."""
        try:
            import subprocess
            result = subprocess.run(['git', 'init'], cwd=project_path, capture_output=True, text=True)
            if result.returncode != 0:
                logger.warning(f"Failed to initialize Git repository: {result.stderr}")
                return False
                
            # Create .gitignore
            gitignore_content = """# AIWhisperer
.WHISPER/sessions/
.WHISPER/artifacts/tmp/

# Common ignores
.env
.env.local
*.log
.DS_Store
Thumbs.db

# IDE
.vscode/
.idea/
*.swp
*.swo

# Language specific
__pycache__/
*.pyc
*.pyo
*.pyd
.Python
node_modules/
npm-debug.log*
yarn-debug.log*
yarn-error.log*
"""
            with open(project_path / ".gitignore", 'w') as f:
                f.write(gitignore_content)
                
            logger.info(f"Initialized Git repository at {project_path}")
            return True
            
        except Exception as e:
            logger.warning(f"Failed to initialize Git repository: {e}")
            return False
    
    def _update_recent_projects(self, project: Project):
        """Update recent projects list."""
        # Remove if already in list
        self.history.recent_projects = [
            p for p in self.history.recent_projects 
            if p.id != project.id
        ]
        
        # Add to front
        summary = ProjectSummary(
            id=project.id,
            name=project.name,
            path=project.path,
            last_accessed_at=project.last_accessed_at
        )
        self.history.recent_projects.insert(0, summary)
        
        # Trim to max size
        if len(self.history.recent_projects) > self.history.max_recent_projects:
            self.history.recent_projects = self.history.recent_projects[:self.history.max_recent_projects]
        
        self._save_history()
    
    def _initialize_path_manager(self, project: Project):
        """Initialize PathManager with project configuration."""
        path_manager = PathManager.get_instance()
        
        # Build project.json compatible dict
        project_json = {
            "path": project.path,
            "output_path": project.output_path if project.output_path else None,
            "workspace_path": project.path,  # workspace is same as project path
            "prompt_path": project.path,     # prompt path defaults to project path
            "whisper_path": project.whisper_path  # add whisper path to PathManager
        }
        
        # Initialize PathManager with project settings
        path_manager.initialize_with_project_json(project_json)
        
        logger.info(f"Initialized PathManager for project: {project.name}")
        logger.info(f"  - Workspace: {path_manager.workspace_path}")
        logger.info(f"  - Output: {path_manager.output_path}")
        logger.info(f"  - Whisper: {path_manager.whisper_path}")
    
    def create_project(self, project_data: ProjectCreate) -> Project:
        """Create a new project (legacy method - connects to existing directory)."""
        project_path = Path(project_data.path)
        
        # Validate path
        if not project_path.exists():
            raise ValueError(f"Project path does not exist: {project_path}")
        
        if not project_path.is_dir():
            raise ValueError(f"Project path is not a directory: {project_path}")
        
        # Handle custom whisper path
        custom_whisper_base = None
        if project_data.custom_whisper_path:
            custom_whisper_base = Path(project_data.custom_whisper_path)
            if not custom_whisper_base.exists():
                raise ValueError(f"Custom whisper path does not exist: {custom_whisper_base}")
            if not custom_whisper_base.is_dir():
                raise ValueError(f"Custom whisper path is not a directory: {custom_whisper_base}")
        
        # Check if .WHISPER already exists
        if custom_whisper_base:
            whisper_path = custom_whisper_base / f".WHISPER_{project_path.name}"
        else:
            whisper_path = project_path / ".WHISPER"
            
        if whisper_path.exists():
            if custom_whisper_base:
                raise ValueError(f"Project already exists at custom whisper location: {whisper_path}. Use join_project() instead.")
            else:
                raise ValueError(f"Project already exists at {project_path}. Use join_project() instead.")
        
        # Create .WHISPER structure
        whisper_path = self._create_whisper_structure(project_path, custom_whisper_base)
        
        # Create project
        project = Project(
            name=project_data.name,
            path=str(project_path),
            whisper_path=str(whisper_path),
            output_path=project_data.output_path if project_data.output_path else None,
            description=project_data.description
        )
        
        # Save project metadata
        project_file = whisper_path / "project.json"
        with open(project_file, 'w') as f:
            json.dump(project.model_dump(), f, indent=2, default=str)
        
        # Add to projects
        self.projects[project.id] = project
        self._save_projects()
        
        # Update recent projects
        self._update_recent_projects(project)
        
        logger.info(f"Created project: {project.name} at {project.path}")
        
        return project
    
    def join_project(self, join_data: ProjectJoin) -> Project:
        """Join an existing project with .WHISPER folder."""
        project_path = Path(join_data.path)
        
        # Validate path
        if not project_path.exists():
            raise ValueError(f"Project path does not exist: {project_path}")
        
        if not project_path.is_dir():
            raise ValueError(f"Project path is not a directory: {project_path}")
        
        # Check if .WHISPER exists
        whisper_path = project_path / ".WHISPER"
        if not whisper_path.exists():
            raise ValueError(f"No .WHISPER folder found at {project_path}. Use create_project() instead.")
        
        # Load existing project metadata
        project_file = whisper_path / "project.json"
        if not project_file.exists():
            raise ValueError(f"No project.json found in .WHISPER folder at {whisper_path}")
        
        try:
            with open(project_file, 'r') as f:
                project_data = json.load(f)
                
            # Create project from existing data
            project = Project(**project_data)
            
            # Ensure paths are up to date (in case project was moved)
            project.path = str(project_path)
            project.whisper_path = str(whisper_path)
            
            # Update last accessed time
            project.last_accessed_at = datetime.now(timezone.utc)
            
        except Exception as e:
            raise ValueError(f"Failed to load existing project: {e}")
        
        # Check if project already exists in our registry (by path)
        existing_project = None
        for pid, proj in self.projects.items():
            if proj.path == str(project_path):
                existing_project = proj
                break
        
        if existing_project:
            # Update existing project with loaded data
            existing_project.name = project.name
            existing_project.description = project.description
            existing_project.settings = project.settings
            existing_project.last_accessed_at = project.last_accessed_at
            project = existing_project
        else:
            # Add new project to registry
            self.projects[project.id] = project
        
        # Save updated registry
        self._save_projects()
        
        # Update project.json with any changes
        with open(project_file, 'w') as f:
            json.dump(project.model_dump(), f, indent=2, default=str)
        
        # Update recent projects
        self._update_recent_projects(project)
        
        logger.info(f"Joined existing project: {project.name} at {project.path}")
        
        return project
    
    def create_new_project(self, project_data: ProjectCreateNew) -> Project:
        """Create a brand new project with directory structure."""
        
        # Check if using existing workspace or creating new project folder
        if project_data.workspace_path:
            # Use existing workspace directory
            workspace_path = Path(project_data.workspace_path)
            
            # Validate workspace directory exists
            if not workspace_path.exists():
                raise ValueError(f"Workspace directory does not exist: {workspace_path}")
            
            if not workspace_path.is_dir():
                raise ValueError(f"Workspace path is not a directory: {workspace_path}")
            
            # Check if we have read access to workspace directory
            if not os.access(workspace_path, os.R_OK):
                raise ValueError(f"No read permission to workspace directory: {workspace_path}")
            
            # Set project path to the workspace (where code lives)
            project_path = workspace_path
                
        else:
            # Create new project folder
            project_path = Path(project_data.path) / project_data.name
            parent_path = Path(project_data.path)
            
            # Validate parent directory
            if not parent_path.exists():
                raise ValueError(f"Parent directory does not exist: {parent_path}")
            
            if not parent_path.is_dir():
                raise ValueError(f"Parent path is not a directory: {parent_path}")
            
            # Check if we have write permission to parent directory
            if not os.access(parent_path, os.W_OK):
                raise ValueError(f"No write permission to parent directory: {parent_path}")
            
            # Check if project directory already exists
            if project_path.exists():
                raise ValueError(f"Directory already exists at {project_path}")
            
            # Create project directory
            try:
                project_path.mkdir(parents=True, exist_ok=False)
            except PermissionError as e:
                raise ValueError(f"Permission denied creating project directory: {project_path}") from e
            except OSError as e:
                raise ValueError(f"Failed to create project directory: {project_path} - {e}") from e
            
            # Set up project template (only for new projects, not existing workspaces)
            self._setup_project_template(project_path, project_data.template)
            
            # Initialize Git if requested (only for new projects)
            if project_data.git_init:
                self._init_git_repository(project_path)
        
        # Determine whisper location
        if project_data.workspace_path:
            # For existing workspace, create .WHISPER at parent/name location
            whisper_base_path = Path(project_data.path) / project_data.name
            # Create the whisper base directory if it doesn't exist
            whisper_base_path.mkdir(parents=True, exist_ok=True)
        else:
            # For new project, .WHISPER goes with the project
            whisper_base_path = project_path
        
        # Handle custom whisper path
        custom_whisper_base = None
        if project_data.custom_whisper_path:
            custom_whisper_base = Path(project_data.custom_whisper_path)
            if not custom_whisper_base.exists():
                raise ValueError(f"Custom whisper path does not exist: {custom_whisper_base}")
            if not custom_whisper_base.is_dir():
                raise ValueError(f"Custom whisper path is not a directory: {custom_whisper_base}")
        
        # Create .WHISPER structure
        whisper_path = self._create_whisper_structure(whisper_base_path, custom_whisper_base)
        
        # Create project
        project = Project(
            name=project_data.name,
            path=str(project_path),  # This is the workspace (code) path
            whisper_path=str(whisper_path),
            description=project_data.description
        )
        
        # Save project metadata
        project_file = whisper_path / "project.json"
        with open(project_file, 'w') as f:
            json.dump(project.model_dump(), f, indent=2, default=str)
        
        # Add to projects
        self.projects[project.id] = project
        self._save_projects()
        
        # Update recent projects
        self._update_recent_projects(project)
        
        logger.info(f"Created new project: {project.name} at {project.path}")
        
        return project
    
    def get_project(self, project_id: str) -> Optional[Project]:
        """Get a project by ID."""
        return self.projects.get(project_id)
    
    def list_projects(self) -> List[Project]:
        """List all projects."""
        return list(self.projects.values())
    
    def get_recent_projects(self) -> List[ProjectSummary]:
        """Get recent projects."""
        # Update list to remove any deleted projects
        valid_summaries = []
        for summary in self.history.recent_projects:
            if summary.id in self.projects:
                valid_summaries.append(summary)
        
        self.history.recent_projects = valid_summaries
        return valid_summaries
    
    def update_project(self, project_id: str, update_data: ProjectUpdate) -> Optional[Project]:
        """Update a project."""
        project = self.projects.get(project_id)
        if not project:
            return None
        
        # Update fields
        if update_data.name is not None:
            project.name = update_data.name
        
        if update_data.output_path is not None:
            project.output_path = update_data.output_path
        
        if update_data.description is not None:
            project.description = update_data.description
        
        if update_data.settings is not None:
            project.settings = update_data.settings
        
        # Save changes
        self._save_projects()
        
        # Update project.json in .WHISPER
        project_file = Path(project.whisper_path) / "project.json"
        with open(project_file, 'w') as f:
            json.dump(project.model_dump(), f, indent=2, default=str)
        
        logger.info(f"Updated project: {project.name}")
        
        return project
    
    def delete_project(self, project_id: str, delete_files: bool = False) -> bool:
        """Delete a project."""
        project = self.projects.get(project_id)
        if not project:
            return False
        
        # Delete .WHISPER folder if requested
        if delete_files:
            whisper_path = Path(project.whisper_path)
            if whisper_path.exists():
                shutil.rmtree(whisper_path)
                logger.info(f"Deleted .WHISPER folder: {whisper_path}")
        
        # Remove from projects
        del self.projects[project_id]
        self._save_projects()
        
        # Remove from recent projects
        self.history.recent_projects = [
            p for p in self.history.recent_projects 
            if p.id != project_id
        ]
        
        # Clear last active if it was this project
        if self.history.last_active_project_id == project_id:
            self.history.last_active_project_id = None
        
        self._save_history()
        
        # Clear active project if it was this one
        if self.active_project and self.active_project.id == project_id:
            self.active_project = None
        
        logger.info(f"Deleted project: {project.name}")
        
        return True
    
    def activate_project(self, project_id: str) -> Optional[Project]:
        """Activate a project."""
        project = self.projects.get(project_id)
        if not project:
            return None
        
        # Update last accessed time
        project.last_accessed_at = datetime.now(timezone.utc)
        self._save_projects()
        
        # Set as active
        self.active_project = project
        
        # Update history
        self.history.last_active_project_id = project_id
        self._update_recent_projects(project)
        
        # Initialize PathManager with project paths
        self._initialize_path_manager(project)
        
        logger.info(f"Activated project: {project.name}")
        
        return project
    
    def get_active_project(self) -> Optional[Project]:
        """Get the currently active project."""
        return self.active_project
    
    def get_last_project(self) -> Optional[Project]:
        """Get the last active project."""
        if self.history.last_active_project_id:
            return self.get_project(self.history.last_active_project_id)
        return None
    
    def get_ui_settings(self) -> UISettings:
        """Get UI settings."""
        return self.ui_settings
    
    def update_ui_settings(self, settings: UISettings) -> UISettings:
        """Update UI settings."""
        self.ui_settings = settings
        self._save_ui_settings()
        return self.ui_settings
    
    @contextmanager
    def project_context(self, project_id: str):
        """Context manager for working within a project."""
        previous_project = self.active_project
        
        try:
            # Activate project
            project = self.activate_project(project_id)
            if not project:
                raise ValueError(f"Project not found: {project_id}")
            
            yield project
            
        finally:
            # Restore previous project
            if previous_project:
                self.active_project = previous_project
                # Re-initialize PathManager with previous project
                self._initialize_path_manager(previous_project)