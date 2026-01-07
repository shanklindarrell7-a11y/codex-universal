"""
RFID tag storage system with SQLite backend.
"""

import json
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Dict, Any
from contextlib import contextmanager

from rfid_toolkit.models import RFIDTag, TagType


class RFIDStorage:
    """
    Professional storage system for RFID tags using SQLite.
    
    Provides thread-safe storage, retrieval, and management of RFID tags
    with full CRUD operations and export/import capabilities.
    """

    def __init__(self, db_path: Optional[Path] = None):
        """
        Initialize storage system.
        
        Args:
            db_path: Path to SQLite database file. If None, uses default location.
        """
        if db_path is None:
            db_path = Path.home() / ".flipper_rfid" / "tags.db"
        
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_database()

    @contextmanager
    def _get_connection(self):
        """Context manager for database connections."""
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def _init_database(self) -> None:
        """Initialize database schema."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS rfid_tags (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    uid TEXT NOT NULL UNIQUE,
                    tag_type TEXT NOT NULL,
                    data TEXT NOT NULL,
                    format TEXT NOT NULL,
                    name TEXT NOT NULL,
                    description TEXT,
                    frequency INTEGER NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    metadata TEXT NOT NULL
                )
            """)
            
            # Create indexes for faster lookups
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_uid ON rfid_tags(uid)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_name ON rfid_tags(name)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_tag_type ON rfid_tags(tag_type)
            """)

    def save(self, tag: RFIDTag) -> None:
        """
        Save or update an RFID tag.
        
        Args:
            tag: RFIDTag instance to save
            
        Raises:
            ValueError: If tag data is invalid
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            now = datetime.utcnow().isoformat()
            
            cursor.execute("""
                INSERT INTO rfid_tags (
                    uid, tag_type, data, format, name, description,
                    frequency, created_at, updated_at, metadata
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(uid) DO UPDATE SET
                    tag_type = excluded.tag_type,
                    data = excluded.data,
                    format = excluded.format,
                    name = excluded.name,
                    description = excluded.description,
                    frequency = excluded.frequency,
                    updated_at = excluded.updated_at,
                    metadata = excluded.metadata
            """, (
                tag.uid,
                tag.tag_type.value,
                tag.data,
                tag.format.value,
                tag.name,
                tag.description,
                tag.frequency,
                tag.created_at.isoformat(),
                now,
                json.dumps(tag.metadata)
            ))

    def get(self, uid: str) -> Optional[RFIDTag]:
        """
        Retrieve a tag by its UID.
        
        Args:
            uid: Unique identifier of the tag
            
        Returns:
            RFIDTag if found, None otherwise
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM rfid_tags WHERE uid = ?", (uid,))
            row = cursor.fetchone()
            
            if row:
                return self._row_to_tag(row)
            return None

    def get_by_name(self, name: str) -> Optional[RFIDTag]:
        """
        Retrieve a tag by its name.
        
        Args:
            name: Name of the tag
            
        Returns:
            RFIDTag if found, None otherwise
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM rfid_tags WHERE name = ?", (name,))
            row = cursor.fetchone()
            
            if row:
                return self._row_to_tag(row)
            return None

    def list_all(self, tag_type: Optional[TagType] = None) -> List[RFIDTag]:
        """
        List all stored tags, optionally filtered by type.
        
        Args:
            tag_type: Optional filter by tag type
            
        Returns:
            List of RFIDTag instances
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            if tag_type:
                cursor.execute(
                    "SELECT * FROM rfid_tags WHERE tag_type = ? ORDER BY created_at DESC",
                    (tag_type.value,)
                )
            else:
                cursor.execute("SELECT * FROM rfid_tags ORDER BY created_at DESC")
            
            return [self._row_to_tag(row) for row in cursor.fetchall()]

    def delete(self, uid: str) -> bool:
        """
        Delete a tag by its UID.
        
        Args:
            uid: Unique identifier of the tag
            
        Returns:
            True if tag was deleted, False if not found
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM rfid_tags WHERE uid = ?", (uid,))
            return cursor.rowcount > 0

    def search(self, query: str) -> List[RFIDTag]:
        """
        Search tags by name or description.
        
        Args:
            query: Search query string
            
        Returns:
            List of matching RFIDTag instances
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            search_pattern = f"%{query}%"
            cursor.execute("""
                SELECT * FROM rfid_tags 
                WHERE name LIKE ? OR description LIKE ?
                ORDER BY created_at DESC
            """, (search_pattern, search_pattern))
            
            return [self._row_to_tag(row) for row in cursor.fetchall()]

    def export_to_json(self, output_path: Path) -> int:
        """
        Export all tags to JSON file.
        
        Args:
            output_path: Path to output JSON file
            
        Returns:
            Number of tags exported
        """
        tags = self.list_all()
        data = {
            "version": "1.0",
            "exported_at": datetime.utcnow().isoformat(),
            "tags": [tag.to_dict() for tag in tags]
        }
        
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w') as f:
            json.dump(data, f, indent=2)
        
        return len(tags)

    def import_from_json(self, input_path: Path) -> int:
        """
        Import tags from JSON file.
        
        Args:
            input_path: Path to input JSON file
            
        Returns:
            Number of tags imported
        """
        with open(input_path, 'r') as f:
            data = json.load(f)
        
        count = 0
        for tag_data in data.get("tags", []):
            tag = RFIDTag.from_dict(tag_data)
            self.save(tag)
            count += 1
        
        return count

    def get_statistics(self) -> Dict[str, Any]:
        """
        Get storage statistics.
        
        Returns:
            Dictionary with storage statistics
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            # Total count
            cursor.execute("SELECT COUNT(*) as total FROM rfid_tags")
            total = cursor.fetchone()["total"]
            
            # Count by type
            cursor.execute("""
                SELECT tag_type, COUNT(*) as count 
                FROM rfid_tags 
                GROUP BY tag_type
            """)
            by_type = {row["tag_type"]: row["count"] for row in cursor.fetchall()}
            
            # Database size
            db_size = self.db_path.stat().st_size if self.db_path.exists() else 0
            
            return {
                "total_tags": total,
                "by_type": by_type,
                "database_size": db_size,
                "database_path": str(self.db_path)
            }

    def _row_to_tag(self, row: sqlite3.Row) -> RFIDTag:
        """Convert database row to RFIDTag instance."""
        return RFIDTag(
            uid=row["uid"],
            tag_type=TagType(row["tag_type"]),
            data=row["data"],
            format=row["format"],
            name=row["name"],
            description=row["description"],
            frequency=row["frequency"],
            created_at=datetime.fromisoformat(row["created_at"]),
            metadata=json.loads(row["metadata"])
        )

    def clear_all(self) -> int:
        """
        Clear all tags from storage (use with caution).
        
        Returns:
            Number of tags deleted
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) as count FROM rfid_tags")
            count = cursor.fetchone()["count"]
            cursor.execute("DELETE FROM rfid_tags")
            return count
