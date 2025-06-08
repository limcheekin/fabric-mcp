"""Tests for fabric_run_pattern tool implementation.

This module tests the complete fabric_run_pattern tool functionality,
including error handling, SSE response parsing, and API integration.
"""

from collections.abc import Callable
from typing import Any
from unittest.mock import patch

import pytest
from mcp import McpError

from fabric_mcp.core import FabricMCP, PatternExecutionConfig
from tests.shared.fabric_api_mocks import (
    FabricApiMockBuilder,
    assert_mcp_error,
    mock_fabric_api_client,
)


class TestFabricRunPattern:
    """Test cases for fabric_run_pattern tool."""

    @pytest.fixture
    def server_instance(self) -> FabricMCP:
        """Create a FabricMCP server instance for testing."""
        return FabricMCP()

    @pytest.fixture
    def fabric_run_pattern_tool(self, server_instance: FabricMCP) -> Callable[..., Any]:
        """Get the fabric_run_pattern tool from the server."""
        tools = getattr(server_instance, "_FabricMCP__tools")
        # fabric_run_pattern is the 3rd tool (index 2)
        return tools[2]

    def test_successful_execution_with_basic_input(
        self, fabric_run_pattern_tool: Callable[..., Any]
    ) -> None:
        """Test successful pattern execution with basic input."""
        builder = FabricApiMockBuilder().with_successful_sse("Hello, World!")

        with mock_fabric_api_client(builder) as mock_api_client:
            result: dict[str, Any] = fabric_run_pattern_tool(
                "test_pattern", "test input"
            )

            assert isinstance(result, dict)
            assert "output_format" in result
            assert "output_text" in result
            assert result["output_text"] == "Hello, World!"
            assert result["output_format"] == "text"
            mock_api_client.close.assert_called_once()

    def test_successful_execution_with_markdown_format(
        self, fabric_run_pattern_tool: Callable[..., Any]
    ) -> None:
        """Test successful pattern execution with markdown output."""
        builder = FabricApiMockBuilder().with_successful_sse(
            "# Header\n\nContent", "markdown"
        )

        with mock_fabric_api_client(builder) as mock_api_client:
            result: dict[str, Any] = fabric_run_pattern_tool(
                "test_pattern", "test input"
            )

            assert result["output_text"] == "# Header\n\nContent"
            assert result["output_format"] == "markdown"
            mock_api_client.close.assert_called_once()

    def test_successful_execution_with_complex_sse_response(
        self, fabric_run_pattern_tool: Callable[..., Any]
    ) -> None:
        """Test pattern execution with complex SSE response containing
        multiple chunks."""
        sse_lines = [
            'data: {"type": "content", "content": "First chunk", "format": "text"}',
            'data: {"type": "content", "content": " Second chunk", "format": "text"}',
            'data: {"type": "content", "content": " Final chunk", "format": "text"}',
            'data: {"type": "complete"}',
        ]
        builder = FabricApiMockBuilder().with_sse_lines(sse_lines)

        with mock_fabric_api_client(builder) as mock_api_client:
            result: dict[str, Any] = fabric_run_pattern_tool(
                "test_pattern", "test input"
            )

            assert result["output_text"] == "First chunk Second chunk Final chunk"
            assert result["output_format"] == "text"
            mock_api_client.close.assert_called_once()

    def test_network_connection_error(
        self, fabric_run_pattern_tool: Callable[..., Any]
    ) -> None:
        """Test handling of network connection errors."""
        builder = FabricApiMockBuilder().with_connection_error("Connection failed")

        with mock_fabric_api_client(builder) as mock_api_client:
            with pytest.raises(McpError) as exc_info:
                fabric_run_pattern_tool("test_pattern", "test input")

            assert_mcp_error(exc_info, -32603, "Unexpected error executing pattern")
            mock_api_client.close.assert_called_once()

    def test_http_404_error(self, fabric_run_pattern_tool: Callable[..., Any]) -> None:
        """Test handling of HTTP 404 errors."""
        builder = FabricApiMockBuilder().with_http_error(404, "Pattern not found")

        with mock_fabric_api_client(builder) as mock_api_client:
            with pytest.raises(McpError) as exc_info:
                fabric_run_pattern_tool("nonexistent_pattern", "test input")

            assert_mcp_error(exc_info, -32603, "Fabric API returned error 404")
            mock_api_client.close.assert_called_once()

    def test_timeout_error(self, fabric_run_pattern_tool: Callable[..., Any]) -> None:
        """Test handling of timeout errors."""
        builder = FabricApiMockBuilder().with_timeout_error()

        with mock_fabric_api_client(builder) as mock_api_client:
            with pytest.raises(McpError) as exc_info:
                fabric_run_pattern_tool("test_pattern", "test input")

            assert_mcp_error(exc_info, -32603, "Request timed out")
            mock_api_client.close.assert_called_once()

    def test_sse_error_response(
        self, fabric_run_pattern_tool: Callable[..., Any]
    ) -> None:
        """Test handling of SSE error responses."""
        builder = FabricApiMockBuilder().with_sse_error("Pattern execution failed")

        with mock_fabric_api_client(builder) as mock_api_client:
            with pytest.raises(McpError) as exc_info:
                fabric_run_pattern_tool("test_pattern", "test input")

            assert_mcp_error(exc_info, -32603, "Pattern execution failed")
            mock_api_client.close.assert_called_once()

    def test_malformed_sse_data(
        self, fabric_run_pattern_tool: Callable[..., Any]
    ) -> None:
        """Test handling of malformed SSE data."""
        builder = FabricApiMockBuilder().with_partial_sse_data()

        with mock_fabric_api_client(builder) as mock_api_client:
            with pytest.raises(McpError) as exc_info:
                fabric_run_pattern_tool("test_pattern", "test input")

            assert_mcp_error(exc_info, -32603, "Malformed SSE data")
            mock_api_client.close.assert_called_once()

    def test_empty_input_handling(
        self, fabric_run_pattern_tool: Callable[..., Any]
    ) -> None:
        """Test pattern execution with empty input."""
        builder = FabricApiMockBuilder().with_successful_sse("No input provided")

        with mock_fabric_api_client(builder) as mock_api_client:
            result: dict[str, Any] = fabric_run_pattern_tool("test_pattern", "")

            assert result["output_text"] == "No input provided"
            mock_api_client.close.assert_called_once()

    def test_large_input_handling(
        self, fabric_run_pattern_tool: Callable[..., Any]
    ) -> None:
        """Test pattern execution with large input."""
        large_input = "x" * 10000
        builder = FabricApiMockBuilder().with_successful_sse("Output")

        with mock_fabric_api_client(builder) as mock_api_client:
            result: dict[str, Any] = fabric_run_pattern_tool(
                "test_pattern", large_input
            )

            assert result["output_text"] == "Output"
            mock_api_client.close.assert_called_once()

    def test_special_characters_in_pattern_name(
        self, fabric_run_pattern_tool: Callable[..., Any]
    ) -> None:
        """Test pattern execution with special characters in pattern name."""
        builder = FabricApiMockBuilder().with_successful_sse("Output")

        with mock_fabric_api_client(builder) as mock_api_client:
            result: dict[str, Any] = fabric_run_pattern_tool(
                "pattern-with_special.chars", "test input"
            )

            assert result["output_text"] == "Output"
            mock_api_client.close.assert_called_once()

    def test_empty_sse_stream(
        self, fabric_run_pattern_tool: Callable[..., Any]
    ) -> None:
        """Test handling of empty SSE stream."""
        builder = FabricApiMockBuilder().with_empty_sse_stream()

        with mock_fabric_api_client(builder) as mock_api_client:
            with pytest.raises(McpError) as exc_info:
                fabric_run_pattern_tool("test_pattern", "test input")

            assert_mcp_error(exc_info, -32603, "Empty SSE stream")
            mock_api_client.close.assert_called_once()

    def test_sse_stream_with_non_data_lines(
        self, fabric_run_pattern_tool: Callable[..., Any]
    ) -> None:
        """Test SSE stream processing with non-data lines (should be ignored)."""
        sse_lines = [
            ": This is a comment line",
            'data: {"type": "content", "content": "Hello", "format": "text"}',
            "event: test-event",
            'data: {"type": "complete"}',
            "",  # Empty line
        ]
        builder = FabricApiMockBuilder().with_sse_lines(sse_lines)

        with mock_fabric_api_client(builder) as mock_api_client:
            result: dict[str, Any] = fabric_run_pattern_tool(
                "test_pattern", "test input"
            )

            assert result["output_text"] == "Hello"
            assert result["output_format"] == "text"
            mock_api_client.close.assert_called_once()


class TestFabricRunPatternWithDefaultModels:
    """Test cases for fabric_run_pattern tool with default model configuration."""

    @pytest.fixture
    def fabric_run_pattern_tool_with_defaults(self) -> Callable[..., Any]:
        """Get fabric_run_pattern tool from server with default config."""
        with patch("fabric_mcp.core.get_default_model") as mock_get_default:
            mock_get_default.return_value = ("claude-3-sonnet", "anthropic")

            server = FabricMCP()
            tools = getattr(server, "_FabricMCP__tools")
            return tools[2]  # fabric_run_pattern is the 3rd tool

    @pytest.fixture
    def fabric_run_pattern_tool_no_defaults(self) -> Callable[..., Any]:
        """Get fabric_run_pattern tool from server with no default config."""
        with patch("fabric_mcp.core.get_default_model") as mock_get_default:
            mock_get_default.return_value = (None, None)

            server = FabricMCP()
            tools = getattr(server, "_FabricMCP__tools")
            return tools[2]  # fabric_run_pattern is the 3rd tool

    def test_default_model_applied_when_no_explicit_config(
        self, fabric_run_pattern_tool_with_defaults: Callable[..., Any]
    ) -> None:
        """Test that default model from environment is applied when no
        config specified."""
        builder = FabricApiMockBuilder().with_successful_sse("Test output")

        with mock_fabric_api_client(builder) as mock_api_client:
            result: dict[str, Any] = fabric_run_pattern_tool_with_defaults(
                "test_pattern", "test input"
            )

            # Verify the result
            assert result["output_text"] == "Test output"

            # Verify the API was called with default model/vendor
            mock_api_client.post.assert_called_once()
            call_args = mock_api_client.post.call_args
            request_payload = call_args[1]["json_data"]

            assert request_payload["prompts"][0]["model"] == "claude-3-sonnet"
            assert request_payload["prompts"][0]["vendor"] == "anthropic"

    def test_explicit_model_overrides_default(
        self, fabric_run_pattern_tool_with_defaults: Callable[..., Any]
    ) -> None:
        """Test that explicit model config overrides default from environment."""

        builder = FabricApiMockBuilder().with_successful_sse("Test output")
        explicit_config = PatternExecutionConfig(model_name="gpt-4o")

        with mock_fabric_api_client(builder) as mock_api_client:
            result: dict[str, Any] = fabric_run_pattern_tool_with_defaults(
                "test_pattern", "test input", config=explicit_config
            )

            # Verify the result
            assert result["output_text"] == "Test output"

            # Verify the API was called with explicit model, but default vendor
            mock_api_client.post.assert_called_once()
            call_args = mock_api_client.post.call_args
            request_payload = call_args[1]["json_data"]

            assert request_payload["prompts"][0]["model"] == "gpt-4o"
            assert (
                request_payload["prompts"][0]["vendor"] == "anthropic"
            )  # Still uses default

    def test_fallback_behavior_without_defaults(
        self, fabric_run_pattern_tool_no_defaults: Callable[..., Any]
    ) -> None:
        """Test fallback to hardcoded defaults when no environment config."""
        builder = FabricApiMockBuilder().with_successful_sse("Test output")

        with mock_fabric_api_client(builder) as mock_api_client:
            result: dict[str, Any] = fabric_run_pattern_tool_no_defaults(
                "test_pattern", "test input"
            )

            # Verify the result
            assert result["output_text"] == "Test output"

            # Verify the API was called with hardcoded defaults
            mock_api_client.post.assert_called_once()
            call_args = mock_api_client.post.call_args
            request_payload = call_args[1]["json_data"]

            assert request_payload["prompts"][0]["model"] == "gpt-4o"
            assert request_payload["prompts"][0]["vendor"] == "openai"
