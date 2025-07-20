"""Configuration management for the journaling MCP server."""

from .settings import JournalConfig, load_config

__all__ = ["JournalConfig", "load_config"]