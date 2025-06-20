"""Data models used throughout the fabric-mcp package."""

from dataclasses import dataclass


@dataclass
class PatternExecutionConfig:  # pylint: disable=too-many-instance-attributes
    """Configuration for pattern execution parameters."""

    model_name: str | None = None
    vendor_name: str | None = None
    strategy_name: str | None = None
    variables: dict[str, str] | None = None
    attachments: list[str] | None = None
    temperature: float | None = None
    top_p: float | None = None
    presence_penalty: float | None = None
    frequency_penalty: float | None = None
