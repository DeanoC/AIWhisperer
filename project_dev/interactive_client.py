
import asyncio
import websockets
import json
import sys

async def print_server_messages(websocket):
    while True:
        try:
            msg = await websocket.recv()
            try:
                parsed = json.loads(msg)
            except Exception:
                parsed = msg
            print("[SERVER]", parsed)
        except websockets.ConnectionClosed:
            print("[INFO] WebSocket connection closed.")
            break
        except Exception as e:
            print(f"[ERROR] {e}")
            break

async def interactive_client():
    uri = "ws://127.0.0.1:8000/ws"
    print("Connecting to interactive server at", uri)
    session_id = None
    msg_id = 1
    websocket = await websockets.connect(uri)
    print("[INFO] Connected.")

    async def send_start_session():
        nonlocal session_id, msg_id
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
            print("[SERVER]", msg)
            if msg.get("result") and msg["result"].get("sessionId"):
                session_id = msg["result"]["sessionId"]
        print(f"Session started: {session_id}")

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

    async def send_user_message():
        nonlocal session_id, msg_id
        if not session_id:
            print("[WARN] No session active.")
            return
        user_msg = input("You: ")
        req = {
            "jsonrpc": "2.0",
            "id": msg_id,
            "method": "sendUserMessage",
            "params": {"sessionId": session_id, "message": user_msg}
        }
        await websocket.send(json.dumps(req))
        msg_id += 1

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
    asyncio.run(interactive_client())
