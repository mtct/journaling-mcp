#!/usr/bin/env python3
"""
Main entry point for the Journaling MCP Server.

This script initializes and runs the professional journaling MCP server
with proper error handling and logging.
"""

import sys
import logging
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

from journaling_mcp import create_server
from journaling_mcp.exceptions import ConfigurationError


def main() -> None:
    """Main entry point for the server."""
    try:
        # Create and run the server
        server = create_server()
        server.run()
        
    except ConfigurationError as e:
        print(f"Configuration Error: {e}", file=sys.stderr)
        sys.exit(1)
        
    except KeyboardInterrupt:
        print("\\nServer stopped by user", file=sys.stderr)
        sys.exit(0)
        
    except Exception as e:
        print(f"Fatal Error: {e}", file=sys.stderr)
        logging.exception("Fatal error occurred")
        sys.exit(1)


if __name__ == "__main__":
    main()