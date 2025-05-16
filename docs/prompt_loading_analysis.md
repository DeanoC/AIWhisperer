# Enhanced Analysis of Current Prompt Loading System

## Prompt Types and Loading Mechanisms

### 1. Core Task Prompts (via [`src/ai_whisperer/config.py`](src/ai_whisperer/config.py))

- Defined in `DEFAULT_TASKS`: ["initial_plan", "subtask_generator", "refine_requirements"]
- Located in `prompts/` directory:
  - [`prompts/initial_plan_default.md`](prompts/initial_plan_default.md)
  - [`prompts/subtask_generator_default.md`](prompts/subtask_generator_default.md)
  - [`prompts/refine_requirements_default.md`](prompts/refine_requirements_default.md)
- Configurable per-task paths in YAML config
- Managed through `TaskPromptsContentOnDemand` lazy loader

### 2. Additional Prompt Types

- **Global Runner Default Prompt**:
  - Default file: [`prompts/global_runner_fallback_default.md`](prompts/global_runner_fallback_default.md)
  - Used as fallback for test-specific prompts
  - Handled separately in config.py

- **Agent Type Defaults**:
  - Specified under `prompts.agent_type_defaults` in config
  - Each agent type (e.g., "code_generation") has its own prompt path

### 3. Prompt Loading Hierarchy

1. Task-specific configured path (relative to config)
2. Default location in project root
3. Fallback to config directory
4. Global runner default (if configured)
5. Built-in defaults (for core tasks)

## Structural Analysis

### Loading Flow

1. Config loads initial paths (lines 246-258 in config.py)
2. `TaskPromptsContentOnDemand` handles on-demand loading (lines 96-112)
3. Global defaults loaded separately (lines 331-347)

### Key Classes

- `_load_prompt_content`: Base loading function with path resolution
- `_load_default_prompt_content`: Handles default task prompts
- `TaskPromptsContentOnDemand`: Dictionary-like lazy loader
- `OpenRouterAPI`: Executes loaded prompts

### Dependencies

- All prompt access goes through config.py
- SubtaskGenerator initiates prompt execution
- PostprocessingPipeline modifies prompt results

## Recommendations for Refactoring

1. Create dedicated `PromptSystem` service
2. Standardize prompt loading interface
3. Improve separation between:
   - Prompt content storage
   - Path resolution
   - Template processing
   - Execution
4. Add support for:
   - Prompt versioning
   - Environment-specific variants
   - Dynamic parameter injection
