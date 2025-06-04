#!/usr/bin/env python3
"""
Quick agent continuation compliance checker for Debbie.

Outputs a simple YES/NO for the current model's compliance.
"""
import subprocess
import re
import json
from pathlib import Path

def check_current_model_compliance():
    """Check if the current model includes continuation signals."""
    # Create test file
    test_file = Path("temp_compliance_test.txt")
    test_file.write_text("Who are you?")
    
    try:
        # Run conversation replay with current config
        result = subprocess.run(
            ["python", "-m", "ai_whisperer.interfaces.cli.main",
             "--config", "config/main.yaml",
             "replay", "temp_compliance_test.txt",
             "--timeout", "5"],
            capture_output=True,
            text=True,
            timeout=20
        )
        
        output = result.stdout + result.stderr
        
        # Find model name
        model_match = re.search(r"Starting OpenRouter stream for model: (.+)", output)
        model = model_match.group(1) if model_match else "Unknown"
        
        # Check for continuation signal
        final_pos = output.rfind("[FINAL]")
        if final_pos != -1:
            response = output[final_pos:final_pos+1000]
            json_pattern = r'\{"continuation":\s*\{[^}]+\}\}'
            has_continuation = bool(re.search(json_pattern, response))
            
            # Output simple result
            if has_continuation:
                print(f"✅ {model}: COMPLIANT")
                return True
            else:
                print(f"❌ {model}: NOT COMPLIANT")
                return False
        else:
            print(f"❓ {model}: Unable to test (no response)")
            return None
            
    finally:
        test_file.unlink(missing_ok=True)

if __name__ == "__main__":
    import sys
    result = check_current_model_compliance()
    # Exit with 0 for compliant, 1 for non-compliant, 2 for error
    if result is True:
        sys.exit(0)
    elif result is False:
        sys.exit(1)
    else:
        sys.exit(2)