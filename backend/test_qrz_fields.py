#!/usr/bin/env python3
"""
Test script to explore QRZ result object fields
"""

import os
import sys
from callsignlookuptools import QrzSyncClient

def test_qrz_fields():
    """Test what fields are available in QRZ lookup results"""
    print("🔍 Testing QRZ Fields\n")
    
    # Create a mock result to see available attributes
    try:
        # Create client (won't authenticate, just want to see structure)
        client = QrzSyncClient("test", "test")
        
        # Check if we can get sample data structure
        print("QRZ Client created successfully")
        
        # Let's see what the search method returns by examining the source
        import inspect
        print("\nSearch method signature:")
        print(inspect.signature(client.search))
        
        # Let's try to understand the result structure by looking at the module
        from callsignlookuptools import qrz
        print("\nQRZ module attributes:")
        print([attr for attr in dir(qrz) if not attr.startswith('_')])
        
    except Exception as e:
        print(f"Error: {e}")
        
    # Let's also check what we can import
    try:
        from callsignlookuptools.qrz import QrzResult
        print("\nQRZ Result attributes:")
        print([attr for attr in dir(QrzResult) if not attr.startswith('_')])
    except ImportError:
        print("QrzResult not directly importable")
        
    try:
        import callsignlookuptools
        print(f"\nCallsignlookuptools version: {callsignlookuptools.__version__}")
    except:
        print("Version not available")

if __name__ == "__main__":
    test_qrz_fields()
