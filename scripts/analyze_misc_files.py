#!/usr/bin/env python3
"""Analyze miscellaneous files (configs, scripts, etc.) for refactoring."""

import os
import json
import yaml
from pathlib import Path
from typing import Dict, List, Set
from collections import defaultdict

class MiscAnalyzer:
    def __init__(self, root_path: str):
        self.root_path = Path(root_path)
        self.results = {
            'configs': defaultdict(list),
            'scripts': defaultdict(list),
            'project_artifacts': defaultdict(list),
            'build_files': [],
            'temp_files': [],
            'logs': []
        }

    def analyze(self):
        """Analyze all miscellaneous files."""
        
        # Analyze configuration files
        self.analyze_configs()
        
        # Analyze scripts
        self.analyze_scripts()
        
        # Analyze project_dev
        self.analyze_project_dev()
        
        # Analyze .WHISPER directory
        self.analyze_whisper_dir()
        
        # Find temp and log files
        self.find_temp_and_logs()
        
        return self.results

    def analyze_configs(self):
        """Analyze configuration files."""
        # YAML files
        for yaml_file in self.root_path.rglob('*.yaml'):
            if self.should_skip(yaml_file):
                continue
            
            category = self.categorize_yaml(yaml_file)
            self.results['configs'][category].append({
                'path': str(yaml_file.relative_to(self.root_path)),
                'size': yaml_file.stat().st_size
            })
        
        # JSON configs (not in project_dev)
        for json_file in self.root_path.rglob('*.json'):
            if self.should_skip(json_file) or 'project_dev' in str(json_file):
                continue
            
            if json_file.parent.name == 'schemas':
                self.results['configs']['schemas'].append({
                    'path': str(json_file.relative_to(self.root_path)),
                    'purpose': 'JSON Schema validation'
                })
            elif json_file.parent.name == '.WHISPER':
                self.results['configs']['whisper'].append({
                    'path': str(json_file.relative_to(self.root_path))
                })

    def analyze_scripts(self):
        """Analyze script files."""
        # Python scripts in scripts/
        scripts_dir = self.root_path / 'scripts'
        if scripts_dir.exists():
            for script in scripts_dir.iterdir():
                if script.suffix == '.py':
                    self.results['scripts']['python'].append({
                        'name': script.name,
                        'purpose': self.infer_script_purpose(script)
                    })
                elif script.suffix == '.json':
                    self.results['scripts']['batch_tests'].append({
                        'name': script.name,
                        'type': 'batch mode test script'
                    })
        
        # Shell scripts in root
        for sh_file in self.root_path.glob('*.sh'):
            self.results['scripts']['shell'].append({
                'name': sh_file.name,
                'executable': os.access(sh_file, os.X_OK)
            })

    def analyze_project_dev(self):
        """Analyze project_dev directory."""
        project_dev = self.root_path / 'project_dev'
        if not project_dev.exists():
            return
        
        # Count task JSONs
        done_count = len(list((project_dev / 'done').rglob('*.json')))
        in_dev_count = len(list((project_dev / 'in_dev').rglob('*.json')))
        
        self.results['project_artifacts']['summary'] = {
            'done_tasks': done_count,
            'in_dev_tasks': in_dev_count,
            'total_json_files': done_count + in_dev_count
        }
        
        # Analyze structure
        for task_dir in (project_dev / 'done').iterdir():
            if task_dir.is_dir():
                json_files = list(task_dir.glob('*.json'))
                self.results['project_artifacts']['done_features'].append({
                    'name': task_dir.name,
                    'files': len(json_files),
                    'has_overview': any('overview' in f.name for f in json_files),
                    'subtasks': len([f for f in json_files if 'subtask' in f.name])
                })

    def analyze_whisper_dir(self):
        """Analyze .WHISPER directory structure."""
        whisper_dir = self.root_path / '.WHISPER'
        if not whisper_dir.exists():
            return
        
        self.results['configs']['whisper_structure'] = {
            'has_project_json': (whisper_dir / 'project.json').exists(),
            'plans': len(list((whisper_dir / 'plans').rglob('*.json'))),
            'rfcs': len(list((whisper_dir / 'rfc').rglob('*.md'))),
            'rfc_jsons': len(list((whisper_dir / 'rfc').rglob('*.json')))
        }

    def find_temp_and_logs(self):
        """Find temporary and log files."""
        # Common temp patterns
        temp_patterns = ['*.log', '*.tmp', '*.bak', '*.pyc', '.DS_Store']
        
        for pattern in temp_patterns:
            for temp_file in self.root_path.rglob(pattern):
                if self.should_skip(temp_file):
                    continue
                self.results['temp_files'].append(str(temp_file.relative_to(self.root_path)))
        
        # Text files that might be test outputs
        for txt_file in self.root_path.glob('*.txt'):
            if 'test' in txt_file.name or 'debug' in txt_file.name:
                self.results['temp_files'].append({
                    'name': txt_file.name,
                    'type': 'test output',
                    'size': txt_file.stat().st_size
                })

    def should_skip(self, path: Path) -> bool:
        """Check if path should be skipped."""
        skip_dirs = {'node_modules', '.venv', 'venv', '__pycache__', '.git', 'build', 'dist'}
        return any(part in skip_dirs for part in path.parts)

    def categorize_yaml(self, yaml_file: Path) -> str:
        """Categorize YAML file by purpose."""
        name = yaml_file.name.lower()
        if 'config' in name:
            return 'app_config'
        elif name == 'pyproject.yaml':
            return 'project_meta'
        elif 'agents' in str(yaml_file):
            return 'agent_config'
        elif 'tools' in str(yaml_file):
            return 'tool_config'
        else:
            return 'other'

    def infer_script_purpose(self, script: Path) -> str:
        """Infer script purpose from name."""
        name = script.name.lower()
        if 'analyze' in name:
            return 'Code analysis (refactoring)'
        elif 'test' in name:
            return 'Testing utility'
        elif 'check' in name:
            return 'Validation/checking'
        elif 'run' in name:
            return 'Execution helper'
        else:
            return 'Unknown'

    def generate_report(self):
        """Generate summary report."""
        results = self.analyze()
        
        print("\n=== Miscellaneous Files Analysis ===\n")
        
        print("Configuration Files:")
        for category, files in results['configs'].items():
            if category != 'whisper_structure' and files:
                print(f"  {category}: {len(files)} files")
        
        print("\nScripts:")
        for script_type, scripts in results['scripts'].items():
            if scripts:
                print(f"  {script_type}: {len(scripts)} scripts")
        
        print("\nProject Artifacts:")
        if 'summary' in results['project_artifacts']:
            summary = results['project_artifacts']['summary']
            print(f"  Completed tasks: {summary['done_tasks']} JSON files")
            print(f"  In development: {summary['in_dev_tasks']} JSON files")
            print(f"  Total artifacts: {summary['total_json_files']} files")
        
        print("\nWhisper Directory:")
        if 'whisper_structure' in results['configs']:
            ws = results['configs']['whisper_structure']
            print(f"  Plans: {ws['plans']} files")
            print(f"  RFCs: {ws['rfcs']} markdown + {ws['rfc_jsons']} JSON")
        
        print(f"\nTemporary/Test Files: {len(results['temp_files'])}")
        
        # Save detailed report
        output_path = self.root_path / 'refactor_analysis' / 'misc_files_report.json'
        output_path.parent.mkdir(exist_ok=True)
        with open(output_path, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        
        print(f"\nDetailed report saved to: {output_path}")

if __name__ == "__main__":
    analyzer = MiscAnalyzer(Path.cwd())
    analyzer.generate_report()