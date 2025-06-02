"""
Tests for Agent E Task Decomposition Engine.
Following TDD principles - these tests are written before implementation.
"""
import pytest
import json
import uuid
from datetime import datetime
from unittest.mock import Mock, AsyncMock, patch
from pathlib import Path

# These imports will fail until we implement the classes
# This is expected in TDD - tests first, implementation second
from ai_whisperer.extensions.agents.task_decomposer import TaskDecomposer
from ai_whisperer.extensions.agents.decomposed_task import DecomposedTask
from ai_whisperer.agents.agent_e_exceptions import (
    InvalidPlanError,
    TaskDecompositionError,
    DependencyCycleError
)



pytestmark = pytest.mark.xfail(reason="Agent E feature in development")
# Mark all tests as xfail - Agent E feature in development

class TestTaskDecomposer:
    """Test the TaskDecomposer class that breaks down plans into executable tasks."""
    
    @pytest.fixture
    def sample_plan(self):
        """Create a sample plan following the plan_generation_schema."""
        return {
            "plan_type": "initial",
            "title": "Implement User Authentication",
            "description": "Add user authentication to the application",
            "agent_type": "planning",
            "tdd_phases": {
                "red": ["Write authentication tests", "Write user model tests"],
                "green": ["Implement authentication logic", "Implement user model"],
                "refactor": ["Optimize authentication flow"]
            },
            "tasks": [
                {
                    "name": "Write authentication tests",
                    "description": "Create comprehensive tests for authentication endpoints",
                    "agent_type": "test_generation",
                    "dependencies": [],
                    "tdd_phase": "red",
                    "validation_criteria": ["Tests exist for login/logout", "Tests cover edge cases"]
                },
                {
                    "name": "Write user model tests",
                    "description": "Create tests for user model and database operations",
                    "agent_type": "test_generation", 
                    "dependencies": [],
                    "tdd_phase": "red",
                    "validation_criteria": ["User CRUD tests exist", "Validation tests exist"]
                },
                {
                    "name": "Implement authentication logic",
                    "description": "Create authentication endpoints and JWT handling",
                    "agent_type": "code_generation",
                    "dependencies": ["Write authentication tests"],
                    "tdd_phase": "green",
                    "validation_criteria": ["All auth tests pass", "JWT tokens generated correctly"]
                },
                {
                    "name": "Implement user model",
                    "description": "Create user model with database schema",
                    "agent_type": "code_generation",
                    "dependencies": ["Write user model tests"],
                    "tdd_phase": "green",
                    "validation_criteria": ["All user tests pass", "Database migrations work"]
                },
                {
                    "name": "Optimize authentication flow",
                    "description": "Refactor authentication for performance and clarity",
                    "agent_type": "code_generation",
                    "dependencies": ["Implement authentication logic", "Implement user model"],
                    "tdd_phase": "refactor",
                    "validation_criteria": ["No performance regression", "Code quality improved"]
                }
            ],
            "validation_criteria": [
                "User can register and login",
                "Authentication is secure",
                "All tests pass"
            ]
        }
    
    @pytest.fixture
    def decomposer(self):
        """Create a TaskDecomposer instance."""
        return TaskDecomposer()
    
    def test_decomposer_initialization(self, decomposer):
        """Test that TaskDecomposer initializes correctly."""
        assert decomposer is not None
        assert hasattr(decomposer, 'decompose_plan')
        assert hasattr(decomposer, 'validate_dependencies')
    
    def test_decompose_simple_plan(self, decomposer, sample_plan):
        """Test decomposing a simple plan into tasks."""
        decomposed_tasks = decomposer.decompose_plan(sample_plan)
        
        assert len(decomposed_tasks) == 5
        assert all(isinstance(task, DecomposedTask) for task in decomposed_tasks)
        
        # Check first task
        first_task = decomposed_tasks[0]
        assert first_task.parent_task_name == "Write authentication tests"
        assert first_task.title.startswith("Create comprehensive tests")
        assert first_task.estimated_complexity in ["simple", "moderate"]
        assert first_task.status == "pending"
    
    def test_task_has_required_fields(self, decomposer, sample_plan):
        """Test that decomposed tasks have all required fields."""
        decomposed_tasks = decomposer.decompose_plan(sample_plan)
        
        for task in decomposed_tasks:
            # Required fields from our schema
            assert hasattr(task, 'task_id') and task.task_id
            assert hasattr(task, 'parent_task_name') and task.parent_task_name
            assert hasattr(task, 'title') and task.title
            assert hasattr(task, 'description') and task.description
            assert hasattr(task, 'context') and task.context
            assert hasattr(task, 'acceptance_criteria') and task.acceptance_criteria
            assert hasattr(task, 'estimated_complexity') and task.estimated_complexity
            assert hasattr(task, 'status') and task.status
            
            # Context should have required subfields
            assert 'files_to_read' in task.context
            assert 'files_to_modify' in task.context
            assert 'technology_stack' in task.context
            assert 'constraints' in task.context
    
    def test_external_agent_prompts_generated(self, decomposer, sample_plan):
        """Test that external agent prompts are generated for each task."""
        decomposed_tasks = decomposer.decompose_plan(sample_plan)
        
        for task in decomposed_tasks:
            assert hasattr(task, 'external_agent_prompts')
            prompts = task.external_agent_prompts
            
            # Should have prompts for our three agents
            assert 'claude_code' in prompts
            assert 'roocode' in prompts
            assert 'github_copilot' in prompts
            
            # Each prompt should have required fields
            for agent_name, agent_prompt in prompts.items():
                assert 'suitable' in agent_prompt
                assert 'prompt' in agent_prompt
                assert 'strengths' in agent_prompt
    
    def test_task_dependencies_preserved(self, decomposer, sample_plan):
        """Test that task dependencies are correctly preserved."""
        decomposed_tasks = decomposer.decompose_plan(sample_plan)
        
        # Create a map of task names to tasks
        task_map = {task.parent_task_name: task for task in decomposed_tasks}
        
        # Check authentication logic depends on tests
        auth_logic = task_map["Implement authentication logic"]
        assert "Write authentication tests" in auth_logic.context.get('dependencies', [])
        
        # Check refactor depends on both implementations
        refactor = task_map["Optimize authentication flow"]
        deps = refactor.context.get('dependencies', [])
        assert "Implement authentication logic" in deps
        assert "Implement user model" in deps
    
    def test_tdd_phase_context_added(self, decomposer, sample_plan):
        """Test that TDD phase context is added to tasks."""
        decomposed_tasks = decomposer.decompose_plan(sample_plan)
        
        red_tasks = [t for t in decomposed_tasks if "test" in t.parent_task_name.lower()]
        green_tasks = [t for t in decomposed_tasks if "implement" in t.parent_task_name.lower()]
        refactor_tasks = [t for t in decomposed_tasks if "optimize" in t.parent_task_name.lower()]
        
        # Red phase tasks should emphasize test-first
        for task in red_tasks:
            assert any("test" in step['description'].lower() 
                      for step in task.execution_strategy.get('steps', []))
        
        # Green phase tasks should mention making tests pass
        for task in green_tasks:
            assert any("pass" in step['description'].lower() 
                      for step in task.execution_strategy.get('steps', []))
    
    def test_invalid_plan_raises_error(self, decomposer):
        """Test that invalid plans raise appropriate errors."""
        invalid_plan = {"title": "Missing required fields"}
        
        with pytest.raises(InvalidPlanError) as exc_info:
            decomposer.decompose_plan(invalid_plan)
        
        assert "tasks" in str(exc_info.value).lower()
    
    def test_circular_dependency_detection(self, decomposer):
        """Test that circular dependencies are detected."""
        circular_plan = {
            "plan_type": "initial",
            "title": "Circular Dependencies",
            "description": "Plan with circular deps",
            "agent_type": "planning",
            "tdd_phases": {"red": [], "green": ["Task A", "Task B"], "refactor": []},
            "tasks": [
                {
                    "name": "Task A",
                    "description": "Depends on B",
                    "agent_type": "code_generation",
                    "dependencies": ["Task B"],
                    "tdd_phase": "green"
                },
                {
                    "name": "Task B", 
                    "description": "Depends on A",
                    "agent_type": "code_generation",
                    "dependencies": ["Task A"],
                    "tdd_phase": "green"
                }
            ],
            "validation_criteria": []
        }
        
        with pytest.raises(DependencyCycleError) as exc_info:
            decomposer.decompose_plan(circular_plan)
        
        assert "circular" in str(exc_info.value).lower()
    
    def test_technology_detection(self, decomposer):
        """Test that technology stack is detected from task descriptions."""
        plan_with_tech = {
            "plan_type": "initial",
            "title": "React TypeScript App",
            "description": "Build a React app with TypeScript",
            "agent_type": "planning",
            "tdd_phases": {"red": ["Write Jest tests"], "green": ["Build React components"], "refactor": []},
            "tasks": [
                {
                    "name": "Write Jest tests",
                    "description": "Write tests using Jest and React Testing Library",
                    "agent_type": "test_generation",
                    "dependencies": [],
                    "tdd_phase": "red"
                },
                {
                    "name": "Build React components",
                    "description": "Create TypeScript React components with hooks",
                    "agent_type": "code_generation", 
                    "dependencies": ["Write Jest tests"],
                    "tdd_phase": "green"
                }
            ],
            "validation_criteria": []
        }
        
        decomposed_tasks = decomposer.decompose_plan(plan_with_tech)
        
        for task in decomposed_tasks:
            tech_stack = task.context.get('technology_stack', {})
            assert tech_stack.get('language') == 'TypeScript'
            assert tech_stack.get('framework') == 'React'
            assert tech_stack.get('testing_framework') == 'Jest'
    
    def test_acceptance_criteria_generation(self, decomposer, sample_plan):
        """Test that acceptance criteria are generated from validation criteria."""
        decomposed_tasks = decomposer.decompose_plan(sample_plan)
        
        for task in decomposed_tasks:
            assert len(task.acceptance_criteria) > 0
            
            # Each criterion should have required fields
            for criterion in task.acceptance_criteria:
                assert 'criterion' in criterion
                assert 'verification_method' in criterion
                assert 'automated' in criterion
                assert isinstance(criterion['automated'], bool)
    
    def test_complexity_estimation(self, decomposer, sample_plan):
        """Test that task complexity is estimated correctly."""
        decomposed_tasks = decomposer.decompose_plan(sample_plan)
        
        valid_complexities = ["trivial", "simple", "moderate", "complex", "very_complex"]
        
        for task in decomposed_tasks:
            assert task.estimated_complexity in valid_complexities
            
            # Test tasks should generally be simpler
            if "test" in task.parent_task_name.lower():
                assert task.estimated_complexity in ["trivial", "simple", "moderate"]
            
            # Refactor tasks might be more complex
            if "refactor" in task.parent_task_name.lower():
                assert task.estimated_complexity in ["moderate", "complex", "very_complex"]


class TestDecomposedTask:
    """Test the DecomposedTask data model."""
    
    def test_task_creation(self):
        """Test creating a DecomposedTask instance."""
        task = DecomposedTask(
            task_id=str(uuid.uuid4()),
            parent_task_name="Test Task",
            title="Create a test task",
            description="This is a test task",
            context={
                "files_to_read": [],
                "files_to_modify": [],
                "technology_stack": {"language": "Python"},
                "constraints": []
            },
            acceptance_criteria=[],
            estimated_complexity="simple",
            status="pending"
        )
        
        assert task.task_id
        assert task.parent_task_name == "Test Task"
        assert task.status == "pending"
    
    def test_task_serialization(self):
        """Test that tasks can be serialized to JSON."""
        task = DecomposedTask(
            task_id=str(uuid.uuid4()),
            parent_task_name="Test Task",
            title="Create a test task",
            description="This is a test task",
            context={"files_to_read": ["test.py"]},
            acceptance_criteria=[{"criterion": "Test passes", "verification_method": "pytest", "automated": True}],
            estimated_complexity="simple",
            status="pending"
        )
        
        # Should be able to convert to dict
        task_dict = task.to_dict()
        assert isinstance(task_dict, dict)
        assert task_dict['task_id'] == task.task_id
        
        # Should be JSON serializable
        json_str = json.dumps(task_dict)
        assert json_str
        
        # Should be able to recreate from dict
        recreated = DecomposedTask.from_dict(task_dict)
        assert recreated.task_id == task.task_id
        assert recreated.parent_task_name == task.parent_task_name
    
    def test_task_status_transitions(self):
        """Test that task status transitions are valid."""
        task = DecomposedTask(
            task_id=str(uuid.uuid4()),
            parent_task_name="Test Task", 
            title="Test",
            description="Test",
            context={},
            acceptance_criteria=[],
            estimated_complexity="simple",
            status="pending"
        )
        
        # Valid transitions
        task.update_status("assigned")
        assert task.status == "assigned"
        
        task.update_status("in_progress")
        assert task.status == "in_progress"
        
        task.update_status("completed")
        assert task.status == "completed"
        
        # Invalid transition - can't go from completed to pending
        with pytest.raises(ValueError):
            task.update_status("pending")
    
    def test_execution_result_recording(self):
        """Test recording execution results."""
        task = DecomposedTask(
            task_id=str(uuid.uuid4()),
            parent_task_name="Test Task",
            title="Test",
            description="Test", 
            context={},
            acceptance_criteria=[],
            estimated_complexity="simple",
            status="in_progress"
        )
        
        # Record successful execution
        task.record_execution_result(
            agent_used="claude_code",
            success=True,
            files_changed=["test.py", "test_test.py"],
            tests_passed=True,
            notes="All tests passed on first try"
        )
        
        assert task.status == "completed"
        assert task.execution_result['success'] is True
        assert len(task.execution_result['files_changed']) == 2
        assert task.execution_result['agent_used'] == "claude_code"
        assert task.execution_result['start_time']
        assert task.execution_result['end_time']


class TestDependencyResolution:
    """Test dependency resolution and validation."""
    
    @pytest.fixture
    def decomposer(self):
        return TaskDecomposer()
    
    def test_simple_dependency_chain(self, decomposer):
        """Test resolving a simple dependency chain."""
        tasks = [
            Mock(parent_task_name="A", context={"dependencies": []}),
            Mock(parent_task_name="B", context={"dependencies": ["A"]}),
            Mock(parent_task_name="C", context={"dependencies": ["B"]})
        ]
        
        execution_order = decomposer.resolve_dependencies(tasks)
        
        assert len(execution_order) == 3
        assert execution_order[0].parent_task_name == "A"
        assert execution_order[1].parent_task_name == "B"
        assert execution_order[2].parent_task_name == "C"
    
    def test_parallel_dependencies(self, decomposer):
        """Test resolving tasks that can run in parallel."""
        tasks = [
            Mock(parent_task_name="A", context={"dependencies": []}),
            Mock(parent_task_name="B", context={"dependencies": []}),
            Mock(parent_task_name="C", context={"dependencies": ["A", "B"]}),
            Mock(parent_task_name="D", context={"dependencies": ["A"]})
        ]
        
        execution_order = decomposer.resolve_dependencies(tasks)
        
        # A and B can run in parallel (both have no deps)
        first_batch = [t.parent_task_name for t in execution_order[:2]]
        assert "A" in first_batch
        assert "B" in first_batch
        
        # C must come after both A and B
        c_index = next(i for i, t in enumerate(execution_order) if t.parent_task_name == "C")
        assert c_index > 1
    
    def test_missing_dependency_error(self, decomposer):
        """Test that missing dependencies raise an error."""
        tasks = [
            Mock(parent_task_name="A", context={"dependencies": ["NonExistent"]}),
            Mock(parent_task_name="B", context={"dependencies": []})
        ]
        
        with pytest.raises(TaskDecompositionError) as exc_info:
            decomposer.resolve_dependencies(tasks)
        
        assert "nonexistent" in str(exc_info.value).lower()


class TestExternalAgentPromptGeneration:
    """Test generation of prompts for external agents."""
    
    @pytest.fixture 
    def decomposer(self):
        return TaskDecomposer()
    
    def test_claude_code_prompt_generation(self, decomposer):
        """Test generating prompts optimized for Claude Code."""
        task = Mock(
            parent_task_name="Write authentication tests",
            description="Create comprehensive tests for authentication endpoints",
            context={
                "technology_stack": {"language": "Python", "framework": "FastAPI", "testing_framework": "pytest"},
                "files_to_read": ["auth.py"],
                "constraints": ["Must test JWT validation"]
            },
            acceptance_criteria=[
                {"criterion": "Tests cover login endpoint", "verification_method": "pytest", "automated": True}
            ]
        )
        
        prompt_data = decomposer.generate_claude_code_prompt(task)
        
        assert isinstance(prompt_data, dict)
        assert 'prompt' in prompt_data
        prompt = prompt_data['prompt']
        
        assert "pytest" in prompt
        assert "FastAPI" in prompt
        assert "JWT" in prompt
        assert "TDD" in prompt  # Should mention test-driven development
        assert "auth.py" in prompt  # Should reference files to read
    
    def test_github_copilot_prompt_generation(self, decomposer):
        """Test generating prompts optimized for GitHub Copilot."""
        task = Mock(
            parent_task_name="Implement user model",
            description="Create user model with database schema",
            context={
                "technology_stack": {"language": "Python", "framework": "SQLAlchemy"},
                "files_to_modify": ["models/user.py"],
                "constraints": ["Use UUID for primary key"]
            }
        )
        
        prompt_data = decomposer.generate_github_copilot_prompt(task)
        
        assert isinstance(prompt_data, dict)
        assert 'prompt' in prompt_data
        prompt = prompt_data['prompt']
        
        assert "agent mode" in prompt.lower()  # Should specify agent mode
        assert "SQLAlchemy" in prompt
        assert "UUID" in prompt
        assert "models/user.py" in prompt
    
    def test_agent_suitability_assessment(self, decomposer):
        """Test assessing which agents are suitable for different tasks."""
        test_task = Mock(
            parent_task_name="Write tests",
            description="Write unit tests",
            context={"technology_stack": {"testing_framework": "pytest"}}
        )
        
        refactor_task = Mock(
            parent_task_name="Refactor authentication",
            description="Refactor across multiple files",
            context={"files_to_modify": ["auth.py", "models.py", "views.py"]}
        )
        
        # Claude Code should be good for TDD tasks
        test_suitability = decomposer.assess_agent_suitability(test_task)
        assert test_suitability['claude_code']['suitable'] is True
        assert 'TDD' in test_suitability['claude_code']['strengths']
        
        # RooCode should be good for multi-file refactoring
        refactor_suitability = decomposer.assess_agent_suitability(refactor_task)
        assert refactor_suitability['roocode']['suitable'] is True
        assert any('multi' in s.lower() for s in refactor_suitability['roocode']['strengths'])