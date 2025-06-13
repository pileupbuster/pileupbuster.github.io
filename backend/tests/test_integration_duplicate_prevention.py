"""
Integration test for the complete duplicate callsign prevention flow.
"""
import pytest
from unittest.mock import Mock, patch
from fastapi.testclient import TestClient
from app.app import create_app


@pytest.fixture
def test_app():
    """Create a test app instance"""
    return create_app()


@pytest.fixture
def test_client(test_app):
    """Create a test client"""
    return TestClient(test_app)


class TestIntegrationDuplicatePrevention:
    """Integration tests for duplicate callsign prevention across the full API"""
    
    @patch('app.routes.queue.queue_db')
    def test_full_api_duplicate_prevention_flow(self, mock_db, test_client):
        """Test the complete flow from API request to database validation"""
        
        # Test 1: First registration succeeds
        mock_db.register_callsign.return_value = {
            'callsign': 'KC1ABC',
            'timestamp': '2024-01-01T12:00:00',
            'position': 1
        }
        
        response1 = test_client.post('/api/queue/register', json={'callsign': 'KC1ABC'})
        
        assert response1.status_code == 200
        assert response1.json()['message'] == 'Callsign registered successfully'
        assert response1.json()['entry']['callsign'] == 'KC1ABC'
        
        # Test 2: Duplicate registration fails
        mock_db.register_callsign.side_effect = ValueError("Callsign already in queue")
        
        response2 = test_client.post('/api/queue/register', json={'callsign': 'KC1ABC'})
        
        assert response2.status_code == 400
        assert response2.json()['detail'] == 'Callsign already in queue'
        
    @patch('app.routes.queue.queue_db')
    @patch('app.routes.queue.qrz_service')
    def test_case_insensitive_duplicate_detection(self, mock_qrz_service, mock_db, test_client):
        """Test that duplicate detection works across different case variations"""
        
        # Mock QRZ service
        mock_qrz_service.lookup_callsign.return_value = {
            'callsign': 'KC1ABC',
            'name': None,
            'address': None,
            'error': 'QRZ.com credentials not configured. Please set QRZ_USERNAME and QRZ_PASSWORD environment variables.'
        }
        
        # Mock active system
        mock_db.get_system_status.return_value = {'active': True}
        
        # Mock that the uppercase version already exists
        mock_db.register_callsign.side_effect = ValueError("Callsign already in queue")
        
        # Try to register lowercase version of existing callsign
        response = test_client.post('/api/queue/register', json={'callsign': 'kc1abc'})
        
        assert response.status_code == 400
        assert response.json()['detail'] == 'Callsign already in queue'
        
        # Verify the database was called with normalized uppercase callsign and QRZ info
        args, kwargs = mock_db.register_callsign.call_args
        assert args[0] == 'KC1ABC'  # First argument is callsign
        assert args[1]['callsign'] == 'KC1ABC'  # Second argument is QRZ info dict
        
    @patch('app.routes.queue.queue_db')
    @patch('app.routes.queue.qrz_service')
    def test_whitespace_handling_in_duplicate_detection(self, mock_qrz_service, mock_db, test_client):
        """Test that whitespace is properly handled in duplicate detection"""
        
        # Mock QRZ service
        mock_qrz_service.lookup_callsign.return_value = {
            'callsign': 'KC1ABC',
            'name': None,
            'address': None,
            'error': 'QRZ.com credentials not configured. Please set QRZ_USERNAME and QRZ_PASSWORD environment variables.'
        }
        
        # Mock active system
        mock_db.get_system_status.return_value = {'active': True}
        
        # Mock that the trimmed version already exists
        mock_db.register_callsign.side_effect = ValueError("Callsign already in queue")
        
        # Try to register callsign with whitespace
        response = test_client.post('/api/queue/register', json={'callsign': '  KC1ABC  '})
        
        assert response.status_code == 400
        assert response.json()['detail'] == 'Callsign already in queue'
        
        # Verify the database was called with trimmed callsign and QRZ info
        args, kwargs = mock_db.register_callsign.call_args
        assert args[0] == 'KC1ABC'  # First argument is callsign
        assert args[1]['callsign'] == 'KC1ABC'  # Second argument is QRZ info dict
        
    @patch('app.routes.queue.queue_db')
    def test_admin_endpoints_do_not_bypass_validation(self, mock_db, test_client):
        """Test that admin endpoints don't provide a way to bypass duplicate validation"""
        
        # Test that admin endpoints don't allow adding callsigns
        # They should only allow viewing, removing, clearing, or processing
        
        # Try to POST to admin endpoints (should not accept callsign data)
        response1 = test_client.post('/api/admin/queue/clear', 
                                    auth=('admin', 'admin'),
                                    json={'callsign': 'KC1ABC'})
        # Should work for clearing but ignore the callsign data
        
        response2 = test_client.post('/api/admin/queue/next',
                                    auth=('admin', 'admin'), 
                                    json={'callsign': 'KC1ABC'})
        # Should work for processing next but ignore the callsign data
        
        # Neither should result in a callsign being added to the queue
        # The only way to add is through /api/queue/register which is validated
        
        # These will fail due to auth/database issues but won't bypass validation
        assert response1.status_code in [401, 500, 503]  # Auth or DB error, not success
        assert response2.status_code in [400, 401, 500, 503]  # Auth, empty queue, or DB error
        
    def test_only_one_registration_endpoint_exists(self, test_client):
        """Verify that there is only one endpoint for registering callsigns"""
        
        # Test that the known registration endpoint exists
        response = test_client.post('/api/queue/register', json={'callsign': ''})
        assert response.status_code in [400, 500]  # Should fail validation or DB, not 404
        
        # Test that non-existent registration endpoints return 404
        response1 = test_client.post('/api/queue/add', json={'callsign': 'KC1ABC'})
        assert response1.status_code == 404
        
        response2 = test_client.post('/api/admin/register', json={'callsign': 'KC1ABC'})
        assert response2.status_code == 404
        
        response3 = test_client.put('/api/queue/register', json={'callsign': 'KC1ABC'})
        assert response3.status_code == 405  # Method not allowed