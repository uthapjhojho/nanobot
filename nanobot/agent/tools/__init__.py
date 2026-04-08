"""Agent tools module."""

# Core base classes and decorators
from nanobot.agent.tools.base import Schema, Tool, tool_parameters

# Schema types for parameter validation
from nanobot.agent.tools.schema import (
    ArraySchema,
    BooleanSchema,
    IntegerSchema,
    NumberSchema,
    ObjectSchema,
    StringSchema,
    tool_parameters_schema,
)

# Tool registry
from nanobot.agent.tools.registry import ToolRegistry

# Filesystem tools (adopted upstream)
from nanobot.agent.tools.filesystem import (
    EditFileTool,
    ListDirTool,
    ReadFileTool,
    WriteFileTool,
)

# Shell execution tool (adopted upstream)
from nanobot.agent.tools.shell import ExecTool

# Web tools (adopted upstream)
from nanobot.agent.tools.web import WebFetchTool, WebSearchTool

# Search tools (adopted upstream)
from nanobot.agent.tools.search import GlobTool, GrepTool

# Sandbox utilities (adopted upstream)
from nanobot.agent.tools.sandbox import wrap_command

# Local/preserved tools
from nanobot.agent.tools.cron import CronTool
from nanobot.agent.tools.mcp import MCPToolWrapper
from nanobot.agent.tools.message import MessageTool
from nanobot.agent.tools.spawn import SpawnTool

__all__ = [
    # Base classes and utilities
    "Schema",
    "Tool",
    "tool_parameters",
    "ToolRegistry",
    # Schema types
    "StringSchema",
    "IntegerSchema",
    "NumberSchema",
    "BooleanSchema",
    "ArraySchema",
    "ObjectSchema",
    "tool_parameters_schema",
    # Filesystem tools
    "ReadFileTool",
    "WriteFileTool",
    "EditFileTool",
    "ListDirTool",
    # Shell tool
    "ExecTool",
    # Web tools
    "WebSearchTool",
    "WebFetchTool",
    # Search tools
    "GlobTool",
    "GrepTool",
    # Sandbox
    "wrap_command",
    # Local/preserved tools
    "CronTool",
    "MCPToolWrapper",
    "MessageTool",
    "SpawnTool",
]
