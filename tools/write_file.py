import logging
import os

from pydantic import BaseModel, Field

from config import SANDBOX_ROOT
from tools.base import Tool
from tools.paths import resolve_path

logger = logging.getLogger(__name__)

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
        with open(full_path, "w") as f:
            f.write(args.content)
        logger.info(f"Wrote {len(args.content)} characters to {full_path}")
        return f"Wrote {len(args.content)} characters to {args.path}"
