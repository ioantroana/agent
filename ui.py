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


class TerminalUI(AgentUI):
    """Shows the agent's work in the terminal."""

    def __init__(self) -> None:
        self._in_text = False  # are we in the middle of printing a reply?

    def text(self, chunk: str) -> None:
        if not self._in_text:
            print("AI: ", end="")  # only when there's text, so tool-only replies don't print an empty "AI:"
            self._in_text = True
        print(chunk, end="", flush=True)  # show each piece as soon as it arrives

    def text_done(self) -> None:
        if self._in_text:
            print()
            self._in_text = False

    def tool_call(self, name: str, tool_input: object) -> None:
        print(f"[tool] {name}({tool_input})")

    def review(self, name: str, allowed: bool) -> None:
        print(f"[reviewer] {'allowed' if allowed else 'BLOCKED'}")

    def error(self, message: str) -> None:
        self.text_done()  # end a half-printed reply first
        print(f"Error: {message}")

    def confirm(self, question: str) -> bool:
        self.text_done()
        try:
            answer = input(f"{question} [y/N] ")
        except (KeyboardInterrupt, EOFError):  # Ctrl+C, Ctrl+D, or no terminal to ask (e.g. piped input)
            print()
            return False
        return answer.strip().lower() in ("y", "yes")
