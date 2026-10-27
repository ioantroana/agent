"""Small factories for the API's request types, so the verbose TypedDict constructors are written once.

For the assistant's reply there's no factory here: the SDK already has response.to_param().
"""

import base64
from typing import Any

from anthropic.types import (
    Base64PDFSourceParam,
    CacheControlEphemeralParam,
    DocumentBlockParam,
    ToolParam,
    ToolResultBlockParam,
    ToolUseBlock,
    UserMessageParam,
)
from anthropic.types.tool_result_block_param import Content

def user_message(content: str | list[ToolResultBlockParam]) -> UserMessageParam:
    """A user turn: either text the user typed, or the results of tool calls."""
    return UserMessageParam(role="user", content=content)

def tool_result(block: ToolUseBlock, content: str | list[Content]) -> ToolResultBlockParam:
    """A successful result for one tool_use block."""
    return ToolResultBlockParam(type="tool_result", tool_use_id=block.id, content=content)

def tool_error_result(block: ToolUseBlock, message: str) -> ToolResultBlockParam:
    """A failed result for one tool_use block. The model sees the message and can react to it."""
    return ToolResultBlockParam(
        type="tool_result",
        tool_use_id=block.id,
        content=message,
        is_error=True,
    )

def tool_definition(name: str, description: str, input_schema: dict[str, Any]) -> ToolParam:
    return ToolParam(name=name, description=description, input_schema=input_schema)

def pdf_document(data: bytes, title: str) -> DocumentBlockParam:
    """A PDF the model reads directly: each page's text and an image of the page."""
    return DocumentBlockParam(
        type="document",
        source=Base64PDFSourceParam(
            type="base64",
            media_type="application/pdf",
            data=base64.standard_b64encode(data).decode("ascii"),
        ),
        title=title,
    )

def ephemeral_cache() -> CacheControlEphemeralParam:
    """Cache everything up to this point for 5 minutes, so the next request can reuse it."""
    return CacheControlEphemeralParam(type="ephemeral")
