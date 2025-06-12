import React, { useState } from 'react';
import { queueApi } from '../services/api';
import { LoadingState } from '../types';

interface CallsignFormProps {
  onSuccess?: (callsign: string, position: number) => void;
}

const CallsignForm: React.FC<CallsignFormProps> = ({ onSuccess }) => {
  const [callsign, setCallsign] = useState('');
  const [loadingState, setLoadingState] = useState<LoadingState>({ isLoading: false });

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!callsign.trim()) {
      setLoadingState({ isLoading: false, error: 'Please enter a callsign' });
      return;
    }

    setLoadingState({ isLoading: true });

    try {
      const response = await queueApi.register(callsign.trim());
      setLoadingState({ isLoading: false });
      setCallsign('');
      
      if (onSuccess) {
        onSuccess(response.entry.callsign, response.entry.position);
      }
    } catch (error: any) {
      setLoadingState({ 
        isLoading: false, 
        error: error.message || 'Failed to register callsign' 
      });
    }
  };

  return (
    <div className="card">
      <div className="card-header">
        <h3 className="card-title">Register Your Callsign</h3>
        <p className="card-description">
          Enter your callsign to join the queue for callback
        </p>
      </div>

      <form onSubmit={handleSubmit} className="form">
        <div className="form-group">
          <label htmlFor="callsign" className="form-label">
            Callsign
          </label>
          <input
            id="callsign"
            type="text"
            value={callsign}
            onChange={(e) => {
              setCallsign(e.target.value.toUpperCase());
              if (loadingState.error) {
                setLoadingState({ isLoading: false });
              }
            }}
            className={`form-input ${loadingState.error ? 'error' : ''}`}
            placeholder="e.g., W1AW"
            disabled={loadingState.isLoading}
            maxLength={20}
          />
        </div>

        {loadingState.error && (
          <div className="alert alert-error">
            {loadingState.error}
          </div>
        )}

        <button
          type="submit"
          className="btn btn-primary btn-lg"
          disabled={loadingState.isLoading || !callsign.trim()}
        >
          {loadingState.isLoading ? (
            <>
              <span className="spinner" />
              Registering...
            </>
          ) : (
            'Register Callsign'
          )}
        </button>
      </form>
    </div>
  );
};

export default CallsignForm;