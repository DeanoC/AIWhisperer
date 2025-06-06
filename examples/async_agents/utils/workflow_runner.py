"""
Module: examples/async_agents/utils/workflow_runner.py
Purpose: Reusable workflow runner for async agent patterns

GREEN Phase: Minimal implementation for workflow pattern tests.
Provides common patterns for multi-agent workflows.

Key Components:
- WorkflowRunner: Main runner class
- Pipeline patterns: Sequential, Parallel
- Monitor patterns: Event-driven workflows
"""

import asyncio
import logging
from typing import Dict, Any, List, Optional, Union
from datetime import datetime
from dataclasses import dataclass, field
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)


@dataclass
class PipelineResult:
    """Result from pipeline execution."""
    execution_order: List[str] = field(default_factory=list)
    timestamps: List[float] = field(default_factory=list)
    agent_times: Dict[str, Dict[str, float]] = field(default_factory=dict)
    parallel_agents_ran_concurrently: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "execution_order": self.execution_order,
            "timestamps": self.timestamps,
            "agent_times": self.agent_times,
            "parallel_agents_ran_concurrently": self.parallel_agents_ran_concurrently
        }


@dataclass
class MonitorResult:
    """Result from monitor execution."""
    events_triggered: int = 0
    agents_woken: List[str] = field(default_factory=list)
    responses_received: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "events_triggered": self.events_triggered,
            "agents_woken": self.agents_woken,
            "responses_received": self.responses_received
        }


class Pipeline(ABC):
    """Abstract base class for workflow pipelines."""
    
    @abstractmethod
    async def run(self) -> Dict[str, Any]:
        """Run the pipeline."""
        pass


class SequentialPipeline(Pipeline):
    """Sequential execution pipeline: A → B → C."""
    
    def __init__(self, steps: List[Dict[str, Any]]):
        """Initialize sequential pipeline."""
        self.steps = steps
        self.result = PipelineResult()
        
    async def run(self) -> Dict[str, Any]:
        """Execute pipeline sequentially."""
        start_time = datetime.now()
        
        for step in self.steps:
            agent_id = step["agent"]
            task = step["task"]
            
            # Record execution
            self.result.execution_order.append(agent_id)
            step_start = datetime.now()
            
            # Simulate agent execution
            await asyncio.sleep(0.5)  # Simulated work
            
            step_end = datetime.now()
            self.result.timestamps.append((step_end - start_time).total_seconds())
            
            logger.info(f"Sequential: Agent {agent_id} completed {task}")
        
        return self.result.to_dict()


class ParallelPipeline(Pipeline):
    """Parallel collaboration pipeline: A → (B || C) → D."""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize parallel pipeline."""
        self.start_agent = config["start"]
        self.parallel_agents = config["parallel"]
        self.aggregator_agent = config["aggregator"]
        self.result = PipelineResult()
        
    async def run(self) -> Dict[str, Any]:
        """Execute pipeline with parallel section."""
        start_time = datetime.now()
        
        # Execute start agent
        self.result.execution_order.append(self.start_agent)
        await asyncio.sleep(0.5)
        
        # Execute parallel agents concurrently
        parallel_tasks = []
        for agent_id in self.parallel_agents:
            task = self._run_parallel_agent(agent_id, start_time)
            parallel_tasks.append(task)
        
        # Wait for all parallel agents
        await asyncio.gather(*parallel_tasks)
        
        # Check if they ran concurrently
        times = [self.result.agent_times[agent_id] for agent_id in self.parallel_agents]
        start_times = [t["start"] for t in times]
        if max(start_times) - min(start_times) < 0.5:
            self.result.parallel_agents_ran_concurrently = True
        
        # Execute aggregator
        self.result.execution_order.append(self.aggregator_agent)
        await asyncio.sleep(0.5)
        
        return self.result.to_dict()
    
    async def _run_parallel_agent(self, agent_id: str, workflow_start: datetime):
        """Run a single agent in parallel."""
        agent_start = (datetime.now() - workflow_start).total_seconds()
        
        self.result.execution_order.append(agent_id)
        await asyncio.sleep(0.5)  # Simulated work
        
        agent_end = (datetime.now() - workflow_start).total_seconds()
        
        self.result.agent_times[agent_id] = {
            "start": agent_start,
            "end": agent_end
        }


class EventMonitor:
    """Event-driven workflow monitor."""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize event monitor."""
        self.monitor_agent = config["monitor_agent"]
        self.check_interval = config["check_interval"]
        self.wake_agents_on = config["wake_agents_on"]
        self.target_agents = config["target_agents"]
        self.result = MonitorResult()
        self._events_queue = asyncio.Queue()
        self._running = False
        
    async def run(self):
        """Run the monitor."""
        self._running = True
        
        while self._running:
            try:
                # Check for events
                event = await asyncio.wait_for(
                    self._events_queue.get(),
                    timeout=self.check_interval
                )
                
                # Process event
                await self._handle_event(event)
                
            except asyncio.TimeoutError:
                # No events, continue monitoring
                await asyncio.sleep(0.1)
            except Exception as e:
                logger.error(f"Monitor error: {e}")
                
    async def trigger_event(self, event_type: str, data: Dict[str, Any]):
        """Trigger an event for the monitor to handle."""
        await self._events_queue.put({
            "type": event_type,
            "data": data,
            "timestamp": datetime.now()
        })
        
    async def _handle_event(self, event: Dict[str, Any]):
        """Handle a triggered event."""
        event_type = event["type"]
        
        if event_type in self.wake_agents_on:
            self.result.events_triggered += 1
            
            # Wake target agents
            for agent_id in self.target_agents:
                self.result.agents_woken.append(agent_id)
                # Simulate agent response
                await asyncio.sleep(0.1)
                self.result.responses_received += 1
                
            logger.info(f"Handled event {event_type}, woke {len(self.target_agents)} agents")
            
    async def get_status(self) -> Dict[str, Any]:
        """Get current monitor status."""
        return self.result.to_dict()
    
    def stop(self):
        """Stop the monitor."""
        self._running = False


class WorkflowRunner:
    """
    Main workflow runner for creating and executing agent workflows.
    
    GREEN Phase: Minimal implementation to make pattern tests pass.
    """
    
    def __init__(self):
        """Initialize workflow runner."""
        self.pipelines = {}
        self.monitors = {}
        
    def create_pipeline(self, name: str, config: Union[List, Dict]) -> Pipeline:
        """
        Create a workflow pipeline.
        
        Args:
            name: Pipeline type ("sequential" or "parallel")
            config: Pipeline configuration
            
        Returns:
            Pipeline instance
        """
        if name == "sequential":
            pipeline = SequentialPipeline(config)
        elif name == "parallel":
            pipeline = ParallelPipeline(config)
        else:
            raise ValueError(f"Unknown pipeline type: {name}")
            
        self.pipelines[name] = pipeline
        return pipeline
        
    def create_monitor(self, name: str, config: Dict[str, Any]) -> EventMonitor:
        """
        Create an event-driven monitor.
        
        Args:
            name: Monitor name
            config: Monitor configuration
            
        Returns:
            EventMonitor instance
        """
        monitor = EventMonitor(config)
        self.monitors[name] = monitor
        return monitor