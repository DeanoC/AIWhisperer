[CmdletBinding()] # Enables common parameters like -Verbose, -Debug
param(
    [Parameter(Mandatory = $true, Position = 0)]
    [string]$InputArg,

    [Parameter(HelpMessage = "Switch to clean the output directory before generating new content.")]
    [switch]$Clean,

    [Parameter(HelpMessage = "Automatically confirm prompts without user interaction. Alias: -y.")]
    [Alias("y")]
    [switch]$Yes,

    [Parameter(HelpMessage = "Pass --debug to the Python CLI to wait for debugger attach.")]
    [switch]$DebugPython,

    [Parameter(HelpMessage = "Enable terminal monitor mode.")]
    [switch]$Monitor
)

function Show-Usage {
    Write-Host "Usage:"
    Write-Host "  .\plan_overview_rfc.ps1 <plan_json_path>"
    Write-Host "  .\plan_overview_rfc.ps1 <plan_name>"
    Write-Host ""
    Write-Host "Examples:"
    Write-Host "  .\plan_overview_rfc.ps1 .\project_dev\in_dev\add_1st_runner_test\add_1st_runner_test.json"
    Write-Host "  .\plan_overview_rfc.ps1 add_1st_runner_test"
}

# Resolve argument to JSON file path if needed
if ($InputArg -eq "-h" -or $InputArg -eq "--help" -or $InputArg -eq "/?") {
    Show-Usage
    exit 0
}

if (Test-Path $InputArg -PathType Leaf) {
    $planJsonPath = $InputArg
} else {
    # Assume it's a plan name, try to resolve to JSON file
    $candidate = Join-Path -Path ".\tests\code_generation\$InputArg" -ChildPath "$InputArg.json"
    if (Test-Path $candidate -PathType Leaf) {
        $planJsonPath = $candidate
    } else {
        Write-Host "Could not find plan JSON file for input: $InputArg"
        Show-Usage
        exit 1
    }
}

# --- Script Initialization ---
Write-Verbose "Script starting. PowerShell version: $($PSVersionTable.PSVersion)"
Write-Verbose "Raw Input Argument: '$InputArg'"
Write-Verbose "Resolved Plan JSON Path: '$planJsonPath'"
Write-Verbose "Clean switch set: $Clean"
Write-Verbose "Yes switch set: $Yes"
Write-Verbose "DebugPython switch set: $DebugPython"

# Use the automatic variable $PSScriptRoot for the script's directory
$ScriptDir = $PSScriptRoot
Write-Verbose "Script directory: $ScriptDir"

# Determine Project Root (assuming script is in 'tests/code_generator/n_times_4')
try {
    $ProjectRoot = (Resolve-Path -Path (Join-Path -Path $ScriptDir -ChildPath "..\..")).Path
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

    # Always get the base name for output folder
    $RfcBaseName = [System.IO.Path]::GetFileNameWithoutExtension($planJsonPath)

    Write-Verbose "Constructed RFC Base Name: $RfcBaseName"

    # Validate RFC file existence
    if (-not (Test-Path $planJsonPath -PathType Leaf)) {
        Write-Error "Plan JSON file not found at expected location: '$planJsonPath'. Please ensure the file exists."
        exit 1
    }
    Write-Verbose "Confirmed Plan JSON file exists: $planJsonPath"

    # Locate the .venv Python environment
    # 1. Check for .venv in current directory
    $LocalVenvPythonWin = ".venv\Scripts\python.exe"
    $LocalVenvPythonUnix = ".venv/bin/python"
    if (Test-Path $LocalVenvPythonWin -PathType Leaf) {
        $VenvPythonPath = (Resolve-Path $LocalVenvPythonWin).Path
    } elseif (Test-Path $LocalVenvPythonUnix -PathType Leaf) {
        $VenvPythonPath = (Resolve-Path $LocalVenvPythonUnix).Path
    } else {
        # 2. Fallback to project root .venv
        $VenvPythonPath = Join-Path -Path $ProjectRoot -ChildPath ".venv\Scripts\python.exe" # Windows default
        if (-not (Test-Path $VenvPythonPath -PathType Leaf)) {
            $VenvPythonPath = Join-Path -Path $ProjectRoot -ChildPath ".venv\bin\python" # Linux/macOS/other default
            if (-not (Test-Path $VenvPythonPath -PathType Leaf)) {
                Write-Error "Python executable not found in the virtual environment (.venv/Scripts/python.exe or .venv/bin/python) in current directory or within '$ProjectRoot'. Please ensure the virtual environment is set up correctly and activated, or adjust the path."
                exit 1
            }
        }
    }
    Write-Verbose "Using Python executable from virtual environment: $VenvPythonPath"

    # Locate the main Python script (using module path relative to ProjectRoot)
    $MainModulePath = "ai_whisperer.main" # Path used with python -m

    # Try all possible locations for main.py (project root first)
    $TrueProjectRoot = (Resolve-Path -Path (Join-Path -Path $ScriptDir -ChildPath "..\..")).Path
    $MainPyCheckPaths = @(
        (Join-Path -Path $TrueProjectRoot -ChildPath "ai_whisperer\main.py"),
        (Join-Path -Path (Split-Path $TrueProjectRoot -Parent) -ChildPath "ai_whisperer\main.py"),
        (Join-Path -Path $ProjectRoot    -ChildPath "ai_whisperer\main.py"),
        (Join-Path -Path (Join-Path $ProjectRoot "..") -ChildPath "ai_whisperer\main.py"),
        (Join-Path -Path $ScriptDir      -ChildPath "ai_whisperer\main.py")
    )
    $MainPyCheckPath = $null
    foreach ($candidatePath in $MainPyCheckPaths) {
        if (Test-Path $candidatePath -PathType Leaf) {
            $MainPyCheckPath = $candidatePath
            break
        }
    }
    if (-not $MainPyCheckPath) {
        Write-Error "The main Python script was not found at any of the expected locations:`n$($MainPyCheckPaths -join "`n")`nPlease verify the project structure. If your project root is 'D:\Projects\AIWhisperer', ensure 'src\ai_whisperer\main.py' exists there."
        exit 1
    }
    Write-Verbose "Confirmed main Python script exists for module '$MainModulePath' at '$MainPyCheckPath'"

    # Locate the configuration file
    # Try config in script dir, then parent dirs up to project root
    $ConfigSearchDirs = @(
        $ScriptDir,
        (Join-Path -Path $ScriptDir -ChildPath ".."),
        (Join-Path -Path $ScriptDir -ChildPath "..\.."),
        $ProjectRoot,
        $TrueProjectRoot
    ) | ForEach-Object { (Resolve-Path $_).Path } | Select-Object -Unique

    $ConfigFile = $null
    foreach ($dir in $ConfigSearchDirs) {
        $candidate = Join-Path -Path $dir -ChildPath "aiwhisperer_config.yaml"
        if (Test-Path $candidate -PathType Leaf) {
            $ConfigFile = $candidate
            break
        }
    }
    if (-not $ConfigFile) {
        Write-Error "Configuration file 'aiwhisperer_config.yaml' not found in any of:`n$($ConfigSearchDirs -join "`n")"
        exit 1
    }
    Write-Verbose "Using configuration file: $ConfigFile"

    # Create the output directory ('in_dev/<rfc_basename>')
    $OutputFolder = Join-Path -Path $ScriptDir -ChildPath "output"
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
                # Only delete files starting with 'overview_' or 'subtask_' or 'state.json' (recursively)
                Get-ChildItem -Path $OutputFolder -Recurse -File | Where-Object { $_.Name -like 'overview_*' -or $_.Name -like 'subtask_*' -or $_.Name -eq 'state.json' } | Remove-Item -Force -ErrorAction Stop
                Write-Host "Selected files (overview_*, subtask_*, state.json) deleted successfully from output directory."
            } catch {
                Write-Error "Failed to clean selected files in output directory: $_"
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
        "--config", $ConfigFile
    )
    if ($DebugPython) {
        $pythonArgs += "--debug"
    }
    $pythonArgs += @(
        "run",
        "--plan-file", $planJsonPath,
        "--state-file", (Join-Path -Path $OutputFolder -ChildPath "state.json")
    )
    if ($Monitor) {
        $pythonArgs += "--monitor"
    }
    Write-Verbose "Executing Python script from Project Root: $ProjectRoot"
    Write-Verbose "Command: $VenvPythonPath $($pythonArgs -join ' ')"
    
    # Ensure current directory contains 'src' for correct Python module resolution
    if (-not (Test-Path -Path (Join-Path (Get-Location) "src") -PathType Container)) {
        Set-Location -Path $ProjectRoot
        Write-Verbose "Changed location to Project Root: $ProjectRoot"
    } else {
        Write-Verbose "Current directory already contains 'src'."
    }
    $env:PYTHONPATH = "./src"

    # Execute the command
    & $VenvPythonPath $pythonArgs
    $exitCode = $LASTEXITCODE # Capture exit code immediately

    # Check execution result
    if ($exitCode -ne 0) {
        Write-Error "Python script execution failed with exit code $exitCode."
        # Note: Python script stderr should ideally provide more details.
        exit $exitCode
    }

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
