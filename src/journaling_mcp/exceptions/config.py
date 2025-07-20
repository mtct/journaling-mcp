"""Configuration-related exceptions."""

from .base import JournalingError


class ConfigurationError(JournalingError):
    """Raised when there's an error in configuration."""
    pass