# Define file paths relative to the script location (assuming script is in project root)
$configFile = "test.yaml"
$requirementsFile = "test_requirements.md"
$outputFile = "test_output.yaml"

Write-Host "Running AI Whisperer test..."

# Construct arguments array for Python
$pythonArgs = @(
    "-m", "src.ai_whisperer.main",
    "--config", $configFile,
    "--requirements", $requirementsFile,
    "--output", $outputFile
)

# Execute the main script as a module using the arguments array
# Ensure your Python environment is active if needed (e.g., .\.venv\Scripts\Activate.ps1)
python $pythonArgs

# Check the exit code of the last command
if ($LASTEXITCODE -ne 0) {
    Write-Error "AI Whisperer script failed with exit code $LASTEXITCODE"
    exit $LASTEXITCODE
}

Write-Host "-------------------------------------"
Write-Host "AI Whisperer test finished."
Write-Host "Config: $configFile"
Write-Host "Requirements: $requirementsFile"
Write-Host "Output: $outputFile"
Write-Host "-------------------------------------"

# Optional: Display the output file content
# Write-Host "Generated Output ($outputFile):"
# Get-Content $outputFile

exit 0
