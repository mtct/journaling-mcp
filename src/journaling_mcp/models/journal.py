"""Journal entry data models."""

from datetime import datetime
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, field
from pathlib import Path

from .conversation import ConversationLog


@dataclass
class JournalMetadata:
    """Metadata for a journal entry."""
    
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    word_count: int = 0
    entry_count: int = 0
    tags: List[str] = field(default_factory=list)
    mood_rating: Optional[int] = None  # 1-10 scale
    custom_fields: Dict[str, Any] = field(default_factory=dict)
    
    def update_timestamp(self) -> None:
        """Update the last modified timestamp."""
        self.updated_at = datetime.now()
    
    def add_tag(self, tag: str) -> None:
        """Add a tag if it doesn't already exist."""
        if tag not in self.tags:
            self.tags.append(tag)
    
    def remove_tag(self, tag: str) -> None:
        """Remove a tag if it exists."""
        if tag in self.tags:
            self.tags.remove(tag)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "word_count": self.word_count,
            "entry_count": self.entry_count,
            "tags": self.tags,
            "mood_rating": self.mood_rating,
            "custom_fields": self.custom_fields
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "JournalMetadata":
        """Create instance from dictionary."""
        return cls(
            created_at=datetime.fromisoformat(data["created_at"]),
            updated_at=datetime.fromisoformat(data["updated_at"]),
            word_count=data.get("word_count", 0),
            entry_count=data.get("entry_count", 0),
            tags=data.get("tags", []),
            mood_rating=data.get("mood_rating"),
            custom_fields=data.get("custom_fields", {})
        )


@dataclass
class JournalEntry:
    """Represents a complete journal entry."""
    
    title: str
    date: datetime = field(default_factory=datetime.now)
    conversation: ConversationLog = field(default_factory=ConversationLog)
    summary: str = ""
    emotional_analysis: str = ""
    reflections: str = ""
    metadata: JournalMetadata = field(default_factory=JournalMetadata)
    file_path: Optional[Path] = None
    
    def __post_init__(self) -> None:
        """Initialize computed fields after creation."""
        self._update_metadata()
    
    def _update_metadata(self) -> None:
        """Update metadata based on current content."""
        self.metadata.entry_count = self.conversation.get_entries_count()
        self.metadata.word_count = self._calculate_word_count()
        self.metadata.update_timestamp()
    
    def _calculate_word_count(self) -> int:
        """Calculate total word count of the entry."""
        total_words = 0
        
        # Count words in conversation
        for entry in self.conversation.entries:
            total_words += len(entry.message.split())
        
        # Count words in summary and analysis
        total_words += len(self.summary.split())
        total_words += len(self.emotional_analysis.split())
        total_words += len(self.reflections.split())
        
        return total_words
    
    def add_tag(self, tag: str) -> None:
        """Add a tag to this journal entry."""
        self.metadata.add_tag(tag)
        self._update_metadata()
    
    def set_mood_rating(self, rating: int) -> None:
        """Set mood rating (1-10 scale)."""
        if not 1 <= rating <= 10:
            raise ValueError("Mood rating must be between 1 and 10")
        self.metadata.mood_rating = rating
        self._update_metadata()
    
    def get_formatted_date(self) -> str:
        """Get formatted date string."""
        return self.date.strftime("%B %d, %Y")
    
    def get_short_date(self) -> str:
        """Get short date string for filenames."""
        return self.date.strftime("%Y-%m-%d")
    
    def to_markdown(self) -> str:
        """Convert journal entry to markdown format."""
        lines = []
        
        # Header with date
        lines.append(f"# {self.title}")
        lines.append(f"**Date:** {self.get_formatted_date()}")
        
        if self.metadata.tags:
            lines.append(f"**Tags:** {', '.join(self.metadata.tags)}")
        
        if self.metadata.mood_rating:
            lines.append(f"**Mood:** {self.metadata.mood_rating}/10")
        
        lines.append("")
        
        # Conversation transcript
        if self.conversation.entries:
            lines.append("## Conversation")
            lines.append("")
            
            for entry in self.conversation.entries:
                speaker = "You" if entry.speaker.value == "user" else "Assistant"
                timestamp = entry.timestamp.strftime("%H:%M")
                lines.append(f"**{speaker} ({timestamp})**: {entry.message}")
                lines.append("")
        
        # Summary
        if self.summary:
            lines.append("## Summary")
            lines.append(self.summary)
            lines.append("")
        
        # Emotional analysis
        if self.emotional_analysis:
            lines.append("## Emotional Analysis")
            lines.append(self.emotional_analysis)
            lines.append("")
        
        # Reflections
        if self.reflections:
            lines.append("## Reflections")
            lines.append(self.reflections)
            lines.append("")
        
        # Metadata
        lines.append("---")
        lines.append(f"*Word count: {self.metadata.word_count} | "
                    f"Entries: {self.metadata.entry_count} | "
                    f"Created: {self.metadata.created_at.strftime('%Y-%m-%d %H:%M')}*")
        
        return "\n".join(lines)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "title": self.title,
            "date": self.date.isoformat(),
            "conversation": self.conversation.to_dict(),
            "summary": self.summary,
            "emotional_analysis": self.emotional_analysis,
            "reflections": self.reflections,
            "metadata": self.metadata.to_dict(),
            "file_path": str(self.file_path) if self.file_path else None
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "JournalEntry":
        """Create instance from dictionary."""
        entry = cls(
            title=data["title"],
            date=datetime.fromisoformat(data["date"]),
            conversation=ConversationLog.from_dict(data.get("conversation", {})),
            summary=data.get("summary", ""),
            emotional_analysis=data.get("emotional_analysis", ""),
            reflections=data.get("reflections", ""),
            metadata=JournalMetadata.from_dict(data.get("metadata", {}))
        )
        
        if file_path := data.get("file_path"):
            entry.file_path = Path(file_path)
        
        return entry