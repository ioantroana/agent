from typing import Any

from anthropic.types import ToolParam, ToolResultBlockParam, ToolUseBlock
from pydantic import ValidationError

from messages import tool_error, tool_result

from .base import Tool
from .files import ListFiles, ReadFile, WriteFile

# The registry: tool name -> tool object. To add a tool, add it to this list.
tools: dict[str, Tool[Any]] = {tool.name: tool for tool in [ReadFile(), WriteFile(), ListFiles()]}

def get_definitions() -> list[ToolParam]:
    return [tool.definition() for tool in tools.values()]

def needs_review(name: str) -> bool:
    tool = tools.get(name)
    return tool is not None and tool.needs_review

def run_tool(block: ToolUseBlock) -> ToolResultBlockParam:
    """Run one tool_use block and return its tool_result."""
    tool = tools.get(block.name)
    if tool is None:
        return tool_error(block, f"Unknown tool: {block.name}")

    try:
        args = tool.parse_input(block.input)
    except ValidationError as e:
        # Tell the model exactly which field was wrong, so it can fix the call
        return tool_error(block, f"Invalid input: {e}")

    try:
        content = tool.run(args)
    except (OSError, UnicodeDecodeError) as e:
        return tool_error(block, f"Error: {e}")
    return tool_result(block, content)
