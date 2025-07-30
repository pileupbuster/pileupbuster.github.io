#!/usr/bin/env python3
"""Test script to verify worked callers are displayed on the map"""

import asyncio
from playwright.async_api import async_playwright
import json

async def test_worked_callers_map():
    async with async_playwright() as p:
        # Launch browser with headless=False to see what's happening
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()
        
        # Enable console logging
        page.on("console", lambda msg: print(f"Browser console: {msg.text}"))
        page.on("pageerror", lambda err: print(f"Page error: {err}"))
        
        # First, let's check the API directly
        print("\n1. Testing /api/public/worked-callers endpoint...")
        api_response = await page.request.get("http://localhost:8000/api/public/worked-callers")
        api_data = await api_response.json()
        print(f"API Response Status: {api_response.status}")
        print(f"API Response: {json.dumps(api_data, indent=2)}")
        
        # Navigate to the frontend
        print("\n2. Loading frontend...")
        await page.goto("http://localhost:5173")
        
        # Wait for the page to load
        await page.wait_for_timeout(3000)
        
        # Check if map container exists
        print("\n3. Checking map container...")
        map_container = await page.query_selector(".map-container")
        if map_container:
            print("✓ Map container found")
        else:
            print("✗ Map container NOT found")
        
        # Check for map markers
        print("\n4. Checking for map markers...")
        markers = await page.query_selector_all(".leaflet-marker-icon")
        print(f"Found {len(markers)} markers on the map")
        
        # Check for worked operator markers specifically
        worked_markers = await page.query_selector_all(".marker-avatar.worked")
        print(f"Found {len(worked_markers)} worked operator markers")
        
        # Get marker details if any exist
        if worked_markers:
            for i, marker in enumerate(worked_markers):
                marker_html = await marker.inner_html()
                print(f"Marker {i+1} HTML: {marker_html}")
        
        # Check React state by evaluating in browser context
        print("\n5. Checking React component state...")
        try:
            # Try to access the worked operators state
            worked_state = await page.evaluate("""
                () => {
                    // Try to find React fiber
                    const container = document.querySelector('#root');
                    if (!container || !container._reactRootContainer) {
                        return 'Could not find React root';
                    }
                    
                    // Log to console for debugging
                    console.log('React root found');
                    
                    // Try to access component state through React DevTools hook
                    if (window.__REACT_DEVTOOLS_GLOBAL_HOOK__) {
                        const hook = window.__REACT_DEVTOOLS_GLOBAL_HOOK__;
                        console.log('React DevTools hook found');
                    }
                    
                    return 'Check console for React debugging';
                }
            """)
            print(f"React state check: {worked_state}")
        except Exception as e:
            print(f"Could not check React state: {e}")
        
        # Check network requests
        print("\n6. Monitoring network requests...")
        
        # Set up network monitoring
        network_logs = []
        
        async def log_request(request):
            if "worked-callers" in request.url or "previous-qsos" in request.url:
                network_logs.append(f"Request: {request.method} {request.url}")
        
        async def log_response(response):
            if "worked-callers" in response.url or "previous-qsos" in response.url:
                try:
                    body = await response.body()
                    json_body = json.loads(body)
                    network_logs.append(f"Response: {response.status} {response.url}")
                    network_logs.append(f"Response body: {json.dumps(json_body, indent=2)}")
                except:
                    network_logs.append(f"Response: {response.status} {response.url} (could not parse body)")
        
        page.on("request", log_request)
        page.on("response", log_response)
        
        # Reload the page to capture network requests
        print("Reloading page to capture network requests...")
        await page.reload()
        await page.wait_for_timeout(3000)
        
        # Print network logs
        print("\n7. Network requests:")
        for log in network_logs:
            print(log)
        
        # Check for errors in the console
        print("\n8. Checking for JavaScript errors...")
        errors = await page.evaluate("""
            () => {
                // Check if there are any errors in window.onerror
                return window.__errors || [];
            }
        """)
        if errors:
            print(f"JavaScript errors found: {errors}")
        else:
            print("No JavaScript errors found")
        
        # Take a screenshot for visual debugging
        print("\n9. Taking screenshot...")
        await page.screenshot(path="map_debug_screenshot.png")
        print("Screenshot saved as map_debug_screenshot.png")
        
        # Keep browser open for manual inspection
        print("\n10. Browser will stay open for 30 seconds for manual inspection...")
        await page.wait_for_timeout(30000)
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(test_worked_callers_map())