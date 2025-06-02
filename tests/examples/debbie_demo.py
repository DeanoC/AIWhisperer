"""
Interactive demonstration of Debbie the Debugger's capabilities.
Shows realistic debugging scenarios with formatted output.
"""

import asyncio
import random
from datetime import datetime, timedelta
from typing import Dict, Any, List
import json

# Add parent directory to path
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ai_whisperer.batch.debbie_integration import DebbieDebugger, DebbieFactory
from ai_whisperer.batch.monitoring import MonitoringEvent, AnomalyAlert
from ai_whisperer.logging.debbie_logger import DebbieLogger


class DebbieDemoLogger:
    """Demo logger that prints formatted output"""
    
    def __init__(self):
        self.start_time = datetime.now()
    
    def log(self, level: str, source: str, message: str, details: Dict[str, Any] = None):
        """Print formatted log message"""
        timestamp = (datetime.now() - self.start_time).total_seconds()
        
        # Choose emoji based on level
        emoji = {
            "INFO": "ℹ️ ",
            "WARNING": "⚠️ ",
            "ERROR": "❌",
            "SUCCESS": "✅",
            "COMMENT": "💭",
            "ACTION": "🔧"
        }.get(level, "•")
        
        # Choose color based on source
        color = {
            "DEBBIE": "\033[94m",      # Blue
            "AGENT": "\033[92m",       # Green
            "SYSTEM": "\033[93m",      # Yellow
            "ERROR": "\033[91m",       # Red
            "SUCCESS": "\033[92m",     # Green
        }.get(source, "\033[0m")
        
        reset = "\033[0m"
        
        print(f"[{timestamp:6.1f}s] {emoji} {color}[{source}]{reset} {message}")
        
        if details:
            for key, value in details.items():
                print(f"           └─ {key}: {value}")


class DebbieDemo:
    """Demonstration scenarios for Debbie"""
    
    def __init__(self):
        self.logger = DebbieDemoLogger()
        self.session_data = {}
    
    async def demo_scenario_1_continuation_stall(self):
        """Demo 1: Agent stalls after tool execution - Debbie fixes it"""
        print("\n" + "="*60)
        print("🎬 DEMO 1: Continuation Stall Recovery")
        print("="*60)
        print("Scenario: Agent Patricia lists RFCs but forgets to continue\n")
        
        # Simulate agent activity
        self.logger.log("INFO", "AGENT", "Received user message: 'Create an RFC for the new feature'")
        await asyncio.sleep(0.5)
        
        self.logger.log("INFO", "AGENT", "I'll list the existing RFCs first to check for duplicates")
        await asyncio.sleep(0.5)
        
        self.logger.log("ACTION", "AGENT", "Executing tool: list_rfcs")
        await asyncio.sleep(1.0)
        
        self.logger.log("SUCCESS", "SYSTEM", "Tool completed successfully", {
            "found": "3 RFCs",
            "duration": "245ms"
        })
        await asyncio.sleep(0.5)
        
        # Agent stalls here - no activity
        self.logger.log("WARNING", "SYSTEM", "No activity detected...")
        
        # Simulate time passing (30 seconds)
        for i in range(3):
            await asyncio.sleep(1.0)
            self.logger.log("INFO", "SYSTEM", f"Waiting... ({(i+1)*10}s)")
        
        # Debbie detects the stall
        self.logger.log("WARNING", "DEBBIE", "Stall detected! Agent inactive for 30s after tool execution", {
            "pattern": "continuation_stall",
            "confidence": "92%"
        })
        await asyncio.sleep(0.5)
        
        self.logger.log("COMMENT", "DEBBIE", "This is a known issue where agents wait for user input after using tools")
        await asyncio.sleep(0.5)
        
        self.logger.log("ACTION", "DEBBIE", "Injecting continuation prompt to unstick the agent")
        await asyncio.sleep(0.5)
        
        self.logger.log("INFO", "SYSTEM", "Message injected: 'Please continue with the task based on the tool results.'")
        await asyncio.sleep(1.0)
        
        # Agent resumes
        self.logger.log("SUCCESS", "AGENT", "Ah yes! Based on the existing RFCs, I'll now create a new one")
        await asyncio.sleep(0.5)
        
        self.logger.log("ACTION", "AGENT", "Executing tool: create_rfc", {
            "title": "New Feature Implementation",
            "author": "Patricia"
        })
        await asyncio.sleep(0.5)
        
        self.logger.log("SUCCESS", "DEBBIE", "Intervention successful! Agent resumed activity", {
            "recovery_time": "2.3s",
            "strategy": "prompt_injection"
        })
    
    async def demo_scenario_2_performance_analysis(self):
        """Demo 2: Performance degradation detection"""
        print("\n" + "="*60)
        print("🎬 DEMO 2: Performance Degradation Detection")
        print("="*60)
        print("Scenario: System gradually slows down during processing\n")
        
        # Normal performance
        self.logger.log("INFO", "SYSTEM", "Processing user requests...")
        
        response_times = [100, 120, 110, 95, 105]  # Normal
        for i, rt in enumerate(response_times):
            await asyncio.sleep(0.3)
            self.logger.log("INFO", "AGENT", f"Processed request {i+1}", {
                "response_time": f"{rt}ms"
            })
        
        self.logger.log("INFO", "DEBBIE", "Establishing performance baseline", {
            "avg_response_time": "106ms"
        })
        
        # Performance degrades
        await asyncio.sleep(1.0)
        self.logger.log("WARNING", "SYSTEM", "Memory usage increasing...")
        
        slow_times = [250, 320, 450, 580, 720]  # Degrading
        for i, rt in enumerate(slow_times):
            await asyncio.sleep(0.5)
            self.logger.log("WARNING", "AGENT", f"Processed request {i+6}", {
                "response_time": f"{rt}ms",
                "status": "SLOW" if rt > 300 else "OK"
            })
        
        # Debbie detects the issue
        await asyncio.sleep(0.5)
        self.logger.log("WARNING", "DEBBIE", "Performance degradation detected!", {
            "current_avg": "464ms",
            "baseline": "106ms",
            "degradation": "4.4x slower"
        })
        
        self.logger.log("ACTION", "DEBBIE", "Executing Python analysis script")
        await asyncio.sleep(0.5)
        
        # Simulate Python script output
        print("\n--- Python Analysis Output ---")
        print("import pandas as pd")
        print("df = pd.DataFrame(performance_logs)")
        print("slow_operations = df[df['duration_ms'] > 300]")
        print(f"\nFound {len(slow_times)} slow operations")
        print("Potential causes:")
        print("  1. Memory pressure (current: 487MB)")
        print("  2. Database connection pool exhausted")
        print("  3. Inefficient algorithm with O(n²) complexity")
        print("--- End Analysis ---\n")
        
        await asyncio.sleep(0.5)
        self.logger.log("COMMENT", "DEBBIE", "Recommending optimization strategies", {
            "suggestion_1": "Implement caching for repeated queries",
            "suggestion_2": "Increase connection pool size",
            "suggestion_3": "Profile and optimize the slow algorithm"
        })
    
    async def demo_scenario_3_error_pattern_recovery(self):
        """Demo 3: Recurring error pattern and recovery"""
        print("\n" + "="*60)
        print("🎬 DEMO 3: Error Pattern Detection & Recovery")
        print("="*60)
        print("Scenario: Agent repeatedly fails with the same error\n")
        
        # Agent tries and fails multiple times
        for attempt in range(3):
            await asyncio.sleep(0.5)
            self.logger.log("INFO", "AGENT", f"Attempt {attempt+1}: Trying to fetch data from API")
            await asyncio.sleep(0.5)
            self.logger.log("ERROR", "SYSTEM", "API request failed", {
                "error": "ConnectionTimeout",
                "endpoint": "/api/v1/data",
                "timeout": "30s"
            })
            await asyncio.sleep(0.5)
        
        # Debbie recognizes the pattern
        self.logger.log("WARNING", "DEBBIE", "Recurring error pattern detected", {
            "error_type": "ConnectionTimeout",
            "occurrences": 3,
            "pattern": "Same error on all attempts"
        })
        
        await asyncio.sleep(0.5)
        self.logger.log("COMMENT", "DEBBIE", "The API endpoint appears to be unresponsive")
        
        await asyncio.sleep(0.5)
        self.logger.log("ACTION", "DEBBIE", "Injecting error recovery message with alternative approach")
        
        await asyncio.sleep(0.5)
        self.logger.log("INFO", "SYSTEM", "Message injected: 'The API is not responding. Try using the cached data or an alternative data source.'")
        
        await asyncio.sleep(0.5)
        self.logger.log("SUCCESS", "AGENT", "Good idea! I'll use the cached data instead")
        
        await asyncio.sleep(0.5)
        self.logger.log("ACTION", "AGENT", "Executing tool: read_cache", {
            "cache_key": "api_data_backup",
            "max_age": "1 hour"
        })
        
        await asyncio.sleep(0.5)
        self.logger.log("SUCCESS", "DEBBIE", "Error recovery successful!", {
            "strategy": "alternative_approach",
            "resolved": True
        })
    
    async def demo_scenario_4_tool_loop_intervention(self):
        """Demo 4: Tool execution loop detection"""
        print("\n" + "="*60)
        print("🎬 DEMO 4: Tool Loop Detection & Intervention")
        print("="*60)
        print("Scenario: Agent gets stuck in a search loop\n")
        
        search_terms = ["config", "configuration", "config.yaml", "settings", "config*", "*.config"]
        
        self.logger.log("INFO", "AGENT", "Searching for configuration files...")
        
        # Agent searches repeatedly
        for i, term in enumerate(search_terms):
            await asyncio.sleep(0.4)
            self.logger.log("ACTION", "AGENT", f"Executing tool: search_files (attempt {i+1})", {
                "pattern": term,
                "results": "0 files"
            })
        
        # Debbie detects the loop
        await asyncio.sleep(0.5)
        self.logger.log("ERROR", "DEBBIE", "Tool loop detected!", {
            "tool": "search_files",
            "executions": len(search_terms),
            "threshold": 5
        })
        
        await asyncio.sleep(0.5)
        self.logger.log("COMMENT", "DEBBIE", "Agent is searching repeatedly with no results - possible infinite loop")
        
        await asyncio.sleep(0.5)
        self.logger.log("ACTION", "DEBBIE", "Executing state reset intervention")
        
        await asyncio.sleep(0.5)
        self.logger.log("INFO", "SYSTEM", "Message injected: 'The search is not yielding results. Let's reset and try a different approach. What specific file are you looking for?'")
        
        await asyncio.sleep(0.5)
        self.logger.log("SUCCESS", "AGENT", "You're right. I should ask for clarification instead of searching blindly")
        
        await asyncio.sleep(0.5)
        self.logger.log("INFO", "AGENT", "I was looking for the project configuration file. Could you tell me where it's located?")
        
        await asyncio.sleep(0.5)
        self.logger.log("SUCCESS", "DEBBIE", "Loop broken successfully", {
            "strategy": "state_reset",
            "outcome": "Agent asking for clarification"
        })
    
    async def demo_scenario_5_comprehensive_session(self):
        """Demo 5: Complete debugging session with multiple interventions"""
        print("\n" + "="*60)
        print("🎬 DEMO 5: Comprehensive Debugging Session")
        print("="*60)
        print("Scenario: Complex task with multiple issues - Debbie handles all\n")
        
        self.logger.log("INFO", "SYSTEM", "Session started: Complex data processing task")
        
        # Phase 1: Normal start
        await asyncio.sleep(0.5)
        self.logger.log("INFO", "AGENT", "Starting data analysis pipeline")
        await asyncio.sleep(0.5)
        self.logger.log("ACTION", "AGENT", "Loading dataset...")
        await asyncio.sleep(0.5)
        self.logger.log("SUCCESS", "SYSTEM", "Dataset loaded: 50,000 records")
        
        # Phase 2: Memory issue
        await asyncio.sleep(0.5)
        self.logger.log("WARNING", "SYSTEM", "Memory usage: 450MB")
        await asyncio.sleep(0.5)
        self.logger.log("ERROR", "DEBBIE", "Memory spike detected", {
            "current": "450MB",
            "baseline": "150MB",
            "increase": "3x"
        })
        
        # Phase 3: Performance degradation
        await asyncio.sleep(0.5)
        self.logger.log("WARNING", "AGENT", "Processing slowing down...", {
            "records_per_second": 100,
            "expected": 1000
        })
        
        # Phase 4: Debbie's analysis
        await asyncio.sleep(0.5)
        self.logger.log("ACTION", "DEBBIE", "Running comprehensive analysis")
        
        await asyncio.sleep(1.0)
        print("\n--- Debbie's Session Analysis ---")
        print(f"Session Duration: 3m 24s")
        print(f"Messages Processed: 47")
        print(f"Tool Executions: 12")
        print(f"Errors Encountered: 3")
        print(f"Interventions Made: 2")
        print(f"Performance Score: 65/100")
        print("\nKey Issues Identified:")
        print("  1. Memory leak in data processing loop")
        print("  2. Inefficient batch size (processing one at a time)")
        print("  3. Missing error handling for edge cases")
        print("\nRecommendations:")
        print("  1. Process data in batches of 1000")
        print("  2. Implement memory cleanup after each batch")
        print("  3. Add try-catch blocks for data validation")
        print("--- End Analysis ---\n")
        
        await asyncio.sleep(0.5)
        self.logger.log("SUCCESS", "DEBBIE", "Session completed with assistance", {
            "interventions": 2,
            "issues_resolved": 3,
            "time_saved": "~15 minutes"
        })
    
    async def run_all_demos(self):
        """Run all demonstration scenarios"""
        print("\n🐛 Welcome to Debbie the Debugger Demo!\n")
        print("This demonstration shows how Debbie helps debug AIWhisperer sessions")
        print("by detecting issues and automatically intervening to fix them.\n")
        
        demos = [
            self.demo_scenario_1_continuation_stall,
            self.demo_scenario_2_performance_analysis,
            self.demo_scenario_3_error_pattern_recovery,
            self.demo_scenario_4_tool_loop_intervention,
            self.demo_scenario_5_comprehensive_session
        ]
        
        for i, demo in enumerate(demos, 1):
            if i > 1:
                print("\nPress Enter to continue to next demo...")
                input()
            
            await demo()
        
        print("\n" + "="*60)
        print("✅ Demo Complete!")
        print("="*60)
        print("\nDebbie successfully demonstrated:")
        print("  • Automatic stall detection and recovery")
        print("  • Performance degradation analysis")
        print("  • Error pattern recognition")
        print("  • Tool loop intervention")
        print("  • Comprehensive session debugging")
        print("\nDebbie is ready to help debug your AIWhisperer sessions!")


async def main():
    """Main entry point"""
    demo = DebbieDemo()
    await demo.run_all_demos()


if __name__ == "__main__":
    asyncio.run(main())