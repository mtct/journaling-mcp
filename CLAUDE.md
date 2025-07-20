# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a professional MCP (Message Control Protocol) server for interactive journaling with emotional analysis and automatic conversation saving. The server features a modular architecture with proper separation of concerns, comprehensive error handling, and extensive configuration options.

## Development Commands

**Run the MCP server (new professional version):**
```bash
uv run main.py
```

**Run the legacy server:**
```bash
uv run server.py
```

**Install dependencies:**
```bash
uv sync
```

**Run tests (when available):**
```bash
pytest src/tests/
```

## Architecture

### Professional Structure (v0.2.0+)

The codebase follows a professional Python package structure:

```
src/journaling_mcp/
├── __init__.py                 # Package entry point
├── main.py                     # CLI entry point
├── server.py                   # Main server class
├── config/
│   ├── __init__.py
│   └── settings.py             # Configuration management
├── models/
│   ├── __init__.py
│   ├── conversation.py         # Conversation data models
│   └── journal.py              # Journal entry models
├── services/
│   ├── __init__.py
│   ├── conversation_service.py # Conversation management
│   └── journal_service.py      # Journal file operations
├── exceptions/
│   ├── __init__.py
│   ├── base.py                 # Base exception classes
│   ├── config.py               # Configuration exceptions
│   └── journal.py              # Journal-specific exceptions
└── utils/
    ├── __init__.py
    └── logging.py              # Logging configuration
```

### Core Components

- **JournalingMCPServer** (`src/journaling_mcp/server.py`): Main server class with dependency injection
- **JournalConfig** (`src/journaling_mcp/config/settings.py`): Professional configuration management with validation
- **JournalService** (`src/journaling_mcp/services/journal_service.py`): File operations and journal management
- **ConversationService** (`src/journaling_mcp/services/conversation_service.py`): Conversation state management
- **Data Models** (`src/journaling_mcp/models/`): Strongly typed data structures with methods

### Key Features

- **Professional Error Handling**: Custom exception hierarchy with detailed error messages
- **Comprehensive Logging**: Rotating file logs with configurable levels
- **Data Models**: Strongly typed models for conversations and journal entries
- **Service Layer**: Separation of business logic from MCP endpoint handling
- **Configuration Management**: Environment-based config with validation and defaults
- **Backup System**: Automatic backup creation for journal files
- **Statistics Tracking**: Word counts, entry counts, and metadata

### MCP Tools

- `start_new_session()`: Initialize new conversation session with unique ID
- `record_interaction(user_message, assistant_message)`: Record message pairs with metadata
- `generate_session_summary(summary, emotional_analysis, reflections, tags, mood_rating)`: Create comprehensive journal entry
- `get_journal_statistics()`: Get collection statistics and metrics
- `add_journal_tags(filepath, tags)`: Add tags to existing entries

### MCP Resources

- `journals://recent`: Access recent journal entries
- `journals://statistics`: Get statistics as JSON

### Configuration

Enhanced environment variables in `.env`:
- `JOURNAL_DIR`: Storage directory (default: "journal")
- `FILENAME_PREFIX`: File name prefix (default: "journal") 
- `FILE_EXTENSION`: File extension (default: "md")
- `MAX_RECENT_ENTRIES`: Number of recent entries to return (default: 5)
- `ENABLE_BACKUP`: Enable automatic backups (default: true)
- `BACKUP_DIR`: Backup directory (optional, defaults to journal_dir/backups)

### Entry Format

Enhanced journal entries include:
1. Title with metadata (tags, mood rating)
2. Timestamped conversation transcript
3. Summary section
4. Emotional analysis
5. Personal reflections
6. Statistics footer (word count, entry count, timestamps)

### Security & Validation

- Comprehensive path validation preventing directory traversal
- File extension enforcement
- Configuration validation with meaningful error messages
- Proper exception handling at all levels
- Secure file operations with backup creation

## Development Notes

- The legacy `server.py` is maintained for backward compatibility
- New development should use the professional structure in `src/journaling_mcp/`
- All new features should include proper error handling and logging
- Data models should be used instead of raw dictionaries
- Services should handle business logic, keeping MCP endpoints thin