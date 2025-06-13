"""
Test to check admin queue behavior during system deactivation
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


def test_admin_queue_behavior_during_deactivation(real_test_client):
    """Test admin queue endpoint behavior during system deactivation"""
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
    callsigns = ['W1TEST', 'K2TEST']
    for callsign in callsigns:
        response = client.post('/api/queue/register', json={'callsign': callsign})
        print(f"Registration response for {callsign}: {response.status_code}")
    
    # Check admin queue before deactivation
    response = client.get('/api/admin/queue', auth=('admin', 'admin'))
    assert response.status_code == 200
    admin_queue_before = response.json()
    print(f"Admin queue before deactivation: {admin_queue_before}")
    assert len(admin_queue_before['queue']) == len(callsigns)
    
    # Check public queue before deactivation (should show entries)
    response = client.get('/api/queue/list')
    assert response.status_code == 200
    public_queue_before = response.json()
    print(f"Public queue before deactivation: {public_queue_before}")
    assert len(public_queue_before['queue']) == len(callsigns)
    assert public_queue_before['system_active'] is True
    
    # Now deactivate the system
    response = client.post(
        '/api/admin/status',
        json={'active': False},
        auth=('admin', 'admin')
    )
    assert response.status_code == 200
    deactivation_data = response.json()
    print(f"Deactivation response: {deactivation_data}")
    
    # Check admin queue after deactivation (should be empty if clear worked)
    response = client.get('/api/admin/queue', auth=('admin', 'admin'))
    assert response.status_code == 200
    admin_queue_after = response.json()
    print(f"Admin queue after deactivation: {admin_queue_after}")
    
    # Check public queue after deactivation (should be empty due to inactive system)
    response = client.get('/api/queue/list')
    assert response.status_code == 200
    public_queue_after = response.json()
    print(f"Public queue after deactivation: {public_queue_after}")
    assert len(public_queue_after['queue']) == 0
    assert public_queue_after['system_active'] is False
    
    # This is the key test - admin queue should also be empty if clearing worked
    if len(admin_queue_after['queue']) > 0:
        print("ERROR: Admin queue still has entries after deactivation!")
        print(f"Entries still in queue: {admin_queue_after['queue']}")
        assert False, "Queue was not properly cleared during deactivation"
    else:
        print("SUCCESS: Admin queue is properly cleared after deactivation")


if __name__ == '__main__':
    pytest.main([__file__, '-v', '-s'])
