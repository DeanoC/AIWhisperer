#!/usr/bin/env python3
"""
Quick demonstration of Debbie the Debugger's capabilities.
Shows how Debbie detects and fixes common AIWhisperer issues.
"""

import asyncio
import time
from datetime import datetime, timedelta
from typing import Dict, Any

# Mock classes to simulate AIWhisperer components
class MockSession:
    def __init__(self, session_id: str):
        self.id = session_id
        self.messages = []
        self.last_activity = datetime.now()
        self.state = "active"
        
    def add_message(self, msg_type: str, content: str):
        self.messages.append({
            "type": msg_type,
            "content": content,
            "timestamp": datetime.now()
        })
        self.last_activity = datetime.now()

class DebbieDemo:
    """Simplified Debbie demonstration"""
    
    def __init__(self):
        self.sessions = {}
        self.interventions = []
        
    def log(self, emoji: str, source: str, message: str, **details):
        """Pretty print log messages"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] {emoji} [{source}] {message}")
        if details:
            for key, value in details.items():
                print(f"            └─ {key}: {value}")
    
    async def detect_stall(self, session: MockSession) -> bool:
        """Detect if session is stalled"""
        stall_threshold = 30  # seconds
        time_since_activity = (datetime.now() - session.last_activity).total_seconds()
        
        if time_since_activity > stall_threshold and session.state == "active":
            # Check if last message was a tool execution
            if session.messages and session.messages[-1]["type"] == "tool_result":
                return True
        return False
    
    async def inject_continuation(self, session: MockSession):
        """Inject a continuation prompt"""
        self.log("💉", "DEBBIE", f"Injecting continuation prompt for session {session.id}")
        session.add_message("system", "Please continue with the task based on the tool results.")
        self.interventions.append({
            "session_id": session.id,
            "type": "continuation",
            "timestamp": datetime.now()
        })
    
    async def demo_scenario_1_stall_recovery(self):
        """Demonstrate stall detection and recovery"""
        print("\n" + "="*60)
        print("🎬 SCENARIO 1: Agent Stall After Tool Use")
        print("="*60)
        print("Problem: Agent Patricia gets stuck after listing RFCs\n")
        
        # Create session
        session = MockSession("demo_session_1")
        self.sessions[session.id] = session
        
        # Simulate normal activity
        self.log("💬", "USER", "Create an RFC for the new authentication feature")
        session.add_message("user", "Create an RFC for the new authentication feature")
        await asyncio.sleep(0.5)
        
        self.log("🤖", "PATRICIA", "I'll first list existing RFCs to check for duplicates")
        session.add_message("agent", "I'll first list existing RFCs to check for duplicates")
        await asyncio.sleep(0.5)
        
        self.log("🔧", "TOOL", "Executing: list_rfcs")
        session.add_message("tool_execution", "list_rfcs")
        await asyncio.sleep(0.5)
        
        self.log("✅", "TOOL", "Found 3 RFCs", 
                 RFC1="Authentication Redesign", 
                 RFC2="API Gateway", 
                 RFC3="Database Migration")
        session.add_message("tool_result", "Found 3 RFCs")
        
        # Simulate stall - set last activity to 35 seconds ago
        session.last_activity = datetime.now() - timedelta(seconds=35)
        
        # Debbie detects the stall
        await asyncio.sleep(1)
        if await self.detect_stall(session):
            self.log("⚠️", "DEBBIE", "Stall detected! Agent inactive for >30s after tool use",
                     pattern="continuation_stall",
                     confidence="95%")
            
            self.log("💭", "DEBBIE", "This is a common issue where agents wait for user input after tools")
            
            # Inject continuation
            await self.inject_continuation(session)
            
            # Agent resumes
            await asyncio.sleep(0.5)
            self.log("✨", "PATRICIA", "Thank you! Now I'll create the new RFC...")
            session.add_message("agent", "Creating new RFC")
            
            self.log("🎯", "DEBBIE", "Intervention successful! Agent resumed activity",
                     recovery_time="2.1s",
                     strategy="prompt_injection")
    
    async def demo_scenario_2_error_recovery(self):
        """Demonstrate error pattern detection"""
        print("\n" + "="*60)
        print("🎬 SCENARIO 2: Recurring Error Pattern")
        print("="*60)
        print("Problem: Agent repeatedly fails with the same error\n")
        
        session = MockSession("demo_session_2")
        self.sessions[session.id] = session
        
        # Simulate repeated errors
        for attempt in range(3):
            self.log("🔧", "AGENT", f"Attempt {attempt+1}: Fetching data from API")
            session.add_message("tool_execution", "fetch_api_data")
            await asyncio.sleep(0.3)
            
            self.log("❌", "ERROR", "ConnectionTimeout: API not responding",
                     endpoint="/api/v1/data",
                     timeout="30s")
            session.add_message("error", "ConnectionTimeout")
            await asyncio.sleep(0.3)
        
        # Debbie detects the pattern
        self.log("🔍", "DEBBIE", "Recurring error pattern detected",
                 error_type="ConnectionTimeout",
                 occurrences=3,
                 pattern="Identical errors")
        
        self.log("💭", "DEBBIE", "The API appears to be down. Suggesting alternative approach...")
        
        # Inject recovery suggestion
        self.log("💉", "DEBBIE", "Injecting error recovery message")
        session.add_message("system", "The API is not responding. Try using cached data or an alternative source.")
        
        # Agent recovers
        await asyncio.sleep(0.5)
        self.log("💡", "AGENT", "Good idea! I'll use the cached data instead")
        self.log("✅", "AGENT", "Successfully retrieved data from cache")
        
        self.log("🎯", "DEBBIE", "Error recovery successful!",
                 strategy="alternative_approach")
    
    async def demo_scenario_3_performance_analysis(self):
        """Demonstrate performance monitoring"""
        print("\n" + "="*60)
        print("🎬 SCENARIO 3: Performance Degradation")
        print("="*60)
        print("Problem: System gradually slows down\n")
        
        # Normal performance
        response_times = [95, 102, 98, 105, 99]
        for i, rt in enumerate(response_times):
            self.log("⚡", "SYSTEM", f"Request {i+1} processed", 
                     response_time=f"{rt}ms")
            await asyncio.sleep(0.2)
        
        avg_baseline = sum(response_times) / len(response_times)
        self.log("📊", "DEBBIE", f"Performance baseline established",
                 avg_response=f"{avg_baseline:.0f}ms")
        
        # Performance degrades
        await asyncio.sleep(0.5)
        slow_times = [250, 380, 520, 650, 800]
        for i, rt in enumerate(slow_times):
            status = "⚠️ SLOW" if rt > 300 else "OK"
            self.log("🐌", "SYSTEM", f"Request {i+6} processed {status}",
                     response_time=f"{rt}ms")
            await asyncio.sleep(0.2)
        
        avg_current = sum(slow_times) / len(slow_times)
        degradation = avg_current / avg_baseline
        
        self.log("🚨", "DEBBIE", "Performance degradation detected!",
                 current_avg=f"{avg_current:.0f}ms",
                 baseline=f"{avg_baseline:.0f}ms",
                 degradation=f"{degradation:.1f}x slower")
        
        # Debbie analyzes
        self.log("🔬", "DEBBIE", "Running performance analysis...")
        await asyncio.sleep(0.5)
        
        print("\n    --- Analysis Results ---")
        print("    Potential causes:")
        print("    1. Memory leak (usage increased 3x)")
        print("    2. Database connection pool exhausted")
        print("    3. Inefficient algorithm scaling poorly")
        print("    ")
        print("    Recommendations:")
        print("    • Implement connection pooling")
        print("    • Add caching layer")
        print("    • Profile and optimize hot paths")
        print("    --- End Analysis ---\n")
        
        self.log("💡", "DEBBIE", "Recommendations provided for optimization")
    
    async def run_all_demos(self):
        """Run all demonstration scenarios"""
        print("\n🐛 Welcome to Debbie the Debugger Demo!")
        print("Your AI debugging assistant for AIWhisperer\n")
        
        await self.demo_scenario_1_stall_recovery()
        await asyncio.sleep(1)
        
        await self.demo_scenario_2_error_recovery()
        await asyncio.sleep(1)
        
        await self.demo_scenario_3_performance_analysis()
        
        print("\n" + "="*60)
        print("✅ Demo Complete!")
        print("="*60)
        print("\nDebbie's Capabilities Demonstrated:")
        print("  • Automatic stall detection and recovery")
        print("  • Error pattern recognition and mitigation")
        print("  • Performance degradation analysis")
        print("  • Intelligent intervention strategies")
        print("\nTotal interventions made:", len(self.interventions))
        print("\nDebbie is ready to help debug your AIWhisperer sessions!")


async def main():
    demo = DebbieDemo()
    await demo.run_all_demos()


if __name__ == "__main__":
    asyncio.run(main())