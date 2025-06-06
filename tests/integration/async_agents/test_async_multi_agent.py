"""
Integration test for async multi-agent workflows.

This demonstrates multiple agents working independently and
coordinating through the mailbox system.
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch

from ai_whisperer.services.agents.async_session_manager import AsyncAgentSessionManager
from ai_whisperer.extensions.mailbox.mailbox import get_mailbox, Mail, MessagePriority


class TestAsyncMultiAgent:
    """Test async multi-agent workflows."""
    
    @pytest.fixture
    def config(self):
        """Test configuration."""
        return {
            "openrouter": {
                "api_key": "test-key",
                "model": "test-model"
            }
        }
    
    @pytest.fixture
    def mailbox(self):
        """Get clean mailbox."""
        mb = get_mailbox()
        mb.clear_all()
        return mb
        
    @pytest.mark.asyncio
    async def test_parallel_agent_workflow(self, config, mailbox):
        """Test agents working in parallel on different tasks."""
        
        # Create manager
        manager = AsyncAgentSessionManager(config)
        await manager.start()
        
        try:
            with patch('ai_whisperer.services.agents.factory.AgentFactory') as mock_factory:
                # Mock configs for different agents
                def get_agent_config(agent_id):
                    config = Mock()
                    if agent_id == "analyzer":
                        config.system_prompt = "I analyze data"
                    elif agent_id == "writer":
                        config.system_prompt = "I write reports"
                    elif agent_id == "reviewer":
                        config.system_prompt = "I review work"
                    return config
                    
                mock_factory.return_value.get_agent_config.side_effect = get_agent_config
                
                # Create agent sessions
                analyzer = await manager.create_agent_session("analyzer")
                writer = await manager.create_agent_session("writer")
                reviewer = await manager.create_agent_session("reviewer")
                
                # Mock AI loops to simulate work
                analyzer.ai_loop = Mock()
                writer.ai_loop = Mock()
                reviewer.ai_loop = Mock()
                
                # Analyzer processes data and sends to writer
                async def analyzer_process(prompt, **kwargs):
                    await asyncio.sleep(0.1)  # Simulate work
                    return {"response": "Analysis complete: 50% positive sentiment"}
                    
                analyzer.ai_loop.process_message = AsyncMock(side_effect=analyzer_process)
                
                # Writer creates report and sends to reviewer
                async def writer_process(prompt, **kwargs):
                    await asyncio.sleep(0.2)  # Simulate work
                    return {"response": "Report written: Sentiment Analysis Report v1"}
                    
                writer.ai_loop.process_message = AsyncMock(side_effect=writer_process)
                
                # Reviewer reviews and approves
                async def reviewer_process(prompt, **kwargs):
                    await asyncio.sleep(0.05)  # Simulate work
                    return {"response": "Review complete: Approved with minor edits"}
                    
                reviewer.ai_loop.process_message = AsyncMock(side_effect=reviewer_process)
                
                # Start workflow - send task to analyzer
                mail = Mail(
                    from_agent="user",
                    to_agent="analyzer",
                    subject="Analyze customer feedback",
                    body="Please analyze the sentiment of recent customer feedback"
                )
                mailbox.send_mail(mail)
                
                # Let agents work
                await asyncio.sleep(1.0)
                
                # Check results
                # Analyzer should have processed the task
                assert analyzer.ai_loop.process_message.called
                
                # Writer should have received results from analyzer
                writer_mail = mailbox.get_mail("writer")
                assert any("Analysis complete" in mail.body for mail in writer_mail)
                
                # Reviewer should have received report from writer
                reviewer_mail = mailbox.get_mail("reviewer")
                assert any("Report written" in mail.body for mail in reviewer_mail)
                
        finally:
            await manager.stop()
            
    @pytest.mark.asyncio
    async def test_agent_sleep_wake_workflow(self, config, mailbox):
        """Test agents sleeping and waking on events."""
        
        manager = AsyncAgentSessionManager(config)
        await manager.start()
        
        try:
            with patch('ai_whisperer.services.agents.factory.AgentFactory') as mock_factory:
                mock_config = Mock()
                mock_config.system_prompt = "Monitor agent"
                mock_factory.return_value.get_agent_config.return_value = mock_config
                
                # Create monitor agent
                monitor = await manager.create_agent_session("monitor")
                monitor.ai_loop = Mock()
                monitor.ai_loop.process_message = AsyncMock(return_value={
                    "response": "Alert processed"
                })
                
                # Set wake events
                await manager.sleep_agent(
                    "monitor",
                    wake_events={"alert", "shutdown"}
                )
                
                # Verify sleeping
                assert monitor.state.value == "sleeping"
                
                # Broadcast alert event
                await manager.broadcast_event("alert", {
                    "level": "high",
                    "message": "CPU usage high"
                })
                
                # Should wake up
                await asyncio.sleep(0.1)
                assert monitor.state.value == "idle"
                
                # Should have wake event in queue
                assert not monitor.task_queue.empty()
                
        finally:
            await manager.stop()
            
    @pytest.mark.asyncio
    async def test_coordinated_multi_agent_task(self, config, mailbox):
        """Test multiple agents coordinating on a complex task."""
        
        manager = AsyncAgentSessionManager(config)
        await manager.start()
        
        try:
            with patch('ai_whisperer.services.agents.factory.AgentFactory') as mock_factory:
                # Mock configs
                def get_agent_config(agent_id):
                    config = Mock()
                    config.system_prompt = f"I am {agent_id}"
                    return config
                    
                mock_factory.return_value.get_agent_config.side_effect = get_agent_config
                
                # Create team of agents
                planner = await manager.create_agent_session("planner")
                coder1 = await manager.create_agent_session("coder1")
                coder2 = await manager.create_agent_session("coder2")
                tester = await manager.create_agent_session("tester")
                
                # Track work done
                work_log = []
                
                # Mock AI loops
                async def planner_work(prompt, **kwargs):
                    work_log.append("planner: created plan")
                    # Send tasks to coders
                    mailbox.send_mail(Mail(
                        from_agent="planner",
                        to_agent="coder1",
                        subject="Implement feature A",
                        body="Please implement the user authentication feature"
                    ))
                    mailbox.send_mail(Mail(
                        from_agent="planner",
                        to_agent="coder2",
                        subject="Implement feature B",
                        body="Please implement the data export feature"
                    ))
                    return {"response": "Plan created and tasks assigned"}
                    
                async def coder1_work(prompt, **kwargs):
                    await asyncio.sleep(0.2)  # Simulate coding
                    work_log.append("coder1: implemented auth")
                    # Send to tester
                    mailbox.send_mail(Mail(
                        from_agent="coder1",
                        to_agent="tester",
                        subject="Test auth feature",
                        body="Auth feature ready for testing"
                    ))
                    return {"response": "Auth feature implemented"}
                    
                async def coder2_work(prompt, **kwargs):
                    await asyncio.sleep(0.3)  # Simulate coding
                    work_log.append("coder2: implemented export")
                    # Send to tester
                    mailbox.send_mail(Mail(
                        from_agent="coder2",
                        to_agent="tester",
                        subject="Test export feature",
                        body="Export feature ready for testing"
                    ))
                    return {"response": "Export feature implemented"}
                    
                async def tester_work(prompt, **kwargs):
                    work_log.append(f"tester: testing {prompt[:20]}...")
                    return {"response": "Tests passed"}
                    
                planner.ai_loop = Mock()
                planner.ai_loop.process_message = AsyncMock(side_effect=planner_work)
                
                coder1.ai_loop = Mock()
                coder1.ai_loop.process_message = AsyncMock(side_effect=coder1_work)
                
                coder2.ai_loop = Mock()
                coder2.ai_loop.process_message = AsyncMock(side_effect=coder2_work)
                
                tester.ai_loop = Mock()
                tester.ai_loop.process_message = AsyncMock(side_effect=tester_work)
                
                # Start workflow
                mailbox.send_mail(Mail(
                    from_agent="user",
                    to_agent="planner",
                    subject="Build new features",
                    body="We need auth and export features"
                ))
                
                # Let agents work
                await asyncio.sleep(1.5)
                
                # Verify workflow
                assert "planner: created plan" in work_log
                assert "coder1: implemented auth" in work_log
                assert "coder2: implemented export" in work_log
                assert any("tester: testing" in log for log in work_log)
                
                # Both coders should have worked in parallel
                assert coder1.ai_loop.process_message.called
                assert coder2.ai_loop.process_message.called
                
        finally:
            await manager.stop()