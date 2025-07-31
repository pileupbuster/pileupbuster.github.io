import { useState, useEffect } from 'react';
import HeaderFrequencyDisplay from './HeaderFrequencyDisplay';

interface HeaderProps {
  frequency: string;
  split?: string;
  systemStatus?: boolean | null;
}

function Header({ frequency, split, systemStatus }: HeaderProps) {
  const [currentTime, setCurrentTime] = useState('');

  useEffect(() => {
    const updateClock = () => {
      const now = new Date();
      const hours = String(now.getUTCHours()).padStart(2, '0');
      const minutes = String(now.getUTCMinutes()).padStart(2, '0');
      setCurrentTime(`${hours}:${minutes}`);
    };

    updateClock();
    const interval = setInterval(updateClock, 1000);

    return () => clearInterval(interval);
  }, []);

  return (
    <header className="top-header">
      <div className="logo-section">
        <img 
          src="/ei6jgb-pileupbuster.png" 
          alt="EI6JGB PileupBuster" 
          className="logo-image"
        />
      </div>
      
      <HeaderFrequencyDisplay frequency={frequency} systemStatus={systemStatus} split={split} />
      
      <div className="clock-section">
        <div className="clock">
          {currentTime}
          <span className="utc-label">UTC</span>
        </div>
      </div>
    </header>
  );
}

export default Header;
