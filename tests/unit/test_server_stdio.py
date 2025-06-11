"""Unit tests for the server_stdio module in fabric_mcp."""

import importlib
import logging

import pytest

# Import the module to test. This will execute the top-level code.
# We need to be careful about side effects, especially logging configuration.
# Using importlib might be an alternative if finer control is needed.
import fabric_mcp.server_stdio as server_stdio_module
from fabric_mcp.core import FabricMCP
from fabric_mcp.utils import Log


def test_log_instance_creation():
    """Test if the Log instance is created correctly."""
    assert isinstance(server_stdio_module.log, Log)
    assert server_stdio_module.log.level_name == server_stdio_module.LOG_LEVEL
    assert server_stdio_module.log.level == Log.log_level(server_stdio_module.LOG_LEVEL)


def test_logger_instance_creation():
    """Test if the logger instance is created and configured."""
    assert isinstance(server_stdio_module.logger, logging.Logger)
    assert server_stdio_module.logger.name == "FabricMCP"


def test_fabric_mcp_server_instance_creation():
    """Test if the FabricMCPServer instance is created correctly."""
    assert isinstance(server_stdio_module.fabric_mcp, FabricMCP)


@pytest.mark.usefixtures("caplog")  # Use caplog fixture to capture logs
def test_initial_log_message(caplog: pytest.LogCaptureFixture):
    """Test if the initial server start message is logged."""
    # Re-import or reload the module within the test if necessary
    # to ensure the log message is captured by caplog for this specific test.
    # This can be complex due to Python's module caching.
    # A simpler approach is to check if the message *was* logged during
    # the initial import.
    # Note: This assumes the test runner captures logs from module import time.

    # Forcing re-import (use with caution):

    with caplog.at_level(logging.INFO):
        importlib.reload(server_stdio_module)

    assert (
        f"Starting server with log level {server_stdio_module.LOG_LEVEL}" in caplog.text
    )
