# RFC to Structured Plan Implementation Checklist

## Overview
This document outlines the implementation plan for extending Agent Patricia's functionality to convert RFCs into structured execution plans. The goal is to allow users to progress from natural language RFCs to executable JSON plans while maintaining bidirectional synchronization.

## Architecture Design

### Core Concepts

1. **Plan Storage Structure**
   - Plans will live in `.WHISPER/plans/` directory
   - Subdirectories: `in_progress/` and `archived/`
   - Natural naming convention: `{rfc-short-name}-plan-{date}/`
   - Each plan directory contains:
     - `plan.json` - The main plan file
     - `subtasks/` - Individual subtask JSON files (for overview plans)
     - `rfc_reference.json` - Link back to source RFC

2. **RFC-Plan Linkage**
   - RFCs get a `derived_plan` field in metadata when plan is created
   - Plans reference source RFC via `source_rfc` field
   - Bidirectional updates: RFC changes can trigger plan regeneration

3. **Plan Generation Strategy**
   - Use OpenRouter's structured output feature for JSON generation
   - Two-stage approach: Initial simple plan → Detailed subtask breakdown
   - Design new optimal schemas for RFC-based plans (no backwards compatibility constraints)

## Implementation Checklist

### Phase 1: Infrastructure Setup

- [x] **1.1 Create Plan Directory Structure**
  - [x] Add `.WHISPER/plans/` directory creation to workspace initialization
  - [x] Create `in_progress/` and `archived/` subdirectories
  - [x] Update `.gitignore` to exclude `.WHISPER/` if needed

- [x] **1.2 Design New Plan Schemas (No Backwards Compatibility Required)**
  - [x] Create optimized schema specifically for RFC-based plans
  - [x] Add `source_rfc` field to plan schemas
  - [x] Add `rfc_version_hash` for change detection
  - [x] Create `rfc_reference.json` schema
  - [x] Consider improvements over existing plan format:
    - Better agent type definitions
    - Clearer dependency tracking
    - Enhanced validation rules
    - RFC-specific metadata fields

- [x] **1.3 Update RFC Schema**
  - [x] Add `derived_plans` array field to RFC metadata
  - [x] Include plan status and location information

### Phase 2: Core Tools Development

- [x] **2.1 Create `convert_rfc_to_plan` Tool** (Named: `create_plan_from_rfc`)
  - [x] Input: RFC ID or short name
  - [x] Parse RFC content to extract:
    - Requirements section
    - Technical considerations
    - Implementation approach
    - Acceptance criteria
  - [x] Generate structured prompt for plan creation
  - [x] Use OpenRouter structured output API
  - [x] Validate against plan schema
  - [x] Save plan with natural naming
  - [x] Update RFC metadata with plan reference

- [x] **2.2 Create `list_plans` Tool**
  - [x] Similar to `list_rfcs` functionality
  - [x] Support filtering by status (in_progress, archived)
  - [x] Show RFC linkage information
  - [x] Include plan creation date and last modified

- [x] **2.3 Create `read_plan` Tool**
  - [x] Load plan JSON and format for display
  - [x] Show RFC reference information
  - [x] Support both initial and overview plan formats
  - [x] Include subtask summary if overview plan

- [x] **2.4 Create `update_plan_from_rfc` Tool**
  - [x] Detect RFC changes via hash comparison
  - [x] Regenerate affected plan sections
  - [x] Preserve manual plan modifications where possible
  - [x] Log update history

- [x] **2.5 Create `move_plan` Tool**
  - [x] Move plans between in_progress and archived
  - [x] Update RFC metadata references
  - [x] Maintain directory structure

### Phase 3: Plan Generation Prompts

- [x] **3.1 Create RFC-to-Plan Conversion Prompt**
  - [x] Location: `prompts/agents/rfc_to_plan.prompt.md`
  - [x] Include instructions for:
    - Extracting requirements from RFC format
    - Mapping to appropriate agent types
    - Generating dependencies based on TDD approach
    - Creating validation criteria from acceptance criteria

- [x] **3.2 Create Plan Refinement Prompt**
  - [x] For breaking initial plans into detailed subtasks
  - [x] Include RFC context awareness
  - [x] Maintain traceability to RFC sections

### Phase 4: OpenRouter Integration

- [ ] **4.1 Implement Structured Output Support**
  - [ ] Extend `OpenRouterAIService` to support response_format parameter
  - [ ] Add schema validation for structured responses
  - [ ] Handle fallback for models without structured output support

- [ ] **4.2 Add Model Capability Detection**
  - [ ] Check if model supports structured outputs
  - [ ] Implement graceful degradation to postprocessing pipeline

### Phase 5: Patricia Agent Enhancement

- [x] **5.1 Update Patricia's System Prompt**
  - [x] Add plan conversion workflow instructions
  - [x] Include examples of when to suggest plan creation
  - [x] Add guidance for plan refinement dialogue

- [x] **5.2 Update Patricia's Tool Set**
  - [x] Add new plan-related tools to her available tools
  - [x] Register tools in stateless_session_manager.py
  - [x] Update tool_sets.yaml and agents.yaml configuration
  - [x] Fix Patricia's tool set reference from "rfc_management" to "rfc_specialist"

### Phase 6: Testing and Validation (Red/Green/Refactor TDD)

- [x] **6.1 Unit Tests (RED → GREEN → REFACTOR)**
  - [x] **RED Phase**: Write failing tests first
    - [x] Test specs for each tool's expected behavior
    - [x] Test cases for schema validation failures
    - [x] Test cases for structured output edge cases
    - [x] Test specs for RFC change detection algorithm
  - [x] **GREEN Phase**: Implement minimal code to pass
    - [x] Tool execution logic
    - [x] Schema validation implementation
    - [x] Structured output generation (via agent)
    - [x] Change detection implementation
  - [x] **REFACTOR Phase**: Improve code quality
    - [x] Extract common patterns
    - [x] Optimize performance (refactored to agent-based)
    - [x] Improve error messages
    - [x] Add comprehensive docstrings

- [x] **6.2 Integration Tests**
  - [x] Test full RFC-to-plan workflow (manually tested with chat-icons RFC)
  - [ ] Test bidirectional updates
  - [ ] Test plan archival process
  - [ ] Test error handling and recovery

- [x] **6.3 Debbie/Batch Mode End-to-End Testing**
  - [x] **Create Batch Test Scripts**
    - [x] `test_patricia_rfc_to_plan.json` - Full workflow test
    - [x] `test_rfc_plan_sync.json` - Bidirectional sync test
    - [ ] `test_plan_generation_quality.json` - Plan quality validation
  - [ ] **Debbie Integration Tests**
    - [ ] Use Debbie to monitor Patricia's RFC-to-plan conversion
    - [ ] Test error recovery scenarios with Debbie observation
    - [ ] Validate agent handoffs during plan creation
  - [ ] **Batch Mode Scenarios**
    - [ ] Script: Create RFC → Convert to plan → Execute plan
    - [ ] Script: Modify RFC → Update plan → Verify changes
    - [ ] Script: Archive RFC → Verify plan archival
    - [ ] Script: Multiple RFC conversions in sequence

- [ ] **6.4 Example Test Scenarios**
  - [ ] Simple RFC conversion (basic feature)
  - [ ] Complex RFC with multiple requirements
  - [ ] RFC with technical dependencies
  - [ ] RFC update triggering plan regeneration
  - [ ] Verify TDD enforcement in all generated plans

### Phase 7: Documentation

- [ ] **7.1 Update CLAUDE.md**
  - [ ] Document plan management workflow
  - [ ] Add examples of RFC-to-plan conversion

- [ ] **7.2 Create User Guide**
  - [ ] Document Patricia's plan conversion flow
  - [ ] Include best practices for RFC structure
  - [ ] Show example conversations

## Key Design Decisions

### 1. **Why Natural Naming for Plans?**
- Consistency with RFC naming approach
- Easier human navigation and understanding
- Clear linkage between RFC and derived plan

### 2. **Why Structured Output API?**
- More reliable than postprocessing
- Better model performance with schemas
- Reduced error rates in JSON generation

### 3. **Why Maintain RFC-Plan Linkage?**
- Enables iterative refinement
- Maintains traceability
- Supports bidirectional updates

### 4. **Why Two-Stage Plan Generation?**
- Matches existing plan system design
- Allows for progressive refinement
- Manages complexity better

## Implementation Priority

1. **High Priority**
   - Basic `convert_rfc_to_plan` tool
   - Plan storage infrastructure
   - Patricia prompt updates

2. **Medium Priority**
   - Bidirectional update mechanism
   - Structured output integration
   - Plan refinement features

3. **Low Priority**
   - Advanced plan analysis
   - Plan comparison tools
   - Automated plan execution triggers

## Success Criteria

- [x] Patricia can convert an RFC to a structured plan through natural conversation
- [x] Generated plans pass schema validation
- [x] Plans maintain proper TDD structure
- [x] RFC updates can be reflected in associated plans
- [x] Users can list and read plans through Patricia
- [x] Plans follow natural naming convention matching their RFC
- [ ] All new functionality has comprehensive test coverage

## TDD Workflow Guidelines

### Red Phase (Test First)
1. Write test specifications before any implementation
2. Define expected behavior through test cases
3. Ensure tests fail initially (no implementation exists)
4. Focus on edge cases and error conditions

### Green Phase (Make It Work)
1. Write minimal code to make tests pass
2. Don't worry about optimization or elegance yet
3. Focus solely on passing the test suite
4. Resist the urge to add extra functionality

### Refactor Phase (Make It Right)
1. Clean up code while keeping tests green
2. Extract common patterns and reduce duplication
3. Improve naming and documentation
4. Optimize performance where needed
5. Ensure code follows project conventions

## Testing Strategy with Debbie & Batch Mode

### Why Use Debbie for Testing?
- Monitors complex multi-agent interactions
- Catches edge cases in conversational flows
- Validates error recovery mechanisms
- Ensures agents work together correctly

### Why Use Batch Mode for Testing?
- Automates end-to-end workflow testing
- Creates reproducible test scenarios
- Tests real-world usage patterns
- Validates complete feature flows

### Example Batch Test Script Structure
```json
{
  "name": "test_patricia_rfc_to_plan",
  "description": "Test RFC to plan conversion workflow",
  "steps": [
    {
      "agent": "patricia",
      "message": "Create an RFC for adding a new caching feature",
      "expected_behavior": "Creates RFC with proper structure"
    },
    {
      "agent": "patricia", 
      "message": "Convert this RFC to a structured plan",
      "expected_behavior": "Generates valid plan with TDD structure"
    },
    {
      "agent": "debbie",
      "message": "monitor",
      "expected_behavior": "Observes the conversion process"
    }
  ]
}
```

## Notes

- Consider future integration with batch mode execution
- **No backwards compatibility required**: We are NOT constrained by the existing plan system format
  - Free to design optimal plan structure for RFC-based workflows
  - Can make breaking changes to schemas if it improves the design
  - Focus on the best solution for RFC-to-plan conversion
- Focus on user experience through conversational flow
- Use Debbie for debugging complex agent interactions
- Leverage batch mode for comprehensive workflow testing