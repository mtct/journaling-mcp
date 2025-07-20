"""Journal-related exceptions."""

from .base import JournalingError


class JournalError(JournalingError):
    """Base exception for journal-related operations."""
    pass


class JournalNotFoundError(JournalError):
    """Raised when a requested journal entry is not found."""
    pass


class InvalidJournalPathError(JournalError):
    """Raised when an invalid journal path is provided."""
    pass