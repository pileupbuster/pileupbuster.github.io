"""
Test to verify that both queue and current QSO are cleared when system is deactivated
"""
import pytest
import os
from unittest.mock import patch
from fastapi.testclient import TestClient
from app.app import create_app


@pytest.fixture
def real_test_client():
    """Create a test client with real database but test environment variables"""
    app = create_app()
    
    # Set admin credentials for testing
    with patch.dict(os.environ, {
        'ADMIN_USERNAME': 'admin', 
        'ADMIN_PASSWORD': 'admin',
        'MONGO_URI': 'mongodb://localhost:27017/pileup_buster_test'
    }):
        with TestClient(app) as client:
            yield client


def test_complete_system_clearing_on_deactivation(real_test_client):
    """Test that both queue and current QSO are cleared when system is deactivated"""
    client = real_test_client
    
    # First activate the system
    response = client.post(
        '/api/admin/status',
        json={'active': True},
        auth=('admin', 'admin')
    )
    assert response.status_code == 200
    print(f"Activation response: {response.json()}")
    
    # Add some callsigns to the queue
    callsigns = ['W1ABC', 'K2DEF', 'KC3GHI']
    for callsign in callsigns:
        response = client.post('/api/queue/register', json={'callsign': callsign})
        print(f"Registration response for {callsign}: {response.status_code}")
    
    # Verify queue has entries
    response = client.get('/api/admin/queue', auth=('admin', 'admin'))
    assert response.status_code == 200
    queue_data = response.json()
    print(f"Queue before processing: {len(queue_data['queue'])} entries")
    assert len(queue_data['queue']) == len(callsigns)
    
    # Process the next callsign to create a current QSO
    response = client.post('/api/admin/queue/next', auth=('admin', 'admin'))
    print(f"Next callsign response: {response.status_code}, {response.json()}")
    assert response.status_code == 200
    current_qso = response.json()
    assert current_qso is not None
    assert current_qso['callsign'] in callsigns
    
    # Verify we now have a current QSO
    response = client.get('/api/admin/current', auth=('admin', 'admin'))
    print(f"Current QSO before deactivation: {response.json()}")
    assert response.status_code == 200
    assert response.json() is not None
    
    # Verify queue now has one less entry
    response = client.get('/api/admin/queue', auth=('admin', 'admin'))
    assert response.status_code == 200
    queue_data = response.json()
    print(f"Queue after processing next: {len(queue_data['queue'])} entries")
    assert len(queue_data['queue']) == len(callsigns) - 1
    
    # Now deactivate the system (this should clear both queue and current QSO)
    response = client.post(
        '/api/admin/status',
        json={'active': False},
        auth=('admin', 'admin')
    )
    assert response.status_code == 200
    deactivation_data = response.json()
    print(f"Deactivation response: {deactivation_data}")
    
    # Check that the response indicates both queue and QSO were cleared
    assert 'Queue cleared' in deactivation_data['message']
    assert 'Current QSO cleared' in deactivation_data['message']
    assert deactivation_data['status']['queue_cleared'] is True
    assert deactivation_data['status']['qso_cleared'] is True
    
    # Verify queue is now empty
    response = client.get('/api/admin/queue', auth=('admin', 'admin'))
    assert response.status_code == 200
    queue_data = response.json()
    print(f"Queue after deactivation: {len(queue_data['queue'])} entries")
    assert len(queue_data['queue']) == 0
    
    # Verify current QSO is now empty
    response = client.get('/api/admin/current', auth=('admin', 'admin'))
    print(f"Current QSO after deactivation: {response.json()}")
    assert response.status_code == 200
    assert response.json() is None


if __name__ == '__main__':
    pytest.main([__file__, '-v', '-s'])
