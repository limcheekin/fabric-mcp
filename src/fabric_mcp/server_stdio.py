"""Fabric MCP server in stdio mode."""

from fabric_mcp.core import FabricMCP
from fabric_mcp.utils import Log

LOG_LEVEL = "DEBUG"

log = Log(LOG_LEVEL)
logger = log.logger

logger.info("Starting server with log level %s", LOG_LEVEL)
fabric_mcp = FabricMCP()

mcp = fabric_mcp
