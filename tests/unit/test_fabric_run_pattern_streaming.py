"""Tests for fabric_run_pattern tool streaming functionality.

This module tests the streaming functionality of the fabric_run_pattern tool,
including streaming mode behavior, error handling during streaming, and
comparison between streaming and non-streaming modes.
"""

from collections.abc import Callable
from typing import Any

import pytest

from tests.shared.fabric_api.utils import fabric_api_server_fixture
from tests.shared.fabric_api_mocks import (
    FabricApiMockBuilder,
    mock_fabric_api_client,
)
from tests.unit.test_fabric_run_pattern_base import TestFabricRunPatternFixtureBase

_ = fabric_api_server_fixture  # to get rid of unused variable warning


class TestFabricRunPatternStreaming(TestFabricRunPatternFixtureBase):
    """Test cases for fabric_run_pattern tool streaming functionality."""

    def test_streaming_mode_with_simple_content(
        self, fabric_run_pattern_tool: Callable[..., Any]
    ) -> None:
        """Test streaming mode returns generator with simple content."""
        builder = FabricApiMockBuilder().with_successful_sse("Hello, World!")

        with mock_fabric_api_client(builder) as mock_api_client:
            result = fabric_run_pattern_tool("test_pattern", "test input", stream=True)

            # Should return a generator for streaming mode
            assert hasattr(result, "__iter__")

            # Collect all chunks from the stream
            chunks = list(result)

            # Should have content and complete chunks
            assert len(chunks) >= 1

            # Find content chunks
            content_chunks = [c for c in chunks if c.get("type") == "content"]
            assert len(content_chunks) >= 1

            # Verify chunk structure
            content_chunk = content_chunks[0]
            assert "type" in content_chunk
            assert "format" in content_chunk
            assert "content" in content_chunk
            assert content_chunk["type"] == "content"
            assert content_chunk["content"] == "Hello, World!"

            mock_api_client.close.assert_called_once()

    def test_streaming_mode_with_multiple_chunks(
        self, fabric_run_pattern_tool: Callable[..., Any]
    ) -> None:
        """Test streaming mode with multiple content chunks."""
        sse_lines = [
            'data: {"type": "content", "content": "First", "format": "text"}',
            'data: {"type": "content", "content": " Second", "format": "text"}',
            'data: {"type": "content", "content": " Third", "format": "text"}',
            'data: {"type": "complete"}',
        ]
        builder = FabricApiMockBuilder().with_sse_lines(sse_lines)

        with mock_fabric_api_client(builder) as mock_api_client:
            result = fabric_run_pattern_tool("test_pattern", "test input", stream=True)

            chunks = list(result)
            content_chunks = [c for c in chunks if c.get("type") == "content"]

            # Should have 3 content chunks
            assert len(content_chunks) == 3
            assert content_chunks[0]["content"] == "First"
            assert content_chunks[1]["content"] == " Second"
            assert content_chunks[2]["content"] == " Third"

            mock_api_client.close.assert_called_once()

    def test_streaming_mode_with_different_formats(
        self, fabric_run_pattern_tool: Callable[..., Any]
    ) -> None:
        """Test streaming mode handles different content formats."""
        sse_lines = [
            'data: {"type": "content", "content": "# Header", "format": "markdown"}',
            'data: {"type": "content", "content": " Text", "format": "markdown"}',
            'data: {"type": "complete", "format": "markdown"}',
        ]
        builder = FabricApiMockBuilder().with_sse_lines(sse_lines)

        with mock_fabric_api_client(builder) as mock_api_client:
            result = fabric_run_pattern_tool("test_pattern", "test input", stream=True)

            chunks = list(result)
            content_chunks = [c for c in chunks if c.get("type") == "content"]

            # Verify format is preserved in streaming
            assert len(content_chunks) == 2
            assert content_chunks[0]["format"] == "markdown"
            assert content_chunks[1]["format"] == "markdown"

            mock_api_client.close.assert_called_once()

    def test_streaming_mode_error_handling(
        self, fabric_run_pattern_tool: Callable[..., Any]
    ) -> None:
        """Test streaming mode error handling during stream."""
        builder = FabricApiMockBuilder().with_sse_error("Stream error occurred")

        with mock_fabric_api_client(builder) as mock_api_client:
            result = fabric_run_pattern_tool("test_pattern", "test input", stream=True)

            # Should raise RuntimeError when iterating over the stream
            with pytest.raises(RuntimeError) as exc_info:
                list(result)

            assert "Stream error occurred" in str(exc_info.value)
            mock_api_client.close.assert_called_once()

    def test_streaming_mode_malformed_sse_data(
        self, fabric_run_pattern_tool: Callable[..., Any]
    ) -> None:
        """Test streaming mode with malformed SSE data."""
        builder = FabricApiMockBuilder().with_partial_sse_data()

        with mock_fabric_api_client(builder) as mock_api_client:
            result = fabric_run_pattern_tool("test_pattern", "test input", stream=True)

            # Should raise RuntimeError when processing malformed data
            with pytest.raises(RuntimeError) as exc_info:
                list(result)

            assert "Malformed SSE data" in str(exc_info.value)
            mock_api_client.close.assert_called_once()

    def test_streaming_mode_empty_stream(
        self, fabric_run_pattern_tool: Callable[..., Any]
    ) -> None:
        """Test streaming mode with empty SSE stream."""
        builder = FabricApiMockBuilder().with_empty_sse_stream()

        with mock_fabric_api_client(builder) as mock_api_client:
            result = fabric_run_pattern_tool("test_pattern", "test input", stream=True)

            # Should raise RuntimeError for empty stream
            with pytest.raises(RuntimeError) as exc_info:
                list(result)

            assert "Empty SSE stream" in str(exc_info.value)
            mock_api_client.close.assert_called_once()

    def test_streaming_vs_non_streaming_behavior(
        self, fabric_run_pattern_tool: Callable[..., Any]
    ) -> None:
        """Test that streaming vs non-streaming modes behave differently."""
        sse_lines = [
            'data: {"type": "content", "content": "First", "format": "text"}',
            'data: {"type": "content", "content": " Second", "format": "text"}',
            'data: {"type": "complete"}',
        ]
        builder = FabricApiMockBuilder().with_sse_lines(sse_lines)

        with mock_fabric_api_client(builder) as mock_api_client:
            # Test non-streaming mode (default)
            non_streaming_result = fabric_run_pattern_tool(
                "test_pattern", "test input", stream=False
            )

            # Should return dict with accumulated content
            assert isinstance(non_streaming_result, dict)
            assert "output_text" in non_streaming_result
            assert "output_format" in non_streaming_result
            assert non_streaming_result["output_text"] == "First Second"

        # Reset the mock for streaming test
        with mock_fabric_api_client(builder) as mock_api_client:
            # Test streaming mode
            streaming_result = fabric_run_pattern_tool(
                "test_pattern", "test input", stream=True
            )

            # Should return generator
            assert hasattr(streaming_result, "__iter__")
            chunks = list(streaming_result)
            content_chunks = [c for c in chunks if c.get("type") == "content"]

            # Should have separate chunks, not accumulated
            assert len(content_chunks) == 2
            assert content_chunks[0]["content"] == "First"
            assert content_chunks[1]["content"] == " Second"
            # Note: close() is called twice in this test (once for non-streaming, once
            # for streaming)
            assert mock_api_client.close.call_count == 2
