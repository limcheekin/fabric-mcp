"""Test utilities for managing the mock Fabric API server.

This module provides utilities to start and stop the mock Fabric API server
during integration tests, ensuring that tests have a reliable API to connect to.
"""

import logging
import multiprocessing
import os
import signal
import time
from collections.abc import AsyncGenerator, Generator
from contextlib import asynccontextmanager
from types import TracebackType

import pytest
import uvicorn

from ..port_utils import find_free_port, is_port_in_use
from .server import app

logger = logging.getLogger(__name__)


def wait_for_server(host: str, port: int, timeout: float = 10.0) -> bool:
    """Wait for server to be ready to accept connections."""
    start_time = time.time()
    while time.time() - start_time < timeout:
        if is_port_in_use(port, host):
            return True
        time.sleep(0.1)
    return False


def run_mock_server_process(host: str, port: int) -> None:
    """Run the mock server in a separate process."""

    # Configure logging for the subprocess
    logging.basicConfig(
        level=logging.INFO,
        format="[Mock API] %(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    # Configure uvicorn
    config = uvicorn.Config(
        app=app,
        host=host,
        port=port,
        log_level="info",
        access_log=False,  # Reduce noise in tests
        loop="asyncio",
    )

    server = uvicorn.Server(config)

    # Handle shutdown gracefully
    def signal_handler(signum: int, _frame) -> None:  # type: ignore[misc]
        logger.info("Mock server received signal %s, shutting down...", signum)
        server.should_exit = True

    signal.signal(signal.SIGINT, signal_handler)  # type: ignore[arg-type]
    signal.signal(signal.SIGTERM, signal_handler)  # type: ignore[arg-type]

    # Run the server
    logger.info("Starting mock Fabric API server on %s:%s", host, port)
    server.run()


class MockFabricAPIServer:
    """Context manager for running a mock Fabric API server during tests."""

    def __init__(self, host: str = "127.0.0.1", port: int | None = None):
        """Initialize the mock server manager.

        Args:
            host: Host to bind the server to
            port: Port to bind the server to. If None, a free port will be found.
        """
        self.host = host
        self.port = port or find_free_port()
        self.process: multiprocessing.Process | None = None

    def start(self) -> None:
        """Start the mock server in a background process."""
        if self.process is not None:
            raise RuntimeError("Mock server is already running")

        logger.info("Starting mock Fabric API server on %s:%s", self.host, self.port)

        # Start server in separate process
        self.process = multiprocessing.Process(
            target=run_mock_server_process, args=(self.host, self.port), daemon=True
        )
        self.process.start()
        # Wait for server to be ready
        if not wait_for_server(self.host, self.port, timeout=5.0):
            self.stop()
            raise RuntimeError(
                f"Mock server failed to start on {self.host}:{self.port}"
            )

        logger.info(
            "Mock Fabric API server is ready at http://%s:%s", self.host, self.port
        )

    def stop(self) -> None:
        """Stop the mock server."""
        if self.process is None:
            return

        logger.info("Stopping mock Fabric API server...")

        # Try graceful shutdown first
        if self.process.is_alive():
            self.process.terminate()
            self.process.join(timeout=2.0)

        # Force kill if still alive
        if self.process.is_alive():
            logger.warning("Force killing mock server process")
            self.process.kill()
            self.process.join(timeout=2.0)

        self.process = None
        logger.info("Mock Fabric API server stopped")

    def __enter__(self) -> "MockFabricAPIServer":
        """Context manager entry."""
        self.start()
        return self

    def __exit__(
        self,
        _exc_type: type[BaseException] | None,
        _exc_val: BaseException | None,
        _exc_tb: TracebackType | None,
    ) -> None:
        """Context manager exit."""
        self.stop()

    @property
    def base_url(self) -> str:
        """Get the base URL for the mock server."""
        return f"http://{self.host}:{self.port}"


@asynccontextmanager
async def mock_fabric_api_server(
    host: str = "127.0.0.1", port: int | None = None
) -> AsyncGenerator[MockFabricAPIServer, None]:
    """Async context manager for mock Fabric API server.

    Args:
        host: Host to bind the server to
        port: Port to bind the server to. If None, a free port will be found.

    Yields:
        MockFabricAPIServer instance with the server running
    """
    server = MockFabricAPIServer(host, port)
    try:
        server.start()
        yield server
    finally:
        server.stop()


def setup_mock_fabric_api_env(server: MockFabricAPIServer) -> dict[str, str]:
    """Set up environment variables to point to the mock server.

    Args:
        server: Running mock server instance

    Returns:
        Dictionary of environment variables to set
    """
    return {
        "FABRIC_BASE_URL": server.base_url,
        "FABRIC_API_KEY": "",  # Mock server doesn't require authentication
    }


# Pytest fixtures for easy use in tests
@pytest.fixture(scope="session", name="mock_fabric_api_server")
def fabric_api_server_fixture() -> Generator[MockFabricAPIServer, None, None]:
    """Pytest fixture for mock Fabric API server."""
    with MockFabricAPIServer() as server:
        # Set environment variables for this test
        old_env = os.environ.copy()
        os.environ.update(setup_mock_fabric_api_env(server))

        try:
            yield server
        finally:
            # Restore original environment
            os.environ.clear()
            os.environ.update(old_env)
