"""Unit tests for the config module."""

import os
from pathlib import Path
from unittest.mock import MagicMock, mock_open, patch

from fabric_mcp.config import get_default_model, get_fabric_env_path, load_fabric_env


class TestLoadFabricEnv:
    """Test the load_fabric_env function."""

    def test_returns_correct_path(self):
        """Test that get_fabric_env_path returns the correct path."""
        expected_path = Path.home() / ".config" / "fabric" / ".env"
        assert get_fabric_env_path() == expected_path

    @patch("fabric_mcp.config.Path.home")
    @patch("fabric_mcp.config.load_dotenv")
    def test_file_not_exists(self, mock_load_dotenv: MagicMock, mock_home: MagicMock):
        """Test behavior when .env file doesn't exist."""
        # Mock home directory
        mock_home.return_value = Path("/mock/home")

        # Mock file not existing
        with patch("fabric_mcp.config.Path.exists", return_value=False):
            result = load_fabric_env()

        assert not result
        mock_load_dotenv.assert_not_called()

    @patch("fabric_mcp.config.Path.home")
    @patch("fabric_mcp.config.load_dotenv")
    @patch("fabric_mcp.config.Path.open")
    @patch("fabric_mcp.config.Path.exists")
    def test_successful_load(
        self,
        mock_exists: MagicMock,
        mock_open_file: MagicMock,
        mock_load_dotenv: MagicMock,
        mock_home: MagicMock,
    ):
        """Test successful loading of environment variables."""
        # Mock home directory
        mock_home.return_value = Path("/mock/home")
        mock_exists.return_value = True
        mock_load_dotenv.return_value = True

        # Mock file content
        mock_file_content = "DEFAULT_MODEL=gpt-4\nDEFAULT_VENDOR=openai\n# comment\n"
        mock_open_file.return_value = mock_open(
            read_data=mock_file_content
        ).return_value

        # Mock environment variables
        env_vars = {"DEFAULT_MODEL": "gpt-4", "DEFAULT_VENDOR": "openai"}
        with patch.dict(os.environ, env_vars):
            result = load_fabric_env()

        assert result == {"DEFAULT_MODEL": "gpt-4", "DEFAULT_VENDOR": "openai"}

    @patch("fabric_mcp.config.Path.home")
    @patch("fabric_mcp.config.load_dotenv")
    @patch("fabric_mcp.config.Path.exists")
    def test_load_dotenv_fails(
        self, mock_exists: MagicMock, mock_load_dotenv: MagicMock, mock_home: MagicMock
    ):
        """Test behavior when load_dotenv fails."""
        mock_home.return_value = Path("/mock/home")
        mock_exists.return_value = True
        mock_load_dotenv.return_value = False

        result = load_fabric_env()

        assert not result

    @patch("fabric_mcp.config.Path.home")
    @patch("fabric_mcp.config.Path.exists")
    def test_permission_error(self, mock_exists: MagicMock, mock_home: MagicMock):
        """Test behavior when file access is denied."""
        mock_home.return_value = Path("/mock/home")
        mock_exists.side_effect = PermissionError("Permission denied")

        result = load_fabric_env()

        assert not result

    @patch("fabric_mcp.config.Path.home")
    @patch("fabric_mcp.config.load_dotenv")
    @patch("fabric_mcp.config.Path.open")
    @patch("fabric_mcp.config.Path.exists")
    def test_malformed_line_handling(
        self,
        mock_exists: MagicMock,
        mock_open_file: MagicMock,
        mock_load_dotenv: MagicMock,
        mock_home: MagicMock,
    ):
        """Test handling of malformed lines in .env file."""
        mock_home.return_value = Path("/mock/home")
        mock_exists.return_value = True
        mock_load_dotenv.return_value = True

        # Mock file content with malformed line
        mock_file_content = (
            "DEFAULT_MODEL=gpt-4\n"
            "malformed_line_without_equals\n"
            "DEFAULT_VENDOR=openai\n"
        )
        mock_open_file.return_value = mock_open(
            read_data=mock_file_content
        ).return_value

        env_vars = {"DEFAULT_MODEL": "gpt-4", "DEFAULT_VENDOR": "openai"}
        with patch.dict(os.environ, env_vars):
            result = load_fabric_env()

        # Should still get valid variables despite malformed line
        assert result == {"DEFAULT_MODEL": "gpt-4", "DEFAULT_VENDOR": "openai"}

    @patch("fabric_mcp.config.Path.home")
    @patch("fabric_mcp.config.load_dotenv")
    @patch("fabric_mcp.config.Path.open")
    @patch("fabric_mcp.config.Path.exists")
    def test_empty_and_comment_lines(
        self,
        mock_exists: MagicMock,
        mock_open_file: MagicMock,
        mock_load_dotenv: MagicMock,
        mock_home: MagicMock,
    ):
        """Test handling of empty lines and comments."""
        mock_home.return_value = Path("/mock/home")
        mock_exists.return_value = True
        mock_load_dotenv.return_value = True

        # Mock file content with empty lines and comments
        mock_file_content = """
# This is a comment
DEFAULT_MODEL=gpt-4

# Another comment
DEFAULT_VENDOR=openai

"""
        mock_open_file.return_value = mock_open(
            read_data=mock_file_content
        ).return_value

        env_vars = {"DEFAULT_MODEL": "gpt-4", "DEFAULT_VENDOR": "openai"}
        with patch.dict(os.environ, env_vars):
            result = load_fabric_env()

        assert result == {"DEFAULT_MODEL": "gpt-4", "DEFAULT_VENDOR": "openai"}


class TestGetDefaultModel:
    """Test the get_default_model function."""

    @patch("fabric_mcp.config.load_fabric_env")
    def test_both_values_present(self, mock_load_env: MagicMock):
        """Test when both DEFAULT_MODEL and DEFAULT_VENDOR are present."""
        mock_load_env.return_value = {
            "DEFAULT_MODEL": "gpt-4",
            "DEFAULT_VENDOR": "openai",
        }

        model, vendor = get_default_model()

        assert model == "gpt-4"
        assert vendor == "openai"

    @patch("fabric_mcp.config.load_fabric_env")
    def test_only_model_present(self, mock_load_env: MagicMock):
        """Test when only DEFAULT_MODEL is present."""
        mock_load_env.return_value = {"DEFAULT_MODEL": "gpt-4"}

        model, vendor = get_default_model()

        assert model == "gpt-4"
        assert vendor is None

    @patch("fabric_mcp.config.load_fabric_env")
    def test_only_vendor_present(self, mock_load_env: MagicMock):
        """Test when only DEFAULT_VENDOR is present."""
        mock_load_env.return_value = {"DEFAULT_VENDOR": "anthropic"}

        model, vendor = get_default_model()

        assert model is None
        assert vendor == "anthropic"

    @patch("fabric_mcp.config.load_fabric_env")
    def test_neither_present(self, mock_load_env: MagicMock):
        """Test when neither DEFAULT_MODEL nor DEFAULT_VENDOR are present."""
        mock_load_env.return_value = {}

        model, vendor = get_default_model()

        assert model is None
        assert vendor is None

    @patch("fabric_mcp.config.load_fabric_env")
    def test_empty_values(self, mock_load_env: MagicMock):
        """Test when DEFAULT_MODEL and DEFAULT_VENDOR are empty strings."""
        mock_load_env.return_value = {"DEFAULT_MODEL": "", "DEFAULT_VENDOR": ""}

        model, vendor = get_default_model()

        assert model is None
        assert vendor is None
