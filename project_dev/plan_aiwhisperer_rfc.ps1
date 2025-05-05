# Improved version of project_dev\plan_aiwhisperer_rfc.ps1

[CmdletBinding()] # Enables common parameters like -Verbose, -Debug
param (
    [Parameter(Position = 0, Mandatory = $true, HelpMessage = "Path or name of the RFC Markdown file (relative to project_dev/rfc/). '.md' extension is optional.")]
    [ValidateNotNullOrEmpty()]
    [string]$RfcFile,

    [Parameter(HelpMessage = "Switch to skip generating subtasks and only create the main plan.")]
    [switch]$NoSubtasks
)

# --- Script Initialization ---
Write-Verbose "Script starting. PowerShell version: $($PSVersionTable.PSVersion)"
Write-Verbose "Raw RFC File Parameter: '$RfcFile'"
Write-Verbose "NoSubtasks switch set: $NoSubtasks"

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

    # Handle RFC file name and extension
    $RfcBaseName = [System.IO.Path]::GetFileNameWithoutExtension($RfcFile)
    $RfcFileName = $RfcBaseName + ".md" # Ensure .md extension
    $RfcPath = Join-Path -Path $RfcDir -ChildPath $RfcFileName
    Write-Verbose "Constructed RFC Path: $RfcPath"

    # Validate RFC file existence
    if (-not (Test-Path $RfcPath -PathType Leaf)) {
        Write-Error "RFC file not found at expected location: '$RfcPath'. Please ensure the file exists in the '$RfcDir' directory."
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
    $MainModulePath = "src.ai_whisperer.main" # Path used with python -m
    $MainPyCheckPath = Join-Path -Path $ProjectRoot -ChildPath "src\ai_whisperer\main.py" # Path for existence check
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

    # Create the output directory ('in_dev/<rfc_basename>')
    $InDevBaseFolder = Join-Path -Path $ScriptDir -ChildPath "in_dev"
    $OutputFolder = Join-Path -Path $InDevBaseFolder -ChildPath $RfcBaseName
    Write-Verbose "Target output folder: $OutputFolder"

    if (-not (Test-Path $OutputFolder -PathType Container)) {
        try {
            New-Item -ItemType Directory -Path $OutputFolder -ErrorAction Stop | Out-Null
            Write-Verbose "Created output folder: $OutputFolder"
        } catch {
            Write-Error "Failed to create output directory '$OutputFolder'. Error: $_"
            exit 1
        }
    } else {
        Write-Verbose "Output folder already exists: $OutputFolder"
    }

    # --- Execute Python Script ---

    # Build the arguments for the Python script
    $pythonArgs = @(
        "-m", $MainModulePath,
        "--config", $ConfigFile,
        "--requirements", $RfcPath,
        "--output", $OutputFolder
    )
    if (-not $NoSubtasks) {
        $pythonArgs += "--full-project"
        Write-Verbose "Adding '--full-project' flag."
    } else {
        Write-Verbose "'--full-project' flag skipped due to -NoSubtasks switch."
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
        # Note: Python script stderr should ideally provide more details.
        exit $exitCode
    }

    Write-Host "Successfully generated planning artifacts in '$OutputFolder'." # Use Write-Host for final success message

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
