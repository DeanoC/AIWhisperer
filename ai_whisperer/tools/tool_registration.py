"""
Module: ai_whisperer/tools/tool_registration.py
Purpose: Utility functions for tool registration

Centralized tool registration for AIWhisperer.
This module handles registering all available tools with the tool registry.

Key Components:
- register_all_tools(): 
- register_tool_category(): 

Usage:
    tool = Tool()
    result = await tool.execute(**parameters)

Dependencies:
- logging
- execute_command_tool
- move_rfc_tool

Related:
- See docs/dependency-analysis-report.md
- See docs/archive/consolidated_phase2/CODEBASE_ANALYSIS_REPORT.md

"""

import logging
from typing import Optional

from .tool_registry import get_tool_registry
from ai_whisperer.utils.path import PathManager

logger = logging.getLogger(__name__)


def register_all_tools(path_manager: Optional[PathManager] = None) -> None:
    """
    Register all available tools with the tool registry.
    
    Args:
        path_manager: Optional PathManager instance for tools that need it
    """
    tool_registry = get_tool_registry()
    
    # If no path_manager provided, create one
    if path_manager is None:
        path_manager = PathManager()
    
    # Register basic file operation tools
    _register_file_tools(tool_registry)
    
    # Register analysis tools
    _register_analysis_tools(tool_registry, path_manager)
    
    # Register RFC management tools
    _register_rfc_tools(tool_registry)
    
    # Register plan management tools
    _register_plan_tools(tool_registry)
    
    # Register codebase analysis tools
    _register_codebase_tools(tool_registry)
    
    # Register web research tools
    _register_web_tools(tool_registry)
    
    # Register debugging and monitoring tools
    _register_debugging_tools(tool_registry)
    
    # Register mailbox communication tools
    _register_mailbox_tools(tool_registry)
    
    # Register Agent E task decomposition tools
    _register_agent_e_tools(tool_registry)
    
    logger.info(f"Registered {len(tool_registry.get_all_tools())} tools")


def _register_file_tools(tool_registry) -> None:
    """Register basic file operation tools."""
    from .read_file_tool import ReadFileTool
    from .write_file_tool import WriteFileTool
    from .execute_command_tool import ExecuteCommandTool
    from .list_directory_tool import ListDirectoryTool
    from .search_files_tool import SearchFilesTool
    from .get_file_content_tool import GetFileContentTool
    
    tool_registry.register_tool(ReadFileTool())
    tool_registry.register_tool(WriteFileTool())
    tool_registry.register_tool(ExecuteCommandTool())
    tool_registry.register_tool(ListDirectoryTool())
    tool_registry.register_tool(SearchFilesTool())
    tool_registry.register_tool(GetFileContentTool())
    
    logger.debug("Registered file operation tools")


def _register_analysis_tools(tool_registry, path_manager: PathManager) -> None:
    """Register advanced analysis tools."""
    from .find_pattern_tool import FindPatternTool
    from .workspace_stats_tool import WorkspaceStatsTool
    
    tool_registry.register_tool(FindPatternTool(path_manager))
    tool_registry.register_tool(WorkspaceStatsTool(path_manager))
    
    logger.debug("Registered analysis tools")


def _register_rfc_tools(tool_registry) -> None:
    """Register RFC management tools."""
    from .create_rfc_tool import CreateRFCTool
    from .read_rfc_tool import ReadRFCTool
    from .list_rfcs_tool import ListRFCsTool
    from .update_rfc_tool import UpdateRFCTool
    from .move_rfc_tool import MoveRFCTool
    from .delete_rfc_tool import DeleteRFCTool
    
    tool_registry.register_tool(CreateRFCTool())
    tool_registry.register_tool(ReadRFCTool())
    tool_registry.register_tool(ListRFCsTool())
    tool_registry.register_tool(UpdateRFCTool())
    tool_registry.register_tool(MoveRFCTool())
    tool_registry.register_tool(DeleteRFCTool())
    
    logger.debug("Registered RFC tools")


def _register_plan_tools(tool_registry) -> None:
    """Register plan management tools."""
    from .prepare_plan_from_rfc_tool import PreparePlanFromRFCTool
    from .save_generated_plan_tool import SaveGeneratedPlanTool
    from .list_plans_tool import ListPlansTool
    from .read_plan_tool import ReadPlanTool
    from .update_plan_from_rfc_tool import UpdatePlanFromRFCTool
    from .move_plan_tool import MovePlanTool
    from .delete_plan_tool import DeletePlanTool
    
    tool_registry.register_tool(PreparePlanFromRFCTool())
    tool_registry.register_tool(SaveGeneratedPlanTool())
    tool_registry.register_tool(ListPlansTool())
    tool_registry.register_tool(ReadPlanTool())
    tool_registry.register_tool(UpdatePlanFromRFCTool())
    tool_registry.register_tool(MovePlanTool())
    tool_registry.register_tool(DeletePlanTool())
    
    logger.debug("Registered plan tools")


def _register_codebase_tools(tool_registry) -> None:
    """Register codebase analysis tools."""
    from .analyze_languages_tool import AnalyzeLanguagesTool
    from .find_similar_code_tool import FindSimilarCodeTool
    from .get_project_structure_tool import GetProjectStructureTool
    
    tool_registry.register_tool(AnalyzeLanguagesTool())
    tool_registry.register_tool(FindSimilarCodeTool())
    tool_registry.register_tool(GetProjectStructureTool())
    
    logger.debug("Registered codebase tools")


def _register_web_tools(tool_registry) -> None:
    """Register web research tools."""
    from .web_search_tool import WebSearchTool
    from .fetch_url_tool import FetchURLTool
    
    tool_registry.register_tool(WebSearchTool())
    tool_registry.register_tool(FetchURLTool())
    
    logger.debug("Registered web tools")


def _register_debugging_tools(tool_registry) -> None:
    """Register Debbie's debugging and monitoring tools."""
    try:
        from .session_health_tool import SessionHealthTool
        from .session_analysis_tool import SessionAnalysisTool
        from .monitoring_control_tool import MonitoringControlTool
        from .session_inspector_tool import SessionInspectorTool
        from .message_injector_tool import MessageInjectorTool
        from .workspace_validator_tool import WorkspaceValidatorTool
        from .python_executor_tool import PythonExecutorTool
        from .script_parser_tool import ScriptParserTool
        from .batch_command_tool import BatchCommandTool
        from .system_health_check_tool import SystemHealthCheckTool
        
        tool_registry.register_tool(SessionHealthTool())
        tool_registry.register_tool(SessionAnalysisTool())
        tool_registry.register_tool(MonitoringControlTool())
        tool_registry.register_tool(SessionInspectorTool())
        tool_registry.register_tool(MessageInjectorTool())
        tool_registry.register_tool(WorkspaceValidatorTool())
        tool_registry.register_tool(PythonExecutorTool())
        tool_registry.register_tool(ScriptParserTool())
        tool_registry.register_tool(BatchCommandTool(tool_registry))
        tool_registry.register_tool(SystemHealthCheckTool())
        
        logger.debug("Registered debugging tools")
    except ImportError as e:
        logger.warning(f"Some debugging tools not available: {e}")
    except Exception as e:
        logger.error(f"Failed to register debugging tools: {e}")


def _register_mailbox_tools(tool_registry) -> None:
    """Register mailbox communication tools."""
    try:
        from ..agents.mailbox_tools import register_mailbox_tools
        register_mailbox_tools()
        logger.debug("Registered mailbox tools")
    except ImportError as e:
        logger.warning(f"Mailbox tools not available: {e}")
    except Exception as e:
        logger.error(f"Failed to register mailbox tools: {e}")


def _register_agent_e_tools(tool_registry) -> None:
    """Register Agent E task decomposition tools."""
    try:
        from .decompose_plan_tool import DecomposePlanTool
        from .analyze_dependencies_tool import AnalyzeDependenciesTool
        from .format_for_external_agent_tool import FormatForExternalAgentTool
        from .update_task_status_tool import UpdateTaskStatusTool
        from .validate_external_agent_tool import ValidateExternalAgentTool
        from .recommend_external_agent_tool import RecommendExternalAgentTool
        from .parse_external_result_tool import ParseExternalResultTool
        
        tool_registry.register_tool(DecomposePlanTool())
        tool_registry.register_tool(AnalyzeDependenciesTool())
        tool_registry.register_tool(FormatForExternalAgentTool())
        tool_registry.register_tool(UpdateTaskStatusTool())
        tool_registry.register_tool(ValidateExternalAgentTool())
        tool_registry.register_tool(RecommendExternalAgentTool())
        tool_registry.register_tool(ParseExternalResultTool())
        
        logger.debug("Registered Agent E tools")
    except ImportError as e:
        logger.warning(f"Agent E tools not available: {e}")
    except Exception as e:
        logger.error(f"Failed to register Agent E tools: {e}")


def register_tool_category(category: str, path_manager: Optional[PathManager] = None) -> None:
    """
    Register only tools from a specific category.
    
    Args:
        category: Category name (e.g., 'file', 'rfc', 'debugging')
        path_manager: Optional PathManager instance
    """
    tool_registry = get_tool_registry()
    
    if path_manager is None:
        path_manager = PathManager()
    
    category_map = {
        'file': _register_file_tools,
        'analysis': lambda tr: _register_analysis_tools(tr, path_manager),
        'rfc': _register_rfc_tools,
        'plan': _register_plan_tools,
        'codebase': _register_codebase_tools,
        'web': _register_web_tools,
        'debugging': _register_debugging_tools,
        'mailbox': _register_mailbox_tools,
        'agent_e': _register_agent_e_tools,
    }
    
    if category in category_map:
        category_map[category](tool_registry)
        logger.info(f"Registered {category} tools")
    else:
        logger.warning(f"Unknown tool category: {category}")
        logger.info(f"Available categories: {', '.join(category_map.keys())}")