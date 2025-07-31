"""Tests for QRZ information storage at registration time"""
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


class TestQRZStorageAtRegistration:
    """Test QRZ information storage during callsign registration"""
    
    @patch('app.routes.queue.queue_db')
    @patch('app.routes.queue.qrz_service')
    def test_register_callsign_stores_qrz_info(self, mock_qrz_service, mock_db, test_client):
        """Test that QRZ information is fetched and stored during registration"""
        # Mock active system status
        mock_db.get_system_status.return_value = {'active': True}
        
        # Mock QRZ service response
        mock_qrz_info = {
            'callsign': 'KC1ABC',
            'name': 'John Doe',
            'address': '123 Main St, City, State, Country',
            'image': 'http://example.com/image.jpg',
            'grid': {
                'lat': 42.3601,
                'long': -71.0589,
                'grid': 'FN42ko'
            },
            'error': None
        }
        mock_qrz_service.lookup_callsign.return_value = mock_qrz_info
        
        # Mock database registration response
        mock_entry = {
            'callsign': 'KC1ABC',
            'timestamp': '2024-01-01T12:00:00Z',
            'position': 1,
            'qrz': mock_qrz_info
        }
        mock_db.register_callsign.return_value = mock_entry
        
        # Make registration request
        response = test_client.post('/api/queue/register', json={'callsign': 'KC1ABC'})
        
        # Verify response
        assert response.status_code == 200
        data = response.json()
        assert data['message'] == 'Callsign registered successfully'
        assert data['entry']['callsign'] == 'KC1ABC'
        assert data['entry']['qrz']['name'] == 'John Doe'
        assert data['entry']['qrz']['address'] == '123 Main St, City, State, Country'
        assert data['entry']['qrz']['grid']['lat'] == 42.3601
        assert data['entry']['qrz']['grid']['long'] == -71.0589
        assert data['entry']['qrz']['grid']['grid'] == 'FN42ko'
        
        # Verify QRZ service was called during registration
        mock_qrz_service.lookup_callsign.assert_called_once_with('KC1ABC')
        
        # Verify database was called with QRZ information
        mock_db.register_callsign.assert_called_once_with('KC1ABC', mock_qrz_info)
    
    @patch('app.routes.queue.queue_db')
    def test_get_status_uses_stored_qrz_info(self, mock_db, test_client):
        """Test that status endpoint returns stored QRZ information without making API calls"""
        # Mock active system status
        mock_db.get_system_status.return_value = {'active': True}
        
        # Mock database entry with stored QRZ info
        mock_entry = {
            'callsign': 'KC1ABC',
            'timestamp': '2024-01-01T12:00:00Z',
            'position': 1,
            'qrz': {
                'callsign': 'KC1ABC',
                'name': 'John Doe',
                'address': '123 Main St, City, State, Country',
                'image': 'http://example.com/image.jpg',
                'grid': {
                    'lat': 42.3601,
                    'long': -71.0589,
                    'grid': 'FN42ko'
                },
                'error': None
            }
        }
        mock_db.find_callsign.return_value = mock_entry
        
        # Make status request
        response = test_client.get('/api/queue/status/KC1ABC')
        
        # Verify response includes stored QRZ information
        assert response.status_code == 200
        data = response.json()
        assert data['callsign'] == 'KC1ABC'
        assert data['qrz']['name'] == 'John Doe'
        assert data['qrz']['address'] == '123 Main St, City, State, Country'
        
        # Verify only database was queried, no QRZ API call was made
        mock_db.find_callsign.assert_called_once_with('KC1ABC')
    
    @patch('app.routes.queue.queue_db')
    def test_get_current_qso_uses_stored_qrz_info(self, mock_db, test_client):
        """Test that current QSO endpoint returns stored QRZ information"""
        # Mock active system status
        mock_db.get_system_status.return_value = {'active': True}
        
        # Mock current QSO with stored QRZ info
        mock_qso = {
            'callsign': 'KC1ABC',
            'timestamp': '2024-01-01T12:00:00Z',
            'qrz': {
                'callsign': 'KC1ABC',
                'name': 'John Doe',
                'address': '123 Main St, City, State, Country',
                'image': 'http://example.com/image.jpg',
                'error': None
            }
        }
        mock_db.get_current_qso.return_value = mock_qso
        
        # Make current QSO request
        response = test_client.get('/api/queue/current')
        
        # Verify response includes stored QRZ information
        assert response.status_code == 200
        data = response.json()
        assert data['callsign'] == 'KC1ABC'
        assert data['qrz']['name'] == 'John Doe'
        assert data['qrz']['address'] == '123 Main St, City, State, Country'
        
        # Verify only database was queried
        mock_db.get_current_qso.assert_called_once()
    
    @patch('app.routes.queue.queue_db')
    def test_queue_list_includes_qrz_info(self, mock_db, test_client):
        """Test that queue list includes stored QRZ information for all entries"""
        # Mock active system status
        mock_db.get_system_status.return_value = {'active': True}
        
        # Mock queue list with stored QRZ info
        mock_queue = [
            {
                'callsign': 'KC1ABC',
                'timestamp': '2024-01-01T12:00:00Z',
                'position': 1,
                'qrz': {
                    'callsign': 'KC1ABC',
                    'name': 'John Doe',
                    'address': '123 Main St, City, State, Country',
                    'image': None,
                    'error': None
                }
            },
            {
                'callsign': 'KC2XYZ',
                'timestamp': '2024-01-01T12:01:00Z',
                'position': 2,
                'qrz': {
                    'callsign': 'KC2XYZ',
                    'name': 'Jane Smith',
                    'address': '456 Oak Ave, Town, State, Country',
                    'image': 'http://example.com/image2.jpg',
                    'error': None
                }
            }
        ]
        mock_db.get_queue_list.return_value = mock_queue
        
        # Make queue list request
        response = test_client.get('/api/queue/list')
        
        # Verify response includes stored QRZ information for all entries
        assert response.status_code == 200
        data = response.json()
        assert data['system_active'] is True
        assert data['total'] == 2
        assert len(data['queue']) == 2
        
        # Check first entry
        entry1 = data['queue'][0]
        assert entry1['callsign'] == 'KC1ABC'
        assert entry1['qrz']['name'] == 'John Doe'
        
        # Check second entry
        entry2 = data['queue'][1]
        assert entry2['callsign'] == 'KC2XYZ'
        assert entry2['qrz']['name'] == 'Jane Smith'
        
        # Verify only database was queried
        mock_db.get_queue_list.assert_called_once()
    
    @patch('app.routes.queue.queue_db')
    @patch('app.routes.queue.qrz_service')
    def test_register_callsign_handles_qrz_failure(self, mock_qrz_service, mock_db, test_client):
        """Test that registration continues even if QRZ lookup fails"""
        # Mock active system status
        mock_db.get_system_status.return_value = {'active': True}
        
        # Mock QRZ service failure
        mock_qrz_info = {
            'callsign': 'KC1ABC',
            'name': None,
            'address': None,
            'image': None,
            'error': 'QRZ.com credentials not configured. Please set QRZ_USERNAME and QRZ_PASSWORD environment variables.'
        }
        mock_qrz_service.lookup_callsign.return_value = mock_qrz_info
        
        # Mock database registration response
        mock_entry = {
            'callsign': 'KC1ABC',
            'timestamp': '2024-01-01T12:00:00Z',
            'position': 1,
            'qrz': mock_qrz_info
        }
        mock_db.register_callsign.return_value = mock_entry
        
        # Make registration request
        response = test_client.post('/api/queue/register', json={'callsign': 'KC1ABC'})
        
        # Verify response - registration should succeed even with QRZ failure
        assert response.status_code == 200
        data = response.json()
        assert data['message'] == 'Callsign registered successfully'
        assert data['entry']['callsign'] == 'KC1ABC'
        assert data['entry']['qrz']['error'] is not None
        
        # Verify QRZ service was called and database was updated with error info
        mock_qrz_service.lookup_callsign.assert_called_once_with('KC1ABC')
        mock_db.register_callsign.assert_called_once_with('KC1ABC', mock_qrz_info)


class TestQRZRedundancyElimination:
    """Test that redundant QRZ API calls are eliminated"""
    
    @patch('app.routes.queue.qrz_service')
    def test_no_qrz_api_calls_after_registration(self, mock_qrz_service, test_client):
        """Test that no QRZ API calls are made after registration"""
        with patch('app.routes.queue.queue_db') as mock_db:
            # Mock active system status
            mock_db.get_system_status.return_value = {'active': True}
            
            # Mock stored entry with QRZ data
            mock_entry = {
                'callsign': 'KC1ABC',
                'timestamp': '2024-01-01T12:00:00Z',
                'position': 1,
                'qrz': {
                    'callsign': 'KC1ABC',
                    'name': 'John Doe',
                    'address': '123 Main St',
                    'image': None,
                    'error': None
                }
            }
            mock_db.find_callsign.return_value = mock_entry
            mock_db.get_current_qso.return_value = mock_entry
            mock_db.get_queue_list.return_value = [mock_entry]
            
            # Make multiple requests that previously would have triggered QRZ API calls
            test_client.get('/api/queue/status/KC1ABC')
            test_client.get('/api/queue/current')
            test_client.get('/api/queue/list')
            
            # Verify no QRZ API calls were made
            mock_qrz_service.lookup_callsign.assert_not_called()


class TestQRZGridFunctionality:
    """Test QRZ grid/coordinates functionality"""
    
    @patch('app.services.qrz.qrz_service')
    def test_qrz_lookup_returns_grid_info(self, mock_qrz_service):
        """Test that QRZ lookup returns grid coordinates"""
        from app.services.qrz import QRZService
        
        # Create a real QRZ service instance to test grid extraction
        qrz_service = QRZService()
        
        # Mock the client search result
        mock_result = Mock()
        mock_result.name.formatted_name = "John Doe"
        mock_result.address.line1 = "123 Main St"
        mock_result.address.line2 = None
        mock_result.address.city = "Boston"
        mock_result.address.state = "MA"
        mock_result.address.country = "United States"
        mock_result.address.zip = "02101"
        mock_result.dxcc.name = "United States"
        mock_result.image.url = "http://example.com/image.jpg"
        mock_result.grid = "FN42ko"
        mock_result.latlong.lat = 42.3601
        mock_result.latlong.long = -71.0589
        
        # Test grid extraction
        grid_info = qrz_service._extract_grid_info(mock_result)
        
        assert grid_info['lat'] == 42.3601
        assert grid_info['long'] == -71.0589
        assert grid_info['grid'] == 'FN42ko'
    
    @patch('app.services.qrz.qrz_service')
    def test_qrz_lookup_handles_missing_grid_info(self, mock_qrz_service):
        """Test that QRZ lookup handles missing grid information gracefully"""
        from app.services.qrz import QRZService
        
        # Create a real QRZ service instance to test grid extraction
        qrz_service = QRZService()
        
        # Mock the client search result with missing grid data
        mock_result = Mock()
        mock_result.name.formatted_name = "John Doe"
        mock_result.address.line1 = "123 Main St"
        mock_result.address.line2 = None
        mock_result.address.city = "Boston"
        mock_result.address.state = "MA"
        mock_result.address.country = "United States"
        mock_result.address.zip = "02101"
        mock_result.dxcc.name = "United States"
        mock_result.image.url = "http://example.com/image.jpg"
        mock_result.grid = None
        mock_result.latlong = None
        
        # Test grid extraction with missing data
        grid_info = qrz_service._extract_grid_info(mock_result)
        
        assert grid_info['lat'] is None
        assert grid_info['long'] is None
        assert grid_info['grid'] is None
    
    @patch('app.database.queue_db')
    def test_worked_caller_stores_grid_info(self, mock_db):
        """Test that worked callers store grid information"""
        from app.database import QueueDatabase
        
        # Mock the database
        db = QueueDatabase()
        db.worked_callers_collection = Mock()
        db.worked_callers_collection.find_one.return_value = None  # No existing entry
        db.worked_callers_collection.insert_one.return_value = Mock()
        
        # Test QRZ info with grid data
        qrz_info = {
            'callsign': 'KC1ABC',
            'name': 'John Doe',
            'address': 'Boston, MA',
            'dxcc_name': 'United States',
            'image': 'http://example.com/image.jpg',
            'grid': {
                'lat': 42.3601,
                'long': -71.0589,
                'grid': 'FN42ko'
            },
            'error': None
        }
        
        # Add worked caller
        result = db.add_worked_caller('KC1ABC', qrz_info)
        
        # Verify grid info is included
        assert result['grid']['lat'] == 42.3601
        assert result['grid']['long'] == -71.0589
        assert result['grid']['grid'] == 'FN42ko'
        
        # Verify database insert was called with grid info
        db.worked_callers_collection.insert_one.assert_called_once()
        call_args = db.worked_callers_collection.insert_one.call_args[0][0]
        assert call_args['grid']['lat'] == 42.3601
        assert call_args['grid']['long'] == -71.0589
        assert call_args['grid']['grid'] == 'FN42ko'