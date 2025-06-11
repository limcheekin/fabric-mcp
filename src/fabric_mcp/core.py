"""Core MCP server implementation using the Model Context Protocol."""

import json
import logging
from asyncio.exceptions import CancelledError
from dataclasses import dataclass
from typing import Any, cast

import httpx
from anyio import WouldBlock
from fastmcp import FastMCP
from mcp.shared.exceptions import McpError
from mcp.types import ErrorData

from . import __version__
from .api_client import FabricApiClient
from .config import get_default_model

DEFAULT_MCP_HTTP_PATH = "/message"

DEFAULT_VENDOR = "openai"
DEFAULT_MODEL = "gpt-4o"  # Default model if none specified in config


@dataclass
class PatternExecutionConfig:  # pylint: disable=too-many-instance-attributes
    """Configuration for pattern execution parameters."""

    model_name: str | None = None
    strategy_name: str | None = None
    variables: dict[str, str] | None = None
    attachments: list[str] | None = None
    temperature: float | None = None
    top_p: float | None = None
    presence_penalty: float | None = None
    frequency_penalty: float | None = None


class FabricMCP(FastMCP[None]):
    """Base class for the Model Context Protocol server."""

    def __init__(self, log_level: str = "INFO"):
        """Initialize the MCP server with a model."""
        super().__init__(f"Fabric MCP v{__version__}")
        self.logger = logging.getLogger(__name__)
        self.log_level = log_level

        # Load default model configuration from Fabric environment
        self._default_model: str | None = None
        self._default_vendor: str | None = None
        self._load_default_config()

        # Explicitly register tool methods
        for fn in (
            self.fabric_list_patterns,
            self.fabric_get_pattern_details,
            self.fabric_run_pattern,
            self.fabric_list_models,
            self.fabric_list_strategies,
            self.fabric_get_configuration,
        ):
            self.tool(fn)

    def _load_default_config(self) -> None:
        """Load default model configuration from Fabric environment.

        This method loads DEFAULT_MODEL and DEFAULT_VENDOR from the Fabric
        environment configuration (~/.config/fabric/.env) and stores them
        as instance variables for use in pattern execution.

        Errors during configuration loading are logged but do not prevent
        server startup to ensure graceful degradation.
        """
        try:
            self._default_model, self._default_vendor = get_default_model()
            if self._default_model and self._default_vendor:
                self.logger.info(
                    "Loaded default model configuration: %s (%s)",
                    self._default_model,
                    self._default_vendor,
                )
            elif self._default_model:
                self.logger.info(
                    "Loaded ONLY default model: %s (no vendor)", self._default_model
                )
            elif self._default_vendor:
                self.logger.info(
                    "Loaded ONLY default vendor: %s (no model)", self._default_vendor
                )
            else:
                self.logger.info("No default model configuration found")
        except (OSError, ValueError, TypeError) as e:
            self.logger.warning(
                "Failed to load default model configuration: %s. "
                "Pattern execution will use hardcoded defaults.",
                e,
            )

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
            raise McpError(
                ErrorData(
                    code=-32603,  # Internal error
                    message="Failed to connect to Fabric API",
                )
            ) from e
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 500 and pattern_name:
                # Check for pattern not found (500 with file not found message)
                error_message = e.response.text or ""
                if "no such file or directory" in error_message:
                    raise McpError(
                        ErrorData(
                            code=-32602,  # Invalid params - pattern doesn't exist
                            message=f"Pattern '{pattern_name}' not found",
                        )
                    ) from e
                # Other 500 errors for pattern requests
                raise McpError(
                    ErrorData(
                        code=-32603,  # Internal error
                        message=f"Fabric API internal error: {error_message}",
                    )
                ) from e
            # Generic HTTP status errors
            status_code = e.response.status_code
            reason = e.response.reason_phrase or "Unknown error"
            raise McpError(
                ErrorData(
                    code=-32603,  # Internal error
                    message=f"Fabric API error: {status_code} {reason}",
                )
            ) from e
        except Exception as e:
            raise McpError(
                ErrorData(
                    code=-32603,  # Internal error
                    message=f"Unexpected error during {operation}: {e}",
                )
            ) from e

    def fabric_list_patterns(self) -> list[str]:
        """Return a list of available fabric patterns."""
        # Use helper method for API request
        response_data = self._make_fabric_api_request(
            "/patterns/names", operation="retrieving patterns"
        )

        # Validate response is a list
        if not isinstance(response_data, list):
            error_msg = "Invalid response format from Fabric API: expected list"
            raise McpError(
                ErrorData(code=-32603, message=error_msg)  # Internal error
            )

        # Ensure all items are strings
        validated_patterns: list[str] = []
        for item in response_data:  # type: ignore[misc]
            if isinstance(item, str):
                validated_patterns.append(item)
            else:
                # Log warning but continue with valid patterns
                item_any = cast(Any, item)
                item_type = type(item_any).__name__ if item_any is not None else "None"
                self.logger.warning("Non-string pattern name found: %s", item_type)

        return validated_patterns

    def fabric_get_pattern_details(self, pattern_name: str) -> dict[str, str]:
        """Retrieve detailed information for a specific Fabric pattern."""
        # Use helper method for API request with pattern-specific error handling
        response_data = self._make_fabric_api_request(
            f"/patterns/{pattern_name}",
            pattern_name=pattern_name,
            operation="retrieving pattern details",
        )

        # Transform Fabric API response to MCP expected format
        details = {
            "name": response_data.get("Name", ""),
            "description": response_data.get("Description", ""),
            "system_prompt": response_data.get("Pattern", ""),
        }

        return details

    def fabric_run_pattern(
        self,
        pattern_name: str,
        input_text: str = "",
        stream: bool = False,  # Will be used later; pylint: disable=unused-argument
        config: PatternExecutionConfig | None = None,
    ) -> dict[Any, Any]:
        """
        Execute a Fabric pattern with input text and return complete output.

        This tool calls the Fabric API's /chat endpoint to execute a named pattern
        with the provided input text. Returns the complete LLM-generated output
        in a non-streaming manner (streaming parameter is ignored in this version).

        Args:
            pattern_name: The name of the fabric pattern to run (required).
            input_text: The input text to be processed by the pattern (optional).
            stream: Whether to stream the output (ignored, always non-streaming).
            config: Optional configuration for execution parameters.

        Returns:
            dict[Any, Any]: Contains 'output_format' and 'output_text' fields.

        Raises:
            McpError: For any API errors, connection issues, or parsing problems.
        """
        _ = stream  # TODO: #36 remove this later when streaming is implemented
        try:
            return self._execute_fabric_pattern(pattern_name, input_text, config)
        except RuntimeError as e:
            error_message = str(e)
            # Check for pattern not found (500 with file not found message)
            if (
                "Fabric API returned error 500" in error_message
                and "no such file or directory" in error_message
            ):
                raise McpError(
                    ErrorData(
                        code=-32602,  # Invalid params - pattern doesn't exist
                        message=f"Pattern '{pattern_name}' not found",
                    )
                ) from e
            # Check for other HTTP status errors
            if "Fabric API returned error" in error_message:
                raise McpError(
                    ErrorData(
                        code=-32603,  # Internal error
                        message=f"Error executing pattern '{pattern_name}': {e}",
                    )
                ) from e
            # Other runtime errors
            raise McpError(
                ErrorData(
                    code=-32603,  # Internal error
                    message=f"Error executing pattern '{pattern_name}': {e}",
                )
            ) from e
        except ConnectionError as e:
            raise McpError(
                ErrorData(
                    code=-32603,  # Internal error
                    message=f"Error executing pattern '{pattern_name}': {e}",
                )
            ) from e

    def fabric_list_models(self) -> dict[Any, Any]:
        """Retrieve configured Fabric models by vendor."""
        # This is a placeholder for the actual implementation
        return {
            "models": ["gpt-4o", "gpt-3.5-turbo", "claude-3-opus"],
            "vendors": {
                "openai": ["gpt-4o", "gpt-3.5-turbo"],
                "anthropic": ["claude-3-opus"],
            },
        }

    def fabric_list_strategies(self) -> dict[Any, Any]:
        """Retrieve available Fabric strategies."""
        # This is a placeholder for the actual implementation
        return {
            "strategies": [
                {
                    "name": "default",
                    "description": "Default strategy for pattern execution",
                    "prompt": "Execute the pattern with default settings",
                },
                {
                    "name": "creative",
                    "description": "Creative strategy with higher temperature",
                    "prompt": "Execute the pattern with creative parameters",
                },
            ]
        }

    def fabric_get_configuration(self) -> dict[Any, Any]:
        """Retrieve Fabric configuration with sensitive values redacted."""
        # This is a placeholder for the actual implementation
        return {
            "openai_api_key": "[REDACTED_BY_MCP_SERVER]",
            "ollama_url": "http://localhost:11434",
            "anthropic_api_key": "[REDACTED_BY_MCP_SERVER]",
            "fabric_config_dir": "~/.config/fabric",
        }

    def http_streamable(
        self,
        host: str = "127.0.0.1",
        port: int = 8000,
        mcp_path: str = DEFAULT_MCP_HTTP_PATH,
    ):
        """Run the MCP server with StreamableHttpTransport."""
        try:
            self.run(transport="streamable-http", host=host, port=port, path=mcp_path)
        except (KeyboardInterrupt, CancelledError, WouldBlock) as e:
            # Handle graceful shutdown
            self.logger.debug("Exception details: %s: %s", type(e).__name__, e)
            self.logger.info("Server stopped by user.")

    def stdio(self):
        """Run the MCP server."""
        try:
            self.run()
        except (KeyboardInterrupt, CancelledError, WouldBlock):
            # Handle graceful shutdown
            self.logger.info("Server stopped by user.")

    def get_vendor_and_model(self, config: PatternExecutionConfig) -> tuple[str, str]:
        """Get the vendor and model based on the provided configuration."""
        vendor_name = self._default_vendor
        if not vendor_name:
            self.logger.debug(
                "Vendor name is None or empty. Set to hardcoded default vendor: %s",
                DEFAULT_VENDOR,
            )
            vendor_name = DEFAULT_VENDOR

        model_name = config.model_name or self._default_model
        if not model_name:
            self.logger.debug(
                "Model name is None or empty. Set to hardcoded default model: %s",
                DEFAULT_MODEL,
            )
            model_name = DEFAULT_MODEL

        return vendor_name, model_name

    def _execute_fabric_pattern(
        self,
        pattern_name: str,
        input_text: str,
        config: PatternExecutionConfig | None,
    ) -> dict[Any, Any]:
        """
        Execute a Fabric pattern against the API.

        Separated from the tool method to reduce complexity.
        """
        # AC5: Client-side validation
        if not pattern_name or not pattern_name.strip():
            raise ValueError("pattern_name is required and cannot be empty")

        # Use default config if none provided
        if config is None:
            config = PatternExecutionConfig()

        vendor, model_name = self.get_vendor_and_model(config)

        # AC3: Construct proper JSON payload for Fabric API /chat endpoint
        request_payload = {
            "prompts": [
                {
                    "userInput": input_text,
                    "patternName": pattern_name.strip(),
                    "model": model_name,
                    "vendor": vendor,
                    "contextName": "",
                    "strategyName": config.strategy_name or "",
                }
            ],
            "language": "en",
            "temperature": config.temperature or 0.7,
            "topP": config.top_p or 0.9,
            "frequencyPenalty": config.frequency_penalty or 0.0,
            "presencePenalty": config.presence_penalty or 0.0,
        }

        # AC1: Use FabricApiClient to call Fabric's /chat endpoint
        api_client = FabricApiClient()
        try:
            # AC4: Handle Server-Sent Events (SSE) stream response
            response = api_client.post("/chat", json_data=request_payload)
            response.raise_for_status()  # Raise HTTPError for bad responses

            return self._parse_sse_response(response)

        except httpx.ConnectError as e:
            self.logger.error("Failed to connect to Fabric API: %s", e)
            raise ConnectionError(f"Unable to connect to Fabric API: {e}") from e
        except httpx.HTTPStatusError as e:
            self.logger.error("Fabric API HTTP error: %s", e)
            error_text = e.response.text
            status_code = e.response.status_code
            raise RuntimeError(
                f"Fabric API returned error {status_code}: {error_text}"
            ) from e
        except Exception as e:
            self.logger.error("Unexpected error calling Fabric API: %s", e)
            raise RuntimeError(f"Unexpected error executing pattern: {e}") from e
        finally:
            api_client.close()

    def _parse_sse_response(self, response: httpx.Response) -> dict[str, str]:
        """
        Parse Server-Sent Events response from Fabric API.

        Returns:
            dict[str, str]: Contains 'output_format' and 'output_text' fields.
        """
        # Process SSE stream to collect all content
        output_chunks: list[str] = []
        output_format = "text"  # default
        has_data = False  # Track if we received any actual data

        # Parse SSE response line by line
        for line in response.iter_lines():
            line = line.strip()
            if not line:
                continue

            # SSE lines start with "data: "
            if line.startswith("data: "):
                has_data = True
                try:
                    data = json.loads(line[6:])  # Remove "data: " prefix

                    if data.get("type") == "content":
                        # Collect content chunks
                        content = data.get("content", "")
                        output_chunks.append(content)
                        # Update format if provided
                        output_format = data.get("format", output_format)

                    elif data.get("type") == "complete":
                        # End of stream
                        break

                    elif data.get("type") == "error":
                        # Handle error from Fabric API
                        error_msg = data.get("content", "Unknown Fabric API error")
                        raise RuntimeError(f"Fabric API error: {error_msg}")

                except json.JSONDecodeError as e:
                    self.logger.warning("Failed to parse SSE JSON: %s", e)
                    # For malformed SSE data, raise an error after logging
                    raise RuntimeError(f"Malformed SSE data: {e}") from e

        # Check if we received no data at all
        if not has_data:
            raise RuntimeError("Empty SSE stream - no data received")

        # AC6: Return structured response
        return {
            "output_format": output_format,
            "output_text": "".join(output_chunks),
        }

    def get_default_model_config(self) -> tuple[str | None, str | None]:
        """Get the current default model configuration.

        Returns:
            Tuple of (default_model, default_vendor). Either or both can be None.

        Note:
            This method is primarily intended for testing and introspection.
        """
        return self._default_model, self._default_vendor
