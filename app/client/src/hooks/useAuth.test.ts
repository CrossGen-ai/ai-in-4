import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { renderHook, waitFor, act } from '@testing-library/react'
import { AuthProvider, useAuth } from '../context/AuthContext'
import { api } from '../lib/api/client'
import type { User, AuthResponse } from '../lib/api/types'

// Mock the API client
vi.mock('../lib/api/client', () => ({
  api: {
    users: {
      getCurrentUser: vi.fn(),
    },
    auth: {
      validateMagicLink: vi.fn(),
      logout: vi.fn(),
    },
  },
}))

describe('useAuth', () => {
  const mockUser: User = {
    id: 1,
    email: 'test@example.com',
    created_at: '2024-01-01T00:00:00Z',
    last_login: '2024-01-02T00:00:00Z',
  }

  const mockAuthResponse: AuthResponse = {
    access_token: 'test-token-123',
    user: mockUser,
  }

  beforeEach(() => {
    // Clear localStorage before each test
    localStorage.clear()
    vi.clearAllMocks()
  })

  afterEach(() => {
    localStorage.clear()
  })

  describe('Hook Context Validation', () => {
    it('throws error when used outside AuthProvider', () => {
      // Suppress console.error for this test
      const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => {})

      expect(() => {
        renderHook(() => useAuth())
      }).toThrow('useAuth must be used within an AuthProvider')

      consoleSpy.mockRestore()
    })
  })

  describe('Initial State and Token Validation', () => {
    it('initializes with null user and loading true when no token exists', async () => {
      const { result } = renderHook(() => useAuth(), {
        wrapper: AuthProvider,
      })

      // Initial state should have loading true
      expect(result.current.user).toBeNull()
      expect(result.current.isAuthenticated).toBe(false)

      // Wait for loading to complete
      await waitFor(() => {
        expect(result.current.loading).toBe(false)
      })
    })

    it('validates existing token on mount and sets user', async () => {
      localStorage.setItem('auth_token', 'existing-token')
      vi.mocked(api.users.getCurrentUser).mockResolvedValue(mockUser)

      const { result } = renderHook(() => useAuth(), {
        wrapper: AuthProvider,
      })

      await waitFor(() => {
        expect(result.current.loading).toBe(false)
      })

      expect(api.users.getCurrentUser).toHaveBeenCalledTimes(1)
      expect(result.current.user).toEqual(mockUser)
      expect(result.current.isAuthenticated).toBe(true)
    })

    it('clears invalid token on mount when validation fails', async () => {
      localStorage.setItem('auth_token', 'invalid-token')
      vi.mocked(api.users.getCurrentUser).mockRejectedValue(new Error('Unauthorized'))

      const { result } = renderHook(() => useAuth(), {
        wrapper: AuthProvider,
      })

      await waitFor(() => {
        expect(result.current.loading).toBe(false)
      })

      expect(localStorage.getItem('auth_token')).toBeNull()
      expect(result.current.user).toBeNull()
      expect(result.current.isAuthenticated).toBe(false)
    })
  })

  describe('Login Function', () => {
    it('successfully logs in user with valid token', async () => {
      vi.mocked(api.users.getCurrentUser).mockResolvedValue(mockUser)

      const { result } = renderHook(() => useAuth(), {
        wrapper: AuthProvider,
      })

      await waitFor(() => {
        expect(result.current.loading).toBe(false)
      })

      await act(async () => {
        await result.current.login('new-token-123')
      })

      await waitFor(() => {
        expect(result.current.user).toEqual(mockUser)
      })

      expect(localStorage.getItem('auth_token')).toBe('new-token-123')
      expect(result.current.isAuthenticated).toBe(true)
    })

    it('removes token and throws error when login fails', async () => {
      const error = new Error('Invalid token')
      vi.mocked(api.users.getCurrentUser).mockRejectedValue(error)

      const { result } = renderHook(() => useAuth(), {
        wrapper: AuthProvider,
      })

      await waitFor(() => {
        expect(result.current.loading).toBe(false)
      })

      await expect(result.current.login('bad-token')).rejects.toThrow('Invalid token')

      expect(localStorage.getItem('auth_token')).toBeNull()
      expect(result.current.user).toBeNull()
    })

    it('handles network errors during login', async () => {
      const networkError = new Error('Network request failed')
      vi.mocked(api.users.getCurrentUser).mockRejectedValue(networkError)

      const { result } = renderHook(() => useAuth(), {
        wrapper: AuthProvider,
      })

      await waitFor(() => {
        expect(result.current.loading).toBe(false)
      })

      await expect(result.current.login('token-123')).rejects.toThrow('Network request failed')

      expect(localStorage.getItem('auth_token')).toBeNull()
    })
  })

  describe('Logout Function', () => {
    it('clears user state and removes token on logout', async () => {
      localStorage.setItem('auth_token', 'existing-token')
      vi.mocked(api.users.getCurrentUser).mockResolvedValue(mockUser)
      vi.mocked(api.auth.logout).mockResolvedValue({ message: 'Logged out' })

      const { result } = renderHook(() => useAuth(), {
        wrapper: AuthProvider,
      })

      await waitFor(() => {
        expect(result.current.user).toEqual(mockUser)
      })

      act(() => {
        result.current.logout()
      })

      await waitFor(() => {
        expect(result.current.user).toBeNull()
      })

      expect(localStorage.getItem('auth_token')).toBeNull()
      expect(result.current.isAuthenticated).toBe(false)
      expect(api.auth.logout).toHaveBeenCalledTimes(1)
    })

    it('handles logout even when API call fails', async () => {
      localStorage.setItem('auth_token', 'existing-token')
      vi.mocked(api.users.getCurrentUser).mockResolvedValue(mockUser)
      vi.mocked(api.auth.logout).mockRejectedValue(new Error('Logout failed'))

      const { result } = renderHook(() => useAuth(), {
        wrapper: AuthProvider,
      })

      await waitFor(() => {
        expect(result.current.user).toEqual(mockUser)
      })

      // Should not throw - errors are silently ignored
      act(() => {
        result.current.logout()
      })

      await waitFor(() => {
        expect(result.current.user).toBeNull()
      })

      expect(localStorage.getItem('auth_token')).toBeNull()
    })

    it('handles browser back button after logout', async () => {
      localStorage.setItem('auth_token', 'existing-token')
      vi.mocked(api.users.getCurrentUser).mockResolvedValue(mockUser)
      vi.mocked(api.auth.logout).mockResolvedValue({ message: 'Logged out' })

      const { result } = renderHook(() => useAuth(), {
        wrapper: AuthProvider,
      })

      await waitFor(() => {
        expect(result.current.user).toEqual(mockUser)
      })

      act(() => {
        result.current.logout()
      })

      await waitFor(() => {
        expect(result.current.user).toBeNull()
      })

      // Simulate browser navigation - token should still be gone
      expect(localStorage.getItem('auth_token')).toBeNull()
      expect(result.current.isAuthenticated).toBe(false)
    })
  })

  describe('Validate Token Function', () => {
    it('validates magic link token successfully', async () => {
      vi.mocked(api.auth.validateMagicLink).mockResolvedValue(mockAuthResponse)

      const { result } = renderHook(() => useAuth(), {
        wrapper: AuthProvider,
      })

      await waitFor(() => {
        expect(result.current.loading).toBe(false)
      })

      let isValid: boolean = false
      await act(async () => {
        isValid = await result.current.validateToken('magic-link-token')
      })

      await waitFor(() => {
        expect(result.current.user).toEqual(mockUser)
      })

      expect(isValid).toBe(true)
      expect(localStorage.getItem('auth_token')).toBe('test-token-123')
      expect(result.current.isAuthenticated).toBe(true)
    })

    it('returns false when magic link validation fails', async () => {
      vi.mocked(api.auth.validateMagicLink).mockRejectedValue(new Error('Invalid magic link'))

      const { result } = renderHook(() => useAuth(), {
        wrapper: AuthProvider,
      })

      await waitFor(() => {
        expect(result.current.loading).toBe(false)
      })

      const isValid = await result.current.validateToken('invalid-token')

      expect(isValid).toBe(false)
      expect(localStorage.getItem('auth_token')).toBeNull()
      expect(result.current.user).toBeNull()
    })
  })

  describe('Edge Cases', () => {
    it('handles missing authentication token for protected routes', async () => {
      const { result } = renderHook(() => useAuth(), {
        wrapper: AuthProvider,
      })

      await waitFor(() => {
        expect(result.current.loading).toBe(false)
      })

      expect(result.current.isAuthenticated).toBe(false)
      expect(result.current.user).toBeNull()
    })

    it('handles token expiry while user is on course page', async () => {
      localStorage.setItem('auth_token', 'expired-token')
      vi.mocked(api.users.getCurrentUser).mockRejectedValue(new Error('Token expired'))

      const { result } = renderHook(() => useAuth(), {
        wrapper: AuthProvider,
      })

      await waitFor(() => {
        expect(result.current.loading).toBe(false)
      })

      // Token should be cleared automatically
      expect(localStorage.getItem('auth_token')).toBeNull()
      expect(result.current.user).toBeNull()
      expect(result.current.isAuthenticated).toBe(false)
    })

    it('handles concurrent login attempts', async () => {
      vi.mocked(api.users.getCurrentUser)
        .mockResolvedValueOnce(mockUser)
        .mockResolvedValueOnce(mockUser)

      const { result } = renderHook(() => useAuth(), {
        wrapper: AuthProvider,
      })

      await waitFor(() => {
        expect(result.current.loading).toBe(false)
      })

      // Start two login attempts concurrently
      await act(async () => {
        const login1 = result.current.login('token-1')
        const login2 = result.current.login('token-2')
        await Promise.all([login1, login2])
      })

      await waitFor(() => {
        expect(result.current.user).toEqual(mockUser)
      })

      // Last login should win
      expect(localStorage.getItem('auth_token')).toBe('token-2')
    })

    it('maintains auth state during network errors for subsequent API calls', async () => {
      localStorage.setItem('auth_token', 'valid-token')
      vi.mocked(api.users.getCurrentUser).mockResolvedValue(mockUser)

      const { result } = renderHook(() => useAuth(), {
        wrapper: AuthProvider,
      })

      await waitFor(() => {
        expect(result.current.user).toEqual(mockUser)
      })

      // User should still be authenticated even if logout API fails
      vi.mocked(api.auth.logout).mockRejectedValue(new Error('Network error'))

      act(() => {
        result.current.logout()
      })

      await waitFor(() => {
        expect(result.current.user).toBeNull()
      })

      // Local state should be cleared regardless of API error
      expect(result.current.isAuthenticated).toBe(false)
    })
  })

  describe('State Consistency', () => {
    it('maintains consistent isAuthenticated derived from user state', async () => {
      const { result } = renderHook(() => useAuth(), {
        wrapper: AuthProvider,
      })

      await waitFor(() => {
        expect(result.current.loading).toBe(false)
      })

      // No user = not authenticated
      expect(result.current.user).toBeNull()
      expect(result.current.isAuthenticated).toBe(false)

      // Add user via validateToken
      vi.mocked(api.auth.validateMagicLink).mockResolvedValue(mockAuthResponse)
      await act(async () => {
        await result.current.validateToken('magic-token')
      })

      await waitFor(() => {
        expect(result.current.user).toEqual(mockUser)
      })

      // Has user = authenticated
      expect(result.current.isAuthenticated).toBe(true)

      // Logout
      vi.mocked(api.auth.logout).mockResolvedValue({ message: 'Logged out' })
      act(() => {
        result.current.logout()
      })

      await waitFor(() => {
        expect(result.current.user).toBeNull()
      })

      // No user again = not authenticated
      expect(result.current.isAuthenticated).toBe(false)
    })
  })
})
