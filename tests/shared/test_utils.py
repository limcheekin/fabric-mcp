"""Shared test utilities for reducing code duplication across test files.

This module provides common test fixtures, mocking utilities, and helper functions
to maintain DRY principles in test code and improve maintainability.
"""

from collections.abc import Generator
from contextlib import contextmanager
from typing import Any
from unittest.mock import Mock, patch

import pytest


class MockFabricApiClientBuilder:
    """Builder class for creating consistently configured mock FabricApiClient."""

    def __init__(self) -> None:
        """Initialize the builder with default configuration."""
        self.mock_api_client = Mock()
        self.mock_response = Mock()
        self.sse_lines: list[str] = []
        self.should_raise: Exception | None = None

    def with_sse_response(self, lines: list[str]) -> "MockFabricApiClientBuilder":
        """Configure the mock to return specific SSE lines."""
        self.sse_lines = lines
        return self

    def with_successful_sse(
        self, content: str = "Test output", format_type: str = "text"
    ) -> "MockFabricApiClientBuilder":
        """Configure the mock with a successful SSE response."""
        self.sse_lines = [
            f'data: {{"type": "content", "content": "{content}", '
            f'"format": "{format_type}"}}',
            'data: {"type": "complete"}',
        ]
        return self

    def with_error_response(self, error_message: str) -> "MockFabricApiClientBuilder":
        """Configure the mock to return an error SSE response."""
        self.sse_lines = [
            f'data: {{"type": "error", "content": "{error_message}"}}',
        ]
        return self

    def with_exception(self, exception: Exception) -> "MockFabricApiClientBuilder":
        """Configure the mock to raise an exception."""
        self.should_raise = exception
        return self

    def with_json_response(
        self, json_data: dict[str, Any]
    ) -> "MockFabricApiClientBuilder":
        """Configure the mock to return a JSON response (for non-SSE endpoints)."""
        self.mock_response.json.return_value = json_data
        return self

    def build(self) -> Mock:
        """Build and return the configured mock API client."""
        if self.should_raise:
            self.mock_api_client.post.side_effect = self.should_raise
            self.mock_api_client.get.side_effect = self.should_raise
        else:
            if self.sse_lines:
                self.mock_response.iter_lines.return_value = self.sse_lines
            self.mock_api_client.post.return_value = self.mock_response
            self.mock_api_client.get.return_value = self.mock_response

        return self.mock_api_client


@contextmanager
def mock_fabric_api_client(
    builder: MockFabricApiClientBuilder | None = None,
) -> Generator[Mock, None, None]:
    """Context manager for mocking FabricApiClient with consistent setup.

    Args:
        builder: Optional MockFabricApiClientBuilder instance. If None, creates default.

    Yields:
        Mock: The mocked API client instance.
    """
    if builder is None:
        builder = MockFabricApiClientBuilder().with_successful_sse()

    mock_api_client = builder.build()

    with patch("fabric_mcp.core.FabricApiClient") as mock_api_client_class:
        mock_api_client_class.return_value = mock_api_client
        yield mock_api_client


@pytest.fixture
def mock_successful_fabric_api() -> Generator[Mock, None, None]:
    """Pytest fixture for a successful FabricApiClient mock."""
    with mock_fabric_api_client() as mock_client:
        yield mock_client


@pytest.fixture
def fabric_api_builder() -> MockFabricApiClientBuilder:
    """Pytest fixture that returns a MockFabricApiClientBuilder for custom config."""
    return MockFabricApiClientBuilder()
