# AIWhisperer Code Map

## Summary
- Total Python Files: 139
- Total Classes: 228
- Total Functions: 79
- Total Lines: 32732

## Module Details

### ai_whisperer

#### `ai_whisperer/__init__.py`
*AI Whisperer package initialization.*


**Stats:** 10 lines

---

#### `ai_whisperer/__main__.py`

**Stats:** 4 lines

---

#### `ai_whisperer/cli.py`

**Functions:**
- `cli(args)`
  - Main entry point for the AI Whisperer CLI application.
- `main()`
  - Standard Python main function entry point.

**Stats:** 102 lines

---

#### `ai_whisperer/cli_commands.py`
**Classes:**
- `BaseCliCommand`: 2 methods
  - Base class for all CLI commands.
- `BatchModeCliCommand`: 2 methods

**Stats:** 266 lines

---

#### `ai_whisperer/cli_commands_batch_mode.py`
**Classes:**
- `BatchModeCliCommand`: 2 methods

**Stats:** 43 lines

---

#### `ai_whisperer/config.py`

**Functions:**
- `load_config(config_path, cli_args)`
  - Loads configuration from a YAML file, validates required keys, handles API key precedence,

**Stats:** 204 lines

---

#### `ai_whisperer/context_management.py`
**Classes:**
- `ContextManager`: 4 methods
  - Manages the conversation history for AI interactions.

**Stats:** 72 lines

---

#### `ai_whisperer/exceptions.py`
*Custom exception types for the AI Whisperer application.*

**Classes:**
- `AIWhispererError`: 0 methods
  - Base class for all application-specific errors.
- `ConfigError`: 0 methods
  - Exception raised for errors in the configuration file (loading, parsing, validation).
- `OpenRouterAIServiceError`: 1 methods
  - Base class for errors during interaction with the OpenRouter API.
- `OpenRouterAuthError`: 0 methods
  - Raised for authentication errors (HTTP 401) with the OpenRouter API.
- `OpenRouterRateLimitError`: 0 methods
  - Raised for rate limit errors (HTTP 429) with the OpenRouter API.
- `OpenRouterConnectionError`: 1 methods
  - Raised for network connection errors when trying to reach the OpenRouter API.
- `ProcessingError`: 0 methods
  - Exception raised for errors during file processing (reading MD, writing YAML, etc.).
- `OrchestratorError`: 0 methods
  - Base class for errors specific to the Orchestrator.
- `PlanNotLoadedError`: 0 methods
  - Exception raised when a plan is expected but has not been loaded.
- `HashMismatchError`: 1 methods
  - Error raised when input hashes in the API response do not match calculated hashes.
- `YAMLValidationError`: 1 methods
  - Custom exception for YAML validation errors.
- `PromptError`: 0 methods
  - Errors related to loading or processing prompt files.
- `OrchestrationError`: 0 methods
  - Exception raised for errors during the orchestration process.
- `TaskExecutionError`: 1 methods
  - Exception raised for errors during the execution of a task.
- `ToolNotFound`: 0 methods
  - Exception raised when a requested tool is not found in the registry.
- `FileRestrictionError`: 0 methods
  - Exception raised when a file operation is restricted.
- `SubtaskGenerationError`: 0 methods
  - Exception raised for errors during the subtask generation process.
- `SchemaValidationError`: 0 methods
  - Exception raised when generated data fails schema validation.
- `PromptNotFoundError`: 0 methods
  - Exception raised when a prompt is not found in the resolution hierarchy.

**Stats:** 154 lines

---

#### `ai_whisperer/interactive_entry.py`
*Entry point for starting the interactive server from the CLI.*


**Functions:**
- `main()`
  - Start the interactive_server.main module as a subprocess.

**Stats:** 20 lines

---

#### `ai_whisperer/json_validator.py`

**Functions:**
- `set_schema_directory(directory)`
  - Sets the global schema directory.
- `get_schema_directory()`
  - Gets the current schema directory, defaulting to DEFAULT_SCHEMA_DIR.
- `load_schema(schema_path)`
  - Loads a JSON schema from the given path.
- `generate_uuid()`
  - Generates a new UUID string.
- `format_timestamp(dt_object)`
  - Converts a datetime object to an ISO 8601 string in UTC.
- `parse_timestamp(timestamp_str)`
  - Converts an ISO 8601 string to a datetime object.
- `validate_against_schema(data, schema_name)`
  - Validates a dictionary against a specified JSON schema.

**Stats:** 94 lines

---

#### `ai_whisperer/logging_custom.py`
**Classes:**
- `LogLevel`: 0 methods
- `ComponentType`: 0 methods
- `LogSource`: 0 methods
  - Identifies the source of log messages for multi-source debugging.
- `LogMessage`: 1 methods
- `EnhancedLogMessage`: 1 methods
  - Extended log message with debugging context for Debbie's multi-source logging.

**Functions:**
- `setup_logging(config_path, port)`
  - Configures the logging system.
- `setup_basic_logging(port)`
  - Sets up a basic console logger.
- `get_logger(name)`
  - Gets a logger instance by name.
- `get_server_logger()`
- `get_test_logger()`
- `log_event(log_message, logger_name)`
  - Logs a structured LogMessage using a specified logger.

**Stats:** 269 lines

---

#### `ai_whisperer/main.py`
*This file is deprecated. CLI entry point is now handled by ai_whisperer/cli.py (batch mode only).*


**Stats:** 8 lines

---

#### `ai_whisperer/model_capabilities.py`
*Model capabilities configuration for AIWhisperer.*


**Functions:**
- `get_model_capabilities(model_name)`
  - Get capabilities for a specific model.
- `supports_multi_tool(model_name)`
  - Check if a model supports multiple tool calls in one turn.
- `supports_structured_output(model_name)`
  - Check if a model supports structured output with JSON Schema validation.

**Stats:** 219 lines

---

#### `ai_whisperer/model_info_provider.py`
*This module contains the ModelInfoProvider class, responsible for querying*

**Classes:**
- `ModelInfoProvider`: 3 methods
  - Provides information about available AI models from OpenRouter.

**Stats:** 126 lines

---

#### `ai_whisperer/model_override.py`
*Model override utilities for testing different models without modifying config.yaml*

**Classes:**
- `ModelOverride`: 6 methods
  - Manages model overrides for testing and development

**Functions:**
- `get_model_from_config(config)`
  - Extract model name from configuration
- `apply_model_override_to_session(session_manager, model_name)`
  - Apply model override to an existing session manager

**Stats:** 228 lines

---

#### `ai_whisperer/path_management.py`
**Classes:**
- `PathManager`: 14 methods

**Stats:** 182 lines

---

#### `ai_whisperer/plan_parser.py`
**Classes:**
- `PlanParsingError`: 0 methods
  - Base class for errors during plan parsing.
- `PlanFileNotFoundError`: 0 methods
  - Raised when the main plan file is not found.
- `PlanInvalidJSONError`: 0 methods
  - Raised when the main plan file contains malformed JSON.
- `PlanValidationError`: 0 methods
  - Raised when the main plan JSON fails validation.
- `SubtaskFileNotFoundError`: 0 methods
  - Raised when a referenced subtask file is not found.
- `SubtaskInvalidJSONError`: 0 methods
  - Raised when a subtask file contains malformed JSON.
- `SubtaskValidationError`: 0 methods
  - Raised when a subtask JSON fails schema validation.
- `PlanNotLoadedError`: 0 methods
  - Raised when data access is attempted before a plan is loaded.
- `ParserPlan`: 8 methods
  - Parses and validates different types of JSON plan files and their referenced subtasks.

**Stats:** 243 lines

---

#### `ai_whisperer/processing.py`

**Functions:**
- `read_markdown(file_path)`
  - Reads the content of a Markdown file.
- `save_json(data, file_path)`
  - Saves a dictionary to a JSON file.
- `format_prompt(template, requirements, config_vars)`
  - Formats the prompt using a template string and provided variables.
- `process_response(response_text)`
  - Processes the raw text response from the API, expecting JSON format.

**Stats:** 128 lines

---

#### `ai_whisperer/prompt_system.py`
**Classes:**
- `Prompt`: 3 methods
  - Represents a loaded prompt with lazy content loading.
- `PromptConfiguration`: 4 methods
  - Manages the configuration for the prompt system.
- `PromptLoader`: 1 methods
  - Handles the actual reading of prompt content from a file.
- `PromptResolver`: 3 methods
  - Determines the correct file path for a requested prompt based on a hierarchy.
- `PromptSystem`: 9 methods
  - The central service for accessing and managing prompts.

**Stats:** 317 lines

---

#### `ai_whisperer/state_management.py`
**Classes:**
- `StateManagerEncoder`: 1 methods
  - Custom JSONEncoder to serialize ContextManager and skip unserializable objects.
- `StateManagerDecoder`: 2 methods
  - Custom JSONDecoder to deserialize ContextManager.
- `StateManager`: 13 methods
  - Manages the state of the execution for tasks and global context,

**Functions:**
- `save_state(state, file_path)`
  - Saves the state dictionary to a JSON file.
- `load_state(file_path)`
  - Loads the state from a JSON file.
- `update_task_status(state, task_id, status)`
  - Updates the status of a task in the state.
- `store_task_result(state, task_id, result)`
  - Stores the intermediate result of a task in the state.
- `get_task_result(state, task_id)`
  - Retrieves the intermediate result of a task from the state.
- `update_global_state(state, key, value)`
  - Updates a key-value pair in the global state.
- `get_global_state(state, key)`
  - Retrieves a value from the global state.

**Stats:** 323 lines

---

#### `ai_whisperer/task_selector.py`

**Functions:**
- `get_model_for_task(config, task_name)`
  - Get the model configuration for a specific task.
- `get_prompt_for_task(prompt_system, task_name)`
  - Get the prompt content for a specific task using the PromptSystem.

**Stats:** 79 lines

---

#### `ai_whisperer/user_message_level.py`
*Simple enum for message detail levels.*

**Classes:**
- `UserMessageLevel`: 0 methods

**Stats:** 9 lines

---

#### `ai_whisperer/utils.py`

**Functions:**
- `setup_logging(level)`
  - Sets up basic logging configuration to output to stderr.
- `calculate_sha256(file_path)`
  - Calculates the SHA-256 hash of a file's content.
- `save_json_to_file(data, output_path)`
  - Saves a dictionary as a JSON file with indentation.
- `_parse_gitignore(gitignore_path)`
  - Parses a .gitignore file.
- `_is_item_ignored(full_item_path, is_item_dir, item_name, active_ignore_rules)`
  - Checks if an item should be ignored based on the current set of active_ignore_rules.
- `_build_tree_recursive(current_dir_path, prefix_str, inherited_ignore_rules, output_lines_list)`
  - Internal recursive function to build the tree.
- `build_ascii_directory_tree(start_path, ignore)`
  - Builds an ASCII directory tree starting from the given directory,

**Stats:** 274 lines

---

#### `ai_whisperer/version.py`

**Stats:** 1 lines

---

#### `ai_whisperer/workspace_detection.py`
**Classes:**
- `WorkspaceNotFoundError`: 0 methods

**Functions:**
- `find_whisper_workspace(start_path)`
  - Search for a .WHISPER folder starting from start_path (or cwd) and walking up to the filesystem root.
- `load_project_json(workspace_path)`
  - Loads .WHISPER/project.json from the workspace and returns the parsed dict.

**Stats:** 50 lines

---

### ai_whisperer/agents

#### `ai_whisperer/agents/__init__.py`

**Stats:** 7 lines

---

#### `ai_whisperer/agents/agent.py`
**Classes:**
- `Agent`: 1 methods

**Stats:** 30 lines

---

#### `ai_whisperer/agents/agent_communication.py`
*Agent Communication Protocol for inter-agent messaging.*

**Classes:**
- `MessageType`: 0 methods
  - Types of messages agents can exchange.
- `AgentMessage`: 2 methods
  - Base message structure for agent communication.
- `ClarificationRequest`: 1 methods
  - Request for clarification on a specific aspect of a task.
- `ClarificationResponse`: 1 methods
  - Response to a clarification request.
- `PlanRefinementRequest`: 1 methods
  - Request to refine part of a plan based on decomposition insights.
- `PlanRefinementResponse`: 1 methods
  - Response to plan refinement request.

**Stats:** 156 lines

---

#### `ai_whisperer/agents/agent_e_exceptions.py`
*Exception classes for Agent E functionality.*

**Classes:**
- `AgentEException`: 0 methods
  - Base exception for Agent E errors.
- `InvalidPlanError`: 0 methods
  - Raised when a plan is invalid or missing required fields.
- `TaskDecompositionError`: 0 methods
  - Raised when task decomposition fails.
- `DependencyCycleError`: 0 methods
  - Raised when circular dependencies are detected in tasks.
- `ExternalAgentError`: 0 methods
  - Raised when external agent integration fails.
- `CommunicationError`: 0 methods
  - Raised when agent communication fails.

**Stats:** 33 lines

---

#### `ai_whisperer/agents/agent_e_handler.py`
*Agent E Handler - manages communication and task decomposition for external agent execution.*

**Classes:**
- `AgentEHandler`: 3 methods
  - Handles Agent E operations including decomposition and communication.

**Stats:** 278 lines

---

#### `ai_whisperer/agents/base_handler.py`
**Classes:**
- `BaseAgentHandler`: 2 methods
  - Base class for all agent handlers

**Stats:** 18 lines

---

#### `ai_whisperer/agents/config.py`
**Classes:**
- `AgentConfigError`: 0 methods
  - Raised when agent configuration is invalid.
- `AgentConfig`: 4 methods

**Stats:** 143 lines

---

#### `ai_whisperer/agents/context_manager.py`
**Classes:**
- `AgentContextManager`: 5 methods
  - Context manager specialized for agent-specific needs

**Stats:** 62 lines

---

#### `ai_whisperer/agents/continuation_strategy.py`
*Continuation strategy module for managing multi-step agent operations.*

**Classes:**
- `ContinuationProgress`: 1 methods
  - Tracks progress information for continuation operations.
- `ContinuationState`: 1 methods
  - Represents the continuation state from an AI response.
- `ContinuationStrategy`: 13 methods
  - Manages continuation detection and execution for agents.

**Stats:** 267 lines

---

#### `ai_whisperer/agents/debbie_tools.py`
*Tool registration for Debbie the Debugger.*


**Functions:**
- `get_debbie_tools()`
  - Get all of Debbie's debugging tools
- `register_debbie_tools()`
  - Register Debbie's tools with the tool registry
- `unregister_debbie_tools()`
  - Unregister Debbie's tools from the tool registry

**Stats:** 41 lines

---

#### `ai_whisperer/agents/decomposed_task.py`
*DecomposedTask data model for Agent E.*

**Classes:**
- `TaskStatus`: 0 methods
  - Status of a decomposed task.
- `DecomposedTask`: 10 methods
  - A task decomposed by Agent E for execution by external agents.

**Stats:** 135 lines

---

#### `ai_whisperer/agents/external_adapters.py`
*External Agent Adapters for Agent E.*

**Classes:**
- `ExternalAgentAdapter`: 4 methods
  - Base class for external agent adapters.
- `ClaudeCodeAdapter`: 4 methods
  - Adapter for Claude Code CLI (REPL mode).
- `RooCodeAdapter`: 4 methods
  - Adapter for RooCode in VS Code.
- `GitHubCopilotAdapter`: 4 methods
  - Adapter for GitHub Copilot in agent mode.
- `AdapterRegistry`: 9 methods
  - Registry for external agent adapters.

**Stats:** 628 lines

---

#### `ai_whisperer/agents/external_agent_result.py`
*External Agent Result class.*

**Classes:**
- `ExternalAgentResult`: 3 methods
  - Result from external agent execution.

**Stats:** 48 lines

---

#### `ai_whisperer/agents/factory.py`
**Classes:**
- `AgentFactory`: 7 methods
- `DummyAILoop`: 0 methods

**Stats:** 97 lines

---

#### `ai_whisperer/agents/mail_notification.py`
*Mail Notification System - Adds "You've got mail" notifications to agent responses.*

**Classes:**
- `MailNotificationMixin`: 3 methods
  - Mixin to add mail notification capabilities to agents.

**Functions:**
- `get_mail_notification(agent_name)`
  - Helper function to generate mail notification string.
- `inject_mail_notification(agent_method)`
  - Decorator to inject mail notifications into agent responses.

**Stats:** 123 lines

---

#### `ai_whisperer/agents/mailbox.py`
*Universal Mailbox System for Agent and User Communication.*

**Classes:**
- `MessagePriority`: 0 methods
  - Message priority levels.
- `MessageStatus`: 0 methods
  - Message delivery status.
- `Mail`: 2 methods
  - A mail message in the system.
- `MailboxSystem`: 10 methods
  - Centralized mailbox system for all agents and users.

**Functions:**
- `get_mailbox()`
  - Get the global mailbox system instance.
- `reset_mailbox()`
  - Reset the mailbox system (mainly for testing).

**Stats:** 297 lines

---

#### `ai_whisperer/agents/mailbox_tools.py`
*Tool registration for Mailbox system.*


**Functions:**
- `get_mailbox_tools()`
  - Get all mailbox communication tools
- `register_mailbox_tools()`
  - Register mailbox tools with the tool registry
- `is_mailbox_tool(tool_name)`
  - Check if a tool name is a mailbox tool

**Stats:** 38 lines

---

#### `ai_whisperer/agents/planner_handler.py`
**Classes:**
- `PlannerAgentHandler`: 6 methods

**Stats:** 39 lines

---

#### `ai_whisperer/agents/planner_tools.py`

**Functions:**
- `analyze_workspace(workspace_path)`
  - Return a flat list of files and folders in the workspace.
- `read_schema_files(schema_dir)`
  - Read all JSON schema files in a directory.
- `validate_plan(plan, schema)`
  - Validate a plan dict against a JSON schema (very basic).

**Stats:** 34 lines

---

#### `ai_whisperer/agents/prompt_optimizer.py`
*Prompt optimization for model-specific continuation behavior.*

**Classes:**
- `PromptOptimizer`: 4 methods
  - Optimizes prompts based on model capabilities for better continuation

**Functions:**
- `optimize_user_message(message, model_name, agent_type)`
  - Convenience function to optimize a user message.

**Stats:** 188 lines

---

#### `ai_whisperer/agents/registry.py`
**Classes:**
- `Agent`: 1 methods
  - Represents a specialized AI agent with specific capabilities
- `AgentRegistry`: 4 methods
  - Manages available agents and their configurations

**Stats:** 92 lines

---

#### `ai_whisperer/agents/session_manager.py`
**Classes:**
- `AgentSession`: 3 methods
  - Manages a chat session with agent switching capabilities
- `DummyHandler`: 1 methods

**Stats:** 37 lines

---

#### `ai_whisperer/agents/stateless_agent.py`
*Stateless Agent implementation that works with the new stateless AILoop.*

**Classes:**
- `StatelessAgent`: 9 methods
  - A stateless agent that processes messages without session management.

**Stats:** 242 lines

---

#### `ai_whisperer/agents/task_decomposer.py`
*Task Decomposer for Agent E.*

**Classes:**
- `TaskDecomposer`: 23 methods
  - Decomposes plans into executable tasks for external agents.

**Stats:** 814 lines

---

### ai_whisperer/ai_loop

#### `ai_whisperer/ai_loop/__init__.py`

**Stats:** 6 lines

---

#### `ai_whisperer/ai_loop/ai_config.py`
**Classes:**
- `AIConfig`: 2 methods
  - Configuration for the AILoop.

**Stats:** 26 lines

---

#### `ai_whisperer/ai_loop/ai_loopy.py`
**Classes:**
- `SessionState`: 0 methods
- `AILoop`: 2 methods
  - The core AI Loop orchestrates the interaction between the AI service,

**Stats:** 667 lines

---

#### `ai_whisperer/ai_loop/stateless_ai_loop.py`
*Stateless AILoop implementation that works without delegates.*

**Classes:**
- `StatelessAILoop`: 2 methods
  - A stateless version of AILoop that processes messages directly without

**Stats:** 569 lines

---

#### `ai_whisperer/ai_loop/tool_call_accumulator.py`
*Tool call accumulator for properly handling streaming tool calls.*

**Classes:**
- `ToolCallAccumulator`: 4 methods
  - Accumulates streaming tool call chunks into complete tool calls.

**Stats:** 68 lines

---

### ai_whisperer/ai_service

#### `ai_whisperer/ai_service/ai_service.py`
**Classes:**
- `AIStreamChunk`: 3 methods
- `AIService`: 0 methods

**Stats:** 42 lines

---

#### `ai_whisperer/ai_service/openrouter_ai_service.py`
*OpenRouter AI Service implementation*

**Classes:**
- `OpenRouterAIService`: 5 methods
  - OpenRouter API wrapper that passes messages directly to the API.

**Stats:** 253 lines

---

#### `ai_whisperer/ai_service/tool_calling.py`
*OpenAI/OpenRouter standard tool calling implementation.*

**Classes:**
- `ToolChoice`: 0 methods
  - Tool choice options
- `ToolCall`: 2 methods
  - Represents a tool call request from the model
- `ToolCallResult`: 1 methods
  - Result from executing a tool call
- `Message`: 1 methods
  - Base message class
- `UserMessage`: 1 methods
  - User message
- `AssistantMessage`: 2 methods
  - Assistant message with optional tool calls
- `ToolCallMessage`: 2 methods
  - Tool call result message
- `StreamAccumulator`: 2 methods
  - Accumulates streaming chunks for tool calls
- `ToolCallHandler`: 12 methods
  - Handles tool calling following OpenAI/OpenRouter standards

**Stats:** 322 lines

---

### ai_whisperer/batch

#### `ai_whisperer/batch/__init__.py`
*Batch mode components for Debbie the Debugger.*


**Stats:** 21 lines

---

#### `ai_whisperer/batch/__main__.py`
*Entry point for batch mode execution.*


**Functions:**
- `main()`
  - Main entry point for batch client

**Stats:** 29 lines

---

#### `ai_whisperer/batch/batch_client.py`
*Batch client core integration for Debbie the Debugger.*

**Classes:**
- `BatchClient`: 1 methods

**Stats:** 169 lines

---

#### `ai_whisperer/batch/debbie_integration.py`
*Integration module for Debbie the Debugger.*

**Classes:**
- `DebbieDebugger`: 4 methods
  - Main integration point for Debbie's debugging capabilities.
- `DebbieFactory`: 3 methods
  - Factory for creating Debbie instances with different configurations

**Stats:** 344 lines

---

#### `ai_whisperer/batch/intervention.py`
*Automated intervention system for Debbie the Debugger.*

**Classes:**
- `InterventionStrategy`: 0 methods
  - Types of intervention strategies
- `InterventionResult`: 0 methods
  - Result of an intervention attempt
- `InterventionConfig`: 0 methods
  - Configuration for intervention behavior
- `InterventionRecord`: 1 methods
  - Record of an intervention attempt
- `InterventionHistory`: 6 methods
  - Tracks intervention history and patterns
- `InterventionExecutor`: 3 methods
  - Executes intervention strategies
- `InterventionOrchestrator`: 2 methods
  - Orchestrates monitoring and intervention systems

**Stats:** 640 lines

---

#### `ai_whisperer/batch/monitoring.py`
*Real-time monitoring system for Debbie the Debugger.*

**Classes:**
- `MonitoringEvent`: 0 methods
  - Types of monitoring events
- `MonitoringMetrics`: 2 methods
  - Performance and health metrics for a session
- `AnomalyAlert`: 1 methods
  - Alert for detected anomaly
- `AnomalyDetector`: 4 methods
  - Detects anomalies in session behavior
- `DebbieMonitor`: 6 methods
  - Main monitoring system for Debbie
- `MetricsCollector`: 3 methods
  - Collects and aggregates performance metrics

**Stats:** 607 lines

---

#### `ai_whisperer/batch/script_processor.py`
*Script processor for Debbie the Debugger.*

**Classes:**
- `ScriptFileNotFoundError`: 0 methods
  - Raised when a script file cannot be found.
- `ScriptProcessor`: 7 methods
  - Processes batch scripts for execution.

**Stats:** 117 lines

---

#### `ai_whisperer/batch/server_manager.py`
*Server lifecycle management for batch mode.*

**Classes:**
- `ServerManager`: 6 methods

**Stats:** 126 lines

---

#### `ai_whisperer/batch/websocket_client.py`
*WebSocket client for Debbie the Debugger.*

**Classes:**
- `WebSocketError`: 0 methods
  - Base exception for WebSocket operations.
- `WebSocketConnectionError`: 0 methods
  - Raised when WebSocket connection fails.
- `WebSocketClient`: 2 methods
  - WebSocket client for communicating with the interactive server.

**Stats:** 210 lines

---

#### `ai_whisperer/batch/websocket_interceptor.py`
*WebSocket message interceptor for Debbie the Debugger.*

**Classes:**
- `MessageDirection`: 0 methods
  - Direction of WebSocket messages
- `MessageType`: 0 methods
  - Types of JSON-RPC messages
- `InterceptedMessage`: 1 methods
  - Represents an intercepted WebSocket message
- `MessageInterceptor`: 3 methods
  - Base class for message interception
- `WebSocketInterceptor`: 7 methods
  - Intercepts WebSocket messages for monitoring and debugging.
- `InterceptingWebSocket`: 3 methods
  - WebSocket wrapper that intercepts messages.

**Stats:** 520 lines

---

### ai_whisperer/commands

#### `ai_whisperer/commands/agent.py`
**Classes:**
- `AgentInspectCommand`: 1 methods

**Functions:**
- `inspect_agent_context(agent_id, info_type, context_manager, session_id)`
  - Inspect agent info (context, state, etc.) for debugging. Synchronous version for command system.
- `get_context_manager_for_agent(agent_id, session_id)`

**Stats:** 73 lines

---

#### `ai_whisperer/commands/args.py`

**Functions:**
- `parse_args(argstr)`
  - Parse a command argument string into positional args and options.

**Stats:** 22 lines

---

#### `ai_whisperer/commands/base.py`
**Classes:**
- `Command`: 2 methods
  - Abstract base class for all commands.

**Stats:** 28 lines

---

#### `ai_whisperer/commands/debbie.py`
*Debbie debugging commands for interactive session monitoring and analysis.*

**Classes:**
- `DebbieCommand`: 6 methods
  - Debbie debugging command with subcommands for session monitoring.

**Stats:** 386 lines

---

#### `ai_whisperer/commands/echo.py`
**Classes:**
- `EchoCommand`: 1 methods

**Stats:** 12 lines

---

#### `ai_whisperer/commands/errors.py`
**Classes:**
- `CommandError`: 0 methods
  - Custom exception for command errors (invalid arguments, unknown command, etc.)

**Stats:** 3 lines

---

#### `ai_whisperer/commands/help.py`
**Classes:**
- `HelpCommand`: 1 methods

**Stats:** 27 lines

---

#### `ai_whisperer/commands/registry.py`
**Classes:**
- `CommandRegistry`: 3 methods
  - Registry for all available commands.

**Stats:** 23 lines

---

#### `ai_whisperer/commands/session.py`
**Classes:**
- `SessionSwitchAgentCommand`: 1 methods

**Stats:** 22 lines

---

#### `ai_whisperer/commands/status.py`
**Classes:**
- `StatusCommand`: 1 methods

**Stats:** 20 lines

---

### ai_whisperer/context

#### `ai_whisperer/context/__init__.py`
*Context tracking for agent file awareness.*


**Stats:** 5 lines

---

#### `ai_whisperer/context/agent_context.py`
**Classes:**
- `AgentContext`: 16 methods
  - Concrete implementation of ContextProvider for agent-specific context management.

**Stats:** 142 lines

---

#### `ai_whisperer/context/context_item.py`
*Context item model for tracking files and content in agent context.*

**Classes:**
- `ContextItem`: 5 methods
  - Represents a single item in agent context.

**Stats:** 89 lines

---

#### `ai_whisperer/context/context_manager.py`
*Context manager for tracking agent context items.*

**Classes:**
- `AgentContextManager`: 11 methods
  - Manages context items for agents in a session.

**Stats:** 378 lines

---

#### `ai_whisperer/context/provider.py`
**Classes:**
- `ContextProvider`: 4 methods
  - Abstract interface for unified context management.

**Stats:** 39 lines

---

### ai_whisperer/logging

#### `ai_whisperer/logging/__init__.py`
*Enhanced logging infrastructure for Debbie the Debugger.*


**Stats:** 13 lines

---

#### `ai_whisperer/logging/debbie_logger.py`
*Debbie's enhanced logger with intelligent commentary and pattern detection.*

**Classes:**
- `PatternType`: 0 methods
  - Types of patterns Debbie can detect
- `DetectedPattern`: 1 methods
  - A pattern detected in the logs
- `Insight`: 1 methods
  - An insight generated by Debbie
- `PatternDetector`: 10 methods
  - Detects patterns in log streams
- `InsightGenerator`: 7 methods
  - Generates actionable insights from detected patterns
- `DebbieCommentary`: 5 methods
  - Debbie's intelligent commentary system
- `DebbieLogger`: 8 methods
  - Enhanced logger with Debbie's commentary capabilities

**Stats:** 479 lines

---

#### `ai_whisperer/logging/log_aggregator.py`
*Log aggregator for multi-source log management and correlation.*

**Classes:**
- `CorrelationGroup`: 2 methods
  - Group of correlated log entries
- `Timeline`: 4 methods
  - Timeline of events for visualization
- `TimelineBuilder`: 4 methods
  - Builds timelines from log events
- `LogAggregator`: 13 methods
  - Aggregates logs from multiple sources with correlation

**Stats:** 353 lines

---

### ai_whisperer/tools

#### `ai_whisperer/tools/__init__.py`

**Stats:** 1 lines

---

#### `ai_whisperer/tools/analyze_dependencies_tool.py`
*Tool for analyzing task dependencies and creating execution order.*

**Classes:**
- `AnalyzeDependenciesTool`: 7 methods
  - Tool for analyzing and resolving task dependencies.

**Stats:** 164 lines

---

#### `ai_whisperer/tools/analyze_languages_tool.py`
*Analyze Languages Tool - Detects programming languages used in the project*

**Classes:**
- `AnalyzeLanguagesTool`: 10 methods
  - Tool for analyzing programming languages used in the project.

**Stats:** 447 lines

---

#### `ai_whisperer/tools/base_tool.py`
**Classes:**
- `AITool`: 8 methods
  - Abstract base class for all AI-usable tools in the AIWhisperer project.

**Stats:** 90 lines

---

#### `ai_whisperer/tools/batch_command_tool.py`
*BatchCommandTool - Interprets and executes batch script commands.*

**Classes:**
- `CommandInterpreter`: 3 methods
  - Interprets natural language commands into structured actions
- `BatchCommandTool`: 15 methods
  - Tool for interpreting and executing batch script commands.

**Stats:** 590 lines

---

#### `ai_whisperer/tools/check_mail_tool.py`
*Check Mail Tool - Allows agents to check their mailbox for messages.*

**Classes:**
- `CheckMailTool`: 2 methods
  - Tool for checking mailbox messages.

**Stats:** 104 lines

---

#### `ai_whisperer/tools/create_plan_from_rfc_tool.py`
*Create Plan from RFC Tool - Converts RFCs into structured execution plans*

**Classes:**
- `CreatePlanFromRFCTool`: 12 methods
  - Tool for converting RFCs into structured execution plans.

**Stats:** 305 lines

---

#### `ai_whisperer/tools/create_rfc_tool.py`
*Create RFC Tool - Creates new RFC documents for feature refinement*

**Classes:**
- `CreateRFCTool`: 10 methods
  - Tool for creating new RFC documents from ideas.

**Stats:** 297 lines

---

#### `ai_whisperer/tools/decompose_plan_tool.py`
*Tool for decomposing Agent P plans into executable tasks.*

**Classes:**
- `DecomposePlanTool`: 7 methods
  - Tool for decomposing plans into executable tasks.

**Stats:** 124 lines

---

#### `ai_whisperer/tools/delete_plan_tool.py`
*Delete Plan Tool - Removes plan documents from the system*

**Classes:**
- `DeletePlanTool`: 9 methods
  - Tool for deleting plan documents and their directories.

**Stats:** 215 lines

---

#### `ai_whisperer/tools/delete_rfc_tool.py`
*Delete RFC Tool - Removes RFC documents from the system*

**Classes:**
- `DeleteRFCTool`: 8 methods
  - Tool for deleting RFC documents.

**Stats:** 179 lines

---

#### `ai_whisperer/tools/execute_command_tool.py`
**Classes:**
- `ExecuteCommandTool`: 7 methods
  - A tool to execute shell commands on the system.

**Stats:** 171 lines

---

#### `ai_whisperer/tools/fetch_url_tool.py`
*Fetch URL Tool - Fetches and processes web page content*

**Classes:**
- `FetchURLTool`: 14 methods
  - Tool for fetching and processing web page content.

**Stats:** 350 lines

---

#### `ai_whisperer/tools/find_pattern_tool.py`
*Tool for finding patterns in files using regex, similar to grep.*

**Classes:**
- `FindPatternTool`: 10 methods
  - Tool for searching files for regex patterns with context lines.

**Stats:** 341 lines

---

#### `ai_whisperer/tools/find_similar_code_tool.py`
*Find Similar Code Tool - Searches for code similar to proposed features*

**Classes:**
- `FindSimilarCodeTool`: 11 methods
  - Tool for finding code similar to proposed features or patterns.

**Stats:** 460 lines

---

#### `ai_whisperer/tools/format_for_external_agent_tool.py`
*Tool for formatting tasks for external AI coding assistants.*

**Classes:**
- `FormatForExternalAgentTool`: 7 methods
  - Tool for formatting tasks for specific external agents.

**Stats:** 161 lines

---

#### `ai_whisperer/tools/get_file_content_tool.py`
*Get File Content Tool - Read file content with advanced options*

**Classes:**
- `GetFileContentTool`: 10 methods
  - Tool for reading file content with advanced options like preview mode and line ranges.

**Stats:** 237 lines

---

#### `ai_whisperer/tools/get_project_structure_tool.py`
*Get Project Structure Tool - Analyzes and describes project organization*

**Classes:**
- `GetProjectStructureTool`: 11 methods
  - Tool for analyzing and understanding project structure and organization.

**Stats:** 516 lines

---

#### `ai_whisperer/tools/list_directory_tool.py`
*List Directory Tool - Lists files and directories in workspace paths*

**Classes:**
- `ListDirectoryTool`: 10 methods
  - Tool for listing files and directories within the workspace.

**Stats:** 233 lines

---

#### `ai_whisperer/tools/list_plans_tool.py`
*List Plans Tool - Lists available execution plans*

**Classes:**
- `ListPlansTool`: 8 methods
  - Tool for listing execution plans.

**Stats:** 211 lines

---

#### `ai_whisperer/tools/list_rfcs_tool.py`
*List RFCs Tool - Lists RFC documents by status*

**Classes:**
- `ListRFCsTool`: 9 methods
  - Tool for listing RFC documents with filtering options.

**Stats:** 236 lines

---

#### `ai_whisperer/tools/message_injector_tool.py`
*Message Injector Tool for Debbie the Debugger.*

**Classes:**
- `InjectionType`: 0 methods
  - Types of message injections
- `InjectionResult`: 1 methods
  - Result of message injection
- `MessageInjectorTool`: 19 methods
  - Injects messages into AI sessions to unstick agents, recover from errors,

**Stats:** 432 lines

---

#### `ai_whisperer/tools/monitoring_control_tool.py`
*Monitoring control tool for Debbie the Debugger.*

**Classes:**
- `MonitoringControlTool`: 10 methods
  - Control monitoring settings for AI sessions

**Stats:** 319 lines

---

#### `ai_whisperer/tools/move_plan_tool.py`
*Move Plan Tool - Moves plans between status directories*

**Classes:**
- `MovePlanTool`: 9 methods
  - Tool for moving plans between status directories.

**Stats:** 205 lines

---

#### `ai_whisperer/tools/move_rfc_tool.py`
*Move RFC Tool - Moves RFCs between status folders*

**Classes:**
- `MoveRFCTool`: 10 methods
  - Tool for moving RFC documents between status folders.

**Stats:** 269 lines

---

#### `ai_whisperer/tools/parse_external_result_tool.py`
*Tool for parsing results from external agent execution.*

**Classes:**
- `ParseExternalResultTool`: 7 methods
  - Tool for parsing execution results from external agents.

**Stats:** 178 lines

---

#### `ai_whisperer/tools/prepare_plan_from_rfc_tool.py`
*Tool to prepare RFC content and context for plan generation.*

**Classes:**
- `PreparePlanFromRFCTool`: 11 methods
  - Prepares RFC content and metadata for plan generation.

**Stats:** 276 lines

---

#### `ai_whisperer/tools/python_ast_json_tool.py`
*Python AST to JSON converter tool.*

**Classes:**
- `ProcessingTimeoutError`: 0 methods
  - Custom timeout error for processing timeouts.
- `PythonASTJSONTool`: 48 methods
  - Tool for converting Python code to AST JSON representation and back.

**Functions:**
- `extract_comments_from_source(source)`
  - Extract comments from Python source code.
- `calculate_formatting_metrics(source)`
  - Calculate formatting metrics for source code.
- `extract_docstring_info(node)`
  - Extract docstring information from AST node.

**Stats:** 4346 lines

---

#### `ai_whisperer/tools/python_executor_tool.py`
*Python Executor Tool for Debbie the Debugger.*

**Classes:**
- `ExecutionResult`: 1 methods
  - Result of Python script execution
- `DebugSandbox`: 3 methods
  - Sandboxed environment for executing Python scripts
- `PythonExecutorTool`: 15 methods
  - Executes Python scripts for advanced debugging and analysis.

**Stats:** 574 lines

---

#### `ai_whisperer/tools/read_file_tool.py`
**Classes:**
- `ReadFileTool`: 7 methods

**Stats:** 106 lines

---

#### `ai_whisperer/tools/read_plan_tool.py`
*Read Plan Tool - Reads and displays execution plan details*

**Classes:**
- `ReadPlanTool`: 9 methods
  - Tool for reading execution plan details.

**Stats:** 210 lines

---

#### `ai_whisperer/tools/read_rfc_tool.py`
*Read RFC Tool - Reads RFC documents and extracts information*

**Classes:**
- `ReadRFCTool`: 10 methods
  - Tool for reading RFC documents and extracting structured information.

**Stats:** 243 lines

---

#### `ai_whisperer/tools/recommend_external_agent_tool.py`
*Tool for recommending the best external agent for a task.*

**Classes:**
- `RecommendExternalAgentTool`: 7 methods
  - Tool for recommending external agents based on task characteristics.

**Stats:** 190 lines

---

#### `ai_whisperer/tools/reply_mail_tool.py`
*Reply Mail Tool - Allows agents to reply to messages in their mailbox.*

**Classes:**
- `ReplyMailTool`: 2 methods
  - Tool for replying to mail messages.

**Stats:** 127 lines

---

#### `ai_whisperer/tools/save_generated_plan_tool.py`
*Tool to save a plan that was generated by the agent.*

**Classes:**
- `SaveGeneratedPlanTool`: 8 methods
  - Saves a plan that was generated by the agent through the AI loop.

**Stats:** 222 lines

---

#### `ai_whisperer/tools/script_parser_tool.py`
*ScriptParserTool - Parses and validates batch scripts in multiple formats.*

**Classes:**
- `ScriptFormat`: 0 methods
  - Supported script formats
- `ParsedScript`: 1 methods
  - Represents a parsed batch script
- `ScriptParserTool`: 20 methods
  - Tool for parsing and validating batch scripts in multiple formats.

**Stats:** 535 lines

---

#### `ai_whisperer/tools/search_files_tool.py`
*Search Files Tool - Search for files by name pattern or content*

**Classes:**
- `SearchFilesTool`: 9 methods
  - Tool for searching files within the workspace by name or content.

**Stats:** 247 lines

---

#### `ai_whisperer/tools/send_mail_tool.py`
*Send Mail Tool - Allows agents to send messages to other agents or users.*

**Classes:**
- `SendMailTool`: 2 methods
  - Tool for sending mail messages to agents or users.

**Stats:** 125 lines

---

#### `ai_whisperer/tools/session_analysis_tool.py`
*Session analysis tool for Debbie the Debugger.*

**Classes:**
- `SessionAnalysisTool`: 10 methods
  - Analyze session patterns and performance

**Stats:** 371 lines

---

#### `ai_whisperer/tools/session_health_tool.py`
*Session health monitoring tool for Debbie the Debugger.*

**Classes:**
- `SessionHealthTool`: 7 methods
  - Check the health status of AI sessions

**Stats:** 182 lines

---

#### `ai_whisperer/tools/session_inspector_tool.py`
*Session Inspector Tool for Debbie the Debugger.*

**Classes:**
- `SessionAnalysis`: 1 methods
  - Results of session analysis
- `SessionInspectorTool`: 22 methods
  - Inspects and analyzes active AI sessions to detect issues like stalls,

**Stats:** 410 lines

---

#### `ai_whisperer/tools/system_health_check_tool.py`
*System Health Check Tool - Runs automated health check scripts for AIWhisperer*

**Classes:**
- `SystemHealthCheckTool`: 8 methods
  - Runs system health check scripts from a designated folder to verify

**Stats:** 401 lines

---

#### `ai_whisperer/tools/tool_registration.py`
*Centralized tool registration for AIWhisperer.*


**Functions:**
- `register_all_tools(path_manager)`
  - Register all available tools with the tool registry.
- `_register_file_tools(tool_registry)`
  - Register basic file operation tools.
- `_register_analysis_tools(tool_registry, path_manager)`
  - Register advanced analysis tools.
- `_register_rfc_tools(tool_registry)`
  - Register RFC management tools.
- `_register_plan_tools(tool_registry)`
  - Register plan management tools.
- `_register_codebase_tools(tool_registry)`
  - Register codebase analysis tools.
- `_register_web_tools(tool_registry)`
  - Register web research tools.
- `_register_debugging_tools(tool_registry)`
  - Register Debbie's debugging and monitoring tools.
- `_register_mailbox_tools(tool_registry)`
  - Register mailbox communication tools.
- `_register_agent_e_tools(tool_registry)`
  - Register Agent E task decomposition tools.
- `register_tool_category(category, path_manager)`
  - Register only tools from a specific category.

**Stats:** 251 lines

---

#### `ai_whisperer/tools/tool_registry.py`
**Classes:**
- `ToolRegistry`: 15 methods
  - Central registry for managing AI-usable tools.

**Functions:**
- `get_tool_registry()`
  - Returns the singleton instance of the ToolRegistry.

**Stats:** 249 lines

---

#### `ai_whisperer/tools/tool_set.py`
*Tool Set management for organizing tools into collections.*

**Classes:**
- `ToolSet`: 2 methods
  - Represents a collection of tools with inheritance support.
- `ToolSetManager`: 9 methods
  - Manages tool sets including loading, inheritance resolution, and lookups.

**Stats:** 235 lines

---

#### `ai_whisperer/tools/tool_usage_logging.py`

**Functions:**
- `log_tool_usage(agent, tool, params, result)`
- `get_tool_usage_log()`

**Stats:** 23 lines

---

#### `ai_whisperer/tools/update_plan_from_rfc_tool.py`
*Update Plan from RFC Tool - Updates plans when source RFC changes*

**Classes:**
- `UpdatePlanFromRFCTool`: 11 methods
  - Tool for updating plans when source RFC changes.

**Stats:** 315 lines

---

#### `ai_whisperer/tools/update_rfc_tool.py`
*Update RFC Tool - Updates existing RFC documents*

**Classes:**
- `UpdateRFCTool`: 13 methods
  - Tool for updating existing RFC documents during refinement.

**Stats:** 335 lines

---

#### `ai_whisperer/tools/update_task_status_tool.py`
*Tool for updating the status of decomposed tasks.*

**Classes:**
- `UpdateTaskStatusTool`: 9 methods
  - Tool for updating task execution status.

**Stats:** 207 lines

---

#### `ai_whisperer/tools/validate_external_agent_tool.py`
*Tool for validating external agent availability.*

**Classes:**
- `ValidateExternalAgentTool`: 7 methods
  - Tool for validating external agent environments.

**Stats:** 132 lines

---

#### `ai_whisperer/tools/web_search_tool.py`
*Web Search Tool - Basic web search functionality for Agent P*

**Classes:**
- `WebSearchTool`: 15 methods
  - Tool for searching the web for technical information and best practices.

**Stats:** 312 lines

---

#### `ai_whisperer/tools/workspace_stats_tool.py`
*Tool for analyzing workspace statistics.*

**Classes:**
- `WorkspaceStatsTool`: 9 methods
  - Tool for gathering statistics about the workspace.

**Stats:** 355 lines

---

#### `ai_whisperer/tools/workspace_validator_tool.py`
*Workspace Validator Tool for Debbie the Debugger.*

**Classes:**
- `ValidationStatus`: 0 methods
  - Status levels for validation checks
- `CheckCategory`: 0 methods
  - Categories of validation checks
- `ValidationCheck`: 1 methods
  - Individual validation check result
- `WorkspaceHealth`: 3 methods
  - Overall workspace health report
- `WorkspaceValidatorTool`: 19 methods
  - Validates AIWhisperer workspace structure, configuration, and health.

**Stats:** 673 lines

---

#### `ai_whisperer/tools/write_file_tool.py`
**Classes:**
- `WriteFileTool`: 7 methods

**Stats:** 123 lines

---

