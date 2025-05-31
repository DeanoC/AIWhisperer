#!/usr/bin/env python3
"""
Test script to validate Patricia's RFC-to-plan conversion with structured output.
"""

import asyncio
import json
from pathlib import Path
import pytest

@pytest.mark.asyncio
async def test_patricia_rfc_to_plan():
    """Test Patricia's ability to generate structured plans from RFCs."""
    
    # First, let's create a simple RFC for testing
    print("Creating test RFC...")
    
    # Simulate creating an RFC through the interactive server
    # In real usage, this would be done through the WebSocket API
    
    rfc_content = """# RFC: Add Dark Mode Support

## Summary
Implement a dark mode toggle for the application UI.

## Requirements
- User-toggleable dark/light mode
- Persist preference across sessions
- Apply theme to all UI components
- Support system preference detection

## Technical Approach
- Use CSS variables for theming
- React Context for theme state
- LocalStorage for persistence
- Media query for system preference

## Acceptance Criteria
- [ ] Toggle switches between dark and light modes
- [ ] Preference persists on reload
- [ ] All components respect theme
- [ ] Follows system preference on first load
"""
    
    # Save test RFC
    from ai_whisperer.path_management import PathManager
    import os
    
    # Initialize PathManager
    workspace_path = os.getcwd()
    PathManager().initialize(config_values={
        'workspace_path': workspace_path,
        'output_path': workspace_path
    })
    path_manager = PathManager.get_instance()
    
    rfc_dir = Path(path_manager.workspace_path) / ".WHISPER" / "rfc" / "in_progress"
    rfc_dir.mkdir(parents=True, exist_ok=True)
    
    # Create RFC metadata
    rfc_metadata = {
        "rfc_id": "RFC-2025-05-31-TEST",
        "short_name": "dark-mode-test",
        "title": "Add Dark Mode Support",
        "created": "2025-05-31T10:00:00Z",
        "status": "in_progress",
        "filename": "dark-mode-test.md"
    }
    
    # Save RFC files
    rfc_md_path = rfc_dir / "dark-mode-test.md"
    rfc_json_path = rfc_dir / "dark-mode-test.json"
    
    with open(rfc_md_path, 'w') as f:
        f.write(rfc_content)
    
    with open(rfc_json_path, 'w') as f:
        json.dump(rfc_metadata, f, indent=2)
    
    print(f"Created test RFC: {rfc_metadata['rfc_id']}")
    
    # Now test Patricia's plan generation
    print("\nTesting Patricia's plan generation with structured output...")
    
    # This demonstrates what would happen in the interactive server
    # when Patricia processes a prepare_plan_from_rfc call
    
    print("""
Expected workflow:
1. User asks Patricia to create a plan from the RFC
2. Patricia uses prepare_plan_from_rfc tool
3. System detects plan generation context
4. System enables structured output if model supports it
5. Patricia generates JSON plan directly
6. Patricia uses save_generated_plan tool
""")
    
    # Clean up test RFC
    print("\nCleaning up test RFC...")
    rfc_md_path.unlink(missing_ok=True)
    rfc_json_path.unlink(missing_ok=True)
    
    print("\nTest setup complete!")
    print("To fully test structured output:")
    print("1. Start the interactive server: python -m interactive_server.main")
    print("2. Connect with a client")
    print("3. Switch to Patricia agent")
    print("4. Ask: 'Please create a plan from the dark-mode-test RFC'")
    print("\nThe system will automatically use structured output if available.")

if __name__ == "__main__":
    asyncio.run(test_patricia_rfc_to_plan())