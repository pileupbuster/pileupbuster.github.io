import { useState, useEffect } from 'react';
import { BrowserRouter as Router, useLocation } from 'react-router-dom';
import './App.css';
import MapSection from './components/MapSection';
import Header from './components/Header';
import Sidebar from './components/Sidebar';
import QueueBar from './components/QueueBar';
import AdminPage from './pages/AdminPage';
import { apiService, type QueueEntry, type PreviousQsoData } from './services/api';
import { sseService, type StateChangeEvent } from './services/sse';

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

function MainApp() {
  const [queue, setQueue] = useState<QueueItem[]>([]);
  const [worked, setWorked] = useState<WorkedItem[]>([]);
  const [currentOperator, setCurrentOperator] = useState<CurrentOperator | null>(null);
  const [frequency] = useState('14,121.00');
  const [loading, setLoading] = useState(true);

  // Function to fetch initial data
  const fetchInitialData = async () => {
    try {
      const [queueData, workedData, currentQso] = await Promise.all([
        apiService.getQueueList(),
        apiService.getPreviousQsos(10),
        apiService.getCurrentQso()
      ]);

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
      
      // Set current operator based on current QSO
      updateCurrentOperator(currentQso, convertedQueue);
      setLoading(false);
    } catch (error) {
      console.error('Error fetching initial data:', error);
      setLoading(false);
    }
  };

  // Function to update current operator based on QSO data
  const updateCurrentOperator = (currentQso: any, queueData?: QueueItem[]) => {
    if (currentQso) {
      setCurrentOperator({
        callsign: currentQso.callsign,
        name: currentQso.qrz?.name || currentQso.callsign,
        location: currentQso.qrz?.address || currentQso.qrz?.dxcc_name || 'Unknown',
        coordinates: { lat: 53.3498, lon: -6.2603 }, // Default coordinates
        profileImage: currentQso.qrz?.image || `https://i.pravatar.cc/200?img=${Math.floor(Math.random() * 70)}`
      });
    } else {
      const currentQueue = queueData || queue;
      if (currentQueue.length > 0) {
        const first = currentQueue[0];
        setCurrentOperator({
          callsign: first.callsign,
          name: first.name || first.callsign,
          location: first.location || 'Unknown',
          coordinates: { lat: 53.3498, lon: -6.2603 },
          profileImage: first.image || `https://i.pravatar.cc/200?img=${Math.floor(Math.random() * 70)}`
        });
      } else {
        // Default operator when no QSO and no queue
        setCurrentOperator({
          callsign: 'EI6LF',
          name: 'Brian Keating',
          location: 'Worked from Pileupbuster',
          coordinates: { lat: 53.3498, lon: -6.2603 },
          profileImage: 'https://i.pravatar.cc/200?img=68'
        });
      }
    }
  };

  // SSE event handlers
  const handleQueueUpdateEvent = (event: StateChangeEvent) => {
    console.log('Main app received queue_update event:', event);
    if (event.data?.queue) {
      // Convert queue entries to the format expected by the UI
      const convertedQueue = event.data.queue.map(convertQueueEntryToItem);
      setQueue(convertedQueue);
      
      // If no current QSO, update current operator based on new queue
      if (!currentOperator || currentOperator.callsign === 'EI6LF') {
        updateCurrentOperator(null, convertedQueue);
      }
    }
  };

  const handleCurrentQsoEvent = (event: StateChangeEvent) => {
    console.log('Main app received current_qso event:', event);
    updateCurrentOperator(event.data);
  };

  const handleWorkedCallersUpdateEvent = (event: StateChangeEvent) => {
    console.log('Main app received worked_callers_update event:', event);
    if (event.data?.worked_callers) {
      // Convert worked callers to the format expected by the UI
      const convertedWorked: WorkedItem[] = event.data.worked_callers.map((caller: any) => ({
        callsign: caller.callsign,
        name: caller.qrz?.name,
        completedAt: caller.worked_timestamp,
        source: caller.metadata?.source === 'queue' ? 'pileupbuster' : 'direct',
        address: caller.qrz?.address,
        grid: {
          lat: undefined,
          long: undefined,
          grid: undefined
        },
        image: caller.qrz?.image,
        dxcc_name: caller.qrz?.dxcc_name,
        location: caller.qrz?.address || caller.qrz?.dxcc_name
      }));
      setWorked(convertedWorked);
    }
  };

  // SSE connection setup
  useEffect(() => {
    // Register SSE event listeners
    sseService.addEventListener('queue_update', handleQueueUpdateEvent);
    sseService.addEventListener('current_qso', handleCurrentQsoEvent);
    sseService.addEventListener('worked_callers_update', handleWorkedCallersUpdateEvent);

    // Start SSE connection
    sseService.connect();

    // Fetch initial data
    fetchInitialData();

    // Cleanup on component unmount
    return () => {
      sseService.removeEventListener('queue_update', handleQueueUpdateEvent);
      sseService.removeEventListener('current_qso', handleCurrentQsoEvent);
      sseService.removeEventListener('worked_callers_update', handleWorkedCallersUpdateEvent);
      sseService.disconnect();
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

function AppRouter() {
  const location = useLocation();
  
  // If the path is /admin, show the admin page
  if (location.pathname === '/admin') {
    return <AdminPage />;
  }
  
  // Otherwise, always show the main app (no 404)
  return <MainApp />;
}

function App() {
  return (
    <Router>
      <AppRouter />
    </Router>
  );
}

export default App;
