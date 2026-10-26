from anthropic.types import ToolParam, ToolResultBlockParam, ToolUseBlock
from pydantic import ValidationError

from .base import Tool
from .files import ListFiles, ReadFile, WriteFile

# The registry: tool name -> tool object. To add a tool, add it to this list.
tools: dict[str, Tool] = {tool.name: tool for tool in [ReadFile(), WriteFile(), ListFiles()]}

def get_definitions() -> list[ToolParam]:
    return [tool.definition() for tool in tools.values()]

def needs_review(name: str) -> bool:
    tool = tools.get(name)
    return tool is not None and tool.needs_review

def error_result(block: ToolUseBlock, message: str) -> ToolResultBlockParam:
    return {"type": "tool_result", "tool_use_id": block.id, "content": message, "is_error": True}

def run_tool(block: ToolUseBlock) -> ToolResultBlockParam:
    """Run one tool_use block and return its tool_result."""
    tool = tools.get(block.name)
    if tool is None:
        return error_result(block, f"Unknown tool: {block.name}")

    try:
        args = tool.parse_input(block.input)
    except ValidationError as e:
        # Tell the model exactly which field was wrong, so it can fix the call
        return error_result(block, f"Invalid input: {e}")

    try:
        content = tool.run(args)
    except (OSError, UnicodeDecodeError) as e:
        return error_result(block, f"Error: {e}")
    return {"type": "tool_result", "tool_use_id": block.id, "content": content}
