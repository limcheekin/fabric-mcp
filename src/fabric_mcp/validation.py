"""Parameter validation utilities for fabric-mcp."""

from typing import Any, cast

from mcp.types import INVALID_PARAMS

from fabric_mcp.utils import raise_mcp_error


class ValidationMixin:
    """Mixin class providing parameter validation methods."""

    def _validate_numeric_parameter(
        self, name: str, value: float | None, min_value: float, max_value: float
    ) -> None:
        """Validate a single parameter against its expected range.

        Args:
            name: The name of the parameter (for error messages)
            value: The value of the parameter to validate
            min_value: The minimum acceptable value
            max_value: The maximum acceptable value

        Raises:
            McpError: If the parameter is invalid
        """
        if value is not None:
            try:
                if not min_value <= value <= max_value:
                    raise_mcp_error(
                        ValueError(),
                        INVALID_PARAMS,
                        f"{name} must be a number between {min_value} and {max_value}",
                    )
            except TypeError as exc:
                raise_mcp_error(
                    exc,
                    INVALID_PARAMS,
                    f"{name} must be a number between {min_value} and {max_value}",
                )

    def _validate_string_parameter(self, name: str, value: str | None) -> None:
        """Validate a string parameter to ensure it is not empty.

        Args:
            name: The name of the parameter (for error messages)
            value: The value of the parameter to validate

        Raises:
            McpError: If the parameter is invalid
        """
        if value is not None and not value.strip():
            raise_mcp_error(
                ValueError(),
                INVALID_PARAMS,
                f"{name} must be a non-empty string",
            )

    def _validate_variables_parameter(self, variables: Any | None) -> None:
        """Validate variables parameter: dict with string keys and values.

        Args:
            variables: The variables parameter to validate

        Raises:
            McpError: If the parameter is invalid
        """
        if variables is not None:
            if not isinstance(variables, dict):
                raise_mcp_error(
                    ValueError(),
                    INVALID_PARAMS,
                    "variables must be a dictionary",
                )
            variable_keys_and_values: list[Any] = list(
                cast(list[Any], variables.values())
            ) + list(cast(list[Any], variables.keys()))
            if any(not isinstance(item, str) for item in variable_keys_and_values):
                raise_mcp_error(
                    ValueError(),
                    INVALID_PARAMS,
                    "variables must be a dictionary with string keys and values",
                )

    def _validate_attachments_parameter(self, attachments: Any | None) -> None:
        """Validate an attachments parameter to ensure it is a list of strings.

        Args:
            attachments: The attachments parameter to validate

        Raises:
            McpError: If the parameter is invalid
        """
        if attachments is not None:
            if not isinstance(attachments, list):
                raise_mcp_error(
                    ValueError(),
                    INVALID_PARAMS,
                    "attachments must be a list",
                )
            if any(not isinstance(item, str) for item in cast(list[Any], attachments)):
                raise_mcp_error(
                    ValueError(),
                    INVALID_PARAMS,
                    "attachments must be a list of strings",
                )

    def _validate_execution_parameters(
        self,
        model_name: str | None = None,
        _vendor_name: str | None = None,
        temperature: float | None = None,
        top_p: float | None = None,
        presence_penalty: float | None = None,
        frequency_penalty: float | None = None,
        strategy_name: str | None = None,
        variables: dict[str, str] | None = None,
        attachments: list[str] | None = None,
    ) -> None:
        """Validate execution control parameters."""
        # Validate temperature range
        self._validate_numeric_parameter("temperature", temperature, 0.0, 2.0)

        # Validate top_p range
        self._validate_numeric_parameter("top_p", top_p, 0.0, 1.0)

        # Validate presence_penalty range
        self._validate_numeric_parameter(
            "presence_penalty", presence_penalty, -2.0, 2.0
        )

        # Validate frequency_penalty range
        self._validate_numeric_parameter(
            "frequency_penalty", frequency_penalty, -2.0, 2.0
        )

        # Validate model_name format (basic validation - not empty string)
        self._validate_string_parameter("model_name", model_name)

        # Validate strategy_name format (basic validation - not empty string)
        self._validate_string_parameter("strategy_name", strategy_name)

        # Validate variables parameter format
        self._validate_variables_parameter(variables)

        # Validate attachments parameter format
        self._validate_attachments_parameter(attachments)
