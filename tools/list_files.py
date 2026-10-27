import os

from pydantic import BaseModel, Field

from config import SANDBOX_ROOT
from tools.base import Tool
from tools.paths import resolve_path

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
