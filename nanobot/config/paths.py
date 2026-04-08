"""Path management for nanobot config and media."""

from pathlib import Path


def get_media_dir(workspace: Path | None = None) -> Path:
    """Get the media directory for storing images, videos, etc.

    Args:
        workspace: Optional workspace path. Defaults to ~/.nanobot/workspace.

    Returns:
        Media directory path
    """
    from nanobot.utils.helpers import get_workspace_path

    ws = workspace or get_workspace_path()
    media_dir = ws / "files" / "media"
    media_dir.mkdir(parents=True, exist_ok=True)
    return media_dir
