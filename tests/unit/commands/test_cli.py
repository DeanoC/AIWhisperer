
import subprocess
import sys
import os
import pytest
import pathlib
PACKAGE_ROOT = pathlib.Path(__file__).parent.parent.parent.resolve()

@pytest.mark.parametrize("arglist,expected", [
    (["--help"], "usage:"),
    (["-h"], "usage:"),
])
def test_cli_help_message(arglist, expected):
    """Test that CLI help messages are shown for -h/--help."""
    # Run as a module so relative imports work
    result = subprocess.run([
        sys.executable, "-m", "ai_whisperer", *arglist
    ], capture_output=True, text=True, cwd=str(PACKAGE_ROOT))
    assert expected in result.stdout or expected in result.stderr
    # argparse exits with 0 on help
    assert result.returncode == 0

@pytest.mark.skip(reason="TODO: Add CLI mode selection and test batch/interactive mode dispatch.")
def test_cli_mode_selection():
    """Test that CLI dispatches to batch or interactive mode as appropriate (placeholder)."""
    pass
