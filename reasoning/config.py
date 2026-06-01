"""Configuration for the reasoning module."""

import os
from dataclasses import dataclass, field

BASE_PROMPT = (
    "You are a decision-making system embedded in a mobile device that observes "
    "traffic signs in real-time. You receive the classified name of a traffic sign "
    "and must reason about what action or information is relevant for the user. "
    "Respond in plain text only — no markdown, no HTML, no bullet points. "
    "Keep responses concise and direct, suitable for printing on a thermal receipt."
)


@dataclass
class ReasoningConfig:
    """Configuration for the Claude reasoning module.

    Args:
        api_key: Anthropic API key (falls back to ANTHROPIC_API_KEY env var).
        model: Claude model identifier.
        base_prompt: System prompt defining Claude's role and behaviour.
        max_tokens: Maximum tokens in Claude's response.
    """

    api_key: str = ""
    model: str = "claude-sonnet-4-6"
    base_prompt: str = field(default=BASE_PROMPT)
    max_tokens: int = 1024

    def __post_init__(self) -> None:
        if not self.api_key:
            self.api_key = os.environ.get("ANTHROPIC_API_KEY", "")
        if not self.api_key:
            raise ValueError(
                "Missing Anthropic API key. "
                "Set ANTHROPIC_API_KEY env var or pass api_key to ReasoningConfig."
            )
