"""Tests for fabric_run_pattern tool error handling.

This module tests error handling scenarios for the fabric_run_pattern tool,
including network errors, HTTP errors, SSE errors, and malformed data handling.
"""

from collections.abc import Callable
from typing import Any

import pytest
from mcp import McpError
from mcp.types import INTERNAL_ERROR

from fabric_mcp.core import FabricMCP
from tests.shared.fabric_api.utils import fabric_api_server_fixture
from tests.shared.fabric_api_mocks import (
    FabricApiMockBuilder,
    assert_mcp_error,
    mock_fabric_api_client,
)
from tests.unit.test_fabric_run_pattern_base import TestFabricRunPatternFixtureBase

_ = fabric_api_server_fixture  # to get rid of unused variable warning


class TestFabricRunPatternErrorHandling(TestFabricRunPatternFixtureBase):
    """Test cases for fabric_run_pattern tool error handling."""

    def test_network_connection_error(
        self, server: FabricMCP, fabric_run_pattern_tool: Callable[..., Any]
    ) -> None:
        """Test handling of network connection errors."""
        _ = server  # to avoid unused variable warning
        builder = FabricApiMockBuilder().with_connection_error("Connection failed")

        with mock_fabric_api_client(builder) as mock_api_client:
            with pytest.raises(McpError) as exc_info:
                fabric_run_pattern_tool("test_pattern", "test input")

            # Connection errors should be wrapped in McpError by the tool wrapper
            assert_mcp_error(exc_info, INTERNAL_ERROR, "Error executing pattern")
            mock_api_client.close.assert_called_once()

    def test_http_404_error(self, fabric_run_pattern_tool: Callable[..., Any]) -> None:
        """Test handling of HTTP 404 errors."""
        builder = FabricApiMockBuilder().with_http_error(404, "Pattern not found")

        with mock_fabric_api_client(builder) as mock_api_client:
            with pytest.raises(McpError) as exc_info:
                fabric_run_pattern_tool("nonexistent_pattern", "test input")

            assert_mcp_error(exc_info, INTERNAL_ERROR, "Fabric API returned error 404")
            mock_api_client.close.assert_called_once()

    def test_timeout_error(self, fabric_run_pattern_tool: Callable[..., Any]) -> None:
        """Test handling of timeout errors."""
        builder = FabricApiMockBuilder().with_timeout_error()

        with mock_fabric_api_client(builder) as mock_api_client:
            with pytest.raises(McpError) as exc_info:
                fabric_run_pattern_tool("test_pattern", "test input")

            assert_mcp_error(exc_info, INTERNAL_ERROR, "Request timed out")
            mock_api_client.close.assert_called_once()

    def test_sse_error_response(
        self, fabric_run_pattern_tool: Callable[..., Any]
    ) -> None:
        """Test handling of SSE error responses."""
        builder = FabricApiMockBuilder().with_sse_error("Pattern execution failed")

        with mock_fabric_api_client(builder) as mock_api_client:
            with pytest.raises(McpError) as exc_info:
                fabric_run_pattern_tool("test_pattern", "test input")

            assert_mcp_error(exc_info, INTERNAL_ERROR, "Pattern execution failed")
            mock_api_client.close.assert_called_once()

    def test_malformed_sse_data(
        self, fabric_run_pattern_tool: Callable[..., Any]
    ) -> None:
        """Test handling of malformed SSE data."""
        builder = FabricApiMockBuilder().with_partial_sse_data()

        with mock_fabric_api_client(builder) as mock_api_client:
            with pytest.raises(McpError) as exc_info:
                fabric_run_pattern_tool("test_pattern", "test input")

            assert_mcp_error(exc_info, INTERNAL_ERROR, "Malformed SSE data")
            mock_api_client.close.assert_called_once()

    def test_empty_sse_stream(
        self, fabric_run_pattern_tool: Callable[..., Any]
    ) -> None:
        """Test handling of empty SSE stream."""
        builder = FabricApiMockBuilder().with_empty_sse_stream()

        with mock_fabric_api_client(builder) as mock_api_client:
            with pytest.raises(McpError) as exc_info:
                fabric_run_pattern_tool("test_pattern", "test input")

            assert_mcp_error(exc_info, INTERNAL_ERROR, "Empty SSE stream")
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
