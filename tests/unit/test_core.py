"""Test core functionality of fabric-mcp"""

import logging
import subprocess
import sys
from asyncio.exceptions import CancelledError
from collections.abc import Callable
from typing import Any
from unittest.mock import Mock, patch

import pytest
from anyio import WouldBlock
from fastmcp import FastMCP

from fabric_mcp import __version__
from fabric_mcp.core import FabricMCP
from tests.shared.fabric_api_mocks import (
    FabricApiMockBuilder,
    mock_fabric_api_client,
)
from tests.shared.mocking_utils import COMMON_PATTERN_LIST


def test_cli_version():
    """Test the --version flag of the CLI."""
    command = [sys.executable, "-m", "fabric_mcp.cli", "--version"]
    result = subprocess.run(command, capture_output=True, text=True, check=False)

    # click --version action prints to stdout and exits with 0
    assert result.returncode == 0
    assert result.stderr == ""
    expected_output = f"fabric-mcp, version {__version__}\n"
    assert result.stdout == expected_output


@pytest.fixture(name="server_instance")  # Renamed fixture
def server_instance_fixture() -> FabricMCP:
    """Fixture to create a FabricMCPServer instance."""
    return FabricMCP(log_level="DEBUG")


def test_server_initialization(server_instance: FabricMCP):
    """Test the initialization of the FabricMCPServer."""
    assert isinstance(server_instance.mcp, FastMCP)
    assert server_instance.mcp.name == f"Fabric MCP v{__version__}"
    assert isinstance(server_instance.logger, logging.Logger)
    # Check if log level propagates (Note: FastMCP handles its own logger setup)
    # We check the logger passed during init, FastMCP might configure differently
    # assert server_instance.logger.level == logging.DEBUG


def test_stdio_method_runs_mcp(server_instance: FabricMCP):
    """Test that the stdio method calls mcp.run()."""
    with patch.object(server_instance.mcp, "run") as mock_run:
        server_instance.stdio()
        mock_run.assert_called_once()


def test_stdio_method_handles_keyboard_interrupt(
    server_instance: FabricMCP,
    caplog: pytest.LogCaptureFixture,
):
    """Test that stdio handles KeyboardInterrupt gracefully."""
    with patch.object(server_instance.mcp, "run", side_effect=KeyboardInterrupt):
        with caplog.at_level(logging.INFO):
            server_instance.stdio()
    assert "Server stopped by user." in caplog.text


def test_stdio_method_handles_cancelled_error(
    server_instance: FabricMCP,
    caplog: pytest.LogCaptureFixture,
):
    """Test that stdio handles CancelledError gracefully."""
    with patch.object(server_instance.mcp, "run", side_effect=CancelledError):
        with caplog.at_level(logging.INFO):
            server_instance.stdio()
    assert "Server stopped by user." in caplog.text


def test_stdio_method_handles_would_block(
    server_instance: FabricMCP,
    caplog: pytest.LogCaptureFixture,
):
    """Test that stdio handles WouldBlock gracefully."""
    with patch.object(server_instance.mcp, "run", side_effect=WouldBlock):
        with caplog.at_level(logging.INFO):
            server_instance.stdio()
    assert "Server stopped by user." in caplog.text


def test_server_initialization_with_default_log_level():
    """Test server initialization with default log level."""
    server = FabricMCP()
    assert server.log_level == "INFO"


def test_server_initialization_with_custom_log_level():
    """Test server initialization with custom log level."""
    server = FabricMCP(log_level="ERROR")
    assert server.log_level == "ERROR"


def test_fabric_mcp_tools_registration():
    """Test that tools are properly registered with the FastMCP instance."""
    server = FabricMCP()

    # Check that tools are available through the mcp instance
    # Note: The exact way to check registered tools may depend on FastMCP's API
    # This is a basic check to ensure the tools list is populated
    assert hasattr(server, "_FabricMCP__tools")
    assert len(getattr(server, "_FabricMCP__tools")) == 6


def test_tool_registration_coverage():
    """Test that all tools are properly registered and accessible."""
    server = FabricMCP(log_level="DEBUG")

    # Check that the tools are registered by accessing them
    tools: list[Callable[..., Any]] = getattr(server, "_FabricMCP__tools")
    assert len(tools) == 6

    _test_list_patterns_tool(tools[0])
    _test_get_pattern_details_tool(tools[1])
    _test_run_pattern_tool(tools[2])
    _test_list_models_tool(tools[3])
    _test_list_strategies_tool(tools[4])
    _test_get_configuration_tool(tools[5])


def _test_list_patterns_tool(fabric_list_patterns: Callable[..., Any]) -> None:
    # Test fabric_list_patterns with new shared utilities
    builder = FabricApiMockBuilder().with_successful_pattern_list(COMMON_PATTERN_LIST)
    with mock_fabric_api_client(builder):
        patterns_result: list[str] = fabric_list_patterns()
        assert isinstance(patterns_result, list)
        assert len(patterns_result) == 3


def _test_get_pattern_details_tool(
    fabric_get_pattern_details: Callable[..., Any],
) -> None:
    # Test fabric_get_pattern_details with new shared utilities
    builder = FabricApiMockBuilder().with_successful_pattern_details(
        "test_pattern", "Test pattern description", "# Test pattern system prompt"
    )
    with mock_fabric_api_client(builder):
        pattern_details_result: dict[str, str] = fabric_get_pattern_details(
            "test_pattern"
        )
        assert isinstance(pattern_details_result, dict)
        assert "name" in pattern_details_result
        assert "description" in pattern_details_result
        assert "system_prompt" in pattern_details_result
        assert pattern_details_result["name"] == "test_pattern"
        assert pattern_details_result["description"] == "Test pattern description"
        assert pattern_details_result["system_prompt"] == "# Test pattern system prompt"


def _test_run_pattern_tool(fabric_run_pattern: Callable[..., Any]) -> None:
    # Test fabric_run_pattern with new shared utilities
    builder = FabricApiMockBuilder().with_successful_sse("Hello, World!")

    with mock_fabric_api_client(builder) as mock_api_client:
        run_pattern_result = fabric_run_pattern("test_pattern", "test_input")
        assert isinstance(run_pattern_result, dict)
        assert "output_format" in run_pattern_result
        assert "output_text" in run_pattern_result
        assert run_pattern_result["output_text"] == "Hello, World!"
        assert run_pattern_result["output_format"] == "text"
        mock_api_client.close.assert_called_once()


def _test_list_models_tool(
    fabric_list_models: Callable[..., Any],
) -> None:
    models_result = fabric_list_models()
    assert isinstance(models_result, dict)
    assert "models" in models_result
    assert "vendors" in models_result


def _test_list_strategies_tool(
    fabric_list_strategies: Callable[..., Any],
) -> None:
    strategies_result = fabric_list_strategies()
    assert isinstance(strategies_result, dict)
    assert "strategies" in strategies_result


def _test_get_configuration_tool(
    fabric_get_configuration: Callable[..., Any],
) -> None:
    config_result = fabric_get_configuration()
    assert isinstance(config_result, dict)
    assert "openai_api_key" in config_result


def test_http_streamable_method_runs_mcp(server_instance: FabricMCP):
    """Test that the http_streamable method calls mcp.run() with streamable-http."""
    with patch.object(server_instance.mcp, "run") as mock_run:
        # Mock run to avoid actually starting the server
        mock_run.return_value = None

        # Test with default parameters
        server_instance.http_streamable()

        # Verify mcp.run was called with streamable-http transport and defaults
        mock_run.assert_called_once_with(
            transport="streamable-http",
            host="127.0.0.1",
            port=8000,
            path="/message",
        )


def test_http_streamable_method_with_custom_config(server_instance: FabricMCP):
    """Test that the http_streamable method calls mcp.run() with custom config."""
    with patch.object(server_instance.mcp, "run") as mock_run:
        # Mock run to avoid actually starting the server
        mock_run.return_value = None

        # Test with custom parameters
        server_instance.http_streamable(host="0.0.0.0", port=9000, mcp_path="/api/mcp")

        # Verify mcp.run was called with streamable-http transport and custom config
        mock_run.assert_called_once_with(
            transport="streamable-http",
            host="0.0.0.0",
            port=9000,
            path="/api/mcp",
        )


def test_http_streamable_method_handles_keyboard_interrupt(server_instance: FabricMCP):
    """Test that the http_streamable method handles KeyboardInterrupt gracefully."""
    with patch.object(server_instance.mcp, "run") as mock_run:
        mock_run.side_effect = KeyboardInterrupt

        # Should not raise exception
        server_instance.http_streamable()

        mock_run.assert_called_once()


def test_http_streamable_method_handles_cancelled_error(server_instance: FabricMCP):
    """Test that the http_streamable method handles CancelledError gracefully."""
    with patch.object(server_instance.mcp, "run") as mock_run:
        mock_run.side_effect = CancelledError

        # Should not raise exception
        server_instance.http_streamable()

        mock_run.assert_called_once()


def test_http_streamable_method_handles_would_block(server_instance: FabricMCP):
    """Test that the http_streamable method handles WouldBlock gracefully."""
    with patch.object(server_instance.mcp, "run") as mock_run:
        mock_run.side_effect = WouldBlock

        # Should not raise exception
        server_instance.http_streamable()

        mock_run.assert_called_once()


def test_sse_method_runs_mcp(server_instance: FabricMCP):
    """Test that the sse method calls mcp.run() with sse transport."""
    with patch.object(server_instance.mcp, "run") as mock_run:
        # Mock run to avoid actually starting the server
        mock_run.return_value = None

        # Test with default parameters
        server_instance.sse()

        # Verify mcp.run was called with sse transport and defaults
        mock_run.assert_called_once_with(
            transport="sse",
            host="127.0.0.1",
            port=8000,
            path="/sse",
        )


def test_sse_method_with_custom_config(server_instance: FabricMCP):
    """Test that the sse method calls mcp.run() with custom config."""
    with patch.object(server_instance.mcp, "run") as mock_run:
        # Mock run to avoid actually starting the server
        mock_run.return_value = None

        # Test with custom parameters
        server_instance.sse(host="0.0.0.0", port=9000, path="/custom-sse")

        # Verify mcp.run was called with sse transport and custom config
        mock_run.assert_called_once_with(
            transport="sse",
            host="0.0.0.0",
            port=9000,
            path="/custom-sse",
        )


def test_sse_method_handles_keyboard_interrupt(
    server_instance: FabricMCP,
    caplog: pytest.LogCaptureFixture,
):
    """Test that the sse method handles KeyboardInterrupt gracefully."""
    with patch.object(server_instance.mcp, "run") as mock_run:
        mock_run.side_effect = KeyboardInterrupt

        with caplog.at_level(logging.DEBUG):
            server_instance.sse()

        mock_run.assert_called_once()
        assert "Exception details: KeyboardInterrupt:" in caplog.text
        assert "Server stopped by user." in caplog.text


def test_sse_method_handles_cancelled_error(
    server_instance: FabricMCP,
    caplog: pytest.LogCaptureFixture,
):
    """Test that the sse method handles CancelledError gracefully."""
    with patch.object(server_instance.mcp, "run") as mock_run:
        mock_run.side_effect = CancelledError

        with caplog.at_level(logging.DEBUG):
            server_instance.sse()

        mock_run.assert_called_once()
        assert "Exception details: CancelledError:" in caplog.text
        assert "Server stopped by user." in caplog.text


def test_sse_method_handles_would_block(
    server_instance: FabricMCP,
    caplog: pytest.LogCaptureFixture,
):
    """Test that the sse method handles WouldBlock gracefully."""
    with patch.object(server_instance.mcp, "run") as mock_run:
        mock_run.side_effect = WouldBlock

        with caplog.at_level(logging.DEBUG):
            server_instance.sse()

        mock_run.assert_called_once()
        assert "Exception details: WouldBlock:" in caplog.text
        assert "Server stopped by user." in caplog.text


def test_server_initialization_with_default_config_logging():
    """Test server initialization logs different default config scenarios."""
    # Test case 1: Both model and vendor present
    with patch("fabric_mcp.core.get_default_model", return_value=("gpt-4", "openai")):
        with patch("fabric_mcp.core.logging") as mock_logging:
            mock_logger = Mock()
            mock_logging.getLogger.return_value = mock_logger

            FabricMCP(log_level="DEBUG")
            mock_logger.info.assert_called_with(
                "Loaded default model configuration: %s (%s)", "gpt-4", "openai"
            )

    # Test case 2: Only model present
    with patch("fabric_mcp.core.get_default_model", return_value=("gpt-4", None)):
        with patch("fabric_mcp.core.logging") as mock_logging:
            mock_logger = Mock()
            mock_logging.getLogger.return_value = mock_logger

            FabricMCP(log_level="DEBUG")
            mock_logger.info.assert_called_with(
                "Loaded ONLY default model: %s (no vendor)", "gpt-4"
            )

    # Test case 3: Only vendor present
    with patch("fabric_mcp.core.get_default_model", return_value=(None, "openai")):
        with patch("fabric_mcp.core.logging") as mock_logging:
            mock_logger = Mock()
            mock_logging.getLogger.return_value = mock_logger

            FabricMCP(log_level="DEBUG")
            mock_logger.info.assert_called_with(
                "Loaded ONLY default vendor: %s (no model)", "openai"
            )

    # Test case 4: Neither present
    with patch("fabric_mcp.core.get_default_model", return_value=(None, None)):
        with patch("fabric_mcp.core.logging") as mock_logging:
            mock_logger = Mock()
            mock_logging.getLogger.return_value = mock_logger

            FabricMCP(log_level="DEBUG")
            mock_logger.info.assert_called_with("No default model configuration found")


def test_server_initialization_handles_config_load_error():
    """Test server initialization handles errors loading default config."""
    error = OSError("File not found")
    with patch("fabric_mcp.core.get_default_model", side_effect=error):
        with patch("fabric_mcp.core.logging") as mock_logging:
            mock_logger = Mock()
            mock_logging.getLogger.return_value = mock_logger

            server = FabricMCP(log_level="DEBUG")

            mock_logger.warning.assert_called_with(
                "Failed to load default model configuration: %s. "
                "Pattern execution will use hardcoded defaults.",
                error,
            )
        # Verify server still initializes with None defaults
        assert server.get_default_model_config() == (None, None)


def test_get_default_model_config_method():
    """Test the public getter for default model configuration."""
    with patch(
        "fabric_mcp.core.get_default_model", return_value=("claude-3", "anthropic")
    ):
        server = FabricMCP()
        model, vendor = server.get_default_model_config()
        assert model == "claude-3"
        assert vendor == "anthropic"
