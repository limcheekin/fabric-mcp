"""Unit tests for fabric_list_strategies MCP tool."""

import json
from typing import Any, cast
from unittest.mock import Mock, patch

import httpx
import pytest
from mcp.shared.exceptions import McpError

from fabric_mcp.core import FabricMCP
from tests.shared.fabric_api.server import MOCK_STRATEGIES
from tests.shared.fabric_api_mocks import assert_mcp_error


class TestFabricListStrategies:
    """Test class for fabric_list_strategies functionality."""

    @pytest.fixture
    def server(self) -> FabricMCP:
        """Create a test server instance."""
        return FabricMCP(log_level="DEBUG")

    @pytest.fixture
    def mock_strategies_response(self) -> list[dict[str, str]]:
        """Mock strategies response data."""
        return MOCK_STRATEGIES

    @pytest.fixture
    def empty_strategies_response(self) -> list[dict[str, str]]:
        """Mock empty strategies response data."""
        return []

    def test_fabric_list_strategies_success(
        self, server: FabricMCP, mock_strategies_response: list[dict[str, str]]
    ) -> None:
        """Test successful strategy listing."""
        with patch("fabric_mcp.core.FabricApiClient") as mock_client_class:
            # Setup mock client
            mock_client = Mock()
            mock_response = Mock()
            mock_response.json.return_value = mock_strategies_response
            mock_client.get.return_value = mock_response
            mock_client_class.return_value = mock_client

            # Call the method
            result = server.fabric_list_strategies()

            # Verify API call
            mock_client.get.assert_called_once_with("/strategies")
            mock_client.close.assert_called_once()

            # Verify response structure
            assert isinstance(result, dict)
            assert "strategies" in result
            assert isinstance(result["strategies"], list)

            strategies = cast(list[dict[str, str]], result["strategies"])
            assert len(strategies) == 4

            # Verify each strategy object
            for i, strategy in enumerate(strategies):
                assert isinstance(strategy, dict)
                assert "name" in strategy
                assert "description" in strategy
                assert "prompt" in strategy
                assert strategy["name"] == mock_strategies_response[i]["name"]
                assert (
                    strategy["description"]
                    == mock_strategies_response[i]["description"]
                )
                assert strategy["prompt"] == mock_strategies_response[i]["prompt"]

    def test_fabric_list_strategies_empty_response(
        self, server: FabricMCP, empty_strategies_response: list[dict[str, str]]
    ) -> None:
        """Test handling of empty strategies list."""
        with patch("fabric_mcp.core.FabricApiClient") as mock_client_class:
            # Setup mock client
            mock_client = Mock()
            mock_response = Mock()
            mock_response.json.return_value = empty_strategies_response
            mock_client.get.return_value = mock_response
            mock_client_class.return_value = mock_client

            # Call the method
            result = server.fabric_list_strategies()

            # Verify API call
            mock_client.get.assert_called_once_with("/strategies")
            mock_client.close.assert_called_once()

            # Verify response structure for empty list
            assert isinstance(result, dict)
            assert "strategies" in result
            assert isinstance(result["strategies"], list)

            strategies = cast(list[dict[str, str]], result["strategies"])
            assert len(strategies) == 0

    def test_fabric_list_strategies_missing_fields(self, server: FabricMCP) -> None:
        """Test handling of strategy objects with missing required fields."""
        invalid_strategies = [
            {
                "name": "valid_strategy",
                "description": "Valid strategy with all fields",
                "prompt": "Valid prompt text",
            },
            {
                "name": "missing_description",
                "prompt": "Has prompt but missing description",
            },
            {
                "description": "Has description but missing name",
                "prompt": "Has prompt",
            },
            {
                "name": "no_prompt_strategy",
                "description": "Has description",
                "prompt": "",  # Empty prompt - should still be valid
            },
        ]

        with patch("fabric_mcp.core.FabricApiClient") as mock_client_class:
            # Setup mock client
            mock_client = Mock()
            mock_response = Mock()
            mock_response.json.return_value = invalid_strategies
            mock_client.get.return_value = mock_response
            mock_client_class.return_value = mock_client

            # Call the method
            result = server.fabric_list_strategies()

            # Verify API call
            mock_client.get.assert_called_once_with("/strategies")
            mock_client.close.assert_called_once()

            # Should return valid strategies (first and last - others missing fields)
            assert isinstance(result, dict)
            assert "strategies" in result
            strategies = cast(list[dict[str, str]], result["strategies"])
            assert len(strategies) == 2  # valid_strategy and no_prompt_strategy

            # Verify valid strategies
            assert strategies[0]["name"] == "valid_strategy"
            assert strategies[1]["name"] == "no_prompt_strategy"

    def test_fabric_list_strategies_non_dict_items(self, server: FabricMCP) -> None:
        """Test handling of non-dict items in strategies list."""
        mixed_strategies: list[Any] = [
            {
                "name": "valid_strategy",
                "description": "Valid strategy",
                "prompt": "Valid prompt",
            },
            "invalid_string_item",  # Non-dict item
        ]
        bad_return = {"strategies": ["s1", "s2"]}  # Not a list of dicts

        with patch("fabric_mcp.core.FabricApiClient") as mock_client_class:
            # Setup mock client
            mock_client = Mock()
            mock_response = Mock()
            mock_response.json.return_value = mixed_strategies
            mock_client.get.return_value = mock_response
            mock_client_class.return_value = mock_client

            # Call should raise McpError
            with pytest.raises(McpError) as exc_info:
                server.fabric_list_strategies()

            # Verify error details
            assert_mcp_error(
                exc_info,
                expected_code=-32603,  # Internal error
                expected_message_contains=(
                    "Invalid strategy object in response: expected dict, got str"
                ),
            )

            mock_response.json.return_value = bad_return
            with pytest.raises(McpError) as exc_info:
                server.fabric_list_strategies()

            assert_mcp_error(
                exc_info,
                expected_code=-32603,  # Internal error
                expected_message_contains=(
                    "Invalid response from Fabric API: expected list of strategies"
                ),
            )

            # Verify API call was attempted
            assert mock_client.get.call_count == 2
            assert mock_client.close.call_count == 2

    def test_fabric_list_strategies_non_string_fields(self, server: FabricMCP) -> None:
        """Test handling of strategy objects with non-string field values."""
        invalid_field_strategies = [
            {
                "name": "valid_strategy",
                "description": "Valid strategy",
                "prompt": "Valid prompt",
            },
            {
                "name": 123,  # Non-string name
                "description": "Has numeric name",
                "prompt": "Has prompt",
            },
            {
                "name": "string_name",
                "description": None,  # None description
                "prompt": "Has prompt",
            },
            {
                "name": "another_name",
                "description": "Has description",
                "prompt": ["list", "prompt"],  # Non-string prompt
            },
        ]

        with patch("fabric_mcp.core.FabricApiClient") as mock_client_class:
            # Setup mock client
            mock_client = Mock()
            mock_response = Mock()
            mock_response.json.return_value = invalid_field_strategies
            mock_client.get.return_value = mock_response
            mock_client_class.return_value = mock_client

            # Call the method
            result = server.fabric_list_strategies()

            # Verify API call
            mock_client.get.assert_called_once_with("/strategies")
            mock_client.close.assert_called_once()

            # Should only return valid strategies
            assert isinstance(result, dict)
            assert "strategies" in result
            strategies = cast(list[dict[str, str]], result["strategies"])
            assert len(strategies) == 1  # Only the valid strategy

            # Verify the valid strategy
            assert strategies[0]["name"] == "valid_strategy"

    def test_fabric_commands_http_error(self, server: FabricMCP) -> None:
        """Test handling of HTTP errors from Fabric API."""
        with patch("fabric_mcp.core.FabricApiClient") as mock_client_class:
            # Setup mock client to raise HTTPStatusError
            mock_client = Mock()
            mock_response = Mock()
            mock_response.status_code = 500
            mock_response.text = "Internal Server Error"
            http_error = httpx.HTTPStatusError(
                "Server error", request=Mock(), response=mock_response
            )
            mock_client.get.side_effect = http_error
            mock_client_class.return_value = mock_client

            # Call should raise McpError
            with pytest.raises(McpError) as exc_info:
                server.fabric_list_strategies()

            # Verify error details
            assert_mcp_error(
                exc_info,
                expected_code=-32603,  # Internal error (HTTP -> 32603)
                expected_message_contains="Fabric API error",
            )

            mock_response.text = "open /some/path/no such file or directory"
            # Call should raise McpError
            with pytest.raises(McpError) as exc_info:
                server.fabric_get_pattern_details("non_existent_pattern")
            assert_mcp_error(
                exc_info,
                expected_code=-32602,
                expected_message_contains="Pattern 'non_existent_pattern' not found",
            )

            # Verify API call was attempted
            assert mock_client.get.call_count == 2
            assert mock_client.close.call_count == 2

    def test_fabric_list_strategies_request_error(self, server: FabricMCP) -> None:
        """Test handling of request errors (network issues)."""
        with patch("fabric_mcp.core.FabricApiClient") as mock_client_class:
            # Setup mock client to raise RequestError
            mock_client = Mock()
            request_error = httpx.RequestError("Connection failed")
            mock_client.get.side_effect = request_error
            mock_client_class.return_value = mock_client

            # Call should raise McpError
            with pytest.raises(McpError) as exc_info:
                server.fabric_list_strategies()

            # Verify error details
            assert_mcp_error(
                exc_info,
                expected_code=-32603,  # Internal error (network issue)
                expected_message_contains="Failed to connect to Fabric API",
            )

            # Verify API call was attempted
            mock_client.get.assert_called_once_with("/strategies")
            mock_client.close.assert_called_once()

    def test_fabric_list_strategies_json_decode_error(self, server: FabricMCP) -> None:
        """Test handling of JSON decode errors."""
        with patch("fabric_mcp.core.FabricApiClient") as mock_client_class:
            # Setup mock client to raise JSON decode error
            mock_client = Mock()
            mock_response = Mock()
            json_error = json.JSONDecodeError("Expecting value", "doc", 0)
            mock_response.json.side_effect = json_error
            mock_client.get.return_value = mock_response
            mock_client_class.return_value = mock_client

            # Call should raise McpError
            with pytest.raises(McpError) as exc_info:
                server.fabric_list_strategies()

            # Verify error details
            assert_mcp_error(
                exc_info,
                expected_code=-32603,  # Internal error
                expected_message_contains=(
                    "Unexpected error during retrieving strategies"
                ),
            )

            # Verify API call was made
            mock_client.get.assert_called_once_with("/strategies")
            mock_client.close.assert_called_once()

    def test_fabric_list_strategies_unexpected_error(self, server: FabricMCP) -> None:
        """Test handling of unexpected errors."""
        with patch("fabric_mcp.core.FabricApiClient") as mock_client_class:
            # Setup mock client to raise unexpected error
            mock_client = Mock()
            mock_client.get.side_effect = RuntimeError("Unexpected error")
            mock_client_class.return_value = mock_client

            # Call should raise McpError
            with pytest.raises(McpError) as exc_info:
                server.fabric_list_strategies()

            # Verify error details
            assert_mcp_error(
                exc_info,
                expected_code=-32603,  # Internal error
                expected_message_contains=(
                    "Unexpected error during retrieving strategies"
                ),
            )

            # Verify API call was attempted
            mock_client.get.assert_called_once_with("/strategies")
            mock_client.close.assert_called_once()
