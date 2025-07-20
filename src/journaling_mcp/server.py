"""
Professional MCP Journaling Server

A comprehensive MCP server for interactive journaling with emotional analysis,
conversation management, and automatic file organization.
"""

import logging
from pathlib import Path
from typing import Optional, Dict, Any

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
        self.conversation_service = ConversationService()
        
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
            return '''First, please read the resource at "journals://recent" into our conversation to understand my previous emotional states and recurring themes. 
            Then start our conversation by asking how I'm feeling today, taking into account any patterns or ongoing situations from previous entries.
            Let's begin - how are you feeling today?'''
    
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
            
            Args:
                summary: AI-generated summary of the conversation
                emotional_analysis: Emotional analysis of the session
                reflections: Personal reflections and insights
                tags: Comma-separated tags for the entry
                mood_rating: Mood rating from 1-10
                
            Returns:
                Confirmation message with file path
            """
            try:
                if not self.conversation_service.has_conversation():
                    return "No conversation to summarize. Please start a new session first."
                
                # Create journal entry
                entry = self.journal_service.create_journal_entry(
                    conversation=self.conversation_service.current_log,
                    summary=summary,
                    emotional_analysis=emotional_analysis,
                    reflections=reflections
                )
                
                # Add tags if provided
                if tags:
                    tag_list = [tag.strip() for tag in tags.split(",") if tag.strip()]
                    for tag in tag_list:
                        entry.add_tag(tag)
                
                # Set mood rating if provided
                if mood_rating is not None:
                    try:
                        entry.set_mood_rating(mood_rating)
                    except ValueError as e:
                        return f"Invalid mood rating: {e}"
                
                # Save the entry
                file_path = self.journal_service.save_journal_entry(entry)
                
                # Get statistics
                stats = entry.metadata.to_dict()
                
                return (f"Journal entry saved to: {file_path}\\n"
                       f"Statistics: {stats['word_count']} words, "
                       f"{stats['entry_count']} conversation entries")
                
            except JournalError as e:
                self.logger.error(f"Error generating session summary: {e}")
                return f"Error saving journal: {e}"
            except Exception as e:
                self.logger.error(f"Unexpected error generating summary: {e}")
                return f"Unexpected error: {e}"
        
        @self.mcp.tool()
        async def get_journal_statistics() -> str:
            """
            Get comprehensive statistics about the journal collection.
            
            Returns:
                Formatted statistics about journal entries
            """
            try:
                stats = self.journal_service.get_journal_statistics()
                
                return f"""Journal Statistics:
• Total entries: {stats['total_entries']}
• Total words: {stats['total_words']:,}
• Average words per entry: {stats['average_words_per_entry']:,}
• Total size: {stats['total_size_bytes'] / 1024:.1f} KB
• Date range: {stats['oldest_entry'] or 'N/A'} to {stats['newest_entry'] or 'N/A'}
• Journal directory: {stats['journal_directory']}
• Backup enabled: {stats['backup_enabled']}"""
                
            except JournalError as e:
                self.logger.error(f"Error getting statistics: {e}")
                return f"Error getting statistics: {e}"
            except Exception as e:
                self.logger.error(f"Unexpected error getting statistics: {e}")
                return f"Unexpected error: {e}"
        
        @self.mcp.tool()
        async def add_journal_tags(filepath: str, tags: str) -> str:
            """
            Add tags to an existing journal entry.
            
            Args:
                filepath: Path to the journal file
                tags: Comma-separated tags to add
                
            Returns:
                Confirmation message
            """
            try:
                # For now, just return a message indicating this would add tags
                # Full implementation would require parsing and updating the markdown file
                tag_list = [tag.strip() for tag in tags.split(",") if tag.strip()]
                return f"Would add tags {tag_list} to journal at {filepath}. "
                "Note: Tag functionality requires markdown parsing implementation."
                
            except Exception as e:
                self.logger.error(f"Error adding tags: {e}")
                return f"Error adding tags: {e}"
    
    def _register_resources(self) -> None:
        """Register MCP resources."""
        
        @self.mcp.resource("journals://recent")
        def get_recent_journals() -> str:
            """
            Get contents of recent journal entries.
            
            Returns:
                Formatted content of recent journal entries
            """
            try:
                content = self.journal_service.get_recent_journals_content()
                return content
            except JournalError as e:
                self.logger.error(f"Error getting recent journals: {e}")
                return f"Error reading journals: {e}"
            except Exception as e:
                self.logger.error(f"Unexpected error getting recent journals: {e}")
                return f"Unexpected error: {e}"
        
        @self.mcp.resource("journals://statistics")
        def get_statistics_resource() -> str:
            """
            Get journal statistics as a resource.
            
            Returns:
                JSON-formatted statistics about the journal collection
            """
            try:
                import json
                stats = self.journal_service.get_journal_statistics()
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