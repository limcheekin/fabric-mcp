"""Additional unit tests for fabric_mcp.cli module."""

from unittest.mock import Mock, patch

from click.testing import CliRunner

from fabric_mcp import __version__
from fabric_mcp.cli import main


class TestCLIMain:
    """Test cases for the main CLI function."""

    def test_version_flag(self):
        """Test --version flag displays version and exits."""
        runner = CliRunner()
        result = runner.invoke(main, ["--version"])

        # Click version option exits with code 0
        assert result.exit_code == 0

        # Check that version was printed to output
        assert f"fabric-mcp, version {__version__}" in result.output

    def test_help_flag(self):
        """Test --help flag displays help and exits."""
        runner = CliRunner()
        result = runner.invoke(main, ["--help"])

        # Click help option exits with code 0
        assert result.exit_code == 0

        # Check that help was printed
        assert "A Model Context Protocol server for Fabric AI" in result.output
        assert "--transport" in result.output
        assert "--log-level" in result.output

    def test_no_args_fails_needing_transport(self):
        """Test that running with no arguments fails due to missing transport."""
        with (
            patch("fabric_mcp.cli.Log") as mock_log_class,
            patch("fabric_mcp.cli.FabricMCP") as mock_fabric_mcp_class,
        ):
            mock_log = Mock()
            mock_log.level_name = "INFO"
            mock_log.logger = Mock()
            mock_log_class.return_value = mock_log

            mock_server = Mock()
            mock_fabric_mcp_class.return_value = mock_server

            runner = CliRunner()
            result = runner.invoke(main, [])

            # Should exit successfully with default stdio transport
            assert result.exit_code != 0
            assert "Missing option '--transport'" in result.stderr

    @patch("fabric_mcp.cli.FabricMCP")
    @patch("fabric_mcp.cli.Log")
    def test_transport_stdio_creates_server_and_runs(
        self, mock_log_class: Mock, mock_fabric_mcp_class: Mock
    ):
        """Test that --transport stdio creates server and runs it."""
        # Setup mocks
        mock_log = Mock()
        mock_log.level_name = "INFO"
        mock_log.logger = Mock()
        mock_log_class.return_value = mock_log

        mock_server = Mock()
        mock_fabric_mcp_class.return_value = mock_server

        runner = CliRunner()
        result = runner.invoke(main, ["--transport", "stdio"])

        # Should exit successfully
        assert result.exit_code == 0

        # Verify Log was created with correct level
        mock_log_class.assert_called_once_with("info")

        # Verify FabricMCP was created
        mock_fabric_mcp_class.assert_called_once()

        # Verify stdio() was called
        mock_server.stdio.assert_called_once()

    @patch("fabric_mcp.cli.FabricMCP")
    @patch("fabric_mcp.cli.Log")
    def test_transport_stdio_with_custom_log_level(
        self, mock_log_class: Mock, mock_fabric_mcp_class: Mock
    ):
        """Test --transport stdio with custom log level."""
        mock_log = Mock()
        mock_log.level_name = "DEBUG"
        mock_log.logger = Mock()
        mock_log_class.return_value = mock_log

        mock_server = Mock()
        mock_fabric_mcp_class.return_value = mock_server

        runner = CliRunner()
        result = runner.invoke(main, ["--transport", "stdio", "--log-level", "debug"])

        assert result.exit_code == 0

        # Verify Log was created with debug level
        mock_log_class.assert_called_once_with("debug")

        # Verify FabricMCP was created
        mock_fabric_mcp_class.assert_called_once()

    @patch("fabric_mcp.cli.FabricMCP")
    @patch("fabric_mcp.cli.Log")
    def test_transport_stdio_with_short_log_level_flag(
        self, mock_log_class: Mock, mock_fabric_mcp_class: Mock
    ):
        """Test --transport stdio with short form -l for log level."""
        mock_log = Mock()
        mock_log.level_name = "ERROR"
        mock_log.logger = Mock()
        mock_log_class.return_value = mock_log

        mock_server = Mock()
        mock_fabric_mcp_class.return_value = mock_server

        runner = CliRunner()
        result = runner.invoke(main, ["--transport", "stdio", "-l", "error"])

        assert result.exit_code == 0
        mock_log_class.assert_called_once_with("error")
        mock_fabric_mcp_class.assert_called_once()

    @patch("fabric_mcp.cli.FabricMCP")
    @patch("fabric_mcp.cli.Log")
    def test_transport_stdio_logs_startup_and_shutdown_messages(
        self, mock_log_class: Mock, mock_fabric_mcp_class: Mock
    ):
        """Test that appropriate log messages are generated."""
        mock_log = Mock()
        mock_log.level_name = "INFO"
        mock_logger = Mock()
        mock_log.logger = mock_logger
        mock_log_class.return_value = mock_log

        mock_server = Mock()
        mock_fabric_mcp_class.return_value = mock_server

        runner = CliRunner()
        result = runner.invoke(main, ["--transport", "stdio"])

        assert result.exit_code == 0

        # Check that startup message was logged
        startup_calls = [
            call
            for call in mock_logger.info.call_args_list
            if "Starting server" in str(call)
        ]
        assert len(startup_calls) == 1
        assert "Starting server with stdio transport" in str(startup_calls[0])
        assert "'INFO'" in str(startup_calls[0])

        # Check that shutdown message was logged
        shutdown_calls = [
            call
            for call in mock_logger.info.call_args_list
            if "Server stopped" in str(call)
        ]
        assert len(shutdown_calls) == 1

    def test_log_level_choices(self):
        """Test that valid log levels are accepted and invalid ones are rejected."""
        valid_levels = ["debug", "info", "warning", "error", "critical"]
        runner = CliRunner()

        for level in valid_levels:
            with patch("fabric_mcp.cli.FabricMCP"):
                with patch("fabric_mcp.cli.Log"):
                    result = runner.invoke(
                        main, ["--transport", "stdio", "--log-level", level]
                    )
                    # Should not raise an exception and exit successfully
                    assert result.exit_code == 0

        # Test invalid log level
        result = runner.invoke(main, ["--transport", "stdio", "--log-level", "invalid"])
        # Click should exit with error for invalid choice
        assert result.exit_code != 0

    def test_default_log_level_is_info(self):
        """Test that default log level is 'info'."""
        with (
            patch("fabric_mcp.cli.Log") as mock_log_class,
            patch("fabric_mcp.cli.FabricMCP") as mock_fabric_mcp_class,
        ):
            mock_log = Mock()
            mock_log.level_name = "INFO"
            mock_log.logger = Mock()
            mock_log_class.return_value = mock_log

            mock_fabric_mcp = Mock()
            mock_fabric_mcp_class.return_value = mock_fabric_mcp

            runner = CliRunner()
            result = runner.invoke(main, ["--transport", "stdio"])

            assert result.exit_code == 0

            # Verify default log level was used
            mock_log_class.assert_called_once_with("info")

    @patch("fabric_mcp.cli.FabricMCP")
    @patch("fabric_mcp.cli.Log")
    def test_transport_http_creates_server_and_runs(
        self, mock_log_class: Mock, mock_fabric_mcp_class: Mock
    ):
        """Test that --transport http creates server and runs it."""
        # Setup mocks
        mock_log = Mock()
        mock_log.level_name = "INFO"
        mock_log.logger = Mock()
        mock_log_class.return_value = mock_log

        mock_server = Mock()
        mock_fabric_mcp_class.return_value = mock_server

        runner = CliRunner()
        result = runner.invoke(main, ["--transport", "http"])

        # Should exit successfully
        assert result.exit_code == 0

        # Verify Log was created with correct level
        mock_log_class.assert_called_once_with("info")

        # Verify FabricMCP was created
        mock_fabric_mcp_class.assert_called_once()

        # Verify http_streamable() was called with defaults
        mock_server.http_streamable.assert_called_once_with(
            host="127.0.0.1", port=8000, mcp_path="/message"
        )

    @patch("fabric_mcp.cli.FabricMCP")
    @patch("fabric_mcp.cli.Log")
    def test_transport_http_with_custom_config(
        self, mock_log_class: Mock, mock_fabric_mcp_class: Mock
    ):
        """Test --transport http with custom host, port, and path."""
        # Setup mocks
        mock_log = Mock()
        mock_log.level_name = "DEBUG"
        mock_log.logger = Mock()
        mock_log_class.return_value = mock_log

        mock_server = Mock()
        mock_fabric_mcp_class.return_value = mock_server

        runner = CliRunner()
        result = runner.invoke(
            main,
            [
                "--transport",
                "http",
                "--host",
                "0.0.0.0",
                "--port",
                "9000",
                "--mcp-path",
                "/api/mcp",
                "--log-level",
                "debug",
            ],
        )

        # Should exit successfully
        assert result.exit_code == 0

        # Verify Log was created with correct level
        mock_log_class.assert_called_once_with("debug")

        # Verify FabricMCP was created
        mock_fabric_mcp_class.assert_called_once()

        # Verify http_streamable() was called with custom config
        mock_server.http_streamable.assert_called_once_with(
            host="0.0.0.0", port=9000, mcp_path="/api/mcp"
        )


class TestCLIValidation:
    """Test cases for CLI argument validation."""

    def test_host_option_rejected_with_stdio_transport(self):
        """Test that --host option is rejected when using stdio transport."""
        runner = CliRunner()
        result = runner.invoke(main, ["--transport", "stdio", "--host", "custom-host"])

        assert result.exit_code == 2
        assert "only valid with --transport http" in result.output

    def test_port_option_rejected_with_stdio_transport(self):
        """Test that --port option is rejected when using stdio transport."""
        runner = CliRunner()
        result = runner.invoke(main, ["--transport", "stdio", "--port", "9000"])

        assert result.exit_code == 2
        assert "only valid with --transport http" in result.output

    def test_mcp_path_option_rejected_with_stdio_transport(self):
        """Test that --mcp-path option is rejected when using stdio transport."""
        runner = CliRunner()
        result = runner.invoke(main, ["--transport", "stdio", "--mcp-path", "/custom"])

        assert result.exit_code == 2
        assert "only valid with --transport http" in result.output

    def test_http_options_accepted_with_http_transport(self):
        """Test that HTTP options are accepted when using http transport."""
        with (
            patch("fabric_mcp.cli.Log") as mock_log_class,
            patch("fabric_mcp.cli.FabricMCP") as mock_fabric_mcp_class,
        ):
            mock_log = Mock()
            mock_log.level_name = "INFO"
            mock_log.logger = Mock()
            mock_log_class.return_value = mock_log

            mock_server = Mock()
            mock_fabric_mcp_class.return_value = mock_server

            runner = CliRunner()
            result = runner.invoke(
                main,
                [
                    "--transport",
                    "http",
                    "--host",
                    "0.0.0.0",
                    "--port",
                    "9000",
                    "--mcp-path",
                    "/api/mcp",
                ],
            )

            assert result.exit_code == 0
            mock_server.http_streamable.assert_called_once_with(
                host="0.0.0.0", port=9000, mcp_path="/api/mcp"
            )

    def test_default_values_with_stdio_transport(self):
        """Test that default values work correctly with stdio transport."""
        with (
            patch("fabric_mcp.cli.Log") as mock_log_class,
            patch("fabric_mcp.cli.FabricMCP") as mock_fabric_mcp_class,
        ):
            mock_log = Mock()
            mock_log.level_name = "INFO"
            mock_log.logger = Mock()
            mock_log_class.return_value = mock_log

            mock_server = Mock()
            mock_fabric_mcp_class.return_value = mock_server

            runner = CliRunner()
            result = runner.invoke(main, ["--transport", "stdio"])

            assert result.exit_code == 0
            # stdio() should be called, not http_streamable()
            mock_server.stdio.assert_called_once()
            mock_server.http_streamable.assert_not_called()

    def test_implicit_stdio_transport_validation(self):
        """Test validation when transport is not specified (default stdio)."""
        runner = CliRunner()
        result = runner.invoke(main, ["--host", "custom-host"])

        assert result.exit_code == 2
        assert "only valid with --transport http" in result.output
