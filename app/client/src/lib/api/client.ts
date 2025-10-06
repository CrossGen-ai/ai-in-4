import type { User, UserCreate, UserExperience, MagicLinkRequest, AuthResponse, Course } from './types';

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

// Helper to get auth token
function getAuthToken(): string | null {
  return localStorage.getItem('auth_token');
}

// Helper to add auth header
function withAuth(headers: HeadersInit = {}): HeadersInit {
  const token = getAuthToken();
  return {
    ...headers,
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
  };
}

// Export API methods
export const api = {
  // Health check
  async healthCheck() {
    return apiRequest<{ status: string }>('/health');
  },

  // Authentication
  auth: {
    async register(data: UserCreate) {
      return apiRequest<AuthResponse>('/auth/register', {
        method: 'POST',
        body: JSON.stringify(data),
      });
    },

    async requestMagicLink(email: string) {
      return apiRequest<{ message: string }>('/auth/magic-link', {
        method: 'POST',
        body: JSON.stringify({ email }),
      });
    },

    async validateMagicLink(token: string) {
      return apiRequest<AuthResponse>('/auth/validate', {
        method: 'POST',
        body: JSON.stringify({ token }),
      });
    },

    async logout() {
      return apiRequest<{ message: string }>('/auth/logout', {
        method: 'POST',
        headers: withAuth(),
      });
    },

    async getDevUsers() {
      return apiRequest<User[]>('/auth/dev-users');
    },
  },

  // Users
  users: {
    async getCurrentUser() {
      return apiRequest<User>('/users/me', {
        headers: withAuth(),
      });
    },

    async getUserExperience() {
      return apiRequest<UserExperience>('/users/me/experience', {
        headers: withAuth(),
      });
    },
  },

  // Courses
  courses: {
    async listCourses() {
      return apiRequest<Course[]>('/courses/');
    },

    async getCourse(id: number) {
      return apiRequest<Course>(`/courses/${id}`);
    },
  },
};
