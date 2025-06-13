import './App.css'
import { useState, useEffect } from 'react'
import CurrentActiveCallsign, { type CurrentActiveUser } from './components/CurrentActiveCallsign'
import WaitingQueue from './components/WaitingQueue'
import AdminLogin from './components/AdminLogin'
import AdminSection from './components/AdminSection'
import { type QueueItemData } from './components/QueueItem'
import { adminApiService } from './services/adminApi'

// Sample data for demonstration
const sampleQueueData: QueueItemData[] = [
  { callsign: 'EI6JGB', location: 'San Juan, Puerto Rico' },
  { callsign: 'EI5JBB', location: 'Atlanta, Georgia' },
  { callsign: 'EI2HF', location: 'Vancouver, Canada' },
  
]

const currentActiveUser: CurrentActiveUser = {
  callsign: 'EI5JDB',
  name: 'Jack Daniels Burbon',
  location: 'Near Jamie, Clonmel, Ireland',
}

function App() {
  const [isAdminLoggedIn, setIsAdminLoggedIn] = useState(false)
  const [systemStatus, setSystemStatus] = useState<boolean | null>(null)

  useEffect(() => {
    // Check if admin is already logged in
    setIsAdminLoggedIn(adminApiService.isLoggedIn())
    
    // Load initial system status
    loadSystemStatus()
  }, [])

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
    // Could refresh queue data here if we had real queue data
  }

  return (
    <div className="pileup-buster-app">
      {/* Header */}
      <header className="header">
        <div className="hamburger-menu">
          <div className="hamburger-line"></div>
          <div className="hamburger-line"></div>
          <div className="hamburger-line"></div>
        </div>
        <h1 className="title">PILEUP BUSTER</h1>
        <AdminLogin 
          onLogin={handleAdminLogin}
          isLoggedIn={isAdminLoggedIn}
          onLogout={handleAdminLogout}
        />
      </header>

      <main className="main-content">
        {/* Current Active Callsign (Green Border) */}
        <CurrentActiveCallsign activeUser={currentActiveUser} />

        {/* Waiting Queue Container (Red Border) */}
        <WaitingQueue queueData={sampleQueueData} />

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
