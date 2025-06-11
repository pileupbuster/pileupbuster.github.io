"""
Test for duplicate callsign prevention in the pileup-buster queue system.
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
    
    # Patch the database instance
    with patch('app.routes.queue.queue_db', mock_database):
        with TestClient(app) as client:
            yield client, mock_database


class TestDuplicateCallsignPrevention:
    """Test cases for duplicate callsign prevention"""
    
    def test_register_new_callsign_succeeds(self, test_client):
        """Test that registering a new callsign works correctly"""
        client, mock_db = test_client
        
        # Mock successful registration
        mock_db.register_callsign.return_value = {
            'callsign': 'KC1ABC',
            'timestamp': '2024-01-01T12:00:00',
            'position': 1
        }
        
        response = client.post('/api/queue/register', json={'callsign': 'KC1ABC'})
        
        assert response.status_code == 200
        assert response.json()['message'] == 'Callsign registered successfully'
        assert response.json()['entry']['callsign'] == 'KC1ABC'
        mock_db.register_callsign.assert_called_once_with('KC1ABC')
    
    def test_register_duplicate_callsign_fails(self, test_client):
        """Test that registering a duplicate callsign fails with proper error"""
        client, mock_db = test_client
        
        # Mock duplicate callsign error
        mock_db.register_callsign.side_effect = ValueError("Callsign already in queue")
        
        response = client.post('/api/queue/register', json={'callsign': 'KC1ABC'})
        
        assert response.status_code == 400
        assert response.json()['detail'] == 'Callsign already in queue'
        mock_db.register_callsign.assert_called_once_with('KC1ABC')
    
    def test_callsign_case_insensitive_handling(self, test_client):
        """Test that callsigns are handled case-insensitively"""
        client, mock_db = test_client
        
        # Test that lowercase input is converted to uppercase
        mock_db.register_callsign.return_value = {
            'callsign': 'KC1ABC',
            'timestamp': '2024-01-01T12:00:00',
            'position': 1
        }
        
        response = client.post('/api/queue/register', json={'callsign': 'kc1abc'})
        
        assert response.status_code == 200
        # Verify the database was called with uppercase callsign
        mock_db.register_callsign.assert_called_once_with('KC1ABC')
    
    def test_callsign_whitespace_trimming(self, test_client):
        """Test that whitespace is properly trimmed from callsigns"""
        client, mock_db = test_client
        
        mock_db.register_callsign.return_value = {
            'callsign': 'KC1ABC',
            'timestamp': '2024-01-01T12:00:00',
            'position': 1
        }
        
        response = client.post('/api/queue/register', json={'callsign': '  KC1ABC  '})
        
        assert response.status_code == 200
        # Verify the database was called with trimmed callsign
        mock_db.register_callsign.assert_called_once_with('KC1ABC')
    
    def test_empty_callsign_validation(self, test_client):
        """Test that empty callsigns are rejected"""
        client, mock_db = test_client
        
        response = client.post('/api/queue/register', json={'callsign': ''})
        
        assert response.status_code == 400
        assert response.json()['detail'] == 'Callsign is required'
        # Database should not be called for empty callsign
        mock_db.register_callsign.assert_not_called()
    
    def test_whitespace_only_callsign_validation(self, test_client):
        """Test that callsigns with only whitespace are rejected"""
        client, mock_db = test_client
        
        response = client.post('/api/queue/register', json={'callsign': '   '})
        
        assert response.status_code == 400
        assert response.json()['detail'] == 'Callsign is required'
        # Database should not be called for whitespace-only callsign
        mock_db.register_callsign.assert_not_called()
    
    def test_database_error_handling(self, test_client):
        """Test that unexpected database errors are handled properly"""
        client, mock_db = test_client
        
        # Mock unexpected database error
        mock_db.register_callsign.side_effect = Exception("Database connection failed")
        
        response = client.post('/api/queue/register', json={'callsign': 'KC1ABC'})
        
        assert response.status_code == 500
        assert response.json()['detail'] == 'Failed to register callsign'
    
    def test_duplicate_prevention_with_mixed_case(self, test_client):
        """Test duplicate prevention works with different case variations"""
        client, mock_db = test_client
        
        # Mock that the callsign already exists (even though input case differs)
        mock_db.register_callsign.side_effect = ValueError("Callsign already in queue")
        
        response = client.post('/api/queue/register', json={'callsign': 'kc1ABC'})
        
        assert response.status_code == 400
        assert response.json()['detail'] == 'Callsign already in queue'
        # Should have been normalized to uppercase before database call
        mock_db.register_callsign.assert_called_once_with('KC1ABC')


class TestDatabaseDuplicatePrevention:
    """Test the database layer duplicate prevention logic"""
    
    def test_database_duplicate_check_logic(self):
        """Test the database duplicate check logic using a mock database instance"""
        # Create a database instance with a mocked collection
        mock_collection = Mock()
        
        db = QueueDatabase()
        db.collection = mock_collection  # Directly set the mock collection
        
        # Test existing callsign
        mock_collection.find_one.return_value = {'callsign': 'KC1ABC', 'timestamp': '2024-01-01T12:00:00'}
        
        with pytest.raises(ValueError, match="Callsign already in queue"):
            db.register_callsign('KC1ABC')
        
        # Verify the correct query was made
        mock_collection.find_one.assert_called_with({"callsign": "KC1ABC"})
    
    def test_database_new_callsign_registration_logic(self):
        """Test successful new callsign registration at database level"""
        # Create a database instance with a mocked collection
        mock_collection = Mock()
        
        db = QueueDatabase()
        db.collection = mock_collection  # Directly set the mock collection
        
        # Mock no existing callsign and successful insert
        mock_collection.find_one.return_value = None
        mock_collection.count_documents.return_value = 0  # Empty queue
        mock_collection.insert_one.return_value = Mock()
        
        result = db.register_callsign('KC1ABC')
        
        assert result['callsign'] == 'KC1ABC'
        assert 'timestamp' in result
        assert result['position'] == 1
        
        # Verify the duplicate check was performed
        mock_collection.find_one.assert_called_with({"callsign": "KC1ABC"})
        # Verify the insert was attempted
        mock_collection.insert_one.assert_called_once()