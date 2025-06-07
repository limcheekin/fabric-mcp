"""Tests for fabric_run_pattern tool implementation.

This module tests the complete fabric_run_pattern tool functionality,
including error handling, SSE response parsing, and API integration.
"""

from collections.abc import Callable
from typing import Any
from unittest.mock import Mock, patch

import httpx
import pytest

from fabric_mcp.core import FabricMCP


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
        with patch("fabric_mcp.core.FabricApiClient") as mock_api_client_class:
            mock_api_client = Mock()
            mock_api_client_class.return_value = mock_api_client

            # Mock successful SSE response
            mock_response = Mock()
            mock_response.iter_lines.return_value = [
                'data: {"type": "content", "content": "Hello, ", "format": "text"}',
                'data: {"type": "content", "content": "World!", "format": "text"}',
                'data: {"type": "complete"}',
            ]
            mock_api_client.post.return_value = mock_response

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
        """Test successful pattern execution with markdown format."""
        with patch("fabric_mcp.core.FabricApiClient") as mock_api_client_class:
            mock_api_client = Mock()
            mock_api_client_class.return_value = mock_api_client

            # Mock SSE response with markdown format
            mock_response = Mock()
            mock_response.iter_lines.return_value = [
                'data: {"type": "content", "content": "# Header\\n", '
                '"format": "markdown"}',
                'data: {"type": "content", "content": "Some content", '
                '"format": "markdown"}',
                'data: {"type": "complete"}',
            ]
            mock_api_client.post.return_value = mock_response

            result: dict[str, Any] = fabric_run_pattern_tool(
                "analyze_claims", "test input"
            )

            assert result["output_text"] == "# Header\nSome content"
            assert result["output_format"] == "markdown"

    def test_empty_pattern_name_validation(
        self, fabric_run_pattern_tool: Callable[..., Any]
    ) -> None:
        """Test that empty pattern_name raises ValueError."""
        with pytest.raises(
            ValueError, match="pattern_name is required and cannot be empty"
        ):
            fabric_run_pattern_tool("", "test input")

    def test_whitespace_only_pattern_name_validation(
        self, fabric_run_pattern_tool: Callable[..., Any]
    ) -> None:
        """Test that whitespace-only pattern_name raises ValueError."""
        with pytest.raises(
            ValueError, match="pattern_name is required and cannot be empty"
        ):
            fabric_run_pattern_tool("   ", "test input")

    def test_none_pattern_name_validation(
        self, fabric_run_pattern_tool: Callable[..., Any]
    ) -> None:
        """Test that None pattern_name raises ValueError."""
        with pytest.raises(
            ValueError, match="pattern_name is required and cannot be empty"
        ):
            fabric_run_pattern_tool(None, "test input")

    def test_connection_error_handling(
        self, fabric_run_pattern_tool: Callable[..., Any]
    ) -> None:
        """Test handling of connection errors to Fabric API."""
        with patch("fabric_mcp.core.FabricApiClient") as mock_api_client_class:
            mock_api_client = Mock()
            mock_api_client_class.return_value = mock_api_client

            # Mock connection error
            mock_api_client.post.side_effect = httpx.ConnectError("Connection failed")

            with pytest.raises(
                ConnectionError, match="Unable to connect to Fabric API"
            ):
                fabric_run_pattern_tool("test_pattern", "test input")

            mock_api_client.close.assert_called_once()

    def test_http_status_error_handling(
        self, fabric_run_pattern_tool: Callable[..., Any]
    ) -> None:
        """Test handling of HTTP status errors from Fabric API."""
        with patch("fabric_mcp.core.FabricApiClient") as mock_api_client_class:
            mock_api_client = Mock()
            mock_api_client_class.return_value = mock_api_client

            # Mock HTTP status error
            mock_response = Mock()
            mock_response.status_code = 404
            mock_response.text = "Pattern not found"
            mock_api_client.post.side_effect = httpx.HTTPStatusError(
                "404 Not Found", request=Mock(), response=mock_response
            )

            with pytest.raises(
                RuntimeError, match="Fabric API returned error 404: Pattern not found"
            ):
                fabric_run_pattern_tool("nonexistent_pattern", "test input")

            mock_api_client.close.assert_called_once()

    def test_unexpected_exception_handling(
        self, fabric_run_pattern_tool: Callable[..., Any]
    ) -> None:
        """Test handling of unexpected exceptions during execution."""
        with patch("fabric_mcp.core.FabricApiClient") as mock_api_client_class:
            mock_api_client = Mock()
            mock_api_client_class.return_value = mock_api_client

            # Mock unexpected exception
            mock_api_client.post.side_effect = Exception("Unexpected error")

            with pytest.raises(
                RuntimeError, match="Unexpected error executing pattern"
            ):
                fabric_run_pattern_tool("test_pattern", "test input")

            mock_api_client.close.assert_called_once()

    def test_sse_error_response_handling(
        self, fabric_run_pattern_tool: Callable[..., Any]
    ) -> None:
        """Test handling of error responses in SSE stream."""
        with patch("fabric_mcp.core.FabricApiClient") as mock_api_client_class:
            mock_api_client = Mock()
            mock_api_client_class.return_value = mock_api_client

            # Mock SSE response with error
            mock_response = Mock()
            mock_response.iter_lines.return_value = [
                'data: {"type": "content", "content": "Starting...", "format": "text"}',
                'data: {"type": "error", "content": "Pattern execution failed"}',
            ]
            mock_api_client.post.return_value = mock_response

            with pytest.raises(
                RuntimeError, match="Fabric API error: Pattern execution failed"
            ):
                fabric_run_pattern_tool("test_pattern", "test input")

            mock_api_client.close.assert_called_once()

    def test_sse_json_decode_error_handling(
        self, fabric_run_pattern_tool: Callable[..., Any]
    ) -> None:
        """Test handling of malformed JSON in SSE stream."""
        with patch("fabric_mcp.core.FabricApiClient") as mock_api_client_class:
            mock_api_client = Mock()
            mock_api_client_class.return_value = mock_api_client

            # Mock SSE response with malformed JSON
            mock_response = Mock()
            mock_response.iter_lines.return_value = [
                'data: {"type": "content", "content": "Good data", "format": "text"}',
                "data: {invalid json}",  # This should be skipped
                'data: {"type": "content", "content": " more data", "format": "text"}',
                'data: {"type": "complete"}',
            ]
            mock_api_client.post.return_value = mock_response

            result: dict[str, Any] = fabric_run_pattern_tool(
                "test_pattern", "test input"
            )

            # Should still work, skipping the malformed JSON line
            assert result["output_text"] == "Good data more data"
            assert result["output_format"] == "text"

    def test_empty_input_text_handling(
        self, fabric_run_pattern_tool: Callable[..., Any]
    ) -> None:
        """Test pattern execution with empty input text."""
        with patch("fabric_mcp.core.FabricApiClient") as mock_api_client_class:
            mock_api_client = Mock()
            mock_api_client_class.return_value = mock_api_client

            # Mock SSE response
            mock_response = Mock()
            mock_response.iter_lines.return_value = [
                'data: {"type": "content", "content": "No input provided", '
                '"format": "text"}',
                'data: {"type": "complete"}',
            ]
            mock_api_client.post.return_value = mock_response

            result: dict[str, Any] = fabric_run_pattern_tool("test_pattern", "")

            assert result["output_text"] == "No input provided"
            assert result["output_format"] == "text"

    def test_stream_parameter_ignored(
        self, fabric_run_pattern_tool: Callable[..., Any]
    ) -> None:
        """Test that stream parameter is ignored (non-streaming behavior)."""
        with patch("fabric_mcp.core.FabricApiClient") as mock_api_client_class:
            mock_api_client = Mock()
            mock_api_client_class.return_value = mock_api_client

            # Mock SSE response
            mock_response = Mock()
            mock_response.iter_lines.return_value = [
                'data: {"type": "content", "content": "Output", "format": "text"}',
                'data: {"type": "complete"}',
            ]
            mock_api_client.post.return_value = mock_response

            # Test with stream=True (should be ignored)
            result: dict[str, Any] = fabric_run_pattern_tool(
                "test_pattern", "test input", stream=True
            )

            assert result["output_text"] == "Output"
            assert result["output_format"] == "text"
            # Should still return complete output, not stream

    def test_api_request_payload_structure(
        self, fabric_run_pattern_tool: Callable[..., Any]
    ) -> None:
        """Test that the API request payload has correct structure."""
        with patch("fabric_mcp.core.FabricApiClient") as mock_api_client_class:
            mock_api_client = Mock()
            mock_api_client_class.return_value = mock_api_client

            # Mock successful response
            mock_response = Mock()
            mock_response.iter_lines.return_value = [
                'data: {"type": "content", "content": "Output", "format": "text"}',
                'data: {"type": "complete"}',
            ]
            mock_api_client.post.return_value = mock_response

            fabric_run_pattern_tool("analyze_claims", "test input")

            # Verify API call was made with correct structure
            mock_api_client.post.assert_called_once()
            call_args = mock_api_client.post.call_args

            assert call_args[0][0] == "/chat"  # endpoint
            payload = call_args[1]["json_data"]

            # Verify payload structure
            assert "prompts" in payload
            assert isinstance(payload["prompts"], list)
            assert len(payload["prompts"]) == 1

            prompt = payload["prompts"][0]
            assert prompt["patternName"] == "analyze_claims"
            assert prompt["userInput"] == "test input"
            assert prompt["model"] == "gpt-4"
            assert prompt["vendor"] == "openai"

            # Verify other request fields
            assert payload["language"] == "en"
            assert "temperature" in payload
            assert "topP" in payload

    def test_no_content_chunks_handling(
        self, fabric_run_pattern_tool: Callable[..., Any]
    ) -> None:
        """Test handling of SSE stream with no content chunks."""
        with patch("fabric_mcp.core.FabricApiClient") as mock_api_client_class:
            mock_api_client = Mock()
            mock_api_client_class.return_value = mock_api_client

            # Mock SSE response with only completion
            mock_response = Mock()
            mock_response.iter_lines.return_value = [
                'data: {"type": "complete"}',
            ]
            mock_api_client.post.return_value = mock_response

            result: dict[str, Any] = fabric_run_pattern_tool(
                "test_pattern", "test input"
            )

            assert result["output_text"] == ""  # Empty output
            assert result["output_format"] == "text"  # Default format
