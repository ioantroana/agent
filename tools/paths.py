import logging
import os

from config import PROJECT_ROOT

logger = logging.getLogger(__name__)

def resolve_path(path: str, root: str = PROJECT_ROOT) -> str:
    # Resolve relative paths, "..", and symlinks before checking anything
    real_root = os.path.realpath(root)
    full_path = os.path.realpath(os.path.join(real_root, path))
    if full_path != real_root and not full_path.startswith(real_root + os.sep):
        logger.warning(f"Blocked access outside {root}: {path} (resolved to {full_path})")
        raise PermissionError(f"Access denied: {path} is outside {root}")
    return full_path
