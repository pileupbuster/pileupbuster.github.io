"""Test script for QLog Bridge"""
import socket
import time
import asyncio
import websockets
import json


def test_udp_sender():
    """Send test UDP packets to the bridge"""
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    
    test_packets = [
        # ADIF format
        b'<call:5>W1ABC <qso_date:8>20250711 <time_on:6>154500 <mode:3>SSB <eor>',
        # Plain text
        b'EI6JGB',
        # ADIF with frequency
        b'<call:6>VK1DEF <freq:8>14.31500 <mode:3>USB <eor>',
    ]
    
    print("Sending test UDP packets to bridge...")
    
    for i, packet in enumerate(test_packets, 1):
        print(f"Sending packet {i}: {packet}")
        sock.sendto(packet, ('127.0.0.1', 2238))
        time.sleep(2)
    
    sock.close()
    print("Test packets sent")


async def test_websocket_client():
    """Test WebSocket client to receive bridge data"""
    try:
        print("Connecting to WebSocket...")
        async with websockets.connect('ws://127.0.0.1:8765') as websocket:
            print("Connected to bridge WebSocket")
            
            # Send ping
            await websocket.send(json.dumps({"type": "ping"}))
            
            # Listen for messages
            timeout_count = 0
            while timeout_count < 10:  # Wait up to 10 seconds
                try:
                    message = await asyncio.wait_for(websocket.recv(), timeout=1.0)
                    data = json.loads(message)
                    print(f"Received: {data}")
                    
                    if data.get('type') == 'qso_start':
                        print(f"🎉 QSO received: {data['data']['callsign']}")
                        
                except asyncio.TimeoutError:
                    timeout_count += 1
                    print(f"Waiting for messages... ({timeout_count}/10)")
                    
    except ConnectionRefusedError:
        print("❌ Could not connect to WebSocket. Is the bridge running?")
    except Exception as e:
        print(f"❌ WebSocket error: {e}")


async def main():
    """Main test function"""
    print("QLog Bridge Test")
    print("================")
    print()
    print("This test will:")
    print("1. Start a WebSocket client to listen for bridge data")
    print("2. Send test UDP packets to the bridge")
    print("3. Verify the bridge forwards the data correctly")
    print()
    
    # Start WebSocket client in background
    websocket_task = asyncio.create_task(test_websocket_client())
    
    # Wait a moment for connection
    await asyncio.sleep(1)
    
    # Send UDP packets in background
    loop = asyncio.get_event_loop()
    await loop.run_in_executor(None, test_udp_sender)
    
    # Wait for WebSocket client to finish
    await websocket_task
    
    print("\nTest completed!")


if __name__ == "__main__":
    print("QLog Bridge Tester")
    print("Make sure the bridge is running before starting this test.")
    print("Run: python -m bridge.main")
    print()
    input("Press Enter when bridge is running...")
    
    asyncio.run(main())
