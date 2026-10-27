import logging
import os

from pydantic import BaseModel, Field

from config import MAX_PDF_BYTES, SANDBOX_ROOT
from messages import pdf_document
from tools.base import Tool, ToolOutput
from tools.paths import resolve_path
from tools.tool_error import ToolError

logger = logging.getLogger(__name__)

class ReadPdfInput(BaseModel):
    path: str = Field(description="Path to the PDF file, relative to the sandboxed folder")

class ReadPdf(Tool[ReadPdfInput]):
    name = "read_pdf"
    description = (
        "Read a PDF file in the sandboxed folder. You see each page's text and its images, "
        "so tables, charts and scanned pages work too."
    )
    input_model = ReadPdfInput

    def run(self, args: ReadPdfInput) -> ToolOutput:
        full_path = resolve_path(args.path, SANDBOX_ROOT)
        size = os.path.getsize(full_path)
        if size > MAX_PDF_BYTES:
            raise ToolError(
                f"{args.path} is {size // (1024 * 1024)} MB; the limit is {MAX_PDF_BYTES // (1024 * 1024)} MB"
            )
        with open(full_path, "rb") as f:
            data = f.read()
        if not data.startswith(b"%PDF"):  # every PDF file starts with these bytes
            raise ToolError(f"{args.path} is not a PDF file")

        logger.info(f"Sending PDF {full_path} ({size} bytes) to the model")
        # Send the file itself, not extracted text: the model reads the pages directly
        return [pdf_document(data, args.path)]
