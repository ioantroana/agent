from typing import Protocol

class AgentUI(Protocol):
    """What the agent reports while it works. The agent never prints; a UI decides how to show things."""

    def text(self, chunk: str) -> None:
        """A piece of the model's reply, as it streams in."""
        ...

    def text_done(self) -> None:
        """The model finished one reply (it may still call tools after this)."""
        ...

    def tool_call(self, name: str, tool_input: object) -> None: ...

    def review(self, name: str, allowed: bool) -> None: ...

    def error(self, message: str) -> None: ...

    def confirm(self, question: str) -> bool:
        """Ask the user a yes/no question. Anything other than a clear yes means no."""
        ...
