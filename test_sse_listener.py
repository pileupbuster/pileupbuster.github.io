#!/usr/bin/env python3
"""
Simple SSE listener to test if QSO completion events are being sent
"""

import requests
import json
import time

def listen_for_sse_events():
    """Listen for SSE events from the backend"""
    print("🎧 Starting SSE listener...")
    print("📡 Connecting to: http://localhost:8000/api/events/stream")
    
    try:
        # Connect to SSE stream
        response = requests.get(
            "http://localhost:8000/api/events/stream",
            headers={"Accept": "text/event-stream", "Cache-Control": "no-cache"},
            stream=True,
            timeout=None
        )
        
        if response.status_code != 200:
            print(f"❌ Failed to connect to SSE: {response.status_code}")
            print(f"   Response: {response.text}")
            return
            
        print("✅ Connected to SSE stream!")
        print("⏳ Listening for events... (Ctrl+C to stop)")
        print("-" * 60)
        
        # Process the stream
        for line in response.iter_lines(decode_unicode=True):
            if line:
                print(f"📨 Received: {line}")
                
                # Parse event data
                if line.startswith("event:"):
                    event_type = line.replace("event:", "").strip()
                    print(f"🎪 Event Type: {event_type}")
                elif line.startswith("data:"):
                    event_data = line.replace("data:", "").strip()
                    try:
                        data_json = json.loads(event_data)
                        print(f"📦 Event Data: {json.dumps(data_json, indent=2)}")
                        
                        # Check for QSO completion events
                        if event_type == "qso_completed":
                            print("🎉 QSO COMPLETION EVENT DETECTED!")
                            print(f"   Message: {data_json.get('message', 'No message')}")
                    except json.JSONDecodeError:
                        print(f"📦 Event Data (raw): {event_data}")
                
    except KeyboardInterrupt:
        print("\n🛑 SSE listener stopped by user")
    except Exception as e:
        print(f"❌ SSE listener error: {e}")

if __name__ == "__main__":
    listen_for_sse_events()
