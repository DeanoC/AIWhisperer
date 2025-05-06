## Project Working Rules

This section outlines key principles governing the development process for this project. Adherence to these rules is crucial for maintaining code quality, ensuring project stability, and facilitating effective collaboration.

All sub tasks MUST be commanded to read this document and confirm to the user they understand the test-first driven design principle before proceeding.

### 1. Test-first Driven Design (TDD)

All code implementation must be preceded by the creation of tests and a basic scaffold (e.g., function signatures, class definitions). These tests must be run and confirmed to fail but not via a ModuleNoFoundError (which means the scaffold is not made) as expected *before* any functional implementation code is written.

**Key Points:**

*   **Write Tests First:** Develop unit tests that define the expected behavior of the new code. Our framework is pytest and must be used for all tests.
*   **Run and See Failures:** Execute the tests to ensure they fail for the correct reasons. This validates the tests themselves.
*   **Write Implementation Code:** Write the minimum amount of code necessary to make the tests pass.
*   **Generic Tests:** Tests should be designed to cover general functionality and not include special case logic merely to achieve a passing state. The goal is to test the intended behavior robustly.
*   **Refactor:** Once tests pass, refactor the code for clarity, performance, and maintainability, ensuring tests continue to pass.

This approach helps ensure that code is written with clear requirements in mind, is inherently testable, and reduces the likelihood of regressions.

### 2. Staged Review Process

Each major phase and its constituent tasks, as outlined in this task list document, must undergo a formal review and receive approval before development work on the subsequent phase or dependent task can commence.

**Key Points:**

*   **Sequential Progression:** Work proceeds in a staged manner, following the defined task list.
*   **Mandatory Review:** Upon completion of a defined stage or significant task block, a review must be initiated. On successful review, update this document's checkbox/s for the feature.
*   **Approval Required:** Work on the next stage/task block cannot begin until the current one has been reviewed and formally approved by the designated reviewers.
*   **Documentation:** Review feedback and approval status should be documented appropriately.
*   **Detailed plans** Planning documents are available in the project_dev/json_plan folder. This should be consulted before starting a task.

This process ensures that each part of the project meets quality standards and aligns with overall project goals before further development effort is invested. It also provides opportunities for course correction and knowledge sharing.

---
# YAML to JSON Migration: Task List Overview

This document outlines the tasks required for migrating the AI Whisperer project from YAML to JSON, based on the "Direct Migration Approach".

## Phase 1: Infrastructure and Utilities

### 1.1. JSON Schema and Validation

- [x] Define JSON schema for task plans (as per `json_schema_design.md`)
- [x] Define JSON schema for subtasks (as per `json_schema_design.md`)
- [ ] Write unit tests for JSON schema validation (target: `tests/unit/test_json_validation.py`)
- [x] Implement JSON schema validation utilities

### 1.2. Postprocessing for JSON

- [x] Design and plan JSON-specific postprocessing steps (ref: `postprocessing_pipeline_migration.md`)
- [x] Write unit tests for new `format_json` postprocessing step (target: `tests/unit/test_format_json.py`)
- [x] Implement `format_json` postprocessing step (`src/postprocessing/scripted_steps/format_json.py`)
- [x] Update `validate_syntax` postprocessing step for JSON and write/update unit tests
- [x] Update `clean_backtick_wrapper` postprocessing step for JSON and write/update unit tests
- [ ] Update `escape_text_fields` postprocessing step for JSON and write/update unit tests
- [ ] Update `handle_required_fields` postprocessing step for JSON and write/update unit tests
- [ ] Update `add_items_postprocessor` postprocessing step for JSON and write/update unit tests

### 1.3. YAML Component Removal

- [ ] Identify all YAML-specific code and dependencies across the codebase
- [ ] Remove YAML-specific postprocessing step: `fix_yaml_structure.py`
- [ ] Remove YAML-specific postprocessing step: `normalize_indentation.py`
- [ ] Remove YAML library imports (e.g., `ruamel.yaml`, `yaml`) where replaced by `json`
- [ ] Update exception types from YAML-specific to JSON-specific (e.g., `YAMLValidationError` to `JSONValidationError`)

## Phase 2: Core Component Migration

### 2.1. Orchestrator (`orchestrator.py`)

- [ ] Rename methods and variables from YAML-to-JSON (e.g., `generate_initial_yaml` to `generate_initial_json`)
- [ ] Update `_sanitize_json_text_fields` (formerly `_sanitize_yaml_text_fields`) for JSON specifics
- [ ] Update `save_json` (formerly `save_yaml`) to save JSON files
- [ ] Update `generate_initial_json` (formerly `generate_initial_yaml`) to:
    - [ ] Handle API responses expecting JSON
    - [ ] Integrate with the updated JSON postprocessing pipeline
    - [ ] Save output as `.json` files
- [ ] Update `generate_full_project_plan` to use new JSON methods and handle JSON files
- [ ] Modify Orchestrator prompt templates to instruct AI to generate JSON

### 2.2. SubtaskGenerator (`subtask_generator.py`)

- [ ] Rename methods and variables from YAML-to-JSON (e.g., `_sanitize_yaml_content` to `_sanitize_json_content`)
- [ ] Update `_prepare_prompt` to convert input steps to JSON for the prompt
- [ ] Update `_sanitize_json_content` (formerly `_sanitize_yaml_content`) for JSON specifics
- [ ] Update `generate_subtask` method to:
    - [ ] Handle AI responses expecting JSON
    - [ ] Integrate with the updated JSON postprocessing pipeline
    - [ ] Validate against JSON subtask schema
    - [ ] Save output as `.json` files
- [ ] Modify SubtaskGenerator prompt templates to instruct AI to generate JSON

### 2.3. Postprocessing Pipeline (`pipeline.py`)

- [ ] Ensure `PostprocessingPipeline` class correctly handles JSON data flow
- [ ] Configure pipeline in Orchestrator and SubtaskGenerator to use the new set of JSON-focused postprocessing steps

## Phase 3: Testing and Validation

### 3.1. Test Data Migration

- [ ] Develop a utility script to convert existing YAML test data to JSON format
- [ ] Execute script to convert all YAML test data files (`tests/**/*.yaml`) to JSON (`.json`)

### 3.2. Test Code Updates

- [ ] Rename test files from YAML-to-JSON (e.g., `tests/test_problematic_yaml.py` to `tests/test_problematic_json.py`)
- [ ] Update all existing unit and integration tests:
    - [ ] Replace YAML test data usage with new JSON test data
    - [ ] Update test assertions to check for JSON-specific behavior and outputs
    - [ ] Rename test methods and classes to reflect JSON testing
- [ ] Specifically update tests for Orchestrator (`tests/test_orchestrator.py`) for JSON functionality
- [ ] Specifically update tests for SubtaskGenerator (`tests/test_subtask_generator.py`) for JSON functionality
- [ ] Specifically update tests for Postprocessing Pipeline (`tests/integration/test_postprocessing_integration.py` and unit tests) for JSON functionality

### 3.3. New Tests for JSON Functionality

- [ ] Create comprehensive unit tests for `format_json.py` (if not fully covered in 1.2)
- [ ] Create comprehensive unit tests for `test_json_validation.py` (if not fully covered in 1.1)
- [ ] Create new integration tests for the end-to-end JSON generation and processing flow

### 3.4. Comprehensive Testing

- [ ] Execute the complete (migrated and new) JSON test suite
- [ ] Perform manual testing with diverse real-world examples and use cases
- [ ] Test edge cases and error handling scenarios for JSON processing
- [ ] Verify system behavior against the defined JSON schemas

## Phase 4: Deployment and Post-Migration

### 4.1. Deployment Preparation

- [ ] Ensure all documentation (READMEs, usage guides, etc.) is updated to reflect the JSON format and breaking changes
- [ ] Prepare migration guidance for users, including the YAML-to-JSON conversion utility script
- [ ] Update CI/CD pipeline to execute the new JSON-only test suite

### 4.2. Release

- [ ] Deploy the JSON-only version of AI Whisperer
- [ ] Announce breaking changes and provide migration support resources to users

### 4.3. Post-Deployment

- [ ] Monitor system for any issues related to JSON processing or new functionality
- [ ] Provide active support to users during the transition period
- [ ] Address any bugs or edge cases discovered post-release
- [ ] Collect user feedback for future improvements
- [ ] Perform a final cleanup of any remaining YAML-specific code or artifacts if not already done
