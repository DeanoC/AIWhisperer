# Migration from YAML to JSON: Main Analysis

## Introduction

This document outlines the strategy for migrating the AI Whisperer project from YAML to JSON as the structured output format. The migration is motivated by several issues with the current YAML implementation:

1. YAML's free-form nature is hard to condition
2. The current tool is broken due to YAML parsing issues
3. A more structured format like JSON would help development
4. The postprocessing system is currently focused on YAML and needs modification

## Current YAML Usage

The project currently uses YAML in several key components:

### Orchestrator
- Generates initial YAML task plans from requirements
- Uses both standard `yaml` and `ruamel.yaml` libraries
- Has methods for sanitizing YAML text fields
- Saves YAML content to files
- Uses a complex postprocessing pipeline for YAML content

### Subtask Generator
- Generates detailed subtask YAML definitions from input steps
- Has a method for sanitizing YAML content
- Uses the same postprocessing pipeline as the Orchestrator

### Postprocessing Pipeline
- Processes YAML through a series of scripted steps
- Handles YAML in both string and dictionary formats
- Includes steps for fixing YAML structure, normalizing indentation, validating syntax, etc.
- Has an AI improvements phase (currently a dummy identity transform)

## Components Requiring Modification

### Files that handle YAML generation:
1. `src/ai_whisperer/orchestrator.py`
   - `generate_initial_yaml` method
   - `save_yaml` method
   - `_sanitize_yaml_text_fields` method

2. `src/ai_whisperer/subtask_generator.py`
   - `generate_subtask` method
   - `_sanitize_yaml_content` method
   - `_prepare_prompt` method

### Files that handle YAML parsing:
1. `src/ai_whisperer/orchestrator.py`
   - YAML parsing in `generate_initial_yaml` method
   - YAML parsing in `generate_full_project_plan` method

2. `src/ai_whisperer/subtask_generator.py`
   - YAML parsing in `generate_subtask` method

### Files that handle YAML validation:
1. `src/postprocessing/scripted_steps/validate_syntax.py`
   - `validate_syntax` function

2. `src/ai_whisperer/utils.py`
   - `validate_against_schema` function

### Postprocessing steps:
1. `src/postprocessing/scripted_steps/fix_yaml_structure.py`
2. `src/postprocessing/scripted_steps/normalize_indentation.py`
3. `src/postprocessing/scripted_steps/clean_backtick_wrapper.py`
4. `src/postprocessing/scripted_steps/escape_text_fields.py`
5. `src/postprocessing/scripted_steps/handle_required_fields.py`
6. `src/postprocessing/scripted_steps/add_items_postprocessor.py`
7. `src/postprocessing/scripted_steps/identity_transform.py`

### Tests:
1. `tests/test_problematic_yaml.py`
2. `tests/unit/test_postprocessing_*.py` (multiple test files)
3. `tests/integration/test_postprocessing_integration.py`
4. `tests/test_orchestrator.py`
5. `tests/test_subtask_generator.py`

## Dependencies Between Components

The project has several dependencies between components that need to be considered during migration:

1. The Orchestrator and SubtaskGenerator both use the PostprocessingPipeline
2. The PostprocessingPipeline uses multiple scripted steps
3. Tests depend on the behavior of all these components
4. The schema validation depends on the structure of the data

## Next Steps

The following documents will provide detailed analysis and migration plans for each component:

1. [JSON Schema Design](json_schema_design.md)
2. [Orchestrator Migration](orchestrator_migration.md)
3. [Subtask Generator Migration](subtask_generator_migration.md)
4. [Postprocessing Pipeline Migration](postprocessing_pipeline_migration.md)
5. [Testing Strategy](testing_strategy.md)
6. [Implementation Approach](implementation_approach.md)