import React, { useState } from 'react';
import Navigation from './components/Navigation';
import HomePage from './pages/HomePage';
import AdminPage from './pages/AdminPage';
import StatusPage from './pages/StatusPage';
import './styles/global.css';

const App: React.FC = () => {
  const [currentView, setCurrentView] = useState<'home' | 'admin' | 'status'>('home');
  const [userCallsign, setUserCallsign] = useState<string>('');
  const [successMessage, setSuccessMessage] = useState<string>('');

  const handleCallsignRegistered = (callsign: string, position: number) => {
    setUserCallsign(callsign);
    setSuccessMessage(`Successfully registered ${callsign} at position #${position}!`);
    
    // Clear success message after 5 seconds
    setTimeout(() => setSuccessMessage(''), 5000);
  };

  const handleViewChange = (view: 'home' | 'admin' | 'status') => {
    setCurrentView(view);
    
    // Clear success message when changing views
    setSuccessMessage('');
  };

  const renderCurrentView = () => {
    switch (currentView) {
      case 'home':
        return (
          <HomePage 
            userCallsign={userCallsign}
            onCallsignRegistered={handleCallsignRegistered}
          />
        );
        
      case 'admin':
        return <AdminPage />;
        
      case 'status':
        if (!userCallsign) {
          return (
            <div className="container">
              <div className="page">
                <div className="card">
                  <div className="alert alert-warning">
                    You need to register a callsign first to view your status.
                  </div>
                  <button 
                    onClick={() => setCurrentView('home')} 
                    className="btn btn-primary"
                  >
                    Go to Registration
                  </button>
                </div>
              </div>
            </div>
          );
        }
        return <StatusPage userCallsign={userCallsign} />;
        
      default:
        return null;
    }
  };

  return (
    <div className="App">
      {/* Navigation - only show on non-admin dashboard views */}
      {!(currentView === 'admin') && (
        <Navigation 
          currentView={currentView}
          onViewChange={handleViewChange}
          userCallsign={userCallsign}
        />
      )}

      {/* Success Message */}
      {successMessage && currentView === 'home' && (
        <div className="container">
          <div className="alert alert-success" style={{ marginTop: '1rem' }}>
            {successMessage}
          </div>
        </div>
      )}

      {/* Main Content */}
      {renderCurrentView()}
    </div>
  );
};

export default App;