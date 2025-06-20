"""Server-Sent Events (SSE) parsing utilities for fabric-mcp."""

import json
import logging
from collections.abc import Generator
from typing import Any

import httpx


class SSEParserMixin:
    """Mixin class providing SSE parsing functionality."""

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
                    logger = logging.getLogger(__name__)
                    logger.warning("Failed to parse SSE JSON: %s", e)
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

    def _parse_sse_stream(
        self, response: httpx.Response
    ) -> Generator[dict[str, Any], None, None]:
        """
        Parse Server-Sent Events response from Fabric API in streaming mode.

        Yields chunks in real-time as they arrive from the Fabric API.

        Yields:
            dict[str, Any]: Each chunk contains 'type', 'format', and 'content' fields.

        Raises:
            RuntimeError: If the SSE data is malformed or empty.
        """
        has_data = False  # Track if we received any actual data
        logger = logging.getLogger(__name__)

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
                        # Yield content chunks in real-time
                        yield {
                            "type": "content",
                            "format": data.get("format", "text"),
                            "content": data.get("content", ""),
                        }

                    elif data.get("type") == "complete":
                        # Yield completion signal and end stream
                        yield {
                            "type": "complete",
                            "format": data.get("format", "text"),
                            "content": data.get("content", ""),
                        }
                        return

                    elif data.get("type") == "error":
                        # Yield error and end stream
                        error_msg = data.get("content", "Unknown Fabric API error")
                        raise RuntimeError(f"Fabric API error: {error_msg}")
                    else:
                        # Handle unexpected types gracefully
                        logger.warning(
                            "Unexpected SSE type: %s", data.get("type", "unknown")
                        )
                        raise RuntimeError(
                            "Unexpected SSE data type "
                            f"received: {data.get('type', 'unknown')}"
                        )

                except json.JSONDecodeError as e:
                    logger.warning("Failed to parse SSE JSON: %s", e)
                    raise RuntimeError(f"Malformed SSE data: {e}") from e

        # Check if we received no data at all
        if not has_data:
            raise RuntimeError("Empty SSE stream - no data received")
