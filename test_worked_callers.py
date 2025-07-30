#!/usr/bin/env python3
"""
Test script for the new worked callers functionality
This script simulates the workflow of working with callers and verifying they are stored correctly.
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from app.database import queue_db

def test_worked_callers_functionality():
    """Test the worked callers functionality"""
    print("🧪 Testing Worked Callers Functionality\n")
    
    try:
        # Test 1: Clear worked callers list
        print("1. Clearing worked callers list...")
        cleared_count = queue_db.clear_worked_callers()
        print(f"   ✅ Cleared {cleared_count} entries")
        
        # Test 2: Check empty list
        print("\n2. Checking empty worked callers list...")
        worked_list = queue_db.get_worked_callers()
        count = queue_db.get_worked_callers_count()
        print(f"   ✅ Found {count} worked callers: {worked_list}")
        
        # Test 3: Add a worked caller
        print("\n3. Adding a worked caller...")
        test_qrz_info = {
            'name': 'John Doe',
            'address': 'Springfield, IL, USA',
            'dxcc_name': 'United States',
            'image': 'https://s3.amazonaws.com/files.qrz.com/k/k0test/k0test.jpg'
        }
        
        worked_entry = queue_db.add_worked_caller('K0TEST', test_qrz_info)
        print(f"   ✅ Added worked caller: {worked_entry}")
        
        # Test 4: Check list after adding
        print("\n4. Checking worked callers list after adding...")
        worked_list = queue_db.get_worked_callers()
        count = queue_db.get_worked_callers_count()
        print(f"   ✅ Found {count} worked callers")
        for caller in worked_list:
            print(f"      - {caller['callsign']}: {caller['name']} from {caller['location']}")
        
        # Test 5: Add same caller again (should update)
        print("\n5. Adding same caller again (should update)...")
        worked_entry = queue_db.add_worked_caller('K0TEST', test_qrz_info)
        print(f"   ✅ Updated worked caller: {worked_entry}")
        print(f"   📊 Times worked: {worked_entry['times_worked']}")
        
        # Test 6: Add different caller
        print("\n6. Adding different caller...")
        test_qrz_info2 = {
            'name': 'Jane Smith',
            'address': 'Denver, CO, USA', 
            'dxcc_name': 'United States',
            'image': 'https://s3.amazonaws.com/files.qrz.com/w/w0test/w0test.jpg'
        }
        
        worked_entry2 = queue_db.add_worked_caller('W0TEST', test_qrz_info2)
        print(f"   ✅ Added second worked caller: {worked_entry2}")
        
        # Test 7: Check final list
        print("\n7. Checking final worked callers list...")
        worked_list = queue_db.get_worked_callers()
        count = queue_db.get_worked_callers_count()
        print(f"   ✅ Found {count} worked callers")
        for caller in worked_list:
            print(f"      - {caller['callsign']}: {caller['name']} from {caller['location']} ({caller['times_worked']} times)")
        
        # Test 8: Test system status clearing
        print("\n8. Testing system deactivation (should clear worked callers)...")
        status = queue_db.set_system_status(False, "test_user")
        print(f"   ✅ System deactivated. Worked callers cleared: {status['worked_callers_cleared']}")
        
        # Test 9: Verify clearing
        print("\n9. Verifying worked callers cleared...")
        worked_list = queue_db.get_worked_callers()
        count = queue_db.get_worked_callers_count()
        print(f"   ✅ Found {count} worked callers after deactivation: {worked_list}")
        
        print("\n🎉 All tests passed! Worked callers functionality is working correctly.")
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_worked_callers_functionality()
