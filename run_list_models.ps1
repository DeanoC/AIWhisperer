# PowerShell script to run the AI Whisperer application with the --list-models command

# Define the path to the configuration file
$configPath = "d:\Projects\AIWhisperer\config.yaml"

# Optionally define the output CSV file path
$outputCsvPath = $null
if ($args.Length -ge 1) {
    $outputCsvPath = $args[0]
}

# Build the base command
$command = "python -m src.ai_whisperer.main --config `"$configPath`" list-models"
if ($outputCsvPath) {
    $command += " --output-csv `"$outputCsvPath`""
}

# Run the application with the constructed command
Invoke-Expression $command
