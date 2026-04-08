"""Utility functions for nanobot."""

from pathlib import Path
from datetime import datetime
import time


def ensure_dir(path: Path) -> Path:
    """Ensure a directory exists, creating it if necessary."""
    path.mkdir(parents=True, exist_ok=True)
    return path


def get_data_path() -> Path:
    """Get the nanobot data directory (~/.nanobot)."""
    return ensure_dir(Path.home() / ".nanobot")


def get_workspace_path(workspace: str | None = None) -> Path:
    """
    Get the workspace path.
    
    Args:
        workspace: Optional workspace path. Defaults to ~/.nanobot/workspace.
    
    Returns:
        Expanded and ensured workspace path.
    """
    if workspace:
        path = Path(workspace).expanduser()
    else:
        path = Path.home() / ".nanobot" / "workspace"
    return ensure_dir(path)


def get_sessions_path() -> Path:
    """Get the sessions storage directory."""
    return ensure_dir(get_data_path() / "sessions")


def get_skills_path(workspace: Path | None = None) -> Path:
    """Get the skills directory within the workspace."""
    ws = workspace or get_workspace_path()
    return ensure_dir(ws / "skills")


def timestamp() -> str:
    """Get current timestamp in ISO format."""
    return datetime.now().isoformat()


def current_time_str(timezone: str | None = None) -> str:
    """Return the current time string with timezone info.

    Args:
        timezone: Optional IANA timezone name (e.g. "Asia/Shanghai").
                 Falls back to host local time if invalid.

    Returns:
        Formatted time string with weekday and UTC offset.
    """
    from zoneinfo import ZoneInfo

    try:
        tz = ZoneInfo(timezone) if timezone else None
    except (KeyError, Exception):
        tz = None

    now = datetime.now(tz=tz) if tz else datetime.now().astimezone()
    offset = now.strftime("%z")
    offset_fmt = f"{offset[:3]}:{offset[3:]}" if len(offset) == 5 else offset
    tz_name = timezone or (time.strftime("%Z") or "UTC")
    return f"{now.strftime('%Y-%m-%d %H:%M (%A)')} ({tz_name}, UTC{offset_fmt})"


def truncate_string(s: str, max_len: int = 100, suffix: str = "...") -> str:
    """Truncate a string to max length, adding suffix if truncated."""
    if len(s) <= max_len:
        return s
    return s[: max_len - len(suffix)] + suffix


def safe_filename(name: str) -> str:
    """Convert a string to a safe filename."""
    # Replace unsafe characters
    unsafe = '<>:"/\\|?*'
    for char in unsafe:
        name = name.replace(char, "_")
    return name.strip()


def image_placeholder_text(path: str | None, *, empty: str = "[image]") -> str:
    """Build an image placeholder string.

    Args:
        path: Optional path to the image file.
        empty: Text to return when path is None.

    Returns:
        Placeholder text for the image.
    """
    return f"[image: {path}]" if path else empty


def parse_session_key(key: str) -> tuple[str, str]:
    """
    Parse a session key into channel and chat_id.

    Args:
        key: Session key in format "channel:chat_id"

    Returns:
        Tuple of (channel, chat_id)
    """
    parts = key.split(":", 1)
    if len(parts) != 2:
        raise ValueError(f"Invalid session key: {key}")
    return parts[0], parts[1]


def strip_think(text: str) -> str:
    """Remove <think>...</think> tags from text (LLM thinking blocks).

    Args:
        text: Text possibly containing <think> tags

    Returns:
        Text with <think> tags removed
    """
    import re
    return re.sub(r'<think>.*?</think>', '', text, flags=re.DOTALL).strip()


def estimate_message_tokens(message: dict) -> int:
    """Estimate token count for a single message.

    Uses a rough heuristic: ~4 characters per token average.
    Accounts for role, content, and tool calls.

    Args:
        message: Message dict with 'role' and 'content' keys

    Returns:
        Estimated token count
    """
    content = message.get('content', '')
    if isinstance(content, list):
        # Tool use content
        content = str(content)

    # Rough heuristic: 4 chars per token
    text_tokens = len(content) // 4

    # Add overhead for role and structure
    role_tokens = 3

    # Account for tool calls if present
    tool_tokens = 0
    if 'tool_use' in message:
        tool_tokens = len(str(message.get('tool_use', {}))) // 4

    return max(1, text_tokens + role_tokens + tool_tokens)


def estimate_prompt_tokens_chain(provider, model: str, messages: list[dict], tools: list) -> tuple[int, str]:
    """Estimate total tokens for a complete prompt chain.

    Includes messages, system prompt, tool definitions, and overhead.

    Args:
        provider: LLM provider instance
        model: Model name string
        messages: List of message dicts
        tools: List of tool definitions

    Returns:
        Tuple of (estimated_token_count, model_name)
    """
    total = 0

    # Count message tokens
    for msg in messages:
        total += estimate_message_tokens(msg)

    # System prompt overhead (~500 tokens for a typical system prompt)
    total += 500

    # Tool definitions (rough estimate: ~100 tokens per tool)
    total += len(tools) * 100

    # Add overhead for structure and formatting
    total += 200

    return (total, model)


def build_assistant_message(
    content: str,
    *,
    tool_calls: list = None,
    reasoning_content: str = None,
    thinking_blocks: list = None,
) -> dict:
    """Build an assistant message dict with optional tool calls.

    Args:
        content: Main content from the assistant
        tool_calls: Optional list of tool call objects (OpenAI format)
        reasoning_content: Optional reasoning/planning content
        thinking_blocks: Optional thinking block content

    Returns:
        Message dict with role='assistant' and content/tool_calls
    """
    msg = {
        "role": "assistant",
        "content": content or "",
    }
    if tool_calls:
        msg["tool_calls"] = tool_calls
    if reasoning_content:
        msg["reasoning_content"] = reasoning_content
    if thinking_blocks:
        msg["thinking_blocks"] = thinking_blocks
    return msg


def find_legal_message_start(messages: list[dict]) -> int | None:
    """Find the index of the first user message in a message list.

    Used to find legal message boundaries for partitioning.

    Args:
        messages: List of message dicts

    Returns:
        Index of first user message, or None if not found
    """
    for i, msg in enumerate(messages):
        if msg.get("role") == "user":
            return i
    return None


def maybe_persist_tool_result(
    workspace: Path,
    session_key: str,
    tool_call_id: str,
    result: any,
    max_chars: int = 50000,
) -> str:
    """Maybe persist a tool result to disk and return content.

    If result is large, persists to file and returns reference.
    Otherwise returns result as string.

    Args:
        workspace: Workspace path
        session_key: Session key (channel:chat_id)
        tool_call_id: Tool call ID
        result: Tool result to persist
        max_chars: Threshold for persistence

    Returns:
        Content string (result or file reference)
    """
    result_str = str(result) if not isinstance(result, str) else result

    # For now, just return the result string
    # Full implementation would persist to files/.toolresults/
    return result_str


def detect_image_mime(raw: bytes) -> str | None:
    """Detect MIME type from raw image bytes.

    Args:
        raw: Raw image bytes

    Returns:
        MIME type string (e.g., 'image/png') or None
    """
    if not raw or len(raw) < 4:
        return None

    # PNG: 89 50 4E 47
    if raw[:4] == b'\x89PNG':
        return 'image/png'
    # JPEG: FF D8 FF
    if raw[:3] == b'\xff\xd8\xff':
        return 'image/jpeg'
    # GIF: 47 49 46 (GIF8 or GIF9)
    if raw[:3] == b'GIF':
        return 'image/gif'
    # WebP: RIFF ... WEBP
    if raw[:4] == b'RIFF' and len(raw) > 12 and raw[8:12] == b'WEBP':
        return 'image/webp'

    return None


def build_image_content_blocks(
    raw: bytes,
    mime: str,
    path: str,
    caption: str = "",
) -> list[dict]:
    """Build image content blocks for the LLM.

    Creates OpenAI-compatible image content blocks from raw image data.

    Args:
        raw: Raw image bytes
        mime: MIME type (e.g., 'image/png')
        path: File path for reference
        caption: Optional caption/description

    Returns:
        List of content block dicts
    """
    import base64

    blocks = []

    # Add image block with base64 encoding
    image_block = {
        "type": "image_url",
        "image_url": {
            "url": f"data:{mime};base64,{base64.b64encode(raw).decode('utf-8')}",
            "detail": "auto",
        },
    }
    blocks.append(image_block)

    # Add caption if provided
    if caption:
        caption_block = {
            "type": "text",
            "text": caption,
        }
        blocks.append(caption_block)

    return blocks


def truncate_text(text: str, max_len: int, suffix: str = "...") -> str:
    """Truncate text to maximum length (alias for truncate_string)."""
    return truncate_string(text, max_len, suffix)
