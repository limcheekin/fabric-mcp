"""Unified integration tests for all MCP transport types.

This module tests HTTP Streamable, SSE, and other transport functionality
in a DRY manner, avoiding code duplication across transport types.
"""

import asyncio
import json
import subprocess
import sys
from typing import Any

import httpx
import pytest
from fastmcp import Client
from fastmcp.client.transports import StreamableHttpTransport
from fastmcp.exceptions import ToolError

from tests.shared.fabric_api.server import MOCK_PATTERNS
from tests.shared.fabric_api.utils import (
    MockFabricAPIServer,
    fabric_api_server_fixture,
)
from tests.shared.port_utils import find_free_port
from tests.shared.transport_test_utils import (
    ServerConfig,
    get_expected_tools,
    run_server,
)

_ = fabric_api_server_fixture  # eliminate unused variable warning

INVALID_PORT = 9999  # Port used for testing invalid configurations


class TransportTestBase:
    """Base class for transport-specific test configurations."""

    @pytest.fixture(scope="class")
    def server_config(self) -> ServerConfig:
        """Override in subclasses to provide transport-specific config."""
        raise NotImplementedError

    @property
    def transport_type(self) -> str:
        """Override in subclasses to specify transport type."""
        raise NotImplementedError

    def create_client(self, url: str) -> Client[Any]:
        """Override in subclasses to create transport-specific client."""
        raise NotImplementedError

    def get_server_url(self, config: ServerConfig) -> str:
        """Override in subclasses to build transport-specific URL."""
        raise NotImplementedError

    @pytest.mark.asyncio
    async def test_server_starts_and_responds(
        self, server_config: ServerConfig
    ) -> None:
        """Test that server starts and responds to basic requests."""
        async with run_server(server_config, self.transport_type) as config:
            url = self.get_server_url(config)

            async with httpx.AsyncClient() as http_client:
                # HTTP endpoints return normal responses
                response = await http_client.get(url)
                if self.transport_type == "http":
                    # Expect 307 redirect or 406 without proper headers
                    assert response.status_code in [307, 406]
                    if response.status_code == 406:
                        assert (
                            "text/event-stream" in response.json()["error"]["message"]
                        )

    @pytest.mark.asyncio
    async def test_mcp_client_connection(self, server_config: ServerConfig) -> None:
        """Test MCP client can connect and list tools."""
        async with run_server(server_config, self.transport_type) as config:
            url = self.get_server_url(config)
            client = self.create_client(url)

            async with client:
                tools = await client.list_tools()
                assert tools is not None
                assert isinstance(tools, list)

                # Verify expected tools are present
                tool_names: list[str] = [tool.name for tool in tools]
                expected_tools = get_expected_tools()

                for expected_tool in expected_tools:
                    assert expected_tool in tool_names

    @pytest.mark.asyncio
    async def test_fabric_list_patterns_tool_fail(
        self, server_config: ServerConfig, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test fabric_list_patterns tool.

        Expects connection error when Fabric API unavailable.
        """
        # Override environment to point to non-existent Fabric API
        monkeypatch.setenv("FABRIC_BASE_URL", f"http://localhost:{INVALID_PORT}")
        monkeypatch.setenv("FABRIC_API_KEY", "test")

        async with run_server(server_config, self.transport_type) as config:
            url = self.get_server_url(config)
            client = self.create_client(url)

            async with client:
                # Since we don't have a real Fabric API running, we expect a ToolError
                with pytest.raises(ToolError) as exc_info:
                    await client.call_tool("fabric_list_patterns")

                # Verify it's the expected connection error
                error_msg = str(exc_info.value)
                assert (
                    "Failed to connect to Fabric API" in error_msg
                    or "Connection refused" in error_msg
                )

    @pytest.mark.asyncio
    async def test_fabric_get_pattern_details_tool(
        self, server_config: ServerConfig, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test fabric_get_pattern_details tool.

        Expects connection error when Fabric API unavailable.
        """
        # Override environment to point to non-existent Fabric API
        monkeypatch.setenv("FABRIC_BASE_URL", "http://localhost:99999")
        monkeypatch.setenv("FABRIC_API_KEY", "test")

        async with run_server(server_config, self.transport_type) as config:
            url = self.get_server_url(config)
            client = self.create_client(url)

            async with client:
                # Since we don't have a real Fabric API running, we expect a ToolError
                with pytest.raises(ToolError) as exc_info:
                    await client.call_tool(
                        "fabric_get_pattern_details", {"pattern_name": "test_pattern"}
                    )

                # Verify it's the expected connection error
                error_msg = str(exc_info.value)
                assert "Failed to connect to Fabric API" in error_msg

    @pytest.mark.asyncio
    async def test_fabric_run_pattern_tool(
        self, server_config: ServerConfig, mock_fabric_api_server: MockFabricAPIServer
    ) -> None:
        """Test fabric_run_pattern tool (non-streaming)."""
        _ = mock_fabric_api_server  # eliminate unused variable warning
        async with run_server(server_config, self.transport_type) as config:
            url = self.get_server_url(config)
            client = self.create_client(url)

            async with client:
                result = await client.call_tool(
                    "fabric_run_pattern",
                    {
                        "pattern_name": "test_pattern",
                        "input_text": "test input",
                        "stream": False,
                    },
                )
                assert result is not None
                assert isinstance(result, list)

                output_text = result[0].text  # type: ignore[misc]
                assert isinstance(output_text, str)
                assert len(output_text) > 0

    @pytest.mark.asyncio
    async def test_fabric_run_pattern_streaming_tool(
        self, server_config: ServerConfig, mock_fabric_api_server: MockFabricAPIServer
    ) -> None:
        """Test fabric_run_pattern tool with streaming."""
        _ = mock_fabric_api_server  # eliminate unused variable warning
        async with run_server(server_config, self.transport_type) as config:
            url = self.get_server_url(config)
            client = self.create_client(url)

            async with client:
                result = await client.call_tool(
                    "fabric_run_pattern",
                    {
                        "pattern_name": "test_pattern",
                        "input_text": "test input",
                        "stream": True,
                    },
                )
                assert result is not None
                assert isinstance(result, list)

                output_text = result[0].text  # type: ignore[misc]
                assert isinstance(output_text, str)
                assert len(output_text) > 0

    @pytest.mark.asyncio
    async def test_fabric_list_models_tool(self, server_config: ServerConfig) -> None:
        """Test fabric_list_models tool."""
        async with run_server(server_config, self.transport_type) as config:
            url = self.get_server_url(config)
            client = self.create_client(url)

            async with client:
                result = await client.call_tool("fabric_list_models")
                assert result is not None
                assert isinstance(result, list)

                models_text = result[0].text  # type: ignore[misc]
                assert isinstance(models_text, str)
                assert len(models_text) > 0

    @pytest.mark.asyncio
    async def test_fabric_list_strategies_tool(
        self, server_config: ServerConfig
    ) -> None:
        """Test fabric_list_strategies tool."""
        async with run_server(server_config, self.transport_type) as config:
            url = self.get_server_url(config)
            client = self.create_client(url)

            async with client:
                result = await client.call_tool("fabric_list_strategies")
                assert result is not None
                assert isinstance(result, list)

                strategies_text = result[0].text  # type: ignore[misc]
                assert isinstance(strategies_text, str)
                assert len(strategies_text) > 0

    @pytest.mark.asyncio
    async def test_fabric_get_configuration_tool(
        self, server_config: ServerConfig
    ) -> None:
        """Test fabric_get_configuration tool."""
        async with run_server(server_config, self.transport_type) as config:
            url = self.get_server_url(config)
            client = self.create_client(url)

            async with client:
                result = await client.call_tool("fabric_get_configuration")
                assert result is not None
                assert isinstance(result, list)

                config_text = result[0].text  # type: ignore[misc]
                assert isinstance(config_text, str)
                # Should have redacted sensitive values
                assert "[REDACTED_BY_MCP_SERVER]" in config_text

    @pytest.mark.asyncio
    async def test_mcp_error_handling(self, server_config: ServerConfig) -> None:
        """Test MCP error handling."""
        async with run_server(server_config, self.transport_type) as config:
            url = self.get_server_url(config)
            client = self.create_client(url)

            async with client:
                # Test calling non-existent tool
                with pytest.raises(Exception):  # Should raise MCP error
                    await client.call_tool("non_existent_tool")

    @pytest.mark.asyncio
    async def test_concurrent_requests(
        self, server_config: ServerConfig, mock_fabric_api_server: MockFabricAPIServer
    ) -> None:
        """Test handling multiple concurrent requests."""
        _ = mock_fabric_api_server  # eliminate unused variable warning
        async with run_server(server_config, self.transport_type) as config:
            url = self.get_server_url(config)
            client = self.create_client(url)

            async with client:
                # Make multiple concurrent requests
                tasks: list[Any] = []
                for _ in range(5):
                    task = asyncio.create_task(client.call_tool("fabric_list_patterns"))
                    tasks.append(task)

                results: list[list[Any]] = await asyncio.gather(*tasks)

                # All requests should succeed
                for result in results:
                    assert result is not None
                    assert isinstance(result, list)
                    assert len(result) > 0

    @pytest.mark.asyncio
    async def test_fabric_list_patterns_tool_success(
        self, server_config: ServerConfig, mock_fabric_api_server: MockFabricAPIServer
    ) -> None:
        """Test fabric_list_patterns tool success path.

        Uses mock Fabric API server to test successful pattern retrieval.
        """
        _ = mock_fabric_api_server  # eliminate unused variable warning

        # Environment is automatically configured by fixture
        async with run_server(server_config, self.transport_type) as config:
            url = self.get_server_url(config)
            client = self.create_client(url)

            async with client:
                # Call the tool and expect success
                result = await client.call_tool("fabric_list_patterns")

                # Verify response structure
                assert result is not None
                assert isinstance(result, list)
                assert len(result) == 1

                # Extract the JSON text and parse it
                patterns_text = result[0].text  # type: ignore[misc]
                assert isinstance(patterns_text, str)

                patterns: list[str] = json.loads(patterns_text)
                assert isinstance(patterns, list)
                assert len(patterns) > 0

                # Expected patterns from mock server
                expected_patterns = MOCK_PATTERNS

                # Verify all expected patterns are present
                assert patterns == expected_patterns


@pytest.mark.integration
class TestHTTPStreamableTransport(TransportTestBase):
    """Integration tests for HTTP Streamable Transport."""

    @pytest.fixture
    def server_config(self) -> ServerConfig:
        """Configuration for the HTTP server."""
        return {
            "host": "127.0.0.1",
            "port": find_free_port(),
            "mcp_path": "/message",
        }

    @property
    def transport_type(self) -> str:
        """HTTP streamable transport type."""
        return "http"

    def create_client(self, url: str) -> Client[Any]:
        """Create HTTP streamable transport client."""
        transport = StreamableHttpTransport(url=url)
        return Client(transport)

    def get_server_url(self, config: ServerConfig) -> str:
        """Build HTTP server URL."""
        return f"http://{config['host']}:{config['port']}{config['mcp_path']}"

    @pytest.mark.asyncio
    async def test_custom_host_port_path_configuration(self) -> None:
        """Test server with custom host, port, and path configuration."""
        custom_config: ServerConfig = {
            "host": "127.0.0.1",
            "port": find_free_port(),
            "mcp_path": "/custom-path",
        }

        async with run_server(custom_config, "http") as config:
            url = self.get_server_url(config)
            client = self.create_client(url)

            async with client:
                tools = await client.list_tools()
                assert tools is not None
                assert isinstance(tools, list)


@pytest.mark.integration
class TestTransportCLI:
    """Integration tests for CLI with different transports."""

    def test_cli_transport_help(self) -> None:
        """Test CLI shows transport options in help."""
        result = subprocess.run(
            [sys.executable, "-m", "fabric_mcp.cli", "--help"],
            capture_output=True,
            text=True,
            check=False,
        )

        assert result.returncode == 0
        assert "--transport" in result.stdout
        assert "[stdio|http]" in result.stdout
        assert "--host" in result.stdout
        assert "--port" in result.stdout
        assert "--mcp-path" in result.stdout

    def test_cli_validates_http_options_with_stdio(self) -> None:
        """Test CLI rejects HTTP options when using stdio transport."""
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "fabric_mcp.cli",
                "--transport",
                "stdio",
                "--host",
                "custom-host",
            ],
            capture_output=True,
            text=True,
            check=False,
        )

        assert result.returncode == 2
        assert "only valid with --transport http" in result.stderr
