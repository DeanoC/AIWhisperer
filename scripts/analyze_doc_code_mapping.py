#!/usr/bin/env python3
"""
Documentation to Code Mapping Analysis Tool

This tool analyzes the relationship between documentation files and source code
to identify:
1. Which docs refer to which code files/components
2. Which code has no documentation coverage
3. Which docs are orphaned (no code references)
4. Staleness indicators based on modification times

Part of the AIWhisperer refactor Phase 0: Documentation Modernization
"""

import os
import re
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Set, Optional, Tuple
from dataclasses import dataclass, asdict
import argparse


@dataclass
class DocCodeReference:
    """Represents a reference from documentation to code."""
    doc_file: str
    code_reference: str
    reference_type: str  # 'file', 'class', 'function', 'module'
    line_number: int
    context: str  # surrounding text


@dataclass
class FileAnalysis:
    """Analysis results for a single file."""
    file_path: str
    size_bytes: int
    last_modified: datetime
    references_found: List[DocCodeReference]
    is_stale: bool
    staleness_reason: str


@dataclass
class MappingReport:
    """Complete mapping analysis report."""
    docs_analyzed: int
    code_files_found: int
    total_references: int
    orphaned_docs: List[str]
    undocumented_code: List[str]
    doc_analysis: List[FileAnalysis]
    code_coverage_map: Dict[str, List[str]]  # code_file -> [doc_files]


class DocCodeMapper:
    """Analyzes documentation to code mapping."""
    
    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.docs_dir = project_root / "docs"
        self.code_dirs = [
            project_root / "ai_whisperer",
            project_root / "interactive_server",
            project_root / "frontend" / "src",
            project_root / "postprocessing",
            project_root / "tests"
        ]
        
        # Patterns to match code references
        self.code_patterns = [
            # File paths
            (r'`([a-zA-Z_][a-zA-Z0-9_/]*\.py)`', 'file'),
            (r'`([a-zA-Z_][a-zA-Z0-9_/]*\.tsx?)`', 'file'),
            (r'`([a-zA-Z_][a-zA-Z0-9_/]*\.yaml)`', 'file'),
            (r'`([a-zA-Z_][a-zA-Z0-9_/]*\.json)`', 'file'),
            
            # Python modules
            (r'`([a-zA-Z_][a-zA-Z0-9_.]*)`', 'module'),
            
            # Class names (PascalCase)
            (r'\b([A-Z][a-zA-Z0-9]*(?:[A-Z][a-zA-Z0-9]*)*)\b', 'class'),
            
            # Function names with parentheses
            (r'`([a-z_][a-zA-Z0-9_]*)\(\)`', 'function'),
            (r'\b([a-z_][a-zA-Z0-9_]*)\(\)', 'function'),
            
            # Directory references
            (r'`([a-zA-Z_][a-zA-Z0-9_/]*)/`', 'directory'),
        ]
    
    def find_all_docs(self) -> List[Path]:
        """Find all markdown documentation files."""
        docs = []
        if self.docs_dir.exists():
            docs.extend(self.docs_dir.rglob("*.md"))
        
        # Also check root-level docs
        docs.extend(self.project_root.glob("*.md"))
        
        return [doc for doc in docs if doc.is_file()]
    
    def find_all_code_files(self) -> List[Path]:
        """Find all source code files."""
        code_files = []
        
        for code_dir in self.code_dirs:
            if code_dir.exists():
                # Python files
                code_files.extend(code_dir.rglob("*.py"))
                # TypeScript files
                code_files.extend(code_dir.rglob("*.ts"))
                code_files.extend(code_dir.rglob("*.tsx"))
                # Config files
                code_files.extend(code_dir.rglob("*.yaml"))
                code_files.extend(code_dir.rglob("*.json"))
        
        return [f for f in code_files if f.is_file()]
    
    def extract_code_references(self, doc_path: Path) -> List[DocCodeReference]:
        """Extract code references from a documentation file."""
        references = []
        
        try:
            with open(doc_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
        except Exception as e:
            print(f"Warning: Could not read {doc_path}: {e}")
            return references
        
        for line_num, line in enumerate(lines, 1):
            for pattern, ref_type in self.code_patterns:
                matches = re.finditer(pattern, line)
                for match in matches:
                    reference = match.group(1)
                    
                    # Filter out obvious false positives
                    if self._is_likely_code_reference(reference, ref_type):
                        references.append(DocCodeReference(
                            doc_file=str(doc_path.relative_to(self.project_root)),
                            code_reference=reference,
                            reference_type=ref_type,
                            line_number=line_num,
                            context=line.strip()
                        ))
        
        return references
    
    def _is_likely_code_reference(self, reference: str, ref_type: str) -> bool:
        """Filter out false positives in code references."""
        # Skip common English words
        common_words = {
            'the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 
            'with', 'by', 'from', 'up', 'about', 'into', 'through', 'during',
            'before', 'after', 'above', 'below', 'between', 'among', 'under',
            'over', 'API', 'CLI', 'UI', 'URL', 'HTTP', 'JSON', 'YAML', 'AI'
        }
        
        if reference.lower() in common_words:
            return False
        
        # For file type, check if it looks like a real path
        if ref_type == 'file':
            return '/' in reference or reference.endswith(('.py', '.ts', '.tsx', '.yaml', '.json'))
        
        # For modules, check if it looks like a Python module
        if ref_type == 'module':
            return '.' in reference and not reference.startswith('.')
        
        # For classes, check reasonable length
        if ref_type == 'class':
            return 3 <= len(reference) <= 50
        
        # For functions, check reasonable length
        if ref_type == 'function':
            return 3 <= len(reference) <= 50 and not reference.lower() in common_words
        
        return True
    
    def check_reference_validity(self, references: List[DocCodeReference], 
                               code_files: List[Path]) -> List[DocCodeReference]:
        """Check which references actually exist in the codebase."""
        valid_references = []
        code_file_names = {f.name for f in code_files}
        code_file_paths = {str(f.relative_to(self.project_root)) for f in code_files}
        
        for ref in references:
            is_valid = False
            
            if ref.reference_type == 'file':
                # Check direct path match or filename match
                if ref.code_reference in code_file_paths or ref.code_reference in code_file_names:
                    is_valid = True
            elif ref.reference_type == 'module':
                # Check if module path exists
                module_path = ref.code_reference.replace('.', '/') + '.py'
                if module_path in code_file_paths:
                    is_valid = True
            else:
                # For classes and functions, we'll assume they're valid if they follow patterns
                # More sophisticated analysis would require parsing the actual code
                is_valid = True
            
            if is_valid:
                valid_references.append(ref)
        
        return valid_references
    
    def analyze_staleness(self, doc_path: Path, references: List[DocCodeReference], 
                         code_files: List[Path]) -> Tuple[bool, str]:
        """Determine if a doc is stale based on modification times."""
        try:
            doc_mtime = datetime.fromtimestamp(doc_path.stat().st_mtime)
        except Exception:
            return True, "Cannot read modification time"
        
        if not references:
            return True, "No code references found"
        
        # Check if any referenced code is newer than the doc
        code_file_map = {str(f.relative_to(self.project_root)): f for f in code_files}
        code_file_map.update({f.name: f for f in code_files})
        
        newest_code_time = None
        for ref in references:
            if ref.reference_type in ['file', 'module']:
                code_file = code_file_map.get(ref.code_reference)
                if code_file and code_file.exists():
                    try:
                        code_mtime = datetime.fromtimestamp(code_file.stat().st_mtime)
                        if newest_code_time is None or code_mtime > newest_code_time:
                            newest_code_time = code_mtime
                    except Exception:
                        continue
        
        if newest_code_time and newest_code_time > doc_mtime:
            days_stale = (newest_code_time - doc_mtime).days
            return True, f"Code modified {days_stale} days after doc"
        
        return False, "Up to date"
    
    def analyze(self) -> MappingReport:
        """Perform complete documentation to code mapping analysis."""
        print("🔍 Starting documentation to code mapping analysis...")
        
        # Find all files
        docs = self.find_all_docs()
        code_files = self.find_all_code_files()
        
        print(f"📄 Found {len(docs)} documentation files")
        print(f"💻 Found {len(code_files)} code files")
        
        # Analyze each doc
        doc_analyses = []
        all_references = []
        
        for doc_path in docs:
            print(f"  Analyzing {doc_path.relative_to(self.project_root)}...")
            
            references = self.extract_code_references(doc_path)
            valid_references = self.check_reference_validity(references, code_files)
            is_stale, staleness_reason = self.analyze_staleness(doc_path, valid_references, code_files)
            
            analysis = FileAnalysis(
                file_path=str(doc_path.relative_to(self.project_root)),
                size_bytes=doc_path.stat().st_size,
                last_modified=datetime.fromtimestamp(doc_path.stat().st_mtime),
                references_found=valid_references,
                is_stale=is_stale,
                staleness_reason=staleness_reason
            )
            
            doc_analyses.append(analysis)
            all_references.extend(valid_references)
        
        # Build coverage map
        code_coverage_map = {}
        code_file_paths = {str(f.relative_to(self.project_root)) for f in code_files}
        code_file_names = {f.name: str(f.relative_to(self.project_root)) for f in code_files}
        
        for ref in all_references:
            if ref.reference_type in ['file', 'module']:
                code_path = ref.code_reference
                if code_path in code_file_paths:
                    target_path = code_path
                elif code_path in code_file_names:
                    target_path = code_file_names[code_path]
                else:
                    continue
                
                if target_path not in code_coverage_map:
                    code_coverage_map[target_path] = []
                if ref.doc_file not in code_coverage_map[target_path]:
                    code_coverage_map[target_path].append(ref.doc_file)
        
        # Find orphaned docs and undocumented code
        orphaned_docs = [
            analysis.file_path for analysis in doc_analyses 
            if not analysis.references_found
        ]
        
        undocumented_code = [
            str(f.relative_to(self.project_root)) for f in code_files
            if str(f.relative_to(self.project_root)) not in code_coverage_map
        ]
        
        return MappingReport(
            docs_analyzed=len(docs),
            code_files_found=len(code_files),
            total_references=len(all_references),
            orphaned_docs=orphaned_docs,
            undocumented_code=undocumented_code,
            doc_analysis=doc_analyses,
            code_coverage_map=code_coverage_map
        )
    
    def generate_report(self, report: MappingReport, output_path: Path):
        """Generate a comprehensive analysis report."""
        with open(output_path, 'w') as f:
            f.write("# Documentation to Code Mapping Analysis Report\n\n")
            f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            
            # Summary
            f.write("## Summary\n\n")
            f.write(f"- **Documentation files analyzed**: {report.docs_analyzed}\n")
            f.write(f"- **Code files found**: {report.code_files_found}\n")
            f.write(f"- **Total code references**: {report.total_references}\n")
            f.write(f"- **Orphaned docs**: {len(report.orphaned_docs)}\n")
            f.write(f"- **Undocumented code files**: {len(report.undocumented_code)}\n")
            f.write(f"- **Code coverage**: {len(report.code_coverage_map)}/{report.code_files_found} files ({len(report.code_coverage_map)/report.code_files_found*100:.1f}%)\n\n")
            
            # Orphaned documentation
            if report.orphaned_docs:
                f.write("## Orphaned Documentation\n")
                f.write("Files with no code references (candidates for archival):\n\n")
                for doc in sorted(report.orphaned_docs):
                    f.write(f"- `{doc}`\n")
                f.write("\n")
            
            # Undocumented code
            if report.undocumented_code:
                f.write("## Undocumented Code\n")
                f.write("Code files with no documentation references:\n\n")
                for code_file in sorted(report.undocumented_code):
                    f.write(f"- `{code_file}`\n")
                f.write("\n")
            
            # Stale documentation
            stale_docs = [analysis for analysis in report.doc_analysis if analysis.is_stale]
            if stale_docs:
                f.write("## Stale Documentation\n")
                f.write("Documentation that may be outdated:\n\n")
                for analysis in sorted(stale_docs, key=lambda x: x.file_path):
                    f.write(f"- `{analysis.file_path}`: {analysis.staleness_reason}\n")
                f.write("\n")
            
            # Code coverage details
            f.write("## Code Coverage Details\n\n")
            for code_file in sorted(report.code_coverage_map.keys()):
                docs = report.code_coverage_map[code_file]
                f.write(f"**`{code_file}`** ({len(docs)} doc(s)):\n")
                for doc in sorted(docs):
                    f.write(f"  - {doc}\n")
                f.write("\n")
            
            # API migration candidates
            f.write("## API Documentation Migration Candidates\n\n")
            api_docs = []
            for analysis in report.doc_analysis:
                if any('api' in analysis.file_path.lower() or 
                      'function' in ref.reference_type or 
                      'class' in ref.reference_type 
                      for ref in analysis.references_found):
                    api_docs.append(analysis.file_path)
            
            if api_docs:
                f.write("Files containing API documentation that should be moved to code:\n\n")
                for doc in sorted(api_docs):
                    f.write(f"- `{doc}`\n")
            else:
                f.write("No obvious API documentation files found.\n")
            f.write("\n")
    
    def save_json_data(self, report: MappingReport, output_path: Path):
        """Save detailed analysis data as JSON for other tools."""
        # Convert dataclasses to dict
        data = asdict(report)
        
        # Convert datetime objects to strings
        for analysis in data['doc_analysis']:
            analysis['last_modified'] = analysis['last_modified'].isoformat()
        
        with open(output_path, 'w') as f:
            json.dump(data, f, indent=2)


def main():
    parser = argparse.ArgumentParser(description="Analyze documentation to code mapping")
    parser.add_argument("--project-root", type=Path, default=Path("."),
                       help="Project root directory (default: current directory)")
    parser.add_argument("--output", type=Path, default=Path("doc_code_mapping_report.md"),
                       help="Output report file (default: doc_code_mapping_report.md)")
    parser.add_argument("--json", type=Path, 
                       help="Also save detailed data as JSON")
    
    args = parser.parse_args()
    
    mapper = DocCodeMapper(args.project_root)
    report = mapper.analyze()
    
    print(f"\n📊 Analysis complete!")
    print(f"📄 Analyzed {report.docs_analyzed} docs with {report.total_references} code references")
    print(f"🔍 Found {len(report.orphaned_docs)} orphaned docs and {len(report.undocumented_code)} undocumented code files")
    print(f"📈 Code coverage: {len(report.code_coverage_map)}/{report.code_files_found} files ({len(report.code_coverage_map)/report.code_files_found*100:.1f}%)")
    
    mapper.generate_report(report, args.output)
    print(f"📝 Report saved to: {args.output}")
    
    if args.json:
        mapper.save_json_data(report, args.json)
        print(f"💾 JSON data saved to: {args.json}")


if __name__ == "__main__":
    main()