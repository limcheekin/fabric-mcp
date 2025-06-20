"""Tests for fabric_run_pattern tool basic execution scenarios.

This module tests the basic execution functionality of the fabric_run_pattern tool,
including successful execution with various input and output formats.
"""

from collections.abc import Callable
from typing import Any

from tests.shared.fabric_api_mocks import (
    FabricApiMockBuilder,
    mock_fabric_api_client,
)
from tests.unit.test_fabric_run_pattern_base import TestFabricRunPatternFixtureBase


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

    def test_sse_response_with_empty_lines(
        self, fabric_run_pattern_tool: Callable[..., Any]
    ) -> None:
        """Test SSE parsing to ensure handling of empty lines in the response."""
        # Create SSE stream with empty lines mixed in
        sse_lines = [
            "",  # Empty line
            'data: {"type": "content", "content": "Hello", "format": "text"}',
            "",  # Another empty line
            'data: {"type": "complete"}',
            "",  # Final empty line
        ]
        builder = FabricApiMockBuilder().with_sse_lines(sse_lines)

        with mock_fabric_api_client(builder) as mock_api_client:
            result: dict[str, Any] = fabric_run_pattern_tool(
                "test_pattern", "test input"
            )

            assert isinstance(result, dict)
            assert result["output_text"] == "Hello"
            assert result["output_format"] == "text"
            mock_api_client.close.assert_called_once()
