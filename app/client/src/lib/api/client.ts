// API client configuration
// In dev: uses Vite proxy (/api -> http://localhost:SERVER_PORT/api)
// In prod: uses VITE_API_URL from environment
const API_BASE_URL = import.meta.env.DEV
  ? '/api'  // Proxy to backend in development
  : import.meta.env.VITE_API_URL || 'http://localhost:8000/api';

// Generic API request function
async function apiRequest<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> {
  const url = `${API_BASE_URL}${endpoint}`;

  try {
    const response = await fetch(url, {
      ...options,
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({ message: 'Request failed' }));
      throw new Error(error.message || `HTTP ${response.status}`);
    }

    return await response.json();
  } catch (error) {
    console.error('API request failed:', error);
    throw error;
  }
}

// Export API methods
export const api = {
  // Health check
  async healthCheck() {
    return apiRequest<{ status: string }>('/health');
  },

  // Add your API methods here
  // Example:
  // async getData() {
  //   return apiRequest<DataResponse>('/data');
  // },
};
