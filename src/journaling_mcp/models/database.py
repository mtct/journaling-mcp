"""Database models for SQLite storage."""

import sqlite3
from dataclasses import dataclass
from datetime import datetime
from typing import Optional, List, Dict, Any
from pathlib import Path

from ..exceptions import JournalingError


@dataclass
class ConversationRecord:
    """Database record for a conversation session."""
    
    id: Optional[int] = None
    session_id: str = ""
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    metadata: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "id": self.id,
            "session_id": self.session_id,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "metadata": self.metadata or {}
        }


@dataclass
class MessageRecord:
    """Database record for a conversation message."""
    
    id: Optional[int] = None
    conversation_id: int = 0
    speaker: str = ""  # "user" or "assistant"
    message: str = ""
    timestamp: Optional[datetime] = None
    metadata: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "id": self.id,
            "conversation_id": self.conversation_id,
            "speaker": self.speaker,
            "message": self.message,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "metadata": self.metadata or {}
        }


class DatabaseManager:
    """Manager for SQLite database operations."""
    
    def __init__(self, db_path: Path):
        """
        Initialize database manager.
        
        Args:
            db_path: Path to the SQLite database file
        """
        self.db_path = db_path
        self._init_database()
    
    def _init_database(self) -> None:
        """Initialize database tables if they don't exist."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Create conversations table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS conversations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT UNIQUE NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    metadata TEXT
                )
            """)
            
            # Create messages table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    conversation_id INTEGER NOT NULL,
                    speaker TEXT NOT NULL CHECK (speaker IN ('user', 'assistant')),
                    message TEXT NOT NULL,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    metadata TEXT,
                    FOREIGN KEY (conversation_id) REFERENCES conversations (id)
                        ON DELETE CASCADE
                )
            """)
            
            # Create indexes for better performance
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_messages_conversation_id 
                ON messages (conversation_id)
            """)
            
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_messages_timestamp 
                ON messages (timestamp)
            """)
            
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_conversations_session_id 
                ON conversations (session_id)
            """)
            
            conn.commit()
    
    def create_conversation(self, session_id: str, metadata: Optional[Dict[str, Any]] = None) -> int:
        """
        Create a new conversation record.
        
        Args:
            session_id: Unique session identifier
            metadata: Optional metadata dictionary
            
        Returns:
            int: Database ID of the created conversation
            
        Raises:
            JournalingError: If creation fails
        """
        try:
            import json
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO conversations (session_id, metadata)
                    VALUES (?, ?)
                """, (session_id, json.dumps(metadata or {})))
                
                conversation_id = cursor.lastrowid
                conn.commit()
                return conversation_id
                
        except sqlite3.IntegrityError as e:
            raise JournalingError(f"Conversation with session_id {session_id} already exists") from e
        except Exception as e:
            raise JournalingError(f"Failed to create conversation: {e}") from e
    
    def add_message(self, conversation_id: int, speaker: str, message: str, 
                   metadata: Optional[Dict[str, Any]] = None) -> int:
        """
        Add a message to a conversation.
        
        Args:
            conversation_id: ID of the conversation
            speaker: "user" or "assistant"
            message: Message content
            metadata: Optional metadata dictionary
            
        Returns:
            int: Database ID of the created message
            
        Raises:
            JournalingError: If addition fails
        """
        try:
            import json
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO messages (conversation_id, speaker, message, metadata)
                    VALUES (?, ?, ?, ?)
                """, (conversation_id, speaker, message, json.dumps(metadata or {})))
                
                message_id = cursor.lastrowid
                
                # Update conversation updated_at timestamp
                cursor.execute("""
                    UPDATE conversations 
                    SET updated_at = CURRENT_TIMESTAMP 
                    WHERE id = ?
                """, (conversation_id,))
                
                conn.commit()
                return message_id
                
        except Exception as e:
            raise JournalingError(f"Failed to add message: {e}") from e
    
    def get_conversation_by_session_id(self, session_id: str) -> Optional[ConversationRecord]:
        """
        Get conversation record by session ID.
        
        Args:
            session_id: Session identifier
            
        Returns:
            ConversationRecord or None if not found
        """
        try:
            import json
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT id, session_id, created_at, updated_at, metadata
                    FROM conversations 
                    WHERE session_id = ?
                """, (session_id,))
                
                row = cursor.fetchone()
                if row:
                    return ConversationRecord(
                        id=row[0],
                        session_id=row[1],
                        created_at=datetime.fromisoformat(row[2]) if row[2] else None,
                        updated_at=datetime.fromisoformat(row[3]) if row[3] else None,
                        metadata=json.loads(row[4]) if row[4] else None
                    )
                return None
                
        except Exception as e:
            raise JournalingError(f"Failed to get conversation: {e}") from e
    
    def get_messages_for_conversation(self, conversation_id: int) -> List[MessageRecord]:
        """
        Get all messages for a conversation.
        
        Args:
            conversation_id: Conversation database ID
            
        Returns:
            List of MessageRecord objects
        """
        try:
            import json
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT id, conversation_id, speaker, message, timestamp, metadata
                    FROM messages 
                    WHERE conversation_id = ?
                    ORDER BY timestamp ASC
                """, (conversation_id,))
                
                messages = []
                for row in cursor.fetchall():
                    messages.append(MessageRecord(
                        id=row[0],
                        conversation_id=row[1],
                        speaker=row[2],
                        message=row[3],
                        timestamp=datetime.fromisoformat(row[4]) if row[4] else None,
                        metadata=json.loads(row[5]) if row[5] else None
                    ))
                
                return messages
                
        except Exception as e:
            raise JournalingError(f"Failed to get messages: {e}") from e
    
    def get_recent_conversations(self, limit: int = 10) -> List[ConversationRecord]:
        """
        Get recent conversations.
        
        Args:
            limit: Maximum number of conversations to return
            
        Returns:
            List of ConversationRecord objects
        """
        try:
            import json
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT id, session_id, created_at, updated_at, metadata
                    FROM conversations 
                    ORDER BY updated_at DESC
                    LIMIT ?
                """, (limit,))
                
                conversations = []
                for row in cursor.fetchall():
                    conversations.append(ConversationRecord(
                        id=row[0],
                        session_id=row[1],
                        created_at=datetime.fromisoformat(row[2]) if row[2] else None,
                        updated_at=datetime.fromisoformat(row[3]) if row[3] else None,
                        metadata=json.loads(row[4]) if row[4] else None
                    ))
                
                return conversations
                
        except Exception as e:
            raise JournalingError(f"Failed to get recent conversations: {e}") from e
    
    def get_database_statistics(self) -> Dict[str, Any]:
        """
        Get database statistics.
        
        Returns:
            Dictionary with database statistics
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Count conversations
                cursor.execute("SELECT COUNT(*) FROM conversations")
                conversation_count = cursor.fetchone()[0]
                
                # Count messages
                cursor.execute("SELECT COUNT(*) FROM messages")
                message_count = cursor.fetchone()[0]
                
                # Get date range
                cursor.execute("""
                    SELECT MIN(created_at), MAX(updated_at) 
                    FROM conversations
                """)
                date_range = cursor.fetchone()
                
                return {
                    "total_conversations": conversation_count,
                    "total_messages": message_count,
                    "database_path": str(self.db_path),
                    "earliest_conversation": date_range[0] if date_range[0] else None,
                    "latest_activity": date_range[1] if date_range[1] else None
                }
                
        except Exception as e:
            raise JournalingError(f"Failed to get database statistics: {e}") from e