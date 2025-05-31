"""
Task Decomposer for Agent E.
Breaks down Agent P plans into executable tasks for external agents.
"""
import re
import uuid
from typing import List, Dict, Any, Set, Tuple
from collections import defaultdict, deque

from .decomposed_task import DecomposedTask
from .agent_e_exceptions import InvalidPlanError, DependencyCycleError, TaskDecompositionError


class TaskDecomposer:
    """Decomposes plans into executable tasks for external agents."""
    
    def _get_task_dependencies(self, task) -> List[str]:
        """Extract dependencies from a task, handling both real and mock objects."""
        # First check if this is a real DecomposedTask with get_dependencies method
        if hasattr(task, '__class__') and task.__class__.__name__ == 'DecomposedTask':
            if hasattr(task, 'get_dependencies') and callable(task.get_dependencies):
                return task.get_dependencies()
        
        # For Mock objects or other objects, use context attribute
        context = getattr(task, 'context', {})
        if isinstance(context, dict):
            deps = context.get('dependencies', [])
            return deps if isinstance(deps, list) else []
        return []
    
    def __init__(self):
        """Initialize the TaskDecomposer."""
        self.technology_patterns = {
            'language': {
                'Python': r'\b(?:python|py|pytest|pip|django|flask|fastapi)\b',
                'TypeScript': r'\b(?:typescript|ts|tsx|angular|react|vue)\b',
                'JavaScript': r'\b(?:javascript|js|jsx|node|npm|react|vue)\b',
                'Java': r'\b(?:java|spring|maven|gradle|junit)\b',
                'Go': r'\b(?:golang|go\s+mod|go\s+test)\b',
                'Rust': r'\b(?:rust|cargo|rustc)\b',
            },
            'framework': {
                'React': r'\b(?:react|jsx|tsx|hooks|component)\b',
                'FastAPI': r'\b(?:fastapi|pydantic|uvicorn)\b',
                'Django': r'\b(?:django|models\.py|views\.py)\b',
                'Spring': r'\b(?:spring|boot|mvc|@Controller)\b',
                'Express': r'\b(?:express|app\.(?:get|post|put|delete))\b',
            },
            'testing_framework': {
                'pytest': r'\b(?:pytest|py\.test|test_.*\.py)\b',
                'Jest': r'\bjest\b',
                'JUnit': r'\b(?:junit|@Test|assertEquals)\b',
                'Mocha': r'\b(?:mocha|describe|it\s|chai)\b',
                'RSpec': r'\b(?:rspec|describe\s+do|it\s+do)\b',
            }
        }
    
    def decompose_plan(self, plan: Dict[str, Any]) -> List[DecomposedTask]:
        """Decompose a plan into executable tasks."""
        # Validate plan structure
        self._validate_plan(plan)
        
        # Extract tasks from plan
        plan_tasks = plan.get('tasks', [])
        if not plan_tasks:
            raise InvalidPlanError("Plan must contain at least one task")
        
        # Create decomposed tasks
        decomposed_tasks = []
        for task_data in plan_tasks:
            decomposed = self._decompose_single_task(task_data, plan)
            decomposed_tasks.append(decomposed)
        
        # Validate dependencies
        self._validate_dependencies(decomposed_tasks)
        
        # Sort by dependencies
        sorted_tasks = self.resolve_dependencies(decomposed_tasks)
        
        return sorted_tasks
    
    def _validate_plan(self, plan: Dict[str, Any]):
        """Validate that plan has required structure."""
        required_fields = ['tasks', 'tdd_phases', 'validation_criteria']
        for field in required_fields:
            if field not in plan:
                raise InvalidPlanError(f"Plan missing required field: {field}")
        
        # Validate TDD phases
        tdd_phases = plan.get('tdd_phases', {})
        required_phases = ['red', 'green', 'refactor']
        for phase in required_phases:
            if phase not in tdd_phases:
                raise InvalidPlanError(f"Plan missing TDD phase: {phase}")
    
    def _decompose_single_task(self, task_data: Dict[str, Any], plan: Dict[str, Any]) -> DecomposedTask:
        """Decompose a single task from the plan."""
        # Generate unique task ID
        task_id = str(uuid.uuid4())
        
        # Extract basic information
        task_name = task_data.get('name', 'Unnamed Task')
        description = task_data.get('description', '')
        tdd_phase = task_data.get('tdd_phase', 'green')
        dependencies = task_data.get('dependencies', [])
        validation_criteria = task_data.get('validation_criteria', [])
        
        # Detect technology stack
        tech_stack = self._detect_technology_stack(task_name, description, plan)
        
        # Build context
        context = self._build_task_context(task_data, dependencies, tech_stack)
        
        # Generate acceptance criteria
        acceptance_criteria = self._generate_acceptance_criteria(validation_criteria, tdd_phase)
        
        # Estimate complexity
        complexity = self._estimate_complexity(task_data, len(dependencies), len(validation_criteria))
        
        # Create execution strategy
        execution_strategy = self._create_execution_strategy(task_data, tdd_phase)
        
        # Create decomposed task
        task = DecomposedTask(
            task_id=task_id,
            parent_task_name=task_name,
            title=self._generate_task_title(task_name, description),
            description=description,
            context=context,
            acceptance_criteria=acceptance_criteria,
            estimated_complexity=complexity,
            status="pending",
            execution_strategy=execution_strategy
        )
        
        # Generate external agent prompts
        self._generate_external_agent_prompts(task)
        
        return task
    
    def _detect_technology_stack(self, task_name: str, description: str, plan: Dict[str, Any]) -> Dict[str, str]:
        """Detect technology stack from task and plan information."""
        # Include all task descriptions from the plan for better detection
        all_task_descriptions = []
        for task in plan.get('tasks', []):
            all_task_descriptions.append(task.get('description', ''))
            all_task_descriptions.append(task.get('name', ''))
        
        combined_text = f"{task_name} {description} {plan.get('description', '')} {' '.join(all_task_descriptions)}".lower()
        
        tech_stack = {}
        
        # Detect language
        for lang, pattern in self.technology_patterns['language'].items():
            if re.search(pattern, combined_text, re.IGNORECASE):
                tech_stack['language'] = lang
                break
        
        # Detect framework
        for framework, pattern in self.technology_patterns['framework'].items():
            if re.search(pattern, combined_text, re.IGNORECASE):
                tech_stack['framework'] = framework
                break
        
        # Detect testing framework
        for test_fw, pattern in self.technology_patterns['testing_framework'].items():
            match = re.search(pattern, combined_text, re.IGNORECASE)
            if match:
                tech_stack['testing_framework'] = test_fw
                break
        
        return tech_stack
    
    def _build_task_context(self, task_data: Dict[str, Any], dependencies: List[str], 
                          tech_stack: Dict[str, str]) -> Dict[str, Any]:
        """Build context for the task."""
        context = {
            'files_to_read': [],
            'files_to_modify': [],
            'dependencies': dependencies,
            'technology_stack': tech_stack,
            'constraints': []
        }
        
        # Extract file references from description
        description = task_data.get('description', '')
        
        # Find file patterns
        file_pattern = r'(?:(?:src/|tests/|lib/|app/)?[\w\-/]+\.(?:py|js|ts|jsx|tsx|java|go|rs|rb))'
        file_matches = re.findall(file_pattern, description)
        
        # Categorize files
        for file in file_matches:
            if 'test' in file.lower():
                context['files_to_modify'].append(file)
            else:
                context['files_to_read'].append(file)
        
        # Extract constraints from validation criteria
        for criterion in task_data.get('validation_criteria', []):
            if any(keyword in criterion.lower() for keyword in ['must', 'should', 'require']):
                context['constraints'].append(criterion)
        
        return context
    
    def _generate_acceptance_criteria(self, validation_criteria: List[str], tdd_phase: str) -> List[Dict[str, Any]]:
        """Generate acceptance criteria from validation criteria."""
        criteria = []
        
        for criterion in validation_criteria:
            # Determine verification method
            verification = "manual"
            automated = False
            
            if any(keyword in criterion.lower() for keyword in ['test', 'pytest', 'jest', 'coverage']):
                verification = "automated testing"
                automated = True
            elif any(keyword in criterion.lower() for keyword in ['lint', 'type', 'check']):
                verification = "static analysis"
                automated = True
            elif any(keyword in criterion.lower() for keyword in ['performance', 'speed', 'latency']):
                verification = "performance testing"
                automated = True
            
            criteria.append({
                'criterion': criterion,
                'verification_method': verification,
                'automated': automated
            })
        
        # Add TDD-specific criteria
        if tdd_phase == 'red':
            criteria.append({
                'criterion': 'Tests exist and initially fail',
                'verification_method': 'test execution',
                'automated': True
            })
        elif tdd_phase == 'green':
            criteria.append({
                'criterion': 'All tests pass',
                'verification_method': 'test execution',
                'automated': True
            })
        
        return criteria
    
    def _estimate_complexity(self, task_data: Dict[str, Any], dep_count: int, criteria_count: int) -> str:
        """Estimate task complexity based on various factors."""
        # Start with base complexity
        complexity_score = 0
        
        # Factor in description length
        description = task_data.get('description', '')
        if len(description) > 200:
            complexity_score += 2
        elif len(description) > 100:
            complexity_score += 1
        
        # Factor in dependencies
        complexity_score += dep_count
        
        # Factor in validation criteria
        complexity_score += criteria_count // 2
        
        # Check for specific keywords
        complex_keywords = ['refactor', 'migrate', 'optimize', 'architecture', 'security']
        if any(keyword in description.lower() for keyword in complex_keywords):
            complexity_score += 2
        
        # Map score to complexity level
        if complexity_score == 0:
            return "trivial"
        elif complexity_score <= 2:
            return "simple"
        elif complexity_score <= 4:
            return "moderate"
        elif complexity_score <= 7:
            return "complex"
        else:
            return "very_complex"
    
    def _create_execution_strategy(self, task_data: Dict[str, Any], tdd_phase: str) -> Dict[str, Any]:
        """Create execution strategy based on task type and TDD phase."""
        agent_type = task_data.get('agent_type', 'code_generation')
        task_name = task_data.get('name', '').lower()
        
        # Determine approach
        approach = "exploratory"
        if tdd_phase == 'red' or 'test' in agent_type:
            approach = "tdd"
        elif 'refactor' in task_name:
            approach = "refactoring"
        elif 'migrat' in task_data.get('description', '').lower():
            approach = "migration"
        elif 'document' in agent_type:
            approach = "documentation"
        elif 'implement' in task_name:
            approach = "implementation"
        
        # Create steps based on approach
        steps = []
        if approach == "tdd":
            steps = [
                {"order": 1, "description": "Understand requirements and acceptance criteria", "validation": "Requirements clear"},
                {"order": 2, "description": "Write failing tests first", "validation": "Tests fail as expected"},
                {"order": 3, "description": "Run tests to confirm they fail", "validation": "All tests fail"},
                {"order": 4, "description": "Implement minimal code to pass tests", "validation": "Tests pass"},
                {"order": 5, "description": "Refactor if needed", "validation": "Tests still pass"}
            ]
        elif approach == "refactoring":
            steps = [
                {"order": 1, "description": "Ensure tests exist and pass", "validation": "Baseline established"},
                {"order": 2, "description": "Identify refactoring targets", "validation": "Targets identified"},
                {"order": 3, "description": "Make incremental changes", "validation": "Tests pass after each change"},
                {"order": 4, "description": "Verify no regression", "validation": "All tests still pass"}
            ]
        elif approach == "implementation":
            steps = [
                {"order": 1, "description": "Review existing tests and requirements", "validation": "Context understood"},
                {"order": 2, "description": "Implement code to make tests pass", "validation": "Tests pass"},
                {"order": 3, "description": "Ensure all acceptance criteria are met", "validation": "Criteria satisfied"},
                {"order": 4, "description": "Clean up and optimize code", "validation": "Code quality good"}
            ]
        else:
            steps = [
                {"order": 1, "description": "Analyze requirements", "validation": "Understanding complete"},
                {"order": 2, "description": "Implement solution", "validation": "Code complete"},
                {"order": 3, "description": "Test implementation", "validation": "Tests pass"},
                {"order": 4, "description": "Document changes", "validation": "Documentation updated"}
            ]
        
        return {
            "approach": approach,
            "steps": steps
        }
    
    def _generate_task_title(self, task_name: str, description: str) -> str:
        """Generate a clear, action-oriented title."""
        # If we have a good description, use it for the title
        if description:
            # Take first sentence or up to 80 chars
            title = description.split('.')[0]
            if len(title) > 80:
                title = title[:77] + "..."
            return title
        
        # Otherwise use task name if it's descriptive
        if len(task_name) > 10 and not task_name.startswith("Task"):
            return task_name
        
        return task_name
    
    def _generate_external_agent_prompts(self, task: DecomposedTask):
        """Generate prompts optimized for each external agent."""
        # Generate Claude Code prompt
        claude_prompt = self.generate_claude_code_prompt(task)
        task.add_external_agent_prompt('claude_code', claude_prompt)
        
        # Generate RooCode prompt
        roocode_prompt = self.generate_roocode_prompt(task)
        task.add_external_agent_prompt('roocode', roocode_prompt)
        
        # Generate GitHub Copilot prompt
        copilot_prompt = self.generate_github_copilot_prompt(task)
        task.add_external_agent_prompt('github_copilot', copilot_prompt)
    
    def _get_task_attributes(self, task) -> Dict[str, Any]:
        """Extract attributes from task, handling both DecomposedTask and Mock objects."""
        if hasattr(task, '__dict__'):
            # Real DecomposedTask
            return {
                'description': task.description,
                'context': task.context,
                'parent_task_name': task.parent_task_name,
                'acceptance_criteria': task.acceptance_criteria,
                'execution_strategy': task.execution_strategy,
                'estimated_complexity': getattr(task, 'estimated_complexity', 'moderate')
            }
        else:
            # Mock object - use getattr
            return {
                'description': getattr(task, 'description', ''),
                'context': getattr(task, 'context', {}),
                'parent_task_name': getattr(task, 'parent_task_name', ''),
                'acceptance_criteria': getattr(task, 'acceptance_criteria', []),
                'execution_strategy': getattr(task, 'execution_strategy', {}),
                'estimated_complexity': getattr(task, 'estimated_complexity', 'moderate')
            }
    
    def generate_claude_code_prompt(self, task) -> Dict[str, Any]:
        """Generate prompt optimized for Claude Code."""
        # Extract attributes
        attrs = self._get_task_attributes(task)
        
        # Build Claude-optimized prompt
        prompt_parts = []
        
        # Add task description
        prompt_parts.append(f"{attrs['description']}")
        
        # Add technology context
        tech_stack = attrs['context'].get('technology_stack', {})
        if tech_stack:
            tech_str = ", ".join(f"{k}: {v}" for k, v in tech_stack.items())
            prompt_parts.append(f"\nTechnology: {tech_str}")
        
        # Add file context
        if attrs['context'].get('files_to_read'):
            prompt_parts.append(f"\nFiles to read first: {', '.join(attrs['context']['files_to_read'])}")
        if attrs['context'].get('files_to_modify'):
            prompt_parts.append(f"\nFiles to modify: {', '.join(attrs['context']['files_to_modify'])}")
        
        # Add constraints
        if attrs['context'].get('constraints'):
            prompt_parts.append(f"\nConstraints:\n" + "\n".join(f"- {c}" for c in attrs['context']['constraints']))
        
        # Add TDD emphasis for test tasks
        if 'test' in attrs['parent_task_name'].lower() or attrs['execution_strategy'].get('approach') == 'tdd':
            prompt_parts.append("\nUse Test-Driven Development (TDD) approach - write tests first!")
        
        # Add acceptance criteria
        if attrs['acceptance_criteria']:
            prompt_parts.append("\nAcceptance criteria:")
            for criterion in attrs['acceptance_criteria']:
                if isinstance(criterion, dict):
                    prompt_parts.append(f"- {criterion['criterion']}")
                else:
                    prompt_parts.append(f"- {criterion}")
        
        prompt = "\n".join(prompt_parts)
        
        # Build command
        command = f'claude -p "{prompt}" --json'
        
        # Assess suitability
        suitable = True
        strengths = []
        if 'test' in attrs['parent_task_name'].lower():
            strengths.append("TDD")
        if 'git' in attrs['description'].lower():
            strengths.append("Git operations")
        if not attrs['context'].get('files_to_modify') or len(attrs['context']['files_to_modify']) <= 2:
            strengths.append("Focused tasks")
        
        return {
            'suitable': suitable,
            'command': command,
            'prompt': prompt,
            'strengths': strengths or ["General coding", "Exploration"]
        }
    
    def generate_roocode_prompt(self, task) -> Dict[str, Any]:
        """Generate prompt optimized for RooCode."""
        # Extract attributes
        attrs = self._get_task_attributes(task)
        
        prompt_parts = []
        
        # Emphasize multi-file nature if applicable
        files_to_modify = attrs['context'].get('files_to_modify', [])
        if len(files_to_modify) > 2:
            prompt_parts.append(f"This task involves modifying {len(files_to_modify)} files:")
            for file in files_to_modify:
                prompt_parts.append(f"  - {file}")
            prompt_parts.append("")
        
        # Add main description
        prompt_parts.append(attrs['description'])
        
        # Add technology context
        tech_stack = attrs['context'].get('technology_stack', {})
        if tech_stack:
            prompt_parts.append(f"\nUsing: {', '.join(tech_stack.values())}")
        
        # Configuration hints
        config_hints = "Use Claude 3.7 Sonnet model for best results"
        
        # Assess suitability
        suitable = True
        strengths = []
        if len(files_to_modify) > 2:
            strengths.append("Multi-file refactoring")
        if 'refactor' in attrs['parent_task_name'].lower():
            strengths.append("Code refactoring")
        strengths.append("VS Code integration")
        
        return {
            'suitable': suitable,
            'prompt': "\n".join(prompt_parts),
            'configuration_hints': config_hints,
            'strengths': strengths
        }
    
    def generate_github_copilot_prompt(self, task) -> Dict[str, Any]:
        """Generate prompt optimized for GitHub Copilot agent mode."""
        # Extract attributes
        attrs = self._get_task_attributes(task)
        
        prompt_parts = []
        
        # Add agent mode instruction
        prompt_parts.append("Using agent mode, complete the following task:")
        prompt_parts.append("")
        
        # Add task description
        prompt_parts.append(attrs['description'])
        
        # Emphasize iteration for complex tasks
        if attrs['estimated_complexity'] in ['complex', 'very_complex']:
            prompt_parts.append("\nIterate on the solution until all acceptance criteria are met:")
            for criterion in attrs['acceptance_criteria']:
                if isinstance(criterion, dict):
                    prompt_parts.append(f"- {criterion['criterion']}")
                else:
                    prompt_parts.append(f"- {criterion}")
        
        # Add technology context
        tech_stack = attrs['context'].get('technology_stack', {})
        if tech_stack:
            prompt_parts.append(f"\nTechnology stack: {', '.join(tech_stack.values())}")
        
        # Assess suitability
        suitable = True
        strengths = []
        if attrs['estimated_complexity'] in ['complex', 'very_complex']:
            strengths.append("Complex iteration")
        if 'performance' in attrs['description'].lower():
            strengths.append("Performance optimization")
        strengths.append("Autonomous refinement")
        
        return {
            'suitable': suitable,
            'prompt': "\n".join(prompt_parts),
            'mode': 'agent',
            'strengths': strengths
        }
    
    def resolve_dependencies(self, tasks: List[DecomposedTask]) -> List[DecomposedTask]:
        """Resolve task dependencies and return sorted order."""
        # Build task map
        task_map = {task.parent_task_name: task for task in tasks}
        
        # Build dependency graph
        graph = defaultdict(list)
        in_degree = defaultdict(int)
        
        for task in tasks:
            task_name = task.parent_task_name
            if task_name not in in_degree:
                in_degree[task_name] = 0
            
            # Get dependencies using helper method
            dependencies = self._get_task_dependencies(task)
            
            for dep in dependencies:
                if dep not in task_map:
                    raise TaskDecompositionError(f"Missing dependency: {dep}")
                graph[dep].append(task_name)
                in_degree[task_name] += 1
        
        # Detect cycles using DFS
        self._detect_cycles(graph, list(task_map.keys()))
        
        # Topological sort using Kahn's algorithm
        queue = deque([task for task in task_map if in_degree[task] == 0])
        sorted_order = []
        
        while queue:
            current = queue.popleft()
            sorted_order.append(task_map[current])
            
            for neighbor in graph[current]:
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    queue.append(neighbor)
        
        if len(sorted_order) != len(tasks):
            raise DependencyCycleError("Circular dependency detected in task graph")
        
        return sorted_order
    
    def _detect_cycles(self, graph: Dict[str, List[str]], nodes: List[str]):
        """Detect cycles in dependency graph using DFS."""
        WHITE, GRAY, BLACK = 0, 1, 2
        color = {node: WHITE for node in nodes}
        
        def has_cycle(node: str) -> bool:
            if color[node] == GRAY:
                return True
            if color[node] == BLACK:
                return False
            
            color[node] = GRAY
            for neighbor in graph.get(node, []):
                if has_cycle(neighbor):
                    return True
            color[node] = BLACK
            return False
        
        for node in nodes:
            if color[node] == WHITE:
                if has_cycle(node):
                    raise DependencyCycleError(f"Circular dependency detected involving task: {node}")
    
    def _validate_dependencies(self, tasks: List[DecomposedTask]):
        """Validate that all dependencies exist."""
        task_names = {task.parent_task_name for task in tasks}
        
        for task in tasks:
            # Get dependencies using helper method
            dependencies = self._get_task_dependencies(task)
            
            for dep in dependencies:
                if dep not in task_names:
                    raise TaskDecompositionError(
                        f"Task '{task.parent_task_name}' depends on non-existent task '{dep}'"
                    )
    
    def validate_dependencies(self, tasks: List[DecomposedTask]) -> bool:
        """Public method to validate dependencies - calls internal method."""
        self._validate_dependencies(tasks)
        return True
    
    def assess_agent_suitability(self, task) -> Dict[str, Dict[str, Any]]:
        """Assess which agents are suitable for a task."""
        # Handle both DecomposedTask and Mock objects for testing
        if hasattr(task, 'external_agent_prompts'):
            # Real DecomposedTask
            return {
                'claude_code': task.external_agent_prompts.get('claude_code', {}),
                'roocode': task.external_agent_prompts.get('roocode', {}),
                'github_copilot': task.external_agent_prompts.get('github_copilot', {})
            }
        else:
            # Mock object - generate prompts on the fly
            prompts = {}
            prompts['claude_code'] = self.generate_claude_code_prompt(task)
            prompts['roocode'] = self.generate_roocode_prompt(task)
            prompts['github_copilot'] = self.generate_github_copilot_prompt(task)
            return prompts