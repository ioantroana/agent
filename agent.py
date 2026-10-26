import anthropic
from anthropic.types import MessageParam, ToolResultBlockParam, ToolUseBlock

from config import MODEL, MAX_TOKENS, SYSTEM_PROMPT
from messages import tool_error, user_message
from reviewer import Reviewer
from tools import get_definitions, needs_review, run_tool

class Agent:
    def __init__(self) -> None:
        self.client = anthropic.Anthropic()
        self.reviewer = Reviewer(self.client)
        self.messages: list[MessageParam] = []

    def send(self, user_input: str) -> None:
        """Handle one user message: call the model and run tools until it's done."""
        turn_start = len(self.messages)  # so we can roll back this whole turn if the API fails
        self.messages.append(user_message(user_input))

        while True:
            try:
                print("AI: ", end="")
                with self.client.messages.stream(
                    model=MODEL,
                    system=SYSTEM_PROMPT,
                    max_tokens=MAX_TOKENS,
                    messages=self.messages,
                    tools=get_definitions()
                ) as stream:
                    for text in stream.text_stream:
                        print(text, end="", flush=True)  # show each piece as soon as it arrives
                    response = stream.get_final_message()
                print()
            except anthropic.APIError as e:
                print(f"\nAPI error: {e}")
                del self.messages[turn_start:]  # drop the unfinished turn so history stays valid
                return

            self.messages.append(response.to_param())

            if response.stop_reason != "tool_use":
                return

            # Run every tool the model asked for, then send all results back in one message
            tool_results: list[ToolResultBlockParam] = []
            for block in response.content:
                if isinstance(block, ToolUseBlock):
                    tool_results.append(self.handle_tool_call(block))

            self.messages.append(user_message(tool_results))

    def handle_tool_call(self, block: ToolUseBlock) -> ToolResultBlockParam:
        """Ask the reviewer if needed, then run the tool."""
        print(f"[tool] {block.name}({block.input})")
        if needs_review(block.name):
            decision = self.reviewer.review(self.messages, block)
            verdict = "allowed" if decision.allow else "BLOCKED"
            print(f"[reviewer] {verdict}: {decision.reason}")
            if not decision.allow:
                return tool_error(block, f"Blocked by reviewer: {decision.reason}")
        return run_tool(block)
