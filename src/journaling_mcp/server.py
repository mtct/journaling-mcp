"""
Professional MCP Journaling Server

A comprehensive MCP server for interactive journaling with emotional analysis,
conversation management, and automatic file organization.
"""

import logging
from pathlib import Path
from typing import Optional, Dict, Any
from datetime import datetime

from mcp.server.fastmcp import FastMCP

from .config import load_config, JournalConfig
from .services import JournalService, ConversationService
from .models import SpeakerType
from .exceptions import JournalingError, JournalError, ConfigurationError
from .utils import setup_logging


class JournalingMCPServer:
    """Main MCP server class for journaling operations."""
    
    def __init__(self, config: Optional[JournalConfig] = None) -> None:
        """
        Initialize the journaling MCP server.
        
        Args:
            config: Optional configuration. If None, will load from environment.
        """
        # Load configuration
        try:
            self.config = config or load_config()
        except ConfigurationError as e:
            logging.error(f"Configuration error: {e}")
            raise
        
        # Setup logging
        log_level = "DEBUG" if self.config.journal_dir.name == "test" else "INFO"
        log_file = self.config.journal_dir / "journaling_mcp.log"
        setup_logging(level=log_level, log_file=log_file)
        
        self.logger = logging.getLogger(self.__class__.__name__)
        self.logger.info("Initializing Journaling MCP Server")
        
        # Initialize services
        self.journal_service = JournalService(self.config)
        self.conversation_service = ConversationService(self.config)
        
        # Initialize FastMCP server
        self.mcp = FastMCP("journaling")
        self._register_endpoints()
        
        self.logger.info(f"Server initialized - Journal dir: {self.config.journal_dir}")
    
    def _register_endpoints(self) -> None:
        """Register all MCP endpoints (tools, resources, prompts)."""
        self._register_prompts()
        self._register_tools()
        self._register_resources()
    
    def _register_prompts(self) -> None:
        """Register MCP prompts."""
        
        @self.mcp.prompt()
        def start_journaling() -> str:
            """
            Interactive prompt to begin a journaling session.
            
            Returns:
                Starting prompt for journaling session
            """
            return '''You are an empathetic AI journaling companion designed to facilitate meaningful conversations that promote self-reflection and emotional well-being.

## Session Workflow

1. **Session Initialization**
   - Call `start_new_session()` to create a new conversation session with unique ID
   - Load context by reading "journals://recent" to understand previous emotional patterns and themes

2. **Conversation Management**
   - Use `record_interaction(user_message, assistant_message)` after each exchange to save all conversation data to the SQLite database
   - Track both user messages and your responses with timestamps and metadata
   - Monitor conversation flow and emotional themes throughout the session

3. **Session Completion**
   - When the conversation naturally concludes, call `generate_session_summary()` with:
     - **summary**: Comprehensive overview of the conversation topics and insights
     - **emotional_analysis**: Analysis of emotional states, patterns, and changes during the session
     - **reflections**: Key insights, breakthroughs, or important realizations
     - **tags**: Relevant tags for categorization (e.g., "stress", "work", "family", "growth")
     - **mood_rating**: Numerical mood rating from 1-10 if discussable

4. **Data Persistence**
   - All data is stored exclusively in the SQLite database (conversations.db)
   - Use `get_journal_statistics()` to view database metrics
   - Use `add_conversation_tags()` to add tags to existing sessions

## Conversation Guidelines

- Ask open-ended questions that encourage deeper reflection
- Provide empathetic responses and validate emotions
- Help identify patterns and connections between different experiences
- Encourage self-awareness and personal growth
- Maintain a safe, non-judgmental space for expression
- Reference previous entries when relevant to show continuity and growth

## Available Resources

- `journals://recent`: Recent conversation sessions from database
- `journals://statistics`: Database statistics and metrics

Begin by reading the recent conversations to understand context, then start with: "How are you feeling today?"'''
    
    def _register_tools(self) -> None:
        """Register MCP tools."""
        
        @self.mcp.tool()
        async def start_new_session() -> str:
            """
            Start a new journaling session by clearing previous conversation log.
            
            Returns:
                Welcome message with current save location and session ID
            """
            try:
                session_id = self.conversation_service.start_new_session()
                return (f"New journaling session started (ID: {session_id}). "
                       f"Entries will be saved to {self.config.journal_dir}")
            except Exception as e:
                self.logger.error(f"Error starting new session: {e}")
                return f"Error starting new session: {e}"
        
        @self.mcp.tool()
        async def record_interaction(user_message: str, assistant_message: str) -> str:
            """
            Record both the user's message and assistant's response.
            
            Args:
                user_message: The user's message
                assistant_message: The assistant's response
                
            Returns:
                Confirmation message with conversation statistics
            """
            try:
                self.conversation_service.add_interaction(user_message, assistant_message)
                summary = self.conversation_service.get_conversation_summary()
                return (f"Conversation updated. Total entries: {summary['total_entries']} "
                       f"(Session: {summary['session_id']})")
            except JournalingError as e:
                self.logger.error(f"Error recording interaction: {e}")
                return f"Error recording interaction: {e}"
            except Exception as e:
                self.logger.error(f"Unexpected error recording interaction: {e}")
                return f"Unexpected error: {e}"
        
        @self.mcp.tool()
        async def generate_session_summary(summary: str, 
                                         emotional_analysis: str = "",
                                         reflections: str = "",
                                         tags: Optional[str] = None,
                                         mood_rating: Optional[int] = None) -> str:
            """
            Generate and save a comprehensive journal entry from the current session.
            All data is saved to the SQLite database only.
            
            Args:
                summary: AI-generated summary of the conversation
                emotional_analysis: Emotional analysis of the session
                reflections: Personal reflections and insights
                tags: Comma-separated tags for the entry
                mood_rating: Mood rating from 1-10
                
            Returns:
                Confirmation message with session details
            """
            try:
                if not self.conversation_service.has_conversation():
                    return "No conversation to summarize. Please start a new session first."
                
                # Validate mood rating if provided
                if mood_rating is not None and (mood_rating < 1 or mood_rating > 10):
                    return "Invalid mood rating: must be between 1 and 10"
                
                # Prepare metadata for the session summary
                session_metadata = {
                    "summary": summary,
                    "emotional_analysis": emotional_analysis,
                    "reflections": reflections,
                    "mood_rating": mood_rating,
                    "tags": [tag.strip() for tag in tags.split(",") if tag and tag.strip()] if tags else [],
                    "session_completed": True,
                    "completion_timestamp": datetime.now().isoformat()
                }
                
                # Update conversation metadata in database
                session_id = self.conversation_service.current_log.session_id
                if self.conversation_service.db_service:
                    try:
                        # Save summary data to conversation metadata
                        conversation = self.conversation_service.db_service.db_manager.get_conversation_by_session_id(session_id)
                        if conversation:
                            # Update the conversation metadata
                            import sqlite3
                            import json
                            with sqlite3.connect(self.conversation_service.db_service.db_manager.db_path) as conn:
                                cursor = conn.cursor()
                                cursor.execute(
                                    "UPDATE conversations SET metadata = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                                    (json.dumps(session_metadata), conversation.id)
                                )
                                conn.commit()
                    except Exception as e:
                        self.logger.warning(f"Failed to update conversation metadata: {e}")
                
                # Get conversation statistics
                conv_summary = self.conversation_service.get_conversation_summary()
                total_words = sum(len(entry.message.split()) for entry in self.conversation_service.current_log.entries)
                
                return (f"Session summary saved to database (ID: {session_id})\\n"
                       f"Statistics: {total_words} words, "
                       f"{conv_summary['total_entries']} conversation entries\\n"
                       f"Tags: {', '.join(session_metadata['tags']) if session_metadata['tags'] else 'None'}\\n"
                       f"Mood rating: {mood_rating if mood_rating else 'Not set'}")
                
            except JournalingError as e:
                self.logger.error(f"Error generating session summary: {e}")
                return f"Error saving session summary: {e}"
            except Exception as e:
                self.logger.error(f"Unexpected error generating summary: {e}")
                return f"Unexpected error: {e}"
        
        @self.mcp.tool()
        async def get_journal_statistics() -> str:
            """
            Get comprehensive statistics about conversation database.
            
            Returns:
                Formatted statistics about conversation sessions and messages
            """
            try:
                if not self.conversation_service.db_service:
                    return "Database service not available"
                
                stats = self.conversation_service.db_service.get_conversation_statistics()
                
                return f"""Conversation Database Statistics:
• Total conversations: {stats.get('total_conversations', 0)}
• Total messages: {stats.get('total_messages', 0)}
• Average messages per conversation: {stats.get('average_messages_per_conversation', 0):.1f}
• User messages: {stats.get('user_messages', 0)}
• Assistant messages: {stats.get('assistant_messages', 0)}
• Database file: {stats.get('database_file', 'N/A')}
• First conversation: {stats.get('first_conversation_date', 'N/A')}
• Last conversation: {stats.get('last_conversation_date', 'N/A')}"""
                
            except JournalingError as e:
                self.logger.error(f"Error getting statistics: {e}")
                return f"Error getting statistics: {e}"
            except Exception as e:
                self.logger.error(f"Unexpected error getting statistics: {e}")
                return f"Unexpected error: {e}"
        
        @self.mcp.tool()
        async def add_conversation_tags(session_id: str, tags: str) -> str:
            """
            Add tags to an existing conversation session.
            
            Args:
                session_id: Session ID of the conversation
                tags: Comma-separated tags to add
                
            Returns:
                Confirmation message
            """
            try:
                if not self.conversation_service.db_service:
                    return "Database service not available"
                
                # Parse tags
                tag_list = [tag.strip() for tag in tags.split(",") if tag.strip()]
                if not tag_list:
                    return "No valid tags provided"
                
                # Get existing conversation
                conversation = self.conversation_service.db_service.db_manager.get_conversation_by_session_id(session_id)
                if not conversation:
                    return f"Conversation with session ID {session_id} not found"
                
                # Get existing metadata
                existing_metadata = conversation.metadata or {}
                existing_tags = existing_metadata.get('tags', [])
                
                # Add new tags (avoid duplicates)
                updated_tags = list(set(existing_tags + tag_list))
                existing_metadata['tags'] = updated_tags
                
                # Update database
                import sqlite3
                import json
                with sqlite3.connect(self.conversation_service.db_service.db_manager.db_path) as conn:
                    cursor = conn.cursor()
                    cursor.execute(
                        "UPDATE conversations SET metadata = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                        (json.dumps(existing_metadata), conversation.id)
                    )
                    conn.commit()
                
                return f"Added tags to conversation {session_id}: {', '.join(tag_list)}\\nAll tags: {', '.join(updated_tags)}"
                
            except Exception as e:
                self.logger.error(f"Error adding tags: {e}")
                return f"Error adding tags: {e}"
    
    def _register_resources(self) -> None:
        """Register MCP resources."""
        
        @self.mcp.resource("journals://recent")
        def get_recent_journals() -> str:
            """
            Get contents of recent conversation sessions from database.
            
            Returns:
                Formatted content of recent conversation sessions
            """
            try:
                if not self.conversation_service.db_service:
                    return "Database service not available"
                
                # Get recent conversations from database
                recent_conversations = self.conversation_service.db_service.get_recent_conversations(limit=5)
                
                if not recent_conversations:
                    return "No conversation sessions found in database"
                
                content_parts = []
                for conv in recent_conversations:
                    # Load full conversation
                    conv_log = self.conversation_service.db_service.load_conversation(conv['session_id'])
                    if not conv_log:
                        continue
                    
                    # Format conversation header
                    content_parts.append(f"# Conversation Session - {conv['created_at'][:10]}")
                    content_parts.append(f"Session ID: {conv['session_id']}")
                    content_parts.append(f"Messages: {conv['total_messages']}")
                    
                    # Add metadata if available
                    if conv.get('metadata'):
                        metadata = conv['metadata']
                        if isinstance(metadata, dict):
                            if metadata.get('summary'):
                                content_parts.append(f"\\n**Summary:** {metadata['summary']}")
                            if metadata.get('emotional_analysis'):
                                content_parts.append(f"\\n**Emotional Analysis:** {metadata['emotional_analysis']}")
                            if metadata.get('tags'):
                                content_parts.append(f"\\n**Tags:** {', '.join(metadata['tags'])}")
                            if metadata.get('mood_rating'):
                                content_parts.append(f"\\n**Mood Rating:** {metadata['mood_rating']}/10")
                    
                    # Add conversation entries
                    content_parts.append("\\n## Conversation")
                    for entry in conv_log.entries:
                        speaker = "**User:**" if entry.speaker == SpeakerType.USER else "**Assistant:**"
                        content_parts.append(f"\\n{speaker} {entry.message}")
                    
                    content_parts.append("\\n---\\n")
                
                return "\\n".join(content_parts)
                
            except Exception as e:
                self.logger.error(f"Error getting recent conversations: {e}")
                return f"Error reading conversations: {e}"
        
        @self.mcp.resource("journals://statistics")
        def get_statistics_resource() -> str:
            """
            Get conversation statistics from database as a resource.
            
            Returns:
                JSON-formatted statistics about the conversation database
            """
            try:
                import json
                if not self.conversation_service.db_service:
                    return json.dumps({"error": "Database service not available"}, indent=2)
                
                stats = self.conversation_service.db_service.get_conversation_statistics()
                return json.dumps(stats, indent=2, default=str)
            except Exception as e:
                self.logger.error(f"Error getting statistics resource: {e}")
                return f'{{"error": "{e}"}}'
    
    def run(self) -> None:
        """Run the MCP server."""
        try:
            self.logger.info("Starting Journaling MCP Server")
            self.mcp.run()
        except KeyboardInterrupt:
            self.logger.info("Server stopped by user")
        except Exception as e:
            self.logger.error(f"Server error: {e}")
            raise


def create_server(config: Optional[JournalConfig] = None) -> JournalingMCPServer:
    """
    Create and return a configured journaling MCP server.
    
    Args:
        config: Optional configuration. If None, will load from environment.
        
    Returns:
        Configured JournalingMCPServer instance
    """
    return JournalingMCPServer(config)