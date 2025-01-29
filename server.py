from mcp.server.fastmcp import FastMCP
from datetime import datetime
from typing import List, Dict, Any
from pathlib import Path
import os
from dotenv import load_dotenv

class JournalConfig:
    """Configuration handler for journaling server."""
    
    # Default configuration values
    DEFAULTS = {
        "JOURNAL_DIR": "journal",
        "FILENAME_PREFIX": "journal",
        "FILE_EXTENSION": "md",
    }
    
    def __init__(self):
        """
        Initialize journal configuration.
        
        """
        
        # Load configuration from environment variables with defaults
        self.journal_dir = Path(os.getenv("JOURNAL_DIR", self.DEFAULTS["JOURNAL_DIR"]))
        self.file_prefix = os.getenv("FILENAME_PREFIX", self.DEFAULTS["FILENAME_PREFIX"])
        self.file_extension = os.getenv("FILE_EXTENSION", self.DEFAULTS["FILE_EXTENSION"])
        
        # Create journal directory
        self.journal_dir.mkdir(parents=True, exist_ok=True)
        
        # Validate configuration
        self._validate_config()
    
    def _validate_config(self):
        """Validate configuration values."""
        if not self.file_extension.startswith('.'):
            self.file_extension = '.' + self.file_extension
    
    def get_default_filepath(self) -> Path:
        """Get default filepath for current date."""
        today = datetime.now().strftime("%Y-%m-%d")
        filename = f"{self.file_prefix}_{today}{self.file_extension}"
        return self.journal_dir / filename
    
    def resolve_filepath(self, filepath: str = None) -> Path:
        """
        Resolve filepath, ensuring it's within journal directory.
        
        Args:
            filepath: Optional specific filepath
            
        Returns:
            Path: Resolved and validated filepath
        """
        if filepath is None:
            return self.get_default_filepath()
            
        path = Path(filepath)
        
        # If path is just a filename, put it in journal directory
        if not path.is_absolute():
            path = self.journal_dir / path
        
        # Ensure file has correct extension
        if not str(path).endswith(self.file_extension):
            path = path.with_suffix(self.file_extension)
            
        # Ensure path is within journal directory
        try:
            path = path.resolve()
            if not str(path).startswith(str(self.journal_dir.resolve())):
                raise ValueError("Path must be within journal directory")
        except (RuntimeError, ValueError):
            raise ValueError("Invalid filepath")
            
        return path
    
# Initialize server with configuration
load_dotenv()
config = JournalConfig()
mcp = FastMCP("journaling")

# Global state
conversation_log: List[Dict[str, Any]] = []

@mcp.prompt()
def start_journaling() -> str:
    """
    Interactive prompt to begin a journaling session.

    Returns: Starting prompt for journaling session
    """

    return """First, please read the resource at "journals://recent" into our conversation to understand my previous emotional states and recurring themes. 
    Then start our conversation by asking how I'm feeling today, taking into account any patterns or ongoing situations from previous entries.
    Let's begin - how are you feeling today?"""

async def save_journal_entry(content: str, filepath: str = None) -> str:
    """
    Save journal content to a markdown file.
    
    Args:
        content: The journal content to save
        filepath: Optional filepath to save the journal. If not specified,
                 a new file with current date will be created in the configured directory.
    
    Returns:
        str: Confirmation message with filepath
    """
    try:
        # Get and validate filepath
        path = config.resolve_filepath(filepath)
  
        # Ensure directory exists
        path.parent.mkdir(parents=True, exist_ok=True)
        
        # Write content
        with open(path, 'a', encoding='utf-8') as file:
            file.write(content + "\n\n")
            
        return f"Journal saved to: {path}"
        
    except ValueError as e:
        return f"Invalid filepath: {str(e)}"
    except Exception as e:
        return f"Error saving journal: {str(e)}"

@mcp.tool()
async def start_new_session() -> str:
    """
    Start a new journaling session by clearing previous conversation log.
    
    Returns:
        str: Welcome message with current save location
    """
    conversation_log.clear()
    return f"New journaling session started. Entries will be saved to {config.journal_dir}"

@mcp.tool()
async def record_interaction(user_message: str, assistant_message: str) -> str:
    """
    Record both the user's message and assistant's response.
    
    Args:
        user_message: The user's message
        assistant_message: The assistant's response
        
    Returns:
        str: Confirmation message
    """
    # Add user message first
    conversation_log.append({
        "speaker": "user",
        "message": user_message,
        "timestamp": datetime.now().isoformat()
    })
    
    # Then add assistant message
    conversation_log.append({
        "speaker": "assistant",
        "message": assistant_message,
        "timestamp": datetime.now().isoformat()
    })
    
    return "Conversation updated"

@mcp.tool()
async def generate_session_summary(summary: str) -> str:
    """
    Generate a markdown summary of the journaling session.

    Args:
        summary: The llm generated summay of the conversation
    
    Returns:
        str: Confirmation message
    """
    if not conversation_log:
        return "No conversation to summarize. Please start a new session first."
    
    lines = []
    
    # Add header with date
    today = datetime.now().strftime("%B %d, %Y")
    lines.append(f"# Journal Entry - {today}\n")
    
    # Add conversation transcript
    lines.append("## Conversation\n")
    for entry in conversation_log:
        speaker = "You" if entry["speaker"] == "user" else "Assistant"
        timestamp = datetime.fromisoformat(entry["timestamp"]).strftime("%H:%M")
        lines.append(f"**{speaker} ({timestamp})**: {entry['message']}\n")
    
    # Add reflection prompt for emotional analysis
    lines.append("\n## Emotional Analysis\n")
    lines.append(summary)
    file_text = "\n".join(lines)
    await save_journal_entry(file_text)
    
    return "Conversation saved to journal"

@mcp.resource("journals://recent")
def get_recent_journals() -> str:
    """Get contents of 5 most recent journal entries."""

    try:
        pattern = f"{config.file_prefix}*{config.file_extension}"
        
        files = sorted(config.journal_dir.glob(pattern), reverse=True)

        entries = []
        for file in files[:5]:
            entries.append(f"# Journal from {file.stem.replace(config.file_prefix + '_', '')}\n")
            entries.append(file.read_text(encoding='utf-8'))
            entries.append("\n---\n")
            
        return "\n".join(entries) if entries else f"No journal entries found in {config.journal_dir} matching {pattern}"
    except Exception as e:
        return f"Error reading journals: {str(e)}"

if __name__ == "__main__":
    mcp.run()