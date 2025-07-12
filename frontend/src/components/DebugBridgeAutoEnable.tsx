/**
 * Debug Bridge Auto-Enable
 * Temporarily auto-enables bridge for testing
 */

import { useEffect } from 'react'
import { useBridge } from '../contexts/BridgeContext'

export default function DebugBridgeAutoEnable() {
  const { bridgeEnabled, setBridgeEnabled } = useBridge()

  useEffect(() => {
    if (!bridgeEnabled) {
      console.log('🧪 DEBUG: Auto-enabling bridge for testing...')
      setBridgeEnabled(true)
    }
  }, [bridgeEnabled, setBridgeEnabled])

  return (
    <div style={{ 
      position: 'fixed', 
      bottom: '10px', 
      right: '10px', 
      background: '#f59e0b', 
      color: 'white', 
      padding: '8px 12px', 
      borderRadius: '4px', 
      fontSize: '0.75rem',
      zIndex: 9999
    }}>
      DEBUG: Bridge Auto-Enabled
    </div>
  )
}
