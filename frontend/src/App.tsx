import { useState, useEffect } from 'react';
import './App.css';
import MapSection from './components/MapSection';
import Header from './components/Header';
import Sidebar from './components/Sidebar';
import QueueBar from './components/QueueBar';

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

interface WorkedItem {
  callsign: string;
  name?: string;
  completedAt: string;
  source: 'pileupbuster' | 'direct';
  address?: string;
  grid?: {
    lat?: number;
    long?: number;
    grid?: string;
  };
  image?: string;
  dxcc_name?: string;
  location?: string;
}

interface CurrentOperator {
  callsign: string;
  name: string;
  location: string;
  coordinates: { lat: number; lon: number };
  profileImage: string;
}

function App() {
  const [queue, setQueue] = useState<QueueItem[]>([]);
  const [worked, setWorked] = useState<WorkedItem[]>([]);
  const [currentOperator, setCurrentOperator] = useState<CurrentOperator | null>(null);
  const [frequency] = useState('14,121.00');
  const [loading, setLoading] = useState(true);

  // SSE connection for real-time updates
  useEffect(() => {
    const eventSource = new EventSource('/api/events');
    
    eventSource.onmessage = (event) => {
      const data = JSON.parse(event.data);
      
      if (data.type === 'queue_update') {
        setQueue(data.queue);
      } else if (data.type === 'worked_update') {
        setWorked(data.worked);
      }
    };

    eventSource.onerror = (error) => {
      console.error('SSE connection error:', error);
    };

    // Initial data fetch
    Promise.all([
      fetch('/api/queue').then(res => res.json()),
      fetch('/api/worked').then(res => res.json())
    ]).then(([queueData, workedData]) => {
      setQueue(queueData.queue || []);
      setWorked(workedData.worked || []);
      
      // Set initial current operator (first in queue or placeholder)
      if (queueData.queue && queueData.queue.length > 0) {
        const first = queueData.queue[0];
        setCurrentOperator({
          callsign: first.callsign,
          name: first.name || first.callsign,
          location: first.address || first.dxcc_name || 'Unknown',
          coordinates: { 
            lat: first.grid?.lat || 53.3498, 
            lon: first.grid?.long || -6.2603 
          },
          profileImage: first.image || `https://i.pravatar.cc/200?img=${Math.floor(Math.random() * 70)}`
        });
      } else {
        // Default operator
        setCurrentOperator({
          callsign: 'EI6LF',
          name: 'Brian Keating',
          location: 'Worked from Pileupbuster',
          coordinates: { lat: 53.3498, lon: -6.2603 },
          profileImage: 'https://i.pravatar.cc/200?img=68'
        });
      }
      
      setLoading(false);
    }).catch(error => {
      console.error('Error fetching initial data:', error);
      setLoading(false);
    });

    return () => {
      eventSource.close();
    };
  }, []);

  const handleWorkCurrentOperator = () => {
    if (!currentOperator || queue.length === 0) return;

    // Move current operator to worked list
    const newWorkedItem: WorkedItem = {
      callsign: currentOperator.callsign,
      name: currentOperator.name,
      completedAt: new Date().toISOString(),
      source: 'pileupbuster',
      location: currentOperator.location,
      grid: {
        lat: currentOperator.coordinates.lat,
        long: currentOperator.coordinates.lon
      },
      image: currentOperator.profileImage
    };

    setWorked(prev => [newWorkedItem, ...prev]);

    // Move next in queue to current position
    if (queue.length > 0) {
      const nextOperator = queue[0];
      setCurrentOperator({
        callsign: nextOperator.callsign,
        name: nextOperator.name || nextOperator.callsign,
        location: nextOperator.address || nextOperator.dxcc_name || 'Unknown',
        coordinates: { 
          lat: nextOperator.grid?.lat || 53.3498, 
          lon: nextOperator.grid?.long || -6.2603 
        },
        profileImage: nextOperator.image || `https://i.pravatar.cc/200?img=${Math.floor(Math.random() * 70)}`
      });

      // Remove from queue
      setQueue(prev => prev.slice(1));
    }
  };

  if (loading) {
    return <div className="loading">Loading...</div>;
  }

  return (
    <div className="container">
      <Header frequency={frequency} />
      
      <div className="main-content">
        <MapSection 
          workedOperators={worked}
          currentOperator={currentOperator}
        />
        
        <Sidebar 
          currentOperator={currentOperator}
          queueCount={queue.length}
          workedCount={worked.length}
          onWorkOperator={handleWorkCurrentOperator}
        />
      </div>
      
      <QueueBar queue={queue} />
    </div>
  );
}

export default App;
