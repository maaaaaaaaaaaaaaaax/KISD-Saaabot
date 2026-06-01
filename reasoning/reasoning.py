"""Reasoning module — orchestrates sign classification to Claude decisions."""

from __future__ import annotations

from ._client import ReasoningSession
from .config import ReasoningConfig


def create_session(config: ReasoningConfig | None = None) -> ReasoningSession:
    """Create a new reasoning session with accumulated conversation history.

    Args:
        config: Optional configuration. Uses defaults (with env-based API key) if None.

    Returns:
        A ReasoningSession instance ready to accept sign labels.
    """
    if config is None:
        config = ReasoningConfig()
    return ReasoningSession(config)


def reason(
    sign_label: str,
    extra_prompt: str | None = None,
    config: ReasoningConfig | None = None,
) -> str:
    """One-shot convenience: send a single sign label and get a response.

    Creates a temporary session with no prior history.
    For accumulated context across multiple signs, use create_session() instead.

    Args:
        sign_label: Classification result string (e.g. "Round-About").
        extra_prompt: Optional additional instruction alongside the sign label.
        config: Optional configuration override.

    Returns:
        Claude's plain-text response.
    """
    session = create_session(config)
    return session.ask(sign_label, extra_prompt)
