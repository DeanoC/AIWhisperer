"""
Test scenarios for Debbie the Debugger.
Demonstrates various debugging situations and Debbie's responses.

NOTE: This test file is meant for manual testing and demonstration.
It is skipped in CI due to async fixture compatibility issues.
"""

import pytest

pytestmark = pytest.mark.skip(reason="Manual test file - async fixture issues in CI")

import asyncio
import json
import time
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
import pytest

# Add parent directory to path for imports
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ai_whisperer.extensions.batch.debbie_integration import DebbieDebugger, DebbieFactory
from ai_whisperer.extensions.batch.monitoring import MonitoringEvent, AnomalyAlert
from ai_whisperer.extensions.batch.websocket_interceptor import MessageDirection, MessageType
from ai_whisperer.core.logging import LogSource, LogLevel


class MockSessionManager:
    """Mock session manager for testing"""
    
    def __init__(self):
        self.sessions = {}
        self.current_session_id = None
        self.message_handlers = []
        
    def create_session(self, session_id: str, user_id: str = "test_user"):
        """Create a mock session"""
        self.sessions[session_id] = {
            'id': session_id,
            'user_id': user_id,
            'start_time': datetime.now(),
            'messages': [],
            'state': 'active',
            'last_activity': datetime.now()
        }
        self.current_session_id = session_id
        return session_id
    
    def get_session_data(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get session data"""
        return self.sessions.get(session_id)
    
    def is_session_active(self, session_id: str) -> bool:
        """Check if session is active"""
        session = self.sessions.get(session_id)
        return session and session['state'] == 'active'
    
    def add_message(self, session_id: str, message_type: str, content: str, 
                   tool_name: Optional[str] = None):
        """Add a message to session history"""
        session = self.sessions.get(session_id)
        if session:
            message = {
                'timestamp': datetime.now().isoformat(),
                'type': message_type,
                'content': content
            }
            if tool_name:
                message['tool_name'] = tool_name
            session['messages'].append(message)
            session['last_activity'] = datetime.now()
    
    def simulate_stall(self, session_id: str, duration_seconds: int):
        """Simulate a stall by setting last activity in the past"""
        session = self.sessions.get(session_id)
        if session:
            session['last_activity'] = datetime.now() - timedelta(seconds=duration_seconds)


@pytest.fixture
async def setup_debbie():
    """Set up Debbie with mock session manager"""
    session_manager = MockSessionManager()
    debbie = DebbieFactory.create_default(session_manager)
    
    # Start Debbie
    await debbie.start()
    
    yield debbie, session_manager
    
    # Cleanup
    await debbie.stop()


class TestScenarios:
    """Test scenarios for Debbie"""
    
    @pytest.mark.asyncio
    async def test_scenario_1_stall_detection_and_recovery(self, setup_debbie):
        """
        Scenario 1: Agent stalls after tool execution
        Expected: Debbie detects stall and injects continuation prompt
        """
        print("\n=== Scenario 1: Stall Detection and Recovery ===")
        
        debbie, session_manager = setup_debbie
        
        # Create a session
        session_id = session_manager.create_session("test_session_1")
        
        # Simulate normal activity
        session_manager.add_message(session_id, "user_message", "List the RFCs")
        session_manager.add_message(session_id, "tool_execution", "Executing list_rfcs", "list_rfcs")
        session_manager.add_message(session_id, "tool_result", "Found 3 RFCs")
        
        # Simulate stall (no activity for 35 seconds)
        session_manager.simulate_stall(session_id, 35)
        
        # Start monitoring this session
        await debbie.monitor.start_monitoring(session_id)
        
        # Wait for monitoring cycle
        await asyncio.sleep(6)  # Wait for check interval
        
        # Check results
        metrics = debbie.monitor.get_session_metrics(session_id)
        assert metrics is not None
        
        print(f"Session metrics: {json.dumps(metrics, indent=2)}")
        
        # Check if intervention was triggered
        intervention_history = debbie.orchestrator.executor.history.get_session_history(session_id)
        print(f"Interventions: {len(intervention_history)}")
        
        if intervention_history:
            latest = intervention_history[-1]
            print(f"Latest intervention: {latest.strategy.value} - {latest.result.value}")
            assert latest.alert.alert_type == "session_stall"
            assert latest.strategy.value == "prompt_injection"
    
    @pytest.mark.asyncio
    async def test_scenario_2_high_error_rate(self, setup_debbie):
        """
        Scenario 2: High error rate in session
        Expected: Debbie detects errors and suggests recovery
        """
        print("\n=== Scenario 2: High Error Rate Detection ===")
        
        debbie, session_manager = setup_debbie
        
        # Create a session
        session_id = session_manager.create_session("test_session_2")
        
        # Simulate multiple errors
        for i in range(5):
            session_manager.add_message(session_id, "user_message", f"Command {i}")
            session_manager.add_message(session_id, "error", f"Error: Command {i} failed")
        
        # Start monitoring
        await debbie.monitor.start_monitoring(session_id)
        
        # Manually update metrics to simulate error detection
        if session_id in debbie.monitor.monitored_sessions:
            metrics = debbie.monitor.monitored_sessions[session_id]
            metrics.message_count = 10
            metrics.error_count = 5
        
        # Trigger anomaly detection
        recent_events = []
        alerts = debbie.monitor.anomaly_detector.analyze(metrics, recent_events)
        
        print(f"Detected alerts: {[a.alert_type for a in alerts]}")
        
        # Process alerts
        for alert in alerts:
            await debbie.monitor._process_alert(alert)
        
        await asyncio.sleep(2)
        
        # Check interventions
        intervention_history = debbie.orchestrator.executor.history.get_session_history(session_id)
        if intervention_history:
            latest = intervention_history[-1]
            print(f"Intervention for errors: {latest.strategy.value} - {latest.result.value}")
            assert latest.alert.alert_type == "high_error_rate"
    
    @pytest.mark.asyncio
    async def test_scenario_3_tool_loop_detection(self, setup_debbie):
        """
        Scenario 3: Tool being called in a loop
        Expected: Debbie detects loop and intervenes
        """
        print("\n=== Scenario 3: Tool Loop Detection ===")
        
        debbie, session_manager = setup_debbie
        
        # Create a session
        session_id = session_manager.create_session("test_session_3")
        
        # Simulate tool loop
        for i in range(7):
            session_manager.add_message(
                session_id, 
                "tool_execution", 
                f"Executing search_files (attempt {i+1})", 
                "search_files"
            )
            # Small delay between executions
            await asyncio.sleep(0.1)
        
        # Start monitoring
        await debbie.monitor.start_monitoring(session_id)
        
        # Create mock events for anomaly detection
        recent_events = []
        for i in range(7):
            recent_events.append({
                'action': 'tool_execution_start',
                'details': {'tool_name': 'search_files'},
                'timestamp': datetime.now().isoformat()
            })
        
        # Get metrics
        metrics = debbie.monitor.monitored_sessions.get(session_id)
        if metrics:
            alerts = debbie.monitor.anomaly_detector.analyze(metrics, recent_events)
            
            print(f"Tool loop alerts: {[a.alert_type for a in alerts]}")
            
            # Process alerts
            for alert in alerts:
                if alert.alert_type == "tool_loop":
                    print(f"Tool loop detected: {alert.message}")
                    await debbie.monitor._process_alert(alert)
    
    @pytest.mark.asyncio
    async def test_scenario_4_performance_degradation(self, setup_debbie):
        """
        Scenario 4: Performance degradation over time
        Expected: Debbie detects slow responses and analyzes
        """
        print("\n=== Scenario 4: Performance Degradation ===")
        
        debbie, session_manager = setup_debbie
        
        # Create session
        session_id = session_manager.create_session("test_session_4")
        
        # Start monitoring
        await debbie.monitor.start_monitoring(session_id)
        
        # Get metrics
        metrics = debbie.monitor.monitored_sessions.get(session_id)
        if metrics:
            # Simulate normal response times
            for i in range(5):
                metrics.update_response_time(100 + i * 10)  # 100-140ms
            
            # Update baseline
            debbie.monitor.anomaly_detector.update_baseline(
                session_id, "response_time", metrics.avg_response_time_ms
            )
            
            # Simulate degradation
            for i in range(5):
                metrics.update_response_time(300 + i * 50)  # 300-500ms
            
            print(f"Average response time: {metrics.avg_response_time_ms:.0f}ms")
            
            # Check for anomalies
            alerts = debbie.monitor.anomaly_detector.analyze(metrics, [])
            
            perf_alerts = [a for a in alerts if a.alert_type == "slow_response"]
            if perf_alerts:
                print(f"Performance alert: {perf_alerts[0].message}")
                assert perf_alerts[0].severity in ["medium", "high"]
    
    @pytest.mark.asyncio
    async def test_scenario_5_websocket_interception(self, setup_debbie):
        """
        Scenario 5: WebSocket message interception
        Expected: Debbie intercepts and analyzes messages
        """
        print("\n=== Scenario 5: WebSocket Message Interception ===")
        
        debbie, session_manager = setup_debbie
        
        # Test message interception
        interceptor = debbie.interceptor
        
        # Simulate session start request
        start_request = json.dumps({
            "jsonrpc": "2.0",
            "id": 1,
            "method": "startSession",
            "params": {"userId": "test_user"}
        })
        
        await interceptor.intercept_message(
            start_request, 
            MessageDirection.OUTGOING,
            "conn_test"
        )
        
        # Simulate session start response
        start_response = json.dumps({
            "jsonrpc": "2.0",
            "id": 1,
            "result": {"sessionId": "ws_session_123"}
        })
        
        await interceptor.intercept_message(
            start_response,
            MessageDirection.INCOMING,
            "conn_test"
        )
        
        # Check statistics
        stats = interceptor.get_statistics()
        print(f"Interceptor stats: {json.dumps(stats, indent=2)}")
        
        assert stats['message_count'] == 2
        assert stats['pending_requests'] == 0  # Request was matched with response
    
    @pytest.mark.asyncio
    async def test_scenario_6_comprehensive_debugging(self, setup_debbie):
        """
        Scenario 6: Comprehensive debugging session
        Expected: Debbie provides full analysis and report
        """
        print("\n=== Scenario 6: Comprehensive Debugging Session ===")
        
        debbie, session_manager = setup_debbie
        
        # Create a complex session
        session_id = session_manager.create_session("test_session_complex")
        
        # Simulate various activities
        session_manager.add_message(session_id, "user_message", "Start complex task")
        session_manager.add_message(session_id, "tool_execution", "Analyzing code", "analyze_code")
        session_manager.add_message(session_id, "tool_result", "Analysis complete")
        session_manager.add_message(session_id, "error", "Memory allocation failed")
        session_manager.add_message(session_id, "tool_execution", "Retrying with smaller batch", "analyze_code")
        
        # Start monitoring
        await debbie.monitor.start_monitoring(session_id)
        
        # Update metrics
        metrics = debbie.monitor.monitored_sessions.get(session_id)
        if metrics:
            metrics.message_count = 5
            metrics.error_count = 1
            metrics.tool_execution_count = 2
            metrics.update_response_time(150)
            metrics.update_response_time(450)  # Slow second attempt
        
        # Wait for monitoring
        await asyncio.sleep(2)
        
        # Get comprehensive analysis
        analysis = await debbie.analyze_session(session_id)
        
        print("\n--- Session Analysis ---")
        print(f"Session ID: {analysis['session_id']}")
        print(f"Metrics: {json.dumps(analysis['metrics'], indent=2)}")
        print(f"Interventions: {analysis['interventions']['count']}")
        print(f"Recommendations: {analysis['recommendations']}")
        
        # Generate debugging report
        report = debbie.get_debugging_report()
        print("\n--- Debugging Report Preview ---")
        print(report[:500] + "...")


async def run_all_scenarios():
    """Run all test scenarios"""
    test = TestScenarios()
    
    # Create test fixtures
    session_manager = MockSessionManager()
    debbie = DebbieFactory.create_default(session_manager)
    
    # Start Debbie
    await debbie.start()
    
    try:
        # Run scenarios
        print("🐛 Running Debbie Test Scenarios...\n")
        
        await test.test_scenario_1_stall_detection_and_recovery((debbie, session_manager))
        await test.test_scenario_2_high_error_rate((debbie, session_manager))
        await test.test_scenario_3_tool_loop_detection((debbie, session_manager))
        await test.test_scenario_4_performance_degradation((debbie, session_manager))
        await test.test_scenario_5_websocket_interception((debbie, session_manager))
        await test.test_scenario_6_comprehensive_debugging((debbie, session_manager))
        
        print("\n✅ All scenarios completed!")
        
    finally:
        # Stop Debbie
        await debbie.stop()


if __name__ == "__main__":
    # Run scenarios
    asyncio.run(run_all_scenarios())