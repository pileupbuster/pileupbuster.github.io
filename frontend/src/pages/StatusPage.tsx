import React, { useState, useEffect, useCallback } from 'react';
import { queueApi } from '../services/api';
import { QueueEntry, LoadingState } from '../types';

interface StatusPageProps {
  userCallsign: string;
}

const StatusPage: React.FC<StatusPageProps> = ({ userCallsign }) => {
  const [userEntry, setUserEntry] = useState<QueueEntry | null>(null);
  const [loadingState, setLoadingState] = useState<LoadingState>({ isLoading: true });

  const fetchUserStatus = useCallback(async () => {
    setLoadingState({ isLoading: true });
    
    try {
      const status = await queueApi.getStatus(userCallsign);
      setUserEntry(status);
      setLoadingState({ isLoading: false });
    } catch (error: any) {
      if (error.status === 404) {
        setUserEntry(null);
        setLoadingState({ 
          isLoading: false, 
          error: 'Callsign not found in queue. You may have been processed or removed.' 
        });
      } else {
        setLoadingState({ 
          isLoading: false, 
          error: error.message || 'Failed to load status' 
        });
      }
    }
  }, [userCallsign]);

  useEffect(() => {
    fetchUserStatus();
    
    const interval = setInterval(fetchUserStatus, 15000); // Refresh every 15 seconds
    return () => clearInterval(interval);
  }, [fetchUserStatus]);

  if (loadingState.isLoading) {
    return (
      <div className="container">
        <div className="page">
          <div className="card">
            <div className="card-header">
              <h3 className="card-title">
                <span className="spinner" /> Loading Your Status...
              </h3>
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="container">
      <div className="page">
        <div style={{ textAlign: 'center', marginBottom: '2rem' }}>
          <h1>Queue Status for {userCallsign}</h1>
        </div>

        {loadingState.error ? (
          <div className="card">
            <div className="alert alert-warning">
              {loadingState.error}
            </div>
            <button 
              onClick={fetchUserStatus} 
              className="btn btn-primary"
            >
              Check Again
            </button>
          </div>
        ) : userEntry ? (
          <div>
            {/* Main Status Card */}
            <div className="card">
              <div className="card-header">
                <h3 className="card-title">Your Position</h3>
              </div>
              
              <div style={{ textAlign: 'center', padding: '2rem' }}>
                <div style={{ 
                  fontSize: '4rem', 
                  fontWeight: 'bold', 
                  color: '#3b82f6',
                  marginBottom: '1rem'
                }}>
                  #{userEntry.position}
                </div>
                
                <p style={{ fontSize: '1.25rem', marginBottom: '1rem' }}>
                  You are position <strong>#{userEntry.position}</strong> in the queue
                </p>
                
                <div style={{ 
                  background: '#eff6ff', 
                  padding: '1rem', 
                  borderRadius: '8px',
                  marginBottom: '1rem'
                }}>
                  <p style={{ color: '#1e40af', fontWeight: '500' }}>
                    {userEntry.position === 1 
                      ? "You're next! Get ready for your callback."
                      : userEntry.position <= 3 
                        ? "You're coming up soon!"
                        : `${userEntry.position - 1} callsign${userEntry.position - 1 === 1 ? '' : 's'} ahead of you`
                    }
                  </p>
                </div>

                <p style={{ color: '#64748b', fontSize: '0.875rem' }}>
                  Joined at {new Date(userEntry.timestamp).toLocaleString()}
                </p>
              </div>
            </div>

            {/* QRZ Information */}
            {userEntry.qrz && (
              <div className="card">
                <div className="card-header">
                  <h3 className="card-title">QRZ.com Information</h3>
                </div>
                
                {userEntry.qrz.error ? (
                  <div className="alert alert-warning">
                    QRZ Lookup: {userEntry.qrz.error}
                  </div>
                ) : (
                  <div style={{ 
                    display: 'grid', 
                    gap: '1rem',
                    gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))'
                  }}>
                    {userEntry.qrz.name && (
                      <div>
                        <strong>Name:</strong>
                        <p>{userEntry.qrz.name}</p>
                      </div>
                    )}
                    
                    {userEntry.qrz.license_class && (
                      <div>
                        <strong>License Class:</strong>
                        <p>{userEntry.qrz.license_class}</p>
                      </div>
                    )}
                    
                    {userEntry.qrz.country && (
                      <div>
                        <strong>Country:</strong>
                        <p>{userEntry.qrz.country}</p>
                      </div>
                    )}
                    
                    {userEntry.qrz.address && (
                      <div>
                        <strong>Address:</strong>
                        <p>{userEntry.qrz.address}</p>
                      </div>
                    )}
                  </div>
                )}
              </div>
            )}
          </div>
        ) : (
          <div className="card">
            <div style={{ textAlign: 'center', padding: '2rem' }}>
              <h3>Not in Queue</h3>
              <p style={{ color: '#64748b', marginBottom: '1.5rem' }}>
                {userCallsign} is not currently in the queue
              </p>
            </div>
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
  );
};

export default StatusPage;