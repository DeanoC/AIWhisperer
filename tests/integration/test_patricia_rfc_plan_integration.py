"""
Integration tests for Patricia's RFC-to-plan conversion workflow.
Tests the complete flow from RFC creation to plan generation with TDD structure.
"""

import pytest
import json
from pathlib import Path
from unittest.mock import Mock, patch, AsyncMock
from ai_whisperer.batch.script_processor import ScriptProcessor
from ai_whisperer.batch.batch_client import BatchClient


@pytest.mark.integration
class TestPatriciaRFCToPlanIntegration:
    """Test Patricia's RFC-to-plan conversion workflow"""
    
    @pytest.fixture
    def script_processor(self, tmp_path):
        """Create a script processor with test configuration"""
        config = {
            'openrouter': {
                'api_key': 'test-key',
                'model': 'openai/gpt-4',
                'params': {
                    'temperature': 0.7,
                    'max_tokens': 2000
                }
            }
        }
        
        # Create workspace directory
        workspace = tmp_path / "workspace"
        workspace.mkdir()
        
        processor = ScriptProcessor(str(workspace))
        processor.config = config
        return processor
    
    @pytest.fixture
    def batch_script_path(self):
        """Path to the test batch script"""
        return Path(__file__).parent.parent.parent / "scripts" / "test_patricia_rfc_to_plan.json"
    
    @pytest.mark.asyncio
    async def test_rfc_to_plan_conversion(self, script_processor, batch_script_path, tmp_path):
        """Test the complete RFC-to-plan conversion workflow"""
        # Create RFC directory structure
        rfc_dir = tmp_path / "workspace" / ".WHISPER" / "rfc" / "in_progress"
        rfc_dir.mkdir(parents=True)
        
        plans_dir = tmp_path / "workspace" / ".WHISPER" / "plans" / "in_progress"
        plans_dir.mkdir(parents=True)
        
        # Mock the WebSocket client
        with patch('ai_whisperer.batch.batch_client.BatchClient') as mock_client_class:
            mock_client = AsyncMock(spec=BatchClient)
            mock_client_class.return_value = mock_client
            
            # Mock connect/disconnect
            mock_client.connect = AsyncMock()
            mock_client.disconnect = AsyncMock()
            
            # Mock responses for the conversation
            mock_responses = [
                # Response to initial feature request
                {
                    "response": "I'll help you create an RFC for the user avatar feature. Let me start by checking existing RFCs and creating a new one.\n\n[Uses create_rfc to create avatar-display-2025-05-31.md]\n\nGreat! I've created avatar-display-2025-05-31.md (RFC-2025-05-31-0001) for the user avatar feature.",
                    "tool_calls": [{"function": {"name": "create_rfc"}}]
                },
                # Response to additional requirements
                {
                    "response": "Perfect! Let me update the RFC with these specific requirements.\n\n[Uses update_rfc to add details]\n\nI've updated the RFC with the avatar specifications.",
                    "tool_calls": [{"function": {"name": "update_rfc"}}]
                },
                # Response to technical details
                {
                    "response": "Excellent technical details! I'll update the RFC with these implementation specifics.\n\n[Uses update_rfc]\n\nThe RFC has been updated with all the technical requirements.",
                    "tool_calls": [{"function": {"name": "update_rfc"}}]
                },
                # Response to plan conversion request
                {
                    "response": "The RFC looks comprehensive now. I'll convert it into an executable plan following TDD principles.\n\n[Uses create_plan_from_rfc]\n\nI've created a structured plan with tasks following the Red-Green-Refactor cycle.",
                    "tool_calls": [{"function": {"name": "create_plan_from_rfc"}}]
                },
                # Response to show plan request
                {
                    "response": "Here's the detailed plan:\n\n**RED Phase (Tests First):**\n- Write tests for avatar component\n- Write tests for color generation\n- Write tests for theme support\n\n**GREEN Phase (Implementation):**\n- Implement avatar component\n- Add color generation logic\n- Implement theme variants\n\n**REFACTOR Phase:**\n- Optimize rendering\n- Extract reusable utilities",
                    "tool_calls": [{"function": {"name": "read_plan"}}]
                }
            ]
            
            # Configure mock to return responses in sequence
            mock_client.send_message = AsyncMock(side_effect=mock_responses)
            
            # Load and validate the script
            assert batch_script_path.exists(), f"Script not found: {batch_script_path}"
            
            with open(batch_script_path) as f:
                script_data = json.load(f)
            
            # Validate script structure
            assert "conversation" in script_data
            assert len(script_data["conversation"]) > 0
            
            # Process the script
            result = await script_processor.process_script(script_data)
            
            # Verify the workflow completed successfully
            assert result["status"] == "completed"
            assert result["steps_completed"] == len(script_data["conversation"])
            
            # Verify expected tools were called
            tool_calls = []
            for response in result.get("responses", []):
                if isinstance(response, dict) and "tool_calls" in response:
                    for tc in response["tool_calls"]:
                        tool_calls.append(tc["function"]["name"])
            
            expected_tools = script_data["validation"]["expect_tools"]
            for tool in expected_tools:
                assert tool in tool_calls, f"Expected tool '{tool}' was not called"
    
    @pytest.mark.asyncio
    async def test_rfc_plan_synchronization(self, script_processor, tmp_path):
        """Test that plans update when RFCs change"""
        # Create test RFC with existing plan
        rfc_dir = tmp_path / "workspace" / ".WHISPER" / "rfc" / "in_progress"
        rfc_dir.mkdir(parents=True)
        
        rfc_content = {
            "id": "RFC-2025-05-31-0001",
            "title": "User Avatar Display",
            "requirements": ["Show initials"],
            "derived_plans": ["avatar-display-plan-2025-05-31"]
        }
        
        rfc_path = rfc_dir / "avatar-display-2025-05-31.json"
        with open(rfc_path, 'w') as f:
            json.dump(rfc_content, f)
        
        # Create corresponding plan
        plans_dir = tmp_path / "workspace" / ".WHISPER" / "plans" / "in_progress"
        plans_dir.mkdir(parents=True)
        
        plan_content = {
            "name": "avatar-display-plan-2025-05-31",
            "source_rfc": {
                "id": "RFC-2025-05-31-0001",
                "path": "avatar-display-2025-05-31.json",
                "hash": "old-hash"
            },
            "tasks": []
        }
        
        plan_path = plans_dir / "avatar-display-plan-2025-05-31.json"
        with open(plan_path, 'w') as f:
            json.dump(plan_content, f)
        
        # Test update detection
        from ai_whisperer.tools.update_plan_from_rfc_tool import UpdatePlanFromRFCTool
        tool = UpdatePlanFromRFCTool()
        
        # Mock the AI service to return updated plan
        with patch('ai_whisperer.tools.update_plan_from_rfc_tool.OpenRouterAIService') as mock_service:
            mock_ai = Mock()
            mock_service.return_value = mock_ai
            
            # Mock streaming response
            async def mock_stream(*args, **kwargs):
                yield '{"status": "updated", "tasks": ["new tasks"]}'
            
            mock_ai.process_request_streaming = mock_stream
            
            # Update RFC to trigger change detection
            rfc_content["requirements"].append("Support image uploads")
            with open(rfc_path, 'w') as f:
                json.dump(rfc_content, f)
            
            # Execute update
            result = await tool.execute(
                plan_id="avatar-display-plan-2025-05-31"
            )
            
            assert result["status"] == "success"
            assert "updated" in result["message"]
    
    def test_batch_script_validation(self, batch_script_path):
        """Validate the batch test scripts are properly formatted"""
        scripts = [
            "test_patricia_rfc_to_plan.json",
            "test_rfc_plan_sync.json"
        ]
        
        for script_name in scripts:
            script_path = batch_script_path.parent / script_name
            if script_path.exists():
                with open(script_path) as f:
                    data = json.load(f)
                
                # Validate required fields
                assert "metadata" in data
                assert "conversation" in data
                assert isinstance(data["conversation"], list)
                
                # Validate conversation steps
                for step in data["conversation"]:
                    assert "user" in step or "wait_for" in step
                
                print(f"✓ {script_name} is valid")