"""Small factories for the messages we send to the API, so the role and type are written once.

For the assistant's reply there's no factory here: the SDK already has response.to_param().
"""

from anthropic.types import ToolResultBlockParam, ToolUseBlock, UserMessageParam

def user_message(content: str | list[ToolResultBlockParam]) -> UserMessageParam:
    """A user turn: either text the user typed, or the results of tool calls."""
    return UserMessageParam(role="user", content=content)

def tool_result(block: ToolUseBlock, content: str) -> ToolResultBlockParam:
    """A successful result for one tool_use block."""
    return ToolResultBlockParam(type="tool_result", tool_use_id=block.id, content=content)

def tool_error(block: ToolUseBlock, message: str) -> ToolResultBlockParam:
    """A failed result for one tool_use block. The model sees the message and can react to it."""
    return ToolResultBlockParam(type="tool_result", tool_use_id=block.id, content=message, is_error=True)
