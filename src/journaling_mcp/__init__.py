"""
MCP Journaling Server Package

A professional MCP server for interactive journaling with emotional analysis
and automatic conversation saving.
"""

from .server import create_server

__version__ = "0.2.0"
__all__ = ["create_server"]