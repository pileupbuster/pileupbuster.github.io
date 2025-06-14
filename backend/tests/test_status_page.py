"""
Tests for the status page endpoint with screenshot functionality
"""
import pytest
from unittest.mock import Mock, patch
from fastapi.testclient import TestClient
from app.app import create_app
import os


@pytest.fixture
def test_client():
    """Create a test client"""
    app = create_app()
    with TestClient(app) as client:
        yield client


class TestStatusPageEndpoint:
    """Test cases for status page endpoint functionality"""
    
    def test_get_status_page_success(self, test_client):
        """Test successful status page generation"""
        with patch('app.services.screenshot.capture_screenshot') as mock_screenshot:
            mock_screenshot.return_value = 'mock_base64_image_data'
            
            response = test_client.get('/status')
            
            assert response.status_code == 200
            assert response.headers['content-type'] == 'text/html; charset=utf-8'
            
            content = response.text
            assert 'Pileup Buster Status' in content
            assert 'mock_base64_image_data' in content
            assert 'Go to Pileup Buster Frontend' in content
    
    def test_get_status_page_with_custom_frontend_url(self, test_client):
        """Test status page with custom frontend URL from environment"""
        custom_url = 'https://example.com:8080'
        
        with patch('app.services.screenshot.capture_screenshot') as mock_screenshot:
            with patch.dict(os.environ, {'FRONTEND_URL': custom_url}):
                mock_screenshot.return_value = 'mock_base64_image_data'
                
                response = test_client.get('/status')
                
                assert response.status_code == 200
                content = response.text
                assert custom_url in content
                
                # Verify screenshot was called with custom URL
                mock_screenshot.assert_called_once_with(custom_url)
    
    def test_get_status_page_screenshot_failure(self, test_client):
        """Test status page when screenshot capture fails"""
        with patch('app.services.screenshot.capture_screenshot') as mock_screenshot:
            mock_screenshot.return_value = None  # Simulate failure
            
            response = test_client.get('/status')
            
            assert response.status_code == 500
            content = response.text
            assert 'Status Page Unavailable' in content
    
    def test_get_status_page_exception_handling(self, test_client):
        """Test status page exception handling"""
        with patch('app.services.screenshot.capture_screenshot') as mock_screenshot:
            mock_screenshot.side_effect = Exception("Screenshot service error")
            
            response = test_client.get('/status')
            
            assert response.status_code == 500
            content = response.text
            assert 'Status Page Unavailable' in content
            assert 'Screenshot service error' in content
    
    def test_get_status_page_default_frontend_url(self, test_client):
        """Test status page uses default frontend URL when not configured"""
        with patch('app.services.screenshot.capture_screenshot') as mock_screenshot:
            with patch.dict(os.environ, {}, clear=True):  # Clear environment
                mock_screenshot.return_value = 'mock_base64_image_data'
                
                response = test_client.get('/status')
                
                assert response.status_code == 200
                
                # Verify screenshot was called with default URL
                mock_screenshot.assert_called_once_with('http://localhost:3000')
    
    def test_get_status_page_no_authentication_required(self, test_client):
        """Test that status page endpoint does not require authentication"""
        with patch('app.services.screenshot.capture_screenshot') as mock_screenshot:
            mock_screenshot.return_value = 'mock_base64_image_data'
            
            # Make request without any authentication
            response = test_client.get('/status')
            
            assert response.status_code == 200
    
    def test_get_status_page_contains_required_elements(self, test_client):
        """Test that status page contains all required elements"""
        with patch('app.services.screenshot.capture_screenshot') as mock_screenshot:
            mock_screenshot.return_value = 'mock_base64_image_data'
            
            response = test_client.get('/status')
            
            assert response.status_code == 200
            content = response.text
            
            # Check for required HTML elements
            assert '<html' in content
            assert '<head>' in content
            assert '<title>Pileup Buster Status</title>' in content
            assert '<img' in content
            assert 'data:image/png;base64,mock_base64_image_data' in content
            assert '<a href=' in content
            assert 'Go to Pileup Buster Frontend' in content
            assert 'Screenshot taken:' in content