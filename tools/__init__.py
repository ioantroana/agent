import logging
from typing import Any

from anthropic.types import ToolParam, ToolResultBlockParam, ToolUseBlock
from pydantic import ValidationError

from logging_setup import shorten
from messages import tool_error_result, tool_result
from tools.base import Tool
from tools.edit_file import EditFile
from tools.list_files import ListFiles
from tools.read_file import ReadFile
from tools.read_pdf import ReadPdf
from tools.tool_error import ToolError
from tools.write_file import WriteFile

# The registry: tool name -> tool object. To add a tool, add it to this list.
_tools: dict[str, Tool[Any]] = {
    tool.name: tool for tool in [ReadFile(), ReadPdf(), WriteFile(), EditFile(), ListFiles()]
}

logger = logging.getLogger(__name__)

def get_definitions() -> list[ToolParam]:
    return [tool.definition() for tool in _tools.values()]

def needs_review(name: str) -> bool:
    tool = _tools.get(name)
    return tool is not None and tool.needs_review

def run_tool(block: ToolUseBlock) -> ToolResultBlockParam:
    """Run one tool_use block and return its tool_result."""
    tool = _tools.get(block.name)
    if tool is None:
        logger.warning(f"Unknown tool requested: {block.name}")
        return tool_error_result(block, f"Unknown tool: {block.name}")

    try:
        args = tool.parse_input(block.input)
    except ValidationError as e:
        # Tell the model exactly which field was wrong, so it can fix the call
        logger.warning(f"Invalid input for {block.name}: {e}")
        return tool_error_result(block, f"Invalid input: {e}")

    try:
        content = tool.run(args)
    except ToolError as e:
        logger.info(f"{block.name} failed (expected): {e}")
        return tool_error_result(block, str(e))
    except (OSError, UnicodeDecodeError) as e:
        logger.warning(f"{block.name} failed: {e}")
        return tool_error_result(block, f"Error: {e}")
    if isinstance(content, str):
        logger.debug(f"{block.name} result: {shorten(content)}")
    else:  # blocks like a PDF are mostly base64, which is no use in the log
        logger.debug(f"{block.name} result: {[part["type"] for part in content]}")
    return tool_result(block, content)
