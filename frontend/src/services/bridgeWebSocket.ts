/**
 * Bridge WebSocket Service for QLog Integration
 * Connects to the local QLog Bridge to receive QSO events
 */

export interface QSOEvent {
  callsign: string
  timestamp: string
  source: 'adif' | 'plain_text' | 'wsjtx'
  frequency_mhz?: number
  mode?: string
}

export interface BridgeMessage {
  type: 'welcome' | 'qso_start' | 'pong' | 'status'
  data?: QSOEvent
  message?: string
  server_time?: number
}

export interface BridgeStatus {
  connected: boolean
  reconnecting: boolean
  lastEventTime: string | null
  connectionAttempts: number
}

export type QSOEventHandler = (qso: QSOEvent) => void
export type StatusChangeHandler = (status: BridgeStatus) => void

class BridgeWebSocketService {
  private ws: WebSocket | null = null
  private url = 'ws://localhost:8765'
  private reconnectTimer: number | null = null
  private reconnectDelay = 5000 // 5 seconds
  private maxReconnectAttempts = 10
  private connectionAttempts = 0
  private isIntentionallyDisconnected = false

  // Event handlers
  private qsoEventHandlers: Set<QSOEventHandler> = new Set()
  private statusChangeHandlers: Set<StatusChangeHandler> = new Set()

  // Status tracking
  private status: BridgeStatus = {
    connected: false,
    reconnecting: false,
    lastEventTime: null,
    connectionAttempts: 0
  }

  constructor() {
    console.log('BridgeWebSocketService initialized')
  }

  /**
   * Connect to the bridge WebSocket
   */
  connect(): void {
    if (this.ws?.readyState === WebSocket.OPEN) {
      console.log('🔌 Bridge WebSocket already connected')
      return
    }

    if (this.ws?.readyState === WebSocket.CONNECTING) {
      console.log('🔌 Bridge WebSocket already connecting')
      return
    }

    this.isIntentionallyDisconnected = false
    this.connectionAttempts++
    this.updateStatus({ connectionAttempts: this.connectionAttempts })

    console.log(`🚀 ATTEMPTING BRIDGE CONNECTION: ${this.url} (attempt ${this.connectionAttempts})`)

    try {
      this.ws = new WebSocket(this.url)
      console.log('✅ WebSocket object created, setting up event handlers...')
      this.setupEventHandlers()
    } catch (error) {
      console.error('🚨 Failed to create WebSocket connection:', error)
      this.scheduleReconnect()
    }
  }

  /**
   * Disconnect from the bridge WebSocket
   */
  disconnect(): void {
    console.log('Disconnecting from bridge WebSocket')
    this.isIntentionallyDisconnected = true
    
    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer)
      this.reconnectTimer = null
    }

    if (this.ws) {
      this.ws.close()
      this.ws = null
    }

    this.updateStatus({ 
      connected: false, 
      reconnecting: false 
    })
  }

  /**
   * Setup WebSocket event handlers
   */
  private setupEventHandlers(): void {
    if (!this.ws) return

    this.ws.onopen = () => {
      console.log('🎉 BRIDGE WEBSOCKET CONNECTED SUCCESSFULLY!')
      this.connectionAttempts = 0
      this.updateStatus({ 
        connected: true, 
        reconnecting: false,
        connectionAttempts: 0
      })

      // Send ping to test connection
      console.log('📤 Sending initial ping to bridge...')
      this.sendPing()
    }

    this.ws.onmessage = (event) => {
      console.log('📥 BRIDGE MESSAGE RECEIVED:', event.data)
      try {
        const message: BridgeMessage = JSON.parse(event.data)
        this.handleMessage(message)
      } catch (error) {
        console.error('🚨 Failed to parse bridge message:', error, event.data)
      }
    }

    this.ws.onclose = (event) => {
      console.log(`🔌 BRIDGE WEBSOCKET CLOSED: ${event.code} ${event.reason}`)
      this.updateStatus({ connected: false })

      if (!this.isIntentionallyDisconnected) {
        console.log('🔄 Scheduling reconnect since disconnect was not intentional...')
        this.scheduleReconnect()
      } else {
        console.log('⚠️ WebSocket closed intentionally, not reconnecting')
      }
    }

    this.ws.onerror = (error) => {
      console.error('🚨 BRIDGE WEBSOCKET ERROR:', error)
      this.updateStatus({ connected: false })
    }
  }

  /**
   * Handle incoming bridge messages
   */
  private handleMessage(message: BridgeMessage): void {
    console.log('Bridge message received:', message)

    switch (message.type) {
      case 'welcome':
        console.log('Bridge welcome:', message.message)
        break

      case 'qso_start':
        if (message.data) {
          console.log('QSO event received:', message.data)
          this.updateStatus({ lastEventTime: new Date().toISOString() })
          this.notifyQSOEventHandlers(message.data)
        }
        break

      case 'pong':
        console.log('Bridge pong received')
        break

      case 'status':
        console.log('Bridge status:', message.data)
        break

      default:
        console.warn('Unknown bridge message type:', message.type)
    }
  }

  /**
   * Schedule reconnection attempt
   */
  private scheduleReconnect(): void {
    if (this.isIntentionallyDisconnected) {
      return
    }

    if (this.connectionAttempts >= this.maxReconnectAttempts) {
      console.error(`Max reconnection attempts (${this.maxReconnectAttempts}) reached`)
      this.updateStatus({ reconnecting: false })
      return
    }

    this.updateStatus({ reconnecting: true })

    const delay = Math.min(this.reconnectDelay * this.connectionAttempts, 30000) // Max 30 seconds
    console.log(`Scheduling reconnection in ${delay}ms`)

    this.reconnectTimer = window.setTimeout(() => {
      this.connect()
    }, delay)
  }

  /**
   * Send ping to bridge
   */
  private sendPing(): void {
    if (this.ws?.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify({ type: 'ping' }))
    }
  }

  /**
   * Send status request to bridge
   */
  requestStatus(): void {
    if (this.ws?.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify({ type: 'status' }))
    }
  }

  /**
   * Add QSO event handler
   */
  onQSOEvent(handler: QSOEventHandler): void {
    this.qsoEventHandlers.add(handler)
  }

  /**
   * Remove QSO event handler
   */
  offQSOEvent(handler: QSOEventHandler): void {
    this.qsoEventHandlers.delete(handler)
  }

  /**
   * Add status change handler
   */
  onStatusChange(handler: StatusChangeHandler): void {
    this.statusChangeHandlers.add(handler)
  }

  /**
   * Remove status change handler
   */
  offStatusChange(handler: StatusChangeHandler): void {
    this.statusChangeHandlers.delete(handler)
  }

  /**
   * Get current connection status
   */
  getStatus(): BridgeStatus {
    return { ...this.status }
  }

  /**
   * Check if currently connected
   */
  isConnected(): boolean {
    return this.ws?.readyState === WebSocket.OPEN && this.status.connected
  }

  /**
   * Update status and notify handlers
   */
  private updateStatus(updates: Partial<BridgeStatus>): void {
    this.status = { ...this.status, ...updates }
    this.notifyStatusChangeHandlers(this.status)
  }

  /**
   * Notify QSO event handlers
   */
  private notifyQSOEventHandlers(qso: QSOEvent): void {
    this.qsoEventHandlers.forEach(handler => {
      try {
        handler(qso)
      } catch (error) {
        console.error('Error in QSO event handler:', error)
      }
    })
  }

  /**
   * Notify status change handlers
   */
  private notifyStatusChangeHandlers(status: BridgeStatus): void {
    this.statusChangeHandlers.forEach(handler => {
      try {
        handler(status)
      } catch (error) {
        console.error('Error in status change handler:', error)
      }
    })
  }
}

// Export singleton instance
export const bridgeWebSocketService = new BridgeWebSocketService()
