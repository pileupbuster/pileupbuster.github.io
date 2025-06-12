"""
Tests for public endpoint functionality in the pileup-buster queue system.
"""
import pytest
from unittest.mock import Mock, patch
from fastapi.testclient import TestClient
from app.app import create_app
from app.database import QueueDatabase


@pytest.fixture
def mock_database():
    """Create a mock database for testing"""
    mock_db = Mock(spec=QueueDatabase)
    return mock_db


@pytest.fixture
def test_client(mock_database):
    """Create a test client with mocked database"""
    app = create_app()
    
    # Patch the database instance in all routes
    with patch('app.routes.admin.queue_db', mock_database):
        with patch('app.routes.queue.queue_db', mock_database):
            with patch('app.routes.public.queue_db', mock_database):
                with TestClient(app) as client:
                    yield client, mock_database


class TestPublicStatusEndpoint:
    """Test cases for public status endpoint functionality"""
    
    def test_get_public_status_active(self, test_client):
        """Test getting public system status when system is active"""
        client, mock_db = test_client
        
        # Mock active system status
        mock_db.get_system_status.return_value = {
            'active': True,
            'last_updated': '2024-01-01T12:00:00Z',
            'updated_by': 'admin'
        }
        
        response = client.get('/api/public/status')
        
        assert response.status_code == 200
        data = response.json()
        assert data['active'] is True
        
        # Ensure sensitive information is not exposed
        assert 'updated_by' not in data
        assert 'last_updated' not in data
        
        # Verify database was called
        mock_db.get_system_status.assert_called_once()
    
    def test_get_public_status_inactive(self, test_client):
        """Test getting public system status when system is inactive"""
        client, mock_db = test_client
        
        # Mock inactive system status
        mock_db.get_system_status.return_value = {
            'active': False,
            'last_updated': '2024-01-01T12:00:00Z',
            'updated_by': 'admin'
        }
        
        response = client.get('/api/public/status')
        
        assert response.status_code == 200
        data = response.json()
        assert data['active'] is False
        
        # Ensure sensitive information is not exposed
        assert 'updated_by' not in data
        assert 'last_updated' not in data
        
        # Verify database was called
        mock_db.get_system_status.assert_called_once()
    
    def test_get_public_status_no_authentication_required(self, test_client):
        """Test that public status endpoint does not require authentication"""
        client, mock_db = test_client
        
        # Mock system status
        mock_db.get_system_status.return_value = {
            'active': False,
            'last_updated': '2024-01-01T12:00:00Z',
            'updated_by': 'admin'
        }
        
        # Make request without any authentication
        response = client.get('/api/public/status')
        
        assert response.status_code == 200
        data = response.json()
        assert 'active' in data
        
    def test_get_public_status_database_error(self, test_client):
        """Test handling of database error in public status endpoint"""
        client, mock_db = test_client
        
        # Mock database error
        mock_db.get_system_status.side_effect = Exception("Database connection error")
        
        response = client.get('/api/public/status')
        
        assert response.status_code == 500
        assert 'Database error' in response.json()['detail']
        
    def test_get_public_status_missing_active_field(self, test_client):
        """Test public status endpoint with missing active field in database response"""
        client, mock_db = test_client
        
        # Mock status without active field
        mock_db.get_system_status.return_value = {
            'last_updated': '2024-01-01T12:00:00Z',
            'updated_by': 'admin'
        }
        
        response = client.get('/api/public/status')
        
        assert response.status_code == 200
        data = response.json()
        # Should default to False when active field is missing
        assert data['active'] is False


class TestPublicEndpointSecurity:
    """Test security aspects of public endpoints"""
    
    def test_public_status_does_not_expose_admin_info(self, test_client):
        """Test that public status endpoint does not expose admin information"""
        client, mock_db = test_client
        
        # Mock status with all fields including sensitive ones
        mock_db.get_system_status.return_value = {
            'active': True,
            'last_updated': '2024-01-01T12:00:00Z',
            'updated_by': 'sensitive_admin_username'
        }
        
        response = client.get('/api/public/status')
        
        assert response.status_code == 200
        data = response.json()
        
        # Only active status should be present
        assert list(data.keys()) == ['active']
        assert data['active'] is True
        
        # Sensitive fields should not be present
        assert 'updated_by' not in data
        assert 'last_updated' not in data