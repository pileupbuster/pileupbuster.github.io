import { useState, useEffect } from 'react';

interface HeaderProps {
  frequency: string;
}

function Header({ frequency }: HeaderProps) {
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
      <div className="frequency-section">
        <div className="frequency-value">{frequency}</div>
        <div className="frequency-unit">MHz</div>
      </div>
      <div className="clock-section">
        <div className="clock">{currentTime}</div>
      </div>
    </header>
  );
}

export default Header;
