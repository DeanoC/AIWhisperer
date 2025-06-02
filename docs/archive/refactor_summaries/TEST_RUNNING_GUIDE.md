# Test Running Guide

## Test Categories

Our test suite is organized into several categories using pytest markers:

### Core Categories
- **unit** - Fast, isolated unit tests with no external dependencies
- **integration** - Tests that integrate multiple components
- **slow** - Tests that take significant time to run
- **network** - Tests that use sockets, websockets, or network connections
- **requires_api** - Tests that require API keys (OpenRouter, etc.)
- **performance** - Benchmarking and load tests
- **ai_regression** - Tests using Debbie/batch runner to validate AI behavior

## Running Tests

### Local Development

```bash
# Run all tests
pytest

# Run only unit tests (fastest)
pytest -m unit

# Run unit and fast integration tests
pytest -m "unit or (integration and not slow)"

# Run everything except slow tests
pytest -m "not slow"

# Run everything except tests requiring API keys
pytest -m "not requires_api"

# Run AI regression tests with Debbie
OPENROUTER_API_KEY=your_key pytest -m ai_regression
```

### CI/CD Pipeline

The CI pipeline runs tests in stages:

1. **Linting** (every PR/push)
   - flake8 for syntax errors
   - black for formatting

2. **Unit Tests** (every PR/push)
   - Fast unit tests only
   - No network, API, or slow tests
   - Code coverage reporting

3. **Integration Tests** (push to main/develop only)
   - Integration tests without API requirements
   - No slow or AI regression tests

4. **Full Test Suite** (manual trigger)
   - All tests including API and slow tests
   - Requires environment with secrets
   - Used before releases

### Running AI Regression Tests

AI regression tests use Debbie to validate AI behavior:

```bash
# Run a specific AI regression script
python -m ai_whisperer.batch.batch_client scripts/test_continuation_feature.json

# Run all AI regression tests
pytest -m ai_regression -v

# Run with specific model
ANTHROPIC_MODEL=claude-3-opus-20240229 pytest -m ai_regression
```

### Debugging Test Failures

```bash
# Run with verbose output
pytest -v

# Run with detailed failure info
pytest -vv

# Run specific test
pytest tests/unit/test_specific.py::test_function_name

# Run with debugging
pytest --pdb  # Drop into debugger on failure

# Run with logging
pytest --log-cli-level=DEBUG
```

## Writing Tests

### Adding Markers to Tests

```python
import pytest

@pytest.mark.unit
def test_simple_function():
    assert 1 + 1 == 2

@pytest.mark.integration
@pytest.mark.network
async def test_websocket_connection():
    # Test that uses network
    pass

@pytest.mark.ai_regression
@pytest.mark.requires_api
def test_ai_behavior():
    # Test that validates AI responses
    pass

@pytest.mark.slow
@pytest.mark.performance
def test_large_dataset_processing():
    # Performance benchmark
    pass
```

### Test Organization

```
tests/
├── unit/              # Fast, isolated tests
├── integration/       # Multi-component tests
├── performance/       # Benchmarks and load tests
├── ai_regression/     # AI behavior validation
└── scripts/          # Debbie test scripts (.json/.txt)
```

## Troubleshooting

### Common Issues

1. **WebSocket/Async Errors in CI**
   - Mark with `@pytest.mark.network`
   - Will skip in default CI runs

2. **API Key Errors**
   - Mark with `@pytest.mark.requires_api`
   - Set OPENROUTER_API_KEY environment variable

3. **Timeout Errors**
   - Mark with `@pytest.mark.slow`
   - Increase timeout: `@pytest.mark.timeout(300)`

4. **Flaky Tests**
   - Use `@pytest.mark.flaky(reruns=3)`
   - Investigate root cause

### Performance Tips

- Run unit tests first during development
- Use `-x` to stop on first failure
- Use `--lf` to run last failed tests
- Use parallel execution: `pytest -n auto`
