# Implementation Approach for YAML to JSON Migration

## Introduction

This document outlines the proposed implementation approach for migrating the AI Whisperer project from YAML to JSON. The migration is a significant change that affects multiple components of the project, so a well-planned implementation strategy is crucial for success.

## Implementation Options

There are two main approaches to implementing the migration:

1. **All-at-once approach**: Migrate all components from YAML to JSON in a single release.
2. **Phased approach**: Migrate components gradually over multiple releases.

Each approach has its advantages and disadvantages, which are discussed below.

### All-at-once Approach

#### Advantages:
- Simpler to reason about: The codebase is either using YAML or JSON, not a mix of both.
- Avoids maintaining dual implementations during a transition period.
- Reduces the risk of inconsistencies between YAML and JSON implementations.
- Allows for a clean break from YAML, with no legacy code to maintain.

#### Disadvantages:
- Higher risk: If something goes wrong, the entire system is affected.
- Requires more upfront testing to ensure all components work correctly with JSON.
- May require more coordination if multiple developers are involved.
- Could disrupt users who have existing YAML files.

### Phased Approach

#### Advantages:
- Lower risk: Only a portion of the system is affected at any given time.
- Allows for incremental testing and validation.
- Can provide backward compatibility during the transition period.
- Easier to roll back if issues are discovered.

#### Disadvantages:
- More complex: The codebase will have both YAML and JSON implementations during the transition.
- Requires maintaining dual implementations for a period of time.
- May introduce inconsistencies between YAML and JSON implementations.
- Takes longer to complete the migration.

## Recommended Approach

Given the nature of the AI Whisperer project and the extent of the changes required, we recommend a **direct approach** with the following phases:

### Phase 1: Infrastructure and Utilities

1. Create JSON schemas for task plans and subtasks.
2. Implement JSON validation utilities.
3. Create JSON-specific postprocessing steps to replace YAML-specific ones.
4. Update the postprocessing pipeline to handle JSON only.

### Phase 2: Core Components

1. Update the Orchestrator to output JSON only.
2. Update the SubtaskGenerator to output JSON only.
3. Update the prompt templates to instruct the AI to generate JSON instead of YAML.
4. Implement and test the new JSON-specific postprocessing steps.

### Phase 3: Testing and Validation

1. Create new tests for the JSON implementation.
2. Replace existing YAML tests with JSON tests.
3. Run all tests to ensure everything works as expected.
4. Perform manual testing with real-world examples.

### Phase 4: Deployment

1. Deploy the new version with JSON-only support.
2. Update documentation to reflect the JSON format.
3. Monitor for issues and provide support.
4. Clean up any remaining YAML-specific code.

## Breaking Changes

Since we're taking a direct approach without backward compatibility, the following breaking changes will occur:

### File Format Changes

All output files will be in JSON format instead of YAML:

```json
{
  "natural_language_goal": "Example goal",
  "plan": [
    {
      "step_id": "example_step",
      "description": "Example description",
      "agent_spec": {
        "type": "example",
        "instructions": "Example instructions"
      }
    }
  ]
}
```

### Code Changes

Code that expects YAML output will need to be updated to handle JSON:

```python
# Old YAML code
with open(file_path, 'r') as f:
    data = yaml.safe_load(f)

# New JSON code
with open(file_path, 'r') as f:
    data = json.load(f)
```

### Migration Utilities

While we won't maintain dual format support, we can provide a one-time utility script to help users convert existing YAML files to JSON:

```python
import yaml
import json
import os
import glob

def convert_yaml_to_json(yaml_file_path, json_file_path):
    """Convert a YAML file to JSON."""
    with open(yaml_file_path, 'r') as yaml_file:
        yaml_data = yaml.safe_load(yaml_file)

    with open(json_file_path, 'w') as json_file:
        json.dump(yaml_data, json_file, indent=2)

def convert_directory(directory_path):
    """Convert all YAML files in a directory to JSON."""
    yaml_files = glob.glob(os.path.join(directory_path, '*.yaml'))

    for yaml_file in yaml_files:
        json_file = yaml_file.replace('.yaml', '.json')
        convert_yaml_to_json(yaml_file, json_file)
        print(f"Converted {yaml_file} to {json_file}")
```

## Implementation Timeline

The following timeline is proposed for the direct migration:

1. **Week 1**: Phase 1 - Infrastructure and Utilities
2. **Week 2-3**: Phase 2 - Core Components
3. **Week 3-4**: Phase 3 - Testing and Validation
4. **Week 4**: Phase 4 - Deployment

## Risk Mitigation

To mitigate the risks associated with the migration, the following strategies are recommended:

1. **Comprehensive Testing**: Implement thorough testing at each phase of the migration.
2. **Rollback Plan**: Have a plan to roll back changes if issues are discovered.
3. **Monitoring**: Monitor the system during and after the migration to detect any issues.
4. **User Communication**: Communicate the changes to users and provide support during the transition.
5. **Documentation**: Update documentation to reflect the changes and provide guidance for users.

## Conclusion

The migration from YAML to JSON is a significant change that requires careful planning and execution. By taking a direct approach with thorough testing, we can implement the migration quickly and efficiently. While this approach will cause some disruption due to breaking changes, the long-term benefits of improved reliability, better error handling, and a more structured output format will significantly outweigh the short-term costs of the migration. The simplified codebase without dual format support will also be easier to maintain going forward.
