"""Command context and routing for agent execution."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, TYPE_CHECKING

if TYPE_CHECKING:
    from nanobot.bus.events import InboundMessage
    from nanobot.session.manager import Session


@dataclass
class CommandContext:
    """Context for executing a command."""

    msg: InboundMessage
    session: Session | None
    key: str  # session key
    raw: str  # raw message content
    loop: Any  # AgentLoop instance


class CommandRouter:
    """Router for dispatching commands."""

    def __init__(self):
        """Initialize command router."""
        self.commands: dict[str, Callable] = {}

    def register(self, name: str, handler: Callable) -> None:
        """Register a command handler.

        Args:
            name: Command name
            handler: Callable to handle the command
        """
        self.commands[name] = handler

    def get(self, name: str) -> Callable | None:
        """Get a command handler by name.

        Args:
            name: Command name

        Returns:
            Handler or None if not found
        """
        return self.commands.get(name)


def register_builtin_commands(router: CommandRouter) -> None:
    """Register built-in commands with a router.

    Args:
        router: CommandRouter instance
    """
    # Stub implementation - would register help, status, etc.
    pass
