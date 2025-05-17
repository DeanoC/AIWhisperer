# Uses aiwhisperers refine ability to improve the a RFC

[CmdletBinding()] # Enables common parameters like -Verbose, -Debug
param (
    [Parameter(Position = 0, Mandatory = $true, HelpMessage = "Path or name of the RFC Markdown file (relative to project_dev/rfc/). '.md' extension is optional. Can also be a path starting with 'project_dev'.")]
    [ValidateNotNullOrEmpty()]
    [string]$RfcFile,

    [Parameter(HelpMessage = "Automatically confirm prompts without user interaction. Alias: -y.")]
    [Alias("y")]
    [switch]$Yes,

    [Parameter(HelpMessage = "Number of refinement iterations to perform (default: 1).")]
    [int]$Iterations = 1,

    [Parameter(HelpMessage = "Show help for the refine command.")]
    [switch]$Help
)

# --- Script Initialization ---
Write-Verbose "Script starting. PowerShell version: $($PSVersionTable.PSVersion)"
Write-Verbose "Raw RFC File Parameter: '$RfcFile'"
Write-Verbose "Yes switch set: $Yes"
Write-Verbose "Iterations set: $Iterations"
Write-Verbose "Help switch set: $Help"

# Use the automatic variable $PSScriptRoot for the script's directory
$ScriptDir = $PSScriptRoot
Write-Verbose "Script directory: $ScriptDir"

# Determine Project Root (assuming script is in 'project_dev')
try {
    $ProjectRoot = (Resolve-Path -Path (Join-Path -Path $ScriptDir -ChildPath "..")).Path
    Write-Verbose "Resolved Project Root: $ProjectRoot"
} catch {
    Write-Error "Failed to resolve project root directory based on script location '$ScriptDir'. Error: $_"
    exit 1
}

# Save the current location to restore later
$OriginalLocation = Get-Location
Write-Verbose "Original location saved: $OriginalLocation"

try {
    # --- Parameter Validation and Path Construction ---

    # Construct the expected RFC directory path
    $RfcDir = Join-Path -Path $ScriptDir -ChildPath "rfc"

    # Normalize RFC file input
    $inputPath = $RfcFile
    $isExplicitPath = $false

    if ($RfcFile -like "project_dev*") {
        $RfcPath = Join-Path -Path $ProjectRoot -ChildPath $RfcFile
        $isExplicitPath = $true
    } elseif ($RfcFile -like ".\*" -or $RfcFile -like "./*") {
        $RfcPath = Resolve-Path -Path $RfcFile | Select-Object -ExpandProperty Path
        $isExplicitPath = $true
    } else {
        $RfcPath = Join-Path -Path $RfcDir -ChildPath ([System.IO.Path]::GetFileNameWithoutExtension($RfcFile) + ".md")
    }

    # Ensure .md extension
    if (-not ($RfcPath.ToLower().EndsWith(".md"))) {
        $RfcPath += ".md"
    }

    # Always get the base name for output folder
    $RfcBaseName = [System.IO.Path]::GetFileNameWithoutExtension($RfcPath)
    # No need to set $RefinedRfcPath for in-place refinement

    Write-Verbose "Constructed RFC Path: $RfcPath"

    # Validate RFC file existence
    if (-not (Test-Path $RfcPath -PathType Leaf)) {
        Write-Error "RFC file not found at expected location: '$RfcPath'. Please ensure the file exists."
        exit 1
    }
    Write-Verbose "Confirmed RFC file exists: $RfcPath"

    # Locate the .venv Python environment
    $VenvPythonPath = Join-Path -Path $ProjectRoot -ChildPath ".venv\Scripts\python.exe" # Windows default
    if (-not (Test-Path $VenvPythonPath -PathType Leaf)) {
        $VenvPythonPath = Join-Path -Path $ProjectRoot -ChildPath ".venv\bin\python" # Linux/macOS/other default
        if (-not (Test-Path $VenvPythonPath -PathType Leaf)) {
            Write-Error "Python executable not found in the virtual environment (.venv/Scripts/python.exe or .venv/bin/python) within '$ProjectRoot'. Please ensure the virtual environment is set up correctly and activated, or adjust the path."
            exit 1
        }
    }
    Write-Verbose "Using Python executable from virtual environment: $VenvPythonPath"

    # Locate the main Python script (using module path relative to ProjectRoot)
    $MainModulePath = "ai_whisperer.main" # Path used with python -m
    $MainPyCheckPath = Join-Path -Path $ProjectRoot -ChildPath "ai_whisperer\main.py" # Path for existence check
    if (-not (Test-Path $MainPyCheckPath -PathType Leaf)) {
        Write-Error "The main Python script was not found at '$MainPyCheckPath'. Please verify the project structure."
        exit 1
    }
    Write-Verbose "Confirmed main Python script exists for module '$MainModulePath'"

    # Locate the configuration file
    $ConfigFile = Join-Path -Path $ScriptDir -ChildPath "aiwhisperer_config.yaml"
    if (-not (Test-Path $ConfigFile -PathType Leaf)) {
        Write-Error "Configuration file '$ConfigFile' not found in the script directory '$ScriptDir'."
        exit 1
    }
    Write-Verbose "Using configuration file: $ConfigFile"

    # --- Execute Python Script ---

    if ($Help) {
        $pythonArgs = @(
            "-m", $MainModulePath,
            "refine",
            "-h"
        )
    } else {
        $pythonArgs = @(
            "-m", $MainModulePath,
            "refine",
            "--config", $ConfigFile,
            "--iterations", $Iterations,
            $RfcPath
        )
    }

    Write-Verbose "Executing Python script from Project Root: $ProjectRoot"
    Write-Verbose "Command: $VenvPythonPath $($pythonArgs -join ' ')"

    # Change to Project Root for correct Python module resolution
    Set-Location -Path $ProjectRoot

    # Execute the command
    & $VenvPythonPath $pythonArgs
    $exitCode = $LASTEXITCODE # Capture exit code immediately

    # Check execution result
    if ($exitCode -ne 0) {
        Write-Error "Python script execution failed with exit code $exitCode."
        exit $exitCode
    }

    Write-Host "Successfully refined RFC in place: '$RfcPath'."

} catch {
    # Catch any unexpected errors during the main script logic
    Write-Error "An unexpected error occurred: $_"
    # Attempt to restore location even after an error
    if ($OriginalLocation -ne (Get-Location)) {
        Set-Location -Path $OriginalLocation -ErrorAction SilentlyContinue
    }
    exit 1
} finally {
    # Always restore the original location
    if ($OriginalLocation -ne (Get-Location)) {
        Set-Location -Path $OriginalLocation
        Write-Verbose "Restored original location: $OriginalLocation"
    } else {
        Write-Verbose "Location was already the original location."
    }
    Write-Verbose "Script finished."
}
