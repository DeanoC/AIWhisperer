from typing import List, Dict, Any
from .registry import Agent
from pathlib import Path

class PlannerAgentHandler:
    def __init__(self, agent: Agent, engine: Any):
        self.agent = agent
        self.engine = engine
        # Context manager and other dependencies can be added as needed

    def extract_requirements(self, conversation: List[Dict]) -> List[str]:
        # Dummy implementation: collect all user messages
        return [msg["content"] for msg in conversation if msg["role"] == "user"]

    def should_generate_plan(self, conversation: List[Dict]) -> bool:
        # Dummy: trigger if user says 'yes' or conversation is long enough
        return any('yes' in msg["content"].lower() for msg in conversation if msg["role"] == "user") or len(conversation) > 3

    def generate_plan_preview(self, requirements: List[str]) -> Dict:
        # Dummy: return a plan dict
        return {
            "tasks": [
                {"description": req, "status": "pending"} for req in requirements
            ],
            "format": "preview"
        }

    def confirm_plan(self, conversation: List[Dict]) -> bool:
        # Dummy: confirm if user says 'yes'
        return any('yes' in msg["content"].lower() for msg in conversation if msg["role"] == "user")

    def generate_plan_json(self, requirements: List[str]) -> Dict:
        # Dummy: return a plan dict in JSON format
        return {
            "tasks": [
                {"description": req, "status": "pending"} for req in requirements
            ],
            "format": "json"
        }
