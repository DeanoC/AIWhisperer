# AIWhisperer Refactor Stage 3 Plan

## Overview
Having completed documentation consolidation, test reorganization, and configuration consolidation, we now move to the core code refactoring stage.

## Current State Summary
1. **Documentation**: Reduced from 250 to ~190 files (24% reduction)
2. **Tests**: Reorganized 109 files into logical structure, identified 65.9% coverage gap
3. **Configuration**: Consolidated from 218 to ~15 active configs
4. **Code**: Previously removed 223 obsolete Python files in Stage 1

## Stage 3: Core Code Refactoring

### Phase 1: Update Configuration System (1-2 days)
**Goal**: Integrate the new hierarchical configuration structure

1. **Update config.py**
   - Integrate hierarchical_config_loader.py
   - Support environment-specific overrides
   - Backward compatibility during transition

2. **Update all config references**
   - Change paths from old to new structure
   - Update schema loading paths
   - Fix agent config loading

3. **Verify functionality**
   - Test both CLI and interactive modes
   - Ensure all tools load correctly
   - Verify agent configurations work

### Phase 2: Address Test Coverage (1 week)
**Goal**: Improve coverage from 34.1% to 70%+ for core modules

1. **Priority 1 - Critical Infrastructure** (11 modules)
   - ai_whisperer.agents.base_handler
   - interactive_server.stateless_session_manager
   - ai_whisperer.batch.server_manager
   - ai_whisperer.ai_service.openrouter_ai_service
   - ai_whisperer.json_validator
   - + 6 more identified modules

2. **Priority 2 - Core Services**
   - AI loop components
   - Batch processing
   - Tool management

3. **Priority 3 - Integration Tests**
   - End-to-end workflows
   - Agent interactions
   - Error scenarios

### Phase 3: Code Quality Improvements (3-4 days)
**Goal**: Standardize code patterns and improve maintainability

1. **Naming Consistency**
   - Fix agent_e_* naming inconsistencies
   - Standardize module naming
   - Update class/function naming

2. **Module Organization**
   - Group related functionality
   - Reduce circular dependencies
   - Clear separation of concerns

3. **Error Handling**
   - Standardize exception hierarchy
   - Improve error messages
   - Add proper logging

4. **Type Annotations**
   - Add missing type hints
   - Use proper typing imports
   - Consider using mypy

### Phase 4: Performance Optimization (2-3 days)
**Goal**: Improve startup time and runtime performance

1. **Lazy Loading**
   - Defer tool loading until needed
   - Optimize imports
   - Cache expensive operations

2. **Memory Usage**
   - Profile memory usage
   - Fix memory leaks
   - Optimize data structures

3. **Async Improvements**
   - Better async/await patterns
   - Reduce blocking operations
   - Optimize WebSocket handling

### Phase 5: Final Cleanup (1-2 days)
**Goal**: Remove all obsolete code and finalize structure

1. **Remove obsolete files**
   - Execute cleanup scripts
   - Remove empty directories
   - Update .gitignore

2. **Documentation Updates**
   - Update README with new structure
   - Create developer guide
   - Update API documentation

3. **CI/CD Updates**
   - Update test discovery
   - Add coverage reporting
   - Update build scripts

## Success Metrics
- [ ] Test coverage ≥ 70% for core modules
- [ ] All tests passing with new structure
- [ ] Configuration system fully migrated
- [ ] Performance improvements measurable
- [ ] Zero circular dependencies
- [ ] Complete documentation

## Risk Mitigation
1. **Incremental Changes**: Make small, testable changes
2. **Backward Compatibility**: Maintain during transition
3. **Comprehensive Testing**: Test after each change
4. **Rollback Plan**: Git tags at each milestone
5. **Communication**: Document all breaking changes

## Timeline
- **Week 1**: Phases 1-2 (Config update + Priority 1 tests)
- **Week 2**: Phases 2-3 (Remaining tests + Code quality)
- **Week 3**: Phases 4-5 (Performance + Cleanup)

## Next Immediate Steps
1. Create feature branch for Stage 3
2. Update config.py to use new structure
3. Fix any broken imports/paths
4. Start with Priority 1 test coverage
5. Document any issues found

This plan provides a systematic approach to completing the prototype-to-production refactor with minimal risk and maximum benefit.