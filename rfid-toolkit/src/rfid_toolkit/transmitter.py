"""
Flipper Zero communication and tag transmission.
"""

import time
from typing import Optional, Callable, Dict, Any
from pathlib import Path
import serial
import serial.tools.list_ports

from rfid_toolkit.models import RFIDTag


class FlipperTransmitter:
    """
    Professional transmission system for Flipper Zero communication.
    
    Handles serial communication with Flipper Zero device for tag
    transmission, reading, and emulation control.
    """

    # Flipper Zero serial communication settings
    BAUD_RATE = 115200
    TIMEOUT = 2.0
    
    # Command protocols
    CMD_PREFIX = "rfid"
    CMD_READ = "read"
    CMD_EMULATE = "emulate"
    CMD_WRITE = "write"
    CMD_STOP = "stop"

    def __init__(self, port: Optional[str] = None, auto_detect: bool = True):
        """
        Initialize Flipper Zero transmitter.
        
        Args:
            port: Serial port path (e.g., '/dev/ttyACM0' or 'COM3')
            auto_detect: If True and port is None, attempt to auto-detect Flipper
        """
        self.port = port
        self.serial_connection: Optional[serial.Serial] = None
        self._connected = False
        
        if auto_detect and port is None:
            self.port = self._auto_detect_flipper()

    def connect(self) -> bool:
        """
        Establish connection with Flipper Zero.
        
        Returns:
            True if connection successful, False otherwise
        """
        if self._connected:
            return True
        
        if not self.port:
            raise ValueError("No serial port specified and auto-detection failed")
        
        try:
            self.serial_connection = serial.Serial(
                port=self.port,
                baudrate=self.BAUD_RATE,
                timeout=self.TIMEOUT,
                write_timeout=self.TIMEOUT,
            )
            time.sleep(2)  # Wait for connection to stabilize
            self._connected = True
            return True
        except serial.SerialException as e:
            raise ConnectionError(f"Failed to connect to Flipper Zero: {e}")

    def disconnect(self) -> None:
        """Disconnect from Flipper Zero."""
        if self.serial_connection and self.serial_connection.is_open:
            self.serial_connection.close()
        self._connected = False

    def transmit_tag(self, tag: RFIDTag, mode: str = "emulate") -> Dict[str, Any]:
        """
        Transmit RFID tag to Flipper Zero.
        
        Args:
            tag: RFIDTag to transmit
            mode: Transmission mode ('emulate', 'write', or 'save')
            
        Returns:
            Dictionary with transmission results
        """
        if not self._connected:
            self.connect()
        
        if mode == "emulate":
            return self._emulate_tag(tag)
        elif mode == "write":
            return self._write_tag(tag)
        elif mode == "save":
            return self._save_tag_to_flipper(tag)
        else:
            raise ValueError(f"Unknown transmission mode: {mode}")

    def read_tag(self, timeout: int = 10) -> Optional[RFIDTag]:
        """
        Read RFID tag from Flipper Zero.
        
        Args:
            timeout: Maximum time to wait for tag (seconds)
            
        Returns:
            RFIDTag if read successfully, None otherwise
        """
        if not self._connected:
            self.connect()
        
        # Send read command
        self._send_command(f"{self.CMD_PREFIX} {self.CMD_READ}")
        
        start_time = time.time()
        while time.time() - start_time < timeout:
            response = self._read_response()
            if response and "uid" in response.lower():
                return self._parse_tag_response(response)
            time.sleep(0.5)
        
        return None

    def stop_emulation(self) -> bool:
        """
        Stop current tag emulation.
        
        Returns:
            True if stopped successfully, False otherwise
        """
        if not self._connected:
            return False
        
        self._send_command(f"{self.CMD_PREFIX} {self.CMD_STOP}")
        response = self._read_response()
        return "stopped" in response.lower() if response else False

    def get_status(self) -> Dict[str, Any]:
        """
        Get Flipper Zero device status.
        
        Returns:
            Dictionary with device status information
        """
        if not self._connected:
            self.connect()
        
        self._send_command("device_info")
        response = self._read_response()
        
        return {
            "connected": self._connected,
            "port": self.port,
            "device_info": response if response else "Unknown",
            "serial_open": self.serial_connection.is_open if self.serial_connection else False,
        }

    def list_saved_tags(self) -> list:
        """
        List tags saved on Flipper Zero.
        
        Returns:
            List of tag names saved on device
        """
        if not self._connected:
            self.connect()
        
        self._send_command("storage list /ext/rfid")
        response = self._read_response()
        
        if response:
            # Parse file list from response
            lines = response.split('\n')
            return [line.strip() for line in lines if line.strip().endswith('.rfid')]
        return []

    def _emulate_tag(self, tag: RFIDTag) -> Dict[str, Any]:
        """Emulate tag on Flipper Zero."""
        # Format emulation command with tag data
        command = f"{self.CMD_PREFIX} {self.CMD_EMULATE} {tag.tag_type.value} {tag.data}"
        self._send_command(command)
        
        response = self._read_response()
        success = "emulating" in response.lower() if response else False
        
        return {
            "success": success,
            "mode": "emulate",
            "tag_uid": tag.uid,
            "response": response,
        }

    def _write_tag(self, tag: RFIDTag) -> Dict[str, Any]:
        """Write tag data to a physical RFID card via Flipper."""
        command = f"{self.CMD_PREFIX} {self.CMD_WRITE} {tag.tag_type.value} {tag.data}"
        self._send_command(command)
        
        response = self._read_response()
        success = "success" in response.lower() if response else False
        
        return {
            "success": success,
            "mode": "write",
            "tag_uid": tag.uid,
            "response": response,
        }

    def _save_tag_to_flipper(self, tag: RFIDTag) -> Dict[str, Any]:
        """Save tag to Flipper Zero's internal storage."""
        # Convert to Flipper format
        flipper_data = tag.to_flipper_format()
        
        # Send save command
        filename = f"/ext/rfid/{tag.name}.rfid"
        self._send_command(f"storage write {filename}")
        
        # Send tag data
        if self.serial_connection:
            self.serial_connection.write(flipper_data.encode())
            self.serial_connection.write(b'\n')
        
        response = self._read_response()
        success = "success" in response.lower() if response else False
        
        return {
            "success": success,
            "mode": "save",
            "filename": filename,
            "response": response,
        }

    def _send_command(self, command: str) -> None:
        """Send command to Flipper Zero."""
        if not self.serial_connection or not self.serial_connection.is_open:
            raise ConnectionError("Not connected to Flipper Zero")
        
        self.serial_connection.write(f"{command}\r\n".encode())
        self.serial_connection.flush()

    def _read_response(self, timeout: Optional[float] = None) -> Optional[str]:
        """Read response from Flipper Zero."""
        if not self.serial_connection or not self.serial_connection.is_open:
            return None
        
        original_timeout = self.serial_connection.timeout
        if timeout:
            self.serial_connection.timeout = timeout
        
        try:
            response = self.serial_connection.read(1024).decode('utf-8', errors='ignore')
            return response.strip() if response else None
        finally:
            self.serial_connection.timeout = original_timeout

    def _parse_tag_response(self, response: str) -> Optional[RFIDTag]:
        """Parse tag data from Flipper response."""
        try:
            # Simple parsing - in real implementation, this would be more robust
            lines = response.split('\n')
            tag_data = {}
            
            for line in lines:
                if ':' in line:
                    key, value = line.split(':', 1)
                    tag_data[key.strip().lower()] = value.strip()
            
            if 'uid' in tag_data and 'data' in tag_data:
                return RFIDTag(
                    uid=tag_data['uid'],
                    data=tag_data['data'],
                    name=f"flipper_read_{int(time.time())}",
                    tag_type=tag_data.get('type', 'Unknown'),
                    frequency=int(tag_data.get('frequency', 125))
                )
        except Exception:
            pass
        
        return None

    def _auto_detect_flipper(self) -> Optional[str]:
        """
        Auto-detect Flipper Zero serial port.
        
        Returns:
            Serial port path if found, None otherwise
        """
        ports = serial.tools.list_ports.comports()
        
        # Look for Flipper Zero USB descriptors
        for port in ports:
            # Flipper Zero typically shows up as "Flipper" in description
            if port.description and "flipper" in port.description.lower():
                return port.device
            # Also check VID:PID (Flipper uses STM32 USB)
            if port.vid == 0x0483:  # STMicroelectronics VID
                return port.device
        
        return None

    def __enter__(self):
        """Context manager entry."""
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.disconnect()
