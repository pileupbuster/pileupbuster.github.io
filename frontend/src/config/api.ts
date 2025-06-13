// Centralized API configuration
const getApiBaseUrl = (): string => {
  // Use environment variable if available, otherwise default to '/api' for development
  return import.meta.env.VITE_API_BASE_URL || '/api'
}

export const API_BASE_URL = getApiBaseUrl()