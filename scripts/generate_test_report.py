#!/usr/bin/env python3
"""
Generate a comprehensive test reorganization report with visualizations.
"""

import os
import json
from pathlib import Path
from datetime import datetime
from collections import defaultdict


def generate_markdown_report(project_root: Path):
    """Generate a markdown report of the test reorganization analysis."""
    
    # Load the reorganization plan
    plan_file = project_root / "test_reorganization_plan.json"
    with open(plan_file, 'r') as f:
        plan = json.load(f)
    
    # Create the report
    report_lines = [
        "# AIWhisperer Test Structure Reorganization Report",
        f"\n**Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        "\n## Executive Summary",
        "",
        "This report provides a comprehensive analysis of the AIWhisperer test structure and a detailed reorganization plan to improve test organization, maintainability, and coverage.",
        "",
        "### Key Metrics",
        "",
        f"- **Total Test Files**: {plan['summary']['total_test_files']}",
        f"- **Files to Move**: {plan['summary']['files_to_move']} ({plan['summary']['files_to_move']/plan['summary']['total_test_files']*100:.1f}%)",
        f"- **Files to Rename**: {plan['summary']['files_to_rename']}",
        f"- **Files to Delete**: {plan['summary']['files_to_delete']}",
        f"- **Files to Review**: {plan['summary']['files_to_review']}",
        f"- **Well-Organized Files**: {plan['summary']['total_test_files'] - sum(plan['summary'].values()) + plan['summary']['total_test_files']} ({(1 - (sum(plan['summary'].values()) - plan['summary']['total_test_files'])/plan['summary']['total_test_files'])*100:.1f}%)",
        "",
        "### Test Distribution",
        "",
        "```",
        "Current Structure:",
        "├── unit/           104 files (62.7%)",
        "├── integration/     26 files (15.7%)",
        "├── server/          24 files (14.5%)",
        "├── uncategorized/    5 files (3.0%)",
        "├── tools/            3 files (1.8%)",
        "├── demo/             2 files (1.2%)",
        "└── other/            2 files (1.2%)",
        "```",
        "",
        "## Issues Identified",
        "",
        "### 1. Misplaced Tests (31 files)",
        "Tests that are in the wrong directory based on their purpose:",
        "",
    ]
    
    # Group actions by issue type
    misplaced = []
    naming_issues = []
    demo_files = []
    
    for action in plan['actions']:
        issues = action['issues']
        for issue in issues:
            if 'Misplaced' in issue:
                misplaced.append(action)
            elif 'Naming' in issue:
                naming_issues.append(action)
            elif 'Demo' in issue:
                demo_files.append(action)
    
    # Add misplaced files
    report_lines.extend([
        "| Current Location | Issue | Proposed Location |",
        "|-----------------|-------|-------------------|"
    ])
    
    for item in misplaced[:5]:  # Show first 5
        current = item['current_path']
        proposed = item['proposed_path'] or "TBD"
        issue = next((i for i in item['issues'] if 'Misplaced' in i), "Misplaced test")
        issue_desc = issue.split(': ')[1] if ': ' in issue else issue
        report_lines.append(f"| `{current}` | {issue_desc} | `{proposed}` |")
    
    if len(misplaced) > 5:
        report_lines.append(f"\n*... and {len(misplaced) - 5} more misplaced files*")
    
    # Add naming issues
    report_lines.extend([
        "",
        "### 2. Naming Convention Issues (9 files)",
        "Files that don't follow the `test_*.py` naming convention:",
        "",
        "| File | Issue |",
        "|------|-------|"
    ])
    
    for item in naming_issues[:5]:
        report_lines.append(f"| `{item['current_path']}` | Should start with 'test_' |")
    
    # Add demo files
    report_lines.extend([
        "",
        "### 3. Demo/Example Files Mixed with Tests (2 files)",
        "Non-test files that should be moved to examples directory:",
        "",
        "- `debbie_demo.py`",
        "- `debbie_practical_example.py`",
        "",
        "## Proposed New Structure",
        "",
        "```",
        "tests/",
        "├── unit/                    # Module-specific unit tests",
        "│   ├── agents/             # Agent system tests",
        "│   ├── ai_loop/            # AI loop tests",
        "│   ├── ai_service/         # AI service tests",
        "│   ├── batch/              # Batch mode tests",
        "│   ├── commands/           # CLI command tests",
        "│   ├── context/            # Context management tests",
        "│   ├── postprocessing/     # Postprocessing tests",
        "│   └── tools/              # Tool tests",
        "├── integration/            # Integration tests",
        "│   ├── batch_mode/         # Batch mode integration",
        "│   ├── rfc_plan/           # RFC to Plan integration",
        "│   └── session/            # Session integration",
        "├── interactive_server/     # Server-specific tests",
        "│   ├── websocket/          # WebSocket tests",
        "│   ├── jsonrpc/            # JSON-RPC tests",
        "│   └── handlers/           # Handler tests",
        "├── performance/            # Performance & stress tests",
        "├── examples/               # Demo files & examples",
        "├── fixtures/               # Test fixtures & data",
        "│   ├── projects/           # Sample projects",
        "│   └── scripts/            # Test scripts",
        "└── conftest.py            # Shared test configuration",
        "```",
        "",
        "## Test Coverage Analysis",
        "",
        "### Coverage Gaps",
        "",
        "- **Total Source Modules**: 138",
        "- **Modules with Tests**: 47 (34.1%)",
        "- **Modules without Tests**: 91 (65.9%)",
        "",
        "### Priority Modules Lacking Coverage",
        "",
        "Critical infrastructure components that should be tested first:",
        "",
        "1. **Handlers & Managers**",
        "   - `ai_whisperer.agents.base_handler`",
        "   - `interactive_server.stateless_session_manager`",
        "   - `interactive_server.services.project_manager`",
        "   - `ai_whisperer.batch.server_manager`",
        "",
        "2. **Services & Processors**",
        "   - `ai_whisperer.ai_service.openrouter_ai_service`",
        "   - `ai_whisperer.batch.script_processor`",
        "   - `postprocessing.scripted_steps.add_items_postprocessor`",
        "",
        "3. **Validators & Tools**",
        "   - `ai_whisperer.json_validator`",
        "   - `ai_whisperer.tools.workspace_validator_tool`",
        "",
        "## Migration Plan",
        "",
        "### Phase 1: Immediate Actions (1-2 days)",
        "",
        "1. **Create new directory structure**",
        "   ```bash",
        "   mkdir -p tests/{unit/{agents,ai_loop,ai_service,batch,commands,context,postprocessing,tools},integration/{batch_mode,rfc_plan,session},performance,examples,fixtures/{projects,scripts}}",
        "   ```",
        "",
        "2. **Move misplaced files** (33 files)",
        "   - Server tests from integration → interactive_server",
        "   - Performance tests → performance directory",
        "   - Demo files → examples directory",
        "",
        "3. **Rename files** (6 files)",
        "   - Add 'test_' prefix to test files",
        "   - Special handling for conftest.py files",
        "",
        "### Phase 2: Test Coverage Improvement (1-2 weeks)",
        "",
        "1. **Create tests for priority modules**",
        "   - Focus on handlers, managers, and services",
        "   - Aim for 80% coverage on critical infrastructure",
        "",
        "2. **Integration test suite**",
        "   - Agent interaction workflows",
        "   - Batch mode end-to-end tests",
        "   - WebSocket communication tests",
        "",
        "### Phase 3: Continuous Improvement",
        "",
        "1. **Maintain test organization**",
        "   - Regular reviews of test placement",
        "   - Update CI/CD to enforce structure",
        "",
        "2. **Coverage monitoring**",
        "   - Set up coverage reporting",
        "   - Track coverage trends",
        "",
        "## Benefits of Reorganization",
        "",
        "1. **Improved Developer Experience**",
        "   - Clear test location based on type",
        "   - Easier to find related tests",
        "   - Better test discovery",
        "",
        "2. **Better Test Isolation**",
        "   - Unit tests separate from integration",
        "   - Performance tests don't slow down CI",
        "   - Examples don't interfere with test runs",
        "",
        "3. **Enhanced Maintainability**",
        "   - Consistent naming conventions",
        "   - Logical directory structure",
        "   - Clear test ownership",
        "",
        "## Implementation Checklist",
        "",
        "- [ ] Review and approve reorganization plan",
        "- [ ] Create migration script",
        "- [ ] Set up new directory structure",
        "- [ ] Execute file moves and renames",
        "- [ ] Update import statements",
        "- [ ] Update CI/CD configuration",
        "- [ ] Update documentation",
        "- [ ] Add __init__.py files",
        "- [ ] Run full test suite",
        "- [ ] Create coverage baseline",
        "",
        "## Conclusion",
        "",
        "The proposed reorganization will significantly improve the AIWhisperer test structure, making it easier to maintain, extend, and understand. The 76.5% of tests that are already well-organized provide a solid foundation, and addressing the remaining 23.5% will create a robust and scalable testing framework.",
        "",
        "The critical next step is improving test coverage from the current 34.1% to at least 70% for core modules, focusing on the identified priority modules that form the backbone of the application.",
    ])
    
    # Write the report
    report_path = project_root / "TEST_REORGANIZATION_REPORT.md"
    with open(report_path, 'w') as f:
        f.write('\n'.join(report_lines))
    
    print(f"Report generated: {report_path}")
    
    # Also create a quick migration script
    create_migration_script(project_root, plan)


def create_migration_script(project_root: Path, plan: dict):
    """Create a migration script for the reorganization."""
    
    script_lines = [
        "#!/usr/bin/env python3",
        '"""',
        "Migration script for AIWhisperer test reorganization.",
        "This script automates the file moves and renames.",
        '"""',
        "",
        "import os",
        "import shutil",
        "from pathlib import Path",
        "",
        "",
        "def migrate_tests():",
        '    """Execute the test migration."""',
        "    project_root = Path(__file__).parent.parent",
        "    tests_dir = project_root / 'tests'",
        "    ",
        "    # Create new directories",
        "    new_dirs = [",
        "        'unit/agents', 'unit/ai_loop', 'unit/ai_service',",
        "        'unit/batch', 'unit/commands', 'unit/context',",
        "        'unit/postprocessing', 'unit/tools',",
        "        'integration/batch_mode', 'integration/rfc_plan',",
        "        'integration/session', 'interactive_server/websocket',",
        "        'interactive_server/jsonrpc', 'interactive_server/handlers',",
        "        'performance', 'examples', 'fixtures/projects',",
        "        'fixtures/scripts'",
        "    ]",
        "    ",
        "    for dir_path in new_dirs:",
        "        (tests_dir / dir_path).mkdir(parents=True, exist_ok=True)",
        "    ",
        "    # File operations",
        "    operations = [",
    ]
    
    # Add move operations
    for action in plan['actions']:
        if action['action'] == 'move' and action['proposed_path']:
            old = action['current_path']
            new = action['proposed_path']
            script_lines.append(f"        ('move', '{old}', '{new}'),")
    
    # Add rename operations  
    for action in plan['actions']:
        if action['action'] == 'rename' and action['proposed_path']:
            old = action['current_path']
            new = action['proposed_path']
            script_lines.append(f"        ('rename', '{old}', '{new}'),")
    
    script_lines.extend([
        "    ]",
        "    ",
        "    # Execute operations",
        "    for op_type, old_path, new_path in operations:",
        "        old_full = tests_dir / old_path",
        "        new_full = tests_dir / new_path",
        "        ",
        "        if old_full.exists():",
        "            print(f'{op_type}: {old_path} → {new_path}')",
        "            new_full.parent.mkdir(parents=True, exist_ok=True)",
        "            shutil.move(str(old_full), str(new_full))",
        "        else:",
        "            print(f'Warning: {old_path} not found')",
        "    ",
        "    print('\\nMigration complete!')",
        "",
        "",
        "if __name__ == '__main__':",
        "    migrate_tests()",
    ])
    
    script_path = project_root / "scripts" / "migrate_tests.py"
    with open(script_path, 'w') as f:
        f.write('\n'.join(script_lines))
    
    os.chmod(script_path, 0o755)
    print(f"Migration script created: {script_path}")


def main():
    """Main entry point."""
    project_root = Path(__file__).parent.parent
    generate_markdown_report(project_root)


if __name__ == "__main__":
    main()