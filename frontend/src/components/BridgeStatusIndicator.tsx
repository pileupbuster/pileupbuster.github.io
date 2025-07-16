/**
 * Bridge Status Indicator Component
 * Shows HTTP POST integration status for direct logging software integration
 */

import { useBridge } from '../contexts/BridgeContext'

interface BridgeStatusIndicatorProps {
  className?: string
}

export default function BridgeStatusIndicator({ className = '' }: BridgeStatusIndicatorProps) {
  const { 
    bridgeEnabled, 
    setBridgeEnabled,
    lastQSOEvent 
  } = useBridge()

  const handleToggleBridge = () => {
    setBridgeEnabled(!bridgeEnabled)
  }

  const getStatusColor = () => {
    return bridgeEnabled ? '#10b981' : '#6b7280' // green if enabled, gray if disabled
  }

  const getStatusText = () => {
    return bridgeEnabled ? 'HTTP POST Integration Enabled' : 'HTTP POST Integration Disabled'
  }

  const indicatorStyle = {
    background: '#f8fafc',
    border: '1px solid #e2e8f0',
    borderRadius: '8px',
    padding: '12px',
    margin: '8px 0'
  }

  const headerStyle = {
    display: 'flex',
    alignItems: 'center',
    gap: '8px'
  }

  const dotStyle = {
    width: '12px',
    height: '12px',
    borderRadius: '50%',
    backgroundColor: getStatusColor(),
    transition: 'background-color 0.3s ease'
  }

  const textStyle = {
    fontWeight: '500',
    color: '#374151',
    flexGrow: 1
  }

  const buttonStyle = {
    padding: '4px 12px',
    borderRadius: '4px',
    border: 'none',
    fontWeight: '600',
    fontSize: '0.75rem',
    cursor: 'pointer',
    transition: 'all 0.2s ease',
    background: bridgeEnabled ? '#10b981' : '#6b7280',
    color: 'white'
  }

  const detailsStyle = {
    marginTop: '8px',
    paddingTop: '8px',
    borderTop: '1px solid #e5e7eb'
  }

  const infoStyle = {
    fontSize: '0.875rem',
    color: '#6b7280',
    marginBottom: '8px',
    lineHeight: '1.4'
  }

  const endpointStyle = {
    fontSize: '0.75rem',
    color: '#059669',
    background: '#ecfdf5',
    padding: '6px 8px',
    borderRadius: '4px',
    fontFamily: 'monospace',
    border: '1px solid #a7f3d0',
    marginBottom: '8px'
  }

  const qsoEventStyle = {
    fontSize: '0.875rem',
    color: '#059669',
    background: '#ecfdf5',
    padding: '4px 8px',
    borderRadius: '4px',
    borderLeft: '3px solid #10b981'
  }

  return (
    <div className={`bridge-status-indicator ${className}`} style={indicatorStyle}>
      <div className="bridge-status-section">
        <div className="bridge-status-header" style={headerStyle}>
          <div className="bridge-status-dot" style={dotStyle} />
          <span className="bridge-status-text" style={textStyle}>{getStatusText()}</span>
          <button 
            className={`bridge-toggle-btn ${bridgeEnabled ? 'enabled' : 'disabled'}`}
            style={buttonStyle}
            onClick={handleToggleBridge}
            title={bridgeEnabled ? 'Disable Logging Integration' : 'Enable Logging Integration'}
          >
            {bridgeEnabled ? 'ON' : 'OFF'}
          </button>
        </div>
        
        {bridgeEnabled && (
          <div className="bridge-status-details" style={detailsStyle}>
            <div className="bridge-connection-info" style={infoStyle}>
              Configure your logging software to POST QSO data to:
            </div>
            
            <div className="endpoint-info" style={endpointStyle}>
              POST http://localhost:8000/api/admin/qso/logging-direct
            </div>
            
            <div className="format-info" style={infoStyle}>
              Expected format: {`{"type": "qso_start", "data": {...}}`}
            </div>
            
            {lastQSOEvent && (
              <div className="last-qso-event" style={qsoEventStyle}>
                <strong style={{ color: '#047857' }}>Last QSO:</strong> {lastQSOEvent.callsign}
                {lastQSOEvent.mode && <span> ({lastQSOEvent.mode})</span>}
                {lastQSOEvent.frequency_mhz && (
                  <span> on {lastQSOEvent.frequency_mhz} MHz</span>
                )}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  )
}
