"""
Module: examples/async_agents/utils/bug_report.py
Purpose: Bug report data structures and utilities

Provides bug report parsing, classification, and validation
for the bug investigation workflow.
"""

from enum import Enum
from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional
from datetime import datetime


class BugSeverity(Enum):
    """Bug severity levels."""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    UNKNOWN = "unknown"


@dataclass
class BugReport:
    """
    Represents a bug report with automatic classification.
    
    Automatically determines severity based on keywords in title/description.
    """
    title: str
    id: Optional[str] = None
    description: Optional[str] = None
    severity: Optional[BugSeverity] = None
    urgency: Optional[str] = None
    reported_by: str = "unknown"
    reported_at: datetime = field(default_factory=datetime.now)
    error_log: Optional[str] = None
    affected_file: Optional[str] = None
    symptoms: List[str] = field(default_factory=list)
    error_patterns: List[str] = field(default_factory=list)
    required_info: List[str] = field(default_factory=list)
    
    def __post_init__(self):
        """Auto-classify severity if not provided."""
        # Convert string severity to enum if needed
        if isinstance(self.severity, str):
            try:
                self.severity = BugSeverity(self.severity.lower())
            except ValueError:
                self.severity = BugSeverity.UNKNOWN
        elif self.severity is None:
            self.severity = self._classify_severity()
    
    def _classify_severity(self) -> BugSeverity:
        """Classify bug severity based on keywords."""
        # Combine title and description for analysis
        text = (self.title + " " + (self.description or "")).lower()
        
        # Critical severity keywords
        critical_keywords = [
            "crash", "security", "vulnerability",
            "production down", "critical", "emergency"
        ]
        if any(keyword in text for keyword in critical_keywords):
            return BugSeverity.CRITICAL
        
        # High severity keywords
        high_keywords = [
            "data loss", "data corruption", "performance", "memory leak",
            "high", "urgent", "blocking"
        ]
        if any(keyword in text for keyword in high_keywords):
            return BugSeverity.HIGH
        
        # Low severity keywords
        low_keywords = [
            "typo", "ui", "alignment", "cosmetic", "minor",
            "documentation", "low priority"
        ]
        if any(keyword in text for keyword in low_keywords):
            return BugSeverity.LOW
        
        # Default to medium
        return BugSeverity.MEDIUM
    
    def validate(self) -> Dict[str, Any]:
        """Validate bug report completeness."""
        validation = {
            "is_valid": True,
            "missing_fields": [],
            "warnings": []
        }
        
        # Check required fields
        if not self.description:
            validation["is_valid"] = False
            validation["missing_fields"].append("description")
        
        if self.severity == BugSeverity.UNKNOWN:
            validation["warnings"].append("Severity could not be determined")
        
        if not self.error_log and not self.symptoms:
            validation["warnings"].append("No error logs or symptoms provided")
        
        return validation
    
    def enhance(self) -> None:
        """Enhance bug report with default values and recommendations."""
        if not self.description:
            self.description = "No description provided. Please add details."
        
        # Add required information checklist
        self.required_info = [
            "Steps to reproduce",
            "Expected behavior",
            "Actual behavior",
            "Environment details",
            "Error messages or logs"
        ]
        
        # If no symptoms, add template
        if not self.symptoms:
            self.symptoms = ["Please describe observed symptoms"]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "severity": self.severity.value if self.severity else "unknown",
            "urgency": self.urgency,
            "reported_by": self.reported_by,
            "reported_at": self.reported_at.isoformat(),
            "error_log": self.error_log,
            "affected_file": self.affected_file,
            "symptoms": self.symptoms,
            "error_patterns": self.error_patterns,
            "required_info": self.required_info
        }