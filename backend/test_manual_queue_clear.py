"""
Test to reproduce the issue where setting system to inactive doesn't clear the queue
"""
import pytest
import os
from unittest.mock import patch
from fastapi.testclient import TestClient
from app.app import create_app
from app.database import QueueDatabase


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


def test_system_deactivation_clears_queue_real_integration(real_test_client):
    """Test that deactivating the system actually clears the queue in real integration"""
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
        print(f"Registration response for {callsign}: {response.status_code}, {response.json()}")
    
    # Verify queue has entries
    response = client.get('/api/queue/list')
    assert response.status_code == 200
    queue_data = response.json()
    print(f"Queue before deactivation: {queue_data}")
    assert len(queue_data['queue']) == len(callsigns)
    
    # Now deactivate the system (this should clear the queue)
    response = client.post(
        '/api/admin/status',
        json={'active': False},
        auth=('admin', 'admin')
    )
    assert response.status_code == 200
    deactivation_data = response.json()
    print(f"Deactivation response: {deactivation_data}")
    
    # Check if queue was cleared according to the response
    assert 'Queue cleared' in deactivation_data['message']
    assert deactivation_data['status']['cleared_count'] == len(callsigns)
    
    # Verify queue is actually empty now
    response = client.get('/api/queue/list')
    assert response.status_code == 200
    queue_data = response.json()
    print(f"Queue after deactivation: {queue_data}")
    assert len(queue_data['queue']) == 0


if __name__ == '__main__':
    pytest.main([__file__, '-v', '-s'])
