import React, { useState } from 'react';
import AdminLogin from '../components/AdminLogin';
import AdminDashboard from '../components/AdminDashboard';
import { AdminCredentials, LoadingState } from '../types';
import { adminApi } from '../services/api';

const AdminPage: React.FC = () => {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [credentials, setCredentials] = useState<AdminCredentials | null>(null);
  const [loadingState, setLoadingState] = useState<LoadingState>({ isLoading: false });

  const handleLogin = async (loginCredentials: AdminCredentials) => {
    setLoadingState({ isLoading: true });

    try {
      // Test credentials by making an API call
      await adminApi.getQueue(loginCredentials);
      
      setCredentials(loginCredentials);
      setIsAuthenticated(true);
      setLoadingState({ isLoading: false });
    } catch (error: any) {
      let errorMessage = 'Login failed';
      
      if (error.status === 401) {
        errorMessage = 'Invalid username or password';
      } else if (error.status === 503) {
        errorMessage = 'Admin authentication not configured on server';
      } else {
        errorMessage = error.message || 'Unable to connect to server';
      }

      setLoadingState({ 
        isLoading: false, 
        error: errorMessage 
      });
    }
  };

  const handleLogout = () => {
    setIsAuthenticated(false);
    setCredentials(null);
    setLoadingState({ isLoading: false });
  };

  if (isAuthenticated && credentials) {
    return (
      <AdminDashboard 
        credentials={credentials} 
        onLogout={handleLogout} 
      />
    );
  }

  return (
    <div className="container">
      <div className="page">
        <AdminLogin
          onLogin={handleLogin}
          isLoading={loadingState.isLoading}
          error={loadingState.error}
        />
      </div>
    </div>
  );
};

export default AdminPage;