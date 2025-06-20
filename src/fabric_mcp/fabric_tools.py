"""Fabric MCP tool implementations and related functionality."""

import fnmatch
import logging
from typing import Any, cast

import httpx
from mcp.shared.exceptions import McpError
from mcp.types import INTERNAL_ERROR, INVALID_PARAMS, ErrorData

from fabric_mcp.utils import raise_mcp_error

from .api_client import FabricApiClient
from .constants import (
    API_KEY_PREFIXES,
    SENSITIVE_CONFIG_PATTERNS,
)
from .models import PatternExecutionConfig
from .validation import ValidationMixin

# Re-export FabricApiClient so tests can still patch fabric_mcp.core.FabricApiClient
__all__ = ["FabricApiClient", "FabricToolsMixin"]


class FabricToolsMixin(ValidationMixin):
    """Mixin class providing all Fabric MCP tool implementations."""

    def _make_fabric_api_request(
        self,
        endpoint: str,
        pattern_name: str | None = None,
        operation: str = "API request",
    ) -> Any:
        """Make a request to the Fabric API with consistent error handling.

        Args:
            endpoint: The API endpoint to call (e.g., "/patterns/names")
            pattern_name: Pattern name for pattern-specific error messages
            operation: Description of the operation for error messages

        Returns:
            The parsed JSON response from the API

        Raises:
            McpError: For any API errors, connection issues, or parsing problems
        """
        try:
            api_client = FabricApiClient()
            try:
                response = api_client.get(endpoint)
                return response.json()
            finally:
                api_client.close()
        except httpx.RequestError as e:
            raise_mcp_error(
                e,
                INTERNAL_ERROR,
                f"Failed to connect to Fabric API during {operation}: {e}",
            )
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 500 and pattern_name:
                # Check for pattern not found (500 with file not found message)
                error_message = e.response.text or ""
                if "no such file or directory" in error_message:
                    raise_mcp_error(
                        e,
                        INVALID_PARAMS,
                        f"Pattern '{pattern_name}' not found in Fabric API",
                    )
                # Other 500 errors for pattern requests
                raise_mcp_error(
                    e,
                    INTERNAL_ERROR,
                    f"Fabric API internal error during {operation}: {error_message}",
                )
            # Generic HTTP status errors
            status_code = e.response.status_code
            reason = e.response.reason_phrase or "Unknown error"
            raise_mcp_error(
                e,
                INTERNAL_ERROR,
                f"Fabric API error during {operation}: {status_code} {reason}",
            )
        except Exception as e:
            raise McpError(
                ErrorData(
                    code=INTERNAL_ERROR,
                    message=f"Unexpected error during {operation}: {e}",
                )
            ) from e

    def fabric_list_patterns(self) -> list[str]:
        """Return a list of available fabric patterns."""
        response_data = self._make_fabric_api_request(
            "/patterns/names", operation="retrieving patterns"
        )

        # Validate response data type
        if not isinstance(response_data, list):
            raise_mcp_error(
                ValueError(),
                INTERNAL_ERROR,
                "Invalid response from Fabric API: expected list of patterns",
            )

        # Cast to expected type
        response_data = cast(list[Any], response_data)

        for item in response_data:
            # Ensure each item is a string
            if not isinstance(item, str):
                raise_mcp_error(
                    ValueError(),
                    INTERNAL_ERROR,
                    "Invalid pattern name in response: "
                    f"expected string, got {type(item).__name__}",
                )

        patterns = cast(list[str], response_data)

        return patterns

    def fabric_get_pattern_details(self, pattern_name: str) -> dict[str, str]:
        """Retrieve detailed information for a specific Fabric pattern."""
        # Use helper method for API request with pattern-specific error handling
        response_data = self._make_fabric_api_request(
            f"/patterns/{pattern_name}",
            pattern_name=pattern_name,
            operation="retrieving pattern details",
        )

        # Validate response data type
        if not isinstance(response_data, dict):
            raise_mcp_error(
                ValueError(),
                INTERNAL_ERROR,
                "Invalid response from Fabric API: expected dict for pattern details",
            )

        response_data = cast(dict[str, Any], response_data)

        # Validate required fields in the response
        if not all(key in response_data for key in ("Name", "Description", "Pattern")):
            raise_mcp_error(
                ValueError(),
                INTERNAL_ERROR,
                "Invalid pattern details response: missing required fields "
                "(Name, Description, Pattern)",
            )

        # Transform Fabric API response to MCP expected format
        details = {
            "name": response_data["Name"],
            "description": response_data["Description"],
            "system_prompt": response_data["Pattern"],
        }

        return details

    def fabric_list_models(self) -> dict[Any, Any]:
        """Retrieve configured Fabric models by vendor."""
        response_data = self._make_fabric_api_request(
            "/models/names", operation="retrieving models"
        )

        # Validate response data type
        if not isinstance(response_data, dict):
            raise_mcp_error(
                ValueError(),
                INTERNAL_ERROR,
                "Invalid response from Fabric API: expected dict for models",
            )

        response_data = cast(dict[str, Any], response_data)

        # Validate models field
        models = response_data.get("models", [])
        if not isinstance(models, list):
            raise_mcp_error(
                ValueError(),
                INTERNAL_ERROR,
                "Invalid models field: expected list",
            )

        # Validate each model name is a string
        models_list = cast(list[Any], models)
        for item in models_list:
            if not isinstance(item, str):
                raise_mcp_error(
                    ValueError(),
                    INTERNAL_ERROR,
                    "Invalid model name in response: "
                    f"expected string, got {type(item).__name__}",
                )

        # Validate vendors field
        vendors = response_data.get("vendors", {})
        if not isinstance(vendors, dict):
            raise_mcp_error(
                ValueError(),
                INTERNAL_ERROR,
                "Invalid vendors field: expected dict",
            )

        # Validate vendor structure - each vendor should have a list of strings
        vendors_dict = cast(dict[Any, Any], vendors)
        for vendor_name, vendor_models in vendors_dict.items():
            if not isinstance(vendor_name, str):
                raise_mcp_error(
                    ValueError(),
                    INTERNAL_ERROR,
                    "Invalid vendor name in response: "
                    f"expected string, got {type(vendor_name).__name__}",
                )
            if not isinstance(vendor_models, list):
                raise_mcp_error(
                    ValueError(),
                    INTERNAL_ERROR,
                    f"Invalid models list for vendor '{vendor_name}': expected list",
                )
            vendor_models_list = cast(list[Any], vendor_models)
            for model in vendor_models_list:
                if not isinstance(model, str):
                    raise_mcp_error(
                        ValueError(),
                        INTERNAL_ERROR,
                        f"Invalid model name for vendor '{vendor_name}': "
                        f"expected string, got {type(model).__name__}",
                    )

        # Return validated structure
        return {
            "models": cast(list[str], models),
            "vendors": cast(dict[str, list[str]], vendors),
        }

    def fabric_list_strategies(self) -> dict[Any, Any]:
        """Retrieve available Fabric strategies."""
        # Use helper method for API request
        response_data = self._make_fabric_api_request(
            "/strategies", operation="retrieving strategies"
        )

        # Validate response data type
        if not isinstance(response_data, list):
            raise_mcp_error(
                ValueError(),
                INTERNAL_ERROR,
                "Invalid response from Fabric API: expected list of strategies",
            )

        response_data = cast(list[Any], response_data)
        # Ensure all items are dictionaries
        for item in response_data:
            if not isinstance(item, dict):
                raise_mcp_error(
                    ValueError(),
                    INTERNAL_ERROR,
                    "Invalid strategy object in response: "
                    f"expected dict, got {type(item).__name__}",
                )

        # Cast to expected type
        response_data = cast(list[dict[str, Any]], response_data)

        # Validate each strategy object and build response
        validated_strategies: list[dict[str, str]] = []
        for item in response_data:
            name = item.get("name", "")
            description = item.get("description", "")
            prompt = item.get("prompt", "")

            # Type check all fields as strings and ensure name/description not empty
            if (
                isinstance(name, str)
                and isinstance(description, str)
                and isinstance(prompt, str)
                and name.strip()  # Name must not be empty/whitespace
                and description.strip()  # Description must not be empty/whitespace
                # Note: prompt can be empty string - that's valid
            ):
                validated_strategies.append(
                    {"name": name, "description": description, "prompt": prompt}
                )
            else:
                # Log warning but continue with valid strategies
                logger = logging.getLogger(__name__)
                logger.warning(
                    "Strategy object missing required string fields: %s",
                    cast(Any, item),
                )

        return {"strategies": validated_strategies}

    def fabric_get_configuration(self) -> dict[Any, Any]:
        """Retrieve Fabric configuration with sensitive values redacted.

        Returns:
            dict[Any, Any]: Configuration key-value pairs with sensitive values
            redacted. Sensitive keys (matching *_API_KEY, *_TOKEN, *_SECRET,
            *_PASSWORD patterns) with non-empty values are replaced with
            "[REDACTED_BY_MCP_SERVER]". Empty sensitive values and all
            non-sensitive values are passed through unchanged.

        Raises:
            McpError: For any API errors, connection issues, or invalid responses.
        """
        # Get configuration from Fabric API
        response_data = self._make_fabric_api_request(
            "/config", operation="retrieving configuration"
        )

        # Validate response data type
        if not isinstance(response_data, dict):
            raise_mcp_error(
                ValueError(),
                INTERNAL_ERROR,
                "Invalid response from Fabric API: expected dict for config",
            )

        response_data = cast(dict[str, Any], response_data)

        # Apply redaction to sensitive values
        redacted_config = self._redact_sensitive_config_values(response_data)

        return redacted_config

    def _redact_sensitive_config_values(
        self, config_data: dict[str, Any]
    ) -> dict[str, Any]:
        """Redact sensitive config values based on key patterns and value patterns.

        Args:
            config_data: Raw configuration data from Fabric API

        Returns:
            Configuration data with sensitive values redacted

        Note:
            - Sensitive keys with values are replaced with "[REDACTED_BY_MCP_SERVER]"
            - Values that look like API keys (based on prefixes) are also redacted
            - Sensitive keys with empty string values are passed through as empty
            - Non-sensitive keys are always passed through unchanged
        """

        redacted_config: dict[str, Any] = {}

        for key, value in config_data.items():
            # Check if key matches any sensitive pattern
            key_is_sensitive = any(
                fnmatch.fnmatch(key.upper(), pattern.upper())
                for pattern in SENSITIVE_CONFIG_PATTERNS
            )

            # Check if value looks like an API key (only for string values)
            value_is_api_key = False
            if isinstance(value, str) and value:
                value_is_api_key = any(
                    value.startswith(prefix) for prefix in API_KEY_PREFIXES
                )

            # Redact if key is sensitive OR value looks like an API key
            if (key_is_sensitive or value_is_api_key) and value != "":
                # Redact non-empty sensitive values or API key values
                redacted_config[key] = "[REDACTED_BY_MCP_SERVER]"
            else:
                # Pass through empty sensitive values and all non-sensitive values
                redacted_config[key] = value

        return redacted_config

    def _merge_execution_config(
        self,
        config: PatternExecutionConfig | None,
        model_name: str | None = None,
        vendor_name: str | None = None,
        temperature: float | None = None,
        top_p: float | None = None,
        presence_penalty: float | None = None,
        frequency_penalty: float | None = None,
        strategy_name: str | None = None,
        variables: dict[str, str] | None = None,
        attachments: list[str] | None = None,
    ) -> PatternExecutionConfig:
        """Merge execution parameters with existing config.

        Parameters provided directly to the tool take precedence over
        those in the config object.

        Args:
            config: Existing configuration (optional)
            model_name: Model name override (optional)
            temperature: Temperature override (optional)
            top_p: Top-p override (optional)
            presence_penalty: Presence penalty override (optional)
            frequency_penalty: Frequency penalty override (optional)
            strategy_name: Strategy name override (optional)
            variables: Variables override (optional)
            attachments: Attachments override (optional)

        Returns:
            Merged PatternExecutionConfig with parameter precedence
        """
        # Start with existing config or create new one
        if config is None:
            config = PatternExecutionConfig()

        # Create new config with parameter precedence
        return PatternExecutionConfig(
            # Use the provided model_name if available; otherwise, fall back
            # to the existing config's model_name
            model_name=model_name or config.model_name,
            # Use the provided vendor_name if available; otherwise, fall back
            # to the existing config's vendor_name
            vendor_name=vendor_name or config.vendor_name,
            # Use the provided strategy_name if available; otherwise, fall back
            # to the existing config's strategy_name
            strategy_name=strategy_name or config.strategy_name,
            # Use the provided variables if available; otherwise, fall back
            # to the existing config's variables
            variables=variables if variables is not None else config.variables,
            # Use the provided attachments if available; otherwise, fall back
            # to the existing config's attachments
            attachments=attachments if attachments is not None else config.attachments,
            # Use the provided temperature if not None; otherwise, fall back
            # to the existing config's temperature
            temperature=temperature if temperature is not None else config.temperature,
            # Use the provided top_p if not None; otherwise, fall back
            # to the existing config's top_p
            top_p=top_p if top_p is not None else config.top_p,
            # Use the provided presence_penalty if not None; otherwise, fall back
            # to the existing config's presence_penalty
            presence_penalty=(
                presence_penalty
                if presence_penalty is not None
                else config.presence_penalty
            ),
            # Use the provided frequency_penalty if not None; otherwise,
            # fall back to the existing config's frequency_penalty
            frequency_penalty=(
                frequency_penalty
                if frequency_penalty is not None
                else config.frequency_penalty
            ),
        )
