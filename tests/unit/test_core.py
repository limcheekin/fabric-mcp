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
from tests.shared.mocking_utils import (
    COMMON_PATTERN_DETAILS,
    COMMON_PATTERN_LIST,
    create_fabric_api_mock,
)


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

    # Test each tool to ensure they're callable
    fabric_list_patterns = tools[0]

    # Mock the FabricApiClient for fabric_list_patterns test
    with patch("fabric_mcp.core.FabricApiClient") as mock_api_client_class:
        create_fabric_api_mock(mock_api_client_class).with_successful_response(
            COMMON_PATTERN_LIST
        ).build()

        patterns_result: list[str] = fabric_list_patterns()
        assert isinstance(patterns_result, list)
        assert len(patterns_result) == 3

    fabric_get_pattern_details = tools[1]
    # Mock the FabricApiClient for fabric_get_pattern_details test
    with patch("fabric_mcp.core.FabricApiClient") as mock_api_client_class:
        create_fabric_api_mock(mock_api_client_class).with_successful_response(
            COMMON_PATTERN_DETAILS
        ).build()

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

    fabric_run_pattern = tools[2]
    # Mock the FabricApiClient for fabric_run_pattern test
    with patch("fabric_mcp.core.FabricApiClient") as mock_api_client_class:
        mock_api_client = Mock()
        mock_api_client_class.return_value = mock_api_client

        # Mock SSE response
        mock_response = Mock()
        mock_response.iter_lines.return_value = [
            'data: {"type": "content", "content": "Hello, ", "format": "text"}',
            'data: {"type": "content", "content": "World!", "format": "text"}',
            'data: {"type": "complete"}',
        ]
        mock_api_client.post.return_value = mock_response

        run_pattern_result = fabric_run_pattern("test_pattern", "test_input")
        assert isinstance(run_pattern_result, dict)
        assert "output_format" in run_pattern_result
        assert "output_text" in run_pattern_result
        assert run_pattern_result["output_text"] == "Hello, World!"
        assert run_pattern_result["output_format"] == "text"

    fabric_list_models = tools[3]
    models_result = fabric_list_models()
    assert isinstance(models_result, dict)
    assert "models" in models_result
    assert "vendors" in models_result

    fabric_list_strategies = tools[4]
    strategies_result = fabric_list_strategies()
    assert isinstance(strategies_result, dict)
    assert "strategies" in strategies_result

    fabric_get_configuration = tools[5]
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
