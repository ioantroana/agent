import json

import anthropic
from anthropic.types import MessageParam, TextBlock, ToolUseBlock
from pydantic import BaseModel

from config import REVIEWER_MODEL, REVIEWER_PROMPT, REVIEWER_HISTORY

class Decision(BaseModel):
    allow: bool
    reason: str

def build_transcript(messages: list[MessageParam]) -> str:
    """Turn the conversation into plain 'User: ...' / 'Assistant: ...' lines.

    Tool results (like file contents) are left out on purpose: they can contain
    text written by anyone, and we don't want that text steering the reviewer.
    """
    lines = []
    for message in messages:
        content = message["content"]
        if message["role"] == "user":
            if isinstance(content, str):  # typed by the user; lists are tool results
                lines.append(f"User: {content}")
        elif not isinstance(content, str):
            text = "".join(block.text for block in content if isinstance(block, TextBlock))
            if text:
                lines.append(f"Assistant: {text}")
    return "\n\n".join(lines[-REVIEWER_HISTORY:])

class Reviewer:
    def __init__(self, client: anthropic.Anthropic) -> None:
        self.client = client

    def review(self, messages: list[MessageParam], block: ToolUseBlock) -> Decision:
        """Ask a second model whether this tool call should run. Returns a Decision."""
        proposal = (
            f"Recent conversation:\n\n{build_transcript(messages)}\n\n"
            f"---\n\nThe assistant now wants to call the tool '{block.name}' with this input:\n"
            f"{json.dumps(block.input, indent=2)}"
        )
        try:
            # parse() makes the model answer in the shape of Decision, so we never parse text by hand
            response = self.client.messages.parse(
                model=REVIEWER_MODEL,
                system=REVIEWER_PROMPT,
                max_tokens=1024,
                messages=[{"role": "user", "content": proposal}],
                output_format=Decision,
            )
        except anthropic.APIError as e:
            # If the reviewer can't answer, block the change: unsafe by default is worse
            return Decision(allow=False, reason=f"Reviewer unavailable: {e}")

        if response.parsed_output is None:
            return Decision(allow=False, reason="Reviewer gave no decision")
        return response.parsed_output
