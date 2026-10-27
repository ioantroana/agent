# CLAUDE.md

## How to communicate with me

Write all messages to me in plain language, following ISO 24495-1:2023
(Plain language — Part 1: Governing principles and guidelines).

The standard has four principles. Readers should be able to:

1. **Find** what they need — put the main point or answer first; use headings and lists when a message has several parts.
2. **Understand** what they find — use short sentences, common words and the active voice; explain technical terms the first time you use them.
3. **Use** the information — say clearly what you did, what happened, and what I need to do next.
4. **Get what they need** — leave out padding, repetition and options you are not recommending.

This applies to chat replies, summaries and questions to me. It does not apply to code, code comments or commit messages, which follow the code style below.

## Code style

- **Wrapping:** when a call or definition doesn't fit on one line, put one argument per line, with a trailing comma.
  ```python
  source = Base64PDFSourceParam(
      type="base64",
      media_type="application/pdf",
      data=encoded,
  )
  ```
- **Quotes:** always double quotes. Use single quotes only when the string itself contains a double quote.
- **Comments:** explain *why*, not *what*. Comment reasons, limits and surprises the code can't show by itself. Don't describe what a line plainly does.
- **Constants:** all settings and limits live in `config.py` (model names, sizes, paths, etc.). Modules import them from there.
- **Bad input:** check for problems first and `raise` or `return` early. Keep the main logic unindented; avoid nested `if`/`else` for error cases.
- **Docstrings:** a one-line docstring on functions whose purpose isn't obvious from the name and types. No Args/Returns sections.
- **Logging:** use f-strings in log calls, e.g. `logger.info(f"Wrote {count} characters to {path}")`.
- **Data types:** choose by where the data comes from.
  - Data from outside our code (model output, tool inputs, files, config): Pydantic models, so it is validated.
  - Data our own code creates: frozen dataclasses (`@dataclass(frozen=True)`).
  - SDK request types and other JSON shapes: TypedDicts, as the SDK defines them.
- **Building TypedDicts:** don't write SDK TypedDict constructors or dict literals inline. Wrap them in short, named factory functions (like `user_message()` and `tool_result()` in `messages.py`), so call sites stay short and IntelliJ doesn't warn.
  ```python
  # messages.py
  def pdf_document(data: bytes, title: str) -> DocumentBlockParam:
      return DocumentBlockParam(
          type="document",
          source=Base64PDFSourceParam(
              type="base64",
              media_type="application/pdf",
              data=base64.standard_b64encode(data).decode("ascii"),
          ),
          title=title,
      )

  # tools/read_pdf.py
  return [pdf_document(data, args.path)]
  ```
- **Line length:** 120 characters at most.
- **File layout:** one class per file, named after the class in snake_case (e.g. `ReadPdf` in `tools/read_pdf.py`). A class's own Pydantic input or output model lives in the same file as the class (e.g. `ReadPdfInput` with `ReadPdf`, `Decision` with `Reviewer`). Shared helpers (like `resolve_path`) go in their own module.
- **Type hints:** type every function parameter and return value. All code must pass pyright in strict mode with 0 errors. Local variables may rely on inference when the type is obvious.
- **Imports:** always absolute, from the project root (`from tools.base import Tool`), never relative (`from .base import Tool`).
- **Private names:** prefix helpers that are only used inside their class or module with an underscore (`_call_model`).
- **Fixed choices:** use `Literal` types (`Verdict = Literal["allow", "block"]`), not `Enum`.
