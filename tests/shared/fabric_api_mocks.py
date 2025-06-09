"""Comprehensive mocking utilities for FabricApiClient in tests.

This module provides a single, consistent interface for mocking FabricApiClient
across all test files, eliminating code duplication and improving maintainability.
"""

import json
from collections.abc import Generator
from contextlib import contextmanager
from json import JSONDecodeError
from typing import Any
from unittest.mock import MagicMock, Mock, patch

import httpx
import pytest
from mcp import McpError


class FabricApiMockBuilder:
    """Comprehensive builder for FabricApiClient mocks supporting all API patterns."""

    def __init__(self) -> None:
        """Initialize builder with sensible defaults."""
        self.mock_api_client = Mock()
        self.mock_response = Mock()
        self._configure_defaults()

    def _configure_defaults(self) -> None:
        """Configure default behavior for the mock."""
        # Default to successful response behavior
        self.mock_api_client.get.return_value = self.mock_response
        self.mock_api_client.post.return_value = self.mock_response
        self.mock_response.json.return_value = {}
        self.mock_response.iter_lines.return_value = []

    # Methods for configuring JSON API responses (GET endpoints)
    def with_json_response(self, json_data: dict[str, Any]) -> "FabricApiMockBuilder":
        """Configure mock for successful JSON API response.

        Args:
            json_data: The JSON data to return from the API

        Returns:
            Self for method chaining
        """
        self.mock_response.json.return_value = json_data
        return self

    def with_successful_pattern_list(
        self, patterns: list[str] | None = None
    ) -> "FabricApiMockBuilder":
        """Configure mock for successful pattern list response.

        Args:
            patterns: List of pattern names. Defaults to common test patterns.

        Returns:
            Self for method chaining
        """
        if patterns is None:
            patterns = ["summarize", "explain", "improve_writing"]

        self.mock_response.json.return_value = patterns
        return self

    def with_successful_pattern_details(
        self,
        name: str = "test_pattern",
        description: str = "Test pattern description",
        system_prompt: str = "# Test pattern system prompt",
    ) -> "FabricApiMockBuilder":
        """Configure mock for successful pattern details response.

        Args:
            name: Pattern name
            description: Pattern description
            system_prompt: Pattern system prompt

        Returns:
            Self for method chaining
        """
        pattern_data = {
            "Name": name,
            "Description": description,
            "Pattern": system_prompt,
        }
        self.mock_response.json.return_value = pattern_data
        return self

    def with_raw_response_data(self, data: Any) -> "FabricApiMockBuilder":
        """Configure mock to return raw response data (for testing mixed types).

        Args:
            data: Raw data to return from the API (any type)

        Returns:
            Self for method chaining
        """
        self.mock_response.json.return_value = data
        return self

    def with_json_decode_error(self, invalid_json: str) -> "FabricApiMockBuilder":
        """Configure mock to raise JSONDecodeError.

        Args:
            invalid_json: Invalid JSON string that triggers the error

        Returns:
            Self for method chaining
        """

        self.mock_response.json.side_effect = JSONDecodeError(
            "Expecting value", invalid_json, 0
        )
        return self

    # Methods for configuring SSE responses (POST endpoints)
    def with_sse_lines(self, lines: list[str]) -> "FabricApiMockBuilder":
        """Configure mock to return specific SSE lines.

        Args:
            lines: List of SSE lines to return

        Returns:
            Self for method chaining
        """
        self.mock_response.iter_lines.return_value = lines
        return self

    def with_successful_sse(
        self, content: str = "Test output", format_type: str = "text"
    ) -> "FabricApiMockBuilder":
        """Configure mock with successful SSE response.

        Args:
            content: Content to return in SSE stream
            format_type: Format type (text, markdown, etc.)

        Returns:
            Self for method chaining
        """

        # Properly escape the content for JSON
        content_data = {
            "type": "content",
            "content": content,
            "format": format_type,
        }
        complete_data = {"type": "complete"}

        lines = [
            f"data: {json.dumps(content_data)}",
            f"data: {json.dumps(complete_data)}",
        ]
        return self.with_sse_lines(lines)

    def with_sse_error(self, error_message: str) -> "FabricApiMockBuilder":
        """Configure mock to return SSE error response.

        Args:
            error_message: Error message to include in SSE stream

        Returns:
            Self for method chaining
        """

        error_data = {"type": "error", "content": error_message}
        lines = [f"data: {json.dumps(error_data)}"]
        return self.with_sse_lines(lines)

    def with_partial_sse_data(self) -> "FabricApiMockBuilder":
        """Configure mock with partial/incomplete SSE data.

        Returns:
            Self for method chaining
        """
        lines = ['data: {"type": "content",']  # Incomplete JSON
        return self.with_sse_lines(lines)

    def with_empty_sse_stream(self) -> "FabricApiMockBuilder":
        """Configure mock with empty SSE stream.

        Returns:
            Self for method chaining
        """
        return self.with_sse_lines([])

    # Methods for configuring error conditions
    def with_connection_error(
        self, error_message: str = "Connection failed"
    ) -> "FabricApiMockBuilder":
        """Configure mock to raise connection error.

        Args:
            error_message: Error message for the connection error

        Returns:
            Self for method chaining
        """
        connection_error = httpx.ConnectError(error_message)
        self.mock_api_client.get.side_effect = connection_error
        self.mock_api_client.post.side_effect = connection_error
        return self

    def with_timeout_error(self) -> "FabricApiMockBuilder":
        """Configure mock to raise timeout error.

        Returns:
            Self for method chaining
        """
        timeout_error = httpx.TimeoutException("Request timed out")
        self.mock_api_client.get.side_effect = timeout_error
        self.mock_api_client.post.side_effect = timeout_error
        return self

    def with_http_error(
        self, status_code: int = 500, response_text: str = "Internal Server Error"
    ) -> "FabricApiMockBuilder":
        """Configure mock to raise HTTP error.

        Args:
            status_code: HTTP status code
            response_text: Response text

        Returns:
            Self for method chaining
        """
        mock_request = Mock()
        mock_response = Mock()
        mock_response.status_code = status_code
        mock_response.text = response_text
        mock_response.reason_phrase = response_text  # Add reason_phrase

        http_error = httpx.HTTPStatusError(
            f"HTTP {status_code}", request=mock_request, response=mock_response
        )
        self.mock_api_client.get.side_effect = http_error
        self.mock_api_client.post.side_effect = http_error
        return self

    def with_unexpected_error(self, error: Exception) -> "FabricApiMockBuilder":
        """Configure mock to raise unexpected error.

        Args:
            error: Exception to raise

        Returns:
            Self for method chaining
        """
        self.mock_api_client.get.side_effect = error
        self.mock_api_client.post.side_effect = error
        return self

    def build(self) -> Mock:
        """Build and return the configured mock API client.

        Returns:
            Configured mock API client instance
        """
        return self.mock_api_client


@contextmanager
def mock_fabric_api_client(
    builder: FabricApiMockBuilder | None = None,
) -> Generator[Mock, None, None]:
    """Context manager for mocking FabricApiClient with consistent setup.

    Args:
        builder: Optional FabricApiMockBuilder instance. If None, creates default.

    Yields:
        Mock: The mocked API client instance.
    """
    if builder is None:
        builder = FabricApiMockBuilder().with_successful_sse()

    mock_api_client = builder.build()

    with patch("fabric_mcp.core.FabricApiClient") as mock_api_client_class:
        mock_api_client_class.return_value = mock_api_client
        yield mock_api_client


# Pytest fixtures for common scenarios
@pytest.fixture
def mock_successful_fabric_api() -> Generator[Mock, None, None]:
    """Pytest fixture for a successful FabricApiClient mock."""
    builder = FabricApiMockBuilder().with_successful_sse()
    with mock_fabric_api_client(builder) as mock_client:
        yield mock_client


@pytest.fixture
def mock_fabric_api_with_patterns() -> Generator[Mock, None, None]:
    """Pytest fixture for FabricApiClient mock with pattern list."""
    builder = FabricApiMockBuilder().with_successful_pattern_list()
    with mock_fabric_api_client(builder) as mock_client:
        yield mock_client


@pytest.fixture
def mock_fabric_api_with_pattern_details() -> Generator[Mock, None, None]:
    """Pytest fixture for FabricApiClient mock with pattern details."""
    builder = FabricApiMockBuilder().with_successful_pattern_details()
    with mock_fabric_api_client(builder) as mock_client:
        yield mock_client


# Helper functions for common assertion patterns
def assert_api_client_calls(
    mock_api_client: Mock,
    expected_endpoint: str,
    method: str = "get",
    expected_call_count: int = 1,
) -> None:
    """Assert that API client was called correctly.

    Args:
        mock_api_client: The mocked API client
        expected_endpoint: Expected API endpoint
        method: HTTP method ('get' or 'post')
        expected_call_count: Expected number of calls
    """
    mock_method = getattr(mock_api_client, method)
    assert mock_method.call_count == expected_call_count
    if expected_call_count > 0:
        call_args = mock_method.call_args[0]
        assert expected_endpoint in call_args[0]


def assert_mcp_error(
    error_info: pytest.ExceptionInfo[McpError],
    expected_code: int,
    expected_message_contains: str,
) -> None:
    """Assert MCP error details.

    Args:
        error_info: pytest ExceptionInfo from pytest.raises
        expected_code: Expected MCP error code
        expected_message_contains: Expected substring in error message
    """
    assert error_info.value.error.code == expected_code
    assert expected_message_contains in str(error_info.value.error.message)


# Helper function for testing error scenarios with consistent pattern
def test_error_scenario(
    mock_api_client_class: MagicMock,
    test_function: Any,
    error_config_func: str,
    error_message_contains: str,
    error_code: int = -32603,
    **error_kwargs: Any,
) -> None:
    """Helper function for testing error scenarios with consistent pattern.

    Args:
        mock_api_client_class: The patched FabricApiClient class mock
        test_function: The function to test
        error_config_func: Name of the error configuration method on
            FabricApiMockBuilder
        error_message_contains: Expected substring in error message
        error_code: Expected MCP error code
        **error_kwargs: Additional arguments for the error configuration method
    """
    # Arrange
    builder = FabricApiMockBuilder()
    config_method = getattr(builder, error_config_func)
    builder = config_method(**error_kwargs)

    mock_api_client = builder.build()
    mock_api_client_class.return_value = mock_api_client

    # Act & Assert
    with pytest.raises(McpError) as exc_info:
        test_function()

    assert_mcp_error(exc_info, error_code, error_message_contains)


# Helper function for testing unexpected error scenarios
def assert_unexpected_error_test(
    test_function: Any, error_message_contains: str
) -> None:
    """Helper function for testing unexpected error scenarios.

    Args:
        test_function: The function to test
        error_message_contains: Expected substring in error message
    """
    # Arrange
    builder = FabricApiMockBuilder().with_unexpected_error(
        ValueError("Unexpected error")
    )

    # Act & Assert
    with mock_fabric_api_client(builder):
        with pytest.raises(McpError) as exc_info:
            test_function()

    assert exc_info.value.error.code == -32603  # Internal error
    assert error_message_contains in str(exc_info.value.error.message)
