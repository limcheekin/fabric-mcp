"""CLI entry point for fabric-mcp."""

from dataclasses import dataclass
from typing import Any

import click

from fabric_mcp import __version__

from .core import DEFAULT_MCP_HTTP_PATH, FabricMCP
from .utils import Log


@dataclass
class ServerConfig:
    """Configuration for the MCP server."""

    transport: str
    host: str
    port: int
    mcp_path: str
    log_level: str


def validate_transport_specific_option(
    ctx: click.Context, param: click.Parameter, value: Any, valid_transports: list[str]
) -> Any:
    """Validate that transport-specific options are only used with valid transports."""
    transport = ctx.params.get("transport")
    if (
        transport not in valid_transports
        and param.name is not None
        and ctx.get_parameter_source(param.name)
        == click.core.ParameterSource.COMMANDLINE
    ):
        transports_str = " or ".join(f"--transport {t}" for t in valid_transports)
        raise click.UsageError(f"{param.opts[0]} is only valid with {transports_str}")
    return value


def validate_http_options(
    ctx: click.Context, param: click.Parameter, value: Any
) -> Any:
    """Validate that HTTP-specific options are only used with HTTP transport."""
    return validate_transport_specific_option(ctx, param, value, ["http"])


def validate_server_options(
    ctx: click.Context, param: click.Parameter, value: Any
) -> Any:
    """Validate that server options are only used with HTTP transport."""
    return validate_transport_specific_option(ctx, param, value, ["http"])


@click.command()
@click.option(
    "--transport",
    type=click.Choice(["stdio", "http"]),
    required=True,
    help="Transport mechanism to use for the MCP server.",
)
@click.option(
    "--host",
    default="127.0.0.1",
    show_default=True,
    callback=validate_server_options,
    help="Host to bind the server to (HTTP transport only).",
)
@click.option(
    "--port",
    default=8000,
    type=int,
    show_default=True,
    callback=validate_server_options,
    help="Port to bind the server to (HTTP transport only).",
)
@click.option(
    "--mcp-path",
    default=DEFAULT_MCP_HTTP_PATH,
    show_default=True,
    callback=validate_http_options,
    help="MCP endpoint path (HTTP transport only).",
)
@click.option(
    "-l",
    "--log-level",
    type=click.Choice(
        ["debug", "info", "warning", "error", "critical"], case_sensitive=False
    ),
    default="info",
    show_default=True,
    help="Set the logging level.",
)
@click.version_option(version=__version__, prog_name="fabric-mcp")
def main(  # pylint: disable=too-many-arguments,too-many-positional-arguments
    transport: str,
    host: str,
    port: int,
    mcp_path: str,
    log_level: str,
) -> None:
    """A Model Context Protocol server for Fabric AI."""
    config = ServerConfig(
        transport=transport,
        host=host,
        port=port,
        mcp_path=mcp_path,
        log_level=log_level,
    )
    _run_server(config)


def _run_server(config: ServerConfig) -> None:
    """Run the MCP server with the given configuration."""
    log = Log(config.log_level)
    logger = log.logger

    fabric_mcp = FabricMCP(config.log_level)

    if config.transport == "stdio":
        logger.info(
            "Starting server with stdio transport (log level: %s)", log.level_name
        )
        fabric_mcp.stdio()
    elif config.transport == "http":
        logger.info(
            "Starting server with streamable HTTP transport at "
            "http://%s:%d%s (log level: %s)",
            config.host,
            config.port,
            config.mcp_path,
            log.level_name,
        )
        fabric_mcp.http_streamable(
            host=config.host, port=config.port, mcp_path=config.mcp_path
        )
    logger.info("Server stopped.")


if __name__ == "__main__":
    main()  # pylint: disable=no-value-for-parameter
