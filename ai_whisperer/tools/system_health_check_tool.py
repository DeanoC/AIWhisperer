"""
Module: ai_whisperer/tools/system_health_check_tool.py
Purpose: AI tool implementation for system health check

This module implements an AI-usable tool that extends the AITool
base class. It provides structured input/output handling and
integrates with the OpenRouter API for AI model interactions.

Key Components:
- SystemHealthCheckTool: 

Usage:
    tool = SystemHealthCheckTool()
    result = await tool.execute(**parameters)

Dependencies:
- logging
- subprocess
- asyncio

Related:
- See UNTESTED_MODULES_REPORT.md
- See TEST_CONSOLIDATED_SUMMARY.md

"""

import asyncio
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime
import logging

from ai_whisperer.tools.base_tool import AITool

logger = logging.getLogger(__name__)

class SystemHealthCheckTool(AITool):
    """
    Runs system health check scripts from a designated folder to verify
    AIWhisperer components are working correctly.
    """
    
    @property
    def name(self) -> str:
        return "system_health_check"
        
    @property
    def description(self) -> str:
        return "Run comprehensive system health checks including agent verification, tool testing, and AI provider validation"
    
    @property
    def parameters_schema(self) -> Dict[str, Any]:
        """Schema for tool parameters."""
        return {
            "type": "object",
            "properties": {
                "check_category": {
                    "type": "string",
                    "description": "Category of checks to run (all, agents, tools, providers, custom)",
                    "enum": ["all", "agents", "tools", "providers", "custom"],
                    "default": "all"
                },
                "specific_checks": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Specific check scripts to run (if not running all)"
                },
                "timeout_per_check": {
                    "type": "integer",
                    "description": "Timeout in seconds for each check script",
                    "default": 30
                },
                "verbose": {
                    "type": "boolean",
                    "description": "Include detailed output from each check",
                    "default": False
                }
            },
            "required": [],
            "additionalProperties": False
        }
    
    def get_ai_prompt_instructions(self) -> str:
        """Instructions for AI on using this tool."""
        return """
        Use the system_health_check tool to verify AIWhisperer components are working correctly.
        You can:
        - Run all checks with default settings
        - Filter by category: agents, tools, providers, or custom
        - Run specific named checks
        - Set a custom timeout per check (default 30s)
        - Enable verbose output for detailed diagnostics
        
        Examples:
        - Check everything: execute()
        - Check only agents: execute(check_category="agents")
        - Run specific checks: execute(specific_checks=["test_agent_alice", "test_openrouter"])
        - Verbose output: execute(verbose=True)
        """
        
    def get_openrouter_tool_definition(self) -> dict:
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.parameters_schema
            }
        }
    
    async def execute(
        self,
        check_category: str = "all",
        specific_checks: Optional[List[str]] = None,
        timeout_per_check: int = 30,
        verbose: bool = False
    ) -> str:
        """Execute system health checks"""
        try:
            # Find health check scripts directory
            health_check_dirs = self._find_health_check_directories()
            if not health_check_dirs:
                return self._format_error("No health check directories found. Expected: scripts/debbie/system_health_check/")
            
            # Collect all check scripts
            all_checks = self._collect_check_scripts(health_check_dirs, check_category, specific_checks)
            if not all_checks:
                return self._format_error(f"No health check scripts found for category: {check_category}")
            
            # Run health checks using conversation command runner
            results = await self._run_health_checks(all_checks, timeout_per_check, verbose)
            
            # Generate report
            return self._generate_health_report(results, verbose)
            
        except Exception as e:
            logger.error(f"System health check failed: {e}")
            return self._format_error(f"Health check error: {str(e)}")
    
    def _find_health_check_directories(self) -> List[Path]:
        """Find all directories containing health check scripts"""
        dirs = []
        
        # Check common locations
        possible_paths = [
            Path("scripts/debbie/system_health_check"),
            Path(".WHISPER/scripts/system_health_check"),
            Path("tests/health_checks"),
            Path("tests/debugging-tools/debbie/system_health_check"),
        ]
        
        # Also check from PathManager paths if available
        try:
            from ai_whisperer.utils.path import PathManager
            pm = PathManager.get_instance()
            if pm._initialized:
                possible_paths.extend([
                    pm.workspace_path / "scripts" / "debbie" / "system_health_check",
                    pm.project_path / "scripts" / "debbie" / "system_health_check",
                    pm.project_path / "tests" / "debugging-tools" / "debbie" / "system_health_check",
                ])
        except:
            pass
        
        # Use a set to deduplicate resolved paths
        seen_paths = set()
        
        for path in possible_paths:
            resolved_path = path.resolve()
            if resolved_path.exists() and resolved_path.is_dir():
                if resolved_path not in seen_paths:
                    dirs.append(resolved_path)
                    seen_paths.add(resolved_path)
                    logger.info(f"Found health check directory: {resolved_path}")
        
        return dirs
    
    def _collect_check_scripts(
        self, 
        directories: List[Path], 
        category: str,
        specific_checks: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """Collect all relevant check scripts"""
        checks = []
        
        # Supported batch script formats
        batch_extensions = ['.json', '.yaml', '.yml', '.txt']
        
        for directory in directories:
            # If specific checks requested, only look for those
            if specific_checks:
                for check_name in specific_checks:
                    for ext in batch_extensions:
                        script_path = directory / f"{check_name}{ext}"
                        if script_path.exists():
                            checks.append({
                                'name': check_name,
                                'path': script_path,
                                'category': self._detect_category(script_path),
                                'format': ext[1:]
                            })
                            break
            else:
                # Collect all batch scripts in category
                for script_path in directory.iterdir():
                    if script_path.is_file() and script_path.suffix in batch_extensions:
                        script_category = self._detect_category(script_path)
                        if category == "all" or script_category == category:
                            checks.append({
                                'name': script_path.stem,
                                'path': script_path,
                                'category': script_category,
                                'format': script_path.suffix[1:]
                            })
        
        # Sort by category and name for consistent ordering
        checks.sort(key=lambda x: (x['category'], x['name']))
        return checks
    
    def _detect_category(self, script_path: Path) -> str:
        """Detect category from script name or location"""
        name = script_path.stem.lower()
        
        if 'agent' in name:
            return 'agents'
        elif 'tool' in name:
            return 'tools'
        elif 'provider' in name or 'model' in name:
            return 'providers'
        else:
            return 'custom'
    
    async def _run_health_checks(
        self, 
        checks: List[Dict[str, Any]], 
        timeout: int,
        verbose: bool
    ) -> List[Dict[str, Any]]:
        """Run all health check scripts using conversation command runner"""
        results = []
        
        # Get conversation command tools
        try:
            from ai_whisperer.tools.tool_registry import get_tool_registry
            registry = get_tool_registry()
            
            conversation_tool = registry.get_tool_by_name('conversation_command')
            parser_tool = registry.get_tool_by_name('script_parser')
            
            if not conversation_tool or not parser_tool:
                logger.error("Conversation command tools not available")
                return [{
                    'name': 'conversation_tools',
                    'category': 'system',
                    'status': 'error',
                    'error': 'Conversation command tools not found',
                    'duration': 0
                }]
            
            # Set the tool registry on the conversation tool if it doesn't have it
            if hasattr(conversation_tool, 'tool_registry') and conversation_tool.tool_registry is None:
                conversation_tool.tool_registry = registry
        except Exception as e:
            logger.error(f"Failed to get conversation tools: {e}")
            return [{
                'name': 'conversation_tools',
                'category': 'system', 
                'status': 'error',
                'error': str(e),
                'duration': 0
            }]
        
        for check in checks:
            start_time = datetime.now()
            result = {
                'name': check['name'],
                'category': check['category'],
                'path': str(check['path']),
                'start_time': start_time.isoformat(),
                'status': 'pending',
                'output': '',
                'error': None,
                'duration': 0
            }
            
            try:
                logger.info(f"Running health check: {check['name']} ({check['format']})")
                
                # Parse the script directly using the parser tool's internal method
                try:
                    # Use the parser tool's parse_script method directly to get ParsedScript object
                    parsed_script = parser_tool.parse_script(str(check['path']))
                except Exception as parse_error:
                    result['status'] = 'error'
                    result['error'] = f"Failed to parse script: {str(parse_error)}"
                    results.append(result)
                    continue
                    
                # Run the parsed script
                conversation_result = conversation_tool.execute(
                    script=parsed_script,
                    dry_run=False,
                    stop_on_error=False,
                    pass_context=True
                )
                
                # Analyze results
                result['output'] = str(conversation_result)
                
                # Check for success indicators
                if isinstance(conversation_result, dict):
                    if conversation_result.get('success', False):
                        result['status'] = 'passed'
                    else:
                        result['status'] = 'failed'
                        result['error'] = conversation_result.get('error', 'Unknown error')
                elif 'error' in str(conversation_result).lower():
                    result['status'] = 'failed'
                    result['error'] = str(conversation_result)
                else:
                    # Assume success if no explicit error
                    result['status'] = 'passed'
                        
            except asyncio.TimeoutError:
                result['status'] = 'timeout'
                result['error'] = f"Check timed out after {timeout} seconds"
            except Exception as e:
                result['status'] = 'error'
                result['error'] = str(e)
                logger.error(f"Error running check {check['name']}: {e}")
            
            # Calculate duration
            end_time = datetime.now()
            result['duration'] = (end_time - start_time).total_seconds()
            result['end_time'] = end_time.isoformat()
            
            results.append(result)
            
            # Log result
            if result['status'] == 'passed':
                logger.info(f"✅ {check['name']}: PASSED ({result['duration']:.2f}s)")
            else:
                logger.warning(f"❌ {check['name']}: {result['status'].upper()} ({result['duration']:.2f}s)")
        
        return results
    
    def _generate_health_report(self, results: List[Dict[str, Any]], verbose: bool) -> str:
        """Generate a formatted health check report"""
        total = len(results)
        passed = sum(1 for r in results if r['status'] == 'passed')
        failed = sum(1 for r in results if r['status'] == 'failed')
        errors = sum(1 for r in results if r['status'] in ['error', 'timeout'])
        
        # Calculate health score
        health_score = int((passed / total * 100) if total > 0 else 0)
        
        # Determine overall status
        if health_score >= 90:
            status = "🟢 Healthy"
        elif health_score >= 70:
            status = "🟡 Fair"
        elif health_score >= 50:
            status = "🟠 Degraded"
        else:
            status = "🔴 Critical"
        
        # Build report
        report = f"""System Health Check Report
==========================
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Status: {status}
Health Score: {health_score}/100

Summary
-------
• Total Checks: {total}
• Passed: {passed} ✅
• Failed: {failed} ❌
• Errors/Timeouts: {errors} ⚠️
• Duration: {sum(r['duration'] for r in results):.2f}s

Results by Category
-------------------"""
        
        # Group results by category
        from itertools import groupby
        results_by_category = groupby(results, key=lambda x: x['category'])
        
        for category, category_results in results_by_category:
            category_results = list(category_results)
            category_passed = sum(1 for r in category_results if r['status'] == 'passed')
            category_total = len(category_results)
            
            report += f"\n\n{category.upper()} ({category_passed}/{category_total}):"
            
            for result in category_results:
                status_icon = {
                    'passed': '✅',
                    'failed': '❌',
                    'error': '⚠️',
                    'timeout': '⏱️'
                }.get(result['status'], '❓')
                
                report += f"\n  {status_icon} {result['name']} ({result['duration']:.2f}s)"
                
                if result['status'] != 'passed' and (verbose or result['status'] in ['error', 'timeout']):
                    if result['error']:
                        error_preview = result['error'].strip().split('\n')[0][:100]
                        report += f"\n     Error: {error_preview}"
        
        # Add critical failures section
        critical_failures = [r for r in results if r['status'] in ['failed', 'error', 'timeout']]
        if critical_failures:
            report += "\n\nCritical Issues"
            report += "\n---------------"
            for result in critical_failures[:5]:  # Show top 5
                report += f"\n• {result['name']}: {result['status'].upper()}"
                if result['error']:
                    report += f"\n  {result['error'].strip().split(chr(10))[0][:200]}"
        
        # Add recommendations
        report += "\n\nRecommendations"
        report += "\n---------------"
        if health_score < 50:
            report += "\n• ⚠️ CRITICAL: Multiple system components are failing"
            report += "\n• Check server logs for detailed error messages"
            report += "\n• Verify all dependencies are installed correctly"
            report += "\n• Consider restarting the server"
        elif health_score < 70:
            report += "\n• Several components need attention"
            report += "\n• Review failed checks and address issues"
            report += "\n• Monitor system performance closely"
        elif health_score < 90:
            report += "\n• System is functional but has some issues"
            report += "\n• Address failed checks when possible"
        else:
            report += "\n• System is healthy!"
            report += "\n• Continue regular monitoring"
        
        # Add verbose output if requested
        if verbose:
            report += "\n\nDetailed Output"
            report += "\n==============="
            for result in results:
                report += f"\n\n### {result['name']} ###"
                report += f"\nStatus: {result['status']}"
                report += f"\nDuration: {result['duration']:.2f}s"
                if result['output']:
                    report += f"\nOutput:\n{result['output'][:500]}"
                if result['error']:
                    report += f"\nError:\n{result['error'][:500]}"
        
        return report
    
    def _format_error(self, message: str) -> str:
        """Format an error message"""
        return f"❌ System Health Check Error\n\n{message}"
