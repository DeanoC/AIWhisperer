# Documentation Consolidation Script

This script helps manage and consolidate the AIWhisperer documentation by identifying redundancies, duplicates, and outdated files.

## Purpose

The AIWhisperer project has accumulated 239 markdown documentation files with significant redundancies:
- Multiple test summary files for the same testing effort
- Numerous phase summary files that should be consolidated
- 24 files from a single debugging session
- Multiple execution logs for Agent E implementation
- Outdated architecture documentation mixed with current ones

This script analyzes all markdown files and creates a consolidation plan to reduce documentation sprawl.

## Usage

### Dry Run Mode (Default - Safe)
```bash
# Analyze and generate report without making changes
python scripts/refactor_phase2_doc_consolidation.py
```

### Execute Mode (Makes Changes)
```bash
# Actually perform the consolidation
python scripts/refactor_phase2_doc_consolidation.py --execute
```

### Custom Project Root
```bash
python scripts/refactor_phase2_doc_consolidation.py --project-root /path/to/project
```

## What It Does

1. **Analysis Phase**:
   - Finds all markdown files (excluding vendor directories)
   - Categorizes files by type (test summaries, phase summaries, etc.)
   - Identifies exact duplicates by content hash
   - Finds outdated files (>90 days old or containing deprecated markers)
   - Calculates similarity between files

2. **Consolidation Planning**:
   - Groups related files for merging
   - Identifies duplicates for deletion
   - Marks outdated files for archival
   - Creates a detailed consolidation plan

3. **Execution Phase** (when --execute is used):
   - Creates timestamped backup of all affected files
   - Merges related files with table of contents
   - Deletes duplicate files
   - Archives outdated files to `docs/archive/consolidated_phase2/`

## Categories Handled

- **Test Summaries**: TEST_*.md files → TEST_CONSOLIDATED_SUMMARY.md
- **Phase Summaries**: *PHASE*SUMMARY*.md files → PHASE_CONSOLIDATED_SUMMARY.md
- **Batch Mode**: Files related to batch mode documentation
- **Debugging Session**: Files from debugging-session-2025-05-30/
- **Agent E Logs**: agent-e-*execution-log.md files
- **Implementation Plans**: Various implementation plan documents
- **Checklists**: Various checklist documents
- **RFC Documents**: RFC-related documentation
- **Architecture**: Architecture documentation files

## Safety Features

1. **Dry Run by Default**: Shows what would happen without making changes
2. **Automatic Backup**: Creates timestamped backup before any modifications
3. **Confirmation Required**: Asks for confirmation before executing changes
4. **Detailed Reporting**: Generates comprehensive report of all actions
5. **Preserves History**: Archives rather than deletes important files

## Output

The script generates:
1. A detailed report: `doc_consolidation_report_YYYYMMDD_HHMMSS.md`
2. Console summary showing reduction statistics
3. Backup directory: `.doc_backup/YYYYMMDD_HHMMSS/` (when executing)

## Example Output

```
============================================================
CONSOLIDATION SUMMARY
============================================================
Current files: 246
Files after consolidation: 161
Total reduction: 85 files (34.6%)

Breakdown:
  - Files to merge: 48 → 4 consolidated files
  - Files to delete (duplicates): 0
  - Files to archive: 41
  - Outdated files identified: 34
============================================================
```

## Restoration

If you need to restore files after consolidation:
1. Navigate to the backup directory shown in the output
2. Copy files back to their original locations
3. The backup preserves the full directory structure

## Notes

- The script excludes common vendor directories (node_modules, .venv, etc.)
- Merged files include a table of contents and preserve original content
- The consolidation is designed to maintain documentation accessibility while reducing clutter
- Archive location: `docs/archive/consolidated_phase2/`