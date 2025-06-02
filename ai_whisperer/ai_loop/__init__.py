"""
Module: ai_whisperer/ai_loop/__init__.py
Purpose: Package initialization for ai_loop

This module provides utility functions and supporting
infrastructure for the AIWhisperer application.

Dependencies:
- ai_config
- stateless_ai_loop

Related:
- See docs/archive/consolidated_phase2/docs/completed/REPOSITORY_CLEANUP_2025-05-29.md
- See UNTESTED_MODULES_REPORT.md

"""

# Export only the config and stateless implementations
from .ai_config import AIConfig
from .stateless_ai_loop import StatelessAILoop

# Note: The old ai_loopy.AILoop is deprecated due to delegate dependencies
# Use StatelessAILoop for new code