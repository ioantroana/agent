from pydantic import BaseModel, Field

from config import SANDBOX_ROOT
from tools.base import Tool
from tools.paths import resolve_path

class ReadFileInput(BaseModel):
    path: str = Field(description="Path to the file, relative to the sandboxed folder")

class ReadFile(Tool[ReadFileInput]):
    name = "read_file"
    description = "Read the contents of a text file in the sandboxed folder. For PDF files, use read_pdf."
    input_model = ReadFileInput

    def run(self, args: ReadFileInput) -> str:
        full_path = resolve_path(args.path, SANDBOX_ROOT)
        with open(full_path, "r") as f:
            return f.read()
