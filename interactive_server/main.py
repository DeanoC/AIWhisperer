
import os
import ai_whisperer.commands.echo
import ai_whisperer.commands.status
import ai_whisperer.commands.help
import logging
import json
import inspect
import asyncio
import uuid
from fastapi import FastAPI, WebSocket
from ai_whisperer.config import load_config
from .session_manager import InteractiveSessionManager
from .message_models import (
    StartSessionRequest, StartSessionResponse, SendUserMessageRequest, SendUserMessageResponse,
    AIMessageChunkNotification, SessionStatusNotification, StopSessionRequest, StopSessionResponse,
    ProvideToolResultRequest, ProvideToolResultResponse, SessionParams,
    SessionStatus, MessageStatus, ToolResultStatus
)

app = FastAPI()

# Load config and initialize session manager at startup
CONFIG_PATH = os.environ.get("AIWHISPERER_CONFIG", "config.yaml")
try:
    app_config = load_config(CONFIG_PATH)
except Exception as e:
    logging.error(f"Failed to load configuration: {e}")
    app_config = {}

session_manager = InteractiveSessionManager(app_config)


# Handler functions
async def start_session_handler(params, websocket=None):
    model = StartSessionRequest(**params)
    # Create a new session for this websocket
    session_id = await session_manager.create_session(
        websocket, 
        session_params=(model.sessionParams.model_dump() if model.sessionParams else {})
    )
    # Start the AI session (system prompt can be extended from params if needed)
    await session_manager.start_session(session_id)
    # Respond with real session ID and status
    response = StartSessionResponse(sessionId=session_id, status=SessionStatus.Active).model_dump()
    # The delegate bridge will handle notifications
    return response


async def send_user_message_handler(params, websocket=None):
    logging.error(f"[send_user_message_handler] ENTRY: params={params}")
    try:
        model = SendUserMessageRequest(**params)
    except Exception as validation_error:
        # Pydantic validation failed - this is the kind of error we want to send via delegate bridge
        logging.error(f"[send_user_message_handler] Validation error: {validation_error}")
        
        # Get the session if possible to trigger delegate bridge notification
        session_id = params.get("sessionId")
        if session_id:
            session = session_manager.get_session(session_id)
            if session and session.delegate_bridge:
                logging.debug("[send_user_message_handler] Calling delegate_bridge._handle_error for validation error...")
                try:
                    await session.delegate_bridge._handle_error(sender=None, event_data=validation_error)
                    logging.debug("[send_user_message_handler] delegate_bridge._handle_error completed.")
                    # Add delay to allow notification delivery
                    await asyncio.sleep(0.3)
                except Exception as bridge_error:
                    logging.error(f"[send_user_message_handler] Error in delegate bridge: {bridge_error}")
        
        # Re-raise for JSON-RPC error response
        raise validation_error
    
    session = session_manager.get_session(model.sessionId)
    if not session:
        raise ValueError(f"Session {model.sessionId} not found")
    
    try:
        logging.debug(f"[send_user_message_handler] Calling session.send_user_message: {model.message}")
        await session.send_user_message(model.message)
        response = SendUserMessageResponse(messageId=str(uuid.uuid4()), status=MessageStatus.OK).model_dump()
        logging.debug("[send_user_message_handler] Message sent successfully, returning OK response.")
        return response
    except Exception as e:
        logging.error(f"[send_user_message_handler] Exception: {e}")
        # The AILoop should have already handled the error and triggered delegate notifications
        # if this was an invalid message type. We just need to return a JSON-RPC error response.
        logging.debug("[send_user_message_handler] Raising exception to return JSON-RPC error response.")
        raise e


async def provide_tool_result_handler(params, websocket=None):
    model = ProvideToolResultRequest(**params)
    session = session_manager.get_session(model.sessionId)
    if not session:
        raise ValueError(f"Session {model.sessionId} not found")
    # Provide the tool result to the AILoop (via InteractiveAI)
    if not session.interactive_ai or not session.interactive_ai.ai_loop:
        raise RuntimeError("AI loop not initialized for session")
    # The AILoop expects tool results via a delegate event
    await session.interactive_ai.ai_loop._handle_provide_tool_result(
        tool_call_id=model.toolCallId, 
        result=model.result
    )
    # Respond with status OK
    response = ProvideToolResultResponse(status=ToolResultStatus.OK).model_dump()
    return response


async def stop_session_handler(params, websocket=None):
    try:
        model = StopSessionRequest(**params)
        session = session_manager.get_session(model.sessionId)
        if session:
            await session_manager.stop_session(model.sessionId)
            # Send final SessionStatusNotification before cleanup
            from .message_models import SessionStatusNotification, SessionStatus
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
}


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
        
        # If result is a dict (from model_dump), return as is, else wrap
        if isinstance(result, dict):
            return {"jsonrpc": "2.0", "id": msg["id"], "result": result}
        else:
            return {"jsonrpc": "2.0", "id": msg["id"], "result": result}
    except (ValueError, TypeError) as e:
        # These are parameter validation errors - return JSON-RPC error
        return {
            "jsonrpc": "2.0",
            "id": msg["id"],
            "error": {"code": -32602, "message": "Invalid params"}
        }
    except Exception as e:
        # Other exceptions - let them bubble up to be handled by the websocket layer
        # The specific handlers (like send_user_message_handler) should handle their own errors
        # and return appropriate responses or trigger delegate notifications
        raise e


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
        # Notification - do nothing
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
    
    logging.debug("[websocket_endpoint] WebSocket endpoint exiting, closing websocket.")
    if not websocket_closed:
        try:
            await websocket.close()
            logging.debug("[websocket_endpoint] WebSocket closed cleanly.")
        except Exception as close_exc:
            logging.error(f"[websocket_endpoint] Exception during websocket.close(): {close_exc}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
