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
