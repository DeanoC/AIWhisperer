#!/usr/bin/env python3
"""
Project Settings Persistence Test Script
Tests that settings are correctly saved and loaded from the backend.
"""

import os
import sys
import json
import tempfile
import shutil
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def test_settings_persistence():
    """Test that project settings persist correctly."""
    print("🧪 Testing Project Settings Persistence")
    print("=" * 50)
    
    try:
        # Import the backend models and services
        from interactive_server.models.project import ProjectCreate, ProjectUpdate, ProjectSettings
        from interactive_server.services.project_manager import ProjectManager
        
        # Create temporary directories for testing
        with tempfile.TemporaryDirectory() as temp_dir:
            print(f"📁 Using temporary directory: {temp_dir}")
            
            data_dir = Path(temp_dir) / "data"
            project_dir = Path(temp_dir) / "test_project"
            project_dir.mkdir(parents=True)
            data_dir.mkdir(parents=True)
            
            # Initialize ProjectManager with data directory
            project_manager = ProjectManager(data_dir)
            
            print("\n1️⃣ Testing project creation...")
            
            # Test 1: Create project
            create_data = ProjectCreate(
                name="Test Project",
                path=str(project_dir),
                output_path=str(project_dir),
                description="Test project for settings persistence"
            )
            project = project_manager.create_project(create_data)
            print(f"✅ Created project: {project.name} (ID: {project.id})")
            print(f"✅ Initial settings: {project.settings.model_dump()}")
            
            print("\n2️⃣ Testing settings update...")
            
            # Test 2: Update project settings (copy exact format from working test)
            update_data = ProjectUpdate(
                name="Test Project",
                output_path=str(project_dir),
                description="Test project for settings persistence",
                settings=ProjectSettings(
                    default_agent="alice",
                    auto_save=False,
                    external_agent_type="openai"
                )
            )
            
            updated_project = project_manager.update_project(project.id, update_data)
            if updated_project:
                print(f"✅ Updated settings: {updated_project.settings.model_dump()}")
                
                # Verify they match
                assert updated_project.settings.default_agent == "alice"
                assert updated_project.settings.auto_save == False
                assert updated_project.settings.external_agent_type == "openai"
                print("✅ Settings match expected values")
            else:
                raise Exception("Failed to update project")
            
            print("\n3️⃣ Testing settings modification...")
            
            # Test 3: Modify settings again (copy exact format from working test)
            update_data2 = ProjectUpdate(
                name="Test Project",
                output_path=str(project_dir),
                description="Test project for settings persistence",
                settings=ProjectSettings(
                    default_agent="bob",
                    auto_save=True,
                    external_agent_type="anthropic"
                )
            )
            
            updated_project2 = project_manager.update_project(project.id, update_data2)
            if updated_project2:
                print(f"✅ Updated settings: {updated_project2.settings.model_dump()}")
            else:
                raise Exception("Failed to update project settings")
            
            print("\n4️⃣ Testing persistence across reload...")
            
            # Test 4: Create new ProjectManager instance to simulate reload
            new_project_manager = ProjectManager(data_dir)
            reloaded_project = new_project_manager.get_project(project.id)
            
            if reloaded_project:
                print(f"✅ Reloaded settings: {reloaded_project.settings.model_dump()}")
                
                # Verify persistence
                assert reloaded_project.settings.default_agent == "bob"
                assert reloaded_project.settings.auto_save == True
                assert reloaded_project.settings.external_agent_type == "anthropic"
                print("✅ Settings persisted correctly across reload")
            else:
                raise Exception("Failed to reload project")
            
            print("\n5️⃣ Testing file system persistence...")
            
            # Test 5: Check that .WHISPER/project.json exists
            whisper_path = Path(reloaded_project.whisper_path)
            project_json = whisper_path / "project.json"
            assert project_json.exists(), f"Project file should exist at {project_json}"
            print(f"✅ Project file exists: {project_json}")
            
            # Verify file contents
            with open(project_json, 'r') as f:
                file_data = json.load(f)
            print(f"✅ Project file settings: {file_data.get('settings', {})}")
            
            settings_data = file_data.get('settings', {})
            assert settings_data["default_agent"] == "bob"
            assert settings_data["auto_save"] == True
            assert settings_data["external_agent_type"] == "anthropic"
            print("✅ File contents match expected values")
            
            print("\n🎉 ALL TESTS PASSED!")
            print("✅ Project settings persistence is working correctly")
            
            return True
            
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False

def run_integration_test():
    """Run the pytest integration test."""
    print("\n🧪 Running Backend Integration Test")
    print("=" * 50)
    
    import subprocess
    
    try:
        # Run the integration test
        result = subprocess.run([
            sys.executable, "-m", "pytest", 
            "tests/integration/test_project_settings_persistence.py", 
            "-v"
        ], cwd=project_root, capture_output=True, text=True)
        
        print("STDOUT:")
        print(result.stdout)
        
        if result.stderr:
            print("STDERR:")
            print(result.stderr)
        
        if result.returncode == 0:
            print("✅ Integration test passed!")
            return True
        else:
            print(f"❌ Integration test failed with return code: {result.returncode}")
            return False
            
    except Exception as e:
        print(f"❌ Failed to run integration test: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Starting Project Settings Test Suite")
    print("=" * 60)
    
    # Run persistence test
    persistence_ok = test_settings_persistence()
    
    # Run integration test
    integration_ok = run_integration_test()
    
    print("\n📊 TEST SUMMARY")
    print("=" * 30)
    print(f"Persistence Test: {'✅ PASS' if persistence_ok else '❌ FAIL'}")
    print(f"Integration Test: {'✅ PASS' if integration_ok else '❌ FAIL'}")
    
    if persistence_ok and integration_ok:
        print("\n🎉 ALL TESTS SUCCESSFUL!")
        print("Project settings persistence is working correctly.")
        sys.exit(0)
    else:
        print("\n💥 SOME TESTS FAILED!")
        print("Please check the errors above.")
        sys.exit(1)
