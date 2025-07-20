"""Service for managing conversation state and operations."""

import logging
from typing import Optional, Dict, Any

from ..models import ConversationLog, ConversationEntry, SpeakerType
from ..exceptions import JournalingError

logger = logging.getLogger(__name__)


class ConversationService:
    """Service for managing conversation operations."""
    
    def __init__(self) -> None:
        self._current_log: Optional[ConversationLog] = None
        self._logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
    
    @property
    def current_log(self) -> ConversationLog:
        """Get the current conversation log, creating one if needed."""
        if self._current_log is None:
            self._current_log = ConversationLog()
            self._logger.info(f"Created new conversation log with session ID: {self._current_log.session_id}")
        return self._current_log
    
    def start_new_session(self) -> str:
        """
        Start a new conversation session.
        
        Returns:
            str: Session ID of the new conversation
        """
        self._current_log = ConversationLog()
        session_id = self._current_log.session_id
        self._logger.info(f"Started new conversation session: {session_id}")
        return session_id
    
    def add_interaction(self, user_message: str, assistant_message: str, 
                       metadata: Optional[Dict[str, Any]] = None) -> None:
        """
        Add a complete user-assistant interaction to the current conversation.
        
        Args:
            user_message: The user's message
            assistant_message: The assistant's response
            metadata: Optional metadata for the interaction
        """
        if not user_message.strip():
            raise JournalingError("User message cannot be empty")
        if not assistant_message.strip():
            raise JournalingError("Assistant message cannot be empty")
        
        log = self.current_log
        log.add_interaction(user_message, assistant_message)
        
        # Add metadata to the last assistant entry if provided
        if metadata and log.entries:
            log.entries[-1].metadata.update(metadata)
        
        self._logger.debug(f"Added interaction to session {log.session_id}. "
                          f"Total entries: {log.get_entries_count()}")
    
    def add_user_message(self, message: str, metadata: Optional[Dict[str, Any]] = None) -> None:
        """
        Add a user message to the current conversation.
        
        Args:
            message: The user's message
            metadata: Optional metadata for the message
        """
        if not message.strip():
            raise JournalingError("Message cannot be empty")
        
        log = self.current_log
        log.add_entry(SpeakerType.USER, message, metadata or {})
        self._logger.debug(f"Added user message to session {log.session_id}")
    
    def add_assistant_message(self, message: str, metadata: Optional[Dict[str, Any]] = None) -> None:
        """
        Add an assistant message to the current conversation.
        
        Args:
            message: The assistant's message
            metadata: Optional metadata for the message
        """
        if not message.strip():
            raise JournalingError("Message cannot be empty")
        
        log = self.current_log
        log.add_entry(SpeakerType.ASSISTANT, message, metadata or {})
        self._logger.debug(f"Added assistant message to session {log.session_id}")
    
    def get_conversation_summary(self) -> Dict[str, Any]:
        """
        Get a summary of the current conversation.
        
        Returns:
            Dict containing conversation statistics and metadata
        """
        log = self.current_log
        user_entries = log.get_user_entries()
        assistant_entries = log.get_assistant_entries()
        
        return {
            "session_id": log.session_id,
            "total_entries": log.get_entries_count(),
            "user_entries": len(user_entries),
            "assistant_entries": len(assistant_entries),
            "has_content": log.get_entries_count() > 0,
            "first_entry_time": log.entries[0].timestamp.isoformat() if log.entries else None,
            "last_entry_time": log.entries[-1].timestamp.isoformat() if log.entries else None
        }
    
    def clear_conversation(self) -> None:
        """Clear the current conversation log."""
        if self._current_log:
            session_id = self._current_log.session_id
            self._current_log.clear()
            self._logger.info(f"Cleared conversation session: {session_id}")
    
    def has_conversation(self) -> bool:
        """Check if there's an active conversation with content."""
        return self._current_log is not None and self._current_log.get_entries_count() > 0
    
    def export_conversation(self) -> Dict[str, Any]:
        """
        Export the current conversation as a dictionary.
        
        Returns:
            Dict representation of the conversation
        """
        if not self.has_conversation():
            raise JournalingError("No active conversation to export")
        
        return self.current_log.to_dict()