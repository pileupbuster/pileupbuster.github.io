import { useState, useEffect } from 'react'
import { apiService } from '../services/api'
import { sseService } from '../services/sse'

export interface FrequencySignalPaneProps {
  className?: string
}

// NOTE: Signal meter component was removed in July 2025.
// If you need to restore it, check git history before this date.

export default function FrequencySignalPane({ className = '' }: FrequencySignalPaneProps) {
  const [frequency, setFrequency] = useState<string | null>(null)
  const [split, setSplit] = useState('')
  const [lastUpdated, setLastUpdated] = useState<string | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [systemStatus, setSystemStatus] = useState<boolean | null>(null)

  useEffect(() => {
    // Load initial frequency and split
    const loadFrequencyData = async () => {
      try {
        const [frequencyData, splitData, statusData] = await Promise.all([
          apiService.getCurrentFrequency(),
          apiService.getCurrentSplit(),
          fetch(`${import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'}/public/status`).then(r => r.json())
        ])
        
        setFrequency(frequencyData.frequency)
        setLastUpdated(frequencyData.last_updated)
        setSplit(splitData.split || '')
        setSystemStatus(statusData.active)
      } catch (error) {
        console.error('Failed to load frequency/split/status:', error)
      } finally {
        setIsLoading(false)
      }
    }

    loadFrequencyData()

    // Listen for frequency updates via SSE
    const handleFrequencyUpdate = (event: { data: any }) => {
      const frequencyData = event.data
      setFrequency(frequencyData.frequency)
      setLastUpdated(frequencyData.last_updated)
    }

    // Listen for split updates via SSE
    const handleSplitUpdate = (event: { data: any }) => {
      const splitData = event.data
      setSplit(splitData.split || '')
    }

    // Listen for system status updates via SSE
    const handleSystemStatusUpdate = (event: { data: any }) => {
      const statusData = event.data
      setSystemStatus(statusData.active)
      
      // When system goes offline, clear split and frequency
      if (!statusData.active) {
        setSplit('')
        setFrequency(null)
        setLastUpdated(null)
      }
    }

    sseService.addEventListener('frequency_update', handleFrequencyUpdate)
    sseService.addEventListener('split_update', handleSplitUpdate)
    sseService.addEventListener('system_status', handleSystemStatusUpdate)

    // Cleanup
    return () => {
      // Note: SSE service doesn't provide removeEventListener in current implementation
      // This would need to be added if we want proper cleanup
    }
  }, [])

  // Parse frequency string to display as KHz with thousand separators
  const formatFrequency = (freq: string | null): string => {
    if (!freq) return systemStatus === false ? '' : '0,000.00'
    
    // Try to parse frequency and format as KHz
    try {
      // Remove "MHz" or "KHz" suffix if present and extract numeric value
      const numericValue = freq.replace(/\s*(MHz|KHz)\s*$/i, '').trim()
      let parsed = parseFloat(numericValue)
      
      if (isNaN(parsed)) return freq // Return original if can't parse
      
      // If the input was in MHz, convert to KHz
      if (freq.toLowerCase().includes('mhz') || parsed < 1000) {
        parsed = parsed * 1000 // Convert MHz to KHz
      }
      
      // Format as XX,XXX.XX (like 14,315.00)
      return parsed.toFixed(2).replace(/\B(?=(\d{3})+(?!\d))/g, ',')
    } catch {
      return freq // Return original on error
    }
  }

  if (isLoading) {
    return (
      <div className={`frequency-signal-pane loading ${className}`}>
        <div className="frequency-display-large">Loading...</div>
      </div>
    )
  }

  return (
    <div className={`frequency-signal-pane ${className} ${systemStatus === false ? 'offline' : ''}`}>
      <div className="frequency-display-large">
        {formatFrequency(frequency)}{systemStatus !== false ? ' KHz' : ''}
        <span className={systemStatus ? 'online-indicator' : 'offline-indicator'}>
          {systemStatus ? 'ONLINE' : 'OFFLINE'}
        </span>
      </div>
      
      {/* Split Display only if split is set and not zero */}
      {split && split !== '0'  ? (
              <div className="split-section">
          <div className="split-display">
            SPLIT {split}
          </div>
        </div>
      ) : null}

      {/* NOTE: Signal meter was removed in July 2025 */}
      {lastUpdated && (
        <div className="frequency-updated">
          Updated: {new Date(lastUpdated).toLocaleTimeString()}
        </div>
      )}
    </div>
  )
}