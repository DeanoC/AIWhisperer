# Find the Python executable in the virtual environment
$pythonExecutable = Resolve-Path "..\..\.venv\Scripts\python.exe" # Corrected path resolution

# Define script directory and project root
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$projectRoot = Resolve-Path (Join-Path $scriptDir "..\..") # Go up two levels

# Define file paths relative to the project root for the python command
$configRelativePath = Join-Path "bootstrap_ourself\initial_orchestrator" "initial_orchestrator_config.yaml" # Updated config filename
$requirementsRelativePath = Join-Path "bootstrap_ourself\initial_orchestrator" "list_openrouter_models.md" # Updated requirements filename
$outputRelativePath = Join-Path "bootstrap_ourself\initial_orchestrator" "test_output.yaml" # Output within the test dir
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
# Use the new requirements filename base for the expected output
$expectedOutputFileName = "list_openrouter_models_initial_orchestrator.yaml"
# Correctly join the path components
$expectedOutputPath = Join-Path -Path (Join-Path -Path $projectRoot -ChildPath "output") -ChildPath $expectedOutputFileName

if (Test-Path $expectedOutputPath) {
    Write-Host "Output file generated: $expectedOutputPath"
    # Get-Content $expectedOutputPath
} else {
    Write-Warning "Expected output file not found: $expectedOutputPath"
}

exit 0
