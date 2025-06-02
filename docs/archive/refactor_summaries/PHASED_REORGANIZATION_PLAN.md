# Phased Module Reorganization Plan

Given the large impact (152 files, 271 imports), we'll take a phased approach to minimize risk.

## Phase 1: Core Module Organization (Lowest Risk)

Move only the most fundamental modules that have clear ownership:

### 1.1 Create Core Package
```
ai_whisperer/core/
├── __init__.py
├── config.py         (from ai_whisperer/config.py)
├── exceptions.py     (from ai_whisperer/exceptions.py)
├── logging.py        (from ai_whisperer/logging_custom.py)
└── types.py         (new - for shared type definitions)
```

### 1.2 Create Utils Package
```
ai_whisperer/utils/
├── __init__.py
├── path.py          (from ai_whisperer/path_management.py)
├── workspace.py     (from ai_whisperer/workspace_detection.py)
├── validation.py    (from ai_whisperer/json_validator.py)
└── helpers.py       (from ai_whisperer/utils.py)
```

**Impact**: ~50 files need import updates
**Risk**: Low - these are foundational modules with clear purposes

## Phase 2: Service Layer Organization

### 2.1 AI Service Consolidation
```
ai_whisperer/services/
├── __init__.py
└── ai/
    ├── __init__.py
    ├── base.py      (from ai_service/ai_service.py)
    ├── openrouter.py (from ai_service/openrouter_ai_service.py)
    └── tool_calling.py
```

### 2.2 Execution Service
```
ai_whisperer/services/execution/
├── __init__.py
├── ai_loop.py       (from ai_loop/stateless_ai_loop.py)
├── context.py       (from context_management.py)
└── state.py         (from state_management.py)
```

**Impact**: ~60 files need import updates
**Risk**: Medium - core functionality but well-isolated

## Phase 3: Interface Layer (CLI)

Move CLI-related files together:
```
ai_whisperer/interfaces/
├── __init__.py
└── cli/
    ├── __init__.py
    ├── main.py      (from cli.py)
    ├── commands.py  (from cli_commands.py)
    └── batch.py     (from cli_commands_batch_mode.py)
```

**Impact**: ~30 files need import updates
**Risk**: Low - UI layer with clear boundaries

## Phase 4: Extensions (Optional Features)

Move batch mode and monitoring to extensions:
```
ai_whisperer/extensions/
├── __init__.py
├── batch/           (entire batch/ directory)
└── monitoring/
    └── debbie.py    (from logging/debbie_logger.py)
```

**Impact**: ~40 files need import updates
**Risk**: Low - these are optional features

## Implementation Strategy

### For Each Phase:

1. **Create migration script** specific to that phase
2. **Update imports** only for moved modules
3. **Run tests** to ensure nothing breaks
4. **Update documentation** for moved modules
5. **Commit changes** before next phase

### Advantages of Phased Approach:

1. **Lower risk** - smaller changes are easier to debug
2. **Gradual migration** - team can adapt incrementally
3. **Easy rollback** - can revert individual phases
4. **Continuous operation** - system stays functional
5. **Learning opportunity** - refine approach based on early phases

## Phase 1 Implementation Script

Here's a focused script for just Phase 1:

```python
#!/usr/bin/env python3
"""Phase 1: Core and Utils module reorganization"""

PHASE1_MOVEMENTS = {
    # Core modules
    "ai_whisperer/config.py": "ai_whisperer/core/config.py",
    "ai_whisperer/exceptions.py": "ai_whisperer/core/exceptions.py",
    "ai_whisperer/logging_custom.py": "ai_whisperer/core/logging.py",
    
    # Utils modules  
    "ai_whisperer/path_management.py": "ai_whisperer/utils/path.py",
    "ai_whisperer/workspace_detection.py": "ai_whisperer/utils/workspace.py",
    "ai_whisperer/json_validator.py": "ai_whisperer/utils/validation.py",
    "ai_whisperer/utils.py": "ai_whisperer/utils/helpers.py",
}

PHASE1_IMPORTS = {
    "ai_whisperer.config": "ai_whisperer.core.config",
    "ai_whisperer.exceptions": "ai_whisperer.core.exceptions", 
    "ai_whisperer.logging_custom": "ai_whisperer.core.logging",
    "ai_whisperer.path_management": "ai_whisperer.utils.path",
    "ai_whisperer.workspace_detection": "ai_whisperer.utils.workspace",
    "ai_whisperer.json_validator": "ai_whisperer.utils.validation",
    "ai_whisperer.utils": "ai_whisperer.utils.helpers",
}
```

## Next Steps

1. Review and approve phased approach
2. Implement Phase 1 migration script
3. Test Phase 1 thoroughly
4. Document lessons learned
5. Proceed to Phase 2 based on success

This phased approach reduces risk while still achieving the goal of better code organization.