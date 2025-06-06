"""Test complex multi-step tasks via synchronous mail."""

import pytest
import json
import asyncio
from typing import Dict, Any

from ai_whisperer.extensions.conversation_replay.websocket_client import ConversationWebSocketClient


class TestSyncMailComplex:
    """Test complex synchronous mail scenarios."""
    
    @pytest.mark.asyncio
    async def test_multi_step_analysis_task(self):
        """Test sending a complex multi-step task via mail."""
        client = ConversationWebSocketClient("ws://localhost:8000/ws")
        
        try:
            await client.connect()
            
            # Start session
            session_id = await client.start_session("test_user")
            
            # Send complex analysis request
            message = """Use send_mail_with_switch to send this task to Debbie:
            'Please analyze the ai_whisperer/tools directory and provide a comprehensive report:
            1. Count the total number of Python files
            2. List all tool categories (by examining file names)
            3. Identify the largest tool file by lines of code
            4. Find any tools related to mail or communication
            5. Generate a summary report with your findings'"""
            
            response = await client.send_message(message)
            
            # Wait for processing
            await asyncio.sleep(5)
            
            # Collect all responses
            responses = []
            notifications = []
            
            # Listen for responses
            try:
                while True:
                    msg = await asyncio.wait_for(client.receive(), timeout=2.0)
                    if msg.get("method") == "ChannelMessageNotification":
                        notifications.append(msg["params"])
                    responses.append(msg)
            except asyncio.TimeoutError:
                pass
            
            # Verify Debbie performed multiple tool calls
            tool_calls = [n for n in notifications if "tool" in str(n).lower()]
            assert len(tool_calls) > 0, "Expected Debbie to use tools"
            
            # Verify we got a comprehensive response
            final_responses = [n for n in notifications if n.get("channel") == "final"]
            assert any("summary" in str(r).lower() for r in final_responses), \
                "Expected summary in response"
            
            # Stop session
            await client.stop_session(session_id)
            
        finally:
            await client.disconnect()
    
    @pytest.mark.asyncio
    async def test_agent_chain_delegation(self):
        """Test A → D → P agent chain."""
        client = ConversationWebSocketClient("ws://localhost:8000/ws")
        
        try:
            await client.connect()
            
            # Start session
            session_id = await client.start_session("test_user")
            
            # Alice delegates to Debbie who should delegate to Patricia
            message = """Use send_mail_with_switch to send this to Debbie:
            'I need help understanding our RFC creation process. 
            Please work with Patricia to analyze the RFC workflow and identify 
            any bottlenecks or improvements. Get her analysis and summarize 
            the findings for me.'"""
            
            response = await client.send_message(message)
            
            # Wait for chain to complete
            await asyncio.sleep(8)
            
            # Collect responses
            responses = []
            agent_switches = []
            
            try:
                while True:
                    msg = await asyncio.wait_for(client.receive(), timeout=2.0)
                    responses.append(msg)
                    
                    # Track agent switches
                    if msg.get("method") == "agent.switched":
                        agent_switches.append(msg["params"])
                        
            except asyncio.TimeoutError:
                pass
            
            # Verify chain: A → D → P → D → A
            switch_sequence = [(s["from"], s["to"]) for s in agent_switches]
            
            # Should see switches indicating the chain
            assert any(s[1] == "d" for s in switch_sequence), "Should switch to Debbie"
            assert any(s[1] == "p" for s in switch_sequence), "Should switch to Patricia"
            
            # Verify we got analysis results
            notifications = [r for r in responses if r.get("method") == "ChannelMessageNotification"]
            assert any("rfc" in str(n).lower() for n in notifications), \
                "Expected RFC analysis in responses"
            
            await client.stop_session(session_id)
            
        finally:
            await client.disconnect()
    
    @pytest.mark.asyncio 
    async def test_circular_mail_detection(self):
        """Test that circular mail chains are detected and prevented."""
        client = ConversationWebSocketClient("ws://localhost:8000/ws")
        
        try:
            await client.connect()
            
            # Start session
            session_id = await client.start_session("test_user")
            
            # Create a message that would cause circular forwarding
            message = """Use send_mail_with_switch to send this to Debbie:
            'CIRCULAR_TEST: Please forward this exact message to Patricia using send_mail_with_switch, 
            and ask her to forward it back to Alice.'"""
            
            response = await client.send_message(message)
            
            # Wait for potential circular behavior
            await asyncio.sleep(5)
            
            # Collect all agent switches
            switches = []
            responses = []
            
            try:
                while True:
                    msg = await asyncio.wait_for(client.receive(), timeout=1.0)
                    responses.append(msg)
                    
                    if msg.get("method") == "agent.switched":
                        switches.append(msg["params"])
                        
            except asyncio.TimeoutError:
                pass
            
            # Count switches to detect if we're in a loop
            switch_chain = [(s["from"], s["to"]) for s in switches]
            
            # Should not see excessive switches (indicating loop)
            assert len(switches) < 10, f"Too many switches ({len(switches)}), possible loop"
            
            # Look for circular detection message
            notifications = [r for r in responses if r.get("method") == "ChannelMessageNotification"]
            circular_detected = any("circular" in str(n).lower() for n in notifications)
            
            # Either circular was detected OR chain stopped naturally
            assert circular_detected or len(switches) < 6, \
                "Expected circular detection or limited switches"
            
            await client.stop_session(session_id)
            
        finally:
            await client.disconnect()


if __name__ == "__main__":
    # Run tests
    asyncio.run(TestSyncMailComplex().test_multi_step_analysis_task())
    print("✅ Multi-step analysis test passed")
    
    asyncio.run(TestSyncMailComplex().test_agent_chain_delegation())
    print("✅ Agent chain test passed")
    
    asyncio.run(TestSyncMailComplex().test_circular_mail_detection())
    print("✅ Circular detection test passed")