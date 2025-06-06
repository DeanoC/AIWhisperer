"""
Module: examples/async_agents/documentation_workflow.py
Purpose: Documentation generation workflow using async agents

Demonstrates collaborative documentation creation with multiple agents
analyzing code, writing docs, reviewing content, and generating outputs.

Key Features:
- Multi-format documentation generation
- Automatic outdated doc detection
- Collaborative review process
- Style guide enforcement
"""

import asyncio
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional, Set
from datetime import datetime
from dataclasses import dataclass, field

from ai_whisperer.services.agents.async_session_manager_v2 import (
    AsyncAgentSessionManager, AgentState
)
from ai_whisperer.extensions.mailbox.mailbox import MessagePriority, Mail

from .utils.base_workflow import BaseWorkflow, WorkflowResult
from .utils.documentation_config import DocumentationConfig, DocumentationType

logger = logging.getLogger(__name__)


@dataclass
class DocumentationResult(WorkflowResult):
    """Results from documentation generation workflow."""
    target_name: str = ""
    target_type: str = ""
    doc_type: str = ""
    agent_contributions: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    sections_generated: List[str] = field(default_factory=list)
    review_performed: bool = False
    review_feedback: List[Dict[str, Any]] = field(default_factory=list)
    tutorial_metadata: Dict[str, Any] = field(default_factory=dict)
    tutorial_sections: Dict[str, Any] = field(default_factory=dict)
    from_version: str = ""
    to_version: str = ""
    breaking_changes: List[Dict[str, Any]] = field(default_factory=list)
    migration_steps: List[str] = field(default_factory=list)
    migration_scripts: List[Dict[str, Any]] = field(default_factory=list)
    scripts_generated: bool = False
    review_iterations_completed: int = 0
    feedback_incorporated: bool = False
    review_history: List[Dict[str, Any]] = field(default_factory=list)
    output_files: List[Dict[str, Any]] = field(default_factory=list)
    style_guide_applied: str = ""
    outdated_sections: List[Dict[str, Any]] = field(default_factory=list)
    update_recommendations: List[str] = field(default_factory=list)
    targets_processed: int = 0
    documentation_results: List[Dict[str, Any]] = field(default_factory=list)
    style_consistency_score: float = 0.0
    cross_references_generated: bool = False
    partial_documentation: bool = False
    confidence_level: str = "medium"
    limitations: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        base_dict = super().to_dict()
        base_dict.update({
            "target_name": self.target_name,
            "target_type": self.target_type,
            "doc_type": self.doc_type,
            "agent_contributions": self.agent_contributions,
            "sections_generated": self.sections_generated,
            "review_performed": self.review_performed,
            "review_feedback": self.review_feedback,
            "tutorial_metadata": self.tutorial_metadata,
            "tutorial_sections": self.tutorial_sections,
            "from_version": self.from_version,
            "to_version": self.to_version,
            "breaking_changes": self.breaking_changes,
            "migration_steps": self.migration_steps,
            "migration_scripts": self.migration_scripts,
            "scripts_generated": self.scripts_generated,
            "review_iterations_completed": self.review_iterations_completed,
            "feedback_incorporated": self.feedback_incorporated,
            "review_history": self.review_history,
            "output_files": self.output_files,
            "style_guide_applied": self.style_guide_applied,
            "outdated_sections": self.outdated_sections,
            "update_recommendations": self.update_recommendations,
            "targets_processed": self.targets_processed,
            "documentation_results": self.documentation_results,
            "style_consistency_score": self.style_consistency_score,
            "cross_references_generated": self.cross_references_generated,
            "partial_documentation": self.partial_documentation,
            "confidence_level": self.confidence_level,
            "limitations": self.limitations
        })
        return base_dict


class DocumentationWorkflow(BaseWorkflow):
    """
    Orchestrates collaborative documentation generation workflow.
    
    Coordinates multiple agents to analyze code, write documentation,
    review content, and generate multi-format outputs.
    """
    
    # Agent role definitions for documentation
    AGENT_ROLES = {
        "a": {
            "name": "Alice",
            "role": "Code Analyst",
            "specialties": ["code analysis", "API extraction", "structure mapping"]
        },
        "p": {
            "name": "Patricia",
            "role": "Documentation Writer",
            "specialties": ["technical writing", "content organization", "style guides"]
        },
        "d": {
            "name": "Debbie",
            "role": "Documentation Debugger",
            "specialties": ["accuracy checking", "completeness", "error detection"]
        },
        "e": {
            "name": "Eamonn",
            "role": "Example Generator",
            "specialties": ["code examples", "tutorials", "practical guides"]
        },
        "t": {
            "name": "Tessa",
            "role": "Documentation Reviewer",
            "specialties": ["quality assurance", "consistency", "user testing"]
        }
    }
    
    async def run(self, config: Dict[str, Any], session_manager: AsyncAgentSessionManager) -> Dict[str, Any]:
        """
        Run documentation generation workflow.
        
        Args:
            config: Workflow configuration
            session_manager: Async agent session manager
            
        Returns:
            Dictionary with documentation results
        """
        result = DocumentationResult()
        result.start_time = datetime.now()
        
        try:
            # Handle batch documentation
            if "targets" in config:
                return await self._run_batch_documentation(config, session_manager, result)
            
            # Parse configuration
            doc_config = self._parse_configuration(config)
            self._populate_result_metadata(result, doc_config)
            
            # Create agent sessions
            await self._create_agent_sessions(
                doc_config.agents, session_manager, result, doc_config.simulate_failures
            )
            
            # Generate documentation based on type
            await self._generate_documentation(doc_config, result)
            
            # Post-processing steps
            await self._perform_post_processing(doc_config, result)
            
            # Determine final status
            result.status = self._determine_final_status(result, doc_config.fallback_to_partial)
            
            result.end_time = datetime.now()
            return result.to_dict()
            
        except Exception as e:
            logger.error(f"Documentation generation failed: {e}")
            result.status = "failed"
            result.add_error("workflow_error", str(e))
            result.end_time = datetime.now()
            return result.to_dict()
    
    async def _generate_api_documentation(
        self,
        agents: List[str],
        target: Dict[str, Any],
        result: DocumentationResult
    ) -> None:
        """Generate API documentation."""
        # Alice analyzes the code
        if "a" in agents:
            analysis = await self._analyze_code(target, result)
            result.agent_contributions["a"] = {
                "role": "code_analysis",
                "findings": analysis
            }
        
        # Patricia writes the documentation
        if "p" in agents:
            await asyncio.sleep(1)  # Simulate processing
            result.agent_contributions["p"] = {
                "role": "documentation_writing",
                "sections": ["api_reference", "usage_examples"]
            }
            result.sections_generated = ["api_reference"]
    
    async def _generate_comprehensive_documentation(
        self,
        agents: List[str],
        target: Dict[str, Any],
        result: DocumentationResult,
        include_examples: bool,
        include_tests: bool,
        review_enabled: bool
    ) -> None:
        """Generate comprehensive documentation."""
        sections = ["overview", "architecture", "api_reference"]
        
        # Add sections based on configuration
        if include_examples:
            sections.append("examples")
        if include_tests:
            sections.append("testing_guide")
        sections.append("troubleshooting")
        
        # Simulate agent contributions
        for agent_id in agents:
            if agent_id == "a":
                result.agent_contributions["a"] = {
                    "role": "code_analysis",
                    "sections_analyzed": sections
                }
            elif agent_id == "p":
                result.agent_contributions["p"] = {
                    "role": "documentation_writing",
                    "sections_written": sections
                }
            elif agent_id == "d":
                result.agent_contributions["d"] = {
                    "role": "debugging_documentation",
                    "troubleshooting_added": True
                }
            elif agent_id == "e":
                result.agent_contributions["e"] = {
                    "role": "example_generation",
                    "examples_created": 5
                }
            elif agent_id == "t":
                result.agent_contributions["t"] = {
                    "role": "review_preparation",
                    "review_checklist": ["completeness", "accuracy", "clarity"]
                }
        
        result.sections_generated = sections
        result.review_performed = review_enabled
        
        if review_enabled:
            result.review_feedback = [
                {"section": "api_reference", "feedback": "Add more examples"},
                {"section": "architecture", "feedback": "Clarify data flow"}
            ]
    
    async def _generate_tutorial_documentation(
        self,
        agents: List[str],
        target: Dict[str, Any],
        config: 'DocumentationConfig',
        result: DocumentationResult
    ) -> None:
        """Generate tutorial documentation."""
        tutorial_config = config.tutorial_config
        difficulty = tutorial_config.get("difficulty", "intermediate")
        
        result.tutorial_metadata = {
            "difficulty": difficulty,
            "estimated_time": "30 minutes",
            "prerequisites": ["Basic Python knowledge", "Understanding of async/await"]
        }
        
        # Generate tutorial structure
        tutorial_sections = {
            "introduction": "Introduction to the Mail System",
            "prerequisites": ["Python 3.8+", "AIWhisperer installed"],
            "steps": [
                {"number": 1, "title": "Setting up the mail system", "content": "..."},
                {"number": 2, "title": "Sending your first mail", "content": "..."},
                {"number": 3, "title": "Handling mail responses", "content": "..."}
            ],
            "summary": "You've learned how to use the mail system"
        }
        
        if tutorial_config.get("include_exercises", False):
            tutorial_sections["exercises"] = [
                {"difficulty": "easy", "task": "Send a mail to Debbie"},
                {"difficulty": "medium", "task": "Implement mail forwarding"}
            ]
        
        result.tutorial_sections = tutorial_sections
        
        # Record agent contributions
        for agent_id in agents:
            if agent_id == "a":
                result.agent_contributions["a"] = {
                    "role": "code_analysis",
                    "api_mapped": True
                }
            elif agent_id == "p":
                result.agent_contributions["p"] = {
                    "role": "tutorial_writing",
                    "sections_written": list(tutorial_sections.keys())
                }
            elif agent_id == "e":
                result.agent_contributions["e"] = {
                    "role": "example_generation",
                    "examples_created": len(tutorial_sections["steps"])
                }
    
    async def _generate_migration_guide(
        self,
        agents: List[str],
        target: Dict[str, Any],
        config: 'DocumentationConfig',
        result: DocumentationResult
    ) -> None:
        """Generate migration guide."""
        result.from_version = target.get("from_version", "1.0")
        result.to_version = target.get("to_version", "2.0")
        
        # Simulate breaking changes detection
        result.breaking_changes = [
            {
                "component": "MailSystem",
                "change": "send_mail() now requires priority parameter",
                "impact": "high",
                "migration": "Add priority=MessagePriority.NORMAL to all calls"
            },
            {
                "component": "AgentSession",
                "change": "create_session() renamed to create_agent_session()",
                "impact": "medium",
                "migration": "Update all method calls"
            }
        ]
        
        result.migration_steps = [
            "1. Update all send_mail() calls to include priority",
            "2. Rename create_session() to create_agent_session()",
            "3. Run migration validation script",
            "4. Test all agent communications"
        ]
        
        if config.generate_migration_scripts:
            result.migration_scripts = [
                {
                    "name": "update_mail_calls.py",
                    "description": "Updates send_mail() calls",
                    "content": "# Migration script content..."
                }
            ]
            result.scripts_generated = True
        
        # Record agent contributions
        for agent_id in agents:
            if agent_id == "a":
                result.agent_contributions["a"] = {
                    "role": "change_analysis",
                    "breaking_changes_found": len(result.breaking_changes)
                }
            elif agent_id == "p":
                result.agent_contributions["p"] = {
                    "role": "guide_writing",
                    "sections": ["overview", "breaking_changes", "migration_steps"]
                }
            elif agent_id == "d":
                result.agent_contributions["d"] = {
                    "role": "migration_testing",
                    "test_scenarios": 5
                }
    
    async def _generate_technical_documentation(
        self,
        agents: List[str],
        target: Dict[str, Any],
        result: DocumentationResult
    ) -> None:
        """Generate technical documentation."""
        result.sections_generated = ["technical_overview", "implementation_details", "api_reference"]
        
        for agent_id in agents:
            if agent_id == "a":
                result.agent_contributions["a"] = {
                    "role": "technical_analysis",
                    "complexity_assessed": True
                }
            elif agent_id == "p":
                result.agent_contributions["p"] = {
                    "role": "technical_writing",
                    "sections_written": result.sections_generated
                }
            elif agent_id == "t":
                result.agent_contributions["t"] = {
                    "role": "review_preparation",
                    "focus_areas": ["technical_accuracy", "completeness"]
                }
    
    async def _conduct_review(
        self,
        agents: List[str],
        result: DocumentationResult,
        iterations: int,
        config: 'DocumentationConfig'
    ) -> None:
        """Conduct documentation review."""
        result.review_performed = True
        
        for i in range(iterations):
            review_round = {
                "iteration": i + 1,
                "reviewer": "t",
                "timestamp": datetime.now(),
                "feedback": [
                    f"Round {i+1}: Check section completeness",
                    f"Round {i+1}: Verify code examples"
                ],
                "improvements": [
                    f"Added clarification to section {i+1}",
                    f"Updated example {i+1}"
                ]
            }
            result.review_history.append(review_round)
        
        result.review_iterations_completed = iterations
        result.feedback_incorporated = config.incorporate_feedback
    
    async def _generate_multi_format_output(
        self,
        result: DocumentationResult,
        formats: List[str],
        style_guide: str
    ) -> None:
        """Generate documentation in multiple formats."""
        for fmt in formats:
            output_file = {
                "format": fmt,
                "path": f"docs/output.{fmt}",
                "size": 1024 * (10 if fmt == "pdf" else 5),
                "generated_at": datetime.now().isoformat()
            }
            result.output_files.append(output_file)
        
        if style_guide:
            result.style_guide_applied = style_guide
    
    async def _check_existing_documentation(
        self,
        agents: List[str],
        target: Dict[str, Any],
        result: DocumentationResult
    ) -> None:
        """Check for outdated documentation."""
        # Simulate finding outdated sections
        result.outdated_sections = [
            {
                "name": "api_reference",
                "reason": "New methods added",
                "last_updated": "2024-01-01",
                "changes_detected": ["new_method_1", "new_method_2"]
            },
            {
                "name": "examples",
                "reason": "API changes",
                "last_updated": "2024-02-01",
                "changes_detected": ["updated_usage_pattern"]
            }
        ]
        
        result.update_recommendations = [
            "Update API reference with new methods",
            "Revise examples to match current API",
            "Add migration notes for breaking changes"
        ]
    
    async def _run_batch_documentation(
        self,
        config: Dict[str, Any],
        session_manager: AsyncAgentSessionManager,
        result: DocumentationResult
    ) -> Dict[str, Any]:
        """Run batch documentation for multiple targets."""
        targets = config.get("targets", [])
        agents = config.get("agents", ["a", "p"])
        
        result.targets_processed = len(targets)
        
        # Process each target
        for target in targets:
            target_result = {
                "name": target.get("name", "Unknown"),
                "type": target.get("type", "module"),
                "status": "completed",
                "sections": ["api_reference", "examples"]
            }
            result.documentation_results.append(target_result)
        
        # Simulate consistency checking
        if config.get("consistent_style", False):
            result.style_consistency_score = 0.85
        
        if config.get("parallel_generation", False):
            # Faster when parallel
            await asyncio.sleep(1)
        else:
            await asyncio.sleep(2)
        
        result.cross_references_generated = True
        result.status = "completed"
        result.end_time = datetime.now()
        return result.to_dict()
    
    async def _analyze_code(self, target: Dict[str, Any], result: DocumentationResult) -> Dict[str, Any]:
        """Analyze code for documentation."""
        return {
            "classes_found": 10,
            "methods_found": 50,
            "complexity": "medium",
            "documentation_coverage": 0.7
        }
    
    def _parse_configuration(self, config: Dict[str, Any]) -> 'DocumentationConfig':
        """Parse and validate configuration."""
        return DocumentationConfig(
            target=config.get("target", {}),
            agents=config.get("agents", ["a", "p"]),
            doc_type=config.get("doc_type", "api"),
            include_examples=config.get("include_examples", False),
            include_tests=config.get("include_tests", False),
            review_enabled=config.get("review_enabled", False),
            review_iterations=config.get("review_iterations", 1),
            output_formats=config.get("output_formats", ["markdown"]),
            style_guide=config.get("style_guide", ""),
            simulate_failures=config.get("simulate_failures", {}),
            tutorial_config=config.get("tutorial_config", {}),
            check_existing=config.get("check_existing", False),
            update_mode=config.get("update_mode", "manual"),
            fallback_to_partial=config.get("fallback_to_partial", False),
            incorporate_feedback=config.get("incorporate_feedback", False),
            analyze_breaking_changes=config.get("analyze_breaking_changes", False),
            generate_migration_scripts=config.get("generate_migration_scripts", False)
        )
    
    def _populate_result_metadata(self, result: DocumentationResult, config: 'DocumentationConfig') -> None:
        """Populate result with initial metadata."""
        result.target_name = config.target.get("name", "Unknown")
        result.target_type = config.target.get("type", "module")
        result.doc_type = config.doc_type
    
    async def _create_agent_sessions(
        self,
        agents: List[str],
        session_manager: AsyncAgentSessionManager,
        result: DocumentationResult,
        simulate_failures: Dict[str, str]
    ) -> None:
        """Create agent sessions with error handling."""
        if not hasattr(session_manager, 'create_agent_session'):
            return
            
        for agent_id in agents:
            if agent_id in simulate_failures:
                result.add_error("agent_failure", f"Agent {agent_id} failed", agent=agent_id)
                continue
            
            try:
                session = await session_manager.create_agent_session(agent_id, auto_start=True)
                logger.info(f"Created agent session for {agent_id}")
            except Exception as e:
                logger.error(f"Failed to create agent {agent_id}: {e}")
                result.add_error("creation_error", str(e), agent=agent_id)
    
    async def _generate_documentation(
        self,
        config: 'DocumentationConfig',
        result: DocumentationResult
    ) -> None:
        """Generate documentation based on type."""
        generation_methods = {
            "api": self._generate_api_documentation,
            "comprehensive": self._generate_comprehensive_documentation,
            "tutorial": self._generate_tutorial_documentation,
            "migration": self._generate_migration_guide,
            "technical": self._generate_technical_documentation
        }
        
        method = generation_methods.get(config.doc_type)
        if method:
            if config.doc_type == "comprehensive":
                await method(
                    config.agents, config.target, result,
                    config.include_examples, config.include_tests, config.review_enabled
                )
            elif config.doc_type in ["tutorial", "migration"]:
                await method(config.agents, config.target, config, result)
            else:
                await method(config.agents, config.target, result)
    
    async def _perform_post_processing(
        self,
        config: 'DocumentationConfig',
        result: DocumentationResult
    ) -> None:
        """Perform post-processing steps."""
        # Review process if enabled
        if config.review_enabled and "t" in config.agents:
            await self._conduct_review(
                config.agents, result, config.review_iterations, config
            )
        
        # Generate multiple output formats
        if len(config.output_formats) > 1:
            await self._generate_multi_format_output(
                result, config.output_formats, config.style_guide
            )
        
        # Check for outdated documentation
        if config.check_existing:
            await self._check_existing_documentation(
                config.agents, config.target, result
            )
    
    def _determine_final_status(self, result: DocumentationResult, fallback_to_partial: bool) -> str:
        """Determine final workflow status."""
        if result.errors and not fallback_to_partial:
            return "failed"
        elif result.errors and fallback_to_partial:
            result.partial_documentation = True
            if "a" in [e.get("agent") for e in result.errors if "agent" in e]:
                result.limitations.append("missing_analysis")
            result.confidence_level = "low"
            return "completed_with_limitations"
        else:
            return "completed"