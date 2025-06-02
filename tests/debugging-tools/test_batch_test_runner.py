#!/usr/bin/env python3
"""
Batch Test Runner - Creates isolated test server on random port
"""

import asyncio
import subprocess
import socket
import time
import json
import websocket
import threading
import os
import signal
import sys
from datetime import datetime
from pathlib import Path

class BatchTestRunner:
    def __init__(self):
        self.server_process = None
        self.server_port = None
        self.server_ready = False
        self.server_output = []
        self.test_results = []
        
    def find_free_port(self):
        """Find a free port to run the test server"""
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind(('', 0))
            s.listen(1)
            port = s.getsockname()[1]
        return port
        
    def start_test_server(self, extra_args=None):
        """Start an isolated test server instance"""
        self.server_port = self.find_free_port()
        print(f"Starting test server on port {self.server_port}...")
        
        # Build command
        cmd = [
            sys.executable, "-m", "interactive_server.main",
            "--port", str(self.server_port),
            "--host", "127.0.0.1"
        ]
        
        if extra_args:
            cmd.extend(extra_args)
            
        print(f"Command: {' '.join(cmd)}")
        
        # Start server
        env = os.environ.copy()
        env['PYTHONUNBUFFERED'] = '1'
        
        self.server_process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
            env=env,
            cwd=Path(__file__).parent
        )
        
        # Monitor output in thread
        def monitor_output():
            for line in self.server_process.stdout:
                line = line.strip()
                self.server_output.append(line)
                print(f"[SERVER] {line}")
                
                # Check for startup completion
                if "Application startup complete" in line or f"Uvicorn running on" in line:
                    self.server_ready = True
                elif "error" in line.lower() and "INFO" not in line:
                    print(f"[ERROR] Server error detected: {line}")
                    
        monitor_thread = threading.Thread(target=monitor_output)
        monitor_thread.daemon = True
        monitor_thread.start()
        
        # Wait for server to start
        timeout = 30
        start_time = time.time()
        while not self.server_ready and time.time() - start_time < timeout:
            if self.server_process.poll() is not None:
                print("❌ Server process died!")
                return False
            time.sleep(0.5)
            
        if not self.server_ready:
            print("⚠️ Server startup timeout - may not be ready")
            return False
        else:
            print("✅ Test server is ready!")
            time.sleep(1)  # Give it a moment to stabilize
            return True
            
    def stop_test_server(self):
        """Stop the test server"""
        if self.server_process:
            print("\nStopping test server...")
            self.server_process.terminate()
            try:
                self.server_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                print("Force killing server...")
                self.server_process.kill()
                self.server_process.wait()
            print("✅ Test server stopped")
            
            # Save server output
            with open("test_server_output.log", "w") as f:
                f.write("\n".join(self.server_output))
            print("Server output saved to: test_server_output.log")
            
    def connect_websocket(self):
        """Connect to the test server WebSocket"""
        ws_url = f"ws://127.0.0.1:{self.server_port}/ws"
        print(f"\nConnecting to {ws_url}...")
        
        ws = websocket.WebSocket()
        ws.settimeout(5)
        
        try:
            ws.connect(ws_url)
            print("✅ Connected to WebSocket")
            return ws
        except Exception as e:
            print(f"❌ Failed to connect: {e}")
            return None
            
    def send_rpc(self, ws, method, params=None):
        """Send JSON-RPC request and get response"""
        request_id = int(time.time() * 1000)
        request = {
            "jsonrpc": "2.0",
            "method": method,
            "id": request_id,
            "params": params or {}
        }
        
        print(f"\n→ {method}: {json.dumps(params or {}, indent=2)}")
        ws.send(json.dumps(request))
        
        # Wait for response
        response = None
        timeout = time.time() + 10
        
        while time.time() < timeout:
            try:
                ws.settimeout(1)  # Set timeout for recv
                msg = ws.recv()
                data = json.loads(msg)
                
                # Check if this is our response
                if data.get("id") == request_id:
                    response = data
                    break
                # Handle streaming notifications
                elif data.get("method") == "AIMessageChunkNotification":
                    # Skip streaming chunks for now
                    continue
                    
            except websocket.WebSocketTimeoutException:
                continue
            except Exception as e:
                print(f"Error receiving: {e}")
                break
                
        if response:
            if "error" in response:
                print(f"← Error: {response['error']['message']}")
            else:
                print(f"← Success")
        else:
            print(f"← No response received")
            
        return response
        
    def collect_all_responses(self, ws, request_id, timeout_seconds=10):
        """Collect both RPC response and streaming chunks"""
        full_text = ""
        start_time = time.time()
        chunks_received = 0
        rpc_received = False
        
        print(f"[COLLECT] Waiting for response to request {request_id}...")
        
        while time.time() - start_time < timeout_seconds:
            try:
                ws.settimeout(1)
                msg = ws.recv()
                data = json.loads(msg)
                
                # Check if this is our RPC response
                if data.get("id") == request_id:
                    rpc_received = True
                    if "error" in data:
                        print(f"[COLLECT] RPC Error: {data['error']['message']}")
                        return ""
                    else:
                        print(f"[COLLECT] RPC Success")
                        # Continue to collect streaming
                
                # Handle streaming chunks
                elif data.get("method") == "AIMessageChunkNotification":
                    chunk = data["params"].get("chunk", "")
                    full_text += chunk
                    chunks_received += 1
                    
                    if chunks_received == 1:
                        print(f"[COLLECT] Started receiving chunks...")
                    
                    if data["params"].get("isFinal", False):
                        print(f"[COLLECT] Final chunk! Total: {chunks_received} chunks, {len(full_text)} chars")
                        break
                        
            except websocket.WebSocketTimeoutException:
                # If we got the RPC response and some text, assume complete
                if rpc_received and full_text:
                    print(f"[COLLECT] Complete: {chunks_received} chunks, {len(full_text)} chars")
                    break
                continue
            except Exception as e:
                print(f"[COLLECT] Error: {e}")
                break
                
        return full_text
    
    def collect_streaming_response(self, ws, timeout_seconds=10):
        """Collect streaming AI response"""
        full_text = ""
        start_time = time.time()
        chunks_received = 0
        
        print(f"[STREAM] Starting to collect response (timeout={timeout_seconds}s)...")
        
        while time.time() - start_time < timeout_seconds:
            try:
                ws.settimeout(1)
                msg = ws.recv()
                data = json.loads(msg)
                
                # Debug log every message
                method = data.get("method", "")
                if method:
                    print(f"[STREAM] Notification: {method}")
                elif "result" in data:
                    print(f"[STREAM] RPC Response: {data.get('id', 'unknown')}")
                
                # Handle different message types
                if data.get("method") == "AIMessageChunkNotification":
                    chunk = data["params"].get("chunk", "")
                    full_text += chunk
                    chunks_received += 1
                    
                    # Show progress
                    if chunks_received % 5 == 1:
                        print(f"[STREAM] Received {chunks_received} chunks, {len(full_text)} chars so far...")
                    
                    if data["params"].get("isFinal", False):
                        print(f"[STREAM] Final chunk received! Total: {chunks_received} chunks, {len(full_text)} chars")
                        break
                elif data.get("method") == "agent.created":
                    print(f"[STREAM] Agent created: {data['params']}")
                    continue
                elif data.get("method") == "agent.switched":
                    print(f"[STREAM] Agent switched: {data['params']}")
                    continue
                elif "result" in data:
                    # This is a response to our RPC call, not streaming
                    continue
                        
            except websocket.WebSocketTimeoutException:
                # Timeout is normal if no more chunks
                if full_text:
                    print(f"[STREAM] Timeout with content - assuming complete ({len(full_text)} chars)")
                    break
                else:
                    print(f"[STREAM] Timeout waiting for content...")
                continue
            except Exception as e:
                print(f"[STREAM] Error: {e}")
                break
        
        elapsed = time.time() - start_time
        print(f"[STREAM] Collection complete: {chunks_received} chunks, {len(full_text)} chars in {elapsed:.1f}s")
        return full_text
        
    def run_test_script(self, script_path=None):
        """Run a test script against the server"""
        if not script_path:
            # Use default Debbie test
            return self.run_debbie_test()
            
        # TODO: Implement script file execution
        print(f"Script execution not yet implemented: {script_path}")
        return False
        
    def run_debbie_test(self):
        """Run the Debbie personality test"""
        print("\n=== RUNNING DEBBIE TEST ===")
        
        ws = self.connect_websocket()
        if not ws:
            return False
            
        session_id = None
        
        try:
            # Start session - need to include userId
            resp = self.send_rpc(ws, "startSession", {
                "userId": "test-user",  # Required field
                "sessionParams": {}
            })
            if resp and "result" in resp:
                session_id = resp["result"].get("sessionId")
                print(f"✅ Session started: {session_id}")
            elif resp and "error" in resp:
                print(f"❌ Failed to start session: {resp['error']['message']}")
                return False
            else:
                print("❌ Failed to start session - no response")
                return False
                
            # Switch to Debbie
            print("\n--- Testing Agent Switch ---")
            resp = self.send_rpc(ws, "session.switch_agent", {"agent_id": "d"})
            if resp and "error" not in resp:
                print("✅ Switched to agent 'd'")
            else:
                print(f"❌ Failed to switch: {resp}")
                return False
                
            # Agent switch may trigger automatic introduction
            print("\nChecking for automatic introduction...")
            intro = self.collect_streaming_response(ws, timeout_seconds=3)
            
            if not intro:
                print("No automatic introduction, sending explicit request...")
                # Send message - don't wait for RPC response before collecting stream
                request_id = int(time.time() * 1000)
                request = {
                    "jsonrpc": "2.0",
                    "method": "sendUserMessage",
                    "id": request_id,
                    "params": {
                        "sessionId": session_id,
                        "message": "Hello, who are you?"
                    }
                }
                ws.send(json.dumps(request))
                print(f"→ Sent introduction request")
                
                # Now collect both RPC response AND streaming chunks
                intro = self.collect_all_responses(ws, request_id, timeout_seconds=5)
            
            print(f"\nIntroduction: {intro[:200]}...")
            
            # Analyze introduction
            test_result = {
                "test": "agent_introduction",
                "response": intro,
                "success": False,
                "issues": []
            }
            
            if "Gemini" in intro:
                test_result["issues"].append("Identified as Gemini instead of Debbie")
                print("❌ FAIL: Debbie identified as Gemini!")
            elif "Debbie" in intro:
                test_result["success"] = True
                print("✅ PASS: Debbie identified correctly")
            else:
                test_result["issues"].append("No clear identity in introduction")
                print("⚠️ WARNING: Unclear identity")
                
            self.test_results.append(test_result)
            
            # Test tools awareness
            print("\n--- Testing Tool Awareness ---")
            request_id = int(time.time() * 1000)
            request = {
                "jsonrpc": "2.0",
                "method": "sendUserMessage",
                "id": request_id,
                "params": {
                    "sessionId": session_id,
                    "message": "What debugging tools do you have available?"
                }
            }
            ws.send(json.dumps(request))
            print(f"→ Sent tools query")
            tools_response = self.collect_all_responses(ws, request_id, timeout_seconds=5)
            print(f"\nTools response: {tools_response[:200]}...")
            
            test_result = {
                "test": "tool_awareness",
                "response": tools_response,
                "success": False,
                "issues": []
            }
            
            tool_keywords = ["session_health", "monitoring_control", "session_analysis", "debugging", "monitor"]
            if any(keyword in tools_response.lower() for keyword in tool_keywords):
                test_result["success"] = True
                print("✅ PASS: Debugging tools mentioned")
            else:
                test_result["issues"].append("No debugging tools mentioned")
                print("❌ FAIL: No debugging tools mentioned")
                
            self.test_results.append(test_result)
            
            # Test actual tool usage
            print("\n--- Testing Tool Usage ---")
            request_id = int(time.time() * 1000)
            request = {
                "jsonrpc": "2.0",
                "method": "sendUserMessage",
                "id": request_id,
                "params": {
                    "sessionId": session_id,
                    "message": "Check the health of this session using your session_health tool"
                }
            }
            ws.send(json.dumps(request))
            print(f"→ Sent health check request")
            health_response = self.collect_all_responses(ws, request_id, timeout_seconds=10)
            print(f"\nHealth check response: {health_response[:200]}...")
            
            test_result = {
                "test": "tool_usage",
                "response": health_response,
                "success": False,
                "issues": []
            }
            
            if "cannot" in health_response.lower() and "provide" in health_response.lower():
                test_result["issues"].append("Generic 'cannot provide' response")
                print("❌ FAIL: Generic refusal instead of using tool")
            elif "health" in health_response.lower() or "session" in health_response.lower():
                test_result["success"] = True
                print("✅ PASS: Appears to have used health check")
            else:
                test_result["issues"].append("Unclear if tool was used")
                print("⚠️ WARNING: Unclear response")
                
            self.test_results.append(test_result)
            
            return True
            
        except Exception as e:
            print(f"\n❌ Test error: {e}")
            import traceback
            traceback.print_exc()
            return False
        finally:
            ws.close()
            print("\n✅ WebSocket closed")
            
    def generate_report(self):
        """Generate test report"""
        print("\n=== TEST REPORT ===")
        
        total_tests = len(self.test_results)
        passed = sum(1 for r in self.test_results if r["success"])
        failed = total_tests - passed
        
        print(f"\nTotal tests: {total_tests}")
        print(f"Passed: {passed}")
        print(f"Failed: {failed}")
        
        if failed > 0:
            print("\nFailed tests:")
            for result in self.test_results:
                if not result["success"]:
                    print(f"\n  {result['test']}:")
                    for issue in result["issues"]:
                        print(f"    - {issue}")
                        
        # Save detailed results
        report = {
            "timestamp": datetime.now().isoformat(),
            "server_port": self.server_port,
            "summary": {
                "total": total_tests,
                "passed": passed,
                "failed": failed
            },
            "results": self.test_results,
            "server_output_lines": len(self.server_output)
        }
        
        with open("batch_test_report.json", "w") as f:
            json.dump(report, f, indent=2)
            
        print(f"\nDetailed report saved to: batch_test_report.json")
        print(f"Server output saved to: test_server_output.log")
        
        return failed == 0

def main():
    """Run batch test"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Batch Test Runner for AIWhisperer")
    parser.add_argument("--script", help="Test script to run")
    parser.add_argument("--debbie-monitor", action="store_true", help="Enable Debbie monitoring")
    parser.add_argument("--no-cleanup", action="store_true", help="Don't stop server after tests")
    
    args = parser.parse_args()
    
    runner = BatchTestRunner()
    
    try:
        # Build server args
        server_args = []
        if args.debbie_monitor:
            server_args.append("--debbie-monitor")
            
        # Start server
        if runner.start_test_server(server_args):
            # Run tests
            success = runner.run_test_script(args.script)
            
            # Generate report
            runner.generate_report()
            
            if not args.no_cleanup:
                runner.stop_test_server()
            else:
                print(f"\nTest server left running on port {runner.server_port}")
                print("Stop it manually when done testing")
                
            return 0 if success else 1
        else:
            print("\n❌ Failed to start test server")
            return 1
            
    except KeyboardInterrupt:
        print("\n\nInterrupted by user")
        return 1
    finally:
        if not args.no_cleanup and runner.server_process:
            runner.stop_test_server()

if __name__ == "__main__":
    sys.exit(main())