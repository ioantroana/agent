import logging
import time

import anthropic
from anthropic.types import MessageParam, TextBlock, ToolResultBlockParam, ToolUseBlock

from config import MODEL, MAX_TOKENS, SYSTEM_PROMPT
from logging_setup import shorten
from messages import tool_error, user_message
from reviewer import Reviewer
from tools import get_definitions, needs_review, run_tool

logger = logging.getLogger(__name__)

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
            logger.debug("Calling %s with %d messages", MODEL, len(self.messages))
            started = time.perf_counter()
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
                logger.exception("API call failed, rolling back this turn")  # also logs the stack trace
                del self.messages[turn_start:]  # drop the unfinished turn so history stays valid
                return

            logger.info(
                "Response in %.1fs: stop_reason=%s, tokens in=%d out=%d",
                time.perf_counter() - started, response.stop_reason,
                response.usage.input_tokens, response.usage.output_tokens,
            )
            text = "".join(block.text for block in response.content if isinstance(block, TextBlock))
            if text:
                logger.info("AI: %s", shorten(text))

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
        logger.info("Tool call %s (id=%s): %s", block.name, block.id, shorten(block.input))
        if needs_review(block.name):
            decision = self.reviewer.review(self.messages, block)
            verdict = "allowed" if decision.allow else "BLOCKED"
            print(f"[reviewer] {verdict}: {decision.reason}")
            logger.log(logging.INFO if decision.allow else logging.WARNING,
                       "Reviewer %s %s: %s", verdict, block.name, decision.reason)
            if not decision.allow:
                return tool_error(block, f"Blocked by reviewer: {decision.reason}")
        return run_tool(block)
