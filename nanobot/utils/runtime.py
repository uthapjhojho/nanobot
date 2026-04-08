"""Runtime utilities for agent execution."""

# Default message when agent returns empty response
EMPTY_FINAL_RESPONSE_MESSAGE = "I encountered an issue processing your request. Please try again."


def build_finalization_retry_message() -> str:
    """Build a message to prompt agent to retry and finalize response.

    Returns:
        Retry prompt message
    """
    return "Please try again and provide a complete response."


def ensure_nonempty_tool_result(tool_name: str, result: any) -> any:
    """Ensure tool result is not empty, add default message if needed.

    Args:
        tool_name: Name of the tool that produced the result
        result: Tool result

    Returns:
        Non-empty result with default message if needed
    """
    if not result or (isinstance(result, str) and not result.strip()):
        return f"{tool_name} returned no output."
    return result


def is_blank_text(text: str) -> bool:
    """Check if text is blank or only whitespace.

    Args:
        text: Text to check

    Returns:
        True if text is blank or whitespace only
    """
    return not text or not text.strip()


def repeated_external_lookup_error(tool_name: str, attempts: int) -> str:
    """Build error message for repeated external lookup failures.

    Args:
        tool_name: Name of the tool
        attempts: Number of failed attempts

    Returns:
        Error message
    """
    return f"{tool_name} failed after {attempts} attempts. Please try a different approach."
