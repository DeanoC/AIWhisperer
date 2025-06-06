"""
Module: examples/async_agents/utils/result_aggregator.py
Purpose: Aggregate results from multiple async agents

GREEN Phase: Minimal implementation for result aggregation.
Combines outputs from multiple agents into coherent results.

Key Components:
- ResultAggregator: Main aggregation class
- Aggregation strategies for different result types
"""

import logging
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from collections import defaultdict

logger = logging.getLogger(__name__)


@dataclass
class AggregatedResult:
    """Aggregated results from multiple agents."""
    total_items: int = 0
    by_agent: Dict[str, Any] = field(default_factory=dict)
    by_category: Dict[str, List[Any]] = field(default_factory=lambda: defaultdict(list))
    summary: str = ""
    consensus: Optional[Dict[str, Any]] = None
    conflicts: List[Dict[str, Any]] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "total_items": self.total_items,
            "by_agent": self.by_agent,
            "by_category": dict(self.by_category),
            "summary": self.summary,
            "consensus": self.consensus,
            "conflicts": self.conflicts
        }


class ResultAggregator:
    """
    Aggregates results from multiple async agents.
    
    GREEN Phase: Basic aggregation functionality.
    """
    
    def __init__(self):
        """Initialize result aggregator."""
        self.results = AggregatedResult()
        
    def add_agent_result(self, agent_id: str, result: Dict[str, Any]):
        """
        Add a result from an agent.
        
        Args:
            agent_id: ID of the agent
            result: Result data from the agent
        """
        self.results.by_agent[agent_id] = result
        self.results.total_items += 1
        
        # Categorize results
        if "category" in result:
            category = result["category"]
            self.results.by_category[category].append({
                "agent": agent_id,
                "data": result
            })
            
        logger.info(f"Added result from agent {agent_id}")
        
    def aggregate(self, strategy: str = "simple") -> Dict[str, Any]:
        """
        Aggregate all results using specified strategy.
        
        Args:
            strategy: Aggregation strategy to use
            
        Returns:
            Aggregated results dictionary
        """
        if strategy == "simple":
            return self._simple_aggregation()
        elif strategy == "consensus":
            return self._consensus_aggregation()
        elif strategy == "weighted":
            return self._weighted_aggregation()
        else:
            raise ValueError(f"Unknown aggregation strategy: {strategy}")
            
    def _simple_aggregation(self) -> Dict[str, Any]:
        """Simple aggregation - combine all results."""
        # Generate summary
        agent_count = len(self.results.by_agent)
        category_count = len(self.results.by_category)
        
        self.results.summary = (
            f"Aggregated results from {agent_count} agents "
            f"across {category_count} categories."
        )
        
        return self.results.to_dict()
        
    def _consensus_aggregation(self) -> Dict[str, Any]:
        """Consensus aggregation - find agreements and conflicts."""
        # Find common elements across agent results
        consensus_items = {}
        conflict_items = []
        
        # For GREEN phase, simple consensus logic
        all_keys = set()
        for agent_result in self.results.by_agent.values():
            if isinstance(agent_result, dict):
                all_keys.update(agent_result.keys())
                
        for key in all_keys:
            values_by_agent = {}
            for agent_id, result in self.results.by_agent.items():
                if isinstance(result, dict) and key in result:
                    values_by_agent[agent_id] = result[key]
                    
            # Check for consensus
            unique_values = set(str(v) for v in values_by_agent.values())
            if len(unique_values) == 1:
                consensus_items[key] = list(values_by_agent.values())[0]
            elif len(unique_values) > 1:
                conflict_items.append({
                    "key": key,
                    "values": values_by_agent
                })
                
        self.results.consensus = consensus_items
        self.results.conflicts = conflict_items
        
        self.results.summary = (
            f"Found {len(consensus_items)} consensus items "
            f"and {len(conflict_items)} conflicts."
        )
        
        return self.results.to_dict()
        
    def _weighted_aggregation(self) -> Dict[str, Any]:
        """Weighted aggregation - give different weights to agents."""
        # For GREEN phase, simple weighted logic
        # Weight by agent reliability (mock weights)
        agent_weights = {
            "p": 1.2,  # Patricia - higher weight for planning
            "a": 1.0,  # Alice - standard weight
            "t": 0.9,  # Tessa - slightly lower for testing
            "d": 1.1   # Debbie - higher for debugging
        }
        
        weighted_scores = {}
        for agent_id, result in self.results.by_agent.items():
            weight = agent_weights.get(agent_id, 1.0)
            
            # Apply weight to numeric results
            if isinstance(result, dict):
                for key, value in result.items():
                    if isinstance(value, (int, float)):
                        if key not in weighted_scores:
                            weighted_scores[key] = 0
                        weighted_scores[key] += value * weight
                        
        self.results.summary = f"Weighted aggregation with {len(weighted_scores)} metrics."
        
        # Add weighted scores to result
        result = self.results.to_dict()
        result["weighted_scores"] = weighted_scores
        
        return result
        
    def clear(self):
        """Clear all accumulated results."""
        self.results = AggregatedResult()
        logger.info("Cleared aggregator results")