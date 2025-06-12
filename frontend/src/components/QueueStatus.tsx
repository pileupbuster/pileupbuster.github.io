import React, { useState, useEffect, useCallback } from 'react';
import { queueApi } from '../services/api';
import { QueueEntry, LoadingState } from '../types';

interface QueueStatusProps {
  userCallsign?: string;
  refreshInterval?: number;
}

const QueueStatus: React.FC<QueueStatusProps> = ({ 
  userCallsign, 
  refreshInterval = 30000 // 30 seconds
}) => {
  const [queue, setQueue] = useState<QueueEntry[]>([]);
  const [userEntry, setUserEntry] = useState<QueueEntry | null>(null);
  const [loadingState, setLoadingState] = useState<LoadingState>({ isLoading: true });

  const fetchQueueData = useCallback(async () => {
    try {
      const queueResponse = await queueApi.getList();
      setQueue(queueResponse.queue);

      // If user has a callsign, fetch their specific status
      if (userCallsign) {
        try {
          const userStatus = await queueApi.getStatus(userCallsign);
          setUserEntry(userStatus);
        } catch (error: any) {
          if (error.status === 404) {
            setUserEntry(null); // User not in queue
          }
        }
      }

      setLoadingState({ isLoading: false });
    } catch (error: any) {
      setLoadingState({ 
        isLoading: false, 
        error: error.message || 'Failed to load queue data' 
      });
    }
  }, [userCallsign]);

  useEffect(() => {
    fetchQueueData();

    const interval = setInterval(fetchQueueData, refreshInterval);
    return () => clearInterval(interval);
  }, [fetchQueueData, refreshInterval]);

  if (loadingState.isLoading) {
    return (
      <div className="card">
        <div className="card-header">
          <h3 className="card-title">
            <span className="spinner" /> Loading Queue Status...
          </h3>
        </div>
      </div>
    );
  }

  if (loadingState.error) {
    return (
      <div className="card">
        <div className="alert alert-error">
          {loadingState.error}
        </div>
        <button 
          onClick={fetchQueueData} 
          className="btn btn-secondary"
        >
          Retry
        </button>
      </div>
    );
  }

  return (
    <div className="card">
      <div className="card-header">
        <h3 className="card-title">Queue Status</h3>
        <p className="card-description">
          {queue.length === 0 
            ? 'Queue is empty' 
            : `${queue.length} callsign${queue.length === 1 ? '' : 's'} in queue`
          }
        </p>
      </div>

      {userEntry && (
        <div className="alert alert-info">
          <strong>{userEntry.callsign}</strong> - You are position{' '}
          <strong>#{userEntry.position}</strong> in the queue
          {userEntry.qrz?.name && (
            <>
              <br />
              <small>Name: {userEntry.qrz.name}</small>
            </>
          )}
        </div>
      )}

      {queue.length > 0 ? (
        <div className="table-container">
          <table className="table">
            <thead>
              <tr>
                <th>Position</th>
                <th>Callsign</th>
                <th>Name</th>
                <th>Joined</th>
              </tr>
            </thead>
            <tbody>
              {queue.map((entry) => (
                <tr 
                  key={entry.callsign}
                  style={{
                    backgroundColor: entry.callsign === userCallsign ? '#eff6ff' : undefined
                  }}
                >
                  <td>
                    <span className="badge badge-primary">
                      #{entry.position}
                    </span>
                  </td>
                  <td>
                    <strong>{entry.callsign}</strong>
                  </td>
                  <td>
                    {entry.qrz?.name || 'Loading...'}
                  </td>
                  <td>
                    <small>
                      {new Date(entry.timestamp).toLocaleTimeString()}
                    </small>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ) : (
        <div style={{ textAlign: 'center', padding: '2rem', color: '#64748b' }}>
          <p>No callsigns in queue</p>
          <small>Be the first to register!</small>
        </div>
      )}

      <div style={{ 
        marginTop: '1rem', 
        fontSize: '0.75rem', 
        color: '#94a3b8', 
        textAlign: 'center' 
      }}>
        Last updated: {new Date().toLocaleTimeString()} • Auto-refreshing every 30s
      </div>
    </div>
  );
};

export default QueueStatus;