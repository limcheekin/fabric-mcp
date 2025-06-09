"""Configuration module for loading Fabric environment settings.

This module handles loading default model preferences from the standard
Fabric environment configuration (~/.config/fabric/.env) and provides
them for use in pattern execution.
"""

import logging
import os
from pathlib import Path

from dotenv import load_dotenv

logger = logging.getLogger(__name__)


def get_fabric_env_path() -> Path:
    """Get the path to the Fabric environment configuration file.

    Returns:
        Path to ~/.config/fabric/.env
    """
    return Path.home() / ".config" / "fabric" / ".env"


def load_fabric_env() -> bool:
    """Load environment variables from the Fabric configuration file.

    Attempts to load ~/.config/fabric/.env using python-dotenv and handles
    loading errors gracefully (file not found, permission denied, etc.)

    Returns:
        True if file was successfully loaded, False otherwise.

    Logs:
        INFO level: when file is missing or can't be accessed
        WARN level: when file exists but has loading issues
    """
    env_file_path = get_fabric_env_path()

    try:
        if not env_file_path.exists():
            logger.info("Fabric environment file not found at %s", env_file_path)
            return False

        # Load the environment file into os.environ
        success = load_dotenv(env_file_path)
        if not success:
            logger.warning(
                "Failed to load environment variables from %s", env_file_path
            )
        return success

    except (PermissionError, OSError) as e:
        logger.info("Cannot access Fabric environment file %s: %s", env_file_path, e)

    return False


def get_default_model() -> tuple[str | None, str | None]:
    """Extract DEFAULT_MODEL and DEFAULT_VENDOR from loaded environment.

    Loads the Fabric environment file and reads DEFAULT_VENDOR and DEFAULT_MODEL
    variables from os.environ, handling missing variables gracefully.

    Returns:
        Tuple of (DEFAULT_MODEL, DEFAULT_VENDOR). Either or both can be None
        if the variables are not set.

    Logs:
        DEBUG level: when DEFAULT_* variables are missing from environment
    """
    # Load the environment file (this populates os.environ)
    load_fabric_env()

    # Get values directly from os.environ after load_dotenv
    default_model = os.environ.get("DEFAULT_MODEL")
    default_vendor = os.environ.get("DEFAULT_VENDOR")

    # Convert empty strings to None
    if not default_model:
        default_model = None
        logger.debug("DEFAULT_MODEL not found in Fabric environment configuration")

    if not default_vendor:
        default_vendor = None
        logger.debug("DEFAULT_VENDOR not found in Fabric environment configuration")

    return default_model, default_vendor
