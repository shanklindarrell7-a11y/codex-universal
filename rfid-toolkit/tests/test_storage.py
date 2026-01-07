"""Unit tests for RFID storage system."""

import pytest
import tempfile
from pathlib import Path
from rfid_toolkit.storage import RFIDStorage
from rfid_toolkit.models import RFIDTag, TagType


@pytest.fixture
def temp_storage():
    """Create a temporary storage instance."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.db"
        storage = RFIDStorage(db_path)
        yield storage


@pytest.fixture
def sample_tag():
    """Create a sample RFID tag."""
    return RFIDTag(
        uid="DEADBEEF01234567",
        data="0102030405060708",
        name="Test Tag",
        tag_type=TagType.EM4100,
        frequency=125,
        description="Test tag for unit tests"
    )


class TestRFIDStorage:
    """Test suite for RFIDStorage."""

    def test_storage_initialization(self, temp_storage):
        """Test storage initialization creates database."""
        assert temp_storage.db_path.exists()

    def test_save_tag(self, temp_storage, sample_tag):
        """Test saving a tag."""
        temp_storage.save(sample_tag)
        retrieved = temp_storage.get(sample_tag.uid)
        assert retrieved is not None
        assert retrieved.uid == sample_tag.uid
        assert retrieved.name == sample_tag.name

    def test_get_tag(self, temp_storage, sample_tag):
        """Test retrieving a tag by UID."""
        temp_storage.save(sample_tag)
        retrieved = temp_storage.get(sample_tag.uid)
        assert retrieved is not None
        assert retrieved.uid == sample_tag.uid

    def test_get_nonexistent_tag(self, temp_storage):
        """Test retrieving a non-existent tag."""
        result = temp_storage.get("NONEXISTENT")
        assert result is None

    def test_get_by_name(self, temp_storage, sample_tag):
        """Test retrieving a tag by name."""
        temp_storage.save(sample_tag)
        retrieved = temp_storage.get_by_name(sample_tag.name)
        assert retrieved is not None
        assert retrieved.name == sample_tag.name

    def test_list_all_tags(self, temp_storage):
        """Test listing all tags."""
        tag1 = RFIDTag(uid="DEADBEEF01", data="0102030401", name="Tag1")
        tag2 = RFIDTag(uid="DEADBEEF02", data="0102030402", name="Tag2")
        
        temp_storage.save(tag1)
        temp_storage.save(tag2)
        
        all_tags = temp_storage.list_all()
        assert len(all_tags) == 2

    def test_list_by_type(self, temp_storage):
        """Test listing tags filtered by type."""
        tag1 = RFIDTag(uid="DEADBEEF01", data="0102030401", name="Tag1", tag_type=TagType.EM4100)
        tag2 = RFIDTag(uid="DEADBEEF02", data="0102030402", name="Tag2", tag_type=TagType.MIFARE_CLASSIC)
        
        temp_storage.save(tag1)
        temp_storage.save(tag2)
        
        em_tags = temp_storage.list_all(TagType.EM4100)
        assert len(em_tags) == 1
        assert em_tags[0].tag_type == TagType.EM4100

    def test_delete_tag(self, temp_storage, sample_tag):
        """Test deleting a tag."""
        temp_storage.save(sample_tag)
        assert temp_storage.get(sample_tag.uid) is not None
        
        deleted = temp_storage.delete(sample_tag.uid)
        assert deleted is True
        assert temp_storage.get(sample_tag.uid) is None

    def test_delete_nonexistent_tag(self, temp_storage):
        """Test deleting a non-existent tag."""
        deleted = temp_storage.delete("NONEXISTENT")
        assert deleted is False

    def test_search_tags(self, temp_storage):
        """Test searching tags."""
        tag1 = RFIDTag(uid="DEADBEEF01", data="0102030401", name="Office Card")
        tag2 = RFIDTag(uid="DEADBEEF02", data="0102030402", name="Home Key")
        tag3 = RFIDTag(uid="DEADBEEF03", data="0102030403", name="Office Backup")
        
        temp_storage.save(tag1)
        temp_storage.save(tag2)
        temp_storage.save(tag3)
        
        results = temp_storage.search("Office")
        assert len(results) == 2

    def test_export_import_json(self, temp_storage, sample_tag):
        """Test JSON export and import."""
        temp_storage.save(sample_tag)
        
        # Export
        with tempfile.TemporaryDirectory() as tmpdir:
            export_path = Path(tmpdir) / "export.json"
            count = temp_storage.export_to_json(export_path)
            assert count == 1
            assert export_path.exists()
            
            # Clear and import
            temp_storage.clear_all()
            assert len(temp_storage.list_all()) == 0
            
            imported = temp_storage.import_from_json(export_path)
            assert imported == 1
            assert len(temp_storage.list_all()) == 1

    def test_get_statistics(self, temp_storage):
        """Test getting storage statistics."""
        tag1 = RFIDTag(uid="DEADBEEF01", data="0102030401", name="Tag1", tag_type=TagType.EM4100)
        tag2 = RFIDTag(uid="DEADBEEF02", data="0102030402", name="Tag2", tag_type=TagType.EM4100)
        tag3 = RFIDTag(uid="DEADBEEF03", data="0102030403", name="Tag3", tag_type=TagType.MIFARE_CLASSIC)
        
        temp_storage.save(tag1)
        temp_storage.save(tag2)
        temp_storage.save(tag3)
        
        stats = temp_storage.get_statistics()
        assert stats["total_tags"] == 3
        assert stats["by_type"]["EM4100"] == 2
        assert stats["by_type"]["MIFARE_Classic"] == 1

    def test_update_existing_tag(self, temp_storage, sample_tag):
        """Test updating an existing tag."""
        temp_storage.save(sample_tag)
        
        # Modify and save again
        sample_tag.description = "Updated description"
        temp_storage.save(sample_tag)
        
        retrieved = temp_storage.get(sample_tag.uid)
        assert retrieved.description == "Updated description"

    def test_clear_all(self, temp_storage):
        """Test clearing all tags."""
        tag1 = RFIDTag(uid="DEADBEEF01", data="0102030401", name="Tag1")
        tag2 = RFIDTag(uid="DEADBEEF02", data="0102030402", name="Tag2")
        
        temp_storage.save(tag1)
        temp_storage.save(tag2)
        
        count = temp_storage.clear_all()
        assert count == 2
        assert len(temp_storage.list_all()) == 0
