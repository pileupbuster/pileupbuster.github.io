import React, { useState } from 'react';
import { AdminCredentials } from '../types';

interface AdminLoginProps {
  onLogin: (credentials: AdminCredentials) => void;
  isLoading?: boolean;
  error?: string;
}

const AdminLogin: React.FC<AdminLoginProps> = ({ onLogin, isLoading, error }) => {
  const [credentials, setCredentials] = useState<AdminCredentials>({
    username: '',
    password: '',
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!credentials.username.trim() || !credentials.password.trim()) {
      return;
    }

    onLogin(credentials);
  };

  const handleInputChange = (field: keyof AdminCredentials) => (
    e: React.ChangeEvent<HTMLInputElement>
  ) => {
    setCredentials(prev => ({
      ...prev,
      [field]: e.target.value
    }));
  };

  return (
    <div className="card" style={{ maxWidth: '400px', margin: '2rem auto' }}>
      <div className="card-header">
        <h3 className="card-title">Admin Login</h3>
        <p className="card-description">
          Enter your admin credentials to access queue management
        </p>
      </div>

      <form onSubmit={handleSubmit} className="form">
        <div className="form-group">
          <label htmlFor="username" className="form-label">
            Username
          </label>
          <input
            id="username"
            type="text"
            value={credentials.username}
            onChange={handleInputChange('username')}
            className={`form-input ${error ? 'error' : ''}`}
            placeholder="Enter admin username"
            disabled={isLoading}
            required
          />
        </div>

        <div className="form-group">
          <label htmlFor="password" className="form-label">
            Password
          </label>
          <input
            id="password"
            type="password"
            value={credentials.password}
            onChange={handleInputChange('password')}
            className={`form-input ${error ? 'error' : ''}`}
            placeholder="Enter admin password"
            disabled={isLoading}
            required
          />
        </div>

        {error && (
          <div className="alert alert-error">
            {error}
          </div>
        )}

        <button
          type="submit"
          className="btn btn-primary btn-lg"
          disabled={
            isLoading || 
            !credentials.username.trim() || 
            !credentials.password.trim()
          }
        >
          {isLoading ? (
            <>
              <span className="spinner" />
              Logging in...
            </>
          ) : (
            'Login'
          )}
        </button>
      </form>
    </div>
  );
};

export default AdminLogin;