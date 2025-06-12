import {
  RegisterResponse,
  QueueEntry,
  QueueListResponse,
  AdminQueueResponse,
  RemoveCallsignResponse,
  ClearQueueResponse,
  NextCallsignResponse,
  AdminCredentials,
} from '../types';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000/api';

class ApiError extends Error {
  constructor(public status: number, message: string) {
    super(message);
    this.name = 'ApiError';
  }
}

const handleResponse = async (response: Response) => {
  if (!response.ok) {
    const errorData = await response.json().catch(() => ({ detail: 'Unknown error' }));
    throw new ApiError(response.status, errorData.detail || `HTTP ${response.status}`);
  }
  return response.json();
};

// Public API endpoints
export const queueApi = {
  // Register a callsign
  async register(callsign: string): Promise<RegisterResponse> {
    const response = await fetch(`${API_BASE_URL}/queue/register`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ callsign }),
    });
    return handleResponse(response);
  },

  // Get callsign status
  async getStatus(callsign: string): Promise<QueueEntry> {
    const response = await fetch(`${API_BASE_URL}/queue/status/${encodeURIComponent(callsign)}`);
    return handleResponse(response);
  },

  // Get queue list
  async getList(): Promise<QueueListResponse> {
    const response = await fetch(`${API_BASE_URL}/queue/list`);
    return handleResponse(response);
  },
};

// Admin API endpoints
export const adminApi = {
  // Get admin queue view
  async getQueue(credentials: AdminCredentials): Promise<AdminQueueResponse> {
    const authHeader = 'Basic ' + btoa(`${credentials.username}:${credentials.password}`);
    const response = await fetch(`${API_BASE_URL}/admin/queue`, {
      headers: {
        'Authorization': authHeader,
      },
    });
    return handleResponse(response);
  },

  // Remove callsign from queue
  async removeCallsign(callsign: string, credentials: AdminCredentials): Promise<RemoveCallsignResponse> {
    const authHeader = 'Basic ' + btoa(`${credentials.username}:${credentials.password}`);
    const response = await fetch(`${API_BASE_URL}/admin/queue/${encodeURIComponent(callsign)}`, {
      method: 'DELETE',
      headers: {
        'Authorization': authHeader,
      },
    });
    return handleResponse(response);
  },

  // Clear entire queue
  async clearQueue(credentials: AdminCredentials): Promise<ClearQueueResponse> {
    const authHeader = 'Basic ' + btoa(`${credentials.username}:${credentials.password}`);
    const response = await fetch(`${API_BASE_URL}/admin/queue/clear`, {
      method: 'POST',
      headers: {
        'Authorization': authHeader,
      },
    });
    return handleResponse(response);
  },

  // Process next callsign
  async processNext(credentials: AdminCredentials): Promise<NextCallsignResponse> {
    const authHeader = 'Basic ' + btoa(`${credentials.username}:${credentials.password}`);
    const response = await fetch(`${API_BASE_URL}/admin/queue/next`, {
      method: 'POST',
      headers: {
        'Authorization': authHeader,
      },
    });
    return handleResponse(response);
  },
};

export { ApiError };