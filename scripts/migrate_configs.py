#!/usr/bin/env python3
"""
Configuration Migration Script

This script migrates the current configuration structure to the new consolidated structure.
It should be run after backing up the current configuration files.
"""

import os
import shutil
import json
import yaml
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Set

class ConfigMigrator:
    """Migrates configuration files to new consolidated structure"""
    
    def __init__(self, root_path: str = '.', dry_run: bool = True):
        self.root_path = Path(root_path).absolute()
        self.dry_run = dry_run
        self.backup_dir = self.root_path / f"config_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.new_config_dir = self.root_path / "config"
        self.operations_log = []
        
    def log_operation(self, operation: str, details: str):
        """Log an operation that will be or was performed"""
        self.operations_log.append({
            'operation': operation,
            'details': details,
            'dry_run': self.dry_run
        })
        prefix = "[DRY RUN] " if self.dry_run else ""
        print(f"{prefix}{operation}: {details}")
    
    def create_directory_structure(self):
        """Create the new configuration directory structure"""
        directories = [
            self.new_config_dir,
            self.new_config_dir / "agents",
            self.new_config_dir / "models",
            self.new_config_dir / "development",
            self.new_config_dir / "schemas"
        ]
        
        for directory in directories:
            if not directory.exists():
                self.log_operation("CREATE_DIR", str(directory.relative_to(self.root_path)))
                if not self.dry_run:
                    directory.mkdir(parents=True, exist_ok=True)
    
    def backup_existing_configs(self):
        """Backup existing configuration files"""
        configs_to_backup = [
            "config.yaml",
            "ai_whisperer/agents/config/agents.yaml",
            "ai_whisperer/tools/tool_sets.yaml",
            "schemas",
            "pyproject.yaml",
            "pytest.ini"
        ]
        
        if not self.dry_run:
            self.backup_dir.mkdir(exist_ok=True)
        
        for config in configs_to_backup:
            source_path = self.root_path / config
            if source_path.exists():
                dest_path = self.backup_dir / config
                self.log_operation("BACKUP", f"{config} -> {dest_path.relative_to(self.root_path)}")
                if not self.dry_run:
                    if source_path.is_dir():
                        shutil.copytree(source_path, dest_path)
                    else:
                        dest_path.parent.mkdir(parents=True, exist_ok=True)
                        shutil.copy2(source_path, dest_path)
    
    def migrate_main_config(self):
        """Migrate main configuration file"""
        source = self.root_path / "config.yaml"
        dest = self.new_config_dir / "main.yaml"
        
        if source.exists():
            self.log_operation("MIGRATE", f"config.yaml -> config/main.yaml")
            if not self.dry_run:
                # Read and process the config
                with open(source, 'r') as f:
                    config = yaml.safe_load(f)
                
                # Extract model-specific settings
                task_models = config.pop('task_models', {})
                
                # Write main config
                with open(dest, 'w') as f:
                    yaml.dump(config, f, default_flow_style=False, sort_keys=False)
                
                # Write task models to separate file
                if task_models:
                    models_dest = self.new_config_dir / "models" / "tasks.yaml"
                    with open(models_dest, 'w') as f:
                        yaml.dump({'task_models': task_models}, f, default_flow_style=False)
                    self.log_operation("EXTRACT", f"Task models -> config/models/tasks.yaml")
    
    def migrate_agent_configs(self):
        """Migrate agent-related configurations"""
        # Migrate agents.yaml
        agents_source = self.root_path / "ai_whisperer/agents/config/agents.yaml"
        agents_dest = self.new_config_dir / "agents" / "agents.yaml"
        
        if agents_source.exists():
            self.log_operation("MIGRATE", f"{agents_source.relative_to(self.root_path)} -> {agents_dest.relative_to(self.root_path)}")
            if not self.dry_run:
                shutil.copy2(agents_source, agents_dest)
        
        # Migrate tool_sets.yaml
        tools_source = self.root_path / "ai_whisperer/tools/tool_sets.yaml"
        tools_dest = self.new_config_dir / "agents" / "tools.yaml"
        
        if tools_source.exists():
            self.log_operation("MIGRATE", f"{tools_source.relative_to(self.root_path)} -> {tools_dest.relative_to(self.root_path)}")
            if not self.dry_run:
                shutil.copy2(tools_source, tools_dest)
    
    def migrate_schemas(self):
        """Migrate JSON schemas"""
        schemas_source = self.root_path / "schemas"
        schemas_dest = self.new_config_dir / "schemas"
        
        if schemas_source.exists() and schemas_source.is_dir():
            for schema_file in schemas_source.glob("*.json"):
                dest_file = schemas_dest / schema_file.name
                self.log_operation("MIGRATE", f"{schema_file.relative_to(self.root_path)} -> {dest_file.relative_to(self.root_path)}")
                if not self.dry_run:
                    shutil.copy2(schema_file, dest_file)
    
    def create_development_configs(self):
        """Create development configuration templates"""
        # Create local.yaml template
        local_template = {
            "# Local Development Configuration": None,
            "# This file is gitignored and can contain local overrides": None,
            "": None,
            "openrouter": {
                "# api_key": "your-local-api-key-here",
                "# model": "override-model-for-local-dev"
            }
        }
        
        local_dest = self.new_config_dir / "development" / "local.yaml.template"
        self.log_operation("CREATE", f"{local_dest.relative_to(self.root_path)}")
        if not self.dry_run:
            with open(local_dest, 'w') as f:
                yaml.dump(local_template, f, default_flow_style=False)
        
        # Create test.yaml template
        test_template = {
            "# Test Configuration": None,
            "# Settings specific to test environments": None,
            "": None,
            "openrouter": {
                "model": "test-model",
                "params": {
                    "temperature": 0.0,
                    "max_tokens": 100
                }
            }
        }
        
        test_dest = self.new_config_dir / "development" / "test.yaml"
        self.log_operation("CREATE", f"{test_dest.relative_to(self.root_path)}")
        if not self.dry_run:
            with open(test_dest, 'w') as f:
                yaml.dump(test_template, f, default_flow_style=False)
    
    def update_gitignore(self):
        """Update .gitignore to include new config patterns"""
        gitignore_path = self.root_path / ".gitignore"
        new_patterns = [
            "\n# Configuration files",
            "config/development/local.yaml",
            "config_backup_*/"
        ]
        
        self.log_operation("UPDATE", ".gitignore")
        if not self.dry_run:
            with open(gitignore_path, 'a') as f:
                for pattern in new_patterns:
                    f.write(f"{pattern}\n")
    
    def create_migration_report(self):
        """Create a detailed migration report"""
        report = {
            'timestamp': datetime.now().isoformat(),
            'dry_run': self.dry_run,
            'operations': self.operations_log,
            'new_structure': {
                'config_dir': str(self.new_config_dir.relative_to(self.root_path)),
                'backup_dir': str(self.backup_dir.relative_to(self.root_path)) if not self.dry_run else None
            }
        }
        
        report_path = self.root_path / f"config_migration_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        self.log_operation("REPORT", str(report_path.relative_to(self.root_path)))
        
        if not self.dry_run:
            with open(report_path, 'w') as f:
                json.dump(report, f, indent=2)
    
    def print_next_steps(self):
        """Print next steps after migration"""
        print("\n" + "="*60)
        print("MIGRATION COMPLETE" if not self.dry_run else "DRY RUN COMPLETE")
        print("="*60)
        
        if self.dry_run:
            print("\nThis was a dry run. To perform the actual migration, run:")
            print("  python scripts/migrate_configs.py --execute")
        else:
            print("\nNext steps:")
            print("1. Update ai_whisperer/config.py to load from new structure")
            print("2. Update all references to old config paths in the codebase")
            print("3. Run tests to ensure everything works correctly")
            print("4. Remove old configuration files after verification")
            print("5. Copy config/development/local.yaml.template to local.yaml and customize")
            print(f"\nBackup created at: {self.backup_dir.relative_to(self.root_path)}")
    
    def run(self):
        """Run the complete migration"""
        print(f"{'DRY RUN: ' if self.dry_run else ''}Starting configuration migration...")
        print(f"Project root: {self.root_path}")
        
        # Backup existing configs
        if not self.dry_run:
            print("\n📦 Backing up existing configurations...")
            self.backup_existing_configs()
        
        # Create new directory structure
        print("\n📁 Creating new directory structure...")
        self.create_directory_structure()
        
        # Migrate configurations
        print("\n🚚 Migrating configuration files...")
        self.migrate_main_config()
        self.migrate_agent_configs()
        self.migrate_schemas()
        
        # Create development configs
        print("\n📝 Creating development configuration templates...")
        self.create_development_configs()
        
        # Update gitignore
        print("\n🔒 Updating .gitignore...")
        self.update_gitignore()
        
        # Create migration report
        print("\n📊 Creating migration report...")
        self.create_migration_report()
        
        # Print next steps
        self.print_next_steps()


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Migrate AIWhisperer configurations to new structure')
    parser.add_argument('--execute', action='store_true', 
                       help='Actually perform the migration (default is dry run)')
    parser.add_argument('--root', default='.', 
                       help='Project root directory (default: current directory)')
    
    args = parser.parse_args()
    
    migrator = ConfigMigrator(root_path=args.root, dry_run=not args.execute)
    migrator.run()