"""Tests for fabric_run_pattern tool implementation.

This module tests the complete fabric_run_pattern tool functionality,
including error handling, SSE response parsing, and API integration.
"""

from collections.abc import Callable
from typing import Any
from unittest.mock import patch

import pytest
import pytest_asyncio
from fastmcp.tools import Tool
from mcp import McpError

from fabric_mcp.core import (
    DEFAULT_MODEL,
    DEFAULT_VENDOR,
    FabricMCP,
    PatternExecutionConfig,
)
from tests.shared.fabric_api.base import TestFixturesBase
from tests.shared.fabric_api_mocks import (
    FabricApiMockBuilder,
    assert_mcp_error,
    mock_fabric_api_client,
)


class TestFabricRunPatternFixtureBase(TestFixturesBase):
    """Test cases for fabric_run_pattern tool SSE response handling."""

    @pytest_asyncio.fixture
    async def fabric_run_pattern_tool(
        self, mcp_tools: dict[str, Tool]
    ) -> Callable[..., Any]:
        """Get the fabric_run_pattern tool from the server."""
        # fabric_run_pattern is the 3rd tool (index 2)
        return getattr(mcp_tools["fabric_run_pattern"], "fn")


class TestFabricRunPatternBasicExecution(TestFabricRunPatternFixtureBase):
    """Test cases for basic fabric_run_pattern tool execution scenarios."""

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


class TestFabricRunPatternErrorHandling(TestFabricRunPatternFixtureBase):
    """Test cases for fabric_run_pattern tool error handling."""

    def test_network_connection_error(
        self, fabric_run_pattern_tool: Callable[..., Any]
    ) -> None:
        """Test handling of network connection errors."""
        builder = FabricApiMockBuilder().with_connection_error("Connection failed")

        with mock_fabric_api_client(builder) as mock_api_client:
            with pytest.raises(McpError) as exc_info:
                fabric_run_pattern_tool("test_pattern", "test input")

            # Connection errors should be wrapped in McpError by the tool wrapper
            assert_mcp_error(exc_info, -32603, "Error executing pattern")
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


class TestFabricRunPatternInputValidation(TestFabricRunPatternFixtureBase):
    """Test cases for fabric_run_pattern tool input validation and edge cases."""

    def test_empty_pattern_name_validation(
        self, fabric_run_pattern_tool: Callable[..., Any]
    ) -> None:
        """Test that empty pattern name raises ValueError."""
        # Test empty string
        with pytest.raises(
            ValueError, match="pattern_name is required and cannot be empty"
        ):
            fabric_run_pattern_tool("", "test input")

        # Test whitespace-only string
        with pytest.raises(
            ValueError, match="pattern_name is required and cannot be empty"
        ):
            fabric_run_pattern_tool("   ", "test input")

        # Test None (though this might be caught by type system)
        with pytest.raises(
            ValueError, match="pattern_name is required and cannot be empty"
        ):
            fabric_run_pattern_tool(None, "test input")

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


class TestFabricRunPatternModelInference(TestFabricRunPatternFixtureBase):
    """Test cases for fabric_run_pattern tool model and vendor inference."""

    @pytest.fixture
    def server_no_defaults(self) -> FabricMCP:
        """Create a FabricMCP server instance with no default model/vendor."""
        with patch("fabric_mcp.core.get_default_model", return_value=(None, None)):
            return FabricMCP()

    @pytest.fixture
    def server_claude_model(self) -> FabricMCP:
        """Create a FabricMCP server instance with Claude model default."""
        with patch(
            "fabric_mcp.core.get_default_model",
            return_value=("claude-3-opus", None),
        ):
            return FabricMCP()

    @pytest.fixture
    def server_gpt_model(self) -> FabricMCP:
        """Create a FabricMCP server instance with GPT model default."""
        with patch(
            "fabric_mcp.core.get_default_model",
            return_value=("gpt-3.5-turbo", None),
        ):
            return FabricMCP()

    @pytest_asyncio.fixture
    async def fabric_run_pattern_tool_no_defaults(
        self, server_no_defaults: FabricMCP
    ) -> Callable[..., Any]:
        """Get the fabric_run_pattern tool from server with no defaults."""
        tools = await server_no_defaults.get_tools()
        return getattr(tools["fabric_run_pattern"], "fn")

    @pytest_asyncio.fixture
    async def fabric_run_pattern_tool_claude(
        self, server_claude_model: FabricMCP
    ) -> Callable[..., Any]:
        """Get the fabric_run_pattern tool from server with Claude model."""
        tools = await server_claude_model.get_tools()
        return getattr(tools["fabric_run_pattern"], "fn")

    @pytest_asyncio.fixture
    async def fabric_run_pattern_tool_gpt(
        self, server_gpt_model: FabricMCP
    ) -> Callable[..., Any]:
        """Get the fabric_run_pattern tool from server with GPT model."""
        tools = await server_gpt_model.get_tools()
        return getattr(tools["fabric_run_pattern"], "fn")

    def test_pattern_not_found_500_error(
        self, fabric_run_pattern_tool: Callable[..., Any]
    ) -> None:
        """Test handling of 500 error indicating pattern not found."""
        builder = FabricApiMockBuilder().with_http_error(
            500, "no such file or directory: pattern not found"
        )

        with mock_fabric_api_client(builder) as mock_api_client:
            with pytest.raises(McpError) as exc_info:
                fabric_run_pattern_tool("nonexistent_pattern", "test input")
                mock_api_client.close.assert_called_once()

            # Should be transformed to Invalid params error
            assert exc_info.value.error.code == -32602
            assert (
                "Pattern 'nonexistent_pattern' not found"
                in exc_info.value.error.message
            )

    def test_generic_500_error(
        self, fabric_run_pattern_tool: Callable[..., Any]
    ) -> None:
        """Test handling of generic 500 error (not pattern not found)."""
        builder = FabricApiMockBuilder().with_http_error(
            500, "Database connection failed"
        )

        with mock_fabric_api_client(builder) as client:
            with pytest.raises(McpError) as exc_info:
                fabric_run_pattern_tool("test_pattern", "test input")

            error = exc_info.value
            assert error.error.code == -32603  # Internal error
            assert "Database connection failed" in error.error.message
            client.close.assert_called_once()

    def test_vendor_inference_from_model_name(
        self, fabric_run_pattern_tool: Callable[..., Any]
    ) -> None:
        """Test vendor inference when no default vendor is configured."""
        builder = FabricApiMockBuilder().with_successful_sse("Inference test")

        # Test Claude model inference
        with patch("fabric_mcp.core.get_default_model", return_value=(None, None)):
            with mock_fabric_api_client(builder):
                config = PatternExecutionConfig(model_name="claude-3-sonnet")
                result = fabric_run_pattern_tool(
                    "test_pattern", "test input", config=config
                )
                assert result["output_text"] == "Inference test"

        # Test GPT model inference
        with patch("fabric_mcp.core.get_default_model", return_value=(None, None)):
            with mock_fabric_api_client(builder):
                config = PatternExecutionConfig(model_name="gpt-4")
                result = fabric_run_pattern_tool(
                    "test_pattern", "test input", config=config
                )
                assert result["output_text"] == "Inference test"

    def test_hardcoded_model_fallback_when_no_defaults(
        self, fabric_run_pattern_tool_no_defaults: Callable[..., Any]
    ) -> None:
        """Test fallback to hardcoded default model when no environment defaults."""
        builder = FabricApiMockBuilder().with_successful_sse("Hello, World!")

        # Mock get_default_model to return None for both model and vendor
        with mock_fabric_api_client(builder) as mock_api_client:
            result: dict[str, Any] = fabric_run_pattern_tool_no_defaults(
                "test_pattern", "test input"
            )

            assert isinstance(result, dict)
            # Check that API was called (would use hardcoded defaults)
            mock_api_client.post.assert_called_once()
            call_args = mock_api_client.post.call_args
            payload = call_args[1]["json_data"]
            assert payload["prompts"][0]["model"] == DEFAULT_MODEL
            assert payload["prompts"][0]["vendor"] == DEFAULT_VENDOR

    def test_vendor_inference_for_claude_models(
        self, fabric_run_pattern_tool_claude: Callable[..., Any]
    ) -> None:
        """Test vendor inference from Claude model names."""
        builder = FabricApiMockBuilder().with_successful_sse("Hello, World!")

        with mock_fabric_api_client(builder) as mock_api_client:
            result: dict[str, Any] = fabric_run_pattern_tool_claude(
                "test_pattern", "test input"
            )

            assert isinstance(result, dict)
            # Check that vendor was inferred as "anthropic" for Claude models
            mock_api_client.post.assert_called_once()
            call_args = mock_api_client.post.call_args
            payload = call_args[1]["json_data"]
            assert payload["prompts"][0]["model"] == "claude-3-opus"
            assert payload["prompts"][0]["vendor"] == DEFAULT_VENDOR

    def test_vendor_inference_for_gpt_models(
        self, fabric_run_pattern_tool_gpt: Callable[..., Any]
    ) -> None:
        """Test vendor inference from GPT model names."""
        builder = FabricApiMockBuilder().with_successful_sse("Hello, World!")

        with mock_fabric_api_client(builder) as mock_api_client:
            result: dict[str, Any] = fabric_run_pattern_tool_gpt(
                "test_pattern", "test input"
            )

            assert isinstance(result, dict)
            # Check that vendor was inferred as "openai" for GPT models
            mock_api_client.post.assert_called_once()
            call_args = mock_api_client.post.call_args
            payload = call_args[1]["json_data"]
            assert payload["prompts"][0]["model"] == "gpt-3.5-turbo"
            assert payload["prompts"][0]["vendor"] == DEFAULT_VENDOR
