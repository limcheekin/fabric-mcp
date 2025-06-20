"""Tests for fabric_run_pattern tool input and parameter validation.

This module tests input validation, parameter validation, and edge cases
for the fabric_run_pattern tool, including temperature, top_p, penalty parameters,
and model/strategy name validation.
"""

from collections.abc import Callable
from typing import Any

import pytest
from mcp import McpError
from mcp.types import INVALID_PARAMS

from tests.shared.fabric_api_mocks import (
    FabricApiMockBuilder,
    assert_mcp_error,
    mock_fabric_api_client,
)
from tests.unit.test_fabric_run_pattern_base import (
    COMMON_PARAMS_FULL,
    COMMON_PARAMS_PARTIAL,
    TestFabricRunPatternFixtureBase,
)


class TestFabricRunPatternInputValidation(TestFabricRunPatternFixtureBase):
    """Test cases for fabric_run_pattern tool input validation and edge cases."""

    def test_empty_pattern_name_validation(
        self, fabric_run_pattern_tool: Callable[..., Any]
    ) -> None:
        """Test that empty pattern name raises McpError."""
        # Test empty string
        with pytest.raises(
            McpError, match="pattern_name is required and cannot be empty"
        ):
            fabric_run_pattern_tool("", "test input")

        # Test whitespace-only string
        with pytest.raises(
            McpError, match="pattern_name is required and cannot be empty"
        ):
            fabric_run_pattern_tool("   ", "test input")

        # Test None (though this might be caught by type system)
        with pytest.raises(
            McpError, match="pattern_name is required and cannot be empty"
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


class TestFabricRunPatternParameterValidation(TestFabricRunPatternFixtureBase):
    """Test cases for fabric_run_pattern parameter validation (Story 3.3)."""

    def test_temperature_validation_valid_ranges(
        self, fabric_run_pattern_tool: Callable[..., Any]
    ) -> None:
        """Test temperature parameter validation with valid ranges."""
        builder = FabricApiMockBuilder().with_successful_sse("Valid temperature test")

        with mock_fabric_api_client(builder):
            # Test minimum valid temperature
            result = fabric_run_pattern_tool(
                "test_pattern", "test input", temperature=0.0
            )
            assert result["output_text"] == "Valid temperature test"

            # Test maximum valid temperature
            result = fabric_run_pattern_tool(
                "test_pattern", "test input", temperature=2.0
            )
            assert result["output_text"] == "Valid temperature test"

            # Test typical temperature
            result = fabric_run_pattern_tool(
                "test_pattern", "test input", temperature=0.7
            )
            assert result["output_text"] == "Valid temperature test"

    def test_temperature_validation_invalid_ranges(
        self, fabric_run_pattern_tool: Callable[..., Any]
    ) -> None:
        """Test temperature parameter validation with invalid ranges."""
        # Test temperature too low
        with pytest.raises(McpError) as exc_info:
            fabric_run_pattern_tool("test_pattern", "test input", temperature=-0.1)
        assert_mcp_error(
            exc_info, INVALID_PARAMS, "temperature must be a number between 0.0 and 2.0"
        )

        # Test temperature too high
        with pytest.raises(McpError) as exc_info:
            fabric_run_pattern_tool("test_pattern", "test input", temperature=2.1)
        assert_mcp_error(
            exc_info, INVALID_PARAMS, "temperature must be a number between 0.0 and 2.0"
        )

        # Test invalid type
        with pytest.raises(McpError) as exc_info:
            fabric_run_pattern_tool("test_pattern", "test input", temperature="invalid")
        assert_mcp_error(
            exc_info, INVALID_PARAMS, "temperature must be a number between 0.0 and 2.0"
        )

    def test_top_p_validation_valid_ranges(
        self, fabric_run_pattern_tool: Callable[..., Any]
    ) -> None:
        """Test top_p parameter validation with valid ranges."""
        builder = FabricApiMockBuilder().with_successful_sse("Valid top_p test")

        with mock_fabric_api_client(builder):
            # Test minimum valid top_p
            result = fabric_run_pattern_tool("test_pattern", "test input", top_p=0.0)
            assert result["output_text"] == "Valid top_p test"

            # Test maximum valid top_p
            result = fabric_run_pattern_tool("test_pattern", "test input", top_p=1.0)
            assert result["output_text"] == "Valid top_p test"

    def test_top_p_validation_invalid_ranges(
        self, fabric_run_pattern_tool: Callable[..., Any]
    ) -> None:
        """Test top_p parameter validation with invalid ranges."""
        # Test top_p too low
        with pytest.raises(McpError) as exc_info:
            fabric_run_pattern_tool("test_pattern", "test input", top_p=-0.1)
        assert_mcp_error(
            exc_info, INVALID_PARAMS, "top_p must be a number between 0.0 and 1.0"
        )

        # Test top_p too high
        with pytest.raises(McpError) as exc_info:
            fabric_run_pattern_tool("test_pattern", "test input", top_p=1.1)
        assert_mcp_error(
            exc_info, INVALID_PARAMS, "top_p must be a number between 0.0 and 1.0"
        )

    def test_penalty_validation_valid_ranges(
        self, fabric_run_pattern_tool: Callable[..., Any]
    ) -> None:
        """Test penalty parameter validation with valid ranges."""
        builder = FabricApiMockBuilder().with_successful_sse("Valid penalty test")

        with mock_fabric_api_client(builder):
            # Test presence_penalty valid range
            result = fabric_run_pattern_tool(
                "test_pattern", "test input", presence_penalty=-2.0
            )
            assert result["output_text"] == "Valid penalty test"

            result = fabric_run_pattern_tool(
                "test_pattern", "test input", presence_penalty=2.0
            )
            assert result["output_text"] == "Valid penalty test"

            # Test frequency_penalty valid range
            result = fabric_run_pattern_tool(
                "test_pattern", "test input", frequency_penalty=-2.0
            )
            assert result["output_text"] == "Valid penalty test"

            result = fabric_run_pattern_tool(
                "test_pattern", "test input", frequency_penalty=2.0
            )
            assert result["output_text"] == "Valid penalty test"

    def test_penalty_validation_invalid_ranges(
        self, fabric_run_pattern_tool: Callable[..., Any]
    ) -> None:
        """Test penalty parameter validation with invalid ranges."""
        # Test presence_penalty too low
        with pytest.raises(McpError) as exc_info:
            fabric_run_pattern_tool("test_pattern", "test input", presence_penalty=-2.1)
        assert_mcp_error(
            exc_info,
            INVALID_PARAMS,
            "presence_penalty must be a number between -2.0 and 2.0",
        )

        # Test presence_penalty too high
        with pytest.raises(McpError) as exc_info:
            fabric_run_pattern_tool("test_pattern", "test input", presence_penalty=2.1)
        assert_mcp_error(
            exc_info,
            INVALID_PARAMS,
            "presence_penalty must be a number between -2.0 and 2.0",
        )

        # Test frequency_penalty too low
        with pytest.raises(McpError) as exc_info:
            fabric_run_pattern_tool(
                "test_pattern", "test input", frequency_penalty=-2.1
            )
        assert_mcp_error(
            exc_info,
            INVALID_PARAMS,
            "frequency_penalty must be a number between -2.0 and 2.0",
        )

        # Test frequency_penalty too high
        with pytest.raises(McpError) as exc_info:
            fabric_run_pattern_tool("test_pattern", "test input", frequency_penalty=2.1)
        assert_mcp_error(
            exc_info,
            INVALID_PARAMS,
            "frequency_penalty must be a number between -2.0 and 2.0",
        )

    def test_model_name_validation(
        self, fabric_run_pattern_tool: Callable[..., Any]
    ) -> None:
        """Test model_name parameter validation."""
        builder = FabricApiMockBuilder().with_successful_sse("Valid model test")

        with mock_fabric_api_client(builder):
            # Test valid model names
            result = fabric_run_pattern_tool(
                "test_pattern", "test input", model_name="gpt-4"
            )
            assert result["output_text"] == "Valid model test"

            result = fabric_run_pattern_tool(
                "test_pattern", "test input", model_name="claude-3-opus"
            )
            assert result["output_text"] == "Valid model test"

        # Test invalid model names
        with pytest.raises(McpError) as exc_info:
            fabric_run_pattern_tool("test_pattern", "test input", model_name="")
        assert_mcp_error(
            exc_info, INVALID_PARAMS, "model_name must be a non-empty string"
        )

        with pytest.raises(McpError) as exc_info:
            fabric_run_pattern_tool("test_pattern", "test input", model_name="   ")
        assert_mcp_error(
            exc_info, INVALID_PARAMS, "model_name must be a non-empty string"
        )

    def test_strategy_name_validation(
        self, fabric_run_pattern_tool: Callable[..., Any]
    ) -> None:
        """Test strategy_name parameter validation."""
        builder = FabricApiMockBuilder().with_successful_sse("Valid strategy test")

        with mock_fabric_api_client(builder):
            # Test valid strategy names
            result = fabric_run_pattern_tool(
                "test_pattern", "test input", strategy_name="creative"
            )
            assert result["output_text"] == "Valid strategy test"

            result = fabric_run_pattern_tool(
                "test_pattern", "test input", strategy_name="analytical"
            )
            assert result["output_text"] == "Valid strategy test"

        # Test invalid strategy names
        with pytest.raises(McpError) as exc_info:
            fabric_run_pattern_tool("test_pattern", "test input", strategy_name="")
        assert_mcp_error(
            exc_info, INVALID_PARAMS, "strategy_name must be a non-empty string"
        )

        with pytest.raises(McpError) as exc_info:
            fabric_run_pattern_tool("test_pattern", "test input", strategy_name="   ")
        assert_mcp_error(
            exc_info, INVALID_PARAMS, "strategy_name must be a non-empty string"
        )

    def test_parameter_combinations(
        self, fabric_run_pattern_tool: Callable[..., Any]
    ) -> None:
        """Test multiple parameter combinations work together."""
        builder = FabricApiMockBuilder().with_successful_sse(
            "Parameter combination test"
        )

        with mock_fabric_api_client(builder):
            # Test all parameters together
            result = fabric_run_pattern_tool(
                "test_pattern",
                "test input",
                **COMMON_PARAMS_FULL,
            )
            assert result["output_text"] == "Parameter combination test"

            # Test partial parameter combinations
            result = fabric_run_pattern_tool(
                "test_pattern",
                "test input",
                **COMMON_PARAMS_PARTIAL,
            )
            assert result["output_text"] == "Parameter combination test"
