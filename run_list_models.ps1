# PowerShell script to run the AI Whisperer application with the --list-models command

# Define the path to the configuration file
$configPath = "d:\Projects\AIWhisperer\config.yaml"

# Define the output CSV file path
$outputCsvPath = "d:\Projects\AIWhisperer\models_output.csv"

# Run the application with the --list-models command
python -m src.ai_whisperer.main list-models --config $configPath --output-csv $outputCsvPath

# Open the generated CSV file
if (Test-Path $outputCsvPath) {
    Invoke-Item $outputCsvPath
} else {
    Write-Host "The output CSV file was not generated."
}
