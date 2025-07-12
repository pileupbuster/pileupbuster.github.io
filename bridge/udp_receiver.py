"""UDP receiver for QLog bridge"""
import socket
import threading
import logging
from typing import Callable, Optional, Dict, Any
from config import BridgeConfig
from parser import PacketParser


logger = logging.getLogger(__name__)


class UDPReceiver:
    """UDP packet receiver for amateur radio logging software"""
    
    def __init__(self, config: BridgeConfig, on_qso_callback: Callable[[Dict[str, Any]], None]):
        """
        Initialize UDP receiver
        
        Args:
            config: Bridge configuration
            on_qso_callback: Function to call when valid QSO data received
        """
        self.config = config
        self.on_qso_callback = on_qso_callback
        self.parser = PacketParser()
        
        self.socket: Optional[socket.socket] = None
        self.thread: Optional[threading.Thread] = None
        self.running = False
        
    def start(self) -> bool:
        """
        Start UDP receiver
        
        Returns:
            True if started successfully, False otherwise
        """
        if self.running:
            logger.warning("UDP receiver already running")
            return True
        
        try:
            # Create UDP socket
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            
            # Bind to configured port
            self.socket.bind(('127.0.0.1', self.config.udp_port))
            
            # Start receiver thread
            self.running = True
            self.thread = threading.Thread(target=self._receive_loop, daemon=True)
            self.thread.start()
            
            logger.info(f"UDP receiver started on port {self.config.udp_port}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to start UDP receiver: {e}")
            self.stop()
            return False
    
    def stop(self) -> None:
        """Stop UDP receiver"""
        self.running = False
        
        if self.socket:
            try:
                self.socket.close()
            except:
                pass
            self.socket = None
        
        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=1.0)
        
        logger.info("UDP receiver stopped")
    
    def _receive_loop(self) -> None:
        """Main UDP receiver loop"""
        logger.info("UDP receiver loop started")
        
        while self.running and self.socket:
            try:
                # Receive data with timeout
                self.socket.settimeout(1.0)
                data, addr = self.socket.recvfrom(self.config.buffer_size)
                
                if not self.running:
                    break
                
                logger.debug(f"Received {len(data)} bytes from {addr}")
                
                # Parse the packet
                qso_data = self.parser.parse_packet(data, addr)
                
                if qso_data:
                    logger.info(f"Valid QSO data parsed: {qso_data}")
                    
                    # Call the callback with parsed data
                    try:
                        self.on_qso_callback(qso_data)
                    except Exception as e:
                        logger.error(f"Error in QSO callback: {e}")
                else:
                    logger.debug(f"Could not parse packet from {addr}")
                    
            except socket.timeout:
                # Normal timeout, continue loop
                continue
            except socket.error as e:
                if self.running:  # Only log if we're supposed to be running
                    logger.error(f"Socket error in UDP receiver: {e}")
                break
            except Exception as e:
                logger.error(f"Unexpected error in UDP receiver: {e}")
                break
        
        logger.info("UDP receiver loop ended")
    
    def is_running(self) -> bool:
        """Check if UDP receiver is running"""
        return self.running and self.socket is not None
    
    def get_status(self) -> Dict[str, Any]:
        """Get receiver status information"""
        return {
            "running": self.is_running(),
            "port": self.config.udp_port,
            "thread_alive": self.thread.is_alive() if self.thread else False
        }
