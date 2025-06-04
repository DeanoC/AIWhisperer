"""
Model Capability Tester Package

A standalone tool for testing and discovering model capabilities and quirks
on OpenRouter. This tool helps maintain accurate model capability configurations
by running automated tests against actual models.

Usage:
    python -m ai_whisperer.tools.model_capability_tester
    
See README.md for detailed documentation.
"""

from .test_models import ModelCapabilityTester, main

__all__ = ['ModelCapabilityTester', 'main']