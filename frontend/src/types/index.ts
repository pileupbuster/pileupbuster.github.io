// API Response Types
export interface QueueEntry {
  callsign: string;
  timestamp: string;
  position: number;
  qrz?: QRZInfo;
}

export interface QRZInfo {
  name?: string;
  address?: string;
  country?: string;
  license_class?: string;
  error?: string;
}

export interface RegisterResponse {
  message: string;
  entry: QueueEntry;
}

export interface QueueListResponse {
  queue: QueueEntry[];
  total: number;
  admin?: boolean;
}

export interface AdminQueueResponse extends QueueListResponse {
  admin: true;
}

export interface RemoveCallsignResponse {
  message: string;
  removed: QueueEntry;
}

export interface ClearQueueResponse {
  message: string;
  cleared_count: number;
}

export interface NextCallsignResponse {
  message: string;
  processed: QueueEntry;
  remaining: number;
}

// Component Props Types
export interface CallsignFormProps {
  onRegister?: (callsign: string) => void;
}

export interface QueueDisplayProps {
  entries: QueueEntry[];
  isAdmin?: boolean;
  onRemove?: (callsign: string) => void;
}

export interface AdminLoginProps {
  onLogin: (credentials: AdminCredentials) => void;
  isLoading?: boolean;
  error?: string;
}

export interface AdminCredentials {
  username: string;
  password: string;
}

// Component State Types
export interface AppState {
  isAuthenticated: boolean;
  currentView: 'home' | 'admin' | 'status';
  userCallsign?: string;
}

export interface LoadingState {
  isLoading: boolean;
  error?: string;
}