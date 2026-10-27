class ToolError(Exception):
    """Raise this from a tool's run() for an expected failure. The message is sent to the model."""
