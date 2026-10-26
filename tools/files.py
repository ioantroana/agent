import logging
import os

from pydantic import BaseModel, Field

from config import PROJECT_ROOT, SANDBOX_ROOT
from .base import Tool, ToolError

logger = logging.getLogger(__name__)

def resolve_path(path: str, root: str = PROJECT_ROOT) -> str:
    # Resolve relative paths, "..", and symlinks before checking anything
    real_root = os.path.realpath(root)
    full_path = os.path.realpath(os.path.join(real_root, path))
    if full_path != real_root and not full_path.startswith(real_root + os.sep):
        logger.warning("Blocked access outside %s: %s (resolved to %s)", root, path, full_path)
        raise PermissionError(f"Access denied: {path} is outside {root}")
    return full_path


class ReadFileInput(BaseModel):
    path: str = Field(description="Path to the file, relative to the sandboxed folder")

class ReadFile(Tool[ReadFileInput]):
    name = "read_file"
    description = "Read the contents of a file in the sandboxed folder"
    input_model = ReadFileInput

    def run(self, args: ReadFileInput) -> str:
        full_path = resolve_path(args.path, SANDBOX_ROOT)
        with open(full_path, 'r') as f:
            return f.read()


class WriteFileInput(BaseModel):
    path: str = Field(description="Path to the file, relative to the sandboxed folder")
    content: str = Field(description="The full text to write to the file")

class WriteFile(Tool[WriteFileInput]):
    name = "write_file"
    description = "Create or overwrite a file in the sandboxed folder. Creates missing subfolders."
    input_model = WriteFileInput
    needs_review = True

    def run(self, args: WriteFileInput) -> str:
        full_path = resolve_path(args.path, SANDBOX_ROOT)
        os.makedirs(os.path.dirname(full_path), exist_ok=True)  # create the sandbox and any subfolders
        with open(full_path, 'w') as f:
            f.write(args.content)
        logger.info("Wrote %d characters to %s", len(args.content), full_path)
        return f"Wrote {len(args.content)} characters to {args.path}"


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
        with open(full_path, 'r') as f:
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
        with open(full_path, 'w') as f:
            f.write(text)
        logger.info("Edited %s: replaced %d occurrence(s)", full_path, replacements)
        return f"Edited {args.path}: replaced {replacements} occurrence(s)"


class ListFilesInput(BaseModel):
    path: str = Field(
        default=".",
        description="Directory to list, relative to the sandboxed folder. Defaults to the sandboxed folder itself.",
    )

class ListFiles(Tool[ListFilesInput]):
    name = "list_files"
    description = "List the files and folders in a directory in the sandboxed folder. Folders end with '/'."
    input_model = ListFilesInput

    def run(self, args: ListFilesInput) -> str:
        full_path = resolve_path(args.path, SANDBOX_ROOT)
        if not os.path.exists(SANDBOX_ROOT):
            return "(sandbox is empty)"  # write_file creates the folder on first use
        entries: list[str] = []
        for name in sorted(os.listdir(full_path)):
            if os.path.isdir(os.path.join(full_path, name)):
                name += "/"
            entries.append(name)
        return "\n".join(entries) or "(empty directory)"
