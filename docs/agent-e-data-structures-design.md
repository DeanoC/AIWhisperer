# Agent E Data Structures Design

## Overview
This document defines the core data structures for Agent E, building on existing AIWhisperer patterns while adding capabilities for task decomposition and external agent integration.

## Core Data Structures

### 1. Decomposed Task Structure

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "Agent E Decomposed Task",
  "description": "A task decomposed by Agent E for execution by external agents",
  "type": "object",
  "properties": {
    "task_id": {
      "type": "string",
      "format": "uuid",
      "description": "Unique identifier for this decomposed task"
    },
    "parent_task_name": {
      "type": "string",
      "description": "Name of the parent task from the plan"
    },
    "title": {
      "type": "string",
      "description": "Clear, action-oriented title for the task"
    },
    "description": {
      "type": "string",
      "description": "Detailed description of what needs to be accomplished"
    },
    "context": {
      "type": "object",
      "properties": {
        "files_to_read": {
          "type": "array",
          "items": {"type": "string"},
          "description": "Files that should be read before starting"
        },
        "files_to_modify": {
          "type": "array",
          "items": {"type": "string"},
          "description": "Files that will be modified"
        },
        "dependencies": {
          "type": "array",
          "items": {"type": "string"},
          "description": "Libraries/packages required"
        },
        "technology_stack": {
          "type": "object",
          "properties": {
            "language": {"type": "string"},
            "framework": {"type": "string"},
            "testing_framework": {"type": "string"},
            "additional_tools": {
              "type": "array",
              "items": {"type": "string"}
            }
          }
        },
        "constraints": {
          "type": "array",
          "items": {"type": "string"},
          "description": "Constraints that must be adhered to"
        }
      }
    },
    "execution_strategy": {
      "type": "object",
      "properties": {
        "approach": {
          "type": "string",
          "enum": ["tdd", "exploratory", "refactoring", "migration", "documentation"],
          "description": "Recommended approach for this task"
        },
        "steps": {
          "type": "array",
          "items": {
            "type": "object",
            "properties": {
              "order": {"type": "integer"},
              "description": {"type": "string"},
              "validation": {"type": "string"}
            }
          }
        }
      }
    },
    "external_agent_prompts": {
      "type": "object",
      "properties": {
        "claude_code": {
          "type": "object",
          "properties": {
            "suitable": {"type": "boolean"},
            "command": {"type": "string"},
            "prompt": {"type": "string"},
            "strengths": {
              "type": "array",
              "items": {"type": "string"}
            }
          }
        },
        "roocode": {
          "type": "object",
          "properties": {
            "suitable": {"type": "boolean"},
            "prompt": {"type": "string"},
            "configuration_hints": {"type": "string"},
            "strengths": {
              "type": "array",
              "items": {"type": "string"}
            }
          }
        },
        "github_copilot": {
          "type": "object",
          "properties": {
            "suitable": {"type": "boolean"},
            "prompt": {"type": "string"},
            "mode": {"type": "string", "enum": ["agent", "edit"]},
            "strengths": {
              "type": "array",
              "items": {"type": "string"}
            }
          }
        }
      }
    },
    "acceptance_criteria": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "criterion": {"type": "string"},
          "verification_method": {"type": "string"},
          "automated": {"type": "boolean"}
        }
      }
    },
    "estimated_complexity": {
      "type": "string",
      "enum": ["trivial", "simple", "moderate", "complex", "very_complex"],
      "description": "Estimated complexity for external agent execution"
    },
    "status": {
      "type": "string",
      "enum": ["pending", "assigned", "in_progress", "completed", "failed", "blocked"],
      "description": "Current status of the task"
    },
    "execution_result": {
      "type": "object",
      "properties": {
        "agent_used": {"type": "string"},
        "start_time": {"type": "string", "format": "date-time"},
        "end_time": {"type": "string", "format": "date-time"},
        "success": {"type": "boolean"},
        "files_changed": {
          "type": "array",
          "items": {"type": "string"}
        },
        "tests_passed": {"type": "boolean"},
        "notes": {"type": "string"}
      }
    }
  },
  "required": ["task_id", "parent_task_name", "title", "description", "context", "acceptance_criteria", "estimated_complexity", "status"]
}
```

### 2. Agent Communication Protocol

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "Agent E Communication Message",
  "description": "Message format for Agent E communications",
  "type": "object",
  "properties": {
    "message_id": {
      "type": "string",
      "format": "uuid"
    },
    "timestamp": {
      "type": "string",
      "format": "date-time"
    },
    "from_agent": {
      "type": "string",
      "enum": ["agent_e", "agent_p", "user", "external_agent"]
    },
    "to_agent": {
      "type": "string",
      "enum": ["agent_e", "agent_p", "user", "external_agent"]
    },
    "message_type": {
      "type": "string",
      "enum": [
        "task_decomposition_request",
        "task_decomposition_response",
        "clarification_request",
        "clarification_response",
        "plan_refinement_request",
        "plan_refinement_response",
        "status_update",
        "error_report"
      ]
    },
    "payload": {
      "type": "object",
      "description": "Message-specific payload"
    },
    "context": {
      "type": "object",
      "properties": {
        "session_id": {"type": "string"},
        "plan_id": {"type": "string"},
        "rfc_id": {"type": "string"},
        "parent_message_id": {"type": "string"}
      }
    }
  },
  "required": ["message_id", "timestamp", "from_agent", "to_agent", "message_type", "payload"]
}
```

### 3. Task Execution Session

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "Agent E Task Execution Session",
  "description": "Tracks a complete task execution session",
  "type": "object",
  "properties": {
    "session_id": {
      "type": "string",
      "format": "uuid"
    },
    "plan_id": {
      "type": "string",
      "description": "ID of the plan being executed"
    },
    "started_at": {
      "type": "string",
      "format": "date-time"
    },
    "status": {
      "type": "string",
      "enum": ["active", "paused", "completed", "failed", "cancelled"]
    },
    "decomposed_tasks": {
      "type": "array",
      "items": {"$ref": "#/definitions/DecomposedTask"}
    },
    "task_dependencies": {
      "type": "object",
      "description": "DAG of task dependencies",
      "additionalProperties": {
        "type": "array",
        "items": {"type": "string"}
      }
    },
    "execution_queue": {
      "type": "array",
      "items": {"type": "string"},
      "description": "Ordered queue of task IDs ready for execution"
    },
    "completed_tasks": {
      "type": "array",
      "items": {"type": "string"}
    },
    "failed_tasks": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "task_id": {"type": "string"},
          "failure_reason": {"type": "string"},
          "retry_count": {"type": "integer"}
        }
      }
    },
    "agent_collaboration_log": {
      "type": "array",
      "items": {"$ref": "#/definitions/AgentCommunicationMessage"}
    }
  },
  "required": ["session_id", "plan_id", "started_at", "status", "decomposed_tasks"]
}
```

### 4. Plan Hierarchy Structure

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "Agent E Plan Hierarchy",
  "description": "Hierarchical structure for complex plans",
  "type": "object",
  "properties": {
    "hierarchy_id": {
      "type": "string",
      "format": "uuid"
    },
    "root_plan_id": {
      "type": "string",
      "description": "ID of the top-level plan"
    },
    "nodes": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "node_id": {"type": "string"},
          "plan_id": {"type": "string"},
          "parent_node_id": {"type": "string", "nullable": true},
          "task_name": {"type": "string"},
          "requires_sub_plan": {"type": "boolean"},
          "sub_plan_rfc_id": {"type": "string", "nullable": true},
          "decomposition_reason": {"type": "string"}
        }
      }
    },
    "created_at": {
      "type": "string",
      "format": "date-time"
    },
    "last_updated": {
      "type": "string",
      "format": "date-time"
    }
  },
  "required": ["hierarchy_id", "root_plan_id", "nodes", "created_at"]
}
```

## Integration Points

### With Existing AIWhisperer Systems

1. **Plan Integration**: Extends existing plan schema with decomposition metadata
2. **Tool Registry**: Agent E tools for decomposition and orchestration
3. **Agent Registry**: Agent E registration in agents.yaml
4. **Session Manager**: Integration with stateless session management

### With External Agents

1. **Prompt Generation**: Structured prompts optimized for each agent
2. **Result Parsing**: Standardized result format from human feedback
3. **Progress Tracking**: Real-time status updates during execution

## Data Validation Rules

### Task Decomposition Rules
1. Each decomposed task must reference a parent plan task
2. Task IDs must be unique within a session
3. Dependencies must form a valid DAG (no cycles)
4. All required context fields must be populated

### Communication Rules
1. Messages must have valid sender/receiver agents
2. Response messages must reference parent message
3. Timestamps must be in UTC
4. Session context must be maintained

### Execution Rules
1. Tasks can only transition through valid status states
2. Completed tasks cannot be re-executed without reset
3. Failed tasks must include failure reason
4. Dependencies must be resolved before execution

## Example Usage

### Task Decomposition Example
```json
{
  "task_id": "550e8400-e29b-41d4-a716-446655440000",
  "parent_task_name": "Implement core task decomposition engine",
  "title": "Create TaskDecomposer class with plan parsing logic",
  "description": "Implement the main TaskDecomposer class that takes Agent P plans and breaks them down into executable tasks with proper context and dependencies",
  "context": {
    "files_to_read": [
      "ai_whisperer/agents/stateless_agent.py",
      "schemas/plan_generation_schema.json"
    ],
    "files_to_modify": [
      "ai_whisperer/agents/task_decomposer.py"
    ],
    "technology_stack": {
      "language": "Python",
      "framework": "None",
      "testing_framework": "pytest"
    }
  },
  "external_agent_prompts": {
    "claude_code": {
      "suitable": true,
      "command": "claude -p \"Create a TaskDecomposer class...\" --json",
      "prompt": "Create a TaskDecomposer class in Python that:\n1. Reads plan JSON following the plan_generation_schema\n2. Extracts tasks and dependencies\n3. Adds execution context to each task\n4. Returns decomposed task objects\n\nUse TDD - write tests first in test_task_decomposer.py"
    }
  },
  "acceptance_criteria": [
    {
      "criterion": "TaskDecomposer class exists with parse_plan method",
      "verification_method": "Check class and method existence",
      "automated": true
    }
  ],
  "estimated_complexity": "moderate",
  "status": "pending"
}
```

## Future Considerations

1. **Streaming Updates**: Real-time task status streaming to UI
2. **Parallel Execution**: Support for concurrent task execution
3. **Rollback Mechanisms**: Task rollback on failure
4. **Metrics Collection**: Performance and success rate tracking
5. **ML Optimization**: Learning optimal task decomposition patterns