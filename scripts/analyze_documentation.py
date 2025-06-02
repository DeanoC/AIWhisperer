#!/usr/bin/env python3
"""Analyze documentation structure for refactoring."""

import os
import re
from pathlib import Path
from typing import Dict, List, Set, Tuple
from datetime import datetime
import json

class DocAnalyzer:
    def __init__(self, root_path: str):
        self.root_path = Path(root_path)
        self.doc_info = []
        self.categories = {
            'architecture': [],
            'api': [],
            'user_guide': [],
            'development': [],
            'implementation': [],
            'rfc': [],
            'plan': [],
            'status': [],
            'execution_log': [],
            'archive': [],
            'prompt': [],
            'readme': [],
            'other': []
        }

    def categorize_doc(self, file_path: Path) -> str:
        """Categorize a documentation file based on path and content."""
        path_str = str(file_path).lower()
        name = file_path.name.lower()
        
        # Path-based categorization
        if '/archive/' in path_str:
            return 'archive'
        elif '/rfc/' in path_str or name.startswith('rfc_'):
            return 'rfc'
        elif '/prompts/' in path_str or name.endswith('.prompt.md'):
            return 'prompt'
        elif '/api/' in path_str:
            return 'api'
        elif 'architecture' in name:
            return 'architecture'
        elif 'readme' in name:
            return 'readme'
        elif any(x in name for x in ['_log', 'execution-log', 'implementation-log']):
            return 'execution_log'
        elif any(x in name for x in ['status', 'summary', 'complete', 'progress']):
            return 'status'
        elif any(x in name for x in ['plan', 'checklist', 'todo']):
            return 'plan'
        elif any(x in name for x in ['guide', 'tutorial', 'usage']):
            return 'user_guide'
        elif any(x in name for x in ['implementation', 'design', 'spec']):
            return 'implementation'
        elif any(x in name for x in ['development', 'contributing']):
            return 'development'
        else:
            return 'other'

    def analyze_doc_file(self, file_path: Path) -> Dict:
        """Analyze a single documentation file."""
        try:
            stat = file_path.stat()
            
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Extract metadata
            doc_info = {
                'path': str(file_path.relative_to(self.root_path)),
                'name': file_path.name,
                'size': len(content),
                'lines': len(content.splitlines()),
                'category': self.categorize_doc(file_path),
                'last_modified': datetime.fromtimestamp(stat.st_mtime).isoformat(),
                'references': self.find_references(content),
                'has_code_blocks': '```' in content,
                'has_todos': bool(re.search(r'\btodo\b|\bTODO\b', content)),
                'is_empty': len(content.strip()) == 0
            }
            
            # Find title
            title_match = re.match(r'^#\s+(.+)$', content, re.MULTILINE)
            doc_info['title'] = title_match.group(1) if title_match else None
            
            # Check if it's outdated
            doc_info['possibly_outdated'] = self.check_if_outdated(file_path, content)
            
            return doc_info
            
        except Exception as e:
            return {
                'path': str(file_path.relative_to(self.root_path)),
                'error': str(e)
            }

    def find_references(self, content: str) -> Dict[str, List[str]]:
        """Find references to code files in documentation."""
        references = {
            'python_files': [],
            'doc_files': [],
            'config_files': []
        }
        
        # Find Python file references
        py_refs = re.findall(r'`([^`]*\.py)`', content)
        py_refs.extend(re.findall(r'\b(\w+\.py)\b', content))
        references['python_files'] = list(set(py_refs))
        
        # Find doc file references
        md_refs = re.findall(r'\[.*?\]\(([^)]*\.md)\)', content)
        md_refs.extend(re.findall(r'\b(\w+\.md)\b', content))
        references['doc_files'] = list(set(md_refs))
        
        # Find config file references
        config_refs = re.findall(r'`([^`]*\.(yaml|yml|json|ini))`', content)
        config_refs.extend(re.findall(r'\b(\w+\.(yaml|yml|json|ini))\b', content))
        references['config_files'] = [ref[0] if isinstance(ref, tuple) else ref for ref in config_refs]
        
        return references

    def check_if_outdated(self, file_path: Path, content: str) -> bool:
        """Check if documentation might be outdated."""
        indicators = [
            'delegate',  # Old architecture
            'runner',    # Old architecture
            'execution engine',  # Old architecture
            'terminal ui',  # Archived feature
            '2023',  # Old year references
            'TODO: Update',
            'DEPRECATED',
            'OUTDATED'
        ]
        
        content_lower = content.lower()
        return any(indicator in content_lower for indicator in indicators)

    def analyze_all_docs(self) -> Dict:
        """Analyze all documentation files."""
        results = {
            'docs': [],
            'summary': {
                'total_files': 0,
                'total_lines': 0,
                'by_category': {},
                'empty_files': [],
                'outdated_files': [],
                'error_files': []
            }
        }
        
        # Find all markdown files
        for md_file in self.root_path.rglob('*.md'):
            # Skip node_modules and venv
            if any(part in str(md_file) for part in ['node_modules', 'venv', '.venv', '__pycache__']):
                continue
            
            doc_info = self.analyze_doc_file(md_file)
            
            if 'error' in doc_info:
                results['summary']['error_files'].append(doc_info['path'])
                continue
            
            results['docs'].append(doc_info)
            results['summary']['total_files'] += 1
            results['summary']['total_lines'] += doc_info['lines']
            
            # Categorize
            category = doc_info['category']
            if category not in results['summary']['by_category']:
                results['summary']['by_category'][category] = 0
            results['summary']['by_category'][category] += 1
            
            # Track issues
            if doc_info['is_empty']:
                results['summary']['empty_files'].append(doc_info['path'])
            if doc_info['possibly_outdated']:
                results['summary']['outdated_files'].append(doc_info['path'])
        
        return results

    def generate_report(self, output_dir: Path):
        """Generate comprehensive documentation analysis reports."""
        output_dir.mkdir(exist_ok=True)
        
        # Analyze all docs
        doc_analysis = self.analyze_all_docs()
        
        # Save detailed doc map
        with open(output_dir / 'doc_map.json', 'w') as f:
            json.dump(doc_analysis, f, indent=2, default=str)
        
        # Generate markdown report
        self.generate_markdown_report(doc_analysis, output_dir / 'doc_map.md')
        
        # Generate recommendations
        self.generate_recommendations(doc_analysis, output_dir / 'doc_recommendations.md')
        
        return doc_analysis

    def generate_markdown_report(self, analysis: Dict, output_path: Path):
        """Generate a markdown report from doc analysis."""
        with open(output_path, 'w') as f:
            f.write("# AIWhisperer Documentation Map\n\n")
            f.write("## Summary\n")
            summary = analysis['summary']
            f.write(f"- Total Documentation Files: {summary['total_files']}\n")
            f.write(f"- Total Lines: {summary['total_lines']:,}\n")
            f.write(f"- Empty Files: {len(summary['empty_files'])}\n")
            f.write(f"- Possibly Outdated: {len(summary['outdated_files'])}\n\n")
            
            f.write("### Documentation by Category\n")
            for category, count in sorted(summary['by_category'].items()):
                f.write(f"- {category}: {count} files\n")
            
            f.write("\n## Documentation Details\n\n")
            
            # Group by category
            docs_by_category = {}
            for doc in analysis['docs']:
                category = doc['category']
                if category not in docs_by_category:
                    docs_by_category[category] = []
                docs_by_category[category].append(doc)
            
            # Write by category
            for category in sorted(docs_by_category.keys()):
                f.write(f"### {category.title().replace('_', ' ')}\n\n")
                
                for doc in sorted(docs_by_category[category], key=lambda x: x['path']):
                    f.write(f"#### `{doc['path']}`\n")
                    if doc['title']:
                        f.write(f"**Title**: {doc['title']}\n")
                    f.write(f"- Lines: {doc['lines']}\n")
                    f.write(f"- Last Modified: {doc['last_modified'][:10]}\n")
                    
                    if doc['possibly_outdated']:
                        f.write("- ⚠️ **Possibly Outdated**\n")
                    if doc['is_empty']:
                        f.write("- ⚠️ **Empty File**\n")
                    if doc['has_todos']:
                        f.write("- 📝 Contains TODOs\n")
                    
                    # Show references
                    refs = doc['references']
                    if any(refs[k] for k in refs):
                        f.write("- References:\n")
                        if refs['python_files']:
                            f.write(f"  - Python: {', '.join(refs['python_files'][:3])}\n")
                        if refs['doc_files']:
                            f.write(f"  - Docs: {', '.join(refs['doc_files'][:3])}\n")
                    
                    f.write("\n")

    def generate_recommendations(self, analysis: Dict, output_path: Path):
        """Generate recommendations for documentation cleanup."""
        with open(output_path, 'w') as f:
            f.write("# Documentation Cleanup Recommendations\n\n")
            
            summary = analysis['summary']
            
            f.write("## Immediate Actions\n\n")
            
            if summary['empty_files']:
                f.write(f"### Delete {len(summary['empty_files'])} Empty Files\n")
                for file in sorted(summary['empty_files'])[:10]:
                    f.write(f"- {file}\n")
                if len(summary['empty_files']) > 10:
                    f.write(f"- ... and {len(summary['empty_files']) - 10} more\n")
                f.write("\n")
            
            if summary['outdated_files']:
                f.write(f"### Review {len(summary['outdated_files'])} Possibly Outdated Files\n")
                for file in sorted(summary['outdated_files'])[:10]:
                    f.write(f"- {file}\n")
                if len(summary['outdated_files']) > 10:
                    f.write(f"- ... and {len(summary['outdated_files']) - 10} more\n")
                f.write("\n")
            
            f.write("## Consolidation Opportunities\n\n")
            
            # Find similar files
            execution_logs = [d for d in analysis['docs'] if d['category'] == 'execution_log']
            if len(execution_logs) > 5:
                f.write(f"### Execution Logs ({len(execution_logs)} files)\n")
                f.write("Consider consolidating multiple execution logs into a single file or archive.\n\n")
            
            status_files = [d for d in analysis['docs'] if d['category'] == 'status']
            if len(status_files) > 5:
                f.write(f"### Status/Summary Files ({len(status_files)} files)\n")
                f.write("Many redundant status updates could be consolidated or archived.\n\n")

if __name__ == "__main__":
    analyzer = DocAnalyzer(Path.cwd())
    analyzer.generate_report(Path("refactor_analysis"))
    print("Documentation analysis complete! Check refactor_analysis/ directory for results.")