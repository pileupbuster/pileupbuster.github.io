import { useState, useEffect } from 'react'
import { adminApiService } from '../services/adminApi'
import { apiService } from '../services/api'
import './AdminPage.css'

export default function AdminPage() {
  const [isLoggedIn, setIsLoggedIn] = useState(false)
  const [isLoggingIn, setIsLoggingIn] = useState(false)
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [systemStatus, setSystemStatus] = useState<boolean | null>(null)
  const [frequency, setFrequency] = useState('')
  const [split, setSplit] = useState('')
  const [frequencyError, setFrequencyError] = useState('')
  const [splitError, setSplitError] = useState('')

  useEffect(() => {
    // Check if already logged in
    setIsLoggedIn(adminApiService.isLoggedIn())
    
    // Load system status, frequency and split if logged in
    if (adminApiService.isLoggedIn()) {
      loadSystemStatus()
      loadCurrentFrequency()
      loadCurrentSplit()
    }
  }, [])

  const loadSystemStatus = async () => {
    try {
      const status = await adminApiService.getSystemStatus()
      setSystemStatus(status)
    } catch (error) {
      console.error('Failed to load system status:', error)
      setSystemStatus(false)
    }
  }

  const loadCurrentFrequency = async () => {
    try {
      const data = await apiService.getCurrentFrequency()
      console.log('Loaded frequency from API:', data)
      if (data.frequency) {
        setFrequency(data.frequency)
      }
    } catch (error) {
      console.error('Failed to load current frequency:', error)
    }
  }

  const loadCurrentSplit = async () => {
    try {
      const data = await apiService.getCurrentSplit()
      console.log('Loaded split from API:', data)
      if (data.split) {
        setSplit(data.split)
      }
    } catch (error) {
      console.error('Failed to load current split:', error)
    }
  }

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault()
    setIsLoggingIn(true)
    setError('')

    try {
      const success = await adminApiService.login(username, password)
      if (success) {
        setIsLoggedIn(true)
        setUsername('')
        setPassword('')
        await loadSystemStatus()
        await loadCurrentFrequency()
        await loadCurrentSplit()
      } else {
        setError('Invalid credentials. Please try again.')
      }
    } catch {
      setError('Login failed. Please check your connection and try again.')
    } finally {
      setIsLoggingIn(false)
    }
  }

  const handleLogout = () => {
    adminApiService.logout()
    setIsLoggedIn(false)
    setUsername('')
    setPassword('')
    setError('')
    setSystemStatus(null)
  }

  const handleToggleSystem = async () => {
    try {
      const newStatus = !systemStatus
      await adminApiService.setSystemStatus(newStatus)
      setSystemStatus(newStatus)
    } catch (error) {
      console.error('Failed to toggle system status:', error)
    }
  }

  const handleWorkNext = async () => {
    try {
      await adminApiService.workNextUser()
      // You could add a success message here
    } catch (error) {
      console.error('Failed to work next user:', error)
    }
  }

  const handleCompleteQso = async () => {
    try {
      await adminApiService.completeCurrentQso()
      // You could add a success message here
    } catch (error) {
      console.error('Failed to complete QSO:', error)
    }
  }

  const handleSetFrequency = async () => {
    if (!frequency.trim()) {
      setFrequencyError('Please enter a frequency')
      return
    }
    
    try {
      setFrequencyError('')
      console.log('Setting frequency:', frequency.trim())
      await adminApiService.setFrequency(frequency.trim())
      // Keep the frequency in the input field
      // Reload to see what the backend stored
      await loadCurrentFrequency()
    } catch (error) {
      console.error('Failed to set frequency:', error)
      setFrequencyError('Failed to set frequency')
    }
  }

  const handleClearFrequency = async () => {
    try {
      setFrequencyError('')
      await adminApiService.clearFrequency()
      setFrequency('')
    } catch (error) {
      console.error('Failed to clear frequency:', error)
      setFrequencyError('Failed to clear frequency')
    }
  }

  const handleSetSplit = async () => {
    if (!split.trim()) {
      setSplitError('Please enter a split frequency')
      return
    }
    
    try {
      setSplitError('')
      console.log('Setting split:', split.trim())
      await adminApiService.setSplit(split.trim())
      // Keep the split in the input field
      // Reload to see what the backend stored
      await loadCurrentSplit()
    } catch (error) {
      console.error('Failed to set split:', error)
      setSplitError('Failed to set split')
    }
  }

  const handleClearSplit = async () => {
    try {
      setSplitError('')
      await adminApiService.clearSplit()
      setSplit('')
    } catch (error) {
      console.error('Failed to clear split:', error)
      setSplitError('Failed to clear split')
    }
  }

  if (!isLoggedIn) {
    return (
      <div className="admin-page">
        <header className="admin-header">
          <div className="admin-logo">🔐 Admin Portal</div>
          <div>Pileup Buster Admin</div>
        </header>
        
        <main className="admin-main">
          <div className="admin-login-screen">
            <div className="admin-login-card">
              <h1 className="admin-login-title">Admin Access</h1>
              <p className="admin-login-subtitle">
                Please enter your admin credentials to access the system controls.
              </p>
              
              {error && <div className="admin-error">{error}</div>}
              
              <form className="admin-login-form" onSubmit={handleLogin}>
                <input
                  type="text"
                  placeholder="Username"
                  value={username}
                  onChange={(e) => setUsername(e.target.value)}
                  className="admin-input"
                  required
                  disabled={isLoggingIn}
                  autoFocus
                />
                <input
                  type="password"
                  placeholder="Password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="admin-input"
                  required
                  disabled={isLoggingIn}
                />
                <button
                  type="submit"
                  className="admin-login-button"
                  disabled={isLoggingIn}
                >
                  {isLoggingIn ? 'Logging in...' : 'Login'}
                </button>
              </form>
            </div>
          </div>
        </main>
      </div>
    )
  }

  return (
    <div className="admin-page">
      <header className="admin-header">
        <div className="admin-logo">⚡ Admin Dashboard</div>
        <div className="admin-status-bar">
          <div className="admin-user-info">
            <div className="admin-user-avatar">A</div>
            <span>Admin User</span>
          </div>
          <button className="admin-logout-button" onClick={handleLogout}>
            Logout
          </button>
        </div>
      </header>
      
      <main className="admin-main">
        <div className="admin-dashboard">
          <div className="admin-welcome">
            <h1 className="admin-welcome-title">System Control Panel</h1>
            <p>Manage your Pileup Buster system from here.</p>
          </div>

          <div className="admin-controls-grid">
            <div className="admin-control-card">
              <h3 className="admin-control-title">System Status</h3>
              <p className="admin-control-description">
                {systemStatus ? 'System is currently active and accepting registrations.' : 'System is currently disabled.'}
              </p>
              <button className="admin-control-button" onClick={handleToggleSystem}>
                {systemStatus ? 'Disable System' : 'Enable System'}
              </button>
            </div>

            <div className="admin-control-card">
              <h3 className="admin-control-title">Queue Management</h3>
              <p className="admin-control-description">
                Work with the next person in the queue.
              </p>
              <button className="admin-control-button" onClick={handleWorkNext}>
                Work Next User
              </button>
            </div>

            <div className="admin-control-card">
              <h3 className="admin-control-title">Current QSO</h3>
              <p className="admin-control-description">
                Complete the current QSO and move to the next.
              </p>
              <button className="admin-control-button" onClick={handleCompleteQso}>
                Complete Current QSO
              </button>
            </div>

            <div className="admin-control-card">
              <h3 className="admin-control-title">View Main Interface</h3>
              <p className="admin-control-description">
                Return to the main Pileup Buster interface.
              </p>
              <button 
                className="admin-control-button" 
                onClick={() => window.location.href = '/'}
              >
                Go to Main Page
              </button>
            </div>

            <div className="admin-control-card">
              <h3 className="admin-control-title">Frequency Management</h3>
              <p className="admin-control-description">
                Set or clear the current operating frequency.
              </p>
              {frequencyError && <div className="admin-error">{frequencyError}</div>}
              <div className="admin-input-group">
                <input
                  type="text"
                  placeholder="e.g., 14.205.00"
                  value={frequency}
                  onChange={(e) => setFrequency(e.target.value)}
                  className="admin-input"
                />
                <div className="admin-button-group">
                  <button className="admin-control-button" onClick={handleSetFrequency}>
                    Set Frequency
                  </button>
                  <button className="admin-control-button admin-secondary" onClick={handleClearFrequency}>
                    Clear Frequency
                  </button>
                </div>
              </div>
            </div>

            <div className="admin-control-card">
              <h3 className="admin-control-title">Split Management</h3>
              <p className="admin-control-description">
                Set or clear the split frequency for duplex operation.
              </p>
              {splitError && <div className="admin-error">{splitError}</div>}
              <div className="admin-input-group">
                <input
                  type="text"
                  placeholder="Up 5 to 10"
                  value={split}
                  onChange={(e) => setSplit(e.target.value)}
                  className="admin-input"
                />
                <div className="admin-button-group">
                  <button className="admin-control-button" onClick={handleSetSplit}>
                    Set Split
                  </button>
                  <button className="admin-control-button admin-secondary" onClick={handleClearSplit}>
                    Clear Split
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
      </main>
    </div>
  )
}