"""JSON-RPC handlers for plan management (list and read plans)"""
import logging
import json
from typing import Dict, Any
from ai_whisperer.tools.list_plans_tool import ListPlansTool
from ai_whisperer.tools.read_plan_tool import ReadPlanTool

logger = logging.getLogger(__name__)

list_plans_tool = ListPlansTool()
read_plan_tool = ReadPlanTool()

async def list_plans_handler(params: Dict[str, Any], websocket=None) -> Dict[str, Any]:
    """List available plans (in_progress and archived)"""
    try:
        # Accept status, sort_by, limit from params and force JSON format for UI
        tool_params = params or {}
        tool_params["format"] = "json"
        result_json = list_plans_tool.execute(tool_params)
        plans = []
        try:
            plans = json.loads(result_json)
        except Exception as e:
            logger.error(f"Failed to parse plans JSON: {e}")
        return {"plans": plans}
    except Exception as e:
        logger.error(f"Failed to list plans: {e}")
        return {"error": {"code": -32603, "message": str(e)}}

async def read_plan_handler(params: Dict[str, Any], websocket=None) -> Dict[str, Any]:
    """Read a specific plan's details"""
    try:
        if not params or "plan_name" not in params:
            return {"error": {"code": -32602, "message": "Missing plan_name parameter"}}
        # Force JSON format for UI
        tool_params = params.copy()
        tool_params["format"] = "json"
        result_json = read_plan_tool.execute(tool_params)
        plan = None
        try:
            plan = json.loads(result_json)
        except Exception as e:
            logger.error(f"Failed to parse plan JSON: {e}")
        return {"plan": plan}
    except Exception as e:
        logger.error(f"Failed to read plan: {e}")
        return {"error": {"code": -32603, "message": str(e)}}
