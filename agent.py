import logging
import time

import anthropic
from anthropic.types import Message, MessageParam, TextBlock, ToolResultBlockParam, ToolUseBlock

from config import MODEL, MAX_TOKENS, SYSTEM_PROMPT
from logging_setup import shorten
from messages import tool_error, user_message
from reviewer import Reviewer
from tools import get_definitions, needs_review, run_tool
from ui import AgentUI

logger = logging.getLogger(__name__)

class Agent:
    def __init__(self, ui: AgentUI) -> None:
        self.ui = ui  # everything the user should see goes through here
        self.client = anthropic.Anthropic()
        self.reviewer = Reviewer(self.client)
        self.messages: list[MessageParam] = []

    def send(self, user_input: str) -> None:
        """Handle one user message: call the model and run tools until it's done."""
        turn_start = len(self.messages)  # so we can roll back this whole turn if the API fails
        self.messages.append(user_message(user_input))

        try:
            while True:
                response = self._call_model()
                self.messages.append(response.to_param())
                if response.stop_reason != "tool_use":
                    return
                self.messages.append(user_message(self._run_tools(response)))
        except anthropic.APIError as e:
            self.ui.error(f"API error: {e}")
            logger.exception("API call failed, rolling back this turn")  # also logs the stack trace
            del self.messages[turn_start:]  # drop the unfinished turn so history stays valid

    def _call_model(self) -> Message:
        """Send the conversation to the model, pass the reply to the UI as it streams in, and return it."""
        logger.debug("Calling %s with %d messages", MODEL, len(self.messages))
        started = time.perf_counter()

        with self.client.messages.stream(
            model=MODEL,
            system=SYSTEM_PROMPT,
            max_tokens=MAX_TOKENS,
            messages=self.messages,
            tools=get_definitions()
        ) as stream:
            for chunk in stream.text_stream:
                self.ui.text(chunk)
            response = stream.get_final_message()
        self.ui.text_done()

        logger.info(
            "Response in %.1fs: stop_reason=%s, tokens in=%d out=%d",
            time.perf_counter() - started, response.stop_reason, response.usage.input_tokens, response.usage.output_tokens,
        )
        text = "".join(block.text for block in response.content if isinstance(block, TextBlock))
        if text:
            logger.info("AI: %s", shorten(text))
            
        return response

    def _run_tools(self, response: Message) -> list[ToolResultBlockParam]:
        """Run every tool the model asked for. All results go back to the model in one message."""
        return [self._handle_tool_call(block) for block in response.content if isinstance(block, ToolUseBlock)]

    def _handle_tool_call(self, block: ToolUseBlock) -> ToolResultBlockParam:
        """Ask the reviewer if needed, then run the tool."""
        self.ui.tool_call(block.name, block.input)
        logger.info("Tool call %s (id=%s): %s", block.name, block.id, shorten(block.input))
        if needs_review(block.name) and not self._is_allowed(block):
            # Don't tell the agent why, so it can't tailor a retry to slip past the reviewer
            return tool_error(block, "Blocked by reviewer.")
        return run_tool(block)

    def _is_allowed(self, block: ToolUseBlock) -> bool:
        """Ask the reviewer about this tool call. The reason only goes to the log file."""
        decision = self.reviewer.review(self.messages, block)
        verdict = "allowed" if decision.allow else "BLOCKED"
        self.ui.review(block.name, decision.allow)
        logger.log(logging.INFO if decision.allow else logging.WARNING,
                   "Reviewer %s %s: %s", verdict, block.name, decision.reason)
        return decision.allow
