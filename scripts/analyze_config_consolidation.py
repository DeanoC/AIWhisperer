#!/usr/bin/env python3
"""
Configuration Consolidation Analysis Script

This script analyzes all configuration files in the AIWhisperer project
and provides recommendations for consolidation and cleanup.
"""

import os
import json
import yaml
import configparser
from pathlib import Path
from collections import defaultdict
from typing import Dict, List, Set, Tuple, Any
import hashlib
from datetime import datetime

class ConfigAnalyzer:
    """Analyzes configuration files for consolidation opportunities"""
    
    # Configuration file extensions to analyze
    CONFIG_EXTENSIONS = {'.yaml', '.yml', '.json', '.ini', '.toml', '.cfg'}
    
    # Directories to skip during analysis
    SKIP_DIRS = {
        'node_modules', '.git', '__pycache__', '.venv', 'venv',
        'build', 'dist', '.pytest_cache', '.mypy_cache'
    }
    
    def __init__(self, root_path: str = '.'):
        self.root_path = Path(root_path).absolute()
        self.configs: Dict[str, Dict[str, Any]] = {}
        self.config_by_type: Dict[str, List[str]] = defaultdict(list)
        self.config_by_purpose: Dict[str, List[str]] = defaultdict(list)
        self.duplicate_content: Dict[str, List[str]] = defaultdict(list)
        self.similar_configs: List[Tuple[str, str, float]] = []
        
    def find_config_files(self) -> List[Path]:
        """Find all configuration files in the project"""
        config_files = []
        
        for root, dirs, files in os.walk(self.root_path):
            # Remove directories we want to skip
            dirs[:] = [d for d in dirs if d not in self.SKIP_DIRS]
            
            root_path = Path(root)
            for file in files:
                file_path = root_path / file
                if file_path.suffix in self.CONFIG_EXTENSIONS:
                    config_files.append(file_path)
                    
        return sorted(config_files)
    
    def analyze_config_file(self, file_path: Path) -> Dict[str, Any]:
        """Analyze a single configuration file"""
        relative_path = file_path.relative_to(self.root_path)
        
        info = {
            'path': str(relative_path),
            'absolute_path': str(file_path),
            'type': file_path.suffix,
            'size': file_path.stat().st_size,
            'purpose': self._determine_purpose(file_path),
            'content': None,
            'content_hash': None,
            'keys': [],
            'parse_error': None
        }
        
        try:
            # Read and parse the content
            content_str = file_path.read_text(encoding='utf-8')
            info['content_hash'] = hashlib.md5(content_str.encode()).hexdigest()
            
            if file_path.suffix in ['.yaml', '.yml']:
                content = yaml.safe_load(content_str)
                info['content'] = content
                if isinstance(content, dict):
                    info['keys'] = list(content.keys())
            elif file_path.suffix == '.json':
                content = json.loads(content_str)
                info['content'] = content
                if isinstance(content, dict):
                    info['keys'] = list(content.keys())
            elif file_path.suffix in ['.ini', '.cfg']:
                parser = configparser.ConfigParser()
                parser.read_string(content_str)
                info['keys'] = parser.sections()
                info['content'] = {s: dict(parser[s]) for s in parser.sections()}
            elif file_path.suffix == '.toml':
                try:
                    import toml
                    content = toml.loads(content_str)
                    info['content'] = content
                    if isinstance(content, dict):
                        info['keys'] = list(content.keys())
                except ImportError:
                    info['parse_error'] = "toml library not installed"
                    
        except Exception as e:
            info['parse_error'] = str(e)
            
        return info
    
    def _determine_purpose(self, file_path: Path) -> str:
        """Determine the purpose of a configuration file based on its location and name"""
        path_str = str(file_path.relative_to(self.root_path))
        name = file_path.stem.lower()
        
        # Check path patterns
        if 'test' in path_str:
            return 'test_config'
        elif 'frontend' in path_str:
            return 'frontend_config'
        elif 'project_dev' in path_str:
            return 'development_artifact'
        elif 'refactor_backup' in path_str:
            return 'backup_config'
        elif 'schemas' in path_str:
            return 'schema_definition'
        elif 'scripts' in path_str:
            return 'script_config'
        
        # Check file name patterns
        if name == 'config':
            return 'main_config'
        elif name == 'agents':
            return 'agent_config'
        elif name == 'tool_sets':
            return 'tool_config'
        elif 'package' in name:
            return 'package_config'
        elif 'tsconfig' in name:
            return 'typescript_config'
        elif 'jest' in name or 'eslint' in name:
            return 'frontend_tooling'
        elif 'pytest' in name:
            return 'test_config'
        elif 'pyproject' in name:
            return 'project_metadata'
        elif 'subtask' in name or 'overview' in name:
            return 'task_artifact'
        elif name == 'sessions':
            return 'runtime_state'
        elif name == 'manifest':
            return 'webapp_metadata'
            
        return 'unknown'
    
    def find_duplicates(self):
        """Find duplicate configuration files by content hash"""
        hash_to_files = defaultdict(list)
        
        for path, info in self.configs.items():
            if info['content_hash']:
                hash_to_files[info['content_hash']].append(path)
                
        for hash_val, files in hash_to_files.items():
            if len(files) > 1:
                self.duplicate_content[hash_val] = files
    
    def analyze_content_overlap(self):
        """Analyze content overlap between configuration files"""
        yaml_configs = [
            (path, info) for path, info in self.configs.items() 
            if info['type'] in ['.yaml', '.yml'] and info['content'] and isinstance(info['content'], dict)
        ]
        
        # Compare configuration keys
        for i, (path1, info1) in enumerate(yaml_configs):
            for path2, info2 in yaml_configs[i+1:]:
                keys1 = set(info1['keys'])
                keys2 = set(info2['keys'])
                
                if keys1 and keys2:
                    overlap = keys1.intersection(keys2)
                    if overlap:
                        similarity = len(overlap) / min(len(keys1), len(keys2))
                        if similarity > 0.3:  # More than 30% overlap
                            self.similar_configs.append((path1, path2, similarity))
    
    def generate_consolidation_plan(self) -> Dict[str, Any]:
        """Generate a consolidation plan based on analysis"""
        plan = {
            'proposed_structure': {
                'config/': {
                    'main.yaml': 'Main application configuration (consolidate config.yaml)',
                    'agents/': {
                        'agents.yaml': 'Agent definitions and configurations',
                        'tools.yaml': 'Tool sets and permissions'
                    },
                    'models/': {
                        'default.yaml': 'Default model configurations',
                        'task_specific.yaml': 'Task-specific model overrides'
                    },
                    'development/': {
                        'local.yaml': 'Local development overrides (gitignored)',
                        'test.yaml': 'Test-specific configurations'
                    },
                    'schemas/': 'Move all JSON schemas here'
                }
            },
            'actions': [],
            'obsolete_files': [],
            'consolidation_targets': defaultdict(list)
        }
        
        # Identify obsolete files
        for path, info in self.configs.items():
            if info['purpose'] in ['backup_config', 'development_artifact', 'task_artifact']:
                plan['obsolete_files'].append({
                    'path': path,
                    'reason': f"Appears to be {info['purpose'].replace('_', ' ')}"
                })
        
        # Identify consolidation opportunities
        if 'config.yaml' in self.configs:
            plan['consolidation_targets']['main_config'].append('config.yaml')
            
        # Group agent-related configs
        for path, info in self.configs.items():
            if info['purpose'] == 'agent_config':
                plan['consolidation_targets']['agent_configs'].append(path)
            elif info['purpose'] == 'tool_config':
                plan['consolidation_targets']['tool_configs'].append(path)
                
        # Add specific actions
        plan['actions'] = [
            {
                'action': 'create_directory_structure',
                'description': 'Create config/ directory with subdirectories for organization'
            },
            {
                'action': 'consolidate_main_config',
                'description': 'Merge config.yaml with any environment-specific overrides',
                'files': plan['consolidation_targets']['main_config']
            },
            {
                'action': 'centralize_schemas',
                'description': 'Move all JSON schemas to config/schemas/',
                'files': [p for p, i in self.configs.items() if i['purpose'] == 'schema_definition']
            },
            {
                'action': 'remove_obsolete',
                'description': 'Remove or archive obsolete configuration files',
                'count': len(plan['obsolete_files'])
            },
            {
                'action': 'create_config_loader',
                'description': 'Update config.py to support new hierarchical structure with overrides'
            }
        ]
        
        return plan
    
    def generate_report(self) -> str:
        """Generate a comprehensive analysis report"""
        report = []
        report.append("# AIWhisperer Configuration Analysis Report")
        report.append(f"\nGenerated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append(f"Project Root: {self.root_path}")
        
        # Summary
        report.append("\n## Summary")
        report.append(f"- Total configuration files found: {len(self.configs)}")
        report.append(f"- Duplicate files: {sum(len(f) - 1 for f in self.duplicate_content.values())}")
        report.append(f"- Configuration types: {', '.join(sorted(set(self.config_by_type.keys())))}")
        
        # Configuration Inventory
        report.append("\n## Configuration Inventory")
        for purpose in sorted(self.config_by_purpose.keys()):
            files = self.config_by_purpose[purpose]
            report.append(f"\n### {purpose.replace('_', ' ').title()} ({len(files)} files)")
            for file in sorted(files):
                info = self.configs[file]
                report.append(f"- `{file}` ({info['size']} bytes)")
                if info['parse_error']:
                    report.append(f"  - ⚠️ Parse error: {info['parse_error']}")
                elif info['keys']:
                    # Convert all keys to strings to handle mixed types
                    keys_str = [str(k) for k in info['keys'][:5]]
                    report.append(f"  - Keys: {', '.join(keys_str)}")
                    if len(info['keys']) > 5:
                        report.append(f"    ... and {len(info['keys']) - 5} more")
        
        # Duplicates
        if self.duplicate_content:
            report.append("\n## Duplicate Files")
            for hash_val, files in self.duplicate_content.items():
                report.append(f"\n### Duplicate Group (hash: {hash_val[:8]}...)")
                for file in files:
                    report.append(f"- `{file}`")
        
        # Similar Configurations
        if self.similar_configs:
            report.append("\n## Similar Configurations")
            report.append("Files with significant key overlap:")
            for file1, file2, similarity in sorted(self.similar_configs, key=lambda x: x[2], reverse=True):
                report.append(f"- `{file1}` ↔️ `{file2}` ({similarity:.0%} similarity)")
        
        # Consolidation Plan
        plan = self.generate_consolidation_plan()
        report.append("\n## Consolidation Plan")
        
        report.append("\n### Proposed Directory Structure")
        report.append("```")
        report.append("config/")
        report.append("├── main.yaml           # Primary application configuration")
        report.append("├── agents/")
        report.append("│   ├── agents.yaml     # Agent definitions")
        report.append("│   └── tools.yaml      # Tool sets and permissions")
        report.append("├── models/")
        report.append("│   ├── default.yaml    # Default model settings")
        report.append("│   └── tasks.yaml      # Task-specific overrides")
        report.append("├── development/")
        report.append("│   ├── local.yaml      # Local overrides (gitignored)")
        report.append("│   └── test.yaml       # Test configurations")
        report.append("└── schemas/            # JSON schemas")
        report.append("```")
        
        report.append("\n### Migration Steps")
        for i, action in enumerate(plan['actions'], 1):
            report.append(f"\n{i}. **{action['description']}**")
            if 'files' in action and action['files']:
                report.append("   Files affected:")
                for file in action['files'][:5]:
                    report.append(f"   - `{file}`")
                if len(action['files']) > 5:
                    report.append(f"   - ... and {len(action['files']) - 5} more")
        
        # Obsolete Files
        if plan['obsolete_files']:
            report.append(f"\n### Obsolete Files ({len(plan['obsolete_files'])} files)")
            report.append("These files appear to be outdated or temporary:")
            for item in plan['obsolete_files'][:10]:
                report.append(f"- `{item['path']}` - {item['reason']}")
            if len(plan['obsolete_files']) > 10:
                report.append(f"- ... and {len(plan['obsolete_files']) - 10} more")
        
        # Benefits
        report.append("\n## Benefits of Consolidation")
        report.append("- **Clarity**: Clear hierarchy makes it obvious where configurations belong")
        report.append("- **Maintainability**: Fewer files to manage, less duplication")
        report.append("- **Flexibility**: Environment-specific overrides without modifying core configs")
        report.append("- **Security**: Sensitive configs can be isolated and gitignored")
        report.append("- **Testing**: Test configs separated from production configs")
        
        # Implementation Notes
        report.append("\n## Implementation Notes")
        report.append("1. Update `config.py` to support hierarchical loading with overrides")
        report.append("2. Create migration script to move files to new structure")
        report.append("3. Update documentation to reflect new configuration structure")
        report.append("4. Add config validation to ensure all required fields are present")
        report.append("5. Consider using a configuration management library (e.g., OmegaConf)")
        
        return '\n'.join(report)
    
    def run(self):
        """Run the complete analysis"""
        print("🔍 Finding configuration files...")
        config_files = self.find_config_files()
        print(f"Found {len(config_files)} configuration files")
        
        print("\n📊 Analyzing configuration files...")
        for file_path in config_files:
            info = self.analyze_config_file(file_path)
            relative_path = str(file_path.relative_to(self.root_path))
            self.configs[relative_path] = info
            self.config_by_type[info['type']].append(relative_path)
            self.config_by_purpose[info['purpose']].append(relative_path)
        
        print("\n🔎 Finding duplicates...")
        self.find_duplicates()
        
        print("\n🔗 Analyzing content overlap...")
        self.analyze_content_overlap()
        
        print("\n📝 Generating report...")
        report = self.generate_report()
        
        # Save report
        report_path = self.root_path / 'config_consolidation_analysis.md'
        report_path.write_text(report, encoding='utf-8')
        print(f"\n✅ Analysis complete! Report saved to: {report_path}")
        
        # Print summary
        print("\n📋 Summary:")
        print(f"   - Configuration files: {len(self.configs)}")
        print(f"   - Duplicate files: {sum(len(f) - 1 for f in self.duplicate_content.values())}")
        print(f"   - Obsolete files: {len([i for i in self.configs.values() if i['purpose'] in ['backup_config', 'development_artifact', 'task_artifact']])}")
        print(f"   - Similar configs: {len(self.similar_configs)}")


if __name__ == '__main__':
    analyzer = ConfigAnalyzer()
    analyzer.run()