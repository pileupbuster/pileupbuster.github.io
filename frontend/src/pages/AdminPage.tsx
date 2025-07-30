import { useState, useEffect, useCallback, useRef } from 'react'
import Layout from '../components/Layout'
import AdminLogin from '../components/AdminLogin'
import CurrentActiveCallsign, { type CurrentActiveUser } from '../components/CurrentActiveCallsign'
import WaitingQueue from '../components/WaitingQueue'
import AdminSection from '../components/AdminSection'
import FrequencySignalPane from '../components/FrequencySignalPane'
import ScaleControl from '../components/ScaleControl'
import { type QueueItemData } from '../components/QueueItem'
import { apiService, type CurrentQsoData, type QueueEntry, ApiError } from '../services/api'
import { adminApiService } from '../services/adminApi'
import { sseService, type StateChangeEvent } from '../services/sse'

export default function AdminPage() {
  // UI Scale state
  const handleScaleChange = (scale: number) => {
    document.documentElement.style.setProperty('--ui-scale', scale.toString())
  }
  
  // Real data state
  const [currentQso, setCurrentQso] = useState<CurrentQsoData | null>(null)
  const [queueData, setQueueData] = useState<QueueItemData[]>([])
  const [queueTotal, setQueueTotal] = useState(0)
  const [queueMaxSize, setQueueMaxSize] = useState(4)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  
  // Admin state
  const [isAdminLoggedIn, setIsAdminLoggedIn] = useState(false)
  const [systemStatus, setSystemStatus] = useState<boolean | null>(null)
  const [currentFrequency, setCurrentFrequency] = useState<string | null>(null)
  const [loggerIntegrationEnabled, setLoggerIntegrationEnabled] = useState(false)

  // Ref to track previous callsign for clipboard functionality
  const previousCallsignRef = useRef<string | null>(null)

  // Utility function to copy text to clipboard
  const copyToClipboard = async (text: string): Promise<void> => {
    try {
      if (navigator.clipboard && window.isSecureContext) {
        // Use modern Clipboard API if available
        await navigator.clipboard.writeText(text)
        console.log(`Copied callsign to clipboard: ${text}`)
      } else {
        // Fallback for older browsers or insecure contexts
        const textArea = document.createElement('textarea')
        textArea.value = text
        textArea.style.position = 'fixed'
        textArea.style.left = '-999999px'
        textArea.style.top = '-999999px'
        document.body.appendChild(textArea)
        textArea.focus()
        textArea.select()
        
        try {
          document.execCommand('copy')
          console.log(`Copied callsign to clipboard (fallback): ${text}`)
        } catch (err) {
          console.warn('Failed to copy callsign to clipboard:', err)
        } finally {
          document.body.removeChild(textArea)
        }
      }
    } catch (err) {
      console.warn('Failed to copy callsign to clipboard:', err)
    }
  }

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
      // Update ref for initial load (don't copy to clipboard on initial load)
      previousCallsignRef.current = data?.callsign || null
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

  // Load admin system status
  const loadSystemStatus = async () => {
    try {
      const status = await adminApiService.getSystemStatus()
      setSystemStatus(status)
    } catch (error) {
      console.error('Failed to load system status:', error)
      // Set default status if can't load
      setSystemStatus(false)
    }
  }

  // Load logger integration status
  const loadLoggerIntegrationStatus = async () => {
    try {
      if (adminApiService.isLoggedIn()) {
        const enabled = await adminApiService.getLoggerIntegration()
        setLoggerIntegrationEnabled(enabled)
      }
    } catch (error) {
      console.error('Failed to load logger integration status:', error)
      setLoggerIntegrationEnabled(false) // Default to disabled on error
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
        fetchQueueList()
      ])
      
      setLoading(false)
    }

    loadData()
  }, [fetchCurrentQso, fetchQueueList])

  // Admin initialization
  useEffect(() => {
    // Check if admin is already logged in
    setIsAdminLoggedIn(adminApiService.isLoggedIn())
    
    // Load initial system status and frequency
    loadSystemStatus()
    loadCurrentFrequency()
    // Load logger integration status if admin is logged in
    if (adminApiService.isLoggedIn()) {
      loadLoggerIntegrationStatus()
    }
  }, [])

  // Real-time updates via Server-Sent Events (SSE)
  useEffect(() => {
    // Event handlers for different types of state changes
    const handleCurrentQsoEvent = (event: StateChangeEvent) => {
      console.log('Received current_qso event:', event)
      const newQso = event.data
      const newCallsign = newQso?.callsign
      
      // Update the ref with the new callsign
      previousCallsignRef.current = newCallsign || null
      
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
      // No additional state management needed at App level
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

  // Admin handlers
  const handleAdminLogin = async (username: string, password: string): Promise<boolean> => {
    const success = await adminApiService.login(username, password)
    if (success) {
      setIsAdminLoggedIn(true)
      // Reload system status after login
      await loadSystemStatus()
      // Load logger integration status after login
      await loadLoggerIntegrationStatus()
    }
    return success
  }

  const handleAdminLogout = () => {
    adminApiService.logout()
    setIsAdminLoggedIn(false)
  }

  const handleToggleSystemStatus = async (active: boolean): Promise<boolean> => {
    try {
      await adminApiService.setSystemStatus(active)
      // SSE will handle the system status update
      // No need to manually refresh data - SSE events will handle this
      
      return true
    } catch (error) {
      console.error('Failed to toggle system status:', error)
      return false
    }
  }

  const handleWorkNextUser = async (targetCallsign?: string): Promise<void> => {
    // For now, we'll keep the existing API that just works the next user in queue
    // The targetCallsign parameter is for future enhancement if we want to support
    // working specific users from the queue
    // eslint-disable-next-line @typescript-eslint/no-unused-vars
    targetCallsign; // Suppress unused parameter warning
    
    const newQso = await adminApiService.workNextUser()
    // Copy callsign to clipboard only for the user who clicked "work next"
    if (newQso?.callsign) {
      copyToClipboard(newQso.callsign)
    }
    // No need to manually refresh - SSE will broadcast the updates
  }

  const handleCompleteCurrentQso = async (): Promise<void> => {
    await adminApiService.completeCurrentQso()
    // No need to manually refresh - SSE will broadcast the updates
  }

  const handleSetFrequency = async (frequency: string): Promise<void> => {
    await adminApiService.setFrequency(frequency)
    // No need to manually refresh - SSE will broadcast the frequency update
    // But also update local state for immediate feedback
    setCurrentFrequency(frequency)
  }

  const handleClearFrequency = async (): Promise<void> => {
    await adminApiService.clearFrequency()
    // Update local state immediately
    setCurrentFrequency(null)
  }

  const handleSetSplit = async (split: string): Promise<void> => {
    await adminApiService.setSplit(split)
    // No need to manually refresh - SSE will broadcast the split update
  }

  const handleClearSplit = async (): Promise<void> => {
    await adminApiService.clearSplit()
    // No need to manually refresh - SSE will broadcast the split update
  }

  const handleToggleLoggerIntegration = async (enabled: boolean): Promise<void> => {
    try {
      await adminApiService.setLoggerIntegration(enabled)
      setLoggerIntegrationEnabled(enabled)
    } catch (error) {
      console.error('Failed to toggle logger integration:', error)
      throw error // Re-throw to let AdminSection handle the error
    }
  }

  return (
    <Layout 
      headerControls={
        <>
          <AdminLogin 
            onLogin={handleAdminLogin}
            isLoggedIn={isAdminLoggedIn}
            onLogout={handleAdminLogout}
          />
          {isAdminLoggedIn && <ScaleControl onScaleChange={handleScaleChange} />}
        </>
      }
    >
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
        {/* Admin QSO Control Buttons - Always visible on admin page when logged in */}
        {isAdminLoggedIn && (
          <div className="admin-qso-controls">
            <button 
              className="complete-qso-button"
              onClick={handleCompleteCurrentQso}
              disabled={!currentQso}
              title="Complete the current QSO without advancing the queue"
            >
              Complete Current QSO
            </button>
            <button 
              className="work-next-button"
              onClick={() => handleWorkNextUser()}
              disabled={queueTotal === 0}
              title="Work the next person in the queue (FIFO order)"
            >
              Work Next ({queueTotal} waiting)
            </button>
          </div>
        )}

        {/* Current Active Callsign (Green Border) */}
        <CurrentActiveCallsign 
          activeUser={currentQso ? convertCurrentQsoToActiveUser(currentQso) : null}
          qrzData={currentQso?.qrz}
          metadata={currentQso?.metadata}
          onCompleteQso={handleCompleteCurrentQso}
          isAdminLoggedIn={isAdminLoggedIn}
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
        isAdminLoggedIn={isAdminLoggedIn}
        systemActive={systemStatus === true}
      />

      {/* Mobile Frequency Display - Below queue for mobile priority */}
      {currentFrequency && (
        <div className="mobile-frequency-row">
          <FrequencySignalPane className="frequency-signal-display-mobile" />
        </div>
      )}

      {/* Admin Section - Always visible on admin page */}
      <AdminSection 
        isLoggedIn={isAdminLoggedIn}
        onToggleSystemStatus={handleToggleSystemStatus}
        onSetFrequency={handleSetFrequency}
        onClearFrequency={handleClearFrequency}
        onSetSplit={handleSetSplit}
        onClearSplit={handleClearSplit}
        systemStatus={systemStatus}
        currentFrequency={currentFrequency}
        loggerIntegrationEnabled={loggerIntegrationEnabled}
        onToggleLoggerIntegration={handleToggleLoggerIntegration}
      />
    </main>
    </Layout>
  )
}
