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

- [ ] **1.1 Create Plan Directory Structure**
  - [ ] Add `.WHISPER/plans/` directory creation to workspace initialization
  - [ ] Create `in_progress/` and `archived/` subdirectories
  - [ ] Update `.gitignore` to exclude `.WHISPER/` if needed

- [ ] **1.2 Design New Plan Schemas (No Backwards Compatibility Required)**
  - [ ] Create optimized schema specifically for RFC-based plans
  - [ ] Add `source_rfc` field to plan schemas
  - [ ] Add `rfc_version_hash` for change detection
  - [ ] Create `rfc_reference.json` schema
  - [ ] Consider improvements over existing plan format:
    - Better agent type definitions
    - Clearer dependency tracking
    - Enhanced validation rules
    - RFC-specific metadata fields

- [ ] **1.3 Update RFC Schema**
  - [ ] Add `derived_plans` array field to RFC metadata
  - [ ] Include plan status and location information

### Phase 2: Core Tools Development

- [ ] **2.1 Create `convert_rfc_to_plan` Tool**
  - [ ] Input: RFC ID or short name
  - [ ] Parse RFC content to extract:
    - Requirements section
    - Technical considerations
    - Implementation approach
    - Acceptance criteria
  - [ ] Generate structured prompt for plan creation
  - [ ] Use OpenRouter structured output API
  - [ ] Validate against plan schema
  - [ ] Save plan with natural naming
  - [ ] Update RFC metadata with plan reference

- [ ] **2.2 Create `list_plans` Tool**
  - [ ] Similar to `list_rfcs` functionality
  - [ ] Support filtering by status (in_progress, archived)
  - [ ] Show RFC linkage information
  - [ ] Include plan creation date and last modified

- [ ] **2.3 Create `read_plan` Tool**
  - [ ] Load plan JSON and format for display
  - [ ] Show RFC reference information
  - [ ] Support both initial and overview plan formats
  - [ ] Include subtask summary if overview plan

- [ ] **2.4 Create `update_plan_from_rfc` Tool**
  - [ ] Detect RFC changes via hash comparison
  - [ ] Regenerate affected plan sections
  - [ ] Preserve manual plan modifications where possible
  - [ ] Log update history

- [ ] **2.5 Create `move_plan` Tool**
  - [ ] Move plans between in_progress and archived
  - [ ] Update RFC metadata references
  - [ ] Maintain directory structure

### Phase 3: Plan Generation Prompts

- [ ] **3.1 Create RFC-to-Plan Conversion Prompt**
  - [ ] Location: `prompts/agents/rfc_to_plan.prompt.md`
  - [ ] Include instructions for:
    - Extracting requirements from RFC format
    - Mapping to appropriate agent types
    - Generating dependencies based on TDD approach
    - Creating validation criteria from acceptance criteria

- [ ] **3.2 Create Plan Refinement Prompt**
  - [ ] For breaking initial plans into detailed subtasks
  - [ ] Include RFC context awareness
  - [ ] Maintain traceability to RFC sections

### Phase 4: OpenRouter Integration

- [ ] **4.1 Implement Structured Output Support**
  - [ ] Extend `OpenRouterAIService` to support response_format parameter
  - [ ] Add schema validation for structured responses
  - [ ] Handle fallback for models without structured output support

- [ ] **4.2 Add Model Capability Detection**
  - [ ] Check if model supports structured outputs
  - [ ] Implement graceful degradation to postprocessing pipeline

### Phase 5: Patricia Agent Enhancement

- [ ] **5.1 Update Patricia's System Prompt**
  - [ ] Add plan conversion workflow instructions
  - [ ] Include examples of when to suggest plan creation
  - [ ] Add guidance for plan refinement dialogue

- [ ] **5.2 Update Patricia's Tool Set**
  - [ ] Add new plan-related tools to her available tools
  - [ ] Ensure proper tool descriptions for AI understanding

### Phase 6: Testing and Validation (Red/Green/Refactor TDD)

- [ ] **6.1 Unit Tests (RED → GREEN → REFACTOR)**
  - [ ] **RED Phase**: Write failing tests first
    - [ ] Test specs for each tool's expected behavior
    - [ ] Test cases for schema validation failures
    - [ ] Test cases for structured output edge cases
    - [ ] Test specs for RFC change detection algorithm
  - [ ] **GREEN Phase**: Implement minimal code to pass
    - [ ] Tool execution logic
    - [ ] Schema validation implementation
    - [ ] Structured output generation
    - [ ] Change detection implementation
  - [ ] **REFACTOR Phase**: Improve code quality
    - [ ] Extract common patterns
    - [ ] Optimize performance
    - [ ] Improve error messages
    - [ ] Add comprehensive docstrings

- [ ] **6.2 Integration Tests**
  - [ ] Test full RFC-to-plan workflow
  - [ ] Test bidirectional updates
  - [ ] Test plan archival process
  - [ ] Test error handling and recovery

- [ ] **6.3 Debbie/Batch Mode End-to-End Testing**
  - [ ] **Create Batch Test Scripts**
    - [ ] `test_patricia_rfc_to_plan.json` - Full workflow test
    - [ ] `test_rfc_plan_sync.json` - Bidirectional sync test
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

- [ ] Patricia can convert an RFC to a structured plan through natural conversation
- [ ] Generated plans pass schema validation
- [ ] Plans maintain proper TDD structure
- [ ] RFC updates can be reflected in associated plans
- [ ] Users can list and read plans through Patricia
- [ ] Plans follow natural naming convention matching their RFC
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