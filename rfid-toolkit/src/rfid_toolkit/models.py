"""
RFID Tag data models and enumerations.
"""

from datetime import datetime
from enum import Enum
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field, field_validator


class TagType(str, Enum):
    """Supported RFID tag types."""
    EM4100 = "EM4100"
    EM4102 = "EM4102"
    HID_PROX = "HID_Prox"
    INDALA = "Indala"
    MIFARE_CLASSIC = "MIFARE_Classic"
    MIFARE_ULTRALIGHT = "MIFARE_Ultralight"
    NTAG = "NTAG"
    ICLASS = "iClass"
    T5577 = "T5577"
    UNKNOWN = "Unknown"


class TagFormat(str, Enum):
    """Data format for RFID tags."""
    HEX = "hex"
    DECIMAL = "decimal"
    BINARY = "binary"
    FLIPPER = "flipper"  # Flipper Zero native format


class RFIDTag(BaseModel):
    """
    Represents an RFID tag with all its metadata and data.
    
    Attributes:
        uid: Unique identifier of the tag
        tag_type: Type of RFID tag
        data: Raw tag data in hexadecimal
        format: Data format
        name: Human-readable name for the tag
        description: Optional description
        frequency: Operating frequency in kHz (e.g., 125 for LF, 13560 for HF)
        created_at: Timestamp when tag was captured
        metadata: Additional metadata
    """
    uid: str = Field(..., description="Unique identifier (hex format)")
    tag_type: TagType = Field(default=TagType.UNKNOWN, description="RFID tag type")
    data: str = Field(..., description="Raw tag data in hex format")
    format: TagFormat = Field(default=TagFormat.HEX, description="Data format")
    name: str = Field(..., description="Human-readable tag name")
    description: Optional[str] = Field(None, description="Optional tag description")
    frequency: int = Field(default=125, description="Operating frequency in kHz")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")

    @field_validator("uid", "data")
    @classmethod
    def validate_hex(cls, v: str) -> str:
        """Validate that UIDs and data are valid hexadecimal."""
        if not v:
            raise ValueError("Value cannot be empty")
        try:
            # Allow spaces and colons for readability
            cleaned = v.replace(" ", "").replace(":", "").upper()
            int(cleaned, 16)
            return cleaned
        except ValueError:
            raise ValueError(f"Invalid hexadecimal value: {v}")

    @field_validator("frequency")
    @classmethod
    def validate_frequency(cls, v: int) -> int:
        """Validate frequency is in common RFID ranges."""
        valid_frequencies = [125, 134, 13560]  # Common LF and HF frequencies
        if v not in valid_frequencies:
            raise ValueError(f"Frequency must be one of {valid_frequencies} kHz")
        return v

    def to_flipper_format(self) -> str:
        """
        Convert tag data to Flipper Zero file format.
        
        Returns:
            String representation in Flipper Zero format
        """
        lines = [
            "Filetype: Flipper RFID key",
            "Version: 1",
            f"# {self.name}",
        ]
        
        if self.description:
            lines.append(f"# {self.description}")
        
        lines.extend([
            f"Key type: {self.tag_type.value}",
            f"Data: {self.data}",
        ])
        
        return "\n".join(lines)

    def to_dict(self) -> Dict[str, Any]:
        """Convert tag to dictionary format."""
        return {
            "uid": self.uid,
            "tag_type": self.tag_type.value,
            "data": self.data,
            "format": self.format.value,
            "name": self.name,
            "description": self.description,
            "frequency": self.frequency,
            "created_at": self.created_at.isoformat(),
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "RFIDTag":
        """Create tag from dictionary format."""
        if "created_at" in data and isinstance(data["created_at"], str):
            data["created_at"] = datetime.fromisoformat(data["created_at"])
        return cls(**data)

    def clone(self, new_name: Optional[str] = None) -> "RFIDTag":
        """
        Create a clone of this tag with optional new name.
        
        Args:
            new_name: Optional new name for the cloned tag
            
        Returns:
            New RFIDTag instance with cloned data
        """
        clone_data = self.to_dict()
        clone_data["created_at"] = datetime.utcnow()
        if new_name:
            clone_data["name"] = new_name
        else:
            clone_data["name"] = f"{self.name}_clone"
        
        return RFIDTag.from_dict(clone_data)
