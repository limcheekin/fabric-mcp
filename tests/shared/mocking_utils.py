"""Shared mocking utilities for test cases."""

import json
from typing import Any
from unittest.mock import MagicMock, Mock

import httpx
import pytest
from mcp import McpError


class FabricApiMockBuilder:
    """Builder class for creating consistent FabricApiClient mocks."""

    def __init__(self, mock_api_client_class: MagicMock):
        """Initialize the mock builder.

        Args:
            mock_api_client_class: The patched FabricApiClient class mock
        """
        self.mock_api_client_class = mock_api_client_class
        self.mock_api_client = Mock()
        self.mock_api_client_class.return_value = self.mock_api_client
        self.mock_response = Mock()
        self.mock_api_client.get.return_value = self.mock_response

    def with_successful_response(self, json_data: Any) -> "FabricApiMockBuilder":
        """Configure mock for successful API response.

        Args:
            json_data: The JSON data to return from the API

        Returns:
            Self for method chaining
        """
        self.mock_response.json.return_value = json_data
        return self

    def with_connection_error(
        self, error_message: str = "Connection failed"
    ) -> "FabricApiMockBuilder":
        """Configure mock to raise connection error.

        Args:
            error_message: The error message for the connection error

        Returns:
            Self for method chaining
        """
        connection_error = httpx.RequestError(error_message)
        self.mock_api_client.get.side_effect = connection_error
        return self

    def with_http_status_error(
        self,
        status_code: int,
        reason_phrase: str = "Internal Server Error",
        response_text: str = "",
    ) -> "FabricApiMockBuilder":
        """Configure mock to raise HTTP status error.

        Args:
            status_code: HTTP status code
            reason_phrase: HTTP reason phrase
            response_text: Response text content

        Returns:
            Self for method chaining
        """
        # Create a mock response for the error
        error_response = Mock()
        error_response.status_code = status_code
        error_response.reason_phrase = reason_phrase
        error_response.text = response_text

        http_error = httpx.HTTPStatusError(
            f"{status_code} {reason_phrase}",
            request=Mock(),
            response=error_response,
        )
        self.mock_api_client.get.side_effect = http_error
        return self

    def with_json_decode_error(
        self, error_message: str = "Invalid JSON"
    ) -> "FabricApiMockBuilder":
        """Configure mock to raise JSON decode error.

        Args:
            error_message: The JSON decode error message

        Returns:
            Self for method chaining
        """
        json_error = json.JSONDecodeError(error_message, "", 0)
        self.mock_response.json.side_effect = json_error
        return self

    def with_unexpected_error(self, error: Exception) -> "FabricApiMockBuilder":
        """Configure mock to raise an unexpected error.

        Args:
            error: The exception to raise

        Returns:
            Self for method chaining
        """
        self.mock_api_client.get.side_effect = error
        return self

    def build(self) -> Mock:
        """Build and return the configured mock API client.

        Returns:
            The configured mock API client
        """
        return self.mock_api_client


def create_fabric_api_mock(mock_api_client_class: MagicMock) -> FabricApiMockBuilder:
    """Create a FabricApiClient mock builder.

    Args:
        mock_api_client_class: The patched FabricApiClient class mock

    Returns:
        FabricApiMockBuilder instance for configuration
    """
    return FabricApiMockBuilder(mock_api_client_class)


# Predefined common response data
COMMON_PATTERN_LIST = ["pattern1", "pattern2", "pattern3"]

COMMON_PATTERN_DETAILS = {
    "Name": "test_pattern",
    "Description": "Test pattern description",
    "Pattern": "# Test pattern system prompt",
}

COMMON_EMPTY_PATTERN_DETAILS = {
    "Name": "test_pattern",
    "Description": "",
    "Pattern": "# Test pattern system prompt",
}

COMMON_PATTERN_NOT_FOUND_ERROR_TEXT = (
    "open /path/to/patterns/nonexistent: no such file or directory"
)


def assert_api_client_calls(
    mock_api_client: Mock, expected_endpoint: str, call_count: int = 1
) -> None:
    """Assert that the API client was called correctly.

    Args:
        mock_api_client: The mock API client
        expected_endpoint: The expected API endpoint that was called
        call_count: Expected number of calls (default: 1)
    """
    if call_count == 1:
        mock_api_client.get.assert_called_once_with(expected_endpoint)
    else:
        assert mock_api_client.get.call_count == call_count
        mock_api_client.get.assert_called_with(expected_endpoint)

    mock_api_client.close.assert_called_once()


# Test helper functions to eliminate duplicate code patterns
def assert_connection_error_test(
    mock_api_client_class: MagicMock,
    test_function: Any,
    error_message_contains: str = "Failed to connect to Fabric API",
) -> None:
    """Helper function for testing connection error scenarios.

    Args:
        mock_api_client_class: The patched FabricApiClient class mock
        test_function: The function to test (e.g., fabric_list_patterns)
        error_message_contains: Expected substring in error message
    """

    # Arrange
    create_fabric_api_mock(mock_api_client_class).with_connection_error(
        "Connection failed"
    ).build()

    # Act & Assert
    with pytest.raises(McpError) as exc_info:
        test_function()

    assert error_message_contains in str(exc_info.value.error.message)


def assert_unexpected_error_test(
    mock_api_client_class: MagicMock, test_function: Any, error_message_contains: str
) -> None:
    """Helper function for testing unexpected error scenarios.

    Args:
        mock_api_client_class: The patched FabricApiClient class mock
        test_function: The function to test
        error_message_contains: Expected substring in error message
    """

    # Arrange
    create_fabric_api_mock(mock_api_client_class).with_unexpected_error(
        ValueError("Unexpected error")
    ).build()

    # Act & Assert
    with pytest.raises(McpError) as exc_info:
        test_function()

    assert exc_info.value.error.code == -32603  # Internal error
    assert error_message_contains in str(exc_info.value.error.message)
