# Find the Python executable in the virtual environment
$pythonExecutable = Resolve-Path "..\..\.venv\Scripts\python.exe" # Corrected path resolution

# Define script directory and project root
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$projectRoot = Resolve-Path (Join-Path $scriptDir "..\..") # Go up two levels

# Define file paths relative to the project root for the python command
# Use the shared bootstrap config
$configRelativePath = Join-Path "bootstrap_ourself" "bootstrap_config.yaml"
# Use the requirements file copied into this directory
$requirementsRelativePath = Join-Path "bootstrap_ourself\subtask_generator" "subtask_generator_requirements.md"
# Output within the subtask generator directory for testing purposes
$outputRelativePath = Join-Path "bootstrap_ourself\subtask_generator" "test_output.yaml"
$promptRelativePath = Join-Path "prompts" "orchestrator_default.md" # Prompt from the main prompts dir

Write-Host "Running AI Whisperer test..."

# Execute the Python script ensuring the project root is the working directory
Push-Location $projectRoot
Write-Host "Running AI Whisperer test from $projectRoot..."
# Corrected argument names: --config, --requirements, --output
& $pythonExecutable -m src.ai_whisperer.main --config "$configRelativePath" --requirements "$requirementsRelativePath" --output "$outputRelativePath" --prompt-file "$promptRelativePath"
$exitCode = $LASTEXITCODE
Pop-Location

# Check the exit code
if ($exitCode -ne 0) {
    Write-Error "AI Whisperer script failed with exit code $exitCode"
    exit $exitCode
} else {
    Write-Host "AI Whisperer script completed successfully."
}

# Optional: Add further checks, e.g., verify output file content
# Construct the expected output path based on Python script's behavior
# Use the requirements filename base and the hardcoded suffix from the orchestrator
$expectedOutputFileName = "subtask_generator_requirements_bootstrap_config.yaml"
# Correctly join the path components
$expectedOutputPath = Join-Path -Path (Join-Path -Path $projectRoot -ChildPath "output") -ChildPath $expectedOutputFileName

if (Test-Path $expectedOutputPath) {
    Write-Host "Output file generated: $expectedOutputPath"
    # Get-Content $expectedOutputPath
} else {
    Write-Warning "Expected output file not found: $expectedOutputPath"
}

exit 0
