import { useState, useEffect } from 'react';
import { BrowserRouter as Router, useLocation } from 'react-router-dom';
import './App.css';
import MapSection from './components/MapSection';
import Header from './components/Header';
import Sidebar from './components/Sidebar';
import QueueBar from './components/QueueBar';
import AdminPage from './pages/AdminPage';
import { apiService, type QueueEntry, type PreviousQsoData, type CurrentQsoData, type WorkedCallerData } from './services/api';
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
  const [frequency, setFrequency] = useState('');
  const [split, setSplit] = useState('');
  const [loading, setLoading] = useState(true);

  // Function to fetch initial data
  const fetchInitialData = async () => {
    try {
      const [queueData, workedCallersData, currentQsoData, frequencyData, splitData] = await Promise.all([
        apiService.getQueueList(),
        apiService.getWorkedCallers(),
        apiService.getCurrentQso(),
        apiService.getCurrentFrequency(),
        apiService.getCurrentSplit()
      ]);

      // Convert queue entries to the format expected by the UI
      const convertedQueue = queueData.queue?.map(convertQueueEntryToItem) || [];
      setQueue(convertedQueue);
      
      // Convert worked callers to worked items
      const convertedWorked: WorkedItem[] = workedCallersData.worked_callers?.map((caller: any) => ({
        callsign: caller.callsign,
        name: caller.name || caller.qrz?.name,
        completedAt: caller.worked_timestamp,
        source: caller.metadata?.source === 'queue' ? 'pileupbuster' : 'direct',
        address: caller.location || caller.qrz?.address,
        grid: caller.grid || {
          lat: caller.qrz?.grid?.lat,
          long: caller.qrz?.grid?.long,
          grid: caller.qrz?.grid?.grid
        },
        image: caller.qrz_image || caller.qrz?.image,
        dxcc_name: caller.country || caller.qrz?.dxcc_name,
        location: caller.location || caller.qrz?.address || caller.qrz?.dxcc_name
      })) || [];
      setWorked(convertedWorked);
      
      // Set current operator display
      // Explicitly handle null case from getCurrentQso
      const qsoData = currentQsoData || null;
      updateCurrentOperator(qsoData);
      
      // Set frequency if available
      console.log('Frequency data from API:', frequencyData);
      if (frequencyData.frequency) {
        // Format frequency with comma separator
        const formattedFreq = frequencyData.frequency.replace('.', ',');
        console.log('Formatted frequency:', frequencyData.frequency, '->', formattedFreq);
        setFrequency(formattedFreq);
      }
      
      // Set split if available
      console.log('Split data from API:', splitData);
      if (splitData.split) {
        // Format split with comma separator
        const formattedSplit = splitData.split.replace('.', ',');
        console.log('Formatted split:', splitData.split, '->', formattedSplit);
        setSplit(formattedSplit);
      }
      
      setLoading(false);
    } catch (error) {
      console.error('Error fetching initial data:', error);
      setLoading(false);
    }
  };

  // Function to update current operator based on QSO data
  const updateCurrentOperator = (currentQsoData: CurrentQsoData | null) => {
    console.log('Updating current operator with QSO data:', currentQsoData);
    
    // Only show a current operator if we have an active QSO from the backend
    // The queue is only for waiting - not for showing current operator
    if (currentQsoData && currentQsoData.callsign) {
      // We have an active QSO - display the current QSO operator
      console.log('Setting current operator from active QSO:', currentQsoData.callsign);
      setCurrentOperator({
        callsign: currentQsoData.callsign,
        name: currentQsoData.qrz?.name || currentQsoData.callsign,
        location: currentQsoData.qrz?.address || currentQsoData.qrz?.dxcc_name || 'In QSO',
        coordinates: { lat: 53.3498, lon: -6.2603 }, // Default coordinates
        profileImage: currentQsoData.qrz?.image || `https://i.pravatar.cc/200?img=${Math.floor(Math.random() * 70)}`
      });
    } else {
      // No active QSO - clear current operator regardless of queue status
      console.log('No current QSO - clearing current operator (queue status irrelevant)');
      setCurrentOperator(null);
    }
  };

  // SSE event handlers
  const handleQueueUpdateEvent = (event: StateChangeEvent) => {
    console.log('Main app received queue_update event:', event);
    if (event.data?.queue) {
      // Convert queue entries to the format expected by the UI
      const convertedQueue = event.data.queue.map(convertQueueEntryToItem);
      setQueue(convertedQueue);
      
      // Note: Queue changes don't affect current operator display
      // Only active QSO data determines current operator
    }
  };

  const handleCurrentQsoEvent = (event: StateChangeEvent) => {
    console.log('Main app received current_qso event:', event);
    
    // Update the current operator display based on the new QSO data
    const qsoData = event.data || null;
    updateCurrentOperator(qsoData);
  };

  const handleWorkedCallersUpdateEvent = (event: StateChangeEvent) => {
    console.log('Main app received worked_callers_update event:', event);
    
    // Handle single worked caller (new format)
    if (event.data?.worked_caller) {
      const caller = event.data.worked_caller;
      const newWorkedItem: WorkedItem = {
        callsign: caller.callsign,
        name: caller.name || caller.qrz?.name,
        completedAt: caller.worked_timestamp,
        source: caller.metadata?.source === 'queue' ? 'pileupbuster' : 'direct',
        address: caller.location || caller.qrz?.address,
        grid: caller.grid || {
          lat: caller.qrz?.grid?.lat,
          long: caller.qrz?.grid?.long,
          grid: caller.qrz?.grid?.grid
        },
        image: caller.qrz_image || caller.qrz?.image,
        dxcc_name: caller.country || caller.qrz?.dxcc_name,
        location: caller.location || caller.qrz?.address || caller.qrz?.dxcc_name
      };
      
      // Prepend new worked item to the list
      setWorked(prev => [newWorkedItem, ...prev]);
    }
    // Handle array of worked callers (backwards compatibility)
    else if (event.data?.worked_callers) {
      // Convert worked callers to the format expected by the UI
      const convertedWorked: WorkedItem[] = event.data.worked_callers.map((caller: any) => ({
        callsign: caller.callsign,
        name: caller.name || caller.qrz?.name,
        completedAt: caller.worked_timestamp,
        source: caller.metadata?.source === 'queue' ? 'pileupbuster' : 'direct',
        address: caller.location || caller.qrz?.address,
        grid: caller.grid || {
          lat: caller.qrz?.grid?.lat,
          long: caller.qrz?.grid?.long,
          grid: caller.qrz?.grid?.grid
        },
        image: caller.qrz_image || caller.qrz?.image,
        dxcc_name: caller.country || caller.qrz?.dxcc_name,
        location: caller.location || caller.qrz?.address || caller.qrz?.dxcc_name
      }));
      setWorked(convertedWorked);
    }
  };

  const handleFrequencyUpdateEvent = (event: StateChangeEvent) => {
    console.log('Main app received frequency_update event:', event);
    if (event.data?.frequency) {
      const formattedFreq = event.data.frequency.replace('.', ',');
      console.log('SSE formatted frequency:', event.data.frequency, '->', formattedFreq);
      setFrequency(formattedFreq);
    } else {
      setFrequency('');
    }
  };

  const handleSplitUpdateEvent = (event: StateChangeEvent) => {
    console.log('Main app received split_update event:', event);
    if (event.data?.split) {
      const formattedSplit = event.data.split.replace('.', ',');
      console.log('SSE formatted split:', event.data.split, '->', formattedSplit);
      setSplit(formattedSplit);
    } else {
      setSplit('');
    }
  };

  // SSE connection setup
  useEffect(() => {
    // Register SSE event listeners
    sseService.addEventListener('queue_update', handleQueueUpdateEvent);
    sseService.addEventListener('current_qso', handleCurrentQsoEvent);
    sseService.addEventListener('worked_callers_update', handleWorkedCallersUpdateEvent);
    sseService.addEventListener('frequency_update', handleFrequencyUpdateEvent);
    sseService.addEventListener('split_update', handleSplitUpdateEvent);

    // Start SSE connection
    sseService.connect();

    // Fetch initial data
    fetchInitialData();

    // Cleanup on component unmount
    return () => {
      sseService.removeEventListener('queue_update', handleQueueUpdateEvent);
      sseService.removeEventListener('current_qso', handleCurrentQsoEvent);
      sseService.removeEventListener('worked_callers_update', handleWorkedCallersUpdateEvent);
      sseService.removeEventListener('frequency_update', handleFrequencyUpdateEvent);
      sseService.removeEventListener('split_update', handleSplitUpdateEvent);
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
      <Header frequency={frequency} split={split} />
      
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
