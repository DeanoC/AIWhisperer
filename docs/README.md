# AIWhisperer Documentation

Welcome to the AIWhisperer documentation! This directory contains all current documentation for the project.

## Quick Links

- [Quick Start Guide](QUICK_START.md) - Get up and running quickly
- [Architecture Overview](architecture/architecture.md) - Understand the system design
- [Configuration Guide](configuration.md) - Set up your environment
- [Technical Debt](TECH_DEBT.md) - Known issues and future work

## Documentation Structure

### Core Documentation
- `architecture/` - System architecture and design
  - [Current Architecture](architecture/architecture.md)
  - [Stateless Architecture](architecture/stateless_architecture.md)
  - [Prompt System](architecture/prompt_system.md) - How prompts work with agents
- `api/` - API documentation (to be populated)
- `user/` - User guides (to be populated)
- `development/` - Development guides (to be populated)

### Configuration & Setup
- [configuration.md](configuration.md) - Configuration reference
- [config_examples.md](config_examples.md) - Example configurations

### Feature Documentation
- `completed/` - Completed feature plans and specifications
- System components:
  - [Context Manager Design](context_manager_design.md)
  - [Path Management Design](path_management_design.md)
  - [Tool Interface Design](tool_interface_design.md)
  - [Postprocessing Design](postprocessing_design.md)

### Legacy Documentation
Obsolete documentation has been moved to the `archive/` directory:
- `archive/delegate_system/` - Old delegate-based architecture
- `archive/terminal_ui/` - Terminal UI and monitor system
- `archive/old_architecture/` - Previous architecture designs
- `archive/analysis/` - Old analysis and planning documents

## Contributing to Documentation

When adding new documentation:
1. Place it in the appropriate directory
2. Update this README with a link
3. Use clear, descriptive filenames
4. Include a header explaining the document's purpose
5. Archive obsolete docs rather than deleting them