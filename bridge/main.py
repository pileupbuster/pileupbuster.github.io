"""Main QLog Bridge application"""
import asyncio
import logging
import signal
import sys
import threading
from pathlib import Path
from typing import Dict, Any

from config import BridgeConfig
from udp_receiver import UDPReceiver
from websocket_server import WebSocketServer


class QLogBridge:
    """Main QLog Bridge application"""
    
    def __init__(self, config_path: str = None):
        """
        Initialize QLog Bridge
        
        Args:
            config_path: Path to configuration file
        """
        self.config = BridgeConfig(config_path)
        self.udp_receiver: UDPReceiver = None
        self.websocket_server: WebSocketServer = None
        self.loop: asyncio.AbstractEventLoop = None
        self.running = False
        
        # Setup logging
        self._setup_logging()
        
        self.logger = logging.getLogger(__name__)
        self.logger.info("QLog Bridge initialized")
    
    def _setup_logging(self) -> None:
        """Setup logging configuration"""
        level = getattr(logging, self.config.log_level.upper(), logging.INFO)
        
        logging.basicConfig(
            level=level,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.StreamHandler(sys.stdout),
                logging.FileHandler('qlog_bridge.log')
            ]
        )
    
    def _on_qso_received(self, qso_data: Dict[str, Any]) -> None:
        """
        Callback for when QSO data is received via UDP
        
        Args:
            qso_data: Parsed QSO information
        """
        self.logger.info(f"QSO received: {qso_data}")
        
        # Schedule broadcast to WebSocket clients
        if self.websocket_server and self.loop:
            asyncio.run_coroutine_threadsafe(
                self.websocket_server.broadcast_qso(qso_data),
                self.loop
            )
    
    async def start(self) -> bool:
        """
        Start the bridge application
        
        Returns:
            True if started successfully, False otherwise
        """
        if self.running:
            self.logger.warning("Bridge already running")
            return True
        
        self.logger.info("Starting QLog Bridge...")
        
        try:
            # Get current event loop
            self.loop = asyncio.get_running_loop()
            
            # Start WebSocket server
            self.websocket_server = WebSocketServer(self.config)
            if not await self.websocket_server.start():
                self.logger.error("Failed to start WebSocket server")
                return False
            
            # Start UDP receiver
            self.udp_receiver = UDPReceiver(self.config, self._on_qso_received)
            if not self.udp_receiver.start():
                self.logger.error("Failed to start UDP receiver")
                await self.websocket_server.stop()
                return False
            
            self.running = True
            self.logger.info("QLog Bridge started successfully")
            self.logger.info(f"UDP listening on port {self.config.udp_port}")
            self.logger.info(f"WebSocket server on port {self.config.websocket_port}")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error starting bridge: {e}")
            await self.stop()
            return False
    
    async def stop(self) -> None:
        """Stop the bridge application"""
        if not self.running:
            return
        
        self.logger.info("Stopping QLog Bridge...")
        self.running = False
        
        # Stop UDP receiver
        if self.udp_receiver:
            self.udp_receiver.stop()
            self.udp_receiver = None
        
        # Stop WebSocket server
        if self.websocket_server:
            await self.websocket_server.stop()
            self.websocket_server = None
        
        self.logger.info("QLog Bridge stopped")
    
    def get_status(self) -> Dict[str, Any]:
        """Get bridge status information"""
        status = {
            "running": self.running,
            "config": {
                "udp_port": self.config.udp_port,
                "websocket_port": self.config.websocket_port,
                "log_level": self.config.log_level
            }
        }
        
        if self.udp_receiver:
            status["udp_receiver"] = self.udp_receiver.get_status()
        
        if self.websocket_server:
            status["websocket_server"] = self.websocket_server.get_status()
        
        return status
    
    async def run_forever(self) -> None:
        """Run the bridge until interrupted"""
        if not await self.start():
            self.logger.error("Failed to start bridge")
            return
        
        self.logger.info("Bridge running. Press Ctrl+C to stop.")
        
        try:
            # Setup signal handlers
            def signal_handler(signum, frame):
                self.logger.info(f"Received signal {signum}, stopping bridge...")
                asyncio.create_task(self.stop())
            
            signal.signal(signal.SIGINT, signal_handler)
            signal.signal(signal.SIGTERM, signal_handler)
            
            # Run until stopped
            while self.running:
                await asyncio.sleep(1)
                
        except KeyboardInterrupt:
            self.logger.info("Keyboard interrupt received")
        except Exception as e:
            self.logger.error(f"Unexpected error: {e}")
        finally:
            await self.stop()


async def main():
    """Main entry point"""
    bridge = QLogBridge()
    await bridge.run_forever()


if __name__ == "__main__":
    asyncio.run(main())
