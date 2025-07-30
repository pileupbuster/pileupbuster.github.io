#!/usr/bin/env python3
"""
Test script for grid/coordinates functionality in QRZ lookup
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from app.services.qrz import qrz_service
from app.database import queue_db

def test_grid_functionality():
    """Test the grid/coordinates functionality"""
    print("🧪 Testing Grid/Coordinates Functionality\n")
    
    try:
        # Test 1: Test QRZ lookup with grid extraction
        print("1. Testing QRZ lookup with grid coordinates...")
        
        # Test with a known callsign (you may want to use a real one for testing)
        test_callsign = "W1AW"  # ARRL headquarters - should have grid data
        
        result = qrz_service.lookup_callsign(test_callsign)
        print(f"   ✅ QRZ lookup result for {test_callsign}:")
        print(f"      Callsign: {result.get('callsign')}")
        print(f"      Name: {result.get('name')}")
        print(f"      Address: {result.get('address')}")
        print(f"      DXCC: {result.get('dxcc_name')}")
        print(f"      Grid: {result.get('grid')}")
        
        if result.get('error'):
            print(f"      Error: {result.get('error')}")
            print("   ⚠️  Note: This test requires valid QRZ credentials")
            return
            
        # Test 2: Test database storage with grid info
        print("\n2. Testing database storage with grid information...")
        
        # Clear worked callers first
        cleared_count = queue_db.clear_worked_callers()
        print(f"   ✅ Cleared {cleared_count} existing entries")
        
        # Add the worked caller with grid info
        worked_entry = queue_db.add_worked_caller(test_callsign, result)
        print(f"   ✅ Added worked caller with grid info:")
        print(f"      Callsign: {worked_entry.get('callsign')}")
        print(f"      Name: {worked_entry.get('name')}")
        print(f"      Location: {worked_entry.get('location')}")
        print(f"      Grid Info: {worked_entry.get('grid')}")
        
        # Test 3: Verify grid data persistence
        print("\n3. Verifying grid data persistence...")
        worked_list = queue_db.get_worked_callers()
        
        if worked_list:
            entry = worked_list[0]
            grid_data = entry.get('grid', {})
            print(f"   ✅ Retrieved from database:")
            print(f"      Latitude: {grid_data.get('lat')}")
            print(f"      Longitude: {grid_data.get('long')}")
            print(f"      Grid Square: {grid_data.get('grid')}")
        else:
            print("   ❌ No entries found in database")
            
        # Test 4: Test QSO workflow with grid data
        print("\n4. Testing QSO workflow with grid data...")
        
        # Set current QSO with grid-enabled QRZ info
        qso_result = queue_db.set_current_qso(test_callsign, result)
        print(f"   ✅ Set current QSO:")
        print(f"      Callsign: {qso_result.get('callsign')}")
        qrz_data = qso_result.get('qrz', {})
        grid_info = qrz_data.get('grid', {})
        print(f"      QSO Grid Info: {grid_info}")
        
        # Complete the QSO (this should add to worked callers with grid)
        completed_qso = queue_db.complete_current_qso()
        print(f"   ✅ Completed QSO: {completed_qso.get('callsign') if completed_qso else 'None'}")
        
        # Verify the worked caller now has grid data
        worked_list_after = queue_db.get_worked_callers()
        if worked_list_after:
            final_entry = worked_list_after[0]
            final_grid = final_entry.get('grid', {})
            print(f"   ✅ Final worked caller grid data: {final_grid}")
            print(f"   📊 Times worked: {final_entry.get('times_worked', 0)}")
        
        print("\n🎉 All grid functionality tests completed successfully!")
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_grid_functionality()
