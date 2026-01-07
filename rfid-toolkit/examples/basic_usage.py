#!/usr/bin/env python3
"""
Example usage of the Flipper Zero RFID Toolkit.

This script demonstrates various features of the toolkit including
storage, duplication, and transmission capabilities.
"""

from rfid_toolkit import RFIDTag, RFIDStorage, RFIDDuplicator, FlipperTransmitter
from rfid_toolkit.models import TagType, TagFormat
from pathlib import Path


def main():
    print("=" * 60)
    print("Flipper Zero RFID Toolkit - Example Usage")
    print("=" * 60)
    print()

    # Initialize storage
    print("1. Initializing storage...")
    storage = RFIDStorage()
    print(f"   ✓ Storage initialized at {storage.db_path}")
    print()

    # Create sample tags
    print("2. Creating sample RFID tags...")
    
    tag1 = RFIDTag(
        uid="DEADBEEF01234567",
        data="0102030405060708",
        name="Office Access Card",
        tag_type=TagType.EM4100,
        frequency=125,
        description="Main office building access"
    )
    
    tag2 = RFIDTag(
        uid="CAFEBABE89ABCDEF",
        data="A1B2C3D4E5F60708",
        name="Parking Garage Card",
        tag_type=TagType.HID_PROX,
        frequency=125,
        description="Underground parking access"
    )
    
    tag3 = RFIDTag(
        uid="1234567890ABCDEF",
        data="FFEEDDCCBBAA9988",
        name="Gym Membership",
        tag_type=TagType.MIFARE_CLASSIC,
        frequency=13560,
        description="24/7 gym access card"
    )
    
    print(f"   ✓ Created {tag1.name}")
    print(f"   ✓ Created {tag2.name}")
    print(f"   ✓ Created {tag3.name}")
    print()

    # Save tags to storage
    print("3. Saving tags to storage...")
    storage.save(tag1)
    storage.save(tag2)
    storage.save(tag3)
    print("   ✓ All tags saved successfully")
    print()

    # List all tags
    print("4. Listing all stored tags...")
    all_tags = storage.list_all()
    for tag in all_tags:
        print(f"   • {tag.name} ({tag.tag_type.value}) - UID: {tag.uid[:16]}...")
    print()

    # Clone a tag
    print("5. Cloning a tag...")
    cloned_tag = RFIDDuplicator.duplicate_tag(tag1, new_name="Office Access Card - Backup")
    storage.save(cloned_tag)
    print(f"   ✓ Cloned '{tag1.name}' as '{cloned_tag.name}'")
    print(f"   • Original UID: {tag1.uid}")
    print(f"   • Clone UID: {cloned_tag.uid}")
    print()

    # Create writable clone
    print("6. Creating writable clone (T5577)...")
    writable = RFIDDuplicator.clone_writable(tag2)
    storage.save(writable)
    print(f"   ✓ Created writable clone: {writable.name}")
    print(f"   • Type: {writable.tag_type.value}")
    print()

    # Analyze a tag
    print("7. Analyzing tag structure...")
    analysis = RFIDDuplicator.analyze_tag(tag3)
    print(f"   Tag: {tag3.name}")
    print(f"   • Type: {analysis['tag_type']}")
    print(f"   • Frequency: {analysis['frequency']} ({analysis['frequency_band']})")
    print(f"   • Writable: {analysis['writable']}")
    print(f"   • Cloneable: {analysis['cloneable']}")
    print(f"   • Security features:")
    for feature in analysis['security_features']:
        print(f"     - {feature}")
    print()

    # Search tags
    print("8. Searching for tags...")
    results = storage.search("Office")
    print(f"   Found {len(results)} tag(s) matching 'Office':")
    for tag in results:
        print(f"   • {tag.name}")
    print()

    # Get statistics
    print("9. Storage statistics...")
    stats = storage.get_statistics()
    print(f"   • Total tags: {stats['total_tags']}")
    print(f"   • Database size: {stats['database_size']:,} bytes")
    print(f"   • Tags by type:")
    for tag_type, count in stats['by_type'].items():
        print(f"     - {tag_type}: {count}")
    print()

    # Export to JSON
    print("10. Exporting tags to JSON...")
    export_path = Path("/tmp/rfid_export.json")
    count = storage.export_to_json(export_path)
    print(f"   ✓ Exported {count} tags to {export_path}")
    print()

    # Convert format
    print("11. Converting tag format...")
    converted = RFIDDuplicator.convert_format(tag1, TagFormat.FLIPPER)
    print(f"   ✓ Converted {tag1.name} to Flipper format")
    print(f"   • Original format: {tag1.format.value}")
    print(f"   • New format: {converted.format.value}")
    print()

    # Prepare for emulation
    print("12. Preparing tag for emulation...")
    emulation_config = RFIDDuplicator.emulate_tag(tag1)
    print(f"   ✓ Emulation configuration prepared for {tag1.name}")
    print(f"   • Emulation mode: {emulation_config['emulation_mode']}")
    print(f"   • Modulation: {emulation_config['configuration']['modulation']}")
    print(f"   • Encoding: {emulation_config['configuration']['encoding']}")
    print()

    # Export to Flipper format
    print("13. Generating Flipper Zero file format...")
    flipper_data = tag1.to_flipper_format()
    print("   ✓ Flipper format generated:")
    print("   " + "\n   ".join(flipper_data.split("\n")))
    print()

    # Note about transmission
    print("14. Transmission capabilities (requires Flipper Zero):")
    print("   To transmit tags to Flipper Zero, connect your device via USB")
    print("   and use the following commands:")
    print()
    print("   # Emulate a tag:")
    print(f"   flipper-rfid transmit send '{tag1.name}' --mode emulate")
    print()
    print("   # Save to Flipper storage:")
    print(f"   flipper-rfid transmit send '{tag1.name}' --mode save")
    print()
    print("   # Read tag from Flipper:")
    print("   flipper-rfid transmit read --save")
    print()

    print("=" * 60)
    print("Example completed successfully!")
    print("=" * 60)
    print()
    print("Next steps:")
    print("1. View all tags: flipper-rfid storage list")
    print("2. Get tag details: flipper-rfid storage get 'Office Access Card'")
    print("3. Connect Flipper Zero and transmit tags")
    print()


if __name__ == "__main__":
    main()
