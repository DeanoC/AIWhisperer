import os
import sys
import logging
import argparse

# Ensure we're using modules from the current worktree directory
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
if project_root not in sys.path:
    sys.path.insert(0, project_root)
    print(f"Added {project_root} to Python path to ensure correct module loading")

# Set up logging early
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
logger.info("Starting AIWhisperer interactive server...")
logger.info(f"Python executable: {sys.executable}")
logger.info(f"Project root: {project_root}")

import ai_whisperer.commands.echo
import ai_whisperer.commands.status
import ai_whisperer.commands.help
import ai_whisperer.commands.agent
import ai_whisperer.commands.session
import ai_whisperer.commands.debbie
import json
import inspect
import asyncio
import uuid
from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from ai_whisperer.config import load_config
from .stateless_session_manager import StatelessSessionManager
from .message_models import (
    StartSessionRequest, StartSessionResponse, SendUserMessageRequest, SendUserMessageResponse,
    AIMessageChunkNotification, SessionStatusNotification, StopSessionRequest, StopSessionResponse,
    ProvideToolResultRequest, ProvideToolResultResponse, SessionParams,
    SessionStatus, MessageStatus, ToolResultStatus
)
from ai_whisperer.agents.registry import AgentRegistry
from ai_whisperer.prompt_system import PromptSystem, PromptConfiguration
from ai_whisperer.path_management import PathManager
from pathlib import Path
from .handlers.project_handlers import init_project_handlers, PROJECT_HANDLERS
from .handlers.workspace_handler import WorkspaceHandler

# Initialize agent registry
try:
    prompts_dir = Path(os.environ.get("AIWHISPERER_PROMPTS", "prompts"))
    agent_registry = AgentRegistry(prompts_dir)
    logger.info(f"AgentRegistry initialized with prompts_dir: {prompts_dir}")
    logger.info(f"Available agents: {[a.agent_id for a in agent_registry.list_agents()]}")
except Exception as e:
    logger.error(f"Failed to initialize AgentRegistry: {e}")
    import traceback
    traceback.print_exc()
    agent_registry = None
# === Agent/Session JSON-RPC Handlers ===
async def agent_list_handler(params, websocket=None):
    if not agent_registry:
        logger.error("AgentRegistry not initialized")
        return {"agents": []}
    
    try:
        # Check if a workspace is active
        has_active_workspace = False
        from .handlers.project_handlers import get_project_manager
        try:
            pm = get_project_manager()
            active_project = pm.get_active_project()
            has_active_workspace = active_project is not None
            logger.info(f"Active workspace check: project={active_project.name if active_project else None}, has_workspace={has_active_workspace}")
        except Exception as e:
            logger.error(f"Error checking active workspace: {e}")
            pass
        
        all_agents = agent_registry.list_agents()
        logger.info(f"All agents from registry: {[a.agent_id for a in all_agents]}")
        
        # If no workspace is active, only show Alice (agent 'a') and Debbie (agent 'd')
        # Debbie should always be available for debugging regardless of workspace status
        if not has_active_workspace:
            all_agents = [agent for agent in all_agents if agent.agent_id.lower() in ['a', 'd']]
            logger.info(f"Filtered to Alice and Debbie: {[a.agent_id for a in all_agents]}")
        
        agents = [
            {
                "agent_id": agent.agent_id.lower(),  # Ensure lowercase for frontend consistency
                "name": agent.name,
                "role": agent.role,
                "description": agent.description,
                "color": agent.color,
                "shortcut": agent.shortcut,
                "icon": getattr(agent, 'icon', '🤖'),
            }
            for agent in all_agents
        ]
        logger.info(f"Returning {len(agents)} agents to frontend")
        return {"agents": agents}
    except Exception as e:
        logger.error(f"Error listing agents: {e}")
        return {"agents": []}

async def session_switch_agent_handler(params, websocket=None):
    agent_id = params.get("agent_id")
    logger.info(f"session_switch_agent_handler called with agent_id: {agent_id}")
    
    # Check if trying to switch to non-Alice/non-Debbie agent without workspace
    # Debbie should always be available for debugging regardless of workspace status
    if agent_id and agent_id.lower() not in ['a', 'd']:
        has_active_workspace = False
        from .handlers.project_handlers import get_project_manager
        try:
            pm = get_project_manager()
            active_project = pm.get_active_project()
            has_active_workspace = active_project is not None
        except:
            pass
        
        if not has_active_workspace:
            return {
                "jsonrpc": "2.0",
                "id": None,
                "error": {"code": -32001, "message": f"Agent '{agent_id}' requires an active workspace"}
            }
    
    session = session_manager.get_session_by_websocket(websocket)
    if not session and "sessionId" in params:
        session = session_manager.get_session(params["sessionId"])
    # In test context, do not auto-create session if websocket is None and sessionId is provided
    if not session and websocket is not None:
        session_id = await session_manager.create_session(websocket)
        await session_manager.start_session(session_id)
        session = session_manager.get_session_by_websocket(websocket)
    try:
        await session.switch_agent(agent_id)
        return {"success": True, "current_agent": agent_id}
    except ValueError as e:
        return {
            "jsonrpc": "2.0",
            "id": None, # ID will be filled by process_json_rpc_request
            "error": {"code": -32001, "message": f"Agent not found: {agent_id}"}
        }
    except Exception as e:
        import logging, traceback
        logging.error(f"[session_switch_agent_handler] Exception: {e}")
        traceback.print_exc()
        return {
            "jsonrpc": "2.0",
            "id": None, # ID will be filled by process_json_rpc_request
            "error": {"code": -32603, "message": f"Internal error: {e}"}
        }

async def session_current_agent_handler(params, websocket=None):
    session = session_manager.get_session_by_websocket(websocket)
    if not session and "sessionId" in params:
        session = session_manager.get_session(params["sessionId"])
    if not session or not session.active_agent:
        return {"current_agent": None}
    # Return lowercase to match frontend expectations
    return {"current_agent": session.active_agent.lower() if session.active_agent else None}

async def session_handoff_handler(params, websocket=None):
    to_agent = params.get("to_agent")
    session = session_manager.get_session_by_websocket(websocket)
    if not session and "sessionId" in params:
        session = session_manager.get_session(params["sessionId"])
    if not session and websocket is not None:
        session_id = await session_manager.create_session(websocket)
        await session_manager.start_session(session_id)
        session = session_manager.get_session_by_websocket(websocket)
    from_agent = session.active_agent if session and session.active_agent else None
    try:
        await session.switch_agent(to_agent)
        # Optionally: send notification/event to frontend
        return {"success": True, "from_agent": from_agent, "to_agent": to_agent}
    except ValueError as e:
        return {
            "jsonrpc": "2.0",
            "id": None, # ID will be filled by process_json_rpc_request
            "error": {"code": -32001, "message": f"Agent not found: {to_agent}"}
        }
    except Exception as e:
        import logging, traceback
        logging.error(f"[session_handoff_handler] Exception: {e}")
        traceback.print_exc()
        return {
            "jsonrpc": "2.0",
            "id": None, # ID will be filled by process_json_rpc_request
            "error": {"code": -32603, "message": f"Internal error: {e}"}
        }

app = FastAPI()

# Configure CORS for any remaining REST endpoints
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001"],  # React dev servers
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Parse command line arguments for Debbie monitoring
def parse_args():
    parser = argparse.ArgumentParser(description="AIWhisperer Interactive Server")
    parser.add_argument("--debbie-monitor", action="store_true", 
                       help="Enable Debbie monitoring for session debugging")
    parser.add_argument("--monitor-level", choices=["passive", "active"], default="passive",
                       help="Monitoring level: passive (observe only) or active (can intervene)")
    parser.add_argument("--config", default=os.environ.get("AIWHISPERER_CONFIG", "config.yaml"),
                       help="Configuration file path")
    parser.add_argument("--host", default="127.0.0.1", help="Host to bind to")
    parser.add_argument("--port", type=int, default=8000, help="Port to bind to")
    return parser.parse_args()

def initialize_server(cli_args=None):
    """Initialize the server with optional CLI arguments"""
    global app_config, debbie_observer
    
    # Use provided args or parse them
    if cli_args is None:
        cli_args = parse_args()
    
    # Load config and initialize session manager at startup
    CONFIG_PATH = cli_args.config
    try:
        app_config = load_config(CONFIG_PATH)
    except Exception as e:
        logging.error(f"Failed to load configuration: {e}")
        app_config = {}

    # Initialize Debbie observer if monitoring is enabled
    debbie_observer = None
    if cli_args.debbie_monitor:
        try:
            from .debbie_observer import get_observer
            debbie_observer = get_observer()
            debbie_observer.enable()
            logger.info(f"Debbie monitoring enabled in {cli_args.monitor_level} mode")
            
            # Configure monitoring level
            if cli_args.monitor_level == "active":
                # TODO: Set active monitoring flags when available
                logger.info("Active monitoring mode: Debbie can intervene in sessions")
            else:
                logger.info("Passive monitoring mode: Debbie will observe only")
                
        except Exception as e:
            logger.error(f"Failed to initialize Debbie observer: {e}")
            debbie_observer = None
    
    return cli_args, app_config, debbie_observer

# Initialize with default args when imported as module
try:
    # Only parse args if running as main module
    if __name__ == "__main__":
        cli_args, app_config, debbie_observer = initialize_server()
    else:
        # When imported, use defaults
        class DefaultArgs:
            debbie_monitor = False
            monitor_level = "passive"
            config = os.environ.get("AIWHISPERER_CONFIG", "config.yaml")
        
        cli_args, app_config, debbie_observer = initialize_server(DefaultArgs())
except Exception as e:
    logger.error(f"Failed to initialize server: {e}")
    # Fallback to basic config
    app_config = {}
    debbie_observer = None
    class DefaultArgs:
        debbie_monitor = False
        monitor_level = "passive"
        config = "config.yaml"
    cli_args = DefaultArgs()

# Initialize PathManager
path_manager = None
try:
    path_manager = PathManager.get_instance()
    path_manager.initialize(config_values=app_config)
    logging.info("PathManager initialized successfully")
    logging.info(f"  - app_path: {path_manager.app_path}")
    logging.info(f"  - prompt_path: {path_manager.prompt_path}")
    logging.info(f"  - workspace_path: {path_manager.workspace_path}")
    logging.info(f"  - project_path: {path_manager.project_path}")
    
    # Verify prompts directory exists
    prompts_dir = path_manager.app_path / "prompts" / "agents"
    if prompts_dir.exists():
        agent_prompts = list(prompts_dir.glob("*.md"))
        logging.info(f"  - Found {len(agent_prompts)} agent prompts in {prompts_dir}")
        if any("debbie" in p.name.lower() for p in agent_prompts):
            logging.info("  - ✓ Debbie's prompt file found")
        else:
            logging.warning("  - ⚠️ Debbie's prompt file NOT found in agent prompts!")
    else:
        logging.warning(f"  - ⚠️ Prompts directory not found at {prompts_dir}")
except Exception as e:
    logging.error(f"Failed to initialize PathManager: {e}")
    # Continue without PathManager

# Initialize project manager
try:
    data_dir = Path.home() / ".aiwhisperer" / "data"
    data_dir.mkdir(parents=True, exist_ok=True)
    project_manager = init_project_handlers(data_dir)
    logging.info("ProjectManager initialized successfully")
except Exception as e:
    logging.error(f"Failed to initialize ProjectManager: {e}")
    project_manager = None

# Initialize workspace handler
workspace_handler = None
if path_manager:
    try:
        workspace_handler = WorkspaceHandler(path_manager)
        logging.info("WorkspaceHandler initialized successfully")
    except Exception as e:
        logging.error(f"Failed to initialize WorkspaceHandler: {e}")
        workspace_handler = None

# Initialize prompt system
prompt_system = None
try:
    from ai_whisperer.tools.tool_registry import get_tool_registry
    prompt_config = PromptConfiguration(app_config)
    tool_registry = get_tool_registry()
    prompt_system = PromptSystem(prompt_config, tool_registry)
    logging.info("PromptSystem initialized successfully with tool registry")
except Exception as e:
    logging.error(f"Failed to initialize PromptSystem: {e}")
    # Continue without prompt system

try:
    session_manager = StatelessSessionManager(app_config, agent_registry, prompt_system, observer=debbie_observer)
    logger.info("StatelessSessionManager initialized successfully")
except Exception as e:
    logger.error(f"Failed to initialize StatelessSessionManager: {e}")
    import traceback
    traceback.print_exc()
    # Create a basic session manager without extras
    session_manager = StatelessSessionManager(app_config, None, None, observer=debbie_observer)
    logger.info("Created basic StatelessSessionManager without agent registry")


# Handler functions
async def start_session_handler(params, websocket=None):
    model = StartSessionRequest(**params)
    # Create a new session for this websocket
    session_id = await session_manager.create_session(websocket)
    
    # Extract system prompt from session params if provided
    system_prompt = None
    if model.sessionParams and model.sessionParams.context:
        system_prompt = model.sessionParams.context
    
    # Start the AI session with optional system prompt
    await session_manager.start_session(session_id, system_prompt)
    # Respond with real session ID and status
    response = StartSessionResponse(sessionId=session_id, status=SessionStatus.Active).model_dump()
    return response


async def send_user_message_handler(params, websocket=None):
    logging.error(f"[send_user_message_handler] ENTRY: params={params}")
    try:
        model = SendUserMessageRequest(**params)
    except Exception as validation_error:
        logging.error(f"[send_user_message_handler] Validation error: {validation_error}")
        raise ValueError(f"Missing required parameter or invalid format: {validation_error}")

    session = session_manager.get_session_by_websocket(websocket)
    if not session and hasattr(model, "sessionId"):
        session = session_manager.get_session(model.sessionId)
    logging.info(f"[send_user_message_handler] Found session: {session.session_id if session else 'None'}, active agent: {session.active_agent if session else 'None'}")
    if not session:
        raise ValueError(f"Invalid session: {getattr(model, 'sessionId', None)}")

    try:
        logging.debug(f"[send_user_message_handler] Calling session.send_user_message: {model.message}")
        # The session now has built-in streaming support
        await session.send_user_message(model.message)
        response = SendUserMessageResponse(messageId=str(uuid.uuid4()), status=MessageStatus.OK).model_dump()
        logging.debug("[send_user_message_handler] Message sent successfully, returning OK response.")
        return response
    except Exception as e:
        logging.error(f"[send_user_message_handler] Exception: {e}")
        raise RuntimeError(f"Failed to send message: {e}")


async def provide_tool_result_handler(params, websocket=None):
    model = ProvideToolResultRequest(**params)
    session = session_manager.get_session(model.sessionId)
    if not session:
        raise ValueError(f"Session {model.sessionId} not found")
    # Tool results are not yet implemented in the stateless architecture
    # For now, just return OK
    response = ProvideToolResultResponse(status=ToolResultStatus.OK).model_dump()
    return response


async def stop_session_handler(params, websocket=None):
    from .message_models import SessionStatusNotification, SessionStatus
    try:
        model = StopSessionRequest(**params)
        session = session_manager.get_session(model.sessionId)
        if session:
            await session_manager.stop_session(model.sessionId)
            # Send final SessionStatusNotification before cleanup
            notification = SessionStatusNotification(
                sessionId=model.sessionId,
                status=SessionStatus.Stopped,
                reason="Session stopped"
            )
            await session.send_notification("SessionStatusNotification", notification)
            await session_manager.cleanup_session(model.sessionId)
    except Exception:
        pass  # Ignore all errors for idempotency
    # Always return stopped for idempotency
    return StopSessionResponse(status=SessionStatus.Stopped).model_dump()

# JSON-RPC echo handler: returns the message param as-is (for protocol/dispatch test compatibility)
async def echo_handler(params, websocket=None):
    # If 'message' is present, return it directly (tests expect this)
    if isinstance(params, dict) and "message" in params:
        return params["message"]
    return params

# Debbie monitoring handlers
async def debbie_get_status_handler(params, websocket=None):
    """Get Debbie monitoring status"""
    if not debbie_observer:
        return {"enabled": False, "message": "Debbie monitoring not initialized"}
    
    return {
        "enabled": debbie_observer._enabled,
        "monitoring_level": cli_args.monitor_level if cli_args.debbie_monitor else None,
        "active_sessions": len(debbie_observer.monitors),
        "session_ids": list(debbie_observer.monitors.keys())
    }

async def debbie_get_alerts_handler(params, websocket=None):
    """Get current monitoring alerts"""
    session_id = params.get("session_id")
    
    if not debbie_observer:
        return {"alerts": [], "message": "Debbie monitoring not initialized"}
    
    alerts = []
    if session_id:
        # Get alerts for specific session
        monitor = debbie_observer.monitors.get(session_id)
        if monitor:
            alerts = [
                {
                    "timestamp": alert.timestamp.isoformat(),
                    "pattern": alert.pattern.value,
                    "severity": alert.severity.value,
                    "message": alert.message,
                    "suggestion": alert.suggestion,
                    "session_id": session_id
                }
                for alert in monitor.alerts
            ]
    else:
        # Get alerts from all sessions
        for sid, monitor in debbie_observer.monitors.items():
            for alert in monitor.alerts:
                alerts.append({
                    "timestamp": alert.timestamp.isoformat(),
                    "pattern": alert.pattern.value,
                    "severity": alert.severity.value,
                    "message": alert.message,
                    "suggestion": alert.suggestion,
                    "session_id": sid
                })
    
    return {"alerts": alerts}

async def debbie_send_alert_notification(websocket, alert_data):
    """Send alert notification to WebSocket client"""
    if not websocket:
        return
        
    notification = {
        "jsonrpc": "2.0",
        "method": "debbie.alert",
        "params": alert_data
    }
    
    try:
        await websocket.send_text(json.dumps(notification))
        logger.debug(f"Sent Debbie alert notification: {alert_data['pattern']}")
    except Exception as e:
        logger.error(f"Failed to send Debbie alert notification: {e}")


# Handler registry
from ai_whisperer.commands.registry import CommandRegistry

from ai_whisperer.commands.errors import CommandError

async def dispatch_command_handler(params, websocket=None):
    session_id = params.get("sessionId")
    command_str = params.get("command", "")
    if not command_str.startswith("/"):
        return {"error": "Invalid command format. Must start with /"}
    parts = command_str[1:].split(" ", 1)
    cmd_name = parts[0]
    cmd_args = parts[1] if len(parts) > 1 else ""
    cmd_cls = CommandRegistry.get(cmd_name)
    if not cmd_cls:
        return {"error": f"Unknown command: {cmd_name}"}
    cmd = cmd_cls()
    try:
        result = cmd.run(cmd_args, context={"session_id": session_id})
        return {"output": result}
    except CommandError as ce:
        return {"error": str(ce)}
    except Exception as e:
        return {"error": f"Command error: {str(e)}"}

HANDLERS = {
    "startSession": start_session_handler,
    "sendUserMessage": send_user_message_handler,
    "provideToolResult": provide_tool_result_handler,
    "stopSession": stop_session_handler,
    "echo": echo_handler,  # JSON-RPC echo handler for protocol/dispatch test compatibility
    "dispatchCommand": dispatch_command_handler,
    # Agent/session management
    "agent.list": agent_list_handler,
    "session.switch_agent": session_switch_agent_handler,
    "session.current_agent": session_current_agent_handler,
    "session.handoff": session_handoff_handler,
    # Debbie monitoring handlers
    "debbie.status": debbie_get_status_handler,
    "debbie.alerts": debbie_get_alerts_handler,
    # Project management handlers
    **PROJECT_HANDLERS
}

# Add workspace handlers if available
if workspace_handler:
    workspace_methods = workspace_handler.get_methods()
    logging.info(f"Adding workspace methods to handlers: {list(workspace_methods.keys())}")
    HANDLERS.update(workspace_methods)
else:
    logging.warning("WorkspaceHandler not available, workspace methods will not be registered")


async def process_json_rpc_request(msg, websocket):
    """Process a JSON-RPC request message."""
    method = msg["method"]
    handler = HANDLERS.get(method)
    
    if not handler:
        return {
            "jsonrpc": "2.0",
            "id": msg["id"],
            "error": {"code": -32601, "message": "Method not found"}
        }
    
    try:
        # If handler is async, await it
        if inspect.iscoroutinefunction(handler):
            result = await handler(msg.get("params", {}), websocket=websocket)
        else:
            result = handler(msg.get("params", {}), websocket=websocket)
        # If result is a dict and contains an "error" key, return it as is (it's already a JSON-RPC error object)
        if isinstance(result, dict) and "error" in result:
            # Ensure the ID is set correctly for the error response
            result["id"] = msg["id"]
            return result
        # Otherwise, wrap the result in a "result" key
        return {"jsonrpc": "2.0", "id": msg["id"], "result": result}
    except (ValueError, TypeError) as e:
        import logging
        logging.error(f"[process_json_rpc_request] ValueError/TypeError: {e}")
        return {
            "jsonrpc": "2.0",
            "id": msg["id"],
            "error": {"code": -32602, "message": f"Invalid params: {e}"}
        }
    except Exception as e:
        import logging
        logging.error(f"[process_json_rpc_request] Exception: {e}")
        return {
            "jsonrpc": "2.0",
            "id": msg["id"],
            "error": {"code": -32603, "message": f"Internal error: {e}"}
        }


async def handle_websocket_message(websocket, data):
    """Handle incoming WebSocket message."""
    try:
        msg = json.loads(data)
    except Exception:
        # Not valid JSON - return JSON-RPC parse error (-32700)
        logging.debug(f"[handle_websocket_message] Not JSON, returning JSON-RPC parse error: {data}")
        return {
            "jsonrpc": "2.0",
            "id": None,
            "error": {"code": -32700, "message": "Parse error"}
        }
    
    # Minimal JSON-RPC 2.0 handling
    if not isinstance(msg, dict) or msg.get("jsonrpc") != "2.0":
        return {
            "jsonrpc": "2.0",
            "id": msg.get("id") if isinstance(msg, dict) else None,
            "error": {"code": -32600, "message": "Invalid Request"}
        }
    
    if "method" not in msg:
        # Invalid Request
        return {
            "jsonrpc": "2.0",
            "id": msg.get("id"),
            "error": {"code": -32600, "message": "Invalid Request"}
        }
    
    if "id" in msg:
        # Request - process and return response
        try:
            return await process_json_rpc_request(msg, websocket)
        except Exception as e:
            # Handler threw an exception that wasn't caught by process_json_rpc_request
            # Return a generic error response
            logging.error(f"[handle_websocket_message] Unhandled exception in handler: {e}")
            return {
                "jsonrpc": "2.0",
                "id": msg["id"],
                "error": {"code": -32603, "message": "Internal error"}
            }
    else:
        # Notification - still process certain critical methods
        method = msg.get("method", "")
        if method in ["sendUserMessage", "provideToolResult"]:
            # These methods should be processed even as notifications
            # to prevent message buffering issues
            logging.warning(f"[handle_websocket_message] Processing critical notification: {method}")
            try:
                # Create a fake ID for internal processing
                msg["id"] = f"notification_{method}_{id(msg)}"
                response = await process_json_rpc_request(msg, websocket)
                # Don't return the response for notifications
                return None
            except Exception as e:
                logging.error(f"[handle_websocket_message] Error processing notification: {e}")
                return None
        else:
            # Other notifications - do nothing
            return None

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    logging.debug("[websocket_endpoint] WebSocket accepted.")
    websocket_closed = False
    
    while True:
        try:
            logging.debug("[websocket_endpoint] Waiting for message...")
            data = await websocket.receive_text()
            logging.error(f"[websocket_endpoint] CRITICAL: Received message: {data}")
            
            # Debug: Check if this is a notification
            try:
                parsed_data = json.loads(data)
                if isinstance(parsed_data, dict) and "method" in parsed_data and "id" not in parsed_data:
                    logging.warning(f"[websocket_endpoint] WARNING: Received notification for method: {parsed_data.get('method')}")
            except:
                pass
            
            response = await handle_websocket_message(websocket, data)
            logging.error(f"[websocket_endpoint] CRITICAL: Generated response: {response}")
            
            if response:  # Only send response for requests (not notifications)
                response_text = json.dumps(response)
                logging.debug(f"[websocket_endpoint] Sending response: {response_text}")
                await websocket.send_text(response_text)
                logging.debug("[websocket_endpoint] Response sent successfully")
            else:
                logging.debug("[websocket_endpoint] No response to send (notification)")
                
        except Exception as e:
            # Not valid JSON or not JSON-RPC or handler error
            logging.error(f"[websocket_endpoint] WebSocket error: {e}")
            websocket_closed = True
            break
    
    # Cleanup session when WebSocket closes
    try:
        if websocket in session_manager.websocket_sessions:
            session_id = session_manager.websocket_sessions[websocket]
            logging.info(f"[websocket_endpoint] Cleaning up session {session_id} for closed WebSocket")
            
            # Remove the WebSocket association
            del session_manager.websocket_sessions[websocket]
            
            # Note: We don't remove the session itself - it may be reconnected
            # But we should mark it as disconnected
            if session_id in session_manager.sessions:
                session = session_manager.sessions[session_id]
                session.websocket = None  # Clear the WebSocket reference
                logging.info(f"[websocket_endpoint] Cleared WebSocket reference for session {session_id}")
    except Exception as cleanup_error:
        logging.error(f"[websocket_endpoint] Error during session cleanup: {cleanup_error}")
    
    logging.debug("[websocket_endpoint] WebSocket endpoint exiting, closing websocket.")
    if not websocket_closed:
        try:
            await websocket.close()
            logging.debug("[websocket_endpoint] WebSocket closed cleanly.")
        except Exception as close_exc:
            logging.error(f"[websocket_endpoint] Exception during websocket.close(): {close_exc}")


if __name__ == "__main__":
    import uvicorn
    # CLI args are already parsed in the initialization above
    logger.info(f"Starting server on {cli_args.host}:{cli_args.port} with Debbie monitoring: {cli_args.debbie_monitor}")
    uvicorn.run(app, host=cli_args.host, port=cli_args.port)
