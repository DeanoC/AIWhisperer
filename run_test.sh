#!/bin/bash

# Ensure the script stops if any command fails
set -e

# Define file paths relative to the script location (assuming script is in project root)
CONFIG_FILE="test.yaml"
REQUIREMENTS_FILE="test_requirements.md"
OUTPUT_FILE="test_output.yaml"

echo "Running AI Whisperer test..."

# Execute the main script as a module
# Ensure your Python environment is active if needed (e.g., source .venv/bin/activate)
python -m src.ai_whisperer.main --config "$CONFIG_FILE" --requirements "$REQUIREMENTS_FILE" --output "$OUTPUT_FILE"

echo "-------------------------------------"
echo "AI Whisperer test finished."
echo "Config: $CONFIG_FILE"
echo "Requirements: $REQUIREMENTS_FILE"
echo "Output: $OUTPUT_FILE"
echo "-------------------------------------"

# Optional: Display the output file content
# echo "Generated Output ($OUTPUT_FILE):"
# cat "$OUTPUT_FILE"

exit 0
