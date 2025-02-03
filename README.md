# MCP Journaling Server

An MCP (Message Control Protocol) server designed to handle interactive journaling sessions with support for emotional analysis and automatic conversation saving.

<a href="https://glama.ai/mcp/servers/kiay3i2li7"><img width="380" height="200" src="https://glama.ai/mcp/servers/kiay3i2li7/badge" alt="Journaling Server MCP server" /></a>

## Features

- Automatic journaling session management
- Conversation saving in Markdown format
- Temporal analysis of conversations with timestamps
- Support for reading recent journal entries
- Chronological organization of journal entries

## Installation

Depend from your MCP client, on Claude Desktop:

```
    "mcpServers": {
        "journaling": {
            "command": "uv",
            "args": [
                "--directory",
                <REPOSITORY PATH>,
                "run",
                "server.py"
            ]
        }
    }
```

## Configuration

The server can be configured using environment variables in .env file:

- `JOURNAL_DIR`: Directory for saving journal files (default: ~/Documents/journal)
- `FILENAME_PREFIX`: Prefix for file names (default: "journal")
- `FILE_EXTENSION`: Journal file extension (default: ".md")

If not specified, default values will be used.

## File Structure

Journal entries are saved with the following structure:
```
[JOURNAL_DIR]/
├── journal_2025-01-27.md
├── journal_2025-01-26.md
└── ...
```

## Entry Format

Each journal entry includes:

1. Header with date
2. Conversation transcript with timestamps
3. Emotional analysis
4. Reflections and recurring themes

## API

### Tools

- `start_new_session()`: Start a new journaling session
- `record_interaction(user_message, assistant_message)`: Record a message exchange
- `generate_session_summary(summary)`: Generate and save session summary
- `get_recent_journals()`: Retrieve 5 most recent entries

### Resources

- `journals://recent`: Endpoint to access recent journal entries

### Prompts

- `start_journaling`: Initial prompt


