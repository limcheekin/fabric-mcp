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


def load_fabric_env() -> dict[str, str]:
    """Load environment variables from the Fabric configuration file.

    Attempts to load ~/.config/fabric/.env using python-dotenv and handles
    loading errors gracefully (file not found, permission denied, etc.)

    Returns:
        Dictionary of environment variables loaded from the file.
        Empty dict if file doesn't exist or can't be read.

    Logs:
        INFO level: when file is missing or can't be accessed
        WARN level: when file exists but has issues loading
    """
    env_file_path = get_fabric_env_path()
    env_vars: dict[str, str] = {}

    try:
        if not env_file_path.exists():
            logger.info("Fabric environment file not found at %s", env_file_path)
            return env_vars

        # Load the environment file
        if load_dotenv(env_file_path):
            # Extract loaded variables that were actually set by this file
            # We need to be careful here since load_dotenv doesn't return
            # which variables it loaded, so we'll read the file content
            try:
                with env_file_path.open("r", encoding="utf-8") as f:
                    for line_num, line in enumerate(f, 1):
                        line = line.strip()
                        if line and not line.startswith("#") and "=" in line:
                            try:
                                key, _ = line.split("=", 1)
                                key = key.strip()
                                # Get the value from environment (after dotenv loading)
                                value = os.environ.get(key)
                                if value is not None:
                                    env_vars[key] = value
                            except ValueError:
                                logger.warning(
                                    "Malformed line %d in %s: %s",
                                    line_num,
                                    env_file_path,
                                    line,
                                )
            except (OSError, UnicodeDecodeError) as e:
                logger.warning(
                    "Error reading Fabric environment file %s: %s", env_file_path, e
                )
        else:
            logger.warning(
                "Failed to load environment variables from %s", env_file_path
            )

    except PermissionError:
        logger.info(
            "Permission denied accessing Fabric environment file %s", env_file_path
        )
    except OSError as e:
        logger.info("Cannot access Fabric environment file %s: %s", env_file_path, e)
    except (ValueError, TypeError) as e:
        logger.warning(
            "Unexpected error loading Fabric environment file %s: %s", env_file_path, e
        )

    return env_vars


def get_default_model() -> tuple[str | None, str | None]:
    """Extract DEFAULT_MODEL and DEFAULT_VENDOR from loaded environment.

    Reads DEFAULT_VENDOR and DEFAULT_MODEL variables from the loaded .env file,
    caches these values for pattern execution, handles missing variables gracefully.

    Returns:
        Tuple of (DEFAULT_MODEL, DEFAULT_VENDOR). Either or both can be None
        if the variables are not set.

    Logs:
        WARN level: when DEFAULT_* variables are missing from environment
    """
    env_vars = load_fabric_env()

    default_model = env_vars.get("DEFAULT_MODEL")
    default_vendor = env_vars.get("DEFAULT_VENDOR")

    # Convert empty strings to None
    if not default_model:
        default_model = None
        logger.warning("DEFAULT_MODEL not found in Fabric environment configuration")

    if not default_vendor:
        default_vendor = None
        logger.warning("DEFAULT_VENDOR not found in Fabric environment configuration")

    return default_model, default_vendor
