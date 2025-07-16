/**
 * Bridge Context for Direct Logging   // Handle bridge enabled state changes
  const handleSetBridgeEnabled = useCallback((enabled: boolean) => {
    localStorage.setItem('bridgeEnabled', JSON.stringify(enabled))
    setBridgeEnabled(enabled)
  }, [])egration
 * Now uses HTTP POST instead of WebSocket for better reliability
 */

import React, { createContext, useContext, useState, useCallback } from 'react'

interface QSOEvent {
  callsign: string
  timestamp: string
  source: string
  frequency_mhz?: number
  mode?: string
  triggered_by?: string
}

interface BridgeContextType {
  // Status
  lastQSOEvent: QSOEvent | null
  
  // Settings
  bridgeEnabled: boolean
  setBridgeEnabled: (enabled: boolean) => void
  
  // Info
  connectionInfo: string
}

const BridgeContext = createContext<BridgeContextType | undefined>(undefined)

interface BridgeProviderProps {
  children: React.ReactNode
}

export function BridgeProvider({ children }: BridgeProviderProps) {
  const [lastQSOEvent] = useState<QSOEvent | null>(null) // Will be updated via SSE events
  const [bridgeEnabled, setBridgeEnabled] = useState(() => {
    const saved = localStorage.getItem('bridgeEnabled')
    const enabled = saved ? JSON.parse(saved) === true : false
    return enabled
  })

  // Handle bridge enabled state changes
  const handleSetBridgeEnabled = useCallback((enabled: boolean) => {
    localStorage.setItem('bridgeEnabled', JSON.stringify(enabled))
    setBridgeEnabled(enabled)
    
    if (enabled) {
      console.log('✅ BRIDGE: HTTP POST integration enabled')
      console.log('� Your logging software should POST to: /api/admin/qso/logging-direct')
    } else {
      console.log('⛔ BRIDGE: HTTP POST integration disabled')
    }
  }, [])

  const connectionInfo = bridgeEnabled 
    ? "HTTP POST enabled - logging software should POST to /api/admin/qso/logging-direct"
    : "HTTP POST integration disabled"

  const contextValue: BridgeContextType = {
    lastQSOEvent,
    bridgeEnabled,
    setBridgeEnabled: handleSetBridgeEnabled,
    connectionInfo
  }

  return (
    <BridgeContext.Provider value={contextValue}>
      {children}
    </BridgeContext.Provider>
  )
}

// Hook to use bridge context
export const useBridge = () => {
  const context = useContext(BridgeContext)
  if (context === undefined) {
    throw new Error('useBridge must be used within a BridgeProvider')
  }
  return context
}

// Hook to use bridge status only (for components that just need status)
export const useBridgeStatus = () => {
  const { bridgeEnabled, connectionInfo } = useBridge()
  return { bridgeEnabled, connectionInfo }
}

// Hook to use QSO events only
export const useBridgeQSOEvents = () => {
  const { lastQSOEvent } = useBridge()
  return { lastQSOEvent }
}

// Default export for easier imports
export default BridgeProvider
