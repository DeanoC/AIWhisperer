# Documentation Cleanup Completion Plan

## Current Status
- ✅ 48 files successfully merged into 4 consolidated files
- ❌ 45 files pending archival (script error occurred)
- ❌ File count discrepancy needs investigation

## Phase 1: Complete the Archiving (45 files)

### Files to Archive:
Based on the consolidation report, these files need to be moved to `docs/archive/consolidated_phase2/`:

1. **Already Merged Files** (should be safe to archive):
   - All source files from TEST_CONSOLIDATED_SUMMARY.md
   - All source files from PHASE_CONSOLIDATED_SUMMARY.md
   - Debugging session files (except DEBBIE_BATCH_MODE_EXAMPLE.md)
   - Agent-E execution logs

2. **Old/Outdated Files** identified in the report:
   - Files marked as >90 days old
   - Files containing deprecated markers
   - refactor_backup files

## Phase 2: Fix the File Count Issue

The script reported 250 files but we actually have 2922. This needs investigation:
1. Check if the script is filtering certain directories incorrectly
2. Identify where the extra ~2700 files are located
3. Determine if these should be included in consolidation

## Phase 3: Additional Consolidation Opportunities

1. **Batch Mode Docs**: Consolidate the 9 batch mode files into a single guide
2. **Checklists**: Merge the 9 checklist files into categories
3. **Implementation Plans**: Consolidate the 7 implementation plan files

## Execution Steps

### Step 1: Create Archive Script
```python
# archive_remaining_files.py
# This script will safely move the 45 files that failed to archive
```

### Step 2: Investigate File Count
```bash
# Find where the extra files are
find . -name "*.md" -type f -not -path "./node_modules/*" -not -path "./.venv/*" | \
  awk -F/ '{print $2}' | sort | uniq -c | sort -nr
```

### Step 3: Run Additional Consolidation
- Batch mode consolidation
- Checklist consolidation
- Implementation plan consolidation

## Safety Measures
1. All operations will be done with backups
2. Use dry-run mode first
3. Verify file contents before deletion
4. Keep the `.doc_backup/20250602_115315/` directory intact

## Expected Final Result
- Current: 231 files (after partial consolidation)
- Target: ~160 files (after completing all phases)
- Total reduction: ~90 files