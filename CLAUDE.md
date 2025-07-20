# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is an MCP (Message Control Protocol) server for interactive journaling with emotional analysis and automatic conversation saving. The server provides tools for recording conversations, generating summaries, and managing journal files.

## Development Commands

**Run the MCP server:**
```bash
uv run server.py
```

**Install dependencies:**
```bash
uv sync
```

## Architecture

### Core Components

- **JournalConfig** (`server.py:8-77`): Configuration management with environment variables and file path validation
- **FastMCP Server** (`server.py:82`): Main MCP server instance with tools, resources, and prompts
- **Conversation Management**: Global state tracking (`server.py:85`) with timestamped message logging

### Key Functions

- `start_new_session()`: Clears conversation log and starts fresh session
- `record_interaction()`: Stores user/assistant message pairs with timestamps
- `generate_session_summary()`: Creates markdown journal entry with conversation transcript and analysis
- `get_recent_journals()`: Resource endpoint returning 5 most recent journal files

### File Structure

Journal entries are saved as markdown files in the configured directory:
```
[JOURNAL_DIR]/
├── journal_2025-01-27.md
├── journal_2025-01-26.md
└── ...
```

### Configuration

Environment variables in `.env`:
- `JOURNAL_DIR`: Storage directory (default: "journal")
- `FILENAME_PREFIX`: File name prefix (default: "journal") 
- `FILE_EXTENSION`: File extension (default: "md")

### Security Features

- Path validation ensures files stay within journal directory (`server.py:69-76`)
- File extension enforcement
- Relative path resolution to prevent directory traversal

## MCP Integration

The server exposes:
- **Tools**: Session management and conversation recording
- **Resources**: `journals://recent` endpoint for accessing recent entries
- **Prompts**: `start_journaling` for session initialization

## Entry Format

Each journal entry includes:
1. Date header
2. Timestamped conversation transcript 
3. Emotional analysis section
4. Automatic markdown formatting