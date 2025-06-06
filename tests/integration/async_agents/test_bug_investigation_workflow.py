"""
Test module: test_bug_investigation_workflow.py
Purpose: TDD tests for bug investigation workflow using async agents

Tests collaborative bug hunting scenarios where agents work together
to diagnose, analyze, and suggest fixes for reported bugs.

Test Scenarios:
- Basic bug investigation with 2 agents
- Full investigation pipeline with multiple specialists
- Urgency-based wake patterns
- Collaborative debugging sessions
- Root cause analysis
"""

import pytest
import asyncio
import json
import tempfile
import shutil
from pathlib import Path
from unittest.mock import Mock, AsyncMock, patch
from typing import Dict, Any, List
from datetime import datetime, timedelta

# These imports will work since we implemented them in earlier phases
from ai_whisperer.services.agents.async_session_manager_v2 import (
    AsyncAgentSessionManager, AsyncAgentSession, AgentState
)
from ai_whisperer.extensions.mailbox.mailbox import get_mailbox, Mail, MessagePriority
from ai_whisperer.utils.path import PathManager


# Mock workflow classes that we'll implement in GREEN phase
try:
    from examples.async_agents.bug_investigation_workflow import BugInvestigationWorkflow
    from examples.async_agents.utils.bug_report import BugReport, BugSeverity
except ImportError:
    # Expected in RED phase - we haven't implemented these yet
    BugInvestigationWorkflow = None
    BugReport = None
    BugSeverity = None


class TestBugInvestigationWorkflow:
    """Test collaborative bug investigation workflow using async agents."""
    
    @pytest.fixture
    def temp_workspace(self):
        """Create temporary workspace with buggy code and logs."""
        temp_dir = tempfile.mkdtemp(prefix="bug_investigation_test_")
        workspace_path = Path(temp_dir) / "workspace"
        output_path = Path(temp_dir) / "output"
        logs_path = Path(temp_dir) / "logs"
        
        # Create directories
        workspace_path.mkdir(parents=True)
        output_path.mkdir(parents=True)
        logs_path.mkdir(parents=True)
        
        # Create sample buggy code
        buggy_code = {
            "user_service.py": '''
class UserService:
    def __init__(self):
        self.users = {}
    
    def get_user(self, user_id):
        # BUG: No error handling for missing user
        return self.users[user_id]
    
    def create_user(self, user_data):
        # BUG: No validation of user_data
        user_id = user_data['id']
        self.users[user_id] = user_data
        return user_id
    
    def delete_user(self, user_id):
        # BUG: No check if user exists
        del self.users[user_id]
''',
            "payment_processor.py": '''
import time

class PaymentProcessor:
    def process_payment(self, amount, card_number):
        # BUG: Card number logged in plain text
        print(f"Processing payment of ${amount} with card {card_number}")
        
        # BUG: No input validation
        if amount > 0:
            time.sleep(1)  # Simulate processing
            return {"status": "success", "transaction_id": "12345"}
        
        # BUG: Negative amounts silently fail
        return {"status": "failed"}
    
    def refund_payment(self, transaction_id, amount):
        # BUG: No verification of original transaction
        return {"status": "refunded", "amount": amount}
''',
            "data_handler.py": '''
def parse_csv_data(file_path):
    # BUG: No file existence check
    with open(file_path, 'r') as f:
        lines = f.readlines()
    
    # BUG: Assumes header exists
    header = lines[0].strip().split(',')
    data = []
    
    # BUG: No error handling for malformed lines
    for line in lines[1:]:
        values = line.strip().split(',')
        row = dict(zip(header, values))
        data.append(row)
    
    return data

def calculate_average(numbers):
    # BUG: Division by zero not handled
    return sum(numbers) / len(numbers)
'''
        }
        
        # Write buggy code files
        for filename, content in buggy_code.items():
            file_path = workspace_path / filename
            file_path.write_text(content)
        
        # Create sample error logs
        error_log = '''
2024-01-15 10:23:45 ERROR: KeyError in user_service.get_user: 'user123'
2024-01-15 10:24:12 ERROR: ValueError in payment_processor: invalid literal for int()
2024-01-15 10:25:33 ERROR: FileNotFoundError in data_handler.parse_csv_data: 'missing.csv'
2024-01-15 10:26:01 ERROR: ZeroDivisionError in data_handler.calculate_average
2024-01-15 10:27:15 ERROR: KeyError in user_service.delete_user: 'user456'
'''
        (logs_path / "application.log").write_text(error_log)
        
        yield workspace_path, output_path, logs_path
        
        # Cleanup
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def session_manager(self, temp_workspace):
        """Create mock AsyncAgentSessionManager for testing."""
        workspace_path, output_path, logs_path = temp_workspace
        
        # Mock configuration
        config = {
            'workspace_path': str(workspace_path),
            'output_path': str(output_path),
            'logs_path': str(logs_path),
            'model': 'mock-model',
            'provider': 'mock'
        }
        
        # Initialize PathManager
        path_manager = PathManager()
        path_manager._workspace_path = workspace_path
        path_manager._output_path = output_path
        path_manager._project_path = workspace_path
        PathManager._instance = path_manager
        
        # Create mock session manager
        mock_manager = Mock(spec=AsyncAgentSessionManager)
        mock_manager.config = config
        mock_manager.sessions = {}
        mock_manager._wake_event_callback = None
        
        # Create mock sessions with state tracking
        async def create_agent_session(agent_id, auto_start=True):
            mock_session = Mock(spec=AsyncAgentSession)
            mock_session.agent_id = agent_id
            mock_session.state = Mock()
            mock_session.state.value = "active"
            mock_manager.sessions[agent_id] = mock_session
            return mock_session
        
        # Mock sleep agent with urgency support
        async def sleep_agent(agent_id, duration_seconds, wake_events=None):
            if agent_id in mock_manager.sessions:
                mock_manager.sessions[agent_id].state.value = "sleeping"
                # Check for high priority wake events
                if wake_events and "high_priority_bug" in wake_events:
                    # Wake immediately for high priority
                    await asyncio.sleep(0.1)
                else:
                    # Normal sleep duration
                    await asyncio.sleep(min(duration_seconds * 0.1, 0.5))
                mock_manager.sessions[agent_id].state.value = "active"
                if mock_manager._wake_event_callback:
                    mock_manager._wake_event_callback({
                        "agent_id": agent_id,
                        "event": "bug_report" if wake_events else "timeout",
                        "time": datetime.now()
                    })
        
        mock_manager.create_agent_session = AsyncMock(side_effect=create_agent_session)
        mock_manager.sleep_agent = AsyncMock(side_effect=sleep_agent)
        mock_manager.wake_agent = AsyncMock()
        mock_manager.broadcast_event = AsyncMock()
        mock_manager.start = AsyncMock()
        mock_manager.stop = AsyncMock()
        
        return mock_manager
    
    @pytest.fixture
    def bug_investigation_workflow(self, temp_workspace):
        """Create BugInvestigationWorkflow instance."""
        if BugInvestigationWorkflow is None:
            pytest.skip("BugInvestigationWorkflow not implemented yet (RED phase)")
        
        workspace_path, output_path, logs_path = temp_workspace
        return BugInvestigationWorkflow(
            workspace_path=workspace_path,
            output_path=output_path,
            logs_path=logs_path
        )
    
    # === BASIC BUG INVESTIGATION TESTS ===
    
    @pytest.mark.asyncio
    async def test_bug_investigation_basic(self, bug_investigation_workflow, session_manager):
        """Test basic bug investigation with Debbie and Alice."""
        # Configure workflow with bug report
        bug_report = {
            "id": "BUG-001",
            "title": "User service crashes when user not found",
            "description": "Getting KeyError when trying to retrieve non-existent user",
            "severity": "high",
            "reported_by": "customer",
            "error_log": "KeyError in user_service.get_user: 'user123'"
        }
        
        workflow_config = {
            "agents": ["d", "a"],  # Debbie and Alice
            "bug_report": bug_report,
            "investigation_depth": "basic"
        }
        
        # Run workflow
        result = await bug_investigation_workflow.run(
            config=workflow_config,
            session_manager=session_manager
        )
        
        # Verify investigation completed
        assert result["status"] == "completed"
        assert "root_cause" in result
        assert "suggested_fix" in result
        assert result["bug_id"] == "BUG-001"
        
        # Verify agents collaborated
        assert len(result["agent_findings"]) >= 2
        assert "d" in result["agent_findings"]  # Debbie's analysis
        assert "a" in result["agent_findings"]  # Alice's code review
        
        # Check specific findings
        assert "KeyError" in result["root_cause"]
        assert "error handling" in result["suggested_fix"].lower()
    
    @pytest.mark.asyncio
    async def test_bug_investigation_full_pipeline(self, bug_investigation_workflow, session_manager):
        """Test full investigation with all available agents."""
        # High severity security bug
        bug_report = {
            "id": "BUG-002", 
            "title": "Credit card numbers exposed in logs",
            "description": "Payment processor logging sensitive card data",
            "severity": "critical",
            "reported_by": "security_team",
            "affected_file": "payment_processor.py"
        }
        
        workflow_config = {
            "agents": ["d", "a", "p", "e"],  # Debbie, Alice, Patricia, Eamonn
            "bug_report": bug_report,
            "investigation_depth": "comprehensive",
            "generate_fix": True
        }
        
        # Run workflow
        result = await bug_investigation_workflow.run(
            config=workflow_config,
            session_manager=session_manager
        )
        
        # Verify comprehensive investigation
        assert result["status"] == "completed"
        assert result["severity_confirmed"] == "critical"
        
        # Check all agents contributed
        assert len(result["agent_findings"]) == 4
        assert result["agent_findings"]["d"]["role"] == "initial_investigation"
        assert result["agent_findings"]["a"]["role"] == "code_analysis"
        assert result["agent_findings"]["p"]["role"] == "fix_planning"
        assert result["agent_findings"]["e"]["role"] == "fix_implementation"
        
        # Verify fix was generated
        assert "proposed_fix" in result
        assert "mask" in result["proposed_fix"].lower() or "redact" in result["proposed_fix"].lower()
        assert result["fix_ready"] is True
    
    # === URGENCY-BASED WAKE TESTS ===
    
    @pytest.mark.asyncio
    async def test_bug_investigation_urgency_wake(self, bug_investigation_workflow, session_manager):
        """Test agents wake immediately for critical bugs."""
        # Critical production bug
        bug_report = {
            "id": "BUG-003",
            "title": "System crash in production",
            "description": "Application crashing on division by zero",
            "severity": "critical",
            "reported_by": "monitoring",
            "urgency": "immediate"
        }
        
        workflow_config = {
            "agents": ["d", "a"],
            "bug_report": bug_report,
            "use_sleep_wake": True,
            "wake_on_severity": ["critical", "high"]
        }
        
        # Track wake events
        wake_times = []
        original_callback = session_manager._wake_event_callback
        
        def track_wake(event):
            wake_times.append(event["time"])
            if original_callback:
                original_callback(event)
        
        session_manager._wake_event_callback = track_wake
        
        # Run workflow
        start_time = datetime.now()
        result = await bug_investigation_workflow.run(
            config=workflow_config,
            session_manager=session_manager
        )
        end_time = datetime.now()
        
        # Verify rapid response
        assert result["status"] == "completed"
        assert len(wake_times) > 0, "Agents should have woken up"
        
        # Check response time for critical bug
        response_time = (end_time - start_time).total_seconds()
        assert response_time < 5, f"Critical bugs should be handled quickly, took {response_time}s"
        
        # Verify urgency was recognized
        assert result["response_priority"] == "immediate"
        assert result["wake_reason"] == "critical_severity"
    
    # === COLLABORATIVE DEBUGGING TESTS ===
    
    @pytest.mark.asyncio
    async def test_bug_investigation_collaborative_debugging(self, bug_investigation_workflow, session_manager):
        """Test agents working together to debug complex issues."""
        # Complex bug requiring multiple perspectives
        bug_report = {
            "id": "BUG-004",
            "title": "Data corruption in user service",
            "description": "Users disappearing after certain operations",
            "severity": "high",
            "reported_by": "qa_team",
            "symptoms": [
                "Users created successfully but missing later",
                "No error logs when users disappear",
                "Happens intermittently"
            ]
        }
        
        workflow_config = {
            "agents": ["d", "a", "t"],  # Debbie, Alice, Tessa
            "bug_report": bug_report,
            "collaborative_mode": True,
            "max_investigation_rounds": 3
        }
        
        # Run workflow
        result = await bug_investigation_workflow.run(
            config=workflow_config,
            session_manager=session_manager
        )
        
        # Verify collaborative investigation
        assert result["status"] == "completed"
        assert result["investigation_rounds"] >= 2
        
        # Check inter-agent communication
        assert result["mailbox_messages_sent"] >= 4  # Multiple exchanges
        assert len(result["collaborative_findings"]) > 0
        
        # Verify they identified the race condition or similar issue
        findings = result["root_cause"].lower()
        assert any(issue in findings for issue in ["race condition", "concurrent", "thread", "synchronization"])
        
        # Check comprehensive solution
        assert "suggested_fix" in result
        assert "test_recommendations" in result  # Tessa's contribution
    
    # === ROOT CAUSE ANALYSIS TESTS ===
    
    @pytest.mark.asyncio
    async def test_bug_investigation_root_cause_analysis(self, bug_investigation_workflow, session_manager):
        """Test deep root cause analysis for systemic issues."""
        # Bug indicating deeper architectural issues
        bug_report = {
            "id": "BUG-005",
            "title": "Multiple related errors in data processing",
            "description": "Several modules failing with similar patterns",
            "severity": "medium",
            "reported_by": "developer",
            "error_patterns": [
                "FileNotFoundError in multiple modules",
                "Unhandled exceptions throughout codebase",
                "No input validation in any module"
            ]
        }
        
        workflow_config = {
            "agents": ["d", "a", "p"],
            "bug_report": bug_report,
            "analysis_mode": "root_cause",
            "check_related_issues": True
        }
        
        # Run workflow
        result = await bug_investigation_workflow.run(
            config=workflow_config,
            session_manager=session_manager
        )
        
        # Verify deep analysis
        assert result["status"] == "completed"
        assert "systemic_issues" in result
        assert len(result["systemic_issues"]) > 0
        
        # Check architectural recommendations
        assert "architectural_recommendations" in result
        recommendations = result["architectural_recommendations"]
        assert any("validation" in rec.lower() for rec in recommendations)
        assert any("error handling" in rec.lower() for rec in recommendations)
        
        # Verify pattern detection
        assert result["pattern_detected"] is True
        assert result["affected_modules"] >= 3
    
    # === ERROR RECOVERY TESTS ===
    
    @pytest.mark.asyncio
    async def test_bug_investigation_error_recovery(self, bug_investigation_workflow, session_manager):
        """Test workflow handles investigation failures gracefully."""
        # Bug with insufficient information
        bug_report = {
            "id": "BUG-006",
            "title": "Something is broken",
            "description": "It doesn't work",
            "severity": "unknown",
            "reported_by": "user"
        }
        
        workflow_config = {
            "agents": ["d", "a"],
            "bug_report": bug_report,
            "handle_incomplete_reports": True,
            "simulate_failures": {
                "a": "timeout"  # Alice times out
            }
        }
        
        # Run workflow
        result = await bug_investigation_workflow.run(
            config=workflow_config,
            session_manager=session_manager
        )
        
        # Should complete despite issues
        assert result["status"] == "completed_with_limitations"
        
        # Check error handling
        assert len(result["errors"]) == 1
        assert result["errors"][0]["agent"] == "a"
        
        # Verify partial results
        assert "d" in result["agent_findings"]  # Debbie still contributed
        assert result["confidence_level"] == "low"  # Due to incomplete info
        
        # Check recommendations for better bug reports
        assert "report_improvements" in result
        assert len(result["report_improvements"]) > 0
    
    # === PERFORMANCE TESTS ===
    
    @pytest.mark.asyncio
    async def test_bug_investigation_performance(self, bug_investigation_workflow, session_manager):
        """Test investigation performance with multiple bugs."""
        # Multiple bug reports to investigate
        bug_reports = [
            {
                "id": f"BUG-{i:03d}",
                "title": f"Issue in module {i}",
                "severity": "medium",
                "reported_by": "automated_scan"
            }
            for i in range(10, 15)
        ]
        
        workflow_config = {
            "agents": ["d", "a"],
            "bug_reports": bug_reports,  # Batch investigation
            "parallel_investigation": True,
            "performance_mode": True
        }
        
        # Measure performance
        start_time = datetime.now()
        result = await bug_investigation_workflow.run(
            config=workflow_config,
            session_manager=session_manager
        )
        end_time = datetime.now()
        
        duration = (end_time - start_time).total_seconds()
        
        # Verify batch processing
        assert result["status"] == "completed"
        assert result["bugs_investigated"] == 5
        
        # Performance checks
        assert duration < 15, f"Should complete batch in under 15s, took {duration:.1f}s"
        assert result["parallel_efficiency"] > 0.5
        
        # Check all bugs were processed
        assert len(result["investigation_results"]) == 5
        for bug_id in [f"BUG-{i:03d}" for i in range(10, 15)]:
            assert bug_id in result["investigation_results"]


class TestBugReportParsing:
    """Test bug report parsing and classification."""
    
    @pytest.mark.asyncio
    async def test_bug_severity_classification(self):
        """Test automatic bug severity classification."""
        if BugReport is None or BugSeverity is None:
            pytest.skip("BugReport not implemented yet (RED phase)")
        
        # Test severity detection from keywords
        test_cases = [
            ("System crash in production", BugSeverity.CRITICAL),
            ("Security vulnerability found", BugSeverity.CRITICAL),
            ("Data loss occurring", BugSeverity.HIGH),
            ("Feature not working correctly", BugSeverity.MEDIUM),
            ("Typo in error message", BugSeverity.LOW),
            ("UI alignment issue", BugSeverity.LOW)
        ]
        
        for description, expected_severity in test_cases:
            report = BugReport(
                title="Test bug",
                description=description
            )
            assert report.severity == expected_severity
    
    @pytest.mark.asyncio
    async def test_bug_report_validation(self):
        """Test bug report validation and enhancement."""
        if BugReport is None:
            pytest.skip("BugReport not implemented yet (RED phase)")
        
        # Minimal bug report
        report = BugReport(
            title="App crashes"
        )
        
        # Should provide validation feedback
        validation = report.validate()
        assert validation["is_valid"] is False
        assert "missing_fields" in validation
        assert "description" in validation["missing_fields"]
        
        # Enhanced report
        report.enhance()
        assert report.description is not None
        assert len(report.required_info) > 0


if __name__ == "__main__":
    # Run tests to see them fail (RED phase)
    pytest.main([__file__, "-v"])