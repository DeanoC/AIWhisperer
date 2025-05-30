# Path Management System Design

## 1. Introduction

This document outlines the design for a consistent path management system for the project. The goal is to ensure all paths are consistent, intuitive, and managed centrally. This system will be based on four core directories and a global singleton object for accessing and resolving these paths.

## 2. Core Directories

The path management system revolves around four fundamental directory types:

* **App Path (`app_path`):**
  * **Description:** This is the root directory of the application code. It is the parent of the `src` folder.
  * **Template Variable:** `{app_path}`
* **Project Path (`project_path`):**
  * **Description:** This directory serves as the primary location for project-specific input files.
    * For initial plans, it's where the requirements markdown is located.
    * For overview plans, it's where the initial plan JSON is located.
    * For runs, it's where the overview and subtasks JSON files are located.
  * **Template Variable:** `{project_path}`
* **Output Path (`output_path`):**
  * **Description:** This directory is designated for all output generated by the project.
  * **Default:** `{project_path}/output` (i.e., a subdirectory named "output" within the project path).
  * **Template Variable:** `{output_path}`
* **Workspace Path (`workspace_path`):**
  * **Description:** This directory is used for all other files and serves as a "secure" space. All AI tool operations are relative to this path.
  * **Default:** The project path (`project_path`), but can be configured to a different location.
  * **Template Variable:** `{workspace_path}`

## 3. Global Path Singleton (`PathManager`)

A global singleton, tentatively named `PathManager`, will be responsible for storing, managing, and providing access to these core paths.

### 3.1. Conceptual Structure

```mermaid
classDiagram
    class PathManager {
        - _app_path: string
        - _project_path: string
        - _output_path: string
        - _workspace_path: string
        + {static} get_instance(): PathManager
        + app_path: string {get}
        + project_path: string {get}
        + output_path: string {get}
        + workspace_path: string {get}
        + initialize(config_values: dict, cli_args: dict) void
        + resolve_path(template_string: string): string
    }
```

### 3.2. Responsibilities

* Store the resolved absolute paths for the four core directories.
* Provide a mechanism to access these core paths.
* Offer a utility function to resolve templated path strings into absolute paths.
* Handle initialization of paths from configuration files and CLI arguments.

### 3.3. Storage

The `PathManager` will internally store the four core paths as private attributes, likely after resolving them to absolute paths upon initialization.

* `_app_path: str`
* `_project_path: str`
* `_output_path: str`
* `_workspace_path: str`

### 3.4. Initialization

The `PathManager` singleton will be initialized early in the application lifecycle, potentially as part of a `load_config` process. Access to the singleton would typically be through a static `get_instance()` method which ensures lazy initialization if not already done.
The initialization process (`initialize` method, possibly called by `get_instance` on first access if paths aren't set) will follow this order of precedence:

1. **Default Values:** Hardcoded sensible defaults (e.g., `output_path` defaulting to `project_path/output`).
2. **Configuration File:** Values loaded from a project configuration file can override the defaults.
3. **CLI Arguments:** Paths specified via Command Line Interface arguments will override both defaults and configuration file settings.

The singleton instance should ensure it's initialized only once.

### 3.5. Accessing Paths

The core paths will be accessible via read-only properties on the `PathManager` instance:

* `PathManager.instance.app_path: str`
* `PathManager.instance.project_path: str`
* `PathManager.instance.output_path: str`
* `PathManager.instance.workspace_path: str`

## 4. Templated Path Expansion

The `PathManager` will provide a function to resolve paths containing template variables.

### 4.1. Template Variables

The following template variables will be supported:

* `{app_path}`: Resolves to the absolute application code path.
* `{project_path}`: Resolves to the absolute project input path.
* `{output_path}`: Resolves to the absolute output path.
* `{workspace_path}`: Resolves to the absolute workspace path.

### 4.2. Expansion Function

A public method, `PathManager.instance.resolve_path(template_string: str) -> str`, will take a string (which may or may not contain template variables) and return a string with all recognized template variables replaced by their corresponding absolute paths.

**Example Usage (Conceptual Python):**

```python
# path_manager_instance = PathManager.get_instance()

# Example:
# path_manager_instance.project_path might be '/path/to/my/project'
# path_manager_instance.output_path might be '/path/to/my/project/output'

requirements_file_template = "{project_path}/requirements.md"
resolved_requirements_file = path_manager_instance.resolve_path(requirements_file_template)
# resolved_requirements_file would be "/path/to/my/project/requirements.md"

log_file_template = "{output_path}/logs/app.log"
resolved_log_file = path_manager_instance.resolve_path(log_file_template)
# resolved_log_file would be "/path/to/my/project/output/logs/app.log"
```

## 5. Documentation Requirement

As per the RFC, a document explaining the four core directories must exist within the project. The "Core Directories" section (Section 2) of this document aims to fulfill this requirement.

## 6. Future Considerations

* **Path Validation:** Add validation to ensure paths exist or are creatable during initialization or when set.
* **Platform Agnosticism:** Ensure path manipulation (joining, resolving) is done in a platform-agnostic way (e.g., using `pathlib` in Python).
* **Error Handling:** Define behavior for unresolvable templates or invalid path configurations.
