"""Configuration settings for the journaling MCP server."""

import os
from pathlib import Path
from typing import Dict, Any, Optional
from dataclasses import dataclass, field

from ..exceptions import ConfigurationError


@dataclass
class JournalConfig:
    """Configuration settings for the journaling server."""
    
    journal_dir: Path
    filename_prefix: str = "journal"
    file_extension: str = ".md"
    max_recent_entries: int = 5
    enable_backup: bool = True
    backup_dir: Optional[Path] = None
    
    # Default configuration values
    DEFAULTS: Dict[str, Any] = field(default_factory=lambda: {
        "JOURNAL_DIR": "journal",
        "FILENAME_PREFIX": "journal", 
        "FILE_EXTENSION": "md",
        "MAX_RECENT_ENTRIES": "5",
        "ENABLE_BACKUP": "true",
        "BACKUP_DIR": None,
    })
    
    def __post_init__(self) -> None:
        """Validate and initialize configuration after creation."""
        self._validate_config()
        self._setup_directories()
    
    def _validate_config(self) -> None:
        """Validate configuration values."""
        if not self.filename_prefix:
            raise ConfigurationError("Filename prefix cannot be empty")
        
        if not self.file_extension.startswith('.'):
            self.file_extension = '.' + self.file_extension
        
        if self.max_recent_entries < 1:
            raise ConfigurationError("max_recent_entries must be at least 1")
        
        if self.enable_backup and self.backup_dir is None:
            self.backup_dir = self.journal_dir / "backups"
    
    def _setup_directories(self) -> None:
        """Create necessary directories."""
        try:
            self.journal_dir.mkdir(parents=True, exist_ok=True)
            if self.enable_backup and self.backup_dir:
                self.backup_dir.mkdir(parents=True, exist_ok=True)
        except OSError as e:
            raise ConfigurationError(
                f"Failed to create directories: {e}",
                f"journal_dir: {self.journal_dir}, backup_dir: {self.backup_dir}"
            )
    
    def get_default_filepath(self) -> Path:
        """Get default filepath for current date."""
        from datetime import datetime
        today = datetime.now().strftime("%Y-%m-%d")
        filename = f"{self.filename_prefix}_{today}{self.file_extension}"
        return self.journal_dir / filename
    
    def resolve_filepath(self, filepath: Optional[str] = None) -> Path:
        """
        Resolve filepath, ensuring it's within journal directory.
        
        Args:
            filepath: Optional specific filepath
            
        Returns:
            Path: Resolved and validated filepath
            
        Raises:
            ConfigurationError: If path is invalid or outside journal directory
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
            resolved_path = path.resolve()
            resolved_journal_dir = self.journal_dir.resolve()
            
            if not str(resolved_path).startswith(str(resolved_journal_dir)):
                raise ConfigurationError(
                    "Path must be within journal directory",
                    f"Attempted path: {resolved_path}, Journal dir: {resolved_journal_dir}"
                )
        except (RuntimeError, OSError) as e:
            raise ConfigurationError(f"Invalid filepath: {e}")
            
        return path


def load_config() -> JournalConfig:
    """
    Load configuration from environment variables.
    
    Returns:
        JournalConfig: Configured instance
        
    Raises:
        ConfigurationError: If configuration is invalid
    """
    from dotenv import load_dotenv
    
    # Load environment variables
    load_dotenv()
    
    # Define defaults here since they're not accessible as class attribute yet
    defaults = {
        "JOURNAL_DIR": "journal",
        "FILENAME_PREFIX": "journal", 
        "FILE_EXTENSION": "md",
        "MAX_RECENT_ENTRIES": "5",
        "ENABLE_BACKUP": "true",
        "BACKUP_DIR": None,
    }
    
    try:
        journal_dir = Path(os.getenv("JOURNAL_DIR", defaults["JOURNAL_DIR"]))
        filename_prefix = os.getenv("FILENAME_PREFIX", defaults["FILENAME_PREFIX"])
        file_extension = os.getenv("FILE_EXTENSION", defaults["FILE_EXTENSION"])
        max_recent_entries = int(os.getenv("MAX_RECENT_ENTRIES", defaults["MAX_RECENT_ENTRIES"]))
        enable_backup = os.getenv("ENABLE_BACKUP", defaults["ENABLE_BACKUP"]).lower() == "true"
        
        backup_dir = None
        if backup_dir_env := os.getenv("BACKUP_DIR"):
            backup_dir = Path(backup_dir_env)
        
        return JournalConfig(
            journal_dir=journal_dir,
            filename_prefix=filename_prefix,
            file_extension=file_extension,
            max_recent_entries=max_recent_entries,
            enable_backup=enable_backup,
            backup_dir=backup_dir
        )
        
    except (ValueError, TypeError) as e:
        raise ConfigurationError(f"Invalid configuration value: {e}")