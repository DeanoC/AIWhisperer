"""
Workspace Validator Tool for Debbie the Debugger.
Validates AIWhisperer workspace health, configuration, and dependencies.
"""

import os
import json
import yaml
import logging
from typing import Dict, Any, List, Optional, Tuple
from pathlib import Path
from datetime import datetime
from dataclasses import dataclass, field, asdict
from enum import Enum

from .base_tool import AITool
from ..logging_custom import EnhancedLogMessage, LogLevel, LogSource, ComponentType

logger = logging.getLogger(__name__)


class ValidationStatus(Enum):
    """Status levels for validation checks"""
    PASS = "pass"
    WARNING = "warning"
    FAIL = "fail"
    INFO = "info"


class CheckCategory(Enum):
    """Categories of validation checks"""
    STRUCTURE = "structure"
    CONFIGURATION = "configuration"
    DEPENDENCIES = "dependencies"
    PERMISSIONS = "permissions"
    INTEGRATION = "integration"


@dataclass
class ValidationCheck:
    """Individual validation check result"""
    name: str
    category: CheckCategory
    status: ValidationStatus
    message: str
    details: Optional[Dict[str, Any]] = None
    recommendation: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data['category'] = self.category.value
        data['status'] = self.status.value
        return data


@dataclass
class WorkspaceHealth:
    """Overall workspace health report"""
    workspace_path: str
    timestamp: datetime
    overall_status: ValidationStatus
    checks: List[ValidationCheck] = field(default_factory=list)
    summary: Dict[str, int] = field(default_factory=dict)
    recommendations: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'workspace_path': self.workspace_path,
            'timestamp': self.timestamp.isoformat(),
            'overall_status': self.overall_status.value,
            'checks': [c.to_dict() for c in self.checks],
            'summary': self.summary,
            'recommendations': self.recommendations
        }
    
    def to_markdown(self) -> str:
        """Generate markdown report"""
        md = f"# Workspace Health Report\n\n"
        md += f"**Workspace:** `{self.workspace_path}`\n"
        md += f"**Generated:** {self.timestamp.strftime('%Y-%m-%d %H:%M:%S')}\n"
        md += f"**Overall Status:** {self.overall_status.value.upper()}\n\n"
        
        # Summary
        md += "## Summary\n"
        for status, count in self.summary.items():
            md += f"- {status}: {count}\n"
        md += "\n"
        
        # Checks by category
        md += "## Detailed Checks\n"
        for category in CheckCategory:
            category_checks = [c for c in self.checks if c.category == category]
            if category_checks:
                md += f"\n### {category.value.title()}\n"
                for check in category_checks:
                    icon = self._get_status_icon(check.status)
                    md += f"- {icon} **{check.name}**: {check.message}\n"
                    if check.recommendation:
                        md += f"  - *Recommendation:* {check.recommendation}\n"
        
        # Recommendations
        if self.recommendations:
            md += "\n## Recommendations\n"
            for i, rec in enumerate(self.recommendations, 1):
                md += f"{i}. {rec}\n"
        
        return md
    
    def _get_status_icon(self, status: ValidationStatus) -> str:
        icons = {
            ValidationStatus.PASS: "✅",
            ValidationStatus.WARNING: "⚠️",
            ValidationStatus.FAIL: "❌",
            ValidationStatus.INFO: "ℹ️"
        }
        return icons.get(status, "•")


class WorkspaceValidatorTool(AITool):
    """
    Validates AIWhisperer workspace structure, configuration, and health.
    """
    
    def __init__(self, workspace_path: Optional[str] = None):
        """
        Initialize with optional workspace path.
        
        Args:
            workspace_path: Path to workspace root (auto-detected if None)
        """
        self.workspace_path = workspace_path or self._find_workspace()
        
    @property
    def name(self) -> str:
        return "workspace_validator"
    
    @property
    def description(self) -> str:
        return "Validates AIWhisperer workspace health, configuration, and dependencies"
    
    @property
    def parameters_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "workspace_path": {
                    "type": "string",
                    "description": "Path to workspace root. Uses current workspace if not specified."
                },
                "categories": {
                    "type": "array",
                    "items": {
                        "type": "string",
                        "enum": ["structure", "configuration", "dependencies", "permissions", "integration"]
                    },
                    "description": "Specific categories to check. Checks all if not specified."
                },
                "generate_report": {
                    "type": "boolean",
                    "description": "Whether to generate a markdown report file",
                    "default": True
                },
                "report_path": {
                    "type": "string",
                    "description": "Path for the markdown report. Auto-generated if not specified."
                }
            }
        }
    
    @property
    def category(self) -> Optional[str]:
        return "Debugging"
    
    @property
    def tags(self) -> List[str]:
        return ["debugging", "validation", "workspace", "health", "configuration"]
    
    def get_ai_prompt_instructions(self) -> str:
        return """
        Use the workspace_validator tool to:
        - Check if the AIWhisperer workspace is properly configured
        - Validate that all required files and directories exist
        - Verify API keys and configuration settings
        - Test agent registrations and tool availability
        - Generate health reports for debugging
        
        Examples:
        - workspace_validator() - Full validation of current workspace
        - workspace_validator(categories=["configuration"]) - Check only configuration
        - workspace_validator(generate_report=true, report_path="health_report.md")
        
        The tool checks:
        - .WHISPER folder structure
        - Configuration files (config.yaml, agents.yaml, etc.)
        - API key presence and format
        - Python dependencies
        - File permissions
        - Agent and tool registrations
        """
    
    def execute(self, workspace_path: Optional[str] = None,
                categories: Optional[List[str]] = None,
                generate_report: bool = True,
                report_path: Optional[str] = None) -> Dict[str, Any]:
        """
        Validate the workspace and generate health report.
        
        Args:
            workspace_path: Override workspace path
            categories: Specific categories to check
            generate_report: Whether to save markdown report
            report_path: Custom report path
            
        Returns:
            Validation results with health status
        """
        try:
            # Use provided path or default
            ws_path = workspace_path or self.workspace_path
            if not ws_path:
                return {"error": "No workspace path found"}
            
            # Parse categories
            if categories:
                check_categories = []
                for cat in categories:
                    try:
                        check_categories.append(CheckCategory(cat))
                    except ValueError:
                        return {"error": f"Invalid category: {cat}"}
            else:
                check_categories = list(CheckCategory)
            
            # Create health report
            health = WorkspaceHealth(
                workspace_path=ws_path,
                timestamp=datetime.now(),
                overall_status=ValidationStatus.PASS
            )
            
            # Run checks
            self._run_checks(health, check_categories)
            
            # Calculate summary and overall status
            self._calculate_summary(health)
            
            # Generate recommendations
            self._generate_recommendations(health)
            
            # Save report if requested
            if generate_report:
                if not report_path:
                    report_path = os.path.join(
                        ws_path, 
                        f"workspace_health_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
                    )
                self._save_report(health, report_path)
            
            # Log validation
            self._log_validation(health)
            
            return {
                "health": health.to_dict(),
                "report_path": report_path if generate_report else None,
                "success": True
            }
            
        except Exception as e:
            logger.error(f"Error validating workspace: {e}")
            return {
                "error": str(e),
                "success": False
            }
    
    def _find_workspace(self) -> Optional[str]:
        """Find workspace by looking for .WHISPER directory"""
        current = Path.cwd()
        
        while current != current.parent:
            whisper_path = current / ".WHISPER"
            if whisper_path.exists() and whisper_path.is_dir():
                return str(current)
            current = current.parent
        
        return None
    
    def _run_checks(self, health: WorkspaceHealth, categories: List[CheckCategory]):
        """Run all validation checks"""
        check_methods = {
            CheckCategory.STRUCTURE: self._check_structure,
            CheckCategory.CONFIGURATION: self._check_configuration,
            CheckCategory.DEPENDENCIES: self._check_dependencies,
            CheckCategory.PERMISSIONS: self._check_permissions,
            CheckCategory.INTEGRATION: self._check_integration
        }
        
        for category in categories:
            if category in check_methods:
                check_methods[category](health)
    
    def _check_structure(self, health: WorkspaceHealth):
        """Check workspace directory structure"""
        ws_path = Path(health.workspace_path)
        
        # Check .WHISPER directory
        whisper_path = ws_path / ".WHISPER"
        if not whisper_path.exists():
            health.checks.append(ValidationCheck(
                name=".WHISPER directory",
                category=CheckCategory.STRUCTURE,
                status=ValidationStatus.FAIL,
                message=".WHISPER directory not found",
                recommendation="Run 'aiwhisperer init' to initialize workspace"
            ))
        else:
            health.checks.append(ValidationCheck(
                name=".WHISPER directory",
                category=CheckCategory.STRUCTURE,
                status=ValidationStatus.PASS,
                message=".WHISPER directory exists"
            ))
            
            # Check subdirectories
            expected_dirs = ["logs", "state", "output"]
            for dir_name in expected_dirs:
                dir_path = whisper_path / dir_name
                if not dir_path.exists():
                    health.checks.append(ValidationCheck(
                        name=f".WHISPER/{dir_name}",
                        category=CheckCategory.STRUCTURE,
                        status=ValidationStatus.WARNING,
                        message=f"Directory .WHISPER/{dir_name} not found",
                        recommendation=f"Create directory: mkdir -p {dir_path}"
                    ))
        
        # Check key project directories
        project_dirs = {
            "ai_whisperer": "Core package directory",
            "prompts": "Prompt templates",
            "tests": "Test suite",
            "docs": "Documentation"
        }
        
        for dir_name, description in project_dirs.items():
            dir_path = ws_path / dir_name
            if not dir_path.exists():
                health.checks.append(ValidationCheck(
                    name=f"{dir_name} directory",
                    category=CheckCategory.STRUCTURE,
                    status=ValidationStatus.WARNING,
                    message=f"{description} directory not found"
                ))
            else:
                health.checks.append(ValidationCheck(
                    name=f"{dir_name} directory",
                    category=CheckCategory.STRUCTURE,
                    status=ValidationStatus.PASS,
                    message=f"{description} directory exists"
                ))
    
    def _check_configuration(self, health: WorkspaceHealth):
        """Check configuration files"""
        ws_path = Path(health.workspace_path)
        
        # Check config.yaml
        config_path = ws_path / "config.yaml"
        if not config_path.exists():
            health.checks.append(ValidationCheck(
                name="config.yaml",
                category=CheckCategory.CONFIGURATION,
                status=ValidationStatus.FAIL,
                message="Main configuration file not found",
                recommendation="Copy config.yaml.example to config.yaml"
            ))
        else:
            # Validate config content
            try:
                with open(config_path) as f:
                    config = yaml.safe_load(f)
                
                # Check for API key
                api_key = os.environ.get('OPENROUTER_API_KEY') or config.get('openrouter_api_key')
                if not api_key:
                    health.checks.append(ValidationCheck(
                        name="API Key",
                        category=CheckCategory.CONFIGURATION,
                        status=ValidationStatus.FAIL,
                        message="OPENROUTER_API_KEY not found",
                        recommendation="Set OPENROUTER_API_KEY environment variable"
                    ))
                else:
                    health.checks.append(ValidationCheck(
                        name="API Key",
                        category=CheckCategory.CONFIGURATION,
                        status=ValidationStatus.PASS,
                        message="API key configured"
                    ))
                
                # Check model configuration
                if 'model' not in config:
                    health.checks.append(ValidationCheck(
                        name="Model Configuration",
                        category=CheckCategory.CONFIGURATION,
                        status=ValidationStatus.WARNING,
                        message="No model specified in config",
                        recommendation="Add 'model' field to config.yaml"
                    ))
                    
            except Exception as e:
                health.checks.append(ValidationCheck(
                    name="config.yaml",
                    category=CheckCategory.CONFIGURATION,
                    status=ValidationStatus.FAIL,
                    message=f"Error reading config.yaml: {e}",
                    recommendation="Fix syntax errors in config.yaml"
                ))
        
        # Check agents.yaml
        agents_path = ws_path / "ai_whisperer" / "agents" / "config" / "agents.yaml"
        if not agents_path.exists():
            health.checks.append(ValidationCheck(
                name="agents.yaml",
                category=CheckCategory.CONFIGURATION,
                status=ValidationStatus.FAIL,
                message="Agent configuration not found"
            ))
        else:
            try:
                with open(agents_path) as f:
                    agents = yaml.safe_load(f)
                
                # Check for Debbie
                if 'agents' in agents and 'd' in agents['agents']:
                    health.checks.append(ValidationCheck(
                        name="Debbie Agent",
                        category=CheckCategory.CONFIGURATION,
                        status=ValidationStatus.PASS,
                        message="Debbie the Debugger is configured"
                    ))
                else:
                    health.checks.append(ValidationCheck(
                        name="Debbie Agent",
                        category=CheckCategory.CONFIGURATION,
                        status=ValidationStatus.WARNING,
                        message="Debbie not found in agent configuration"
                    ))
                    
            except Exception as e:
                health.checks.append(ValidationCheck(
                    name="agents.yaml",
                    category=CheckCategory.CONFIGURATION,
                    status=ValidationStatus.FAIL,
                    message=f"Error reading agents.yaml: {e}"
                ))
    
    def _check_dependencies(self, health: WorkspaceHealth):
        """Check Python dependencies"""
        ws_path = Path(health.workspace_path)
        
        # Check requirements.txt
        req_path = ws_path / "requirements.txt"
        if not req_path.exists():
            health.checks.append(ValidationCheck(
                name="requirements.txt",
                category=CheckCategory.DEPENDENCIES,
                status=ValidationStatus.WARNING,
                message="Requirements file not found"
            ))
        else:
            health.checks.append(ValidationCheck(
                name="requirements.txt",
                category=CheckCategory.DEPENDENCIES,
                status=ValidationStatus.PASS,
                message="Requirements file exists"
            ))
        
        # Check critical imports
        critical_packages = {
            'fastapi': "Web framework for interactive server",
            'websockets': "WebSocket support",
            'pydantic': "Data validation",
            'yaml': "Configuration parsing"
        }
        
        for package, description in critical_packages.items():
            try:
                __import__(package)
                health.checks.append(ValidationCheck(
                    name=f"{package} module",
                    category=CheckCategory.DEPENDENCIES,
                    status=ValidationStatus.PASS,
                    message=f"{description} is available"
                ))
            except ImportError:
                health.checks.append(ValidationCheck(
                    name=f"{package} module",
                    category=CheckCategory.DEPENDENCIES,
                    status=ValidationStatus.FAIL,
                    message=f"{description} not installed",
                    recommendation=f"pip install {package}"
                ))
    
    def _check_permissions(self, health: WorkspaceHealth):
        """Check file permissions"""
        ws_path = Path(health.workspace_path)
        whisper_path = ws_path / ".WHISPER"
        
        if whisper_path.exists():
            # Check write permissions
            test_file = whisper_path / ".permission_test"
            try:
                test_file.touch()
                test_file.unlink()
                health.checks.append(ValidationCheck(
                    name="Write permissions",
                    category=CheckCategory.PERMISSIONS,
                    status=ValidationStatus.PASS,
                    message="Can write to .WHISPER directory"
                ))
            except Exception as e:
                health.checks.append(ValidationCheck(
                    name="Write permissions",
                    category=CheckCategory.PERMISSIONS,
                    status=ValidationStatus.FAIL,
                    message="Cannot write to .WHISPER directory",
                    recommendation="Check directory permissions"
                ))
        
        # Check log directory
        log_dir = ws_path / "logs"
        if log_dir.exists():
            if os.access(log_dir, os.W_OK):
                health.checks.append(ValidationCheck(
                    name="Log directory",
                    category=CheckCategory.PERMISSIONS,
                    status=ValidationStatus.PASS,
                    message="Log directory is writable"
                ))
            else:
                health.checks.append(ValidationCheck(
                    name="Log directory",
                    category=CheckCategory.PERMISSIONS,
                    status=ValidationStatus.WARNING,
                    message="Log directory not writable",
                    recommendation="chmod 755 logs/"
                ))
    
    def _check_integration(self, health: WorkspaceHealth):
        """Check integration points"""
        ws_path = Path(health.workspace_path)
        
        # Check if batch mode files exist
        batch_files = [
            "ai_whisperer/batch/__init__.py",
            "ai_whisperer/batch/batch_client.py",
            "ai_whisperer/batch/server_manager.py"
        ]
        
        all_batch_files_exist = True
        for file_path in batch_files:
            full_path = ws_path / file_path
            if not full_path.exists():
                all_batch_files_exist = False
                break
        
        if all_batch_files_exist:
            health.checks.append(ValidationCheck(
                name="Batch mode",
                category=CheckCategory.INTEGRATION,
                status=ValidationStatus.PASS,
                message="Batch mode components installed"
            ))
        else:
            health.checks.append(ValidationCheck(
                name="Batch mode",
                category=CheckCategory.INTEGRATION,
                status=ValidationStatus.WARNING,
                message="Batch mode components incomplete"
            ))
        
        # Check debugging tools
        debug_tools = [
            "ai_whisperer/tools/session_inspector_tool.py",
            "ai_whisperer/tools/message_injector_tool.py",
            "ai_whisperer/tools/workspace_validator_tool.py"
        ]
        
        for tool_path in debug_tools:
            full_path = ws_path / tool_path
            tool_name = Path(tool_path).stem.replace('_tool', '')
            if full_path.exists():
                health.checks.append(ValidationCheck(
                    name=f"{tool_name} tool",
                    category=CheckCategory.INTEGRATION,
                    status=ValidationStatus.PASS,
                    message=f"Debugging tool {tool_name} available"
                ))
            else:
                health.checks.append(ValidationCheck(
                    name=f"{tool_name} tool",
                    category=CheckCategory.INTEGRATION,
                    status=ValidationStatus.INFO,
                    message=f"Debugging tool {tool_name} not yet implemented"
                ))
    
    def _calculate_summary(self, health: WorkspaceHealth):
        """Calculate summary statistics"""
        health.summary = {
            "pass": 0,
            "warning": 0,
            "fail": 0,
            "info": 0
        }
        
        for check in health.checks:
            health.summary[check.status.value] += 1
        
        # Determine overall status
        if health.summary["fail"] > 0:
            health.overall_status = ValidationStatus.FAIL
        elif health.summary["warning"] > 0:
            health.overall_status = ValidationStatus.WARNING
        else:
            health.overall_status = ValidationStatus.PASS
    
    def _generate_recommendations(self, health: WorkspaceHealth):
        """Generate overall recommendations"""
        if health.overall_status == ValidationStatus.FAIL:
            health.recommendations.append(
                "Critical issues found. Address failing checks before proceeding."
            )
        
        # Check-specific recommendations
        failed_checks = [c for c in health.checks if c.status == ValidationStatus.FAIL]
        if any(c.category == CheckCategory.CONFIGURATION for c in failed_checks):
            health.recommendations.append(
                "Fix configuration issues to ensure AIWhisperer can run properly."
            )
        
        if any(c.category == CheckCategory.DEPENDENCIES for c in failed_checks):
            health.recommendations.append(
                "Install missing dependencies: pip install -r requirements.txt"
            )
        
        # Add any individual recommendations
        for check in health.checks:
            if check.recommendation and check.recommendation not in health.recommendations:
                health.recommendations.append(check.recommendation)
    
    def _save_report(self, health: WorkspaceHealth, report_path: str):
        """Save markdown report to file"""
        try:
            with open(report_path, 'w') as f:
                f.write(health.to_markdown())
            logger.info(f"Health report saved to: {report_path}")
        except Exception as e:
            logger.error(f"Failed to save report: {e}")
    
    def _log_validation(self, health: WorkspaceHealth):
        """Log validation results"""
        log_msg = EnhancedLogMessage(
            level=LogLevel.INFO,
            component=ComponentType.MONITOR,
            source=LogSource.DEBBIE,
            action="workspace_validated",
            event_summary=f"Workspace validation: {health.overall_status.value} ({health.summary})",
            details={
                "overall_status": health.overall_status.value,
                "summary": health.summary,
                "workspace_path": health.workspace_path
            }
        )
        logger.info(log_msg.event_summary, extra=log_msg.to_dict())