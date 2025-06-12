import React, { useState, useEffect, useCallback } from 'react';
import { adminApi } from '../services/api';
import { QueueEntry, AdminCredentials, LoadingState } from '../types';

interface AdminDashboardProps {
  credentials: AdminCredentials;
  onLogout: () => void;
}

const AdminDashboard: React.FC<AdminDashboardProps> = ({ credentials, onLogout }) => {
  const [queue, setQueue] = useState<QueueEntry[]>([]);
  const [loadingState, setLoadingState] = useState<LoadingState>({ isLoading: true });
  const [actionLoading, setActionLoading] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string>('');

  const fetchQueue = useCallback(async () => {
    try {
      const response = await adminApi.getQueue(credentials);
      setQueue(response.queue);
      setLoadingState({ isLoading: false });
    } catch (error: any) {
      if (error.status === 401) {
        onLogout(); // Invalid credentials
        return;
      }
      setLoadingState({ 
        isLoading: false, 
        error: error.message || 'Failed to load queue' 
      });
    }
  }, [credentials, onLogout]);

  useEffect(() => {
    fetchQueue();
    
    const interval = setInterval(fetchQueue, 15000); // Refresh every 15 seconds
    return () => clearInterval(interval);
  }, [fetchQueue]);

  const handleRemoveCallsign = async (callsign: string) => {
    setActionLoading(`remove-${callsign}`);
    
    try {
      const response = await adminApi.removeCallsign(callsign, credentials);
      setSuccessMessage(response.message);
      fetchQueue(); // Refresh the queue
      
      setTimeout(() => setSuccessMessage(''), 3000);
    } catch (error: any) {
      setLoadingState({ isLoading: false, error: error.message });
    } finally {
      setActionLoading(null);
    }
  };

  const handleClearQueue = async () => {
    if (!window.confirm('Are you sure you want to clear the entire queue? This action cannot be undone.')) {
      return;
    }

    setActionLoading('clear');
    
    try {
      const response = await adminApi.clearQueue(credentials);
      setSuccessMessage(response.message);
      fetchQueue(); // Refresh the queue
      
      setTimeout(() => setSuccessMessage(''), 3000);
    } catch (error: any) {
      setLoadingState({ isLoading: false, error: error.message });
    } finally {
      setActionLoading(null);
    }
  };

  const handleProcessNext = async () => {
    setActionLoading('next');
    
    try {
      const response = await adminApi.processNext(credentials);
      setSuccessMessage(response.message);
      fetchQueue(); // Refresh the queue
      
      setTimeout(() => setSuccessMessage(''), 5000);
    } catch (error: any) {
      setLoadingState({ isLoading: false, error: error.message });
    } finally {
      setActionLoading(null);
    }
  };

  if (loadingState.isLoading) {
    return (
      <div className="card">
        <div className="card-header">
          <h3 className="card-title">
            <span className="spinner" /> Loading Admin Dashboard...
          </h3>
        </div>
      </div>
    );
  }

  return (
    <div>
      {/* Header */}
      <div className="nav">
        <div className="container">
          <div className="nav-content">
            <div className="nav-brand">Admin Dashboard</div>
            <button onClick={onLogout} className="btn btn-secondary">
              Logout
            </button>
          </div>
        </div>
      </div>

      <div className="container">
        {/* Success Message */}
        {successMessage && (
          <div className="alert alert-success">
            {successMessage}
          </div>
        )}

        {/* Error Message */}
        {loadingState.error && (
          <div className="alert alert-error">
            {loadingState.error}
            <button 
              onClick={() => setLoadingState({ isLoading: false })} 
              className="btn btn-secondary btn-sm"
              style={{ marginLeft: '1rem' }}
            >
              Dismiss
            </button>
          </div>
        )}

        {/* Queue Actions */}
        <div className="card">
          <div className="card-header">
            <h3 className="card-title">Queue Management</h3>
            <p className="card-description">
              {queue.length === 0 
                ? 'Queue is empty' 
                : `${queue.length} callsign${queue.length === 1 ? '' : 's'} in queue`
              }
            </p>
          </div>

          <div style={{ display: 'flex', gap: '1rem', marginBottom: '1.5rem', flexWrap: 'wrap' }}>
            <button
              onClick={handleProcessNext}
              className="btn btn-success"
              disabled={queue.length === 0 || actionLoading !== null}
            >
              {actionLoading === 'next' ? (
                <>
                  <span className="spinner" />
                  Processing...
                </>
              ) : (
                'Process Next'
              )}
            </button>

            <button
              onClick={handleClearQueue}
              className="btn btn-warning"
              disabled={queue.length === 0 || actionLoading !== null}
            >
              {actionLoading === 'clear' ? (
                <>
                  <span className="spinner" />
                  Clearing...
                </>
              ) : (
                'Clear Queue'
              )}
            </button>

            <button
              onClick={fetchQueue}
              className="btn btn-secondary"
              disabled={actionLoading !== null}
            >
              Refresh
            </button>
          </div>

          {/* Queue Table */}
          {queue.length > 0 ? (
            <div className="table-container">
              <table className="table">
                <thead>
                  <tr>
                    <th>Position</th>
                    <th>Callsign</th>
                    <th>Name</th>
                    <th>Joined</th>
                    <th>QRZ Info</th>
                    <th>Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {queue.map((entry) => (
                    <tr key={entry.callsign}>
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
                          {new Date(entry.timestamp).toLocaleString()}
                        </small>
                      </td>
                      <td>
                        <small>
                          {entry.qrz?.license_class && (
                            <div>Class: {entry.qrz.license_class}</div>
                          )}
                          {entry.qrz?.country && (
                            <div>Country: {entry.qrz.country}</div>
                          )}
                          {entry.qrz?.error && (
                            <div style={{ color: '#ef4444' }}>
                              Error: {entry.qrz.error}
                            </div>
                          )}
                        </small>
                      </td>
                      <td>
                        <button
                          onClick={() => handleRemoveCallsign(entry.callsign)}
                          className="btn btn-error btn-sm"
                          disabled={actionLoading !== null}
                        >
                          {actionLoading === `remove-${entry.callsign}` ? (
                            <>
                              <span className="spinner" />
                              Removing...
                            </>
                          ) : (
                            'Remove'
                          )}
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            <div style={{ textAlign: 'center', padding: '2rem', color: '#64748b' }}>
              <p>No callsigns in queue</p>
              <small>Waiting for registrations...</small>
            </div>
          )}

          <div style={{ 
            marginTop: '1rem', 
            fontSize: '0.75rem', 
            color: '#94a3b8', 
            textAlign: 'center' 
          }}>
            Last updated: {new Date().toLocaleTimeString()} • Auto-refreshing every 15s
          </div>
        </div>
      </div>
    </div>
  );
};

export default AdminDashboard;