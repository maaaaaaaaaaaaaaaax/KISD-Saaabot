"""Anthropic API client wrapper with conversation history."""

from __future__ import annotations

from anthropic import Anthropic

from .config import ReasoningConfig


class ReasoningSession:
    """A chat session that accumulates context across multiple sign observations.

    Each call to ask() appends to the conversation history so Claude can reason
    about sequences of signs (e.g. approaching an intersection).
    """

    def __init__(self, config: ReasoningConfig) -> None:
        self._config = config
        self._client = Anthropic(api_key=config.api_key)
        self._history: list[dict[str, str]] = []

    @property
    def history(self) -> list[dict[str, str]]:
        """Current conversation history."""
        return list(self._history)

    def ask(self, sign_label: str, extra_prompt: str | None = None) -> str:
        """Send a classified sign label to Claude and return the response.

        Args:
            sign_label: Classification result string (e.g. "Round-About").
            extra_prompt: Optional additional instruction appended to the user message.

        Returns:
            Claude's plain-text response.
        """
        user_content = f"Detected sign: {sign_label}"
        if extra_prompt:
            user_content = f"{user_content}\n{extra_prompt}"

        self._history.append({"role": "user", "content": user_content})

        response = self._client.messages.create(
            model=self._config.model,
            max_tokens=self._config.max_tokens,
            system=self._config.base_prompt,
            messages=self._history,
        )

        assistant_text = response.content[0].text
        self._history.append({"role": "assistant", "content": assistant_text})

        return assistant_text

    def reset(self) -> None:
        """Clear conversation history to start a fresh session."""
        self._history.clear()
