#!/usr/bin/env python3
"""
Environment Variable Verification Script

This script verifies that WebSocket environment variables are properly loaded.
Run this from the backend directory to check configuration.
"""

import os
from dotenv import load_dotenv

def check_env_vars():
    """Check if all required environment variables are set."""
    
    # Load environment variables
    load_dotenv()
    
    print("🔍 Environment Variable Check")
    print("=" * 40)
    
    # Required variables
    required_vars = [
        'ADMIN_USERNAME',
        'ADMIN_PASSWORD',
        'WEBSOCKET_MAX_CONNECTIONS', 
        'WEBSOCKET_HEARTBEAT_INTERVAL'
    ]
    
    # Optional variables
    optional_vars = [
        'MONGO_URI',
        'QRZ_USERNAME',
        'QRZ_PASSWORD',
        'MAX_QUEUE_SIZE'
    ]
    
    print("\n📋 Required Variables:")
    all_required_present = True
    for var in required_vars:
        value = os.getenv(var)
        if value:
            # Don't show actual password values
            if 'PASSWORD' in var:
                print(f"✅ {var}: [HIDDEN]")
            else:
                print(f"✅ {var}: {value}")
        else:
            print(f"❌ {var}: NOT SET")
            all_required_present = False
    
    print("\n📋 Optional Variables:")
    for var in optional_vars:
        value = os.getenv(var)
        if value:
            # Don't show actual password/URI values
            if 'PASSWORD' in var or 'URI' in var:
                print(f"ℹ️ {var}: [HIDDEN]")
            else:
                print(f"ℹ️ {var}: {value}")
        else:
            print(f"⚠️ {var}: NOT SET")
    
    print("\n" + "=" * 40)
    if all_required_present:
        print("✅ All required environment variables are set!")
        print("🚀 WebSocket server should work correctly")
    else:
        print("❌ Some required environment variables are missing!")
        print("📝 Check your .env file")
    
    return all_required_present

if __name__ == "__main__":
    check_env_vars()
