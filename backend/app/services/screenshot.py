"""
Screenshot service for capturing frontend screenshots
"""
import os
import base64
import logging
from datetime import datetime
from typing import Optional

logger = logging.getLogger(__name__)


def create_mock_screenshot() -> str:
    """Create a mock screenshot as base64 encoded image"""
    # Create a simple 1x1 pixel PNG image in base64
    # This is a placeholder until actual screenshot implementation is ready
    mock_png = b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90wS\xde\x00\x00\x00\x12IDATx\x9cc```bPPP\x00\x02\xac\x01\x00\x05\x1c\x00\x1a\x1e\x1d\x1d\x9b\x00\x00\x00\x00IEND\xaeB`\x82'
    return base64.b64encode(mock_png).decode('utf-8')


def capture_screenshot_with_playwright(url: str) -> Optional[str]:
    """
    Capture screenshot using playwright (if available)
    
    Args:
        url: The URL to capture
        
    Returns:
        Base64 encoded screenshot image, or None if capture fails
    """
    try:
        from playwright.sync_api import sync_playwright
        
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.goto(url, timeout=30000)
            screenshot_bytes = page.screenshot(type='png', full_page=True)
            browser.close()
            
            return base64.b64encode(screenshot_bytes).decode('utf-8')
            
    except ImportError:
        logger.warning("Playwright not available, falling back to mock screenshot")
        return None
    except Exception as e:
        logger.error(f"Playwright screenshot failed: {e}")
        return None


def capture_screenshot_with_selenium(url: str) -> Optional[str]:
    """
    Capture screenshot using selenium (if available)
    
    Args:
        url: The URL to capture
        
    Returns:
        Base64 encoded screenshot image, or None if capture fails
    """
    try:
        from selenium import webdriver
        from selenium.webdriver.chrome.options import Options
        
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")
        
        driver = webdriver.Chrome(options=chrome_options)
        driver.get(url)
        
        # Wait a moment for page to load
        import time
        time.sleep(2)
        
        screenshot_b64 = driver.get_screenshot_as_base64()
        driver.quit()
        
        return screenshot_b64
        
    except ImportError:
        logger.warning("Selenium not available, falling back to mock screenshot")
        return None
    except Exception as e:
        logger.error(f"Selenium screenshot failed: {e}")
        return None


def capture_screenshot(url: str) -> Optional[str]:
    """
    Capture a screenshot of the given URL
    
    Args:
        url: The URL to capture
        
    Returns:
        Base64 encoded screenshot image, or None if capture fails
    """
    try:
        logger.info(f"Capturing screenshot of {url}")
        
        # Try playwright first
        screenshot_b64 = capture_screenshot_with_playwright(url)
        if screenshot_b64:
            logger.info("Screenshot captured with playwright")
            return screenshot_b64
        
        # Try selenium as fallback
        screenshot_b64 = capture_screenshot_with_selenium(url)
        if screenshot_b64:
            logger.info("Screenshot captured with selenium")
            return screenshot_b64
        
        # Fall back to mock screenshot
        logger.info("Using mock screenshot as fallback")
        return create_mock_screenshot()
        
    except Exception as e:
        logger.error(f"Failed to capture screenshot: {e}")
        return create_mock_screenshot()


def generate_status_html(screenshot_b64: str, frontend_url: str, timestamp: str) -> str:
    """
    Generate HTML status page with screenshot
    
    Args:
        screenshot_b64: Base64 encoded screenshot
        frontend_url: URL to link back to frontend
        timestamp: Timestamp of screenshot
        
    Returns:
        HTML content as string
    """
    html_template = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Pileup Buster Status</title>
    <style>
        body {{
            font-family: Arial, sans-serif;
            margin: 0;
            padding: 20px;
            background-color: #f5f5f5;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background-color: white;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            padding: 30px;
        }}
        .header {{
            text-align: center;
            margin-bottom: 30px;
        }}
        .header h1 {{
            color: #333;
            margin-bottom: 10px;
        }}
        .timestamp {{
            color: #666;
            font-size: 14px;
        }}
        .screenshot-container {{
            text-align: center;
            margin: 30px 0;
        }}
        .screenshot {{
            max-width: 100%;
            height: auto;
            border: 2px solid #ddd;
            border-radius: 8px;
            box-shadow: 0 4px 8px rgba(0,0,0,0.1);
        }}
        .link-container {{
            text-align: center;
            margin-top: 30px;
        }}
        .frontend-link {{
            display: inline-block;
            background-color: #007bff;
            color: white;
            text-decoration: none;
            padding: 12px 24px;
            border-radius: 6px;
            font-weight: 500;
            transition: background-color 0.2s;
        }}
        .frontend-link:hover {{
            background-color: #0056b3;
        }}
        .note {{
            margin-top: 20px;
            padding: 15px;
            background-color: #f8f9fa;
            border-left: 4px solid #007bff;
            color: #666;
            font-size: 14px;
        }}
        .mock-notice {{
            margin-top: 20px;
            padding: 15px;
            background-color: #fff3cd;
            border-left: 4px solid #ffc107;
            color: #856404;
            font-size: 14px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Pileup Buster Status</h1>
            <div class="timestamp">Screenshot taken: {timestamp}</div>
        </div>
        
        <div class="screenshot-container">
            <img src="data:image/png;base64,{screenshot_b64}" 
                 alt="Frontend Screenshot" 
                 class="screenshot">
        </div>
        
        <div class="link-container">
            <a href="{frontend_url}" class="frontend-link" target="_blank">
                ← Go to Pileup Buster Frontend
            </a>
        </div>
        
        <div class="note">
            This page shows a screenshot of the Pileup Buster frontend application. 
            Click the link above to access the live application.
        </div>
        
        <div class="mock-notice">
            <strong>Note:</strong> Currently using a mock screenshot. 
            To enable real screenshots, install playwright (<code>pip install playwright && playwright install chromium</code>) 
            or selenium with chrome driver.
        </div>
    </div>
</body>
</html>
"""
    return html_template