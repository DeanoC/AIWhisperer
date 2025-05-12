# AI Tool Management Design for AIWhisperer

## 1. Introduction

This document outlines the design for managing AI-usable tools within the AIWhisperer project. It details the mechanisms for discovering, registering, listing, filtering, and selecting tools, building upon the `AITool` interface defined in [`docs/tool_interface_design.md`](docs/tool_interface_design.md). The primary goal is to create a robust, efficient, and flexible system for managing a potentially large and diverse set of AI tools.

The key components of this design are:

* A `ToolRegistry` class responsible for central management.
* Defined mechanisms for tool discovery and registration.
* An API for accessing and interacting with the registered tools.

## 2. Tool Discovery and Registration

A flexible discovery and registration mechanism is crucial for allowing easy addition and management of tools.

### 2.1. Approach: Plugin-Based System

AIWhisperer will primarily use a plugin-based system for tool discovery.

* **Primary Method: Python Entry Points**
  * Tools will be packaged as Python libraries and declare themselves via `setuptools` entry points, specifically under a group like `aiwhisperer.tools`.
  * Example `pyproject.toml` or `setup.cfg` entry:

        ```toml
        # pyproject.toml
        [project.entry-points."aiwhisperer.tools"]
        my_custom_tool = "my_tool_package.module:MyCustomToolClass"
        another_tool = "another_package.tools:AnotherTool"
        ```

  * This method is highly recommended as it integrates well with Python's packaging ecosystem, allows for clear dependency management, and supports tools from various sources (internal or third-party).

* **Secondary Method (Optional): Directory Scanning**
  * As a fallback or for simpler local development setups, the system could optionally scan a designated directory (e.g., `AIWHISPERER_PLUGINS_DIR` environment variable or a configured path) for Python modules (`.py` files).
  * Modules found in this directory would be imported, and any classes inheriting from `AITool` would be automatically discovered.
  * This method is simpler for ad-hoc tool additions but less robust for managing dependencies and distribution.

### 2.2. Registration Process

1. **Discovery:** At application startup or when explicitly triggered, the `ToolRegistry` will use the configured discovery method(s) (entry points first, then directory scanning if enabled).
2. **Loading:** For each discovered tool (entry point or module), the corresponding `AITool` class will be imported.
3. **Instantiation:** An instance of each valid `AITool` subclass will be created.
4. **Validation:** The `name` property of the tool instance will be checked for uniqueness.
5. **Registration:** If the tool name is unique, the instance is stored in the `ToolRegistry`.
    * **Duplicate Handling:** If a tool with the same `name` is already registered, a warning will be logged, and the duplicate tool will be skipped. The first one discovered/loaded takes precedence.

## 3. `ToolRegistry` Class

The `ToolRegistry` is the central component for managing AI tools. It will likely be implemented as a singleton or an easily accessible global instance to ensure all parts of the system interact with the same set of tools.

### 3.1. Purpose

* Orchestrates the discovery and registration of `AITool` implementations.
* Provides a centralized point of access for retrieving tool information and instances.
* Facilitates the compilation of tool definitions for AI models.

### 3.2. Core Data Structure

The primary internal storage will be a dictionary mapping unique tool names (strings) to their instantiated `AITool` objects:

```python
# Conceptual representation
_registered_tools: Dict[str, AITool] = {}
```

### 3.3. Responsibilities and Methods (Conceptual)

```python
class ToolRegistry:
    _instance = None
    _registered_tools: Dict[str, AITool]

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ToolRegistry, cls).__new__(cls)
            cls._instance._registered_tools = {}
            cls._instance._load_tools() # Load tools on first instantiation
        return cls._instance

    def _load_tools(self):
        """
        Private method to discover and register tools.
        Iterates through entry points and/or plugin directories.
        """
        # 1. Discover via entry points (importlib.metadata)
        # 2. Discover via directory scanning (if enabled)
        # For each discovered tool class:
        #   try:
        #       tool_instance = ToolClass()
        #       self.register_tool(tool_instance)
        #   except Exception as e:
        #       log.warning(f"Failed to load tool {ToolClass}: {e}")
        pass

    def register_tool(self, tool: AITool):
        """Registers a single tool instance."""
        if tool.name in self._registered_tools:
            log.warning(f"Tool '{tool.name}' already registered. Skipping duplicate.")
            return
        self._registered_tools[tool.name] = tool
        log.info(f"Tool '{tool.name}' registered successfully.")

    def get_tool_by_name(self, name: str) -> Optional[AITool]:
        """Retrieves a specific tool by its unique name."""
        return self._registered_tools.get(name)

    def get_all_tools(self) -> List[AITool]:
        """Returns a list of all registered AITool instances."""
        return list(self._registered_tools.values())

    def get_all_tool_definitions(self) -> List[Dict[str, Any]]:
        """
        Returns a list of Openrouter-compatible JSON definitions for all tools.
        """
        return [tool.get_openrouter_tool_definition() for tool in self.get_all_tools()]

    def get_all_ai_prompt_instructions(self) -> str:
        """
        Returns a consolidated string of AI prompt instructions for all tools.
        """
        return "\n\n".join([tool.get_ai_prompt_instructions() for tool in self.get_all_tools()])

    def get_filtered_tools(self, criteria: Dict[str, Any]) -> List[AITool]:
        """
        Retrieves a list of tools matching the given criteria.
        Example criteria: {"tags": ["file_io"], "category": "Utility"}
        """
        # Implementation would iterate through tools and apply filters.
        # Requires AITool to have 'tags' and 'category' properties (see section 10).
        filtered_list = []
        for tool in self.get_all_tools():
            match = True
            if "tags" in criteria:
                # Assumes tool.tags is List[str] and criteria["tags"] is List[str]
                # Check if all criteria tags are present in tool.tags
                if not all(tag in getattr(tool, 'tags', []) for tag in criteria["tags"]):
                    match = False
            if "category" in criteria:
                # Assumes tool.category is str
                if getattr(tool, 'category', None) != criteria["category"]:
                    match = False
            # Add more filterable attributes as needed (e.g., name_pattern)
            if "name_pattern" in criteria:
                import re
                if not re.match(criteria["name_pattern"], tool.name):
                    match = False

            if match:
                filtered_list.append(tool)
        return filtered_list

    def reload_tools(self):
        """Clears existing tools and re-runs the discovery and registration process."""
        self._registered_tools.clear()
        self._load_tools()
```

## 4. Retrieving All Available Tools

The system needs a way to list all tools that have been successfully registered.

* **Method:** `ToolRegistry.get_all_tools() -> List[AITool]`
  * This method returns a list containing all registered `AITool` instances. This is useful for internal system operations or for UIs that need to display tool details.

* **For AI Consumption:** `ToolRegistry.get_all_tool_definitions() -> List[Dict[str, Any]]`
  * This method iterates through all registered tools and calls `get_openrouter_tool_definition()` on each.
  * It returns a list of dictionaries, where each dictionary is the Openrouter-compatible JSON schema for a tool. This list can be directly passed to an AI model.

* **For AI Prompting:** `ToolRegistry.get_all_ai_prompt_instructions() -> str`
  * This method iterates through all registered tools and calls `get_ai_prompt_instructions()` on each.
  * It concatenates these instructions (e.g., separated by double newlines) into a single string. This aggregated text can be included in the system prompt for the AI.

## 5. Filtering Tools

To allow AI models or the system to select a relevant subset of tools, a filtering mechanism is necessary.

* **Method:** `ToolRegistry.get_filtered_tools(criteria: Dict[str, Any]) -> List[AITool]`
  * This method accepts a `criteria` dictionary.
  * The keys in the dictionary correspond to attributes of the `AITool` (or derived properties), and values are the desired values for those attributes.

* **Filtering Criteria Examples:**
  * `{"tags": ["file_system", "read"]}`: Find tools that have *all* specified tags.
  * `{"category": "Code Execution"}`: Find tools belonging to a specific category.
  * `{"name_pattern": "aws_s3_*"}`: Find tools whose names match a regex pattern.
  * `{"supports_streaming": True}`: (Hypothetical) Find tools with a specific capability flag.

* **Supporting `AITool` Properties for Filtering:**
    To enable effective filtering, the `AITool` interface (defined in [`docs/tool_interface_design.md`](docs/tool_interface_design.md)) should be extended with optional, standardized properties. See Section 10: "Proposed Modifications to `AITool` Interface".

* **Logic:** The `get_filtered_tools` method will iterate over all registered tools. For each tool, it checks if it matches all conditions specified in the `criteria` dictionary.
  * For list-based criteria like `tags`, the tool must possess all tags listed in the criteria.
  * For simple value criteria like `category`, an exact match is required.

## 6. Selecting a Specific Tool

The system must be able to retrieve a single, specific tool by its unique identifier.

* **Method:** `ToolRegistry.get_tool_by_name(name: str) -> Optional[AITool]`
  * The primary identifier for a tool is its `name` property (string).
  * This method performs a direct lookup in the `ToolRegistry`'s internal dictionary (`_registered_tools`).

* **Process:**
    1. The client (e.g., AI execution engine) requests a tool by its name.
    2. The `ToolRegistry` attempts to find the tool in its `_registered_tools` dictionary.
    3. If found, the `AITool` instance is returned.

* **Error Handling / Tool Not Found:**
  * If a tool with the specified `name` does not exist in the registry, the method will return `None`.
  * Alternatively, it could raise a custom `ToolNotFoundError` exception (e.g., `class ToolNotFoundError(KeyError): pass`). Returning `None` is often simpler for callers to handle with an `if tool_instance:` check. The choice depends on the desired error handling philosophy of the broader system. For this design, `Optional[AITool]` (returning `None` if not found) is preferred for its explicitness.

## 7. Data Structures Summary

* **`ToolRegistry` internal store:** `Dict[str, AITool]` (tool name to tool instance).
* **Listing all tools (instances):** `List[AITool]`.
* **Listing all tool definitions (for AI):** `List[Dict[str, Any]]` (list of Openrouter JSON schemas).
* **Filtering criteria:** `Dict[str, Any]` (e.g., `{"tags": ["io"], "category": "file"}`).

## 8. Efficiency and Flexibility

* **Efficiency:**
  * **Discovery/Registration:** This is typically a one-time operation at startup or when `reload_tools()` is called. While it involves I/O (for directory scanning) or metadata iteration, its cost is amortized.
  * **`get_tool_by_name`:** O(1) on average, due to dictionary lookup.
  * **`get_all_tools` / `get_all_tool_definitions`:** O(N) where N is the number of registered tools, as it involves iterating through the tools. This is generally acceptable as N is unlikely to be astronomically large for practical AI use cases.
  * **`get_filtered_tools`:** O(N*M) in the worst case, where N is the number of tools and M is the complexity of matching criteria per tool. With simple attribute checks, it's closer to O(N).

* **Flexibility:**
  * **Tool Addition:** The entry point system makes adding new tools straightforward (install a new package). Directory scanning offers a simpler alternative for local development.
  * **Filtering:** The dictionary-based criteria for filtering are extensible. New filterable attributes can be added to tools and supported by the registry without breaking existing functionality.
  * **`AITool` Interface:** The design relies on the `AITool` ABC, ensuring all tools conform to a standard contract.

## 9. Diagrams (Mermaid)

### 9.1. Tool Discovery and Registration Flow

```mermaid
graph TD
    A[Application Starts / Reload Triggered] --> B(ToolRegistry Initialization/Access);
    B --> C{Discovery Method};
    C -- Python Entry Points --> D[Scan `importlib.metadata` for 'aiwhisperer.tools' group];
    D --> F[For each entry point: Load Module & Get Class];
    C -- Directory Scan (Optional) --> E[Scan designated 'plugins' directory for *.py files];
    E --> F_Scan[For each file: Import Module & Find AITool subclasses];
    F --> G[Instantiate AITool subclass];
    F_Scan --> G;
    G --> H{Valid AITool Instance?};
    H -- Yes --> I[ToolRegistry.register_tool(instance)];
    I --> J{Name Unique?};
    J -- Yes --> K[Store in _registered_tools];
    J -- No --> L[Log Warning, Skip];
    H -- No --> M[Log Error, Skip];
    K --> N[Tool Available];
    L --> N;
    M --> N;
    N --> O[ToolRegistry Ready];
end
```

### 9.2. Tool Retrieval and Filtering Interactions

```mermaid
graph TD
    subgraph ClientSystem as CS
        Action_RequestAll[Request All Tools]
        Action_RequestFiltered[Request Filtered Tools (with criteria)]
        Action_RequestSpecific[Request Specific Tool (by name)]
    end

    subgraph ToolRegistry as TR
        TR_Store[(Internal Tool Store: Dict[name, AITool])]
        TR_Method_GetAll[get_all_tools()]
        TR_Method_GetFiltered[get_filtered_tools(criteria)]
        TR_Method_GetByName[get_tool_by_name(name)]
        TR_Method_GetAllDefs[get_all_tool_definitions()]
        TR_Method_GetAllPrompts[get_all_ai_prompt_instructions()]
    end

    CS -- Calls --> TR

    Action_RequestAll --> TR_Method_GetAll
    Action_RequestFiltered --> TR_Method_GetFiltered
    Action_RequestSpecific --> TR_Method_GetByName
    Action_RequestAll --> TR_Method_GetAllDefs  // Example: AI needs all definitions
    Action_RequestAll --> TR_Method_GetAllPrompts // Example: System prompt needs all instructions


    TR_Method_GetAll --> TR_Store
    TR_Method_GetFiltered --> TR_Store
    TR_Method_GetByName --> TR_Store
    TR_Method_GetAllDefs --> TR_Store
    TR_Method_GetAllPrompts --> TR_Store

    TR_Store -- Returns Data --> TR_Method_GetAll
    TR_Store -- Returns Filtered Data --> TR_Method_GetFiltered
    TR_Store -- Returns Single Item/None --> TR_Method_GetByName
    TR_Store -- Returns Definitions --> TR_Method_GetAllDefs
    TR_Store -- Returns Instructions --> TR_Method_GetAllPrompts

    TR_Method_GetAll --> CS_ResultList[List of AITool Instances]
    TR_Method_GetFiltered --> CS_ResultList
    TR_Method_GetByName --> CS_ResultSingle[AITool Instance or None]
    TR_Method_GetAllDefs --> CS_ResultDefs[List of Tool Definitions (JSON Schema)]
    TR_Method_GetAllPrompts --> CS_ResultPrompts[Aggregated Prompt Instructions (str)]

    CS_ResultList --> ClientSystem
    CS_ResultSingle --> ClientSystem
    CS_ResultDefs --> ClientSystem
    CS_ResultPrompts --> ClientSystem
end
```

## 10. Proposed Modifications to `AITool` Interface

To enhance the filtering capabilities described in Section 5, the following optional properties are proposed to be added to the `AITool` abstract base class (defined in [`docs/tool_interface_design.md`](docs/tool_interface_design.md)). Tools would implement these as needed.

```python
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional # Added Optional

class AITool(ABC):
    # ... existing properties (name, description, parameters_schema) ...

    @property
    def name(self) -> str: # abstractmethod
        pass

    @property
    def description(self) -> str: # abstractmethod
        pass

    @property
    def parameters_schema(self) -> Dict[str, Any]: # abstractmethod
        pass

    # --- PROPOSED NEW OPTIONAL PROPERTIES FOR FILTERING ---
    @property
    def category(self) -> Optional[str]:
        """
        A broad category for the tool (e.g., "File System", "Code Execution", "Data Analysis", "Communication").
        Returns None if not categorized.
        """
        return None # Default implementation

    @property
    def tags(self) -> List[str]:
        """
        A list of keywords or tags describing the tool's capabilities or domain.
        e.g., ["file_io", "read", "text"], ["python", "scripting"]
        Returns an empty list if no tags are applicable.
        """
        return [] # Default implementation
    # --- END PROPOSED NEW PROPERTIES ---

    @abstractmethod
    def get_openrouter_tool_definition(self) -> Dict[str, Any]:
        # ... existing implementation or keep abstract ...
        # Base class can provide a default:
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.parameters_schema
            }
        }


    @abstractmethod
    def get_ai_prompt_instructions(self) -> str:
        pass

    @abstractmethod
    async def execute(self, **kwargs: Any) -> Any:
        pass
```

Adding these properties with default implementations (`None` or `[]`) ensures backward compatibility for existing tools. New tools can override them to provide metadata for richer filtering. The `ToolRegistry.get_filtered_tools` method would then leverage `getattr(tool, 'tags', [])` to safely access these.

## 11. Conclusion

This tool management design provides a comprehensive framework for discovering, registering, and accessing AI tools within AIWhisperer. The `ToolRegistry`, combined with a plugin-based discovery system and flexible filtering, offers scalability and ease of use for both developers integrating tools and AI models utilizing them. The proposed enhancements to the `AITool` interface will further improve the system's ability to manage and select appropriate tools for various tasks.
