#!/usr/bin/env python3
"""
Test script to simulate your logging software sending HTTP POST requests
Use this to test the new HTTP integration before configuring your actual logging software
"""
import requests
import json
from datetime import datetime
import sys

def send_qso_start(callsign, frequency_mhz=None, mode=None, backend_url="http://localhost:8000"):
    """Send a QSO start message via HTTP POST"""
    
    # Create the message in the same format your logging software sends
    message = {
        "type": "qso_start",
        "data": {
            "callsign": callsign,
            "frequency_mhz": frequency_mhz,
            "mode": mode,
            "source": "pblog_native",
            "timestamp": datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S.%fZ'),
            "triggered_by": "callsign_finalized"
        }
    }
    
    url = f"{backend_url}/api/admin/qso/logging-direct"
    
    print(f"📤 Sending QSO start for {callsign}...")
    print(f"🌐 URL: {url}")
    print(f"📋 Message: {json.dumps(message, indent=2)}")
    print()
    
    try:
        response = requests.post(
            url,
            json=message,
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        
        print(f"📡 Response Status: {response.status_code}")
        print(f"📡 Response Headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ SUCCESS! QSO started successfully")
            print(f"📋 Response: {json.dumps(result, indent=2)}")
            
            qso_info = result.get('qso_started', {})
            print(f"\n🎉 QSO Details:")
            print(f"   Callsign: {qso_info.get('callsign')}")
            print(f"   Source: {qso_info.get('source')}")
            print(f"   Was in queue: {qso_info.get('was_in_queue')}")
            print(f"   Frequency: {qso_info.get('frequency_mhz')} MHz")
            print(f"   Mode: {qso_info.get('mode')}")
            
        else:
            print(f"❌ ERROR: {response.status_code}")
            try:
                error_detail = response.json()
                print(f"📋 Error Details: {json.dumps(error_detail, indent=2)}")
            except:
                print(f"📋 Error Text: {response.text}")
                
    except requests.exceptions.ConnectionError:
        print(f"❌ CONNECTION ERROR: Could not connect to {url}")
        print(f"💡 Make sure your backend is running on {backend_url}")
    except requests.exceptions.Timeout:
        print(f"❌ TIMEOUT ERROR: Request took too long")
    except Exception as e:
        print(f"❌ UNEXPECTED ERROR: {e}")

def main():
    """Main function to handle command line arguments"""
    if len(sys.argv) < 2:
        print("Usage: python test_http_logging.py <CALLSIGN> [FREQUENCY_MHZ] [MODE] [BACKEND_URL]")
        print()
        print("Examples:")
        print("  python test_http_logging.py EI6LF")
        print("  python test_http_logging.py EI6LF 14.2715 SSB")
        print("  python test_http_logging.py EI6LF 14.2715 SSB http://localhost:8000")
        print()
        sys.exit(1)
    
    callsign = sys.argv[1]
    frequency_mhz = float(sys.argv[2]) if len(sys.argv) > 2 and sys.argv[2] else None
    mode = sys.argv[3] if len(sys.argv) > 3 else None
    backend_url = sys.argv[4] if len(sys.argv) > 4 else "http://localhost:8000"
    
    print(f"🧪 Testing HTTP POST integration")
    print(f"📻 Callsign: {callsign}")
    print(f"🔊 Frequency: {frequency_mhz} MHz" if frequency_mhz else "🔊 Frequency: Not specified")
    print(f"📡 Mode: {mode}" if mode else "📡 Mode: Not specified")
    print(f"🌐 Backend: {backend_url}")
    print("-" * 50)
    
    send_qso_start(callsign, frequency_mhz, mode, backend_url)

if __name__ == "__main__":
    main()
