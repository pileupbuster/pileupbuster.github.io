import React from 'react';
import CallsignForm from '../components/CallsignForm';
import QueueStatus from '../components/QueueStatus';

interface HomePageProps {
  userCallsign?: string;
  onCallsignRegistered: (callsign: string, position: number) => void;
}

const HomePage: React.FC<HomePageProps> = ({ userCallsign, onCallsignRegistered }) => {
  return (
    <div className="container">
      <div className="page">
        {/* Header */}
        <div style={{ textAlign: 'center', marginBottom: '3rem' }}>
          <h1>Pileup Buster</h1>
          <p style={{ fontSize: '1.125rem', color: '#64748b', maxWidth: '600px', margin: '0 auto' }}>
            Ham Radio Callsign Queue Management System
          </p>
          <p style={{ color: '#94a3b8', marginTop: '0.5rem' }}>
            Register your callsign to join the callback queue
          </p>
        </div>

        {/* Main Content */}
        <div style={{ 
          display: 'grid', 
          gap: '2rem',
          gridTemplateColumns: 'repeat(auto-fit, minmax(400px, 1fr))',
          alignItems: 'start'
        }}>
          {/* Registration Form */}
          <div>
            <CallsignForm onSuccess={onCallsignRegistered} />
          </div>

          {/* Queue Status */}
          <div>
            <QueueStatus userCallsign={userCallsign} />
          </div>
        </div>

        {/* Information Section */}
        <div className="card" style={{ marginTop: '2rem' }}>
          <div className="card-header">
            <h3 className="card-title">How It Works</h3>
          </div>
          
          <div style={{ 
            display: 'grid', 
            gap: '1.5rem',
            gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))'
          }}>
            <div style={{ textAlign: 'center' }}>
              <div style={{ 
                width: '48px', 
                height: '48px', 
                background: '#3b82f6', 
                borderRadius: '50%', 
                display: 'flex', 
                alignItems: 'center', 
                justifyContent: 'center', 
                color: 'white', 
                fontSize: '1.5rem', 
                fontWeight: 'bold',
                margin: '0 auto 1rem auto'
              }}>
                1
              </div>
              <h4>Register</h4>
              <p style={{ fontSize: '0.875rem' }}>
                Enter your callsign to join the queue
              </p>
            </div>

            <div style={{ textAlign: 'center' }}>
              <div style={{ 
                width: '48px', 
                height: '48px', 
                background: '#10b981', 
                borderRadius: '50%', 
                display: 'flex', 
                alignItems: 'center', 
                justifyContent: 'center', 
                color: 'white', 
                fontSize: '1.5rem', 
                fontWeight: 'bold',
                margin: '0 auto 1rem auto'
              }}>
                2
              </div>
              <h4>Wait</h4>
              <p style={{ fontSize: '0.875rem' }}>
                Monitor your position in the queue
              </p>
            </div>

            <div style={{ textAlign: 'center' }}>
              <div style={{ 
                width: '48px', 
                height: '48px', 
                background: '#f59e0b', 
                borderRadius: '50%', 
                display: 'flex', 
                alignItems: 'center', 
                justifyContent: 'center', 
                color: 'white', 
                fontSize: '1.5rem', 
                fontWeight: 'bold',
                margin: '0 auto 1rem auto'
              }}>
                3
              </div>
              <h4>Get Called</h4>
              <p style={{ fontSize: '0.875rem' }}>
                Receive your callback when it's your turn
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default HomePage;