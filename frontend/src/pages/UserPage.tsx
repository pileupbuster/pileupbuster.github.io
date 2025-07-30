import { useState, useEffect, useCallback } from 'react'
import Layout from '../components/Layout'
import CurrentActiveCallsign, { type CurrentActiveUser } from '../components/CurrentActiveCallsign'
import WaitingQueue from '../components/WaitingQueue'
import FrequencySignalPane from '../components/FrequencySignalPane'
import { type QueueItemData } from '../components/QueueItem'
import { apiService, type CurrentQsoData, type QueueEntry, ApiError } from '../services/api'
import { sseService, type StateChangeEvent } from '../services/sse'

export default function UserPage() {
  // Real data state
  const [currentQso, setCurrentQso] = useState<CurrentQsoData | null>(null)
  const [queueData, setQueueData] = useState<QueueItemData[]>([])
  const [queueTotal, setQueueTotal] = useState(0)
  const [queueMaxSize, setQueueMaxSize] = useState(4)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [systemStatus, setSystemStatus] = useState<boolean | null>(null)
  const [currentFrequency, setCurrentFrequency] = useState<string | null>(null)

  // Convert QueueEntry to QueueItemData format
  const convertQueueEntryToItemData = (entry: QueueEntry): QueueItemData => {
    return {
      callsign: entry.callsign,
      location: entry.qrz?.dxcc_name || entry.qrz?.address || 'Location not available',
      timestamp: entry.timestamp,
      qrz: entry.qrz
    }
  }

  // Convert CurrentQsoData to CurrentActiveUser format
  const convertCurrentQsoToActiveUser = (qso: CurrentQsoData): CurrentActiveUser => {
    return {
      callsign: qso.callsign,
      name: qso.qrz?.name || 'Name not available',
      location: qso.qrz?.dxcc_name || qso.qrz?.address || 'Location not available'
    }
  }

  // Fetch current QSO data
  const fetchCurrentQso = useCallback(async () => {
    try {
      const data = await apiService.getCurrentQso()
      setCurrentQso(data)
    } catch (err) {
      if (err instanceof ApiError) {
        console.error('Failed to fetch current QSO:', err.detail || err.message)
        setError(err.detail || err.message)
      } else {
        console.error('Failed to fetch current QSO:', err)
        setError('Failed to load current QSO')
      }
    }
  }, [])

  // Fetch queue list
  const fetchQueueList = useCallback(async () => {
    try {
      const response = await apiService.getQueueList()
      const queueItems = response.queue.map(convertQueueEntryToItemData)
      setQueueData(queueItems)
      setQueueTotal(response.total)
      setQueueMaxSize(response.max_size)
    } catch (err) {
      if (err instanceof ApiError) {
        console.error('Failed to fetch queue list:', err.detail || err.message)
        setError(err.detail || err.message)
      } else {
        console.error('Failed to fetch queue list:', err)
        setError('Failed to load queue')
      }
    }
  }, [])

  // Load system status
  const loadSystemStatus = async () => {
    try {
      const status = await apiService.getSystemStatus()
      setSystemStatus(status.active)
    } catch (error) {
      console.error('Failed to load system status:', error)
      setSystemStatus(false)
    }
  }

  // Load current frequency
  const loadCurrentFrequency = async () => {
    try {
      const frequencyData = await apiService.getCurrentFrequency()
      setCurrentFrequency(frequencyData.frequency)
    } catch (error) {
      console.error('Failed to load current frequency:', error)
      setCurrentFrequency(null)
    }
  }

  // Initial data load
  useEffect(() => {
    const loadData = async () => {
      setLoading(true)
      setError(null)
      
      await Promise.all([
        fetchCurrentQso(),
        fetchQueueList(),
        loadSystemStatus(),
        loadCurrentFrequency()
      ])
      
      setLoading(false)
    }

    loadData()
  }, [fetchCurrentQso, fetchQueueList])

  // Real-time updates via Server-Sent Events (SSE)
  useEffect(() => {
    // Event handlers for different types of state changes
    const handleCurrentQsoEvent = (event: StateChangeEvent) => {
      console.log('Received current_qso event:', event)
      const newQso = event.data
      setCurrentQso(newQso)
    }

    const handleQueueUpdateEvent = (event: StateChangeEvent) => {
      console.log('Received queue_update event:', event)
      if (event.data?.queue) {
        const queueItems = event.data.queue.map(convertQueueEntryToItemData)
        setQueueData(queueItems)
        if (event.data.total !== undefined) {
          setQueueTotal(event.data.total)
        }
        if (event.data.max_size !== undefined) {
          setQueueMaxSize(event.data.max_size)
        }
      }
    }

    const handleSystemStatusEvent = (event: StateChangeEvent) => {
      console.log('Received system_status event:', event)
      if (event.data?.active !== undefined) {
        setSystemStatus(event.data.active)
        
        // Clear error state when system is activated
        if (event.data.active) {
          setError(null)
        }
      }
    }

    const handleConnectedEvent = (event: StateChangeEvent) => {
      console.log('SSE connected:', event)
      // When SSE connects, fetch initial data
      Promise.all([
        fetchCurrentQso(),
        fetchQueueList(),
        loadCurrentFrequency()
      ]).catch(err => {
        console.error('Failed to fetch initial data after SSE connection:', err)
      })
    }

    const handleFrequencyUpdateEvent = (event: StateChangeEvent) => {
      console.log('Received frequency_update event:', event)
      if (event.data?.frequency !== undefined) {
        setCurrentFrequency(event.data.frequency)
      }
    }

    const handleSplitUpdateEvent = (event: StateChangeEvent) => {
      console.log('Received split_update event:', event)
      // Split updates are handled by the FrequencySignalPane component via SSE
      // No additional state management needed at this level
    }

    // Register event listeners
    sseService.addEventListener('current_qso', handleCurrentQsoEvent)
    sseService.addEventListener('queue_update', handleQueueUpdateEvent)
    sseService.addEventListener('system_status', handleSystemStatusEvent)
    sseService.addEventListener('connected', handleConnectedEvent)
    sseService.addEventListener('frequency_update', handleFrequencyUpdateEvent)
    sseService.addEventListener('split_update', handleSplitUpdateEvent)

    // Start SSE connection
    sseService.connect()

    // Fallback polling in case SSE fails (every 30 seconds)
    const fallbackInterval = setInterval(() => {
      if (!sseService.isConnected()) {
        console.log('SSE not connected, using fallback polling')
        fetchCurrentQso()
        fetchQueueList()
      }
    }, 30000) // Fallback poll every 30 seconds

    // Cleanup on component unmount
    return () => {
      sseService.removeEventListener('current_qso', handleCurrentQsoEvent)
      sseService.removeEventListener('queue_update', handleQueueUpdateEvent)
      sseService.removeEventListener('system_status', handleSystemStatusEvent)
      sseService.removeEventListener('connected', handleConnectedEvent)
      sseService.removeEventListener('frequency_update', handleFrequencyUpdateEvent)
      sseService.removeEventListener('split_update', handleSplitUpdateEvent)
      sseService.disconnect()
      clearInterval(fallbackInterval)
    }
  }, [fetchCurrentQso, fetchQueueList])

  // Handle callsign registration
  const handleCallsignRegistration = async (callsign: string) => {
    try {
      await apiService.registerCallsign(callsign)
      // No need to manually refresh - SSE will broadcast the queue update
    } catch (err) {
      if (err instanceof ApiError) {
        console.error('Failed to register callsign:', err.detail || err.message)
        // You might want to show a user-visible error here
        throw new Error(err.detail || err.message)
      } else {
        console.error('Failed to register callsign:', err)
        throw new Error('Failed to register callsign')
      }
    }
  }

  return (
    <Layout>
      <main className="main-content">
      {loading && <div>Loading...</div>}
      
      {/* Show system status info instead of red error when system is inactive */}
      {systemStatus === false && (
        <div className="system-inactive-alert">
          ⚠️ System is currently inactive. Registration and queue access are disabled.
        </div>
      )}
      
      {/* Show errors only if they're not system inactive related */}
      {error && systemStatus !== false && (
        <div className="alert-error">Error: {error}</div>
      )}
      
      <div className={`top-section ${currentFrequency ? 'has-frequency' : 'frequency-hidden'}`}>
        {/* Current Active Callsign (Green Border) */}
        <CurrentActiveCallsign 
          activeUser={currentQso ? convertCurrentQsoToActiveUser(currentQso) : null}
          qrzData={currentQso?.qrz}
          metadata={currentQso?.metadata}
          onCompleteQso={async () => {}} // No-op async function for user page
          isAdminLoggedIn={false} // Always false on user page
        />

        {/* Frequency and Signal Display - Only show if frequency is set */}
        {currentFrequency && (
          <FrequencySignalPane className="frequency-signal-display" />
        )}
      </div>

      {/* Waiting Queue Container (Red Border) */}
      <WaitingQueue 
        queueData={queueData} 
        queueTotal={queueTotal}
        queueMaxSize={queueMaxSize}
        onAddCallsign={handleCallsignRegistration}
        isAdminLoggedIn={false} // Always false on user page
        systemActive={systemStatus === true}
      />

      {/* Mobile Frequency Display - Below queue for mobile priority */}
      {currentFrequency && (
        <div className="mobile-frequency-row">
          <FrequencySignalPane className="frequency-signal-display-mobile" />
        </div>
      )}
    </main>
    </Layout>
  )
}
