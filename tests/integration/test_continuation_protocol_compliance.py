"""
Test continuation protocol compliance across different models.

This test verifies that AI models properly include continuation signals
in their responses as required by the prompt system.
"""
import pytest
import json
import asyncio
from pathlib import Path
import logging
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


class TestContinuationProtocolCompliance:
    """Test that models comply with the continuation protocol."""
    
    def parse_response_for_continuation(self, response_text: str) -> Optional[Dict]:
        """
        Extract continuation JSON from response text.
        
        The continuation signal should be in the format:
        {"continuation": {"status": "TERMINATE|CONTINUE", "reason": "..."}}
        """
        # Look for JSON objects in the response
        import re
        
        # Pattern to find JSON objects
        json_pattern = r'\{[^{}]*"continuation"[^{}]*\}'
        matches = re.findall(json_pattern, response_text, re.DOTALL)
        
        for match in matches:
            try:
                data = json.loads(match)
                if 'continuation' in data:
                    return data['continuation']
            except json.JSONDecodeError:
                continue
        
        return None
    
    def validate_continuation_signal(self, continuation: Dict) -> bool:
        """Validate that continuation signal has required fields."""
        if not isinstance(continuation, dict):
            return False
        
        # Required fields
        if 'status' not in continuation:
            return False
        
        # Status must be TERMINATE or CONTINUE
        if continuation['status'] not in ['TERMINATE', 'CONTINUE']:
            return False
        
        # Should have a reason
        if 'reason' not in continuation:
            logger.warning("Continuation signal missing 'reason' field")
        
        return True
    
    @pytest.mark.asyncio
    async def test_simple_response_includes_continuation(self):
        """Test that simple responses include continuation signals."""
        from ai_whisperer.interfaces.cli.main import main as cli_main
        
        # Create a simple test conversation
        test_conversation = "What is AIWhisperer?"
        test_file = Path("test_continuation_compliance.txt")
        test_file.write_text(test_conversation)
        
        try:
            # Run conversation replay and capture output
            import subprocess
            result = subprocess.run(
                [
                    "python", "-m", "ai_whisperer.interfaces.cli.main",
                    "--config", "config/main.yaml",
                    "replay", str(test_file),
                    "--timeout", "5"
                ],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            output = result.stdout + result.stderr
            
            # Look for AI response in output
            response_start = output.find("[FINAL]")
            if response_start == -1:
                pytest.fail("No [FINAL] response found in output")
            
            # Extract response text after [FINAL]
            response_text = output[response_start:]
            
            # Check for continuation signal
            continuation = self.parse_response_for_continuation(response_text)
            
            assert continuation is not None, (
                "No continuation signal found in response. "
                "Model is not complying with continuation protocol."
            )
            
            assert self.validate_continuation_signal(continuation), (
                f"Invalid continuation signal: {continuation}"
            )
            
            # For simple questions, should terminate
            assert continuation['status'] == 'TERMINATE', (
                f"Expected TERMINATE for simple question, got: {continuation['status']}"
            )
            
        finally:
            test_file.unlink(missing_ok=True)
    
    @pytest.mark.asyncio
    async def test_tool_response_includes_continuation(self):
        """Test that tool-using responses include continuation signals."""
        from ai_whisperer.interfaces.cli.main import main as cli_main
        
        # Create a test conversation that requires tool use
        test_conversation = "Please read the file README.md"
        test_file = Path("test_tool_continuation_compliance.txt")
        test_file.write_text(test_conversation)
        
        try:
            # Run conversation replay
            import subprocess
            result = subprocess.run(
                [
                    "python", "-m", "ai_whisperer.interfaces.cli.main",
                    "--config", "config/main.yaml",
                    "replay", str(test_file),
                    "--timeout", "10"
                ],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            output = result.stdout + result.stderr
            
            # Should have tool execution
            assert "TOOL CALLS COMPLETED" in output or "EXECUTING TOOL" in output, (
                "No tool execution found"
            )
            
            # Look for final response after tool execution
            # Find the last [FINAL] as there might be multiple
            final_responses = []
            pos = 0
            while True:
                pos = output.find("[FINAL]", pos)
                if pos == -1:
                    break
                final_responses.append(pos)
                pos += 1
            
            if not final_responses:
                pytest.fail("No [FINAL] response found")
            
            # Check the last response (after tool execution)
            last_response_start = final_responses[-1]
            response_text = output[last_response_start:]
            
            # Check for continuation signal
            continuation = self.parse_response_for_continuation(response_text)
            
            assert continuation is not None, (
                "No continuation signal found in tool response. "
                "Model is not complying with continuation protocol after tool use."
            )
            
            assert self.validate_continuation_signal(continuation), (
                f"Invalid continuation signal after tool use: {continuation}"
            )
            
        finally:
            test_file.unlink(missing_ok=True)
    
    @pytest.mark.asyncio
    async def test_continuation_signal_in_streaming(self):
        """Test that continuation signals are included during streaming."""
        # This would require WebSocket connection to test streaming
        # For now, we'll test via conversation replay
        
        test_conversation = "Who are you?"
        test_file = Path("test_streaming_continuation.txt")
        test_file.write_text(test_conversation)
        
        try:
            import subprocess
            result = subprocess.run(
                [
                    "python", "-m", "ai_whisperer.interfaces.cli.main",
                    "--config", "config/main.yaml",
                    "replay", str(test_file),
                    "--timeout", "5"
                ],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            output = result.stdout + result.stderr
            
            # Check that StreamingUpdate notifications include the continuation
            # when the response is complete
            streaming_updates = []
            pos = 0
            while True:
                pos = output.find("StreamingUpdate", pos)
                if pos == -1:
                    break
                # Extract the content after this position
                end_pos = output.find("\n", pos)
                if end_pos != -1:
                    update = output[pos:end_pos]
                    streaming_updates.append(update)
                pos += 1
            
            # At least one streaming update should have the continuation
            found_continuation = False
            for update in streaming_updates:
                if "continuation" in update and "status" in update:
                    found_continuation = True
                    break
            
            assert found_continuation or self.parse_response_for_continuation(output), (
                "No continuation signal found in any part of the response"
            )
            
        finally:
            test_file.unlink(missing_ok=True)
    
    def test_continuation_extraction(self):
        """Test the continuation extraction logic."""
        # Test valid continuation
        response = '[FINAL]\nTask complete.\n{"continuation": {"status": "TERMINATE", "reason": "Done"}}'
        continuation = self.parse_response_for_continuation(response)
        assert continuation is not None
        assert continuation['status'] == 'TERMINATE'
        assert continuation['reason'] == 'Done'
        
        # Test continuation with other text
        response = 'Some response text {"continuation": {"status": "CONTINUE", "reason": "More work"}} and more'
        continuation = self.parse_response_for_continuation(response)
        assert continuation is not None
        assert continuation['status'] == 'CONTINUE'
        
        # Test missing continuation
        response = '[FINAL]\nTask complete with no signal.'
        continuation = self.parse_response_for_continuation(response)
        assert continuation is None
        
        # Test malformed JSON
        response = '[FINAL]\nTask complete {"continuation": {"status": "TERMINATE"'
        continuation = self.parse_response_for_continuation(response)
        assert continuation is None


@pytest.mark.parametrize("model_config", [
    "config/main.yaml",  # Default (Gemini)
    # Could add other model configs here
])
def test_model_compliance_report(model_config):
    """Generate a compliance report for different models."""
    import subprocess
    from pathlib import Path
    
    test_cases = [
        ("Simple question", "What is 2+2?"),
        ("Agent intro", "Who are you?"),
        ("Tool use", "What files are in the current directory?"),
        ("Multi-step", "Create a simple Python hello world script and save it as test.py")
    ]
    
    results = []
    
    for test_name, prompt in test_cases:
        test_file = Path(f"test_compliance_{test_name.replace(' ', '_')}.txt")
        test_file.write_text(prompt)
        
        try:
            result = subprocess.run(
                [
                    "python", "-m", "ai_whisperer.interfaces.cli.main",
                    "--config", model_config,
                    "replay", str(test_file),
                    "--timeout", "10"
                ],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            output = result.stdout + result.stderr
            
            # Extract model name from output
            model_match = output.find("Starting OpenRouter stream for model:")
            model_name = "Unknown"
            if model_match != -1:
                line_end = output.find("\n", model_match)
                model_line = output[model_match:line_end]
                model_name = model_line.split(":")[-1].strip()
            
            # Check for continuation
            test_obj = TestContinuationProtocolCompliance()
            continuation = test_obj.parse_response_for_continuation(output)
            
            results.append({
                "test": test_name,
                "model": model_name,
                "has_continuation": continuation is not None,
                "continuation": continuation,
                "valid": test_obj.validate_continuation_signal(continuation) if continuation else False
            })
            
        finally:
            test_file.unlink(missing_ok=True)
    
    # Generate report
    print("\n=== Continuation Protocol Compliance Report ===")
    print(f"Model Config: {model_config}")
    print("-" * 60)
    
    for result in results:
        status = "✅" if result['has_continuation'] and result['valid'] else "❌"
        print(f"{status} {result['test']}: ", end="")
        if result['has_continuation']:
            print(f"Found - {result['continuation']['status']}")
        else:
            print("NOT FOUND - Model not compliant")
    
    # Overall compliance
    compliant_count = sum(1 for r in results if r['has_continuation'] and r['valid'])
    total_count = len(results)
    compliance_rate = (compliant_count / total_count) * 100 if total_count > 0 else 0
    
    print("-" * 60)
    print(f"Overall Compliance: {compliant_count}/{total_count} ({compliance_rate:.0f}%)")
    
    # Assert at least some compliance
    assert compliance_rate > 0, f"Model {model_name} has 0% continuation protocol compliance!"
    
    return results