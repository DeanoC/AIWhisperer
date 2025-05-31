# Agent P Issues and Improvements

This document captures observations and improvement suggestions for Agent P (Patricia) based on the first dogfooding experience with the Agent E RFC and plan generation.

## Date: 2025-05-31

### Context
- First time using Agent P's RFC-to-Plan conversion feature
- Test case: Agent E - Eamonn The Executioner feature
- Frontend timeout issues observed (though seemingly without bad effects)
- Web search tool unavailable to Agent P
- System prompt needs refinement

## RFC Generation Issues

### 1. Content Duplication
- **Issue**: The generated RFC contains duplicate sections (requirements repeated, open questions repeated)
- **Impact**: Makes the RFC harder to read and maintain
- **Suggested Fix**: Add deduplication logic in the RFC generation or post-processing

### 2. Missing Concrete Examples
- **Issue**: RFC lacks specific examples of how Agent E would decompose a plan
- **Impact**: Harder to understand the intended functionality
- **Suggested Improvement**: Prompt should encourage including concrete examples

### 3. Tool Discovery Not Well Represented
- **Issue**: RFC mentions discovering tools through usage but the plan doesn't reflect this discovery approach
- **Impact**: Mismatch between RFC philosophy and implementation plan
- **Suggested Fix**: Ensure plan generation considers discovery-oriented approaches mentioned in RFCs

## Plan Generation Issues

### 1. Missing Phase 0 Discovery Tasks
- **Issue**: The plan jumps directly to implementation without explicit discovery/prototype phase
- **Impact**: Risk of building the wrong thing or over-engineering
- **Suggested Improvement**: Add plan generation logic to detect phased approaches in RFCs and create corresponding tasks

### 2. Insufficient Granularity for Research Tasks
- **Issue**: External agent research lumped into single task instead of per-agent research
- **Impact**: May miss agent-specific requirements and optimizations
- **Suggested Fix**: Decompose research tasks based on enumerated items in RFC

### 3. Lack of Concrete Milestones
- **Issue**: Plan focuses on components but not on working increments
- **Impact**: Harder to validate progress and get early feedback
- **Suggested Improvement**: Include MVP/milestone tasks that deliver working functionality

### 4. Tool Development Tasks Missing
- **Issue**: No explicit tasks for creating Agent E-specific tools mentioned in RFC
- **Impact**: Critical component might be overlooked
- **Suggested Fix**: Scan RFC for tool-related requirements and generate corresponding tasks

## System Prompt Improvements

### 1. Example-Driven Refinement
- **Suggestion**: Include examples of good RFC structures in Agent P's prompt
- **Rationale**: Help avoid duplication and ensure completeness

### 2. Plan-RFC Alignment
- **Suggestion**: Emphasize checking that plans reflect all RFC sections, especially implementation approach
- **Rationale**: Current plan missed the discovery phase emphasis from RFC

### 3. Concrete Example Generation
- **Suggestion**: Prompt should explicitly ask for concrete examples when creating RFCs
- **Rationale**: Makes RFCs more understandable and actionable

### 4. Tool Discovery Awareness
- **Suggestion**: When RFCs mention "discovering" or "learning" approaches, plans should include explicit discovery tasks
- **Rationale**: Supports iterative, learning-based development

## Technical Issues

### 1. Frontend Timeout
- **Observation**: Timeout occurred during plan generation but didn't seem to affect the result
- **Potential Issue**: May indicate long-running operations without proper progress indication
- **Suggested Investigation**: Check if structured output generation takes longer than expected

### 2. Web Search Tool Unavailability
- **Issue**: Agent P couldn't use web search tool when it might have been helpful
- **Impact**: Limited ability to research external agent capabilities
- **Suggested Fix**: Ensure agents have access to appropriate tools based on their role

## Process Improvements

### 1. RFC Quality Validation
- **Suggestion**: Add a validation step to check for common issues (duplication, missing examples)
- **Implementation**: Could be a tool or post-processing step

### 2. Plan Quality Metrics
- **Suggestion**: Define metrics for plan quality (task granularity, phase alignment, completeness)
- **Implementation**: Automated checks during plan generation

### 3. Feedback Loop
- **Suggestion**: Create mechanism to capture learnings from plan execution back to Agent P
- **Rationale**: Continuous improvement of RFC and plan generation

## Next Steps

1. **Immediate**: Fix RFC duplication issue in post-processing
2. **Short-term**: Refine Agent P's system prompt with examples and guidelines
3. **Medium-term**: Implement plan quality validation
4. **Long-term**: Create feedback loop from plan execution to Agent P improvements

## Notes
- These observations come from first real-world use of the RFC-to-Plan system
- Overall the system works well, these are refinements to make it even better
- The Agent E RFC and plan are sufficient to start development despite these issues