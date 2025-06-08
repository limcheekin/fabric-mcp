"""Unit tests for fabric_list_patterns MCP tool."""

import inspect
from typing import Any
from unittest.mock import patch

import pytest
from mcp.shared.exceptions import McpError

from fabric_mcp.core import FabricMCP
from tests.shared.fabric_api_mocks import (
    FabricApiMockBuilder,
    assert_api_client_calls,
    assert_unexpected_error_test,
    mock_fabric_api_client,
)


class TestFabricListPatterns:
    """Test cases for the fabric_list_patterns MCP tool."""

    server: FabricMCP
    fabric_list_patterns: Any

    def setup_method(self) -> None:
        """Set up test fixtures."""
        self.server = FabricMCP()
        # Get the fabric_list_patterns tool function
        self.fabric_list_patterns = getattr(self.server, "_FabricMCP__tools")[0]

    def test_successful_response_with_multiple_patterns(self):
        """Test successful API response with multiple pattern names."""
        # Arrange
        patterns = ["summarize", "explain", "improve_writing"]
        builder = FabricApiMockBuilder().with_successful_pattern_list(patterns)

        # Act
        with mock_fabric_api_client(builder) as mock_client:
            result = self.fabric_list_patterns()

        # Assert
        assert result == patterns
        assert_api_client_calls(mock_client, "/patterns/names")

    def test_successful_response_with_empty_list(self):
        """Test successful API response with empty pattern list."""
        # Arrange
        builder = FabricApiMockBuilder().with_successful_pattern_list([])

        # Act
        with mock_fabric_api_client(builder) as mock_client:
            result = self.fabric_list_patterns()

        # Assert
        assert result == []
        assert_api_client_calls(mock_client, "/patterns/names")

    def test_connection_error_handling(self):
        """Test handling of connection errors (httpx.RequestError)."""
        # Arrange
        builder = FabricApiMockBuilder().with_connection_error(
            "Failed to connect to Fabric API"
        )

        # Act & Assert
        with mock_fabric_api_client(builder) as _:
            with pytest.raises(McpError) as exc_info:
                self.fabric_list_patterns()

            assert "Failed to connect to Fabric API" in str(
                exc_info.value.error.message
            )
            assert exc_info.value.error.code == -32603

    def test_http_status_error_handling(self):
        """Test handling of HTTP status errors (httpx.HTTPStatusError)."""
        # Arrange
        builder = FabricApiMockBuilder().with_http_error(
            status_code=500, response_text="Internal Server Error"
        )

        # Act & Assert
        with mock_fabric_api_client(builder) as mock_client:
            with pytest.raises(McpError) as exc_info:
                self.fabric_list_patterns()

            assert "Fabric API error: 500 Internal Server Error" in str(
                exc_info.value.error.message
            )
            assert exc_info.value.error.code == -32603
            assert_api_client_calls(mock_client, "/patterns/names")

    def test_invalid_response_format_not_list(self):
        """Test handling of invalid response format (not a list)."""
        # Arrange
        builder = FabricApiMockBuilder().with_json_response(
            {"error": "Invalid response"}
        )

        # Act & Assert
        with mock_fabric_api_client(builder) as mock_client:
            with pytest.raises(McpError) as exc_info:
                self.fabric_list_patterns()

        assert "Invalid response format from Fabric API: expected list" in str(
            exc_info.value.error.message
        )
        assert exc_info.value.error.code == -32603
        assert_api_client_calls(mock_client, "/patterns/names")

    def test_mixed_types_in_response_filters_non_strings(self):
        """Test handling of mixed types in response - filters out non-strings."""
        # Arrange
        builder = FabricApiMockBuilder().with_raw_response_data(
            ["pattern1", 123, "pattern2", None, "pattern3"]
        )

        # Act
        with mock_fabric_api_client(builder) as mock_client:
            with patch.object(self.server, "logger") as mock_logging:
                result = self.fabric_list_patterns()

        # Assert
        assert result == ["pattern1", "pattern2", "pattern3"]
        # Verify warnings were logged for non-string items
        assert mock_logging.warning.call_count == 2
        assert_api_client_calls(mock_client, "/patterns/names")

    def test_json_parsing_error_handling(self):
        """Test handling of JSON parsing errors."""
        # Arrange
        builder = FabricApiMockBuilder().with_json_decode_error("Invalid JSON")

        # Act & Assert
        with mock_fabric_api_client(builder) as mock_client:
            with pytest.raises(McpError) as exc_info:
                self.fabric_list_patterns()

        assert "Unexpected error during retrieving patterns" in str(
            exc_info.value.error.message
        )
        assert exc_info.value.error.code == -32603
        assert_api_client_calls(mock_client, "/patterns/names")

    def test_unexpected_exception_handling(self):
        """Test handling of unexpected exceptions."""
        assert_unexpected_error_test(
            self.fabric_list_patterns,
            "Unexpected error during retrieving patterns",
        )

    def test_tool_signature_and_return_type(self):
        """Test that the tool has the correct signature and return type annotation."""
        # Get the function signature
        sig = inspect.signature(self.fabric_list_patterns)

        # Verify no parameters
        assert len(sig.parameters) == 0

        # Verify return type annotation
        assert sig.return_annotation == list[str]

    def test_tool_docstring(self):
        """Test that the tool has appropriate documentation."""
        assert self.fabric_list_patterns.__doc__ is not None
        assert "available fabric patterns" in self.fabric_list_patterns.__doc__.lower()
