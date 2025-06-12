"""
Tests for queue endpoint behavior when system is inactive.
"""
import pytest
import os
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
    
    # Patch the database instance in queue routes
    with patch('app.routes.queue.queue_db', mock_database):
        with TestClient(app) as client:
            yield client, mock_database


class TestQueueInactiveSystem:
    """Test cases for queue behavior when system is inactive"""
    
    def test_queue_list_returns_empty_when_system_inactive(self, test_client):
        """Test that queue list returns empty when system is inactive"""
        client, mock_db = test_client
        
        # Mock inactive system status
        mock_db.get_system_status.return_value = {
            'active': False,
            'last_updated': '2024-01-01T12:00:00Z',
            'updated_by': 'admin'
        }
        
        response = client.get('/api/queue/list')
        
        assert response.status_code == 200
        data = response.json()
        assert data['queue'] == []
        assert data['total'] == 0
        assert data['system_active'] is False
        
        # Verify that system status was checked
        mock_db.get_system_status.assert_called_once()
        # Verify that get_queue_list was NOT called since system is inactive
        mock_db.get_queue_list.assert_not_called()
    
    def test_queue_list_returns_queue_when_system_active(self, test_client):
        """Test that queue list returns actual queue when system is active"""
        client, mock_db = test_client
        
        # Mock active system status
        mock_db.get_system_status.return_value = {
            'active': True,
            'last_updated': '2024-01-01T12:00:00Z',
            'updated_by': 'admin'
        }
        
        # Mock queue with entries
        mock_queue = [
            {'callsign': 'W1ABC', 'timestamp': '2024-01-01T12:00:00Z', 'position': 1},
            {'callsign': 'K2DEF', 'timestamp': '2024-01-01T12:01:00Z', 'position': 2}
        ]
        mock_db.get_queue_list.return_value = mock_queue
        
        response = client.get('/api/queue/list')
        
        assert response.status_code == 200
        data = response.json()
        assert data['queue'] == mock_queue
        assert data['total'] == 2
        assert data['system_active'] is True
        
        # Verify both calls were made
        mock_db.get_system_status.assert_called_once()
        mock_db.get_queue_list.assert_called_once()
    
    def test_register_callsign_fails_when_system_inactive(self, test_client):
        """Test that callsign registration fails when system is inactive"""
        client, mock_db = test_client
        
        # Mock inactive system status
        mock_db.get_system_status.return_value = {
            'active': False,
            'last_updated': '2024-01-01T12:00:00Z',
            'updated_by': 'admin'
        }
        
        response = client.post('/api/queue/register', json={'callsign': 'W1ABC'})
        
        assert response.status_code == 503
        data = response.json()
        assert 'System is currently inactive' in data['detail']
        
        # Verify system status was checked
        mock_db.get_system_status.assert_called_once()
        # Verify that register_callsign was NOT called
        mock_db.register_callsign.assert_not_called()
    
    def test_get_callsign_status_fails_when_system_inactive(self, test_client):
        """Test that getting callsign status fails when system is inactive"""
        client, mock_db = test_client
        
        # Mock inactive system status
        mock_db.get_system_status.return_value = {
            'active': False,
            'last_updated': '2024-01-01T12:00:00Z',
            'updated_by': 'admin'
        }
        
        response = client.get('/api/queue/status/W1ABC')
        
        assert response.status_code == 503
        data = response.json()
        assert 'System is currently inactive' in data['detail']
        
        # Verify system status was checked
        mock_db.get_system_status.assert_called_once()
        # Verify that find_callsign was NOT called
        mock_db.find_callsign.assert_not_called()
