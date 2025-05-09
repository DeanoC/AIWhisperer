<#
.SYNOPSIS
    This script runs an overview json plan using AIWhisperer.
.DESCRIPTION
   This script utilizes the AIWhisperer tool to run an overview json plan.
   It is designed for testing the 'run' functionality of AIWhisperer.
.PARAMETER PlanFile
   Specifies the path to the input plan json file (e.g., from the output of
   AIWhisperer). This file contains the plan that AI will run.
.PARAMETER OutputProjectFolder
   Specifies the path to the directory where the AIWhisperer plan and subsequent
   project files will be generated. If the directory does not exist, it will be created.
   Example: ./test_output/my_project_plan
.PARAMETER Config
   Specifies the path to a configuration file to be passed to AIWhisperer as --config.
.PARAMETER Clean
   If specified, the script will clean the state.json file in the OutputProjectFolder
.PARAMETER Yes
   If specified along with -Clean, it automatically confirms the cleaning of the
   state.json file without prompting the user.
.EXAMPLE
   # Generate a plan from within the AIWhisperer project's test_runner_scripts directory
   .\create_test_plan.ps1 -RequirementsFile test/simple_project/python_hello_world_requirements.md -OutputProjectFolder test_projects/python_hello_world -Clean -Verbose
   This command generates a plan from 'python_hello_world_requirements.md' into the
   'test_projects/python_hello_world' directory, cleaning the directory first
   and providing verbose output.
.EXAMPLE
   # Generate a plan, specifying AIWhisperer root if script is run from a different location
   .\create_test_plan.ps1 -AIWhispererRootPath ../../aiwhisperer_project -RequirementsFile ./my_tests/requirements.md -OutputProjectFolder ./my_tests_output/plan_01
.EXAMPLE
   Get-Help .\create_test_plan.ps1 -Full
   Displays the full help content for this script.
.NOTES
   Version: 1.1
   Author: AIWhisperer Orchestrator
   Requires the AIWhisperer Python module and a configured .venv environment.
.PARAMETER AIWhispererRootPath
   Path to the AIWhisperer project root directory. Defaults to the current directory.
   This allows the script to be run from outside the AIWhisperer project's
   test_runner_scripts directory.
   Example: -AIWhispererRootPath ../../aiwhisperer_project
#>
[CmdletBinding()]
Param(
    
    [Parameter(Mandatory = $true, Position = 0, ParameterSetName = 'Default', HelpMessage = "Path to the input overview file (e.g., from test/simple_project/).")]
    [string]$PlanFile,

    [Parameter(Mandatory = $true, ParameterSetName = 'Default', HelpMessage = "Path to the directory where the overview will be ran from.")]
    [string]$OutputProjectFolder,

    [Parameter(HelpMessage = "Specifies the path to a configuration file to be passed to AIWhisperer as --config.")]
    [string]$Config,

    [Parameter(HelpMessage = "Switch to clean the output directory before generating new content.")]
    [switch]$Clean,

    [Parameter(HelpMessage = "Automatically confirm prompts without user interaction. Alias: -y.")]
    [Alias("y")]
    [switch]$Yes,

    [Parameter(ParameterSetName = 'Help', HelpMessage = "Show the script's help information.")]
    [switch]$ShowHelp,

    [Parameter(HelpMessage = "Path to the AIWhisperer project root directory. Defaults to the current directory if the script is run from there, or if not specified and the script is elsewhere, it might need to be explicitly set.")]
    [string]$AIWhispererRootPath = "."

)

if ($ShowHelp) {
    Get-Help $PSScriptRoot\run_test_plan.ps1 -Full
    exit 0
}

# Resolve the AIWhisperer project root directory path
$ResolvedAIWhispererRootPath = (Resolve-Path -Path $AIWhispererRootPath).Path

Write-Verbose "AIWhisperer Project Root resolved as: $ResolvedAIWhispererRootPath"

# --- Path Validation ---

# Validate that the RequirementsFile exists
$AbsolutePlanPath = Resolve-Path $PlanFile -ErrorAction SilentlyContinue
if (-not $AbsolutePlanPath) {
    Write-Error "Plan file not found: $PlanFile"
    exit 1
}
Write-Verbose "Plan file resolved to: $AbsolutePlanPath"

# Resolve OutputProjectFolder to an absolute path
$AbsoluteOutputProjectFolderPath = Resolve-Path $OutputProjectFolder -ErrorAction SilentlyContinue
# If Resolve-Path fails, it means the directory doesn't exist, which is handled later.
# We still need the absolute path for the command, so construct it if it doesn't exist yet.
if (-not $AbsoluteOutputProjectFolderPath) {
    $AbsoluteOutputProjectFolderPath = Join-Path (Get-Location) $OutputProjectFolder
    Write-Verbose "Output project folder does not exist, constructing absolute path: $AbsoluteOutputProjectFolderPath"
} else {
    Write-Verbose "Output project folder resolved to: $AbsoluteOutputProjectFolderPath"
}

# Resolve Config to absolute path if specified
if ($Config) {
    $AbsoluteConfigPath = Resolve-Path $Config -ErrorAction SilentlyContinue
    if (-not $AbsoluteConfigPath) {
        Write-Error "Config file not found: $Config"
        exit 1
    }
    $Config = $AbsoluteConfigPath.Path
}

# --- Output Directory Management ---

# If OutputProjectFolder does not exist, create it
if (-not (Test-Path $AbsoluteOutputProjectFolderPath -PathType Container)) {
    Write-Host "Creating output directory: $AbsoluteOutputProjectFolderPath"
    New-Item -Path $AbsoluteOutputProjectFolderPath -ItemType Directory | Out-Null
}

# If -Clean is specified and OutputProjectFolder exists and is not empty
if ($Clean -and (Test-Path "$AbsoluteOutputProjectFolderPath\state.json")) {
    if ($Yes) {
        Write-Host "Cleaning state.json file: $AbsoluteOutputProjectFolderPath\state.json (Auto-confirmed)"
        Remove-Item -Path "$AbsoluteOutputProjectFolderPath\state.json" -Force | Out-Null
    } else {
        $ConfirmClean = Read-Host "state.json file exists in '$AbsoluteOutputProjectFolderPath'. Clean it before proceeding? (Y/N)"
        if ($ConfirmClean -ceq 'Y') {
            Write-Host "Cleaning state.json file: $AbsoluteOutputProjectFolderPath\state.json"
            Remove-Item -Path "$AbsoluteOutputProjectFolderPath\state.json" -Force | Out-Null
        } else {
            Write-Host "Cleaning cancelled. Exiting."
            exit 0
        }
    }
}

# --- Python Environment ---

# Locate the Python executable within the .venv directory relative to the resolved root path
$VenvPythonPath = $null
$VenvScriptsDir = Join-Path $ResolvedAIWhispererRootPath ".venv"
if (Test-Path (Join-Path $VenvScriptsDir "Scripts\python.exe")) { # Windows
    $VenvPythonPath = Join-Path $VenvScriptsDir "Scripts\python.exe"
} elseif (Test-Path (Join-Path $VenvScriptsDir "bin\python")) { # Linux/macOS
    $VenvPythonPath = Join-Path $VenvScriptsDir "bin\python"
}

if (-not $VenvPythonPath) {
    Write-Error "Could not find Python executable in the .venv directory at $VenvScriptsDir. Please ensure the virtual environment is set up relative to the AIWhisperer root path: $ResolvedAIWhispererRootPath"
    exit 1
}
Write-Verbose "Found Python executable: $VenvPythonPath"

# --- AIWhisperer Execution ---

# Construct the command to run AIWhisperer run
$Command = "& `"$VenvPythonPath`" -m src.ai_whisperer.main run --plan-file `"$AbsolutePlanPath`""
if ($Config) {
    $Command += " --config `"$Config`""
}

$Command += " --state-file `"$AbsoluteOutputProjectFolderPath\state.json`""

Write-Verbose "Executing command: $Command"

# Execute the command from the AIWhisperer Project Root directory
Push-Location $ResolvedAIWhispererRootPath
try {
    Invoke-Expression $Command
    $LastExitCode = $LASTEXITCODE
} finally {
    Pop-Location
}

# Check the $LASTEXITCODE after execution
if ($LastExitCode -ne 0) {
    Write-Error "AIWhisperer generate command failed with exit code: $LastExitCode"
    exit $LastExitCode
} else {
    Write-Host "AIWhisperer generate command completed successfully."
}