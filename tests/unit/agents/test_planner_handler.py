import pytest
from ai_whisperer.agents.planner_handler import PlannerAgentHandler
from ai_whisperer.services.agents.registry import Agent
from pathlib import Path

@pytest.fixture
def planner_agent():
    return Agent(
        agent_id="P",
        name="Patricia the Planner",
        role="planner",
        description="Creates structured implementation plans",
        tool_tags=["filesystem", "analysis", "planning"],
        prompt_file="agent_planner.md",
        context_sources=["workspace_structure", "existing_schemas", "recent_changes"],
        color="#4CAF50"
    )

@pytest.fixture
def handler(planner_agent):
    # Dummy engine and context for now
    class DummyEngine:
        workspace_path = Path("/tmp/workspace")
    return PlannerAgentHandler(planner_agent, DummyEngine())

def test_requirement_extraction(handler):
    conversation = [
        {"role": "user", "content": "I want a feature to export data as CSV."},
        {"role": "agent", "content": "Can you clarify which data should be exported?"},
        {"role": "user", "content": "All user records from the database."}
    ]
    reqs = handler.extract_requirements(conversation)
    assert "export data as csv" in reqs[0].lower()
    assert "user records" in reqs[-1].lower()

def test_plan_generation_trigger(handler):
    conversation = [
        {"role": "user", "content": "I want a feature to export data as CSV."},
        {"role": "agent", "content": "Can you clarify which data should be exported?"},
        {"role": "user", "content": "All user records from the database."},
        {"role": "user", "content": "Yes, that's all."}
    ]
    assert handler.should_generate_plan(conversation)

def test_plan_preview_generation(handler):
    requirements = ["Export all user records as CSV"]
    plan = handler.generate_plan_preview(requirements)
    assert isinstance(plan, dict)
    assert "tasks" in plan
    assert any("export" in t["description"].lower() for t in plan["tasks"])

def test_plan_confirmation_flow(handler):
    conversation = [
        {"role": "user", "content": "I want a feature to export data as CSV."},
        {"role": "agent", "content": "Can you clarify which data should be exported?"},
        {"role": "user", "content": "All user records from the database."},
        {"role": "user", "content": "Yes, that's all."}
    ]
    confirmed = handler.confirm_plan(conversation)
    assert confirmed is True

def test_plan_json_generation(handler):
    requirements = ["Export all user records as CSV"]
    plan = handler.generate_plan_json(requirements)
    assert isinstance(plan, dict)
    assert "tasks" in plan
    assert plan["format"] == "json"
