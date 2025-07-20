"""Conversation data models."""

from datetime import datetime
from typing import List, Dict, Any, Literal
from dataclasses import dataclass, field
from enum import Enum


class SpeakerType(str, Enum):
    """Types of speakers in a conversation."""
    USER = "user"
    ASSISTANT = "assistant"


@dataclass
class ConversationEntry:
    """Represents a single message in a conversation."""
    
    speaker: SpeakerType
    message: str
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "speaker": self.speaker.value,
            "message": self.message,
            "timestamp": self.timestamp.isoformat(),
            "metadata": self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ConversationEntry":
        """Create instance from dictionary."""
        return cls(
            speaker=SpeakerType(data["speaker"]),
            message=data["message"],
            timestamp=datetime.fromisoformat(data["timestamp"]),
            metadata=data.get("metadata", {})
        )


@dataclass
class ConversationLog:
    """Manages a collection of conversation entries."""
    
    entries: List[ConversationEntry] = field(default_factory=list)
    session_id: str = field(default_factory=lambda: datetime.now().strftime("%Y%m%d_%H%M%S"))
    
    def add_entry(self, speaker: SpeakerType, message: str, metadata: Dict[str, Any] = None) -> None:
        """Add a new conversation entry."""
        entry = ConversationEntry(
            speaker=speaker,
            message=message,
            metadata=metadata or {}
        )
        self.entries.append(entry)
    
    def add_interaction(self, user_message: str, assistant_message: str) -> None:
        """Add a complete user-assistant interaction."""
        self.add_entry(SpeakerType.USER, user_message)
        self.add_entry(SpeakerType.ASSISTANT, assistant_message)
    
    def clear(self) -> None:
        """Clear all conversation entries."""
        self.entries.clear()
        self.session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    def get_entries_count(self) -> int:
        """Get total number of entries."""
        return len(self.entries)
    
    def get_user_entries(self) -> List[ConversationEntry]:
        """Get only user entries."""
        return [entry for entry in self.entries if entry.speaker == SpeakerType.USER]
    
    def get_assistant_entries(self) -> List[ConversationEntry]:
        """Get only assistant entries."""
        return [entry for entry in self.entries if entry.speaker == SpeakerType.ASSISTANT]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "session_id": self.session_id,
            "entries": [entry.to_dict() for entry in self.entries],
            "entry_count": len(self.entries)
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ConversationLog":
        """Create instance from dictionary."""
        log = cls(session_id=data.get("session_id", ""))
        log.entries = [ConversationEntry.from_dict(entry_data) for entry_data in data.get("entries", [])]
        return log