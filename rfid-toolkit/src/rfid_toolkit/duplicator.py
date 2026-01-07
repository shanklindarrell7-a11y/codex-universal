"""
RFID tag duplication and cloning utilities.
"""

from typing import Optional, Dict, Any
from datetime import datetime

from rfid_toolkit.models import RFIDTag, TagType, TagFormat


class RFIDDuplicator:
    """
    Professional RFID tag duplication system.
    
    Provides capabilities to clone, duplicate, and manipulate RFID tag data
    with support for various tag types and formats.
    """

    # Tag-specific data structures and sector information
    MIFARE_SECTORS = {
        "MIFARE_Classic_1K": 16,
        "MIFARE_Classic_4K": 40,
    }

    @staticmethod
    def duplicate_tag(
        original: RFIDTag,
        new_name: Optional[str] = None,
        preserve_uid: bool = False
    ) -> RFIDTag:
        """
        Create a duplicate of an RFID tag.
        
        Args:
            original: Original RFIDTag to duplicate
            new_name: Optional new name for the duplicate
            preserve_uid: If True, keep original UID (default: generate new UID)
            
        Returns:
            New RFIDTag instance with duplicated data
        """
        if new_name is None:
            new_name = f"{original.name}_copy"
        
        duplicate_data = {
            "uid": original.uid if preserve_uid else RFIDDuplicator._generate_new_uid(original.uid),
            "tag_type": original.tag_type,
            "data": original.data,
            "format": original.format,
            "name": new_name,
            "description": f"Duplicate of {original.name}",
            "frequency": original.frequency,
            "created_at": datetime.utcnow(),
            "metadata": {
                **original.metadata,
                "duplicated_from": original.uid,
                "duplicated_at": datetime.utcnow().isoformat(),
            }
        }
        
        return RFIDTag(**duplicate_data)

    @staticmethod
    def clone_writable(original: RFIDTag, target_type: Optional[TagType] = None) -> RFIDTag:
        """
        Clone a tag to a writable format (e.g., T5577).
        
        Args:
            original: Original RFIDTag to clone
            target_type: Target tag type (default: T5577 for writable cards)
            
        Returns:
            New RFIDTag configured for the writable target
        """
        if target_type is None:
            target_type = TagType.T5577  # T5577 is commonly used for cloning
        
        clone_data = {
            "uid": RFIDDuplicator._generate_new_uid(original.uid),
            "tag_type": target_type,
            "data": original.data,
            "format": original.format,
            "name": f"{original.name}_writable",
            "description": f"Writable clone of {original.name}",
            "frequency": original.frequency,
            "created_at": datetime.utcnow(),
            "metadata": {
                **original.metadata,
                "cloned_from": original.uid,
                "original_type": original.tag_type.value,
                "cloned_at": datetime.utcnow().isoformat(),
            }
        }
        
        return RFIDTag(**clone_data)

    @staticmethod
    def convert_format(tag: RFIDTag, target_format: TagFormat) -> RFIDTag:
        """
        Convert tag data to a different format.
        
        Args:
            tag: RFIDTag to convert
            target_format: Target format
            
        Returns:
            New RFIDTag with converted data format
        """
        converted_data = RFIDDuplicator._convert_data_format(
            tag.data,
            tag.format,
            target_format
        )
        
        return RFIDTag(
            uid=tag.uid,
            tag_type=tag.tag_type,
            data=converted_data,
            format=target_format,
            name=tag.name,
            description=tag.description,
            frequency=tag.frequency,
            created_at=tag.created_at,
            metadata={
                **tag.metadata,
                "converted_from": tag.format.value,
                "converted_at": datetime.utcnow().isoformat(),
            }
        )

    @staticmethod
    def emulate_tag(original: RFIDTag) -> Dict[str, Any]:
        """
        Prepare tag data for emulation on Flipper Zero.
        
        Args:
            original: RFIDTag to emulate
            
        Returns:
            Dictionary with emulation parameters
        """
        return {
            "tag_type": original.tag_type.value,
            "uid": original.uid,
            "data": original.data,
            "frequency": original.frequency,
            "emulation_mode": RFIDDuplicator._get_emulation_mode(original.tag_type),
            "configuration": {
                "modulation": RFIDDuplicator._get_modulation(original.frequency),
                "bit_rate": RFIDDuplicator._get_bit_rate(original.tag_type),
                "encoding": "Manchester" if original.frequency == 125 else "Miller",
            }
        }

    @staticmethod
    def analyze_tag(tag: RFIDTag) -> Dict[str, Any]:
        """
        Analyze tag data and provide detailed information.
        
        Args:
            tag: RFIDTag to analyze
            
        Returns:
            Dictionary with analysis results
        """
        analysis = {
            "tag_type": tag.tag_type.value,
            "frequency": f"{tag.frequency} kHz",
            "frequency_band": "LF" if tag.frequency < 1000 else "HF",
            "data_length": len(tag.data),
            "writable": tag.tag_type in [TagType.T5577, TagType.MIFARE_ULTRALIGHT],
            "cloneable": True,  # Most tags can be cloned to T5577
            "security_features": RFIDDuplicator._get_security_features(tag.tag_type),
        }
        
        # Add type-specific analysis
        if tag.tag_type == TagType.MIFARE_CLASSIC:
            analysis["sectors"] = 16  # 1K variant
            analysis["blocks_per_sector"] = 4
            analysis["crypto"] = "CRYPTO1"
        elif tag.tag_type == TagType.EM4100:
            analysis["structure"] = "64-bit ID"
            analysis["read_only"] = True
        
        return analysis

    @staticmethod
    def _generate_new_uid(original_uid: str) -> str:
        """Generate a new UID based on the original."""
        import hashlib
        timestamp = datetime.utcnow().isoformat().encode()
        hash_input = (original_uid + timestamp.decode()).encode()
        new_hash = hashlib.sha256(hash_input).hexdigest()
        # Take the same length as original UID
        return new_hash[:len(original_uid)].upper()

    @staticmethod
    def _convert_data_format(data: str, from_format: TagFormat, to_format: TagFormat) -> str:
        """Convert data between formats."""
        if from_format == to_format:
            return data
        
        # Convert to integer first
        if from_format == TagFormat.HEX:
            value = int(data, 16)
        elif from_format == TagFormat.DECIMAL:
            value = int(data)
        elif from_format == TagFormat.BINARY:
            value = int(data, 2)
        else:
            value = int(data.replace(" ", ""), 16)  # Assume hex for Flipper format
        
        # Convert to target format
        if to_format == TagFormat.HEX:
            return hex(value)[2:].upper()
        elif to_format == TagFormat.DECIMAL:
            return str(value)
        elif to_format == TagFormat.BINARY:
            return bin(value)[2:]
        else:  # Flipper format
            return hex(value)[2:].upper()

    @staticmethod
    def _get_emulation_mode(tag_type: TagType) -> str:
        """Get emulation mode for tag type."""
        emulation_modes = {
            TagType.EM4100: "EM4100",
            TagType.HID_PROX: "HIDProx",
            TagType.INDALA: "Indala",
            TagType.MIFARE_CLASSIC: "MifareClassic",
            TagType.MIFARE_ULTRALIGHT: "MifareUltralight",
            TagType.T5577: "Custom",
        }
        return emulation_modes.get(tag_type, "Generic")

    @staticmethod
    def _get_modulation(frequency: int) -> str:
        """Get modulation type based on frequency."""
        if frequency == 125:
            return "ASK"
        elif frequency == 134:
            return "FSK"
        else:  # 13.56 MHz
            return "ISO14443A"

    @staticmethod
    def _get_bit_rate(tag_type: TagType) -> int:
        """Get bit rate for tag type."""
        rates = {
            TagType.EM4100: 64,
            TagType.HID_PROX: 50,
            TagType.MIFARE_CLASSIC: 106,
            TagType.MIFARE_ULTRALIGHT: 106,
        }
        return rates.get(tag_type, 64)

    @staticmethod
    def _get_security_features(tag_type: TagType) -> list:
        """Get security features for tag type."""
        features = {
            TagType.EM4100: ["Read-only"],
            TagType.MIFARE_CLASSIC: ["CRYPTO1 encryption", "Access keys", "Sector access bits"],
            TagType.MIFARE_ULTRALIGHT: ["Counter", "Signature"],
            TagType.NTAG: ["Password protection", "Counter", "Signature"],
            TagType.ICLASS: ["Encryption", "Secure memory"],
            TagType.T5577: ["Programmable", "Multiple modulations"],
        }
        return features.get(tag_type, ["None"])
