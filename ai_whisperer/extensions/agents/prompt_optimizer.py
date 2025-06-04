"""
Module: ai_whisperer/agents/prompt_optimizer.py
Purpose: AI agent implementation for specialized task handling

This module implements an AI agent that processes user messages
and executes specialized tasks. It integrates with the tool system
and manages conversation context.

Key Components:
- PromptOptimizer: Optimizes prompts based on model capabilities for better continuation
- optimize_user_message(): 

Usage:
    promptoptimizer = PromptOptimizer()
    result = promptoptimizer.optimize_prompt()

Related:
- See PHASE_CONSOLIDATED_SUMMARY.md

"""

from typing import Any, Dict, Optional

import re
from ai_whisperer.model_capabilities import get_model_capabilities
from ai_whisperer.core.logging import get_logger

logger = get_logger(__name__)

# Precompiled regex patterns for analysis
SEQUENTIAL_PATTERNS = [
    re.compile(r'first.*then', re.IGNORECASE),
    re.compile(r'step 1.*step 2', re.IGNORECASE),
    re.compile(r'after.*next', re.IGNORECASE),
    re.compile(r'followed by', re.IGNORECASE),
    re.compile(r'and then', re.IGNORECASE),
    re.compile(r'subsequently', re.IGNORECASE)
]

STEP_INDICATOR_PATTERN = re.compile(r'step \d+|first|then|next', re.IGNORECASE)
TOOL_MENTION_PATTERN = re.compile(r'list|read|create|update|analyze|search|execute', re.IGNORECASE)

# Precompiled regex patterns for continuation detection
CONTINUATION_PATTERNS = [
    re.compile(r'^\bcontinue\b(:?\s*)?', re.IGNORECASE),
    re.compile(r'^\bplease continue\b', re.IGNORECASE),
    re.compile(r'^\b(ok|yes)\b\s*$', re.IGNORECASE),
    re.compile(r'^\b(go on|keep going|proceed)\b', re.IGNORECASE)
]

class PromptOptimizer:
    """Optimizes prompts based on model capabilities for better continuation"""
    
    MIN_WORD_COUNT_FOR_OPTIMIZATION = 10  # Minimum words before applying optimization
    
    def __init__(self):
        self.optimization_patterns = {
            'multi_tool': {
                'replacements': [
                    # Sequential to parallel (precompiled patterns with replacement strings)
                    (re.compile(r'First (.+?), then (.+?)\.', re.IGNORECASE), r'Simultaneously \1 and \2.'),
                    (re.compile(r'Step 1: (.+?)\. Step 2: (.+?)\.', re.IGNORECASE), r'Complete both: \1 and \2.'),
                    (re.compile(r'After (.+?), (.+?)\.', re.IGNORECASE), r'Do \1 and \2 together.'),
                    # Encourage batching (simple string replacements)
                    ('one by one', 'all at once'),
                    ('sequentially', 'in parallel'),
                    ('followed by', 'along with'),
                ],
                'hints': [
                    "You can execute multiple tools in a single response.",
                    "Batch related operations for efficiency.",
                    "Process multiple items simultaneously when possible."
                ]
            },
            'single_tool': {
                'replacements': [
                    # Parallel to sequential (precompiled patterns with replacement strings)
                    (re.compile(r'Simultaneously (.+?) and (.+?)\.', re.IGNORECASE), r'First \1, then \2.'),
                    (re.compile(r'(.+?) and (.+?) together', re.IGNORECASE), r'Step 1: \1. Step 2: \2.'),
                    # Simple string replacements
                    ('all at once', 'one at a time'),
                    # Add step indicators (precompiled pattern)
                    (re.compile(r'Do the following: (.+?)\.', re.IGNORECASE), r'Complete these steps: \1.'),
                ],
                'hints': [
                    "Complete each step before moving to the next.",
                    "I'll guide you through each operation.",
                    "Let's work through this systematically."
                ]
            }
        }
    
    def optimize_prompt(self, prompt: str, model_name: str, agent_type: str = None, is_continuation: bool = False) -> str:
        """
        Optimize a prompt for a specific model.
        
        Args:
            prompt: Original prompt text
            model_name: Target model name
            agent_type: Optional agent type for agent-specific optimizations
            is_continuation: Whether this is a continuation message
            
        Returns:
            Optimized prompt
        """
        # Skip optimization for continuation messages
        if is_continuation:
            logger.debug("Skipping optimization for continuation message")
            return prompt
        
        # Check if this is already a continuation message
        for pattern in CONTINUATION_PATTERNS:
            if pattern.match(prompt.strip()):
                logger.debug("Detected continuation pattern, skipping optimization")
                return prompt
        
        # Skip optimization for very short messages
        word_count = len(prompt.split())
        if word_count < self.MIN_WORD_COUNT_FOR_OPTIMIZATION:
            logger.debug(f"Skipping optimization for short message ({word_count} words)")
            return prompt
        
        capabilities = get_model_capabilities(model_name)
        optimized_prompt = prompt
        
        # Determine optimization strategy
        if capabilities.get('multi_tool'):
            strategy = 'multi_tool'
        else:
            strategy = 'single_tool'
        
        # Apply replacements
        patterns = self.optimization_patterns[strategy]
        for pattern, replacement in patterns['replacements']:
            if isinstance(pattern, re.Pattern):
                # Use compiled regex pattern
                optimized_prompt = pattern.sub(replacement, optimized_prompt)
            else:
                # Convert simple string pattern to regex for case-insensitive replacement
                regex_pattern = re.compile(re.escape(pattern), re.IGNORECASE)
                optimized_prompt = regex_pattern.sub(replacement, optimized_prompt)
        
        # Add hints based on agent type
        if agent_type:
            hints = self._get_agent_specific_hints(agent_type, strategy)
            if hints and hints not in optimized_prompt:
                optimized_prompt = f"{optimized_prompt}\n\n{hints}"
        
        # Add general strategy hints if no significant changes were made
        if abs(len(optimized_prompt) - len(prompt)) < 10:
            general_hint = patterns['hints'][0] if patterns['hints'] else ""
            if general_hint and general_hint not in optimized_prompt:
                optimized_prompt = f"{optimized_prompt}\n\n{general_hint}"
        
        # Log optimization if changed
        if optimized_prompt != prompt:
            logger.debug(f"Optimized prompt for {model_name} ({strategy} strategy)")
        
        return optimized_prompt
    
    def _get_agent_specific_hints(self, agent_type: str, strategy: str) -> str:
        """Get agent-specific optimization hints"""
        agent_hints = {
            'patricia': {
                'multi_tool': "When working with RFCs, you can list, read, and analyze them in a single operation.",
                'single_tool': "For RFC operations, I'll guide you through listing, reading, and analyzing step by step."
            },
            'e': {
                'multi_tool': "Execute multiple plan operations simultaneously when they don't depend on each other.",
                'single_tool': "Execute plan operations in sequence: list plans, read plan details, then decompose."
            },
            'alice': {
                'multi_tool': "Feel free to combine related file operations and searches.",
                'single_tool': "I'll help you with each operation step by step."
            }
        }
        
        return agent_hints.get(agent_type, {}).get(strategy, "")
    
    def analyze_prompt_for_optimization(self, prompt: str, model_name: str) -> Dict[str, Any]:
        """
        Analyze a prompt for optimization opportunities.
        
        Returns:
            Analysis with optimization suggestions
        """
        capabilities = get_model_capabilities(model_name)
        analysis = {
            'model': model_name,
            'supports_multi_tool': capabilities.get('multi_tool', False),
            'optimization_opportunities': [],
            'estimated_improvement': 0
        }
        
        # Check for sequential patterns in multi-tool models
        if capabilities.get('multi_tool'):
            for pattern in SEQUENTIAL_PATTERNS:
                if pattern.search(prompt):
                    analysis['optimization_opportunities'].append({
                        'type': 'sequential_to_parallel',
                        'pattern': pattern.pattern,  # Get the pattern string for display
                        'suggestion': 'Consider rephrasing to encourage parallel execution'
                    })
                    analysis['estimated_improvement'] += 20
        
        # Check for missing step indicators in single-tool models
        elif not capabilities.get('multi_tool'):
            if not STEP_INDICATOR_PATTERN.search(prompt):
                analysis['optimization_opportunities'].append({
                    'type': 'missing_steps',
                    'suggestion': 'Add explicit step indicators for clarity'
                })
                analysis['estimated_improvement'] += 15
        
        # Check for tool count hints
        tool_mentions = len(TOOL_MENTION_PATTERN.findall(prompt))
        if tool_mentions > 3:
            if capabilities.get('multi_tool'):
                analysis['optimization_opportunities'].append({
                    'type': 'high_tool_count',
                    'count': tool_mentions,
                    'suggestion': 'Emphasize batching for multiple operations'
                })
            else:
                analysis['optimization_opportunities'].append({
                    'type': 'high_tool_count', 
                    'count': tool_mentions,
                    'suggestion': 'Consider breaking into smaller sub-tasks'
                })
            analysis['estimated_improvement'] += 25
        
        return analysis

def optimize_user_message(message: str, model_name: str, agent_type: str = None, is_continuation: bool = False) -> str:
    """
    Convenience function to optimize a user message.
    
    Args:
        message: User's message
        model_name: Target model
        agent_type: Optional agent type
        is_continuation: Whether this is a continuation message
        
    Returns:
        Optimized message
    """
    optimizer = PromptOptimizer()
    return optimizer.optimize_prompt(message, model_name, agent_type, is_continuation)
