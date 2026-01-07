"""Unit tests for RFID duplicator."""

import pytest
from rfid_toolkit.duplicator import RFIDDuplicator
from rfid_toolkit.models import RFIDTag, TagType, TagFormat


@pytest.fixture
def sample_tag():
    """Create a sample RFID tag."""
    return RFIDTag(
        uid="DEADBEEF01234567",
        data="0102030405060708",
        name="Test Tag",
        tag_type=TagType.EM4100,
        frequency=125,
        description="Test tag"
    )


class TestRFIDDuplicator:
    """Test suite for RFIDDuplicator."""

    def test_duplicate_tag(self, sample_tag):
        """Test basic tag duplication."""
        duplicate = RFIDDuplicator.duplicate_tag(sample_tag)
        
        assert duplicate.name == "Test Tag_copy"
        assert duplicate.data == sample_tag.data
        assert duplicate.tag_type == sample_tag.tag_type
        assert duplicate.uid != sample_tag.uid  # Should generate new UID

    def test_duplicate_with_custom_name(self, sample_tag):
        """Test duplication with custom name."""
        duplicate = RFIDDuplicator.duplicate_tag(sample_tag, new_name="Custom Name")
        assert duplicate.name == "Custom Name"

    def test_duplicate_preserve_uid(self, sample_tag):
        """Test duplication with preserved UID."""
        duplicate = RFIDDuplicator.duplicate_tag(sample_tag, preserve_uid=True)
        assert duplicate.uid == sample_tag.uid

    def test_clone_writable(self, sample_tag):
        """Test cloning to writable format."""
        writable = RFIDDuplicator.clone_writable(sample_tag)
        
        assert writable.tag_type == TagType.T5577
        assert writable.data == sample_tag.data
        assert "writable" in writable.name

    def test_clone_writable_custom_type(self, sample_tag):
        """Test cloning to custom writable type."""
        writable = RFIDDuplicator.clone_writable(sample_tag, target_type=TagType.MIFARE_ULTRALIGHT)
        assert writable.tag_type == TagType.MIFARE_ULTRALIGHT

    def test_convert_format(self, sample_tag):
        """Test format conversion."""
        converted = RFIDDuplicator.convert_format(sample_tag, TagFormat.DECIMAL)
        assert converted.format == TagFormat.DECIMAL
        assert converted.uid == sample_tag.uid

    def test_emulate_tag(self, sample_tag):
        """Test tag emulation preparation."""
        emulation = RFIDDuplicator.emulate_tag(sample_tag)
        
        assert emulation["tag_type"] == sample_tag.tag_type.value
        assert emulation["uid"] == sample_tag.uid
        assert emulation["frequency"] == sample_tag.frequency
        assert "emulation_mode" in emulation
        assert "configuration" in emulation

    def test_analyze_tag(self, sample_tag):
        """Test tag analysis."""
        analysis = RFIDDuplicator.analyze_tag(sample_tag)
        
        assert analysis["tag_type"] == TagType.EM4100.value
        assert analysis["frequency"] == "125 kHz"
        assert analysis["frequency_band"] == "LF"
        assert "writable" in analysis
        assert "cloneable" in analysis
        assert "security_features" in analysis

    def test_analyze_mifare_classic(self):
        """Test analysis of MIFARE Classic tag."""
        tag = RFIDTag(
            uid="DEADBEEF",
            data="0102030405",
            name="MIFARE Test",
            tag_type=TagType.MIFARE_CLASSIC,
            frequency=13560
        )
        
        analysis = RFIDDuplicator.analyze_tag(tag)
        assert analysis["frequency_band"] == "HF"
        assert "sectors" in analysis
        assert "crypto" in analysis

    def test_get_security_features(self):
        """Test security features extraction."""
        features_em = RFIDDuplicator._get_security_features(TagType.EM4100)
        assert "Read-only" in features_em
        
        features_mifare = RFIDDuplicator._get_security_features(TagType.MIFARE_CLASSIC)
        assert len(features_mifare) > 0

    def test_get_emulation_mode(self):
        """Test emulation mode determination."""
        mode = RFIDDuplicator._get_emulation_mode(TagType.EM4100)
        assert mode == "EM4100"
        
        mode_hid = RFIDDuplicator._get_emulation_mode(TagType.HID_PROX)
        assert mode_hid == "HIDProx"

    def test_get_modulation(self):
        """Test modulation type determination."""
        mod_lf = RFIDDuplicator._get_modulation(125)
        assert mod_lf == "ASK"
        
        mod_hf = RFIDDuplicator._get_modulation(13560)
        assert mod_hf == "ISO14443A"

    def test_format_conversion_hex_to_decimal(self):
        """Test HEX to decimal conversion."""
        result = RFIDDuplicator._convert_data_format("FF", TagFormat.HEX, TagFormat.DECIMAL)
        assert result == "255"

    def test_format_conversion_decimal_to_hex(self):
        """Test decimal to HEX conversion."""
        result = RFIDDuplicator._convert_data_format("255", TagFormat.DECIMAL, TagFormat.HEX)
        assert result == "FF"

    def test_format_conversion_same_format(self):
        """Test conversion with same source and target format."""
        result = RFIDDuplicator._convert_data_format("DEADBEEF", TagFormat.HEX, TagFormat.HEX)
        assert result == "DEADBEEF"
