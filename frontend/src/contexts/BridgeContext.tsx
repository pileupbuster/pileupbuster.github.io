/**
 * Bridge Context for QLog Integration
 * Provides bridge connection state and QSO events throughout the app
 */

import React, { createContext, useContext, useEffect, useState, useCallback } from 'react'
import { bridgeWebSocketService } from '../services/bridgeWebSocket'
import type { QSOEvent, BridgeStatus } from '../services/bridgeWebSocket'

interface BridgeContextType {
  // Connection state
  bridgeStatus: BridgeStatus
  isConnected: boolean
  
  // QSO events
  lastQSOEvent: QSOEvent | null
  
  // Control methods
  connect: () => void
  disconnect: () => void
  requestStatus: () => void
  
  // Settings
  bridgeEnabled: boolean
  setBridgeEnabled: (enabled: boolean) => void
}

const BridgeContext = createContext<BridgeContextType | undefined>(undefined)

interface BridgeProviderProps {
  children: React.ReactNode
}

export function BridgeProvider({ children }: BridgeProviderProps) {
  // State
  const [bridgeStatus, setBridgeStatus] = useState<BridgeStatus>(bridgeWebSocketService.getStatus())
  const [lastQSOEvent, setLastQSOEvent] = useState<QSOEvent | null>(null)
  const [bridgeEnabled, setBridgeEnabled] = useState(() => {
    // Load from localStorage
    const saved = localStorage.getItem('bridgeEnabled')
    const enabled = saved ? JSON.parse(saved) === true : false
    console.log('🏗️ BRIDGE CONTEXT: Initializing with bridge enabled =', enabled)
    return enabled
  })

  // Validate QSO event structure
  const isValidQSOEvent = (qsoData: any): qsoData is QSOEvent => {
    return (
      qsoData &&
      typeof qsoData.callsign === 'string' &&
      qsoData.callsign.length > 2 &&
      typeof qsoData.timestamp === 'string' &&
      typeof qsoData.source === 'string'
    )
  }

  // Handle QSO events
  const handleQSOEvent = useCallback(async (qso: QSOEvent) => {
    console.log('🎉 BRIDGE CONTEXT: QSO Event Received!', qso)
    console.log('📻 Callsign:', qso.callsign)
    console.log('⏰ Timestamp:', qso.timestamp)
    console.log('📡 Source:', qso.source)
    if (qso.mode) console.log('📻 Mode:', qso.mode)
    if (qso.frequency_mhz) console.log('🔊 Frequency:', qso.frequency_mhz, 'MHz')
    
    setLastQSOEvent(qso)
    
    // Validate QSO event structure
    if (!isValidQSOEvent(qso)) {
      console.warn('⚠️ BRIDGE: Invalid QSO event received:', qso)
      return
    }
    
    // Process QSO event through backend API
    try {
      console.log('🔄 BRIDGE: Processing QSO through backend API...')
      
      const adminCredentials = localStorage.getItem('admin_credentials')
      console.log('🔍 BRIDGE: Checking admin auth...', adminCredentials ? 'AUTH FOUND' : 'NO AUTH')
      
      if (!adminCredentials) {
        console.warn('⚠️ BRIDGE: No admin auth available - QSO processing skipped')
        console.warn('💡 BRIDGE: To auto-process QSOs, please log in as admin')
        return
      }
      
      const credentials = JSON.parse(adminCredentials)
      const authHeader = 'Basic ' + btoa(`${credentials.username}:${credentials.password}`)
      
      console.log('🔑 BRIDGE: Admin auth found, making API call...')
      console.log('📤 BRIDGE: Sending request body:', JSON.stringify({
        callsign: qso.callsign,
        frequency: qso.frequency_mhz,
        mode: qso.mode,
        source: 'bridge'
      }, null, 2))
      
      const response = await fetch('/api/admin/qso/bridge-start', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': authHeader
        },
        body: JSON.stringify({
          callsign: qso.callsign,
          frequency: qso.frequency_mhz,
          mode: qso.mode,
          source: 'bridge'
        })
      })
      
      console.log('📡 BRIDGE: API response status:', response.status)
      console.log('📡 BRIDGE: API response headers:', Object.fromEntries(response.headers.entries()))
      
      if (response.ok) {
        const result = await response.json()
        console.log('✅ BRIDGE: QSO processed successfully:', result)
        console.log('📊 Source:', result.source)
        console.log('🔄 Was in queue:', result.was_in_queue)
        if (result.cleared_qso) {
          console.log('🧹 Cleared previous QSO:', result.cleared_qso.callsign)
        }
      } else {
        const errorText = await response.text()
        console.error('❌ BRIDGE: Failed to process QSO:', response.status, errorText)
        
        if (response.status === 401) {
          console.error('🔐 BRIDGE: Authentication failed - please re-login as admin')
        } else if (response.status === 403) {
          console.error('🚫 BRIDGE: Access forbidden - admin privileges required')
        }
      }
    } catch (error) {
      console.error('❌ BRIDGE: Error processing QSO event:', error)
      if (error instanceof TypeError && error.message.includes('Failed to fetch')) {
        console.error('🌐 BRIDGE: Network error - check if backend is running')
      }
    }
  }, [])

  // Handle status changes
  const handleStatusChange = useCallback((status: BridgeStatus) => {
    console.log('🌐 BRIDGE STATUS CHANGED:', status)
    console.log('Connected:', status.connected)
    console.log('Reconnecting:', status.reconnecting)
    console.log('Connection Attempts:', status.connectionAttempts)
    console.log('Last Event Time:', status.lastEventTime)
    setBridgeStatus(status)
  }, [])

  // Control methods
  const connect = useCallback(() => {
    console.log('🔌 BRIDGE: Attempting to connect to WebSocket...')
    bridgeWebSocketService.connect()
  }, [])

  const disconnect = useCallback(() => {
    console.log('🔌 BRIDGE: Disconnecting from WebSocket...')
    bridgeWebSocketService.disconnect()
  }, [])

  const requestStatus = useCallback(() => {
    bridgeWebSocketService.requestStatus()
  }, [])

  // Handle bridge enabled state changes
  useEffect(() => {
    // Save to localStorage
    localStorage.setItem('bridgeEnabled', JSON.stringify(bridgeEnabled))
    
    console.log('🔧 BRIDGE: Bridge enabled state changed to:', bridgeEnabled)
    
    if (bridgeEnabled) {
      console.log('🚀 BRIDGE: Starting bridge connection...')
      connect()
    } else {
      console.log('⛔ BRIDGE: Stopping bridge connection...')
      disconnect()
    }
  }, [bridgeEnabled, connect, disconnect])

  // Setup event handlers
  useEffect(() => {
    bridgeWebSocketService.onQSOEvent(handleQSOEvent)
    bridgeWebSocketService.onStatusChange(handleStatusChange)

    return () => {
      bridgeWebSocketService.offQSOEvent(handleQSOEvent)
      bridgeWebSocketService.offStatusChange(handleStatusChange)
    }
  }, [handleQSOEvent, handleStatusChange])

  // Derived state
  const isConnected = bridgeStatus.connected

  const contextValue: BridgeContextType = {
    // Connection state
    bridgeStatus,
    isConnected,
    
    // QSO events
    lastQSOEvent,
    
    // Control methods
    connect,
    disconnect,
    requestStatus,
    
    // Settings
    bridgeEnabled,
    setBridgeEnabled
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
  const { bridgeStatus, isConnected } = useBridge()
  return { bridgeStatus, isConnected }
}

// Hook to use QSO events only
export const useBridgeQSOEvents = () => {
  const { lastQSOEvent } = useBridge()
  return { lastQSOEvent }
}

// Default export for easier imports
export default BridgeProvider
