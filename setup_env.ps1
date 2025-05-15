param()

$venvPath = ".venv"
$pythonPath = "$venvPath\Scripts\python.exe"
$activateScript = "$venvPath\Scripts\Activate.ps1"
$srcPath = Join-Path $PSScriptRoot "src"

Write-Host "Using Python at: $pythonPath"

if (-not (Test-Path $venvPath)) {
    Write-Host "Creating virtual environment..."
    & $pythonPath -m venv $venvPath
} else {
    Write-Host "Virtual environment already exists."
}

Write-Host "Activating virtual environment..."
. $activateScript

Write-Host "Setting PYTHONPATH for this session..."
$env:PYTHONPATH = "$($env:PYTHONPATH);$srcPath"

Write-Host "Installing requirements..."
& $pythonPath -m pip install -r requirements.txt

Write-Host "`nEnvironment setup complete. You can now run:"
Write-Host "    pytest"
Write-Host "`nNOTE: PYTHONPATH is set only for this session."
Write-Host "If you open a new PowerShell window, run this script again to set up the environment."

Write-Host "`nNOTE: If you see WinError 448 or PluggyTeardownRaisedWarning during pytest runs, it is a known Windows/Python/pytest issue and can usually be ignored. There is currently no environment variable to suppress this warning."
