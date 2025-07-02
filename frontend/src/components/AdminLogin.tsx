import { useState } from 'react'

export interface AdminLoginProps {
  onLogin: (username: string, password: string) => Promise<boolean>
  isLoggedIn: boolean
  onLogout: () => void
}

export default function AdminLogin({ onLogin, isLoggedIn, onLogout }: AdminLoginProps) {
  const [showLoginForm, setShowLoginForm] = useState(false)
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [isLoggingIn, setIsLoggingIn] = useState(false)
  const [error, setError] = useState('')

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault()
    setIsLoggingIn(true)
    setError('')

    try {
      const success = await onLogin(username, password)
      if (success) {
        setShowLoginForm(false)
        setUsername('')
        setPassword('')
      } else {
        setError('Invalid credentials')
      }
    } catch {
      setError('Login failed. Please try again.')
    } finally {
      setIsLoggingIn(false)
    }
  }

  const handleLogout = () => {
    onLogout()
    setShowLoginForm(false)
    setUsername('')
    setPassword('')
    setError('')
  }

  if (isLoggedIn) {
    return (
      <div className="admin-status">
        <span className="admin-chip admin-logged-in">
          Admin
        </span>
        <button 
          className="admin-logout-button"
          onClick={handleLogout}
          type="button"
        >
          Logout
        </button>
      </div>
    )
  }

  return (
    <div className="admin-login">
      {!showLoginForm ? (
        <button 
          className="admin-chip admin-login-button"
          onClick={() => setShowLoginForm(true)}
          type="button"
        >
          🔐 Admin Login
        </button>
      ) : (
        <form className="admin-login-form" onSubmit={handleLogin}>
          <div className="login-form-header">
            <h3>Admin Login</h3>
            <button 
              type="button"
              className="close-button"
              onClick={() => setShowLoginForm(false)}
            >
              ✕
            </button>
          </div>
          {error && <div className="login-error">{error}</div>}
          <div className="login-fields">
            <input
              type="text"
              placeholder="Username"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              required
              disabled={isLoggingIn}
              className="login-input"
              tabIndex={1}
              autoFocus
            />
            <input
              type="password"
              placeholder="Password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              disabled={isLoggingIn}
              className="login-input"
              tabIndex={2}
            />
          </div>
          <div className="login-actions">
            <button 
              type="submit"
              disabled={isLoggingIn}
              className="login-submit-button"
              tabIndex={3}
            >
              {isLoggingIn ? 'Logging in...' : 'Login'}
            </button>
            <button 
              type="button" 
              onClick={() => setShowLoginForm(false)}
              disabled={isLoggingIn}
              className="cancel-button"
              tabIndex={4}
            >
              Cancel
            </button>
          </div>
        </form>
      )}
    </div>
  )
}