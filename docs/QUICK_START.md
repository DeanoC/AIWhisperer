# AIWhisperer Quick Start Guide

Welcome to AIWhisperer! This guide will get you up and running in minutes.

## Prerequisites

- Python 3.12+
- Node.js 16+ (for the web interface)
- An OpenRouter API key

## Installation

1. **Clone and setup:**
   ```bash
   git clone <repository-url>
   cd AIWhisperer
   python3.12 -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   pip install -r requirements.txt
   ```

2. **Configure API access:**
   ```bash
   cp config.yaml.example config.yaml
   # Edit config.yaml and add your OpenRouter API key
   ```

3. **Setup the frontend:**
   ```bash
   cd frontend
   npm install
   cd ..
   ```

## Quick Start - Interactive Mode

1. **Start the backend server:**
   ```bash
   python -m interactive_server.main
   ```

2. **In a new terminal, start the frontend:**
   ```bash
   cd frontend
   npm start
   ```

3. **Open your browser:** Navigate to http://localhost:3000

4. **Start chatting!** Alice the Assistant will introduce herself and help you get started.

## Quick Start - CLI Mode

Generate a complete project plan from requirements:

```bash
python -m ai_whisperer.main generate full-plan requirements.md --config config.yaml
```

This will create:
- Initial task plan
- Detailed overview with subtasks
- All subtask definitions

## Meet the Agents

In the interactive interface, you can switch between specialized AI agents:

- **Alice (A)**: Your general assistant for coding and guidance
- **Patricia (P)**: Creates detailed implementation plans
- **Tessa (T)**: Generates comprehensive test suites

Switch agents by typing `/agent <letter>` or using the UI selector.

## Next Steps

- Check out the full [README.md](../README.md) for detailed documentation
- Explore [example requirements](../tests/simple_project/) for inspiration
- Read about the [architecture](architecture/architecture.md)
- Learn about [custom agent development](../CLAUDE.md#agent-development)

## Troubleshooting

### Common Issues:

**OpenRouter API errors:**
- Verify your API key in config.yaml
- Check you have credits at openrouter.ai

**Frontend won't start:**
- Ensure Node.js 16+ is installed
- Run `npm install` in the frontend directory

**Can't connect to server:**
- Check the backend is running on port 8000
- Verify no firewall is blocking connections

## Getting Help

- Review the documentation in `/docs`
- Check existing issues on GitHub
- Ask Alice in the interactive mode!

Happy coding with AIWhisperer! 🚀