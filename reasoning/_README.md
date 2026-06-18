# Reasoning Module

Claude-based commentary session for detected traffic signs. Maintains a running conversation across multiple signs within a single route, giving the model context about the sequence of decisions made by the vehicle.

## Usage

```python
from reasoning import create_session, ReasoningConfig

config = ReasoningConfig()
session = create_session(config)

text = session.ask("Stop")
print(text)   # Claude's driving commentary for this sign

text = session.ask("Speed-Limit-30")
print(text)   # Claude sees the full prior exchange as context

session.reset()  # clear history for a new route
```

## One-shot convenience

```python
from reasoning import reason

text = reason("Stop")
# Creates a fresh session, sends once, returns text
```

## Configuration

```python
from reasoning import ReasoningConfig

config = ReasoningConfig(
    model="claude-sonnet-4-6",   # default
    max_tokens=1024,             # default
    use_mock=False,              # set True for offline / local mode
    mock_response_text="...",    # returned instead of calling the API when use_mock=True
)
```

Requires `ANTHROPIC_API_KEY` in the environment (or `.env` file) when `use_mock=False`.

## Architecture

| File           | Purpose                                                             |
| -------------- | ------------------------------------------------------------------- |
| `config.py`    | `ReasoningConfig` dataclass — model, prompt, mock settings          |
| `_client.py`   | `ReasoningSession` — manages conversation history, calls Claude API |
| `reasoning.py` | `create_session()` and `reason()` public API                        |

## How the session works

`ReasoningSession` keeps a running `list[MessageParam]`. Each call to `ask(sign_label)`:

1. Appends `"Detected sign: {label}"` as a user message.
2. Calls `anthropic.Anthropic.messages.create()` with the full history and the configured `base_prompt` as the system prompt.
3. Appends the assistant response to history.
4. Returns the response text.

The base prompt instructs Claude to act as a traffic-sign decision system and produce plain text output suitable for thermal printing — short, no markdown.

In mock mode, `ask()` appends the `mock_response_text` directly to history without calling the API.
