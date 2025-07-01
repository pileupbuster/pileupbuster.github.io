import { useState, useEffect } from 'react'

export interface AdminSectionProps {
  isLoggedIn: boolean
  onToggleSystemStatus: (active: boolean) => Promise<boolean>
  onSetFrequency: (frequency: string) => Promise<void>
  onClearFrequency: () => Promise<void>
  onSetSplit: (split: string) => Promise<void>
  onClearSplit: () => Promise<void>
  systemStatus: boolean | null
  currentFrequency: string | null
}

export default function AdminSection({ 
  isLoggedIn, 
  onToggleSystemStatus, 
  onSetFrequency,
  onClearFrequency,
  onSetSplit,
  onClearSplit,
  systemStatus,
  currentFrequency
}: AdminSectionProps) {
  const [isTogglingStatus, setIsTogglingStatus] = useState(false)
  const [frequency, setFrequency] = useState('')
  const [isSettingFrequency, setIsSettingFrequency] = useState(false)
  const [isClearingFrequency, setIsClearingFrequency] = useState(false)
  const [split, setSplit] = useState('')
  const [isSettingSplit, setIsSettingSplit] = useState(false)
  const [isClearingSplit, setIsClearingSplit] = useState(false)

  // Initialize frequency input with current frequency only on component mount or when cleared
  useEffect(() => {
    // Only sync when frequency is cleared (null) or on initial load when input is empty
    if (currentFrequency === null) {
      setFrequency('')
    } else if (currentFrequency && frequency === '') {
      // Only set if our local input is completely empty (initial state)
      setFrequency(currentFrequency)
    }
  }, [currentFrequency]) // Remove frequency from dependencies to prevent constant resets

  if (!isLoggedIn) {
    return null
  }

  const handleToggleStatus = async () => {
    if (systemStatus === null) return
    
    setIsTogglingStatus(true)
    try {
      await onToggleSystemStatus(!systemStatus)
    } catch (error) {
      console.error('Failed to toggle system status:', error)
    } finally {
      setIsTogglingStatus(false)
    }
  }

  const handleSetFrequency = async () => {
    if (!frequency.trim()) return
    
    setIsSettingFrequency(true)
    try {
      await onSetFrequency(frequency.trim())
      // Don't clear input - keep it for persistence as requested
    } catch (error) {
      console.error('Failed to set frequency:', error)
    } finally {
      setIsSettingFrequency(false)
    }
  }

  const handleClearFrequency = async () => {
    setIsClearingFrequency(true)
    try {
      await onClearFrequency()
      setFrequency('') // Clear the input when frequency is cleared
    } catch (error) {
      console.error('Failed to clear frequency:', error)
    } finally {
      setIsClearingFrequency(false)
    }
  }

  const handleSetSplit = async () => {
    if (!split.trim()) return
    
    setIsSettingSplit(true)
    try {
      await onSetSplit(split.trim())
      setSplit('') // Clear input after successful set
    } catch (error) {
      console.error('Failed to set split:', error)
    } finally {
      setIsSettingSplit(false)
    }
  }

  const handleClearSplit = async () => {
    setIsClearingSplit(true)
    try {
      await onClearSplit()
      setSplit('') // Clear input when split is cleared
    } catch (error) {
      console.error('Failed to clear split:', error)
    } finally {
      setIsClearingSplit(false)
    }
  }

  return (
    <section className="admin-section">
      <h2 className="admin-title">Admin Controls</h2>
      <div className="admin-controls">
        <div className="admin-actions-group">

          {/* Frequency Controls */}
          <div className="frequency-control">
            <label className="frequency-label">
              <span className="frequency-label-text">Set Frequency:</span>
              <div className="frequency-input-group">
                <input
                  type="text"
                  value={frequency}
                  onChange={(e) => setFrequency(e.target.value)}
                  placeholder="e.g., 14.315 or 14315.00 KHz"
                  className="frequency-input"
                  disabled={isSettingFrequency || isClearingFrequency}
                  tabIndex={-1}
                />
                <div className="mobile-button-row">
                  <button
                    className="frequency-button"
                    onClick={handleSetFrequency}
                    disabled={isSettingFrequency || isClearingFrequency || !frequency.trim()}
                    type="button"
                  >
                    {isSettingFrequency ? 'Setting...' : 'Set'}
                  </button>
                  <button
                    className="frequency-clear-button"
                    onClick={handleClearFrequency}
                    disabled={isSettingFrequency || isClearingFrequency}
                    type="button"
                  >
                    {isClearingFrequency ? 'Clearing...' : 'Clear'}
                  </button>
                </div>
              </div>
            </label>
          </div>

          {/* Split Controls */}
          <div className="split-control">
            <label className="split-label">
              <span className="split-label-text">Set Split:</span>
              <div className="split-input-group">
                <input
                  type="text"
                  value={split}
                  onChange={(e) => setSplit(e.target.value)}
                  placeholder="e.g., +3, +5, +5-10"
                  className="split-input"
                  disabled={isSettingSplit || isClearingSplit}
                  tabIndex={-1}
                />
                <div className="mobile-button-row">
                  <button
                    className="split-button"
                    onClick={handleSetSplit}
                    disabled={isSettingSplit || isClearingSplit || !split.trim()}
                    type="button"
                  >
                    {isSettingSplit ? 'Setting...' : 'Set Split'}
                  </button>
                  <button
                    className="split-clear-button"
                    onClick={handleClearSplit}
                    disabled={isSettingSplit || isClearingSplit}
                    type="button"
                  >
                    {isClearingSplit ? 'Clearing...' : 'Clear Split'}
                  </button>
                </div>
              </div>
            </label>
          </div>
        </div>

        {/* System Status - Far Right */}
        <div className="system-status-control">
          <label className="status-toggle-label">
            <span className="status-label">System Status:</span>
            <div className="toggle-container">
              <button
                className={`toggle-button ${systemStatus ? 'active' : 'inactive'}`}
                onClick={handleToggleStatus}
                disabled={isTogglingStatus || systemStatus === null}
                type="button"
              >
                <div className="toggle-slider">
                  <div className="toggle-knob"></div>
                </div>
                <span className="toggle-text">
                  {systemStatus === null ? 'Loading...' : systemStatus ? 'ACTIVE' : 'INACTIVE'}
                </span>
              </button>
            </div>
          </label>
        </div>
      </div>
    </section>
  )
}