import logging

from pydantic import BaseModel, Field

from config import SANDBOX_ROOT
from tools.base import Tool
from tools.paths import resolve_path
from tools.tool_error import ToolError

logger = logging.getLogger(__name__)

class EditFileInput(BaseModel):
    path: str = Field(description="Path to the file, relative to the sandboxed folder")
    old_text: str = Field(description="The exact text to replace, including spaces and line breaks")
    new_text: str = Field(description="The text to put in its place")
    replace_all: bool = Field(
        default=False,
        description="Replace every match. If false, old_text must appear exactly once.",
    )

class EditFile(Tool[EditFileInput]):
    name = "edit_file"
    description = (
        "Replace text in an existing file in the sandboxed folder. "
        "old_text must match the file exactly and, unless replace_all is true, appear exactly once. "
        "Prefer this over write_file when changing part of a file."
    )
    input_model = EditFileInput
    needs_review = True

    def run(self, args: EditFileInput) -> str:
        if not args.old_text:
            raise ToolError("old_text must not be empty")

        full_path = resolve_path(args.path, SANDBOX_ROOT)
        with open(full_path, "r") as f:
            text = f.read()

        # Fail loudly instead of guessing: never edit when the match is missing or ambiguous
        count = text.count(args.old_text)
        if count == 0:
            raise ToolError(f"old_text not found in {args.path}. Read the file again and copy the text exactly.")
        if count > 1 and not args.replace_all:
            raise ToolError(
                f"old_text appears {count} times in {args.path}. "
                "Include more surrounding lines so it matches only once, or set replace_all to true."
            )

        replacements = count if args.replace_all else 1
        text = text.replace(args.old_text, args.new_text, replacements)
        with open(full_path, "w") as f:
            f.write(text)
        logger.info(f"Edited {full_path}: replaced {replacements} occurrence(s)")
        return f"Edited {args.path}: replaced {replacements} occurrence(s)"
