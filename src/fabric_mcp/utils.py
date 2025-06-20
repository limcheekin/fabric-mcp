"""Utility functions for the fabric_mcp module."""

import logging
import os
from typing import NoReturn

from mcp.shared.exceptions import McpError
from mcp.types import ErrorData
from rich.console import Console
from rich.logging import RichHandler


def raise_mcp_error(e: Exception, code: int, message: str) -> NoReturn:
    """Raise a generic MCP error.

    This function always raises an exception and never returns.
    """
    raise McpError(
        ErrorData(
            code=code,
            message=message,
        )
    ) from e


class Log:
    """
    Custom class to handle logging setup and log levels.

    This class initializes a logger with a specified log level. If no log level is
    provided during initialization, the class attempts to use the `FABRIC_MCP_LOG_LEVEL`
    environment variable as a fallback. If the environment variable is not set, the
    default log level is `INFO`.
    """

    def __init__(self, level: str = ""):
        """Initialize the Log class with a specific log level."""
        level = os.environ.get("FABRIC_MCP_LOG_LEVEL", level) or "INFO"
        self._level_name = level.upper()
        self._level = Log.log_level(self._level_name)

        handler = RichHandler(
            console=Console(stderr=True),
            rich_tracebacks=True,
        )
        formatter = logging.Formatter(
            "%(asctime)s - %(module)s  - %(levelname)s - %(message)s"
        )
        handler.setFormatter(formatter)

        self._logger = logging.getLogger("FabricMCP")
        self._logger.setLevel(self.level_name)

        self.logger.setLevel(self.level_name)

        # Remove any existing handlers to avoid duplicates on reconfiguration
        for handler in self.logger.handlers[:]:
            self.logger.removeHandler(handler)
        self._logger.addHandler(handler)

    @property
    def level_name(self) -> str:
        """Return the log level as a string."""
        return self._level_name

    @property
    def logger(self) -> logging.Logger:
        """Return the logger instance."""
        return self._logger

    @property
    def level(self) -> int:
        """Return the log level as an integer."""
        return self._level

    @staticmethod
    def log_level(level: str) -> int:
        """Convert a string log level to its corresponding integer value.
        Args:
            level (str): The log level as a string (e.g., "DEBUG", "INFO").
        Returns:
            int: The corresponding log level as an integer.
        Raises:
            KeyError: If the provided log level is not valid.
        """
        levels = {
            "DEBUG": logging.DEBUG,
            "INFO": logging.INFO,
            "WARNING": logging.WARNING,
            "ERROR": logging.ERROR,
            "CRITICAL": logging.CRITICAL,
        }
        # Ensure level is uppercase for dictionary lookup
        level_upper = level.upper()
        if level_upper not in levels:
            raise KeyError(
                f"Invalid log level: {level}. Choose from {list(levels.keys())}."
            )
        return levels[level_upper]
