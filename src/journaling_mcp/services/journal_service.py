"""Service for managing journal entries and file operations."""

import logging
import shutil
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Dict, Any

from ..config import JournalConfig
from ..models import JournalEntry, ConversationLog
from ..exceptions import JournalError, JournalNotFoundError, InvalidJournalPathError

logger = logging.getLogger(__name__)


class JournalService:
    """Service for managing journal entries and file operations."""
    
    def __init__(self, config: JournalConfig) -> None:
        self.config = config
        self._logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
    
    def create_journal_entry(self, 
                           title: Optional[str] = None,
                           conversation: Optional[ConversationLog] = None,
                           summary: str = "",
                           emotional_analysis: str = "",
                           reflections: str = "") -> JournalEntry:
        """
        Create a new journal entry.
        
        Args:
            title: Entry title (defaults to formatted date)
            conversation: Conversation log to include
            summary: Summary of the session
            emotional_analysis: Emotional analysis content
            reflections: Personal reflections
            
        Returns:
            JournalEntry: The created journal entry
        """
        if title is None:
            title = f"Journal Entry - {datetime.now().strftime('%B %d, %Y')}"
        
        entry = JournalEntry(
            title=title,
            conversation=conversation or ConversationLog(),
            summary=summary,
            emotional_analysis=emotional_analysis,
            reflections=reflections
        )
        
        self._logger.info(f"Created journal entry: {title}")
        return entry
    
    def save_journal_entry(self, entry: JournalEntry, filepath: Optional[str] = None) -> Path:
        """
        Save a journal entry to file.
        
        Args:
            entry: The journal entry to save
            filepath: Optional specific filepath
            
        Returns:
            Path: The path where the entry was saved
            
        Raises:
            JournalError: If saving fails
        """
        try:
            # Resolve the file path
            save_path = self.config.resolve_filepath(filepath)
            
            # Create backup if file exists and backup is enabled
            if save_path.exists() and self.config.enable_backup:
                self._create_backup(save_path)
            
            # Ensure directory exists
            save_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Generate markdown content
            content = entry.to_markdown()
            
            # Write to file
            with open(save_path, 'w', encoding='utf-8') as file:
                file.write(content)
            
            # Update entry file path
            entry.file_path = save_path
            
            self._logger.info(f"Saved journal entry to: {save_path}")
            return save_path
            
        except Exception as e:
            error_msg = f"Failed to save journal entry: {e}"
            self._logger.error(error_msg)
            raise JournalError(error_msg) from e
    
    def load_journal_entry(self, filepath: str) -> JournalEntry:
        """
        Load a journal entry from file.
        
        Args:
            filepath: Path to the journal file
            
        Returns:
            JournalEntry: The loaded journal entry
            
        Raises:
            JournalNotFoundError: If the file doesn't exist
            JournalError: If loading fails
        """
        try:
            path = self.config.resolve_filepath(filepath)
            
            if not path.exists():
                raise JournalNotFoundError(f"Journal file not found: {path}")
            
            # For now, we'll create a basic entry with the file content
            # In a more advanced implementation, we could parse the markdown
            with open(path, 'r', encoding='utf-8') as file:
                content = file.read()
            
            # Extract title from first line if it's a header
            lines = content.split('\n')
            title = "Untitled Entry"
            if lines and lines[0].startswith('# '):
                title = lines[0][2:].strip()
            
            entry = JournalEntry(
                title=title,
                file_path=path
            )
            
            # Set file modification time as entry date
            entry.date = datetime.fromtimestamp(path.stat().st_mtime)
            
            self._logger.info(f"Loaded journal entry from: {path}")
            return entry
            
        except JournalNotFoundError:
            raise
        except Exception as e:
            error_msg = f"Failed to load journal entry: {e}"
            self._logger.error(error_msg)
            raise JournalError(error_msg) from e
    
    def get_recent_journals(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Get recent journal entries.
        
        Args:
            limit: Maximum number of entries to return (defaults to config max)
            
        Returns:
            List of journal entry information
        """
        if limit is None:
            limit = self.config.max_recent_entries
        
        try:
            pattern = f"{self.config.filename_prefix}*{self.config.file_extension}"
            files = sorted(
                self.config.journal_dir.glob(pattern), 
                key=lambda p: p.stat().st_mtime,
                reverse=True
            )
            
            entries = []
            for file_path in files[:limit]:
                try:
                    with open(file_path, 'r', encoding='utf-8') as file:
                        content = file.read()
                    
                    # Extract basic info
                    lines = content.split('\\n')
                    title = "Untitled Entry"
                    if lines and lines[0].startswith('# '):
                        title = lines[0][2:].strip()
                    
                    entry_info = {
                        "file_path": str(file_path),
                        "title": title,
                        "date": datetime.fromtimestamp(file_path.stat().st_mtime).strftime("%Y-%m-%d"),
                        "content": content,
                        "word_count": len(content.split()),
                        "size_bytes": file_path.stat().st_size
                    }
                    entries.append(entry_info)
                    
                except Exception as e:
                    self._logger.warning(f"Failed to read journal file {file_path}: {e}")
                    continue
            
            self._logger.info(f"Retrieved {len(entries)} recent journal entries")
            return entries
            
        except Exception as e:
            error_msg = f"Failed to get recent journals: {e}"
            self._logger.error(error_msg)
            raise JournalError(error_msg) from e
    
    def get_recent_journals_content(self, limit: Optional[int] = None) -> str:
        """
        Get content of recent journal entries as a formatted string.
        
        Args:
            limit: Maximum number of entries to return
            
        Returns:
            Formatted string with recent journal contents
        """
        try:
            entries = self.get_recent_journals(limit)
            
            if not entries:
                return f"No journal entries found in {self.config.journal_dir}"
            
            content_parts = []
            for entry in entries:
                # Extract date from filename or use file date
                filename = Path(entry["file_path"]).stem
                date_part = filename.replace(f"{self.config.filename_prefix}_", "")
                
                content_parts.append(f"# Journal from {date_part}")
                content_parts.append(entry["content"])
                content_parts.append("\\n---\\n")
            
            return "\\n".join(content_parts)
            
        except Exception as e:
            return f"Error reading journals: {e}"
    
    def delete_journal_entry(self, filepath: str, create_backup: bool = True) -> bool:
        """
        Delete a journal entry.
        
        Args:
            filepath: Path to the journal file
            create_backup: Whether to create a backup before deletion
            
        Returns:
            bool: True if deletion was successful
            
        Raises:
            JournalNotFoundError: If the file doesn't exist
            JournalError: If deletion fails
        """
        try:
            path = self.config.resolve_filepath(filepath)
            
            if not path.exists():
                raise JournalNotFoundError(f"Journal file not found: {path}")
            
            # Create backup if requested and backup is enabled
            if create_backup and self.config.enable_backup:
                self._create_backup(path)
            
            # Delete the file
            path.unlink()
            
            self._logger.info(f"Deleted journal entry: {path}")
            return True
            
        except JournalNotFoundError:
            raise
        except Exception as e:
            error_msg = f"Failed to delete journal entry: {e}"
            self._logger.error(error_msg)
            raise JournalError(error_msg) from e
    
    def _create_backup(self, filepath: Path) -> Optional[Path]:
        """
        Create a backup of a journal file.
        
        Args:
            filepath: Path to the file to backup
            
        Returns:
            Path to the backup file, or None if backup failed
        """
        if not self.config.enable_backup or not self.config.backup_dir:
            return None
        
        try:
            # Generate backup filename with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_name = f"{filepath.stem}_{timestamp}{filepath.suffix}"
            backup_path = self.config.backup_dir / backup_name
            
            # Copy the file
            shutil.copy2(filepath, backup_path)
            
            self._logger.info(f"Created backup: {backup_path}")
            return backup_path
            
        except Exception as e:
            self._logger.warning(f"Failed to create backup for {filepath}: {e}")
            return None
    
    def get_journal_statistics(self) -> Dict[str, Any]:
        """
        Get statistics about the journal collection.
        
        Returns:
            Dict with statistics about journal entries
        """
        try:
            pattern = f"{self.config.filename_prefix}*{self.config.file_extension}"
            files = list(self.config.journal_dir.glob(pattern))
            
            total_files = len(files)
            total_size = sum(f.stat().st_size for f in files)
            
            # Calculate total word count
            total_words = 0
            for file_path in files:
                try:
                    with open(file_path, 'r', encoding='utf-8') as file:
                        content = file.read()
                        total_words += len(content.split())
                except Exception:
                    continue
            
            # Get date range
            oldest_date = None
            newest_date = None
            if files:
                modification_times = [f.stat().st_mtime for f in files]
                oldest_date = datetime.fromtimestamp(min(modification_times))
                newest_date = datetime.fromtimestamp(max(modification_times))
            
            return {
                "total_entries": total_files,
                "total_size_bytes": total_size,
                "total_words": total_words,
                "average_words_per_entry": total_words // total_files if total_files > 0 else 0,
                "oldest_entry": oldest_date.isoformat() if oldest_date else None,
                "newest_entry": newest_date.isoformat() if newest_date else None,
                "journal_directory": str(self.config.journal_dir),
                "backup_enabled": self.config.enable_backup
            }
            
        except Exception as e:
            error_msg = f"Failed to get journal statistics: {e}"
            self._logger.error(error_msg)
            raise JournalError(error_msg) from e