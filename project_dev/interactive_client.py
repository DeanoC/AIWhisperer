
import asyncio
import websockets
import json

import sys
import argparse
import pathlib

async def print_server_messages(websocket):
    # Use the outer log function
    import inspect
    frame = inspect.currentframe()
    outer_locals = frame.f_back.f_locals
    log = outer_locals.get('log', print)
    while True:
        try:
            msg = await websocket.recv()
            try:
                parsed = json.loads(msg)
            except Exception:
                parsed = msg
            log(parsed)
        except websockets.ConnectionClosed:
            log("[INFO] WebSocket connection closed.")
            break
        except Exception as e:
            log(f"[ERROR] {e}")
            break

async def interactive_client(script_path=None, log_path=None):

    uri = "ws://127.0.0.1:8000/ws"
    print("Connecting to interactive server at", uri)
    session_id = None
    msg_id = 1
    websocket = await websockets.connect(uri)
    print("[INFO] Connected.")

    # For logging
    log_f = open(log_path, "w", encoding="utf-8") if log_path else None
    def log(msg):
        print(msg)
        if log_f:
            import json as _json
            # Always try to parse and re-emit [SERVER] lines as JSON
            if isinstance(msg, str) and msg.startswith('[SERVER] '):
                payload = msg[len('[SERVER] '):]
                try:
                    # Try JSON first
                    parsed = _json.loads(payload)
                except Exception:
                    try:
                        import ast
                        parsed = ast.literal_eval(payload)
                    except Exception:
                        parsed = None
                if parsed is not None:
                    print('[SERVER] ' + _json.dumps(parsed, ensure_ascii=False), file=log_f)
                else:
                    print(msg, file=log_f)
            elif isinstance(msg, (dict, list)):
                print(_json.dumps(msg, ensure_ascii=False), file=log_f)
            else:
                print(msg, file=log_f)

    async def send_start_session(user_id=None):
        nonlocal session_id, msg_id
        if user_id is None:
            user_id = input("Enter userId: ") or "test_user"
        start_req = {
            "jsonrpc": "2.0",
            "id": msg_id,
            "method": "startSession",
            "params": {"userId": user_id, "sessionParams": {"language": "en"}}
        }
        await websocket.send(json.dumps(start_req))
        msg_id += 1
        # Wait for sessionId
        while not session_id:
            msg = json.loads(await websocket.recv())
            log(f"[SERVER] {msg}")
            if msg.get("result") and msg["result"].get("sessionId"):
                session_id = msg["result"]["sessionId"]
        log(f"Session started: {session_id}")

    async def send_stop_session():
        nonlocal session_id, msg_id
        if not session_id:
            print("[WARN] No session active.")
            return
        stop_req = {
            "jsonrpc": "2.0",
            "id": msg_id,
            "method": "stopSession",
            "params": {"sessionId": session_id}
        }
        await websocket.send(json.dumps(stop_req))
        msg_id += 1
        print("Sent stopSession request.")

    async def send_user_message(message=None):
        nonlocal session_id, msg_id
        if not session_id:
            print("[WARN] No session active.")
            return
        if message is None:
            user_msg = input("You: ")
        else:
            user_msg = message
        req = {
            "jsonrpc": "2.0",
            "id": msg_id,
            "method": "sendUserMessage",
            "params": {"sessionId": session_id, "message": user_msg}
        }
        await websocket.send(json.dumps(req))
        # Log the user message for test visibility
        log({"user_message": user_msg})
        msg_id += 1

        # Wait for and print at least one response (result or notification)
        # Print all messages until we get the result for this msg_id and at least one AIMessageChunkNotification (isFinal True)
        got_result = False
        got_final_chunk = False
        while not got_result or not got_final_chunk:
            try:
                msg = await websocket.recv()
                try:
                    parsed = json.loads(msg)
                except Exception:
                    parsed = msg
                log(parsed)
                # Debug: print message type and keys
                if isinstance(parsed, dict):
                    print(f"[DEBUG] Received dict message keys: {list(parsed.keys())}")
                    if parsed.get("id") == req["id"] and parsed.get("result") and "messageId" in parsed["result"]:
                        print(f"[DEBUG] Got result for messageId: {parsed['result']['messageId']}")
                        got_result = True
                    if parsed.get("method") == "AIMessageChunkNotification":
                        params = parsed.get("params", {})
                        print(f"[DEBUG] AIMessageChunkNotification params: {params}")
                        if params.get("isFinal"):
                            print(f"[DEBUG] Got isFinal chunk for session {params.get('sessionId')}")
                            got_final_chunk = True
                else:
                    print(f"[DEBUG] Received non-dict message: {parsed}")
            except websockets.ConnectionClosed:
                print("[INFO] WebSocket connection closed.")
                break
            except Exception as e:
                print(f"[ERROR] {e}")
                break

    async def send_tool_result():
        nonlocal session_id, msg_id
        if not session_id:
            print("[WARN] No session active.")
            return
        tool_call_id = input("Tool call id: ")
        tool_name = input("Tool name: ")
        tool_content = input("Tool result content: ")
        req = {
            "jsonrpc": "2.0",
            "id": msg_id,
            "method": "provideToolResult",
            "params": {
                "sessionId": session_id,
                "result": {
                    "role": "tool",
                    "tool_call_id": tool_call_id,
                    "name": tool_name,
                    "content": tool_content
                }
            }
        }
        await websocket.send(json.dumps(req))
        msg_id += 1

    async def send_malformed():
        bad = input("Enter malformed JSON to send: ")
        await websocket.send(bad)
        print("Sent malformed JSON.")

    async def disconnect():
        await websocket.close()
        print("[INFO] Disconnected.")

    async def reconnect():
        nonlocal websocket, session_id, msg_id
        await websocket.close()
        websocket = await websockets.connect(uri)
        session_id = None
        msg_id = 1
        print("[INFO] Reconnected.")

    # --- Scripted mode ---
    if script_path:
        script_path = pathlib.Path(script_path)
        if script_path.suffix.lower() == ".json":
            import json as _json
            with open(script_path, "r", encoding="utf-8") as f:
                script = _json.load(f)
            for entry in script:
                cmd = entry.get("command")
                if cmd == "startSession":
                    await send_start_session(entry.get("userId"))
                elif cmd == "sendUserMessage":
                    await send_user_message(entry.get("message"))
                elif cmd == "stopSession":
                    await send_stop_session()
                elif cmd == "provideToolResult":
                    # Add support as needed
                    pass
                elif cmd == "sendMalformedJSON":
                    await send_malformed()
                elif cmd == "disconnect":
                    await disconnect()
                elif cmd == "reconnect":
                    await reconnect()
                # Add more as needed
        else:
            # Plain text mode: one command per line, comments start with #
            with open(script_path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith("#"):
                        continue
                    if line.startswith("sendUserMessage ") and "message=" in line:
                        # Special handling: everything after 'message=' is the message
                        cmd = "sendUserMessage"
                        msg_idx = line.index("message=") + len("message=")
                        message = line[msg_idx:]
                        await send_user_message(message)
                    else:
                        parts = line.split()
                        cmd = parts[0]
                        args = dict(p.split("=", 1) for p in parts[1:] if "=" in p)
                        if cmd == "startSession":
                            await send_start_session(args.get("userId"))
                        elif cmd == "stopSession":
                            await send_stop_session()
                        # Add more as needed
        if log_f:
            log_f.flush()
            import os
            os.fsync(log_f.fileno())
            log_f.close()
        # Wait briefly to allow any in-flight notifications to arrive before disconnecting
        await asyncio.sleep(0.5)
        await disconnect()
        return

    # --- Interactive mode ---
    menu = """
Commands:
  1. startSession
  2. sendUserMessage
  3. stopSession
  4. provideToolResult
  5. sendMalformedJSON
  6. disconnect
  7. reconnect
  8. listen (print all server messages)
  9. exit
"""
    while True:
        print(menu)
        cmd = input("Select command: ").strip()
        if cmd == "1":
            await send_start_session()
        elif cmd == "2":
            await send_user_message()
        elif cmd == "3":
            await send_stop_session()
        elif cmd == "4":
            await send_tool_result()
        elif cmd == "5":
            await send_malformed()
        elif cmd == "6":
            await disconnect()
            break
        elif cmd == "7":
            await reconnect()
        elif cmd == "8":
            print("[INFO] Listening for all server messages. Press Ctrl+C to stop.")
            try:
                await print_server_messages(websocket)
            except KeyboardInterrupt:
                print("[INFO] Stopped listening.")
        elif cmd == "9":
            await disconnect()
            break
        else:
            print("Unknown command.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Interactive or scripted client for AILoop server")
    parser.add_argument("--script", type=str, help="Path to script file (.json or .txt)")
    parser.add_argument("--log", type=str, help="Path to log file for server responses")
    args = parser.parse_args()
    asyncio.run(interactive_client(script_path=args.script, log_path=args.log))
