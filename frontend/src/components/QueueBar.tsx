import { useEffect, useState } from 'react';

interface QueueItem {
  callsign: string;
  name?: string;
  timeInQueue: number;
  address?: string;
  grid?: {
    lat?: number;
    long?: number;
    grid?: string;
  };
  image?: string;
  dxcc_name?: string;
  location?: string;
  waitTime?: string;
}

interface QueueBarProps {
  queue: QueueItem[];
}

function QueueBar({ queue }: QueueBarProps) {
  const [timers, setTimers] = useState<Record<string, string>>({});

  // Format time in queue as MM:SS
  const formatTime = (seconds: number): string => {
    const minutes = Math.floor(seconds / 60);
    const remainingSeconds = seconds % 60;
    return `${minutes.toString().padStart(2, '0')}:${remainingSeconds.toString().padStart(2, '0')}`;
  };

  useEffect(() => {
    const interval = setInterval(() => {
      const now = Date.now();
      const newTimers: Record<string, string> = {};
      
      queue.forEach(item => {
        const timeInQueueSeconds = Math.floor((now - item.timeInQueue) / 1000);
        newTimers[item.callsign] = formatTime(timeInQueueSeconds);
      });
      
      setTimers(newTimers);
    }, 1000);

    return () => clearInterval(interval);
  }, [queue]);

  // Create array of 4 positions, filling with placeholders if needed
  const positions = Array.from({ length: 4 }, (_, index) => {
    const item = queue[index];
    if (item) {
      return (
        <div key={item.callsign} className="queue-card" data-position={index}>
          <img 
            src={item.image || `https://i.pravatar.cc/150?img=${Math.floor(Math.random() * 70)}`} 
            alt={item.callsign} 
            className="queue-image" 
          />
          <div className="queue-info">
            <h3 className="queue-callsign">{item.callsign}</h3>
            <p className="queue-location">
              {item.location || item.address || item.dxcc_name || 'Unknown'}
            </p>
            <p className="queue-time">
              {timers[item.callsign] || '00:00'}
            </p>
          </div>
        </div>
      );
    } else {
      return (
        <div key={`placeholder-${index}`} className="queue-card placeholder" data-position={index}>
          <div className="queue-placeholder-icon">➕</div>
          <div className="queue-info">
            <h3 className="queue-callsign" style={{ color: 'rgba(255,255,255,0.4)' }}>
              Empty
            </h3>
            <p className="queue-location" style={{ color: 'rgba(255,255,255,0.3)' }}>
              No operator
            </p>
            <p className="queue-time" style={{ color: 'rgba(255,255,255,0.3)' }}>
              --:--
            </p>
          </div>
        </div>
      );
    }
  });

  return (
    <div className="bottom-queue">
      {positions}
    </div>
  );
}

export default QueueBar;
