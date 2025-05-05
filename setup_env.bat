@echo off
REM Replace the path below with the actual path to your Python 3.13 executable
set PYTHON_PATH=C:\Path\To\Your\Python3.13\python.exe

echo Using Python at: %PYTHON_PATH%

if not exist .venv (
    echo Creating virtual environment...
    %PYTHON_PATH% -m venv .venv
) else (
    echo Virtual environment already exists.
)

echo Activating virtual environment...
call .venv\Scripts\activate

echo Installing requirements...
%PYTHON_PATH% -m pip install -r requirements.txt

echo Environment setup complete. You can now run:
echo pytest
