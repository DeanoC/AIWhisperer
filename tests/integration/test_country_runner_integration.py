import pytest
import json
from unittest.mock import MagicMock, patch

from src.ai_whisperer.execution_engine import ExecutionEngine
from src.ai_whisperer.state_management import StateManager
from src.ai_whisperer.plan_parser import PlanParser
from src.ai_whisperer.config import ConfigManager
from src.ai_whisperer.task_selector import TaskSelector

# Mock the AIServiceInteraction
class MockAIServiceInteraction:
    def execute_ai_interaction(self, prompt, input_artifacts_content, conversation_history, ai_config):
        # Simulate AI responses based on prompt content
        if "What country is" in prompt:
            return "United Kingdom"
        elif "What is the Capital of that country?" in prompt:
            return "London"
        elif "Is" in prompt and "located in the Capital city?" in prompt:
            # Assuming the landmark is the Tower of London for this mock
            if "Tower of London" in prompt:
                return "Yes"
            else:
                return "No"
        return "Mock AI Response"

# Mock the Planning agent's output for the select_landmark step
def mock_planning_agent_execute(task_def, state_manager, config_manager):
    # Simulate writing the selected landmark to landmark_selection.md
    landmark = "Tower of London" # Choose a specific landmark for the test
    state_manager.update_task_output_artifact(task_def.step_id, "landmark_selection.md", landmark)
    state_manager.update_task_state(task_def.step_id, "COMPLETED")
    return True # Indicate success

# Mock the Validation agent's logic
def mock_validation_agent_execute(task_def, state_manager, config_manager):
    input_artifacts = state_manager.get_task_input_artifacts(task_def.step_id)
    validation_result = "Pass" # Assume validation passes for this mock

    # Simulate writing the validation result to the output artifact
    for output_artifact in task_def.agent_spec.output_artifacts:
        state_manager.update_task_output_artifact(task_def.step_id, output_artifact, validation_result)

    state_manager.update_task_state(task_def.step_id, "COMPLETED")
    return True # Indicate success


@pytest.fixture
def simple_country_plan():
    with open("./tests/simple_run_test_country/simple_run_test_country_aiwhisperer_config.json", 'r') as f:
        plan_data = json.load(f)
    return plan_data

@patch('src.ai_whisperer.ai_service_interaction.AIServiceInteraction', new=MockAIServiceInteraction)
@patch('src.ai_whisperer.execution_engine.ExecutionEngine._execute_planning_agent', side_effect=mock_planning_agent_execute)
@patch('src.ai_whisperer.execution_engine.ExecutionEngine._execute_validation_agent', side_effect=mock_validation_agent_execute)
def test_country_runner_integration(mock_validate, mock_plan, simple_country_plan):
    # Initialize components
    state_manager = StateManager()
    config_manager = ConfigManager() # Use default config or mock as needed
    plan_parser = PlanParser()
    task_selector = TaskSelector(state_manager)
    execution_engine = ExecutionEngine(state_manager, config_manager, task_selector)

    # Load and parse the plan
    plan = plan_parser.parse_plan(simple_country_plan)
    state_manager.initialize_plan(plan)

    # Execute the plan
    while not state_manager.is_plan_complete():
        executable_tasks = task_selector.get_executable_tasks(plan)
        if not executable_tasks:
            # If no tasks are executable, but the plan is not complete, it's a deadlock or error
            if not state_manager.is_plan_complete():
                 pytest.fail("Plan execution stalled: No executable tasks but plan is not complete.")
            break # Plan is complete

        for task_id in executable_tasks:
            task_def = plan.get_task(task_id)
            execution_engine.execute_task(task_def)

    # Assertions
    assert state_manager.is_plan_complete()
    assert state_manager.get_plan_status() == "COMPLETED"

    # Verify key output artifacts exist and have content (based on mocks)
    assert state_manager.get_task_output_artifact("select_landmark", "landmark_selection.md") is not None
    assert state_manager.get_task_output_artifact("ask_country", "ai_response_country.txt") is not None
    assert state_manager.get_task_output_artifact("validate_country", "country_validation_result.md") is not None
    assert state_manager.get_task_output_artifact("ask_capital", "ai_response_capital.txt") is not None
    assert state_manager.get_task_output_artifact("validate_capital", "capital_validation_result.md") is not None
    assert state_manager.get_task_output_artifact("ask_landmark_in_capital", "ai_response_landmark_in_capital.txt") is not None
    assert state_manager.get_task_output_artifact("validate_landmark_in_capital", "landmark_in_capital_validation_result.md") is not None

    # Optional: Assert content of specific output artifacts based on mock responses
    assert "Tower of London" in state_manager.get_task_output_artifact("select_landmark", "landmark_selection.md")
    assert "United Kingdom" in state_manager.get_task_output_artifact("ask_country", "ai_response_country.txt")
    assert "Pass" in state_manager.get_task_output_artifact("validate_country", "country_validation_result.md")
    assert "London" in state_manager.get_task_output_artifact("ask_capital", "ai_response_capital.txt")
    assert "Pass" in state_manager.get_task_output_artifact("validate_capital", "capital_validation_result.md")
    assert "Yes" in state_manager.get_task_output_artifact("ask_landmark_in_capital", "ai_response_landmark_in_capital.txt")
    assert "Pass" in state_manager.get_task_output_artifact("validate_landmark_in_capital", "landmark_in_capital_validation_result.md")
