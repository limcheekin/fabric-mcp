"""Unit tests for covering missed lines in core.py."""

from unittest.mock import Mock, patch

import pytest
from mcp.shared.exceptions import McpError

from fabric_mcp.core import FabricMCP
from tests.shared.fabric_api.base import TestFixturesBase
from tests.shared.fabric_api_mocks import assert_mcp_error


class TestCoreCoverage(TestFixturesBase):
    """Test cases for covering missed lines in core.py."""

    # Tests for fabric_list_patterns (lines 175, 189)
    def test_fabric_list_patterns_invalid_response_type(
        self, server: FabricMCP
    ) -> None:
        """Test handling of non-list response from Fabric API."""
        with patch("fabric_mcp.core.FabricApiClient") as mock_client_class:
            mock_client = Mock()
            mock_response = Mock()
            mock_response.json.return_value = {"patterns": ["p1", "p2"]}  # Invalid type
            mock_client.get.return_value = mock_response
            mock_client_class.return_value = mock_client

            with pytest.raises(McpError) as exc_info:
                server.fabric_list_patterns()

            assert_mcp_error(
                exc_info,
                expected_code=-32603,
                expected_message_contains=(
                    "Invalid response from Fabric API: expected list of patterns"
                ),
            )

    def test_fabric_list_patterns_invalid_item_type(self, server: FabricMCP) -> None:
        """Test handling of list with non-string items from Fabric API."""
        with patch("fabric_mcp.core.FabricApiClient") as mock_client_class:
            mock_client = Mock()
            mock_response = Mock()
            mock_response.json.return_value = ["p1", 123, "p2"]  # Invalid item type
            mock_client.get.return_value = mock_response
            mock_client_class.return_value = mock_client

            with pytest.raises(McpError) as exc_info:
                server.fabric_list_patterns()

            assert_mcp_error(
                exc_info,
                expected_code=-32603,
                expected_message_contains=(
                    "Invalid pattern name in response: expected string, got int"
                ),
            )

    def test_fabric_get_pattern_details_invalid_response_type(
        self, server: FabricMCP
    ) -> None:
        """Test handling of non-dict response from Fabric API."""
        with patch("fabric_mcp.core.FabricApiClient") as mock_client_class:
            mock_client = Mock()
            mock_response = Mock()
            mock_response.json.return_value = ["invalid"]  # Invalid type
            mock_client.get.return_value = mock_response
            mock_client_class.return_value = mock_client

            with pytest.raises(McpError) as exc_info:
                server.fabric_get_pattern_details("test_pattern")

            assert_mcp_error(
                exc_info,
                expected_code=-32603,
                expected_message_contains=(
                    "Invalid response from Fabric API:"
                    " expected dict for pattern details"
                ),
            )

    def test_fabric_get_pattern_details_missing_fields(self, server: FabricMCP) -> None:
        """Test handling of response with missing fields."""
        with patch("fabric_mcp.core.FabricApiClient") as mock_client_class:
            mock_client = Mock()
            mock_response = Mock()
            mock_response.json.return_value = {
                "Name": "test_pattern",
                "Pattern": "...",
            }  # Missing Description
            mock_client.get.return_value = mock_response
            mock_client_class.return_value = mock_client

            with pytest.raises(McpError) as exc_info:
                server.fabric_get_pattern_details("test_pattern")

            assert_mcp_error(
                exc_info,
                expected_code=-32603,
                expected_message_contains=(
                    "Invalid pattern details response: missing required fields"
                ),
            )

    # Test for _validate_string_parameter (line 484)
    def test_run_pattern_with_empty_model_name(self, server: FabricMCP) -> None:
        """Test McpError for empty string model_name."""
        with pytest.raises(McpError) as exc_info:
            server.fabric_run_pattern(pattern_name="some_pattern", model_name="   ")

        assert_mcp_error(
            exc_info,
            expected_code=-32602,
            expected_message_contains="model_name must be a non-empty string",
        )

    # Test for line 499: Empty pattern name validation via fabric_run_pattern
    def test_fabric_run_pattern_empty_pattern_name(self, server: FabricMCP) -> None:
        """Test ValueError for empty pattern name via fabric_run_pattern."""
        # This should trigger the ValueError in _execute_fabric_pattern
        with patch("fabric_mcp.core.FabricApiClient"):
            with pytest.raises(McpError) as exc_info:
                server.fabric_run_pattern("   ")  # Empty/whitespace pattern name

            # The ValueError is now wrapped in McpError
            assert_mcp_error(
                exc_info,
                expected_code=-32602,
                expected_message_contains=(
                    "pattern_name is required and cannot be empty"
                ),
            )

    # Test for line 635: Empty SSE stream validation via fabric_run_pattern
    def test_fabric_run_pattern_empty_sse_stream(self, server: FabricMCP) -> None:
        """Test RuntimeError for empty SSE stream via fabric_run_pattern."""
        with patch("fabric_mcp.core.FabricApiClient") as mock_client_class:
            mock_client = Mock()
            mock_response = Mock()
            mock_response.iter_lines.return_value = []  # Empty stream
            mock_response.raise_for_status.return_value = None
            mock_client.post.return_value = mock_response
            mock_client_class.return_value = mock_client

            with pytest.raises(McpError) as exc_info:
                server.fabric_run_pattern("test_pattern")

            assert "Empty SSE stream - no data received" in str(exc_info.value)

    # Test for line 506: Default config creation
    def test_fabric_run_pattern_none_config(self, server: FabricMCP) -> None:
        """Test that None config gets replaced with default PatternExecutionConfig."""
        with patch("fabric_mcp.core.FabricApiClient") as mock_client_class:
            mock_client = Mock()
            mock_response = Mock()
            # Return success content to avoid other errors
            mock_response.iter_lines.return_value = [
                'data: {"type": "content", "content": "test"}',
                'data: {"type": "complete"}',
            ]
            mock_response.raise_for_status.return_value = None
            mock_client.post.return_value = mock_response
            mock_client_class.return_value = mock_client

            # Call without specifying config - this will trigger the None default
            # which should hit line 506: config = PatternExecutionConfig()
            result = server.fabric_run_pattern("test_pattern")
            assert isinstance(result, dict)
            assert result["output_text"] == "test"

    # Test for line 642: Empty lines in SSE response
    def test_fabric_run_pattern_sse_empty_lines(self, server: FabricMCP) -> None:
        """Test SSE parsing with empty lines that should be skipped."""
        with patch("fabric_mcp.core.FabricApiClient") as mock_client_class:
            mock_client = Mock()
            mock_response = Mock()
            # Include empty lines and whitespace-only lines that should be skipped
            mock_response.iter_lines.return_value = [
                "",  # Empty line - should trigger continue
                "   ",  # Whitespace line - should trigger continue
                'data: {"type": "content", "content": "test"}',
                "",  # Another empty line
                'data: {"type": "complete"}',
            ]
            mock_response.raise_for_status.return_value = None
            mock_client.post.return_value = mock_response
            mock_client_class.return_value = mock_client

            result = server.fabric_run_pattern("test_pattern")
            assert isinstance(result, dict)
            assert result["output_text"] == "test"

    # Test for lines 666-669: SSE error handling and unexpected types
    def test_fabric_run_pattern_sse_error_type(self, server: FabricMCP) -> None:
        """Test RuntimeError for SSE error type in streaming mode."""
        import json

        with patch("fabric_mcp.core.FabricApiClient") as mock_client_class:
            mock_client = Mock()
            mock_response = Mock()
            error_data = json.dumps({"type": "error", "content": "Test error"})
            mock_response.iter_lines.return_value = [f"data: {error_data}"]
            mock_response.raise_for_status.return_value = None
            mock_client.post.return_value = mock_response
            mock_client_class.return_value = mock_client

            with pytest.raises(RuntimeError) as exc_info:
                # Use streaming mode to trigger _parse_sse_stream
                list(server.fabric_run_pattern("test_pattern", stream=True))

            assert "Fabric API error: Test error" in str(exc_info.value)

    def test_fabric_run_pattern_sse_unexpected_type(self, server: FabricMCP) -> None:
        """Test RuntimeError for unexpected SSE type in streaming mode."""
        import json

        with patch("fabric_mcp.core.FabricApiClient") as mock_client_class:
            mock_client = Mock()
            mock_response = Mock()
            unexpected_data = json.dumps({"type": "unknown_type", "content": "test"})
            mock_response.iter_lines.return_value = [f"data: {unexpected_data}"]
            mock_response.raise_for_status.return_value = None
            mock_client.post.return_value = mock_response
            mock_client_class.return_value = mock_client

            with pytest.raises(RuntimeError) as exc_info:
                # Use streaming mode to trigger _parse_sse_stream
                list(server.fabric_run_pattern("test_pattern", stream=True))

            assert "Unexpected SSE data type received: unknown_type" in str(
                exc_info.value
            )

    # Test for line 755: Variables validation (non-dict)
    def test_validate_variables_parameter_non_dict(self, server: FabricMCP) -> None:
        """Test McpError for non-dict variables parameter."""
        with pytest.raises(McpError) as exc_info:
            server.fabric_run_pattern(
                pattern_name="test_pattern",
                variables="not_a_dict",  # type: ignore
            )

        assert_mcp_error(
            exc_info,
            expected_code=-32602,
            expected_message_contains="variables must be a dictionary",
        )

    # Test for line 765: Variables validation (non-string keys/values)
    def test_validate_variables_parameter_non_string_values(
        self, server: FabricMCP
    ) -> None:
        """Test McpError for variables with non-string values."""
        with pytest.raises(McpError) as exc_info:
            server.fabric_run_pattern(
                pattern_name="test_pattern",
                variables={"key1": "value1", "key2": 123},  # type: ignore
            )

        assert_mcp_error(
            exc_info,
            expected_code=-32602,
            expected_message_contains=(
                "variables must be a dictionary with string keys and values"
            ),
        )

    def test_validate_variables_parameter_non_string_keys(
        self, server: FabricMCP
    ) -> None:
        """Test McpError for variables with non-string keys."""
        with pytest.raises(McpError) as exc_info:
            server.fabric_run_pattern(
                pattern_name="test_pattern",
                variables={123: "value1", "key2": "value2"},  # type: ignore
            )

        assert_mcp_error(
            exc_info,
            expected_code=-32602,
            expected_message_contains=(
                "variables must be a dictionary with string keys and values"
            ),
        )

    # Test for line 784: Attachments validation (non-list)
    def test_validate_attachments_parameter_non_list(self, server: FabricMCP) -> None:
        """Test McpError for non-list attachments parameter."""
        with pytest.raises(McpError) as exc_info:
            server.fabric_run_pattern(
                pattern_name="test_pattern",
                attachments="not_a_list",  # type: ignore
            )

        assert_mcp_error(
            exc_info,
            expected_code=-32602,
            expected_message_contains="attachments must be a list",
        )

    # Test for line 791: Attachments validation (non-string items)
    def test_validate_attachments_parameter_non_string_items(
        self, server: FabricMCP
    ) -> None:
        """Test McpError for attachments with non-string items."""
        with pytest.raises(McpError) as exc_info:
            server.fabric_run_pattern(
                pattern_name="test_pattern",
                attachments=["file1.txt", 123, "file3.txt"],  # type: ignore
            )

        assert_mcp_error(
            exc_info,
            expected_code=-32602,
            expected_message_contains="attachments must be a list of strings",
        )
