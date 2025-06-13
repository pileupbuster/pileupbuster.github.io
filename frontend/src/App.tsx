import { useState, useEffect, useCallback } from 'react'
import './App.css'
import pileupBusterLogo from './assets/pileup-buster-logo.svg'
import CurrentActiveCallsign, { type CurrentActiveUser } from './components/CurrentActiveCallsign'
import WaitingQueue from './components/WaitingQueue'
import AdminLogin from './components/AdminLogin'
import AdminSection from './components/AdminSection'
import { type QueueItemData } from './components/QueueItem'
import { apiService, type CurrentQsoData, type QueueEntry, ApiError } from './services/api'
import { adminApiService } from './services/adminApi'

function App() {
  // Real data state
  const [currentQso, setCurrentQso] = useState<CurrentQsoData | null>(null)
  const [queueData, setQueueData] = useState<QueueItemData[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  
  // Admin state
  const [isAdminLoggedIn, setIsAdminLoggedIn] = useState(false)
  const [systemStatus, setSystemStatus] = useState<boolean | null>(null)

  // Convert QueueEntry to QueueItemData format
  const convertQueueEntryToItemData = (entry: QueueEntry): QueueItemData => {
    return {
      callsign: entry.callsign,
      location: 'Location not available' // Backend doesn't provide location for queue items
    }
  }

  // Convert CurrentQsoData to CurrentActiveUser format
  const convertCurrentQsoToActiveUser = (qso: CurrentQsoData): CurrentActiveUser => {
    return {
      callsign: qso.callsign,
      name: qso.qrz?.name || 'Name not available',
      location: qso.qrz?.addr2 || 'Location not available'
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
    
    // Load initial system status
    loadSystemStatus()
  }, [])

  // Polling for real-time updates
  useEffect(() => {
    const interval = setInterval(() => {
      fetchCurrentQso()
      fetchQueueList()
    }, 5000) // Poll every 5 seconds

    return () => clearInterval(interval)
  }, [fetchCurrentQso, fetchQueueList])

  // Handle callsign registration
  const handleCallsignRegistration = async (callsign: string) => {
    try {
      await apiService.registerCallsign(callsign)
      // Refresh queue data after successful registration
      await fetchQueueList()
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
    }
    return success
  }

  const handleAdminLogout = () => {
    adminApiService.logout()
    setIsAdminLoggedIn(false)
  }

  const handleToggleSystemStatus = async (active: boolean): Promise<boolean> => {
    try {
      const newStatus = await adminApiService.setSystemStatus(active)
      setSystemStatus(newStatus)
      return true
    } catch (error) {
      console.error('Failed to toggle system status:', error)
      return false
    }
  }

  const handleWorkNextUser = async (): Promise<void> => {
    await adminApiService.workNextUser()
    // Refresh queue data after working next user
    await fetchQueueList()
  }

  return (
    <div className="pileup-buster-app">
      {/* Header */}
      <header className="header">
        <img 
          src={pileupBusterLogo} 
          alt="Pileup Buster Logo" 
          className="logo"
        />
        <AdminLogin 
          onLogin={handleAdminLogin}
          isLoggedIn={isAdminLoggedIn}
          onLogout={handleAdminLogout}
        />
      </header>

      <main className="main-content">
        {loading && <div>Loading...</div>}
        {error && <div style={{ color: 'red' }}>Error: {error}</div>}
        
        {/* Current Active Callsign (Green Border) */}
        <CurrentActiveCallsign 
          activeUser={currentQso ? convertCurrentQsoToActiveUser(currentQso) : null}
          qrzData={currentQso?.qrz}
        />

        {/* Waiting Queue Container (Red Border) */}
        <WaitingQueue 
          queueData={queueData} 
          onAddCallsign={handleCallsignRegistration}
        />

        {/* Admin Section - Only visible when logged in */}
        <AdminSection 
          isLoggedIn={isAdminLoggedIn}
          onToggleSystemStatus={handleToggleSystemStatus}
          onWorkNextUser={handleWorkNextUser}
          systemStatus={systemStatus}
        />
      </main>
    </div>
  )
}

export default App
