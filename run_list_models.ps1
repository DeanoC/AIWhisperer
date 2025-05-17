

# PowerShell script to run the AI Whisperer application with the --list-models command
#
# Usage:
#   .\run_list_models.ps1 [-OutputCsvPath <path>] [-DetailLevel <level>]
#
# Example:
#   .\run_list_models.ps1 -OutputCsvPath models.csv -DetailLevel full


param(
    [Parameter(ValueFromPipelineByPropertyName=$true, Position=0)]
    [string]$OutputCsvPath = $null,
    [Parameter(ValueFromPipelineByPropertyName=$true, Position=1)]
    [string]$DetailLevel = $null
)

# Define the path to the configuration file
$configPath = "d:\Projects\AIWhisperer\config.yaml"








# Build the base command as an array for robust argument handling
$argsList = @("-m", "ai_whisperer.main", "--config", $configPath, "list-models")
if ($DetailLevel) {
    $argsList += @("--detail-level", $DetailLevel)
}
if ($OutputCsvPath) {
    $argsList += @("--output-csv", $OutputCsvPath)
}

# Run the application with the constructed command and show output
python @argsList
