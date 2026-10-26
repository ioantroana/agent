import os

from pydantic import BaseModel, Field

from config import PROJECT_ROOT, SANDBOX_ROOT
from .base import Tool

def resolve_path(path: str, root: str = PROJECT_ROOT) -> str:
    # Resolve relative paths, "..", and symlinks before checking anything
    real_root = os.path.realpath(root)
    full_path = os.path.realpath(os.path.join(real_root, path))
    if full_path != real_root and not full_path.startswith(real_root + os.sep):
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
        return f"Wrote {len(args.content)} characters to {args.path}"


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
        entries = []
        for name in sorted(os.listdir(full_path)):
            if os.path.isdir(os.path.join(full_path, name)):
                name += "/"
            entries.append(name)
        return "\n".join(entries) or "(empty directory)"
