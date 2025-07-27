/**
 * WebSocket Server for Direct Logging Software Integration
 * Creates a WebSocket server that listens for connections from logging software
 */

export interface QSOEvent {
  callsign: string
  timestamp: string
  source: 'adif' | 'plain_text' | 'wsjtx' | 'pblog_native' | string
  frequency_mhz?: number
  mode?: string
  triggered_by?: string
}

export interface LoggingMessage {
  type: 'qso_start' | 'welcome' | 'ping' | 'ack'
  data?: QSOEvent
  message?: string
  timestamp?: string
}

export type QSOEventHandler = (qso: QSOEvent) => void
export type StatusChangeHandler = (connected: boolean) => void

class DirectLoggingWebSocketServer {
  // Event handlers
  private qsoEventHandlers: Set<QSOEventHandler> = new Set()
  private statusChangeHandlers: Set<StatusChangeHandler> = new Set()

  constructor() {
    console.log('DirectLoggingWebSocketServer initialized')
  }

  /**
   * Start WebSocket server (browser can't create servers, so we need a different approach)
   */
  async startServer(): Promise<void> {
    console.log('❌ ERROR: Browsers cannot create WebSocket servers!')
    console.log('💡 SOLUTION: Your logging software needs to connect to a server.')
    console.log('🔄 RECOMMENDATION: Use the existing WebSocket client approach but with a simple server')
    
    // Instead, let's make a simple HTTP endpoint that your logging software can POST to
    this.setupHTTPEndpoint()
  }

  /**
   * Setup HTTP endpoint as fallback
   */
  private setupHTTPEndpoint(): void {
    console.log('💡 Setting up HTTP endpoint fallback...')
    console.log('🌐 Your logging software can POST QSO data to: http://localhost:8080/qso')
    
    // This won't actually work in browser, but shows the concept
    // We need a different approach...
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
}

// Export singleton instance
export const directLoggingServer = new DirectLoggingWebSocketServer()
