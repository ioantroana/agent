import logging
from typing import Any

from anthropic.types import ToolParam, ToolResultBlockParam, ToolUseBlock
from pydantic import ValidationError

from logging_setup import shorten
from messages import tool_error, tool_result

from .base import Tool, ToolError
from .files import EditFile, ListFiles, ReadFile, WriteFile

# The registry: tool name -> tool object. To add a tool, add it to this list.
tools: dict[str, Tool[Any]] = {tool.name: tool for tool in [ReadFile(), WriteFile(), EditFile(), ListFiles()]}

logger = logging.getLogger(__name__)

def get_definitions() -> list[ToolParam]:
    return [tool.definition() for tool in tools.values()]

def needs_review(name: str) -> bool:
    tool = tools.get(name)
    return tool is not None and tool.needs_review

def run_tool(block: ToolUseBlock) -> ToolResultBlockParam:
    """Run one tool_use block and return its tool_result."""
    tool = tools.get(block.name)
    if tool is None:
        logger.warning("Unknown tool requested: %s", block.name)
        return tool_error(block, f"Unknown tool: {block.name}")

    try:
        args = tool.parse_input(block.input)
    except ValidationError as e:
        # Tell the model exactly which field was wrong, so it can fix the call
        logger.warning("Invalid input for %s: %s", block.name, e)
        return tool_error(block, f"Invalid input: {e}")

    try:
        content = tool.run(args)
    except ToolError as e:
        logger.info("%s failed (expected): %s", block.name, e)
        return tool_error(block, str(e))
    except (OSError, UnicodeDecodeError) as e:
        logger.warning("%s failed: %s", block.name, e)
        return tool_error(block, f"Error: {e}")
    logger.debug("%s result: %s", block.name, shorten(content))
    return tool_result(block, content)
