"""Base test fixtures for fabric_run_pattern tool tests.

This module provides shared test fixtures and base classes used across
all fabric_run_pattern tool test modules.
"""

from collections.abc import Callable
from typing import Any

import pytest_asyncio
from fastmcp.tools import Tool

from tests.shared.fabric_api.base import TestFixturesBase

# Common parameter sets to reduce code duplication
COMMON_PARAMS_FULL = {
    "model_name": "claude-3-opus",
    "temperature": 0.8,
    "top_p": 0.95,
    "presence_penalty": 0.1,
    "frequency_penalty": -0.1,
    "strategy_name": "creative",
}

COMMON_PARAMS_PARTIAL = {
    "model_name": "gpt-4",
    "temperature": 0.3,
    "strategy_name": "analytical",
}


class TestFabricRunPatternFixtureBase(TestFixturesBase):
    """Base test class for fabric_run_pattern tool tests."""

    @pytest_asyncio.fixture
    async def fabric_run_pattern_tool(
        self, mcp_tools: dict[str, Tool]
    ) -> Callable[..., Any]:
        """Get the fabric_run_pattern tool from the server."""
        # fabric_run_pattern is the 3rd tool (index 2)
        return getattr(mcp_tools["fabric_run_pattern"], "fn")
