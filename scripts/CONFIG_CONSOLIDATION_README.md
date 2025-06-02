# Configuration Consolidation Scripts

This directory contains scripts to analyze and consolidate the AIWhisperer configuration structure.

## Overview

The AIWhisperer project has accumulated various configuration files over time. These scripts help:
1. Analyze the current configuration landscape
2. Identify duplicates and obsolete files
3. Migrate to a cleaner, hierarchical structure
4. Clean up obsolete configuration files

## Scripts

### 1. `analyze_config_consolidation.py`
Analyzes all configuration files in the project and generates a comprehensive report.

**Usage:**
```bash
python scripts/analyze_config_consolidation.py
```

**Output:**
- `config_consolidation_analysis.md` - Detailed analysis report

### 2. `migrate_configs.py`
Migrates existing configurations to the new hierarchical structure.

**Dry Run (default):**
```bash
python scripts/migrate_configs.py
```

**Execute Migration:**
```bash
python scripts/migrate_configs.py --execute
```

**What it does:**
- Backs up existing configurations
- Creates new directory structure under `config/`
- Migrates configuration files to appropriate locations
- Creates development config templates
- Updates `.gitignore`

### 3. `cleanup_obsolete_configs.py`
Identifies and removes obsolete configuration files.

**Dry Run (default):**
```bash
python scripts/cleanup_obsolete_configs.py
```

**Execute Cleanup:**
```bash
python scripts/cleanup_obsolete_configs.py --execute
```

**Options during execution:**
- Archive files (recommended) - moves to archive directory
- Delete permanently - removes files completely
- Cancel - aborts the operation

### 4. `hierarchical_config_loader.py`
New configuration loader that supports the hierarchical structure with environment-specific overrides.

**Features:**
- Hierarchical configuration loading
- Environment-specific overrides
- Local development overrides
- Environment variable support
- CLI argument overrides
- Backward compatibility with old config structure

## New Configuration Structure

After migration, the configuration structure will be:

```
config/
├── main.yaml           # Primary application configuration
├── agents/
│   ├── agents.yaml     # Agent definitions
│   └── tools.yaml      # Tool sets and permissions
├── models/
│   ├── default.yaml    # Default model settings
│   └── tasks.yaml      # Task-specific overrides
├── development/
│   ├── local.yaml      # Local overrides (gitignored)
│   └── test.yaml       # Test configurations
└── schemas/            # JSON schemas
```

## Migration Workflow

1. **Analyze Current State**
   ```bash
   python scripts/analyze_config_consolidation.py
   ```
   Review the generated report to understand the current configuration landscape.

2. **Backup Important Configs**
   Make sure you have backups of any important configuration files.

3. **Run Migration (Dry Run)**
   ```bash
   python scripts/migrate_configs.py
   ```
   Review what changes will be made.

4. **Execute Migration**
   ```bash
   python scripts/migrate_configs.py --execute
   ```

5. **Update Code References**
   - Update `ai_whisperer/config.py` to use the new loader
   - Update any hardcoded configuration paths in the codebase
   - Run tests to ensure everything works

6. **Clean Up Obsolete Files**
   ```bash
   # First, do a dry run
   python scripts/cleanup_obsolete_configs.py
   
   # If satisfied, execute with archiving
   python scripts/cleanup_obsolete_configs.py --execute
   # Choose option 1 to archive files
   ```

7. **Configure Local Development**
   ```bash
   cp config/development/local.yaml.template config/development/local.yaml
   # Edit local.yaml with your settings
   ```

## Benefits of Consolidation

- **Clarity**: Clear hierarchy makes configuration organization obvious
- **Maintainability**: Fewer files to manage, less duplication
- **Flexibility**: Easy environment-specific overrides
- **Security**: Sensitive configs can be isolated and gitignored
- **Testing**: Test configs separated from production
- **Scalability**: Easy to add new configuration categories

## Notes

- Always run dry-run first before executing any migration or cleanup
- The migration script creates backups automatically
- The cleanup script offers archive option to preserve files
- Local configuration files are gitignored for security
- The new loader maintains backward compatibility during transition