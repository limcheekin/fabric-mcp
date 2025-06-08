# Mock Fabric API Server for Integration Testing

This directory contains a minimal FastAPI-based mock server that mimics the Fabric REST API for integration testing purposes.

## Files

- `server.py` - Main FastAPI application with endpoints
- `utils.py` - Utilities for managing the mock server in tests
- `__init__.py` - Package initialization

## Endpoints

The mock server provides the following endpoints:

### GET /

Health check endpoint that returns server status.

**Response:**

```json
{
  "message": "Mock Fabric API Server",
  "status": "running"
}
```

### GET /patterns/names

Returns a list of available pattern names.

**Response:**

```json
["analyze_claims", "create_story", "summarize", "extract_insights", "check_grammar", "create_outline"]
```

### GET /patterns/{pattern_name}

Returns detailed information for a specific pattern.

**Response:**

```json
{
  "name": "analyze_claims",
  "content": "# IDENTITY\nYou are an expert fact checker and truth evaluator...",
  "metadata": {
    "author": "daniel",
    "version": "1.0",
    "tags": ["analysis", "claims", "facts"]
  }
}
```

### POST /patterns/{pattern_name}/run

Executes a pattern with input text.

**Request Body:**

```json
{
  "input": "Text to process"
}
```

**Response:**

```json
{
  "output_format": "text",
  "output_text": "Mock analyze_claims output for input: Text to process...",
  "model_used": "gpt-4o",
  "tokens_used": 150,
  "execution_time_ms": 1250
}
```

## Usage in Tests

### Using the Pytest Fixture

```python
import pytest
import os
from tests.shared.fabric_api.utils import MockFabricAPIServer, setup_mock_fabric_api_env

@pytest.fixture(scope="function")
def mock_fabric_api_server():
    """Pytest fixture that starts and stops the mock Fabric API server."""
    with MockFabricAPIServer() as server:
        # Set environment variables for this test
        old_env = os.environ.copy()
        os.environ.update(setup_mock_fabric_api_env(server))

        try:
            yield server
        finally:
            # Restore original environment
            os.environ.clear()
            os.environ.update(old_env)

def test_with_mock_server(mock_fabric_api_server):
    # Your test code here
    # The FABRIC_BASE_URL environment variable is automatically set
    pass
```

### Using the Built-in Pytest Fixture

Alternatively, you can use the pre-built pytest fixture:

```python
from tests.shared.fabric_api.utils import fabric_api_server_fixture

def test_with_built_in_fixture(fabric_api_server_fixture):
    # Environment variables are automatically set and restored
    server = fabric_api_server_fixture
    print(f"Server running at {server.base_url}")
    # Your test code here
```

### Manual Usage

```python
from tests.shared.fabric_api.utils import MockFabricAPIServer

# Start the server manually
with MockFabricAPIServer() as server:
    print(f"Server running at {server.base_url}")
    # Your test code here
```

### Async Context Manager

For async test environments:

```python
from tests.shared.fabric_api.utils import mock_fabric_api_server

async def test_async_usage():
    async with mock_fabric_api_server() as server:
        print(f"Server running at {server.base_url}")
        # Your async test code here
```

## Environment Variables

When using the mock server, the following environment variables are automatically set:

- `FABRIC_BASE_URL` - Points to the mock server (e.g., `http://127.0.0.1:50659`)
- `FABRIC_API_KEY` - Set to empty string (mock server doesn't require auth)

## Integration with MCP Tests

The mock server is designed to work with the Fabric MCP integration tests. It provides realistic responses that allow testing the complete workflow without requiring a real Fabric server.

The mock server includes predefined patterns and responses:

- **Patterns Available**: `analyze_claims`, `create_story`, `summarize`, `extract_insights`, `check_grammar`, `create_outline`
- **Pattern Details**: Each pattern includes name, content (system prompt), and metadata with author, version, and tags
- **Pattern Execution**: Returns mock output based on the pattern name and input text

See `tests/integration/test_mcp_integration.py` and `tests/integration/test_transport_integration.py` for examples of how the mock server is used in actual integration tests.

## Running the Server Standalone

You can also run the mock server standalone for manual testing:

```bash
cd /path/to/fabric-mcp
python -m tests.shared.fabric_api.server --host 127.0.0.1 --port 8080
```

The server will be available at `http://127.0.0.1:8080` and you can test the endpoints manually or with tools like curl or Postman.
