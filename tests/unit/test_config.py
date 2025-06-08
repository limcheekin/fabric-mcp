"""Unit tests for the config module."""

from pathlib import Path
from unittest.mock import MagicMock, patch

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
    @patch("fabric_mcp.config.Path.exists")
    def test_successful_load(
        self,
        mock_exists: MagicMock,
        mock_load_dotenv: MagicMock,
        mock_home: MagicMock,
    ):
        """Test successful loading of environment variables."""
        # Mock home directory
        mock_home.return_value = Path("/mock/home")
        mock_exists.return_value = True
        mock_load_dotenv.return_value = True

        result = load_fabric_env()

        assert result is True
        mock_load_dotenv.assert_called_once()

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

        assert result is False


class TestGetDefaultModel:
    """Test the get_default_model function."""

    @patch("fabric_mcp.config.load_fabric_env")
    def test_both_values_present(self, mock_load_env: MagicMock):
        """Test when both DEFAULT_MODEL and DEFAULT_VENDOR are present."""
        env_vars = {"DEFAULT_MODEL": "gpt-4", "DEFAULT_VENDOR": "openai"}

        with patch.dict("os.environ", env_vars):
            model, vendor = get_default_model()

        assert model == "gpt-4"
        assert vendor == "openai"
        mock_load_env.assert_called_once()

    @patch("fabric_mcp.config.load_fabric_env")
    def test_only_model_present(self, mock_load_env: MagicMock):
        """Test when only DEFAULT_MODEL is present."""
        env_vars = {"DEFAULT_MODEL": "gpt-4"}

        with patch.dict("os.environ", env_vars, clear=True):
            model, vendor = get_default_model()

        assert model == "gpt-4"
        assert vendor is None
        mock_load_env.assert_called_once()

    @patch("fabric_mcp.config.load_fabric_env")
    def test_only_vendor_present(self, mock_load_env: MagicMock):
        """Test when only DEFAULT_VENDOR is present."""
        env_vars = {"DEFAULT_VENDOR": "anthropic"}

        with patch.dict("os.environ", env_vars, clear=True):
            model, vendor = get_default_model()

        assert model is None
        assert vendor == "anthropic"
        mock_load_env.assert_called_once()

    @patch("fabric_mcp.config.load_fabric_env")
    def test_neither_present(self, mock_load_env: MagicMock):
        """Test when neither DEFAULT_MODEL nor DEFAULT_VENDOR are present."""
        with patch.dict("os.environ", {}, clear=True):
            model, vendor = get_default_model()

        assert model is None
        assert vendor is None
        mock_load_env.assert_called_once()

    @patch("fabric_mcp.config.load_fabric_env")
    def test_empty_values(self, mock_load_env: MagicMock):
        """Test when DEFAULT_MODEL and DEFAULT_VENDOR are empty strings."""
        env_vars = {"DEFAULT_MODEL": "", "DEFAULT_VENDOR": ""}

        with patch.dict("os.environ", env_vars, clear=True):
            model, vendor = get_default_model()

        assert model is None
        assert vendor is None
        mock_load_env.assert_called_once()
