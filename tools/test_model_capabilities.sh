#!/bin/bash
# Model Capability Tester - Convenience Wrapper
# 
# This script provides an easy way to run the model capability tester
# from anywhere in the project.

# Get the directory of this script
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$( cd "$SCRIPT_DIR/.." && pwd )"

# Change to project root
cd "$PROJECT_ROOT"

# Run the model capability tester module with all arguments passed through
python -m ai_whisperer.tools.model_capability_tester "$@"