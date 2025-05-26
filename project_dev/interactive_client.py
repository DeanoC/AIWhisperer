import asyncio
import websockets
import json

async def interactive_client():
    uri = "ws://127.0.0.1:8000/ws"
    session_id = None
    print("Connecting to interactive server at", uri)
    async with websockets.connect(uri) as websocket:
        # Start session
        user_id = input("Enter userId: ") or "test_user"
        start_req = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "startSession",
            "params": {"userId": user_id, "sessionParams": {"language": "en"}}
        }
        await websocket.send(json.dumps(start_req))
        # Wait for sessionId
        while not session_id:
            msg = json.loads(await websocket.recv())
            print("[SERVER]", msg)
            if msg.get("result") and msg["result"].get("sessionId"):
                session_id = msg["result"]["sessionId"]
        print(f"Session started: {session_id}")
        msg_id = 2
        while True:
            user_msg = input("You: ")
            if not user_msg:
                continue
            req = {
                "jsonrpc": "2.0",
                "id": msg_id,
                "method": "sendUserMessage",
                "params": {"sessionId": session_id, "message": user_msg}
            }
            await websocket.send(json.dumps(req))
            msg_id += 1
            # Print all server messages until next user input
            while True:
                try:
                    response = await asyncio.wait_for(websocket.recv(), timeout=0.5)
                    print("[SERVER]", json.loads(response))
                except asyncio.TimeoutError:
                    break

if __name__ == "__main__":
    asyncio.run(interactive_client())
