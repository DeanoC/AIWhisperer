"""
Prompt optimization for model-specific continuation behavior.
"""

import re
from typing import Dict, List, Any
from ai_whisperer.model_capabilities import get_model_capabilities
from ai_whisperer.logging_custom import get_logger

logger = get_logger(__name__)


class PromptOptimizer:
    """Optimizes prompts based on model capabilities for better continuation"""
    
    def __init__(self):
        self.optimization_patterns = {
            'multi_tool': {
                'replacements': [
                    # Sequential to parallel
                    (r'First (.+?), then (.+?)\.', r'Simultaneously \1 and \2.'),
                    (r'Step 1: (.+?)\. Step 2: (.+?)\.', r'Complete both: \1 and \2.'),
                    (r'After (.+?), (.+?)\.', r'Do \1 and \2 together.'),
                    # Encourage batching
                    (r'one by one', 'all at once'),
                    (r'sequentially', 'in parallel'),
                    (r'followed by', 'along with'),
                ],
                'hints': [
                    "You can execute multiple tools in a single response.",
                    "Batch related operations for efficiency.",
                    "Process multiple items simultaneously when possible."
                ]
            },
            'single_tool': {
                'replacements': [
                    # Parallel to sequential
                    (r'Simultaneously (.+?) and (.+?)\.', r'First \1, then \2.'),
                    (r'(.+?) and (.+?) together', r'Step 1: \1. Step 2: \2.'),
                    (r'all at once', 'one at a time'),
                    # Add step indicators
                    (r'Do the following: (.+?)\.', r'Complete these steps: \1.'),
                ],
                'hints': [
                    "Complete each step before moving to the next.",
                    "I'll guide you through each operation.",
                    "Let's work through this systematically."
                ]
            }
        }
    
    def optimize_prompt(self, prompt: str, model_name: str, agent_type: str = None) -> str:
        """
        Optimize a prompt for a specific model.
        
        Args:
            prompt: Original prompt text
            model_name: Target model name
            agent_type: Optional agent type for agent-specific optimizations
            
        Returns:
            Optimized prompt
        """
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
            optimized_prompt = re.sub(pattern, replacement, optimized_prompt, flags=re.IGNORECASE)
        
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
            sequential_patterns = [
                'first.*then', 'step 1.*step 2', 'after.*next',
                'followed by', 'and then', 'subsequently'
            ]
            
            for pattern in sequential_patterns:
                if re.search(pattern, prompt, re.IGNORECASE):
                    analysis['optimization_opportunities'].append({
                        'type': 'sequential_to_parallel',
                        'pattern': pattern,
                        'suggestion': 'Consider rephrasing to encourage parallel execution'
                    })
                    analysis['estimated_improvement'] += 20
        
        # Check for missing step indicators in single-tool models
        elif not capabilities.get('multi_tool'):
            if not re.search(r'step \d+|first|then|next', prompt, re.IGNORECASE):
                analysis['optimization_opportunities'].append({
                    'type': 'missing_steps',
                    'suggestion': 'Add explicit step indicators for clarity'
                })
                analysis['estimated_improvement'] += 15
        
        # Check for tool count hints
        tool_mentions = len(re.findall(r'list|read|create|update|analyze|search|execute', prompt, re.IGNORECASE))
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


def optimize_user_message(message: str, model_name: str, agent_type: str = None) -> str:
    """
    Convenience function to optimize a user message.
    
    Args:
        message: User's message
        model_name: Target model
        agent_type: Optional agent type
        
    Returns:
        Optimized message
    """
    optimizer = PromptOptimizer()
    return optimizer.optimize_prompt(message, model_name, agent_type)