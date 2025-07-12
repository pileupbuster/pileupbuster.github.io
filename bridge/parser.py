"""UDP packet parsing for various amateur radio logging formats"""
import re
import struct
import logging
from typing import Optional, Dict, Any
from datetime import datetime


logger = logging.getLogger(__name__)


class PacketParser:
    """Parse UDP packets from amateur radio logging software"""
    
    def __init__(self):
        # Regex patterns for different packet formats
        self.callsign_pattern = re.compile(r'\b[A-Z0-9]{1,3}[0-9][A-Z0-9]{0,3}[A-Z]\b')
        self.adif_callsign_pattern = re.compile(r'<call:(\d+)>([A-Z0-9/]+)', re.IGNORECASE)
        self.frequency_pattern = re.compile(r'<freq:(\d+)>([0-9.]+)', re.IGNORECASE)
        self.mode_pattern = re.compile(r'<mode:(\d+)>([A-Z0-9]+)', re.IGNORECASE)
    
    def parse_packet(self, data: bytes, source_addr: tuple) -> Optional[Dict[str, Any]]:
        """
        Parse a UDP packet and extract QSO information
        
        Args:
            data: Raw UDP packet data
            source_addr: (host, port) tuple of packet source
            
        Returns:
            Dictionary with QSO data or None if parsing failed
        """
        try:
            # Try different parsing methods
            result = None
            
            # Method 1: Try WSJT-X binary format
            result = self._parse_wsjtx_binary(data)
            if result:
                logger.info(f"Parsed WSJT-X binary packet from {source_addr}: {result}")
                return result
            
            # Method 2: Try ADIF text format
            try:
                text_data = data.decode('utf-8', errors='ignore')
                result = self._parse_adif_text(text_data)
                if result:
                    logger.info(f"Parsed ADIF text packet from {source_addr}: {result}")
                    return result
            except UnicodeDecodeError:
                pass
            
            # Method 3: Try plain text callsign
            try:
                text_data = data.decode('utf-8', errors='ignore')
                result = self._parse_plain_text(text_data)
                if result:
                    logger.info(f"Parsed plain text packet from {source_addr}: {result}")
                    return result
            except UnicodeDecodeError:
                pass
            
            # Method 4: Try Latin-1 encoding (some logging software uses this)
            try:
                text_data = data.decode('latin-1')
                result = self._parse_adif_text(text_data)
                if result:
                    logger.info(f"Parsed Latin-1 ADIF packet from {source_addr}: {result}")
                    return result
            except UnicodeDecodeError:
                pass
            
            logger.warning(f"Could not parse packet from {source_addr}: {data[:50]}...")
            return None
            
        except Exception as e:
            logger.error(f"Error parsing packet from {source_addr}: {e}")
            return None
    
    def _parse_wsjtx_binary(self, data: bytes) -> Optional[Dict[str, Any]]:
        """Parse WSJT-X binary UDP packet format"""
        try:
            if len(data) < 12:
                return None
            
            # Check for WSJT-X magic number
            magic = struct.unpack('>I', data[0:4])[0]
            if magic != 0xADBCCBDA:
                return None
            
            # Extract schema version and packet type
            schema = struct.unpack('>I', data[4:8])[0]
            packet_type = struct.unpack('>I', data[8:12])[0]
            
            logger.debug(f"WSJT-X packet: magic={hex(magic)}, schema={schema}, type={packet_type}")
            
            # For now, just extract the text portion which contains ADIF
            try:
                # Look for ADIF data in the packet
                text_portion = data[12:].decode('utf-8', errors='ignore')
                return self._parse_adif_text(text_portion)
            except:
                return None
                
        except struct.error:
            return None
    
    def _parse_adif_text(self, text: str) -> Optional[Dict[str, Any]]:
        """Parse ADIF format text"""
        if not text:
            return None
        
        # Extract callsign
        callsign_match = self.adif_callsign_pattern.search(text)
        if not callsign_match:
            return None
        
        callsign = callsign_match.group(2).upper().strip()
        
        # Validate callsign format
        if not self._is_valid_callsign(callsign):
            return None
        
        result = {
            "callsign": callsign,
            "timestamp": datetime.utcnow().isoformat(),
            "source": "adif"
        }
        
        # Extract frequency if present
        freq_match = self.frequency_pattern.search(text)
        if freq_match:
            try:
                frequency = float(freq_match.group(2))
                result["frequency_mhz"] = frequency
            except ValueError:
                pass
        
        # Extract mode if present
        mode_match = self.mode_pattern.search(text)
        if mode_match:
            result["mode"] = mode_match.group(2).upper()
        
        return result
    
    def _parse_plain_text(self, text: str) -> Optional[Dict[str, Any]]:
        """Parse plain text for callsign"""
        text = text.strip().upper()
        
        # Look for callsign patterns
        callsign_matches = self.callsign_pattern.findall(text)
        
        for callsign in callsign_matches:
            if self._is_valid_callsign(callsign):
                return {
                    "callsign": callsign,
                    "timestamp": datetime.utcnow().isoformat(),
                    "source": "plain_text"
                }
        
        return None
    
    def _is_valid_callsign(self, callsign: str) -> bool:
        """
        Validate amateur radio callsign format
        
        Basic validation - should contain:
        - 1-3 letters (prefix)
        - 1 digit
        - 1-3 letters/numbers (suffix)
        """
        if not callsign or len(callsign) < 3 or len(callsign) > 10:
            return False
        
        # Check for at least one digit
        if not any(c.isdigit() for c in callsign):
            return False
        
        # Check for at least one letter
        if not any(c.isalpha() for c in callsign):
            return False
        
        # Check for valid characters only
        if not all(c.isalnum() or c == '/' for c in callsign):
            return False
        
        # Exclude common false positives
        false_positives = {
            'TEST', 'DEMO', 'EXAMPLE', 'SAMPLE',
            'QSO', 'LOG', 'ADIF', 'WSJT', 'FT8', 'FT4'
        }
        
        if callsign in false_positives:
            return False
        
        return True
