"""
Practical example of using Debbie to debug a real AIWhisperer session.
Shows how to set up Debbie and interpret her debugging output.
"""

import asyncio
import json
from datetime import datetime
from typing import Dict, Any

# Add parent directory to path
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ai_whisperer.batch.debbie_integration import DebbieFactory, integrate_debbie_with_batch_client
from ai_whisperer.batch.batch_client import BatchClient
from ai_whisperer.tools.workspace_validator_tool import WorkspaceValidatorTool
from ai_whisperer.tools.python_executor_tool import PythonExecutorTool


class PracticalDebuggingExample:
    """Practical examples of debugging with Debbie"""
    
    async def example_1_debug_stuck_agent(self):
        """Example 1: Debug an agent that gets stuck after listing RFCs"""
        print("\n" + "="*60)
        print("📋 EXAMPLE 1: Debugging a Stuck Agent")
        print("="*60)
        print("Problem: Agent Patricia lists RFCs but doesn't continue\n")
        
        # Create script that will cause the agent to stall
        script_content = """# List RFCs and create a new one
List all RFCs in the system
# Agent will stall here waiting for user input
"""
        
        # Save script
        with open("debug_stuck_agent.txt", "w") as f:
            f.write(script_content)
        
        print("1️⃣ Setting up Debbie with default configuration...")
        
        # Create Debbie with default settings
        debbie = DebbieFactory.create_default()
        
        # Configure for this specific issue
        debbie.monitor.config['stall_threshold_seconds'] = 10  # Faster detection for demo
        
        print("2️⃣ Starting Debbie's monitoring system...")
        await debbie.start()
        
        print("3️⃣ Creating batch client with script...")
        
        # Create batch client
        batch_client = BatchClient("debug_stuck_agent.txt")
        
        # Integrate Debbie
        batch_client = await integrate_debbie_with_batch_client(batch_client, debbie)
        
        print("4️⃣ Running script with Debbie monitoring...\n")
        
        # In a real scenario, you would run:
        # await batch_client.run()
        
        # For demo, we'll simulate the key events:
        print("🔍 [DEBBIE] Monitoring session started")
        print("📝 [AGENT] User message: 'List all RFCs in the system'")
        print("🔧 [AGENT] Executing tool: list_rfcs")
        print("✅ [SYSTEM] Tool completed: Found 3 RFCs")
        print("⏳ [SYSTEM] Waiting... no activity for 10s")
        print("⚠️  [DEBBIE] Stall detected! Agent inactive after tool execution")
        print("💭 [DEBBIE] This appears to be a continuation issue")
        print("🔧 [DEBBIE] Injecting continuation prompt...")
        print("💉 [SYSTEM] Message: 'Please continue with the task'")
        print("✅ [AGENT] Resuming: 'Now I'll create the new RFC...'")
        print("🎯 [DEBBIE] Intervention successful!\n")
        
        # Show analysis
        print("5️⃣ Debbie's Analysis:")
        analysis = {
            "issue_detected": "continuation_stall",
            "detection_time": "10.2s",
            "intervention": "prompt_injection",
            "recovery_time": "1.8s",
            "recommendation": "Update agent configuration to auto-continue after tool use"
        }
        
        print(json.dumps(analysis, indent=2))
        
        # Cleanup
        await debbie.stop()
        os.remove("debug_stuck_agent.txt")
    
    async def example_2_validate_workspace(self):
        """Example 2: Use Debbie's tools to validate workspace health"""
        print("\n" + "="*60)
        print("🏥 EXAMPLE 2: Workspace Health Check")
        print("="*60)
        print("Using Debbie's workspace validator tool\n")
        
        # Create workspace validator
        validator = WorkspaceValidatorTool()
        
        print("Running workspace validation...")
        
        # Run validation
        result = validator.execute(
            generate_report=True,
            report_path="workspace_health.md"
        )
        
        if result['success']:
            health = result['health']
            print(f"\n📊 Workspace Health: {health['overall_status']}")
            print(f"📁 Workspace Path: {health['workspace_path']}")
            
            print("\n📈 Summary:")
            for status, count in health['summary'].items():
                emoji = {
                    'pass': '✅',
                    'warning': '⚠️',
                    'fail': '❌',
                    'info': 'ℹ️'
                }.get(status, '•')
                print(f"  {emoji} {status.upper()}: {count}")
            
            if health['recommendations']:
                print("\n💡 Recommendations:")
                for rec in health['recommendations']:
                    print(f"  • {rec}")
            
            print(f"\n📄 Full report saved to: {result.get('report_path', 'N/A')}")
        else:
            print(f"❌ Validation failed: {result.get('error', 'Unknown error')}")
    
    async def example_3_analyze_performance(self):
        """Example 3: Use Python executor to analyze performance"""
        print("\n" + "="*60)
        print("📊 EXAMPLE 3: Performance Analysis with Python")
        print("="*60)
        print("Using Debbie's Python executor for analysis\n")
        
        # Create Python executor
        executor = PythonExecutorTool()
        
        # Performance analysis script
        script = """
# Analyze mock performance data
import statistics

# Simulated response times (ms)
response_times = [95, 102, 98, 250, 380, 450, 520, 103, 97, 99]

# Calculate statistics
avg_time = statistics.mean(response_times)
median_time = statistics.median(response_times)
std_dev = statistics.stdev(response_times)

# Find slow responses
slow_threshold = 200
slow_responses = [t for t in response_times if t > slow_threshold]

print("=== Performance Analysis ===")
print(f"Total requests: {len(response_times)}")
print(f"Average response time: {avg_time:.1f}ms")
print(f"Median response time: {median_time:.1f}ms")
print(f"Standard deviation: {std_dev:.1f}ms")
print(f"\\nSlow responses (>{slow_threshold}ms): {len(slow_responses)}")
print(f"Slow response times: {slow_responses}")

# Identify performance degradation
if len(slow_responses) > len(response_times) * 0.3:
    print("\\n⚠️ WARNING: High percentage of slow responses!")
    print("Possible causes:")
    print("- Memory pressure")
    print("- Database connection issues")
    print("- Inefficient algorithms")
"""
        
        print("Executing performance analysis script...")
        
        # Execute script
        result = executor.execute(script=script)
        
        if result['success']:
            print("\n" + result['result']['output'])
        else:
            print(f"❌ Script failed: {result['result']['error']}")
    
    async def example_4_real_time_monitoring(self):
        """Example 4: Set up real-time monitoring dashboard"""
        print("\n" + "="*60)
        print("📡 EXAMPLE 4: Real-Time Monitoring Setup")
        print("="*60)
        print("Configuring Debbie for different monitoring scenarios\n")
        
        # Show different configuration options
        configs = {
            "🛡️ Conservative": {
                "check_interval_seconds": 10,
                "stall_threshold_seconds": 60,
                "auto_intervention": True,
                "max_interventions_per_session": 5
            },
            "⚡ Aggressive": {
                "check_interval_seconds": 2,
                "stall_threshold_seconds": 15,
                "auto_intervention": True,
                "max_interventions_per_session": 20
            },
            "👀 Monitor Only": {
                "check_interval_seconds": 5,
                "stall_threshold_seconds": 30,
                "auto_intervention": False,
                "max_interventions_per_session": 0
            }
        }
        
        for name, config in configs.items():
            print(f"\n{name} Configuration:")
            print(json.dumps(config, indent=2))
        
        print("\n📊 Example Monitoring Output:")
        print("""
[00:00] 🚀 [DEBBIE] Monitoring started for session_abc123
[00:05] ℹ️  [MONITOR] Health check - OK (2 active sessions)
[00:10] ℹ️  [MONITOR] Metrics: avg_response=125ms, errors=0
[00:15] ⚠️  [MONITOR] Response time increasing: 280ms
[00:20] ⚠️  [DEBBIE] Performance degradation detected
[00:21] 🔧 [DEBBIE] Analyzing with Python script...
[00:23] 💡 [DEBBIE] Recommendation: Check database connection pool
[00:30] ℹ️  [MONITOR] Session completed successfully
[00:31] 📈 [DEBBIE] Session summary: 45 messages, 1 intervention
""")
    
    async def example_5_debugging_workflow(self):
        """Example 5: Complete debugging workflow"""
        print("\n" + "="*60)
        print("🔄 EXAMPLE 5: Complete Debugging Workflow")
        print("="*60)
        print("Step-by-step debugging process with Debbie\n")
        
        workflow = """
# Debugging Workflow with Debbie

## 1. Initial Setup
```python
# Create Debbie with appropriate configuration
debbie = DebbieFactory.create_default()

# Customize for your needs
debbie.monitor.config.update({
    'stall_threshold_seconds': 20,
    'auto_intervention': True
})
```

## 2. Start Monitoring
```python
# Start Debbie
await debbie.start()

# Integrate with your session
batch_client = await integrate_debbie_with_batch_client(
    batch_client, debbie
)
```

## 3. Run Your Task
```python
# Debbie monitors automatically
await batch_client.run()
```

## 4. Real-Time Interventions
- Debbie detects issues as they occur
- Automatically attempts recovery
- Logs all actions for review

## 5. Post-Session Analysis
```python
# Get comprehensive report
report = debbie.get_debugging_report()
print(report)

# Analyze specific session
analysis = await debbie.analyze_session(session_id)
```

## 6. Review Recommendations
- Check intervention history
- Review success rates
- Apply suggested fixes
"""
        
        print(workflow)
        
        print("\n🎯 Key Benefits:")
        print("  ✅ Automatic issue detection")
        print("  ✅ Smart intervention strategies")
        print("  ✅ Comprehensive logging")
        print("  ✅ Performance tracking")
        print("  ✅ Actionable recommendations")
    
    async def run_all_examples(self):
        """Run all practical examples"""
        print("\n🐛 Debbie Practical Examples")
        print("Real-world debugging scenarios and solutions\n")
        
        examples = [
            ("Debug Stuck Agent", self.example_1_debug_stuck_agent),
            ("Workspace Health Check", self.example_2_validate_workspace),
            ("Performance Analysis", self.example_3_analyze_performance),
            ("Real-Time Monitoring", self.example_4_real_time_monitoring),
            ("Complete Workflow", self.example_5_debugging_workflow)
        ]
        
        for i, (name, example) in enumerate(examples, 1):
            if i > 1:
                print("\nPress Enter to continue...")
                input()
            
            await example()
        
        print("\n" + "="*60)
        print("✅ Examples Complete!")
        print("="*60)
        print("\n🚀 Ready to debug with Debbie!")
        print("\nQuick Start:")
        print("  1. debbie = DebbieFactory.create_default()")
        print("  2. await debbie.start()")
        print("  3. Let Debbie monitor and help!")


async def main():
    """Main entry point"""
    examples = PracticalDebuggingExample()
    await examples.run_all_examples()


if __name__ == "__main__":
    asyncio.run(main())