# Description: This script runs the AI Whisperer application to list available models.
param(
    [Parameter(ValueFromPipelineByPropertyName=$true, Position=0)]
    [string]$OutputCsvPath = $null,
    [Parameter(ValueFromPipelineByPropertyName=$true, Position=1)]
    [string]$DetailLevel = $null,
    [Parameter(ValueFromPipelineByPropertyName=$true, Position=2)]
    [switch]$Interactive,
    [Parameter(ValueFromPipelineByPropertyName=$true, Position=3)]
    [switch]$WaitForDebugger
)
# Define the path to the configuration file
$configPath = "d:\Projects\AIWhisperer\config.yaml"

# Build the base command as an array for robust argument handling

# Build the base command as an array for robust argument handling
$argsList = @("-m", "ai_whisperer.main", "--config", $configPath)
if ($Interactive) {
    $argsList += @("--interactive")
}
if ($WaitForDebugger) {
    $argsList += @("--debug")
}
$argsList += @("list-models")

# If --interactive is set, add it before the command/module
if ($DetailLevel) {
    $argsList += @("--detail-level", $DetailLevel)
}
if ($OutputCsvPath) {
    $argsList += @("--output-csv", $OutputCsvPath)
}

# Run the application with the constructed command and show output
python @argsList