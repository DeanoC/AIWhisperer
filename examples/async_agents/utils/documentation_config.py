"""
Module: examples/async_agents/utils/documentation_config.py
Purpose: Configuration structures for documentation workflow

Provides configuration parsing and validation for documentation generation.
"""

from enum import Enum
from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional


class DocumentationType(Enum):
    """Documentation types supported by the workflow."""
    API = "api"
    COMPREHENSIVE = "comprehensive"
    TUTORIAL = "tutorial"
    MIGRATION = "migration"
    TECHNICAL = "technical"


@dataclass
class DocumentationConfig:
    """
    Configuration for documentation generation workflow.
    
    Encapsulates all configuration options for generating documentation
    including target specification, agent selection, and output preferences.
    """
    # Target configuration
    target: Dict[str, Any]
    agents: List[str] = field(default_factory=lambda: ["a", "p"])
    doc_type: str = "api"
    
    # Content options
    include_examples: bool = False
    include_tests: bool = False
    
    # Review configuration
    review_enabled: bool = False
    review_iterations: int = 1
    incorporate_feedback: bool = False
    
    # Output configuration
    output_formats: List[str] = field(default_factory=lambda: ["markdown"])
    style_guide: str = ""
    
    # Analysis options
    check_existing: bool = False
    update_mode: str = "manual"
    analyze_breaking_changes: bool = False
    
    # Tutorial specific
    tutorial_config: Dict[str, Any] = field(default_factory=dict)
    
    # Migration specific
    generate_migration_scripts: bool = False
    
    # Error handling
    fallback_to_partial: bool = False
    simulate_failures: Dict[str, str] = field(default_factory=dict)
    
    def __post_init__(self):
        """Validate configuration after initialization."""
        # Validate doc_type
        valid_types = [t.value for t in DocumentationType]
        if self.doc_type not in valid_types:
            self.doc_type = DocumentationType.API.value
        
        # Ensure at least one output format
        if not self.output_formats:
            self.output_formats = ["markdown"]
        
        # Validate agents
        if not self.agents:
            self.agents = ["a", "p"]  # Default to Alice and Patricia
    
    def requires_review_agent(self) -> bool:
        """Check if review agent (Tessa) is needed."""
        return self.review_enabled and "t" not in self.agents
    
    def get_required_agents(self) -> List[str]:
        """Get list of required agents based on configuration."""
        required = list(self.agents)
        
        # Add Tessa if review is enabled
        if self.requires_review_agent():
            required.append("t")
        
        # Add Eamonn for examples/tutorials
        if self.include_examples or self.doc_type == DocumentationType.TUTORIAL.value:
            if "e" not in required:
                required.append("e")
        
        # Add Debbie for migration/troubleshooting
        if self.doc_type == DocumentationType.MIGRATION.value:
            if "d" not in required:
                required.append("d")
        
        return required