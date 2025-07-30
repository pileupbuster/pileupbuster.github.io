import { useState, useEffect } from 'react'
import { adminApiService } from '../services/adminApi'
import './AdminPage.css'

interface AdminPageProps {}

export default function AdminPage({}: AdminPageProps) {
  const [isLoggedIn, setIsLoggedIn] = useState(false)
  const [isLoggingIn, setIsLoggingIn] = useState(false)
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [systemStatus, setSystemStatus] = useState<boolean | null>(null)

  useEffect(() => {
    // Check if already logged in
    setIsLoggedIn(adminApiService.isLoggedIn())
    
    // Load system status if logged in
    if (adminApiService.isLoggedIn()) {
      loadSystemStatus()
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
      } else {
        setError('Invalid credentials. Please try again.')
      }
    } catch (err) {
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
          </div>
        </div>
      </main>
    </div>
  )
}