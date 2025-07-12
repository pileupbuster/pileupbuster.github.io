"""Logger Integration Service for WSJT-X UDP Protocol"""
import socket
import struct
import logging
from typing import Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class WSJTXUDPService:
    """Service for sending WSJT-X UDP protocol messages to logging software"""
    
    def __init__(self, host: str = "127.0.0.1", port: int = 2237):
        """
        Initialize WSJT-X UDP service
        
        Args:
            host: Target host for UDP packets (default: localhost)
            port: Target port for UDP packets (default: 2237, WSJT-X standard)
        """
        self.host = host
        self.port = port
        self.socket = None
        self.app_name = "PileupBuster"
        self.enabled = False
        
    def enable(self):
        """Enable the UDP service and create socket"""
        try:
            if self.socket:
                self.socket.close()
            
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.enabled = True
            logger.info(f"Logger integration enabled - sending to {self.host}:{self.port}")
            
        except Exception as e:
            logger.error(f"Failed to enable logger integration: {e}")
            self.enabled = False
            raise
    
    def disable(self):
        """Disable the UDP service and close socket"""
        try:
            if self.socket:
                self.socket.close()
                self.socket = None
            
            self.enabled = False
            logger.info("Logger integration disabled")
            
        except Exception as e:
            logger.error(f"Failed to disable logger integration: {e}")
    
    def _encode_string(self, text: str) -> bytes:
        """Encode a string for WSJT-X UDP protocol"""
        if text is None:
            text = ""
        text_bytes = text.encode('utf-8')
        return struct.pack('>I', len(text_bytes)) + text_bytes
    
    def _create_logged_adif_packet(self, callsign: str, frequency_hz: Optional[int] = None) -> bytes:
        """
        Create a 'Logged ADIF' UDP packet for WSJT-X protocol
        
        This tells the logging software that a QSO has started and should be logged.
        
        Args:
            callsign: The callsign being worked
            frequency_hz: Operating frequency in Hz (optional)
        """
        # WSJT-X packet structure:
        # - Magic number (4 bytes): 0xADBCCBDA
        # - Schema version (4 bytes): 2
        # - Packet type (4 bytes): 5 (Logged ADIF)
        # - Application name (string)
        # - ADIF text (string)
        
        magic = struct.pack('>I', 0xADBCCBDA)
        schema = struct.pack('>I', 2)
        packet_type = struct.pack('>I', 5)  # Logged ADIF
        
        app_name = self._encode_string(self.app_name)
        
        # Create minimal ADIF record
        current_time = datetime.utcnow()
        date_str = current_time.strftime("%Y%m%d")
        time_str = current_time.strftime("%H%M%S")
        
        adif_fields = [
            f"<call:{len(callsign)}>{callsign}",
            f"<qso_date:8>{date_str}",
            f"<time_on:6>{time_str}",
            "<mode:3>SSB",  # Default to SSB, could be made configurable
            "<rst_sent:2>59",  # Default signal report
            "<rst_rcvd:2>59"
        ]
        
        # Add frequency if provided
        if frequency_hz:
            freq_mhz = frequency_hz / 1_000_000
            freq_str = f"{freq_mhz:.6f}"
            adif_fields.append(f"<freq:{len(freq_str)}>{freq_str}")
        
        adif_fields.append("<eor>")  # End of record
        adif_text = " ".join(adif_fields)
        
        adif_data = self._encode_string(adif_text)
        
        return magic + schema + packet_type + app_name + adif_data
    
    def send_qso_started(self, callsign: str, frequency_hz: Optional[int] = None):
        """
        Send a UDP packet indicating a QSO has started
        
        Args:
            callsign: The callsign being worked
            frequency_hz: Operating frequency in Hz (optional)
        """
        if not self.enabled or not self.socket:
            logger.debug("Logger integration not enabled, skipping UDP send")
            return
        
        try:
            packet = self._create_logged_adif_packet(callsign, frequency_hz)
            self.socket.sendto(packet, (self.host, self.port))
            
            logger.info(f"Sent QSO start notification to logger: {callsign}")
            if frequency_hz:
                logger.debug(f"Frequency: {frequency_hz} Hz ({frequency_hz/1_000_000:.3f} MHz)")
            
        except Exception as e:
            logger.error(f"Failed to send QSO notification to logger: {e}")
    
    def update_settings(self, host: str = None, port: int = None):
        """Update connection settings (requires restart to take effect)"""
        if host:
            self.host = host
        if port:
            self.port = port
        
        logger.info(f"Logger integration settings updated: {self.host}:{self.port}")


# Global logger integration service instance
logger_service = WSJTXUDPService()
