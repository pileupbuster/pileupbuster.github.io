#!/usr/bin/env python3
"""
Interactive QSO Testing Script
=============================

This script sends multiple QSO requests to test the Pileup Buster integration
with manual pauses between each one for human verification.

Usage: python interactive_qso_test.py
"""

import requests
import json
import time
from datetime import datetime
from typing import Dict, Any
import sys

class InteractiveQSOTester:
    def __init__(self, backend_url: str = "http://localhost:8000"):
        self.backend_url = backend_url
        self.logging_endpoint = f"{backend_url}/api/admin/qso/logging-direct"
        self.current_qso_endpoint = f"{backend_url}/api/queue/current"
        
        # Test QSO data - mix of frequencies, modes, and callsigns
        self.test_qsos = [
            {
                "callsign": "VK3ABC",
                "frequency_mhz": 14.205,
                "mode": "SSB",
                "description": "Australian station on 20m SSB"
            },
            {
                "callsign": "JA1XYZ", 
                "frequency_mhz": 21.150,
                "mode": "CW",
                "description": "Japanese station on 15m CW"
            },
            {
                "callsign": "G0DEF",
                "frequency_mhz": 7.074,
                "mode": "FT8",
                "description": "UK station on 40m FT8"
            },
            {
                "callsign": "W1AW",
                "frequency_mhz": 28.400,
                "mode": "SSB",
                "description": "ARRL station on 10m SSB"
            },
            {
                "callsign": "LU8GHI",
                "frequency_mhz": 3.573,
                "mode": "FT4",
                "description": "Argentina station on 80m FT4"
            }
        ]
    
    def print_banner(self):
        """Print script banner"""
        print("=" * 70)
        print("🧪 INTERACTIVE QSO TESTING SCRIPT")
        print("=" * 70)
        print("This script will send 5 test QSOs to Pileup Buster with")
        print("manual pauses between each one for verification.")
        print()
        print(f"🌐 Backend URL: {self.backend_url}")
        print(f"📡 Endpoint: {self.logging_endpoint}")
        print("=" * 70)
        print()
    
    def check_backend_connection(self) -> bool:
        """Verify backend is running"""
        try:
            response = requests.get(f"{self.backend_url}/api/queue/status", timeout=5)
            if response.status_code == 200:
                print("✅ Backend connection successful")
                return True
            else:
                print(f"❌ Backend returned status {response.status_code}")
                return False
        except requests.exceptions.RequestException as e:
            print(f"❌ Cannot connect to backend: {e}")
            return False
    
    def get_current_qso(self) -> Dict[str, Any]:
        """Get current QSO information"""
        try:
            response = requests.get(self.current_qso_endpoint, timeout=5)
            if response.status_code == 200:
                return response.json()
            elif response.status_code == 404:
                return {}  # No current QSO
            else:
                print(f"⚠️  Warning: Current QSO endpoint returned {response.status_code}")
                return {}
        except requests.exceptions.RequestException as e:
            print(f"⚠️  Warning: Could not get current QSO: {e}")
            return {}
    
    def send_qso(self, qso_data: Dict[str, Any]) -> bool:
        """Send a QSO to the backend"""
        message = {
            "type": "qso_start",
            "data": {
                "callsign": qso_data["callsign"],
                "frequency_mhz": qso_data["frequency_mhz"],
                "mode": qso_data["mode"],
                "source": "pblog_native",
                "timestamp": datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S.%fZ'),
                "triggered_by": "callsign_finalized"
            }
        }
        
        try:
            print(f"📤 Sending QSO: {qso_data['callsign']} on {qso_data['frequency_mhz']} MHz ({qso_data['mode']})")
            
            response = requests.post(
                self.logging_endpoint,
                json=message,
                headers={"Content-Type": "application/json"},
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                print(f"✅ SUCCESS: QSO started for {qso_data['callsign']}")
                
                # Show response details
                qso_started = result.get('qso_started', {})
                print(f"   📻 Source: {qso_started.get('source', 'unknown')}")
                print(f"   📋 Was in queue: {qso_started.get('was_in_queue', False)}")
                print(f"   🔊 Frequency: {qso_started.get('frequency_mhz', 'unknown')} MHz")
                print(f"   📡 Mode: {qso_started.get('mode', 'unknown')}")
                
                return True
            else:
                print(f"❌ ERROR: HTTP {response.status_code}")
                print(f"   Response: {response.text}")
                return False
                
        except requests.exceptions.RequestException as e:
            print(f"❌ NETWORK ERROR: {e}")
            return False
    
    def show_current_qso_status(self):
        """Display current QSO status"""
        current = self.get_current_qso()
        
        if not current:
            print("📭 No current QSO active")
            return
        
        print("📊 CURRENT QSO STATUS:")
        print(f"   📻 Callsign: {current.get('callsign', 'unknown')}")
        
        qrz = current.get('qrz', {})
        if qrz.get('name'):
            print(f"   👤 Name: {qrz['name']}")
        if qrz.get('dxcc_name'):
            print(f"   🌍 Location: {qrz['dxcc_name']}")
        
        metadata = current.get('metadata', {})
        if metadata:
            print("   📋 Metadata:")
            if metadata.get('frequency_mhz'):
                print(f"      🔊 Frequency: {metadata['frequency_mhz']} MHz")
            if metadata.get('mode'):
                print(f"      📡 Mode: {metadata['mode']}")
            if metadata.get('source'):
                print(f"      📥 Source: {metadata['source']}")
            if metadata.get('started_via'):
                print(f"      🚀 Started via: {metadata['started_via']}")
    
    def wait_for_user(self, test_number: int, total_tests: int):
        """Wait for user input before continuing"""
        print()
        print("=" * 50)
        if test_number < total_tests:
            print(f"🔄 TEST {test_number}/{total_tests} COMPLETED")
            print()
            print("👀 Please check the Pileup Buster frontend to verify:")
            print("   • Current callsign is displayed correctly")
            print("   • Frequency and mode are shown")
            print("   • QRZ information is loaded (if available)")
            print("   • Source indicator shows correct status")
            print()
            print("Press ENTER to continue to next test (or Ctrl+C to stop)...")
        else:
            print(f"🏁 ALL {total_tests} TESTS COMPLETED!")
            print()
            print("👀 Final verification checklist:")
            print("   • All QSOs processed correctly")
            print("   • Frequency/mode data displayed properly")
            print("   • No errors in backend logs")
            print("   • Frontend updates in real-time")
            print()
            print("Press ENTER to finish...")
        
        try:
            input()
        except KeyboardInterrupt:
            print()
            print("🛑 Testing stopped by user")
            sys.exit(0)
        
        print("=" * 50)
        print()
    
    def run_interactive_test(self):
        """Run the interactive test sequence"""
        self.print_banner()
        
        # Check backend connection
        if not self.check_backend_connection():
            print("❌ Cannot proceed without backend connection")
            return
        
        print()
        print("🔍 Checking initial state...")
        self.show_current_qso_status()
        print()
        
        print("📋 TEST SEQUENCE:")
        for i, qso in enumerate(self.test_qsos, 1):
            print(f"   {i}. {qso['callsign']} - {qso['description']}")
        print()
        
        print("Ready to start testing?")
        print("Press ENTER to begin (or Ctrl+C to cancel)...")
        try:
            input()
        except KeyboardInterrupt:
            print("\n🛑 Testing cancelled")
            return
        
        # Run each test
        total_tests = len(self.test_qsos)
        successful_tests = 0
        
        for i, qso_data in enumerate(self.test_qsos, 1):
            print()
            print(f"🧪 TEST {i}/{total_tests}: {qso_data['description']}")
            print("-" * 50)
            
            # Send the QSO
            if self.send_qso(qso_data):
                successful_tests += 1
                print()
                print("⏱️  Waiting 2 seconds for processing...")
                time.sleep(2)
                
                # Show current status
                self.show_current_qso_status()
            else:
                print("💥 Test failed - check backend logs")
            
            # Wait for user verification
            self.wait_for_user(i, total_tests)
        
        # Final summary
        print()
        print("=" * 70)
        print("📊 TEST SUMMARY")
        print("=" * 70)
        print(f"✅ Successful tests: {successful_tests}/{total_tests}")
        print(f"❌ Failed tests: {total_tests - successful_tests}/{total_tests}")
        
        if successful_tests == total_tests:
            print("🎉 ALL TESTS PASSED! QSO integration is working correctly.")
        else:
            print("⚠️  Some tests failed. Check backend logs for errors.")
        
        print("=" * 70)

def main():
    """Main entry point"""
    tester = InteractiveQSOTester()
    tester.run_interactive_test()

if __name__ == "__main__":
    main()
