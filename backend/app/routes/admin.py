from flask import Blueprint, request, jsonify
from app.routes.queue import queue_storage

admin_bp = Blueprint('admin', __name__)

@admin_bp.route('/queue', methods=['GET'])
def admin_queue():
    """Admin view of the queue"""
    # Update positions
    for i, entry in enumerate(queue_storage):
        entry['position'] = i + 1
    
    return jsonify({
        'queue': queue_storage,
        'total': len(queue_storage),
        'admin': True
    })

@admin_bp.route('/queue/<callsign>', methods=['DELETE'])
def remove_callsign(callsign):
    """Remove a callsign from the queue"""
    callsign = callsign.upper().strip()
    
    for i, entry in enumerate(queue_storage):
        if entry['callsign'] == callsign:
            removed_entry = queue_storage.pop(i)
            return jsonify({
                'message': f'Callsign {callsign} removed from queue',
                'removed': removed_entry
            })
    
    return jsonify({'error': 'Callsign not found in queue'}), 404

@admin_bp.route('/queue/clear', methods=['POST'])
def clear_queue():
    """Clear the entire queue"""
    global queue_storage
    count = len(queue_storage)
    queue_storage = []
    
    return jsonify({
        'message': f'Queue cleared. Removed {count} entries.',
        'cleared_count': count
    })

@admin_bp.route('/queue/next', methods=['POST'])
def next_callsign():
    """Process the next callsign in queue"""
    if not queue_storage:
        return jsonify({'error': 'Queue is empty'}), 400
    
    next_entry = queue_storage.pop(0)
    return jsonify({
        'message': f'Next callsign: {next_entry["callsign"]}',
        'processed': next_entry,
        'remaining': len(queue_storage)
    })