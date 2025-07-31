import { API_BASE_URL } from '../config/api'

export interface QueueEntry {
  callsign: string
  timestamp: string
  position: number
  qrz?: {
    callsign?: string
    name?: string
    address?: string
    dxcc_name?: string
    image?: string
    error?: string
    grid?: {
      lat?: number
      long?: number
      grid?: string
    }
  }
}

export interface CurrentQsoData {
  callsign: string
  timestamp: string
  qrz?: {
    name?: string
    address?: string
    dxcc_name?: string
    image?: string
    url?: string
    grid?: {
      lat?: number
      long?: number
      grid?: string
    }
  }
  metadata?: {
    source?: 'queue' | 'direct'
    bridge_initiated?: boolean
    frequency_mhz?: number
    mode?: string
    started_via?: string
    bridge_timestamp?: string
  }
}

export interface PreviousQsoData {
  callsign: string
  worked_timestamp: string
  qrz?: {
    name?: string
    address?: string
    dxcc_name?: string
    image?: string
    url?: string
  }
  metadata?: {
    source?: 'queue' | 'direct'
    bridge_initiated?: boolean
    frequency_mhz?: number
    mode?: string
    started_via?: string
    bridge_timestamp?: string
  }
}

export interface WorkedCallerData {
  callsign: string
  worked_timestamp: string
  qrz?: {
    name?: string
    address?: string
    dxcc_name?: string
    image?: string
    url?: string
    grid?: {
      lat?: number
      long?: number
      grid?: string
    }
  }
  metadata?: {
    source?: 'queue' | 'direct'
    bridge_initiated?: boolean
    frequency_mhz?: number
    mode?: string
    started_via?: string
    bridge_timestamp?: string
  }
}

export interface WorkedCallersResponse {
  worked_callers: WorkedCallerData[]
  total: number
  system_active: boolean
}

export interface QueueListResponse {
  queue: QueueEntry[]
  total: number
  max_size: number
  system_active: boolean
}

export interface RegisterResponse {
  message: string
  entry: QueueEntry
}

export interface PreviousQsosResponse {
  previous_qsos: PreviousQsoData[]
  limit: number
  system_active: boolean
}

export class ApiError extends Error {
  status: number
  detail?: string

  constructor(
    message: string,
    status: number,
    detail?: string
  ) {
    super(message)
    this.name = 'ApiError'
    this.status = status
    this.detail = detail
  }
}

async function handleResponse<T>(response: Response): Promise<T> {
  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}))
    throw new ApiError(
      `HTTP ${response.status}: ${response.statusText}`,
      response.status,
      errorData.detail || response.statusText
    )
  }
  return response.json()
}

export const apiService = {
  // Register a new callsign in the queue
  async registerCallsign(callsign: string): Promise<RegisterResponse> {
    const response = await fetch(`${API_BASE_URL}/queue/register`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ callsign }),
    })
    return handleResponse<RegisterResponse>(response)
  },

  // Get current active callsign
  async getCurrentQso(): Promise<CurrentQsoData | null> {
    const response = await fetch(`${API_BASE_URL}/queue/current`)
    if (response.status === 404) {
      return null
    }
    return handleResponse<CurrentQsoData | null>(response)
  },

  // Get the waiting queue list
  async getQueueList(): Promise<QueueListResponse> {
    const response = await fetch(`${API_BASE_URL}/queue/list`)
    return handleResponse<QueueListResponse>(response)
  },

  // Get current frequency (public endpoint)
  async getCurrentFrequency(): Promise<{ frequency: string | null; last_updated: string | null }> {
    const response = await fetch(`${API_BASE_URL}/public/frequency`)
    return handleResponse<{ frequency: string | null; last_updated: string | null }>(response)
  },

  // Get current split (public endpoint)
  async getCurrentSplit(): Promise<{ split: string | null; last_updated: string | null }> {
    const response = await fetch(`${API_BASE_URL}/public/split`)
    return handleResponse<{ split: string | null; last_updated: string | null }>(response)
  },

  // Get system status (public endpoint)
  async getSystemStatus(): Promise<{ active: boolean }> {
    const response = await fetch(`${API_BASE_URL}/public/status`)
    return handleResponse<{ active: boolean }>(response)
  },

  // Get previous QSOs (public endpoint)
  async getPreviousQsos(limit: number = 10): Promise<PreviousQsosResponse> {
    const response = await fetch(`${API_BASE_URL}/public/previous-qsos?limit=${limit}`)
    return handleResponse<PreviousQsosResponse>(response)
  },

  // Get worked callers (public endpoint)
  async getWorkedCallers(): Promise<WorkedCallersResponse> {
    const response = await fetch(`${API_BASE_URL}/public/worked-callers`)
    return handleResponse<WorkedCallersResponse>(response)
  },
}