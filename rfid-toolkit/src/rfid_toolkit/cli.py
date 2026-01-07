"""
Command-line interface for Flipper Zero RFID Toolkit.
"""

import sys
from pathlib import Path
from typing import Optional

import click
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich import print as rprint

from rfid_toolkit.models import RFIDTag, TagType, TagFormat
from rfid_toolkit.storage import RFIDStorage
from rfid_toolkit.duplicator import RFIDDuplicator
from rfid_toolkit.transmitter import FlipperTransmitter

console = Console()


@click.group()
@click.version_option(version="1.0.0")
def main():
    """Flipper Zero RFID Toolkit - Professional RFID management system."""
    pass


# Storage Commands
@main.group()
def storage():
    """Manage RFID tag storage."""
    pass


@storage.command("add")
@click.option("--uid", required=True, help="Tag UID (hex format)")
@click.option("--data", required=True, help="Tag data (hex format)")
@click.option("--name", required=True, help="Tag name")
@click.option("--type", "tag_type", type=click.Choice([t.value for t in TagType]), 
              default=TagType.UNKNOWN.value, help="Tag type")
@click.option("--frequency", type=int, default=125, help="Frequency in kHz (125, 134, or 13560)")
@click.option("--description", help="Tag description")
@click.option("--db", type=click.Path(), help="Database path")
def storage_add(uid, data, name, tag_type, frequency, description, db):
    """Add a new RFID tag to storage."""
    try:
        db_path = Path(db) if db else None
        storage_inst = RFIDStorage(db_path)
        
        tag = RFIDTag(
            uid=uid,
            data=data,
            name=name,
            tag_type=TagType(tag_type),
            frequency=frequency,
            description=description
        )
        
        storage_inst.save(tag)
        console.print(f"[green]✓[/green] Tag '{name}' added successfully", style="bold")
    except Exception as e:
        console.print(f"[red]✗[/red] Error: {e}", style="bold")
        sys.exit(1)


@storage.command("list")
@click.option("--type", "tag_type", type=click.Choice([t.value for t in TagType]), 
              help="Filter by tag type")
@click.option("--db", type=click.Path(), help="Database path")
def storage_list(tag_type, db):
    """List all stored RFID tags."""
    try:
        db_path = Path(db) if db else None
        storage_inst = RFIDStorage(db_path)
        
        filter_type = TagType(tag_type) if tag_type else None
        tags = storage_inst.list_all(filter_type)
        
        if not tags:
            console.print("[yellow]No tags found[/yellow]")
            return
        
        table = Table(title="Stored RFID Tags", show_header=True, header_style="bold magenta")
        table.add_column("Name", style="cyan")
        table.add_column("UID", style="green")
        table.add_column("Type", style="yellow")
        table.add_column("Frequency", justify="right")
        table.add_column("Created", style="dim")
        
        for tag in tags:
            table.add_row(
                tag.name,
                tag.uid[:16] + "..." if len(tag.uid) > 16 else tag.uid,
                tag.tag_type.value,
                f"{tag.frequency} kHz",
                tag.created_at.strftime("%Y-%m-%d %H:%M")
            )
        
        console.print(table)
        console.print(f"\n[bold]Total:[/bold] {len(tags)} tags")
    except Exception as e:
        console.print(f"[red]✗[/red] Error: {e}", style="bold")
        sys.exit(1)


@storage.command("get")
@click.argument("identifier")
@click.option("--by", type=click.Choice(["uid", "name"]), default="name", help="Search by UID or name")
@click.option("--db", type=click.Path(), help="Database path")
def storage_get(identifier, by, db):
    """Get details of a specific tag."""
    try:
        db_path = Path(db) if db else None
        storage_inst = RFIDStorage(db_path)
        
        if by == "uid":
            tag = storage_inst.get(identifier)
        else:
            tag = storage_inst.get_by_name(identifier)
        
        if not tag:
            console.print(f"[red]✗[/red] Tag not found: {identifier}", style="bold")
            sys.exit(1)
        
        panel_content = f"""[bold cyan]Name:[/bold cyan] {tag.name}
[bold cyan]UID:[/bold cyan] {tag.uid}
[bold cyan]Type:[/bold cyan] {tag.tag_type.value}
[bold cyan]Data:[/bold cyan] {tag.data}
[bold cyan]Frequency:[/bold cyan] {tag.frequency} kHz
[bold cyan]Created:[/bold cyan] {tag.created_at.isoformat()}
[bold cyan]Description:[/bold cyan] {tag.description or 'N/A'}"""
        
        console.print(Panel(panel_content, title="Tag Details", border_style="green"))
    except Exception as e:
        console.print(f"[red]✗[/red] Error: {e}", style="bold")
        sys.exit(1)


@storage.command("delete")
@click.argument("uid")
@click.option("--db", type=click.Path(), help="Database path")
@click.confirmation_option(prompt="Are you sure you want to delete this tag?")
def storage_delete(uid, db):
    """Delete a tag from storage."""
    try:
        db_path = Path(db) if db else None
        storage_inst = RFIDStorage(db_path)
        
        if storage_inst.delete(uid):
            console.print(f"[green]✓[/green] Tag deleted successfully", style="bold")
        else:
            console.print(f"[red]✗[/red] Tag not found: {uid}", style="bold")
            sys.exit(1)
    except Exception as e:
        console.print(f"[red]✗[/red] Error: {e}", style="bold")
        sys.exit(1)


@storage.command("export")
@click.argument("output", type=click.Path())
@click.option("--db", type=click.Path(), help="Database path")
def storage_export(output, db):
    """Export all tags to JSON file."""
    try:
        db_path = Path(db) if db else None
        storage_inst = RFIDStorage(db_path)
        
        count = storage_inst.export_to_json(Path(output))
        console.print(f"[green]✓[/green] Exported {count} tags to {output}", style="bold")
    except Exception as e:
        console.print(f"[red]✗[/red] Error: {e}", style="bold")
        sys.exit(1)


@storage.command("import")
@click.argument("input", type=click.Path(exists=True))
@click.option("--db", type=click.Path(), help="Database path")
def storage_import(input, db):
    """Import tags from JSON file."""
    try:
        db_path = Path(db) if db else None
        storage_inst = RFIDStorage(db_path)
        
        count = storage_inst.import_from_json(Path(input))
        console.print(f"[green]✓[/green] Imported {count} tags from {input}", style="bold")
    except Exception as e:
        console.print(f"[red]✗[/red] Error: {e}", style="bold")
        sys.exit(1)


@storage.command("stats")
@click.option("--db", type=click.Path(), help="Database path")
def storage_stats(db):
    """Show storage statistics."""
    try:
        db_path = Path(db) if db else None
        storage_inst = RFIDStorage(db_path)
        
        stats = storage_inst.get_statistics()
        
        panel_content = f"""[bold cyan]Total Tags:[/bold cyan] {stats['total_tags']}
[bold cyan]Database Size:[/bold cyan] {stats['database_size']:,} bytes
[bold cyan]Database Path:[/bold cyan] {stats['database_path']}

[bold cyan]Tags by Type:[/bold cyan]"""
        
        for tag_type, count in stats['by_type'].items():
            panel_content += f"\n  • {tag_type}: {count}"
        
        console.print(Panel(panel_content, title="Storage Statistics", border_style="blue"))
    except Exception as e:
        console.print(f"[red]✗[/red] Error: {e}", style="bold")
        sys.exit(1)


# Duplication Commands
@main.group()
def duplicate():
    """Duplicate and clone RFID tags."""
    pass


@duplicate.command("clone")
@click.argument("tag_name")
@click.option("--new-name", help="Name for the cloned tag")
@click.option("--preserve-uid", is_flag=True, help="Keep original UID")
@click.option("--db", type=click.Path(), help="Database path")
def duplicate_clone(tag_name, new_name, preserve_uid, db):
    """Clone an existing tag."""
    try:
        db_path = Path(db) if db else None
        storage_inst = RFIDStorage(db_path)
        
        original = storage_inst.get_by_name(tag_name)
        if not original:
            console.print(f"[red]✗[/red] Tag not found: {tag_name}", style="bold")
            sys.exit(1)
        
        cloned = RFIDDuplicator.duplicate_tag(original, new_name, preserve_uid)
        storage_inst.save(cloned)
        
        console.print(f"[green]✓[/green] Tag cloned successfully as '{cloned.name}'", style="bold")
    except Exception as e:
        console.print(f"[red]✗[/red] Error: {e}", style="bold")
        sys.exit(1)


@duplicate.command("writable")
@click.argument("tag_name")
@click.option("--target", type=click.Choice([t.value for t in TagType]), 
              default=TagType.T5577.value, help="Target writable tag type")
@click.option("--db", type=click.Path(), help="Database path")
def duplicate_writable(tag_name, target, db):
    """Convert tag to writable format (e.g., T5577)."""
    try:
        db_path = Path(db) if db else None
        storage_inst = RFIDStorage(db_path)
        
        original = storage_inst.get_by_name(tag_name)
        if not original:
            console.print(f"[red]✗[/red] Tag not found: {tag_name}", style="bold")
            sys.exit(1)
        
        writable = RFIDDuplicator.clone_writable(original, TagType(target))
        storage_inst.save(writable)
        
        console.print(f"[green]✓[/green] Writable clone created as '{writable.name}'", style="bold")
    except Exception as e:
        console.print(f"[red]✗[/red] Error: {e}", style="bold")
        sys.exit(1)


@duplicate.command("analyze")
@click.argument("tag_name")
@click.option("--db", type=click.Path(), help="Database path")
def duplicate_analyze(tag_name, db):
    """Analyze tag structure and capabilities."""
    try:
        db_path = Path(db) if db else None
        storage_inst = RFIDStorage(db_path)
        
        tag = storage_inst.get_by_name(tag_name)
        if not tag:
            console.print(f"[red]✗[/red] Tag not found: {tag_name}", style="bold")
            sys.exit(1)
        
        analysis = RFIDDuplicator.analyze_tag(tag)
        
        panel_content = f"""[bold cyan]Tag Type:[/bold cyan] {analysis['tag_type']}
[bold cyan]Frequency:[/bold cyan] {analysis['frequency']} ({analysis['frequency_band']})
[bold cyan]Data Length:[/bold cyan] {analysis['data_length']} bytes
[bold cyan]Writable:[/bold cyan] {'Yes' if analysis['writable'] else 'No'}
[bold cyan]Cloneable:[/bold cyan] {'Yes' if analysis['cloneable'] else 'No'}

[bold cyan]Security Features:[/bold cyan]"""
        
        for feature in analysis['security_features']:
            panel_content += f"\n  • {feature}"
        
        console.print(Panel(panel_content, title=f"Analysis: {tag_name}", border_style="yellow"))
    except Exception as e:
        console.print(f"[red]✗[/red] Error: {e}", style="bold")
        sys.exit(1)


# Transmission Commands
@main.group()
def transmit():
    """Transmit tags to Flipper Zero."""
    pass


@transmit.command("send")
@click.argument("tag_name")
@click.option("--port", help="Serial port (auto-detect if not specified)")
@click.option("--mode", type=click.Choice(["emulate", "write", "save"]), 
              default="emulate", help="Transmission mode")
@click.option("--db", type=click.Path(), help="Database path")
def transmit_send(tag_name, port, mode, db):
    """Send tag to Flipper Zero."""
    try:
        db_path = Path(db) if db else None
        storage_inst = RFIDStorage(db_path)
        
        tag = storage_inst.get_by_name(tag_name)
        if not tag:
            console.print(f"[red]✗[/red] Tag not found: {tag_name}", style="bold")
            sys.exit(1)
        
        with console.status(f"[bold cyan]Connecting to Flipper Zero..."):
            transmitter = FlipperTransmitter(port=port)
            transmitter.connect()
        
        console.print(f"[green]✓[/green] Connected to Flipper Zero", style="bold")
        
        with console.status(f"[bold cyan]Transmitting tag in {mode} mode..."):
            result = transmitter.transmit_tag(tag, mode)
        
        if result["success"]:
            console.print(f"[green]✓[/green] Tag transmitted successfully", style="bold")
        else:
            console.print(f"[yellow]![/yellow] Transmission completed with warnings", style="bold")
        
        console.print(f"[dim]Response: {result.get('response', 'N/A')}[/dim]")
        
        transmitter.disconnect()
    except Exception as e:
        console.print(f"[red]✗[/red] Error: {e}", style="bold")
        sys.exit(1)


@transmit.command("read")
@click.option("--port", help="Serial port (auto-detect if not specified)")
@click.option("--timeout", type=int, default=10, help="Read timeout in seconds")
@click.option("--save", is_flag=True, help="Save read tag to storage")
@click.option("--db", type=click.Path(), help="Database path")
def transmit_read(port, timeout, save, db):
    """Read tag from Flipper Zero."""
    try:
        with console.status(f"[bold cyan]Connecting to Flipper Zero..."):
            transmitter = FlipperTransmitter(port=port)
            transmitter.connect()
        
        console.print(f"[green]✓[/green] Connected to Flipper Zero", style="bold")
        console.print(f"[cyan]Waiting for tag (timeout: {timeout}s)...[/cyan]")
        
        tag = transmitter.read_tag(timeout)
        
        if tag:
            console.print(f"[green]✓[/green] Tag read successfully", style="bold")
            console.print(f"  UID: {tag.uid}")
            console.print(f"  Type: {tag.tag_type.value}")
            console.print(f"  Data: {tag.data}")
            
            if save:
                db_path = Path(db) if db else None
                storage_inst = RFIDStorage(db_path)
                storage_inst.save(tag)
                console.print(f"[green]✓[/green] Tag saved to storage", style="bold")
        else:
            console.print(f"[yellow]![/yellow] No tag detected within timeout", style="bold")
        
        transmitter.disconnect()
    except Exception as e:
        console.print(f"[red]✗[/red] Error: {e}", style="bold")
        sys.exit(1)


@transmit.command("status")
@click.option("--port", help="Serial port (auto-detect if not specified)")
def transmit_status(port):
    """Check Flipper Zero connection status."""
    try:
        transmitter = FlipperTransmitter(port=port)
        transmitter.connect()
        
        status = transmitter.get_status()
        
        panel_content = f"""[bold cyan]Connected:[/bold cyan] {'Yes' if status['connected'] else 'No'}
[bold cyan]Port:[/bold cyan] {status['port'] or 'N/A'}
[bold cyan]Serial Open:[/bold cyan] {'Yes' if status['serial_open'] else 'No'}
[bold cyan]Device Info:[/bold cyan] {status['device_info']}"""
        
        console.print(Panel(panel_content, title="Flipper Zero Status", border_style="green"))
        
        transmitter.disconnect()
    except Exception as e:
        console.print(f"[red]✗[/red] Error: {e}", style="bold")
        sys.exit(1)


if __name__ == "__main__":
    main()
