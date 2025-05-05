# Navigate to the project root first
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$projectRoot = Resolve-Path (Join-Path -Path $scriptDir -ChildPath "..\..")
Set-Location $projectRoot

# Find the Python executable in the virtual environment
$pythonExecutable = Join-Path -Path ".\.venv\Scripts" -ChildPath "python.exe"

# Define file paths consistently relative to the project root 
$configPath = "bootstrap_ourself\bootstrap_config.yaml"
$requirementsPath = "bootstrap_ourself\yaml_clean_postprocessor\yaml_clean_postprocessor_requirements.md"
$outputPath = "bootstrap_ourself\yaml_clean_postprocessor\test_output.yaml"

Write-Host "Running AI Whisperer from project root: $projectRoot"

# Execute the Python script directly from the project root
& $pythonExecutable -m src.ai_whisperer.main --config "$configPath" --requirements "$requirementsPath" --output "$outputPath" --full-project
$exitCode = $LASTEXITCODE

# Check the exit code
if ($exitCode -ne 0) {
    Write-Error "AI Whisperer script failed with exit code $exitCode"
    exit $exitCode
} else {
    Write-Host "AI Whisperer script completed successfully."
}

# Check the generated output
# Adjust the expected output file name based on how your main script generates it
$expectedOutputFileName = "yaml_clean_postprocessor_requirements_bootstrap_config.yaml" 
$expectedOutputPath = Join-Path -Path "output" -ChildPath $expectedOutputFileName

if (Test-Path $expectedOutputPath) {
    Write-Host "Output file generated: $expectedOutputPath"
} else {
    Write-Warning "Expected output file not found: $expectedOutputPath"
}

exit 0
