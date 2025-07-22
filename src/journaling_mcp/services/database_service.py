"""Database service for conversation and message persistence."""

import logging
from pathlib import Path
from typing import Optional, List, Dict, Any
from datetime import datetime

from ..config import JournalConfig
from ..models.database import DatabaseManager, ConversationRecord, MessageRecord
from ..models.conversation import ConversationLog, ConversationEntry, SpeakerType
from ..exceptions import JournalingError


class DatabaseService:
    """Service for database operations related to conversations and messages."""
    
    def __init__(self, config: JournalConfig):
        """
        Initialize database service.
        
        Args:
            config: Journal configuration containing database path
        """
        self.config = config
        self._logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        
        # Initialize database manager
        db_path = config.journal_dir / "conversations.db"
        self.db_manager = DatabaseManager(db_path)
        
        self._logger.info(f"Database service initialized with database: {db_path}")
    
    def create_conversation_session(self, session_id: str, 
                                  metadata: Optional[Dict[str, Any]] = None) -> int:
        """
        Create a new conversation session in the database.
        
        Args:
            session_id: Unique session identifier
            metadata: Optional metadata for the conversation
            
        Returns:
            int: Database ID of the created conversation
            
        Raises:
            JournalingError: If creation fails
        """
        try:
            conversation_id = self.db_manager.create_conversation(session_id, metadata)
            self._logger.info(f"Created conversation session: {session_id} (ID: {conversation_id})")
            return conversation_id
            
        except JournalingError:
            raise
        except Exception as e:
            error_msg = f"Failed to create conversation session: {e}"
            self._logger.error(error_msg)
            raise JournalingError(error_msg) from e
    
    def save_message(self, session_id: str, speaker: str, message: str,
                    metadata: Optional[Dict[str, Any]] = None) -> int:
        """
        Save a message to the database.
        
        Args:
            session_id: Session identifier for the conversation
            speaker: "user" or "assistant"
            message: Message content
            metadata: Optional message metadata
            
        Returns:
            int: Database ID of the saved message
            
        Raises:
            JournalingError: If saving fails
        """
        try:
            # Get or create conversation
            conversation = self.db_manager.get_conversation_by_session_id(session_id)
            if not conversation:
                conversation_id = self.create_conversation_session(session_id)
            else:
                conversation_id = conversation.id
            
            # Save the message
            message_id = self.db_manager.add_message(
                conversation_id, speaker, message, metadata
            )
            
            self._logger.debug(f"Saved message to session {session_id}: {speaker} - {len(message)} chars")
            return message_id
            
        except JournalingError:
            raise
        except Exception as e:
            error_msg = f"Failed to save message: {e}"
            self._logger.error(error_msg)
            raise JournalingError(error_msg) from e
    
    def save_interaction(self, session_id: str, user_message: str, assistant_message: str,
                        metadata: Optional[Dict[str, Any]] = None) -> Dict[str, int]:
        """
        Save a complete user-assistant interaction.
        
        Args:
            session_id: Session identifier
            user_message: User's message
            assistant_message: Assistant's response
            metadata: Optional metadata for both messages
            
        Returns:
            Dict with user_message_id and assistant_message_id
            
        Raises:
            JournalingError: If saving fails
        """
        try:
            user_msg_id = self.save_message(session_id, "user", user_message, metadata)
            assistant_msg_id = self.save_message(session_id, "assistant", assistant_message, metadata)
            
            self._logger.info(f"Saved interaction for session {session_id}")
            return {
                "user_message_id": user_msg_id,
                "assistant_message_id": assistant_msg_id
            }
            
        except JournalingError:
            raise
        except Exception as e:
            error_msg = f"Failed to save interaction: {e}"
            self._logger.error(error_msg)
            raise JournalingError(error_msg) from e
    
    def load_conversation(self, session_id: str) -> Optional[ConversationLog]:
        """
        Load a complete conversation from the database.
        
        Args:
            session_id: Session identifier
            
        Returns:
            ConversationLog object or None if not found
            
        Raises:
            JournalingError: If loading fails
        """
        try:
            # Get conversation record
            conversation = self.db_manager.get_conversation_by_session_id(session_id)
            if not conversation:
                return None
            
            # Get all messages for this conversation
            message_records = self.db_manager.get_messages_for_conversation(conversation.id)
            
            # Create ConversationLog
            conv_log = ConversationLog(session_id=session_id)
            
            # Add messages to conversation log
            for msg_record in message_records:
                speaker_type = SpeakerType.USER if msg_record.speaker == "user" else SpeakerType.ASSISTANT
                
                entry = ConversationEntry(
                    speaker=speaker_type,
                    message=msg_record.message,
                    timestamp=msg_record.timestamp or datetime.now(),
                    metadata=msg_record.metadata or {}
                )
                
                conv_log.entries.append(entry)
            
            self._logger.info(f"Loaded conversation {session_id} with {len(message_records)} messages")
            return conv_log
            
        except Exception as e:
            error_msg = f"Failed to load conversation: {e}"
            self._logger.error(error_msg)
            raise JournalingError(error_msg) from e
    
    def get_recent_conversations(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get recent conversations with basic information.
        
        Args:
            limit: Maximum number of conversations to return
            
        Returns:
            List of conversation information dictionaries
            
        Raises:
            JournalingError: If retrieval fails
        """
        try:
            conversations = self.db_manager.get_recent_conversations(limit)
            
            result = []
            for conv in conversations:
                # Get message count for this conversation
                messages = self.db_manager.get_messages_for_conversation(conv.id)
                
                # Calculate basic stats
                user_messages = sum(1 for msg in messages if msg.speaker == "user")
                assistant_messages = sum(1 for msg in messages if msg.speaker == "assistant")
                
                result.append({
                    "session_id": conv.session_id,
                    "created_at": conv.created_at.isoformat() if conv.created_at else None,
                    "updated_at": conv.updated_at.isoformat() if conv.updated_at else None,
                    "total_messages": len(messages),
                    "user_messages": user_messages,
                    "assistant_messages": assistant_messages,
                    "metadata": conv.metadata or {}
                })
            
            self._logger.info(f"Retrieved {len(result)} recent conversations")
            return result
            
        except Exception as e:
            error_msg = f"Failed to get recent conversations: {e}"
            self._logger.error(error_msg)
            raise JournalingError(error_msg) from e
    
    def get_conversation_statistics(self) -> Dict[str, Any]:
        """
        Get comprehensive statistics about conversations and messages.
        
        Returns:
            Dictionary with database statistics
            
        Raises:
            JournalingError: If retrieval fails
        """
        try:
            stats = self.db_manager.get_database_statistics()
            
            # Add some computed statistics
            if stats["total_messages"] > 0 and stats["total_conversations"] > 0:
                stats["average_messages_per_conversation"] = (
                    stats["total_messages"] / stats["total_conversations"]
                )
            else:
                stats["average_messages_per_conversation"] = 0
            
            self._logger.debug(f"Generated conversation statistics: {stats['total_conversations']} conversations")
            return stats
            
        except Exception as e:
            error_msg = f"Failed to get conversation statistics: {e}"
            self._logger.error(error_msg)
            raise JournalingError(error_msg) from e
    
    def conversation_exists(self, session_id: str) -> bool:
        """
        Check if a conversation exists in the database.
        
        Args:
            session_id: Session identifier to check
            
        Returns:
            bool: True if conversation exists, False otherwise
        """
        try:
            conversation = self.db_manager.get_conversation_by_session_id(session_id)
            return conversation is not None
            
        except Exception as e:
            self._logger.error(f"Error checking conversation existence: {e}")
            return False
    
    def delete_conversation(self, session_id: str) -> bool:
        """
        Delete a conversation and all its messages.
        
        Args:
            session_id: Session identifier
            
        Returns:
            bool: True if deletion was successful
            
        Raises:
            JournalingError: If deletion fails
        """
        try:
            conversation = self.db_manager.get_conversation_by_session_id(session_id)
            if not conversation:
                return False
            
            # SQLite CASCADE will handle message deletion
            import sqlite3
            with sqlite3.connect(self.db_manager.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM conversations WHERE id = ?", (conversation.id,))
                conn.commit()
                
                deleted = cursor.rowcount > 0
                
            if deleted:
                self._logger.info(f"Deleted conversation {session_id}")
            
            return deleted
            
        except Exception as e:
            error_msg = f"Failed to delete conversation: {e}"
            self._logger.error(error_msg)
            raise JournalingError(error_msg) from e