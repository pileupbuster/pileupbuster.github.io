import { useEffect, useState } from 'react';
import { apiService, ApiError } from '../services/api';

interface QueueItem {
  callsign: string;
  name?: string;
  timeInQueue: number;
  address?: string;
  grid?: {
    lat?: number;
    long?: number;
    grid?: string;
  };
  image?: string;
  dxcc_name?: string;
  location?: string;
  waitTime?: string;
}

interface QueueBarProps {
  queue: QueueItem[];
}

function QueueBar({ queue }: QueueBarProps) {
  const [timers, setTimers] = useState<Record<string, string>>({});
  const [showAddModal, setShowAddModal] = useState(false);
  const [newCallsign, setNewCallsign] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState('');

  // Format time in queue as MM:SS
  const formatTime = (seconds: number): string => {
    const minutes = Math.floor(seconds / 60);
    const remainingSeconds = seconds % 60;
    return `${minutes.toString().padStart(2, '0')}:${remainingSeconds.toString().padStart(2, '0')}`;
  };

  const validateCallsign = (callsign: string): string | null => {
    if (!callsign.trim()) {
      return 'Please enter a callsign';
    }
    
    // Basic callsign validation - simplified ITU format
    const callsignPattern = /^[A-Z0-9]{1,3}[0-9][A-Z0-9]{0,3}[A-Z]$/;
    if (!callsignPattern.test(callsign.trim().toUpperCase())) {
      return 'Invalid callsign format (e.g., W1ABC, KC1XYZ)';
    }
    
    return null;
  };

  const handleAddCallsign = async (event: React.FormEvent) => {
    event.preventDefault();
    
    const validationError = validateCallsign(newCallsign);
    if (validationError) {
      setError(validationError);
      return;
    }

    setIsSubmitting(true);
    setError('');

    try {
      await apiService.registerCallsign(newCallsign.trim().toUpperCase());
      setNewCallsign('');
      setShowAddModal(false);
    } catch (err) {
      if (err instanceof ApiError) {
        setError(err.detail || err.message);
      } else if (err instanceof Error) {
        setError(err.message);
      } else {
        setError('Failed to add callsign to queue');
      }
    } finally {
      setIsSubmitting(false);
    }
  };

  const handlePlaceholderClick = () => {
    setShowAddModal(true);
    setError('');
  };

  const handleCallsignChange = (value: string) => {
    const upperValue = value.toUpperCase();
    setNewCallsign(upperValue);
    
    // Clear error when user starts typing
    if (error) {
      setError('');
    }
  };

  const handleModalClose = () => {
    setShowAddModal(false);
    setNewCallsign('');
    setError('');
  };

  useEffect(() => {
    const interval = setInterval(() => {
      const now = Date.now();
      const newTimers: Record<string, string> = {};
      
      queue.forEach(item => {
        const timeInQueueSeconds = Math.floor((now - item.timeInQueue) / 1000);
        newTimers[item.callsign] = formatTime(timeInQueueSeconds);
      });
      
      setTimers(newTimers);
    }, 1000);

    return () => clearInterval(interval);
  }, [queue]);

  // Create array for queue display: working right to left, first person in queue on the right
  // We'll show only one empty slot if queue size < 4
  const displayItems = [];
  
  // Reverse the queue so first person appears on the right
  const reversedQueue = [...queue].reverse();
  
  // Add actual queue items (up to 4)
  for (let i = 0; i < Math.min(4, reversedQueue.length); i++) {
    const item = reversedQueue[i];
    const originalPosition = queue.length - 1 - i; // Calculate original position in queue (0 = first in queue)
    
    displayItems.push(
      <div key={item.callsign} className="queue-card" data-position={originalPosition}>
        <img 
          src={item.image || `https://i.pravatar.cc/150?img=${Math.floor(Math.random() * 70)}`} 
          alt={item.callsign} 
          className="queue-image" 
        />
        <div className="queue-info">
          <h3 className="queue-callsign">{item.callsign}</h3>
          <p className="queue-location">
            {item.location || item.address || item.dxcc_name || 'Unknown'}
          </p>
          <p className="queue-time">
            {timers[item.callsign] || '00:00'}
          </p>
        </div>
      </div>
    );
  }
  
  // Add one empty slot if queue is not full (only show one empty slot)
  if (queue.length < 4) {
    displayItems.unshift(
      <div 
        key="empty-slot" 
        className="queue-card placeholder" 
        data-position="empty"
        onClick={handlePlaceholderClick}
        style={{ cursor: 'pointer' }}
      >
        <div className="queue-placeholder-icon">➕</div>
        <div className="queue-info">
          <h3 className="queue-callsign" style={{ color: 'rgba(255,255,255,0.4)' }}>
            Add Station
          </h3>
          <p className="queue-location" style={{ color: 'rgba(255,255,255,0.3)' }}>
            Click to add
          </p>
          <p className="queue-time" style={{ color: 'rgba(255,255,255,0.3)' }}>
            --:--
          </p>
        </div>
      </div>
    );
  }

  return (
    <>
      <div className="bottom-queue">
        {displayItems}
      </div>
      
      {showAddModal && (
        <div className="modal-overlay" onClick={handleModalClose}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <h2>Add Callsign to Queue</h2>
            <form onSubmit={handleAddCallsign}>
              <div className="input-group">
                <label htmlFor="callsign">Callsign:</label>
                <input
                  id="callsign"
                  type="text"
                  value={newCallsign}
                  onChange={(e) => handleCallsignChange(e.target.value)}
                  placeholder="Enter callsign (e.g., W1ABC)"
                  disabled={isSubmitting}
                  autoFocus
                  maxLength={10}
                />
              </div>
              
              {error && <div className="error-message">{error}</div>}
              
              <div className="modal-actions">
                <button 
                  type="button" 
                  onClick={handleModalClose}
                  disabled={isSubmitting}
                  className="btn-secondary"
                >
                  Cancel
                </button>
                <button 
                  type="submit" 
                  disabled={isSubmitting || !newCallsign.trim() || !!validateCallsign(newCallsign)}
                  className="btn-primary"
                >
                  {isSubmitting ? 'Adding...' : 'Add to Queue'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </>
  );
}

export default QueueBar;
