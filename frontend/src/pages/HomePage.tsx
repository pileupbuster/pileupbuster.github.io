import { useState, useEffect } from 'react';
import Layout from '../components/Layout'
import MapSection from '../components/MapSection';
import Header from '../components/Header';
import Sidebar from '../components/Sidebar';
import QueueBar from '../components/QueueBar';
import { apiService, type QueueEntry, type PreviousQsoData } from '../services/api';
import { API_BASE_URL } from '../config/api';

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

// Helper function to convert QueueEntry to QueueItem
function convertQueueEntryToItem(entry: QueueEntry): QueueItem {
  return {
    callsign: entry.callsign,
    name: entry.qrz?.name,
    timeInQueue: new Date(entry.timestamp).getTime(),
    address: entry.qrz?.address,
    grid: {
      lat: undefined, // API doesn't provide coordinates yet
      long: undefined,
      grid: undefined
    },
    image: entry.qrz?.image,
    dxcc_name: entry.qrz?.dxcc_name,
    location: entry.qrz?.address || entry.qrz?.dxcc_name
  };
}

export default function HomePage() {
  const [queue, setQueue] = useState<QueueItem[]>([]);
  const [worked, setWorked] = useState<WorkedItem[]>([]);
  const [currentOperator, setCurrentOperator] = useState<CurrentOperator | null>(null);
  const [frequency, setFrequency] = useState('');
  const [loading, setLoading] = useState(true);

  // SSE connection for real-time updates
  useEffect(() => {
    const eventSource = new EventSource(`${API_BASE_URL}/events/stream`);
    
    eventSource.onmessage = (event) => {
      const data = JSON.parse(event.data);
      
      if (data.type === 'queue_update') {
        // Convert queue entries to the format expected by the UI
        const convertedQueue = data.queue?.map(convertQueueEntryToItem) || [];
        setQueue(convertedQueue);
      } else if (data.type === 'worked_update') {
        setWorked(data.worked);
      } else if (data.type === 'frequency_update') {
        // Update frequency when changed
        console.log('SSE frequency update:', data);
        if (data.frequency) {
          const formattedFreq = data.frequency.replace('.', ',');
          console.log('SSE formatted frequency:', data.frequency, '->', formattedFreq);
          setFrequency(formattedFreq);
        } else {
          setFrequency('');
        }
      }
    };

    eventSource.onerror = (error) => {
      console.error('SSE connection error:', error);
    };

    // Initial data fetch
    Promise.all([
      apiService.getQueueList(),
      apiService.getPreviousQsos(10),
      apiService.getCurrentQso(),
      apiService.getCurrentFrequency()
    ]).then(([queueData, workedData, currentQso, frequencyData]) => {
      // Convert queue entries to the format expected by the UI
      const convertedQueue = queueData.queue?.map(convertQueueEntryToItem) || [];
      setQueue(convertedQueue);
      
      // Convert previous QSOs to worked items
      const convertedWorked: WorkedItem[] = workedData.previous_qsos?.map((qso: PreviousQsoData) => ({
        callsign: qso.callsign,
        name: qso.qrz?.name,
        completedAt: qso.worked_timestamp,
        source: qso.metadata?.source === 'queue' ? 'pileupbuster' : 'direct',
        address: qso.qrz?.address,
        grid: {
          lat: undefined, // API doesn't provide coordinates yet
          long: undefined,
          grid: undefined
        },
        image: qso.qrz?.image,
        dxcc_name: qso.qrz?.dxcc_name,
        location: qso.qrz?.address || qso.qrz?.dxcc_name
      })) || [];
      setWorked(convertedWorked);
      
      // Set current operator based on current QSO or default
      if (currentQso) {
        setCurrentOperator({
          callsign: currentQso.callsign,
          name: currentQso.qrz?.name || currentQso.callsign,
          location: currentQso.qrz?.address || currentQso.qrz?.dxcc_name || 'Unknown',
          coordinates: { lat: 53.3498, lon: -6.2603 }, // Default coordinates
          profileImage: currentQso.qrz?.image || ''
        });
      } else if (convertedQueue.length > 0) {
        const first = convertedQueue[0];
        setCurrentOperator({
          callsign: first.callsign,
          name: first.name || first.callsign,
          location: first.location || 'Unknown',
          coordinates: { lat: 53.3498, lon: -6.2603 },
          profileImage: first.image || ''
        });
      } else {
        // Default operator
        setCurrentOperator({
          callsign: 'EI6LF',
          name: 'Brian Keating',
          location: 'Worked from Pileupbuster',
          coordinates: { lat: 53.3498, lon: -6.2603 },
          profileImage: ''
        });
      }
      
      // Set frequency if available
      console.log('Frequency data from API:', frequencyData);
      if (frequencyData.frequency) {
        // Format frequency with comma separator
        const formattedFreq = frequencyData.frequency.replace('.', ',');
        console.log('Formatted frequency:', frequencyData.frequency, '->', formattedFreq);
        setFrequency(formattedFreq);
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
        profileImage: nextOperator.image || ''
      });

      // Remove from queue
      setQueue(prev => prev.slice(1));
    }
  };

  if (loading) {
    return (
      <Layout>
        <div className="loading">Loading...</div>
      </Layout>
    );
  }

  return (
    <Layout>
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
    </Layout>
  );
}
