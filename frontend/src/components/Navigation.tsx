import React from 'react';

interface NavigationProps {
  currentView: 'home' | 'admin' | 'status';
  onViewChange: (view: 'home' | 'admin' | 'status') => void;
  userCallsign?: string;
}

const Navigation: React.FC<NavigationProps> = ({ 
  currentView, 
  onViewChange, 
  userCallsign 
}) => {
  return (
    <div className="nav">
      <div className="container">
        <div className="nav-content">
          <div className="nav-brand">
            Pileup Buster
          </div>
          
          <div className="nav-links">
            <button
              onClick={() => onViewChange('home')}
              className={`btn ${currentView === 'home' ? 'btn-primary' : 'btn-secondary'}`}
            >
              Home
            </button>
            
            {userCallsign && (
              <button
                onClick={() => onViewChange('status')}
                className={`btn ${currentView === 'status' ? 'btn-primary' : 'btn-secondary'}`}
              >
                My Status ({userCallsign})
              </button>
            )}
            
            <button
              onClick={() => onViewChange('admin')}
              className={`btn ${currentView === 'admin' ? 'btn-primary' : 'btn-secondary'}`}
            >
              Admin
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Navigation;