"""Unit tests for RFID tag models."""

import pytest
from datetime import datetime
from rfid_toolkit.models import RFIDTag, TagType, TagFormat


class TestRFIDTag:
    """Test suite for RFIDTag model."""

    def test_create_valid_tag(self):
        """Test creating a valid RFID tag."""
        tag = RFIDTag(
            uid="DEADBEEF",
            data="0102030405",
            name="Test Tag",
            tag_type=TagType.EM4100,
            frequency=125
        )
        assert tag.uid == "DEADBEEF"
        assert tag.data == "0102030405"
        assert tag.name == "Test Tag"
        assert tag.tag_type == TagType.EM4100
        assert tag.frequency == 125

    def test_uid_validation(self):
        """Test UID hexadecimal validation."""
        # Valid hex with spaces and colons
        tag = RFIDTag(
            uid="DE:AD:BE:EF",
            data="01020304",
            name="Test Tag"
        )
        assert tag.uid == "DEADBEEF"

        # Invalid hex should raise error
        with pytest.raises(ValueError):
            RFIDTag(uid="INVALID", data="01020304", name="Test")

    def test_frequency_validation(self):
        """Test frequency validation."""
        # Valid frequencies
        for freq in [125, 134, 13560]:
            tag = RFIDTag(
                uid="DEADBEEF",
                data="01020304",
                name="Test",
                frequency=freq
            )
            assert tag.frequency == freq

        # Invalid frequency should raise error
        with pytest.raises(ValueError):
            RFIDTag(
                uid="DEADBEEF",
                data="01020304",
                name="Test",
                frequency=999
            )

    def test_to_flipper_format(self):
        """Test conversion to Flipper Zero format."""
        tag = RFIDTag(
            uid="DEADBEEF",
            data="0102030405",
            name="Test Tag",
            tag_type=TagType.EM4100,
            description="Test description"
        )
        
        flipper_data = tag.to_flipper_format()
        assert "Filetype: Flipper RFID key" in flipper_data
        assert "Test Tag" in flipper_data
        assert "EM4100" in flipper_data
        assert "0102030405" in flipper_data

    def test_to_dict_and_from_dict(self):
        """Test serialization and deserialization."""
        original = RFIDTag(
            uid="DEADBEEF",
            data="0102030405",
            name="Test Tag",
            tag_type=TagType.MIFARE_CLASSIC,
            frequency=13560,
            description="Test"
        )
        
        # Convert to dict and back
        tag_dict = original.to_dict()
        restored = RFIDTag.from_dict(tag_dict)
        
        assert restored.uid == original.uid
        assert restored.data == original.data
        assert restored.name == original.name
        assert restored.tag_type == original.tag_type
        assert restored.frequency == original.frequency

    def test_clone_tag(self):
        """Test tag cloning."""
        original = RFIDTag(
            uid="DEADBEEF",
            data="0102030405",
            name="Original Tag"
        )
        
        # Clone with new name
        clone = original.clone(new_name="Cloned Tag")
        assert clone.name == "Cloned Tag"
        assert clone.uid == original.uid
        assert clone.data == original.data
        
        # Clone with auto-generated name
        clone2 = original.clone()
        assert clone2.name == "Original Tag_clone"


class TestTagType:
    """Test suite for TagType enum."""

    def test_tag_types(self):
        """Test all tag type values."""
        assert TagType.EM4100.value == "EM4100"
        assert TagType.MIFARE_CLASSIC.value == "MIFARE_Classic"
        assert TagType.T5577.value == "T5577"

    def test_tag_type_enum(self):
        """Test TagType enumeration."""
        assert len(list(TagType)) >= 9
        assert TagType.UNKNOWN in TagType


class TestTagFormat:
    """Test suite for TagFormat enum."""

    def test_format_types(self):
        """Test all format type values."""
        assert TagFormat.HEX.value == "hex"
        assert TagFormat.DECIMAL.value == "decimal"
        assert TagFormat.BINARY.value == "binary"
        assert TagFormat.FLIPPER.value == "flipper"
