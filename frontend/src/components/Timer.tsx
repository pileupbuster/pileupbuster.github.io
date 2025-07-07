import React, { useState, useEffect } from 'react';

interface TimerProps {
  timestamp: string;
}

const Timer: React.FC<TimerProps> = ({ timestamp }) => {
  const [elapsed, setElapsed] = useState('00:00');

  useEffect(() => {
    const calculateElapsed = () => {
      try {
        // Parse the timestamp - handle both with and without timezone
        let startTime: Date;
        
        if (timestamp.includes('+') || timestamp.includes('Z')) {
          // Timestamp already has timezone info
          startTime = new Date(timestamp);
        } else {
          // Timestamp is missing timezone, assume it's UTC
          startTime = new Date(timestamp + 'Z');
        }
        
        const now = new Date();
        
        // Calculate difference in milliseconds, then convert to seconds
        const diffMs = now.getTime() - startTime.getTime();
        const diffSeconds = Math.floor(diffMs / 1000);
        
        // Handle negative times (clock skew) by showing 00:00
        if (diffSeconds < 0) {
          return '00:00';
        }
        
        // Calculate minutes and seconds
        const minutes = Math.floor(diffSeconds / 60);
        const seconds = diffSeconds % 60;
        
        // Format as MM:SS with leading zeros
        return `${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
      } catch (error) {
        console.warn('Failed to parse timestamp:', timestamp, error);
        return '00:00';
      }
    };

    // Initial calculation
    setElapsed(calculateElapsed());

    // Update every second
    const interval = setInterval(() => {
      setElapsed(calculateElapsed());
    }, 1000);

    // Cleanup interval on unmount
    return () => clearInterval(interval);
  }, [timestamp]);

  return (
    <div className="queue-timer">
      {elapsed}
    </div>
  );
};

export default Timer;
