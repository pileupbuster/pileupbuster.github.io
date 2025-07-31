import { useState, useEffect, useRef } from 'react';
import { BrowserRouter as Router, useLocation } from 'react-router-dom';
import './App.css';
import MapSection from './components/MapSection';
import Header from './components/Header';
import Sidebar from './components/Sidebar';
import QueueBar from './components/QueueBar';
import AdminPage from './pages/AdminPage';
import { apiService, type QueueEntry, type CurrentQsoData } from './services/api';
import { adminApiService } from './services/adminApi';
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
  qrz?: {
    name?: string;
    address?: string;
    image?: string;
    url?: string;
  };
  metadata?: {
    source?: 'queue' | 'direct' | 'queue_specific';
    bridge_initiated?: boolean;
    frequency_mhz?: number;
    mode?: string;
    started_via?: string;
  };
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
  const [isAdminLoggedIn, setIsAdminLoggedIn] = useState(false);
  const [queueAnimation, setQueueAnimation] = useState<{ callsign: string; animation: string } | null>(null);
  const previousQsoRef = useRef<CurrentOperator | null>(null);
  const [animatingQueueItem, setAnimatingQueueItem] = useState<QueueItem | null>(null);
  const [systemStatus, setSystemStatus] = useState<boolean | null>(null);
  const queueRef = useRef<QueueItem[]>([]);

  // Check admin login status
  useEffect(() => {
    setIsAdminLoggedIn(adminApiService.isLoggedIn());
  }, []);

  // Function to fetch initial data
  const fetchInitialData = async () => {
    try {
      const [queueData, workedCallersData, currentQsoData, frequencyData, splitData, statusData] = await Promise.all([
        apiService.getQueueList(),
        apiService.getWorkedCallers(),
        apiService.getCurrentQso(),
        apiService.getCurrentFrequency(),
        apiService.getCurrentSplit(),
        fetch(`${import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'}/public/status`).then(r => r.json())
      ]);

      // Convert queue entries to the format expected by the UI
      const convertedQueue = queueData.queue?.map(convertQueueEntryToItem) || [];
      setQueue(convertedQueue);
      queueRef.current = convertedQueue;
      
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
      
      // Set system status
      console.log('Status data from API:', statusData);
      setSystemStatus(statusData.active);
      
      setLoading(false);
    } catch (error) {
      console.error('Error fetching initial data:', error);
      setLoading(false);
    }
  };

  // Function to update current operator based on QSO data
  const updateCurrentOperator = (currentQsoData: CurrentQsoData | null) => {
    console.log('Updating current operator with QSO data:', currentQsoData);
    
    // Track the previous operator for animation purposes
    previousQsoRef.current = currentOperator;
    
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
        profileImage: currentQsoData.qrz?.image || '',
        qrz: currentQsoData.qrz,
        metadata: currentQsoData.metadata
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
      
      // Check if someone was removed from the queue (worked)
      const oldCallsigns = queue.map(item => item.callsign);
      const newCallsigns = convertedQueue.map(item => item.callsign);
      const removedCallsign = oldCallsigns.find(callsign => !newCallsigns.includes(callsign));
      
      // If someone was removed and they're now the current operator, trigger animation
      if (removedCallsign && currentOperator && currentOperator.callsign === removedCallsign) {
        console.log('Detected queue removal for current operator, triggering animation:', removedCallsign);
        setQueueAnimation({ callsign: removedCallsign, animation: 'queue-to-current-animation' });
        
        // Remove animation after it completes
        setTimeout(() => {
          setQueueAnimation(null);
        }, 800);
      }
      
      setQueue(convertedQueue);
      queueRef.current = convertedQueue;
      
      // Note: Queue changes don't affect current operator display
      // Only active QSO data determines current operator
    }
  };

  const handleCurrentQsoEvent = (event: StateChangeEvent) => {
    console.log('Main app received current_qso event:', event);
    
    // Update the current operator display based on the new QSO data
    const qsoData = event.data || null;
    
    // Check if this is a new QSO from the queue
    if (qsoData && qsoData.callsign && (qsoData.metadata?.source === 'queue' || qsoData.metadata?.source === 'queue_specific')) {
      // Find the queue item in the ref (more up-to-date than state)
      const queueItem = queueRef.current.find(item => item.callsign === qsoData.callsign);
      if (queueItem) {
        console.log('New QSO from queue, triggering animation for:', qsoData.callsign);
        console.log('Queue items:', queueRef.current.map(item => item.callsign));
        setAnimatingQueueItem(queueItem);
        setQueueAnimation({ callsign: qsoData.callsign, animation: 'queue-to-current-animation' });
        
        // Remove animation after it completes
        setTimeout(() => {
          setQueueAnimation(null);
          setAnimatingQueueItem(null);
        }, 800);
      } else {
        console.log('Queue item not found for callsign:', qsoData.callsign);
        console.log('Current queue:', queueRef.current.map(item => item.callsign));
      }
    }
    
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
      
      // Trigger animation for QSO to map if this was the current operator
      if (previousQsoRef.current && previousQsoRef.current.callsign === caller.callsign) {
        // The animation will be handled by the CurrentActiveCallsign component
        // when it detects the operator change
      }
      
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

  const handleSystemStatusUpdateEvent = (event: StateChangeEvent) => {
    console.log('Main app received system_status event:', event);
    setSystemStatus(event.data?.active);
    
    // When system goes offline, clear frequency and split
    if (!event.data?.active) {
      setFrequency('');
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
    sseService.addEventListener('system_status', handleSystemStatusUpdateEvent);

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
      sseService.removeEventListener('system_status', handleSystemStatusUpdateEvent);
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
        profileImage: nextOperator.image || ''
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
      <Header frequency={frequency} split={split} systemStatus={systemStatus} />
      
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
      
      <QueueBar 
        queue={queue}
        animatingCallsign={queueAnimation?.callsign}
        animationClass={queueAnimation?.animation}
        animatingItem={animatingQueueItem}
      />
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
