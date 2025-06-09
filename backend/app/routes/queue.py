from flask import Blueprint, request, jsonify
from datetime import datetime

queue_bp = Blueprint('queue', __name__)

# In-memory storage for demo purposes
# In production, this would use MongoDB
queue_storage = []

@queue_bp.route('/register', methods=['POST'])
def register_callsign():
    """Register a callsign in the queue"""
    data = request.get_json()
    callsign = data.get('callsign', '').upper().strip()
    
    if not callsign:
        return jsonify({'error': 'Callsign is required'}), 400
    
    # Check if callsign already in queue
    for entry in queue_storage:
        if entry['callsign'] == callsign:
            return jsonify({'error': 'Callsign already in queue'}), 400
    
    # Add to queue
    entry = {
        'callsign': callsign,
        'timestamp': datetime.utcnow().isoformat(),
        'position': len(queue_storage) + 1
    }
    queue_storage.append(entry)
    
    return jsonify({'message': 'Callsign registered successfully', 'entry': entry}), 201

@queue_bp.route('/status/<callsign>', methods=['GET'])
def get_status(callsign):
    """Get position of callsign in queue"""
    callsign = callsign.upper().strip()
    
    for i, entry in enumerate(queue_storage):
        if entry['callsign'] == callsign:
            entry['position'] = i + 1
            return jsonify(entry)
    
    return jsonify({'error': 'Callsign not found in queue'}), 404

@queue_bp.route('/list', methods=['GET'])
def list_queue():
    """Get current queue status"""
    # Update positions
    for i, entry in enumerate(queue_storage):
        entry['position'] = i + 1
    
    return jsonify({'queue': queue_storage, 'total': len(queue_storage)})