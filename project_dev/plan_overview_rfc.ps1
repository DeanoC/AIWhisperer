
[CmdletBinding()] # Enables common parameters like -Verbose, -Debug
param (
    [Parameter(Position = 0, Mandatory = $true, HelpMessage = "Path or name of the Initial Plan file (relative to project_dev/in_dev/). '.md' extension is optional. Can also be a path starting with 'project_dev'.")]
    [ValidateNotNullOrEmpty()]
    [string]$IndevDir,

    [Parameter(HelpMessage = "Switch to clean the output directory before generating new content.")]
    [switch]$Clean,

    [Parameter(HelpMessage = "Automatically confirm prompts without user interaction. Alias: -y.")]
    [Alias("y")]
    [switch]$Yes
)

# --- Script Initialization ---
Write-Verbose "Script starting. PowerShell version: $($PSVersionTable.PSVersion)"
Write-Verbose "Raw Initial Plan File Parameter: '$IndevDir'"
Write-Verbose "Clean switch set: $Clean"
Write-Verbose "Yes switch set: $Yes"

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

    # Normalize RFC file input (user parameter $IndevDir)
    $RfcPath = $IndevDir
    if ($RfcPath -like "project_dev*") {
        $RfcPath = Join-Path -Path $ProjectRoot -ChildPath $RfcPath
    } elseif ($RfcPath -like ".\*" -or $RfcPath -like "./*") {
        $RfcPath = Resolve-Path -Path $RfcPath | Select-Object -ExpandProperty Path
    } elseif (-not ([System.IO.Path]::IsPathRooted($RfcPath))) {
        # If it's a bare filename, assume it's relative to in_dev
        $RfcPath = Join-Path -Path $ScriptDir -ChildPath "in_dev"
        $RfcPath = Join-Path -Path $RfcPath -ChildPath $IndevDir
    }

    # Always get the base name for output folder
    $RfcBaseName = [System.IO.Path]::GetFileNameWithoutExtension($RfcPath)

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

    # Handle the Clean option if output directory exists
    if ($Clean -and (Test-Path $OutputFolder -PathType Container)) {
        # Check if there are any files in the directory
        $existingFiles = Get-ChildItem -Path $OutputFolder -Recurse
        if ($existingFiles.Count -gt 0) {
            Write-Host "The output directory contains files: $OutputFolder"
            
            if (-not $Yes) {
                $confirmation = Read-Host "Do you want to clean the directory? (Y/N)"
                if ($confirmation -ne 'Y' -and $confirmation -ne 'y') {
                    Write-Host "Clean operation cancelled by user."
                    return
                }
            }

            Write-Verbose "Cleaning output directory: $OutputFolder"
            try {
                Remove-Item -Path "$OutputFolder\*" -Recurse -Force -ErrorAction Stop
                Write-Host "Output directory cleaned successfully."
            } catch {
                Write-Error "Failed to clean output directory: $_"
                exit 1
            }
        } else {
            Write-Verbose "Output directory exists but is empty. No cleaning needed."
        }
    }

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
        "generate",
        "overview-plan",
        $IndevDir,
        "--output", $OutputFolder
    )
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
