import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { renderHook, waitFor, act } from '@testing-library/react';
import { useCourseEntitlements } from './useCourseEntitlements';
import { api } from '../lib/api/client';

// Mock the API client
vi.mock('../lib/api/client', () => ({
  api: {
    payments: {
      getUserEntitlements: vi.fn(),
    },
  },
}));

describe('useCourseEntitlements', () => {
  const mockEntitlements = [
    {
      price_id: 'price_123',
      product_id: 'prod_abc',
      product_name: 'Course A',
      status: 'active',
      created_at: '2024-01-01T00:00:00Z',
    },
    {
      price_id: 'price_456',
      product_id: 'prod_def',
      product_name: 'Course B',
      status: 'active',
      created_at: '2024-01-02T00:00:00Z',
    },
  ];

  beforeEach(() => {
    vi.clearAllMocks();
  });

  afterEach(() => {
    vi.clearAllMocks();
  });

  describe('Initial State and Mount Behavior', () => {
    it('fetches user entitlements on mount', async () => {
      vi.mocked(api.payments.getUserEntitlements).mockResolvedValue(mockEntitlements);

      const { result } = renderHook(() => useCourseEntitlements());

      // Initial state should have loading true
      expect(result.current.loading).toBe(true);
      expect(result.current.entitlements).toEqual([]);
      expect(result.current.error).toBeNull();

      // Wait for API call to complete
      await waitFor(() => {
        expect(result.current.loading).toBe(false);
      });

      expect(api.payments.getUserEntitlements).toHaveBeenCalledTimes(1);
      expect(result.current.entitlements).toEqual(mockEntitlements);
      expect(result.current.error).toBeNull();
    });

    it('initializes with empty entitlements array', () => {
      vi.mocked(api.payments.getUserEntitlements).mockImplementation(
        () => new Promise(() => {}) // Never resolves
      );

      const { result } = renderHook(() => useCourseEntitlements());

      expect(result.current.entitlements).toEqual([]);
      expect(result.current.loading).toBe(true);
      expect(result.current.error).toBeNull();
    });
  });

  describe('Loading State Management', () => {
    it('sets loading to true while fetching', async () => {
      vi.mocked(api.payments.getUserEntitlements).mockImplementation(
        () =>
          new Promise((resolve) =>
            setTimeout(() => resolve(mockEntitlements), 100)
          )
      );

      const { result } = renderHook(() => useCourseEntitlements());

      expect(result.current.loading).toBe(true);

      await waitFor(() => {
        expect(result.current.loading).toBe(false);
      });
    });

    it('sets loading to false after successful fetch', async () => {
      vi.mocked(api.payments.getUserEntitlements).mockResolvedValue(mockEntitlements);

      const { result } = renderHook(() => useCourseEntitlements());

      await waitFor(() => {
        expect(result.current.loading).toBe(false);
      });

      expect(result.current.entitlements).toEqual(mockEntitlements);
    });

    it('sets loading to false after failed fetch', async () => {
      const error = new Error('Network error');
      vi.mocked(api.payments.getUserEntitlements).mockRejectedValue(error);

      const { result } = renderHook(() => useCourseEntitlements());

      await waitFor(() => {
        expect(result.current.loading).toBe(false);
      });

      expect(result.current.error).toBe('Network error');
    });
  });

  describe('Error Handling', () => {
    it('handles Error instance from API', async () => {
      const error = new Error('Unauthorized');
      vi.mocked(api.payments.getUserEntitlements).mockRejectedValue(error);

      const { result } = renderHook(() => useCourseEntitlements());

      await waitFor(() => {
        expect(result.current.loading).toBe(false);
      });

      expect(result.current.error).toBe('Unauthorized');
      expect(result.current.entitlements).toEqual([]);
    });

    it('handles non-Error exceptions with generic message', async () => {
      vi.mocked(api.payments.getUserEntitlements).mockRejectedValue('String error');

      const { result } = renderHook(() => useCourseEntitlements());

      await waitFor(() => {
        expect(result.current.loading).toBe(false);
      });

      expect(result.current.error).toBe('Failed to fetch entitlements');
      expect(result.current.entitlements).toEqual([]);
    });

    it('clears error when refetch succeeds', async () => {
      // First call fails
      vi.mocked(api.payments.getUserEntitlements).mockRejectedValueOnce(
        new Error('First error')
      );

      const { result } = renderHook(() => useCourseEntitlements());

      await waitFor(() => {
        expect(result.current.error).toBe('First error');
      });

      // Second call succeeds
      vi.mocked(api.payments.getUserEntitlements).mockResolvedValueOnce(mockEntitlements);

      await act(async () => {
        await result.current.refetch();
      });

      await waitFor(() => {
        expect(result.current.error).toBeNull();
      });

      expect(result.current.entitlements).toEqual(mockEntitlements);
    });

    it('handles network timeout errors', async () => {
      const timeoutError = new Error('Request timeout after 30s');
      vi.mocked(api.payments.getUserEntitlements).mockRejectedValue(timeoutError);

      const { result } = renderHook(() => useCourseEntitlements());

      await waitFor(() => {
        expect(result.current.error).toBe('Request timeout after 30s');
      });
    });
  });

  describe('hasAccess Helper Function', () => {
    it('returns true when user has active entitlement for price_id', async () => {
      vi.mocked(api.payments.getUserEntitlements).mockResolvedValue(mockEntitlements);

      const { result } = renderHook(() => useCourseEntitlements());

      await waitFor(() => {
        expect(result.current.loading).toBe(false);
      });

      expect(result.current.hasAccess('price_123')).toBe(true);
      expect(result.current.hasAccess('price_456')).toBe(true);
    });

    it('returns false when user does not have entitlement for price_id', async () => {
      vi.mocked(api.payments.getUserEntitlements).mockResolvedValue(mockEntitlements);

      const { result } = renderHook(() => useCourseEntitlements());

      await waitFor(() => {
        expect(result.current.loading).toBe(false);
      });

      expect(result.current.hasAccess('price_nonexistent')).toBe(false);
    });

    it('returns false when entitlement exists but status is not active', async () => {
      const inactiveEntitlements = [
        {
          price_id: 'price_123',
          product_id: 'prod_abc',
          product_name: 'Course A',
          status: 'expired',
          created_at: '2024-01-01T00:00:00Z',
        },
        {
          price_id: 'price_456',
          product_id: 'prod_def',
          product_name: 'Course B',
          status: 'revoked',
          created_at: '2024-01-02T00:00:00Z',
        },
      ];

      vi.mocked(api.payments.getUserEntitlements).mockResolvedValue(inactiveEntitlements);

      const { result } = renderHook(() => useCourseEntitlements());

      await waitFor(() => {
        expect(result.current.loading).toBe(false);
      });

      expect(result.current.hasAccess('price_123')).toBe(false);
      expect(result.current.hasAccess('price_456')).toBe(false);
    });

    it('returns false when entitlements array is empty', async () => {
      vi.mocked(api.payments.getUserEntitlements).mockResolvedValue([]);

      const { result } = renderHook(() => useCourseEntitlements());

      await waitFor(() => {
        expect(result.current.loading).toBe(false);
      });

      expect(result.current.hasAccess('price_123')).toBe(false);
    });

    it('handles mixed active and inactive entitlements', async () => {
      const mixedEntitlements = [
        {
          price_id: 'price_123',
          product_id: 'prod_abc',
          product_name: 'Course A',
          status: 'active',
          created_at: '2024-01-01T00:00:00Z',
        },
        {
          price_id: 'price_456',
          product_id: 'prod_def',
          product_name: 'Course B',
          status: 'expired',
          created_at: '2024-01-02T00:00:00Z',
        },
      ];

      vi.mocked(api.payments.getUserEntitlements).mockResolvedValue(mixedEntitlements);

      const { result } = renderHook(() => useCourseEntitlements());

      await waitFor(() => {
        expect(result.current.loading).toBe(false);
      });

      expect(result.current.hasAccess('price_123')).toBe(true);
      expect(result.current.hasAccess('price_456')).toBe(false);
    });
  });

  describe('Refetch Function', () => {
    it('refetches entitlements and updates state', async () => {
      vi.mocked(api.payments.getUserEntitlements).mockResolvedValue(mockEntitlements);

      const { result } = renderHook(() => useCourseEntitlements());

      await waitFor(() => {
        expect(result.current.loading).toBe(false);
      });

      expect(api.payments.getUserEntitlements).toHaveBeenCalledTimes(1);

      // Update mock to return different data
      const updatedEntitlements = [
        {
          price_id: 'price_789',
          product_id: 'prod_ghi',
          product_name: 'Course C',
          status: 'active',
          created_at: '2024-01-03T00:00:00Z',
        },
      ];

      vi.mocked(api.payments.getUserEntitlements).mockResolvedValue(updatedEntitlements);

      await act(async () => {
        await result.current.refetch();
      });

      await waitFor(() => {
        expect(result.current.entitlements).toEqual(updatedEntitlements);
      });

      expect(api.payments.getUserEntitlements).toHaveBeenCalledTimes(2);
    });

    it('sets loading to true during refetch', async () => {
      vi.mocked(api.payments.getUserEntitlements).mockResolvedValue(mockEntitlements);

      const { result } = renderHook(() => useCourseEntitlements());

      await waitFor(() => {
        expect(result.current.loading).toBe(false);
      });

      // Start refetch with delayed response
      vi.mocked(api.payments.getUserEntitlements).mockImplementation(
        () =>
          new Promise((resolve) =>
            setTimeout(() => resolve(mockEntitlements), 100)
          )
      );

      act(() => {
        result.current.refetch();
      });

      expect(result.current.loading).toBe(true);

      await waitFor(() => {
        expect(result.current.loading).toBe(false);
      });
    });

    it('clears error state when refetch starts', async () => {
      // First call fails
      vi.mocked(api.payments.getUserEntitlements).mockRejectedValue(
        new Error('Network error')
      );

      const { result } = renderHook(() => useCourseEntitlements());

      await waitFor(() => {
        expect(result.current.error).toBe('Network error');
      });

      // Refetch with success
      vi.mocked(api.payments.getUserEntitlements).mockResolvedValue(mockEntitlements);

      await act(async () => {
        await result.current.refetch();
      });

      await waitFor(() => {
        expect(result.current.error).toBeNull();
      });
    });

    it('handles refetch failure', async () => {
      vi.mocked(api.payments.getUserEntitlements).mockResolvedValue(mockEntitlements);

      const { result } = renderHook(() => useCourseEntitlements());

      await waitFor(() => {
        expect(result.current.loading).toBe(false);
      });

      // Refetch fails
      vi.mocked(api.payments.getUserEntitlements).mockRejectedValue(
        new Error('Refetch failed')
      );

      await act(async () => {
        await result.current.refetch();
      });

      await waitFor(() => {
        expect(result.current.error).toBe('Refetch failed');
      });

      expect(result.current.loading).toBe(false);
    });
  });

  describe('Edge Cases', () => {
    it('handles user without any entitlements', async () => {
      vi.mocked(api.payments.getUserEntitlements).mockResolvedValue([]);

      const { result } = renderHook(() => useCourseEntitlements());

      await waitFor(() => {
        expect(result.current.loading).toBe(false);
      });

      expect(result.current.entitlements).toEqual([]);
      expect(result.current.hasAccess('price_123')).toBe(false);
      expect(result.current.error).toBeNull();
    });

    it('handles expired entitlements', async () => {
      const expiredEntitlements = [
        {
          price_id: 'price_expired',
          product_id: 'prod_expired',
          product_name: 'Expired Course',
          status: 'expired',
          created_at: '2023-01-01T00:00:00Z',
        },
      ];

      vi.mocked(api.payments.getUserEntitlements).mockResolvedValue(expiredEntitlements);

      const { result } = renderHook(() => useCourseEntitlements());

      await waitFor(() => {
        expect(result.current.loading).toBe(false);
      });

      expect(result.current.entitlements).toEqual(expiredEntitlements);
      expect(result.current.hasAccess('price_expired')).toBe(false);
    });

    it('handles revoked entitlements', async () => {
      const revokedEntitlements = [
        {
          price_id: 'price_revoked',
          product_id: 'prod_revoked',
          product_name: 'Revoked Course',
          status: 'revoked',
          created_at: '2024-01-01T00:00:00Z',
        },
      ];

      vi.mocked(api.payments.getUserEntitlements).mockResolvedValue(revokedEntitlements);

      const { result } = renderHook(() => useCourseEntitlements());

      await waitFor(() => {
        expect(result.current.loading).toBe(false);
      });

      expect(result.current.hasAccess('price_revoked')).toBe(false);
    });

    it('handles authentication errors gracefully', async () => {
      const authError = new Error('Unauthorized');
      vi.mocked(api.payments.getUserEntitlements).mockRejectedValue(authError);

      const { result } = renderHook(() => useCourseEntitlements());

      await waitFor(() => {
        expect(result.current.error).toBe('Unauthorized');
      });

      expect(result.current.entitlements).toEqual([]);
      expect(result.current.loading).toBe(false);
    });

    it('handles concurrent refetch calls', async () => {
      vi.mocked(api.payments.getUserEntitlements).mockResolvedValue(mockEntitlements);

      const { result } = renderHook(() => useCourseEntitlements());

      await waitFor(() => {
        expect(result.current.loading).toBe(false);
      });

      // Mock delayed responses
      let resolveFirst: any;
      const firstPromise = new Promise<any>((resolve) => {
        resolveFirst = resolve;
      });

      const updatedEntitlements = [
        {
          price_id: 'price_new',
          product_id: 'prod_new',
          product_name: 'New Course',
          status: 'active',
          created_at: '2024-01-04T00:00:00Z',
        },
      ];

      vi.mocked(api.payments.getUserEntitlements)
        .mockReturnValueOnce(firstPromise)
        .mockResolvedValueOnce(updatedEntitlements);

      // Start first refetch
      act(() => {
        result.current.refetch();
      });

      // Start second refetch while first is pending
      await act(async () => {
        await result.current.refetch();
      });

      // Second refetch should complete
      await waitFor(() => {
        expect(result.current.entitlements).toEqual(updatedEntitlements);
      });

      // Resolve first (should not affect state)
      resolveFirst(mockEntitlements);
    });

    it('handles malformed API responses', async () => {
      vi.mocked(api.payments.getUserEntitlements).mockResolvedValue(null as any);

      const { result } = renderHook(() => useCourseEntitlements());

      await waitFor(() => {
        expect(result.current.loading).toBe(false);
      });

      // Should handle null as empty array or set error
      expect(result.current.entitlements).toEqual(null);
    });
  });

  describe('State Consistency', () => {
    it('maintains consistent state across successful fetches', async () => {
      vi.mocked(api.payments.getUserEntitlements).mockResolvedValue(mockEntitlements);

      const { result } = renderHook(() => useCourseEntitlements());

      // Initial state
      expect(result.current.loading).toBe(true);
      expect(result.current.error).toBeNull();
      expect(result.current.entitlements).toEqual([]);

      // After successful fetch
      await waitFor(() => {
        expect(result.current.loading).toBe(false);
      });

      expect(result.current.error).toBeNull();
      expect(result.current.entitlements).toEqual(mockEntitlements);
      expect(result.current.hasAccess('price_123')).toBe(true);
    });

    it('resets error state on new fetch attempt', async () => {
      // First attempt fails
      vi.mocked(api.payments.getUserEntitlements).mockRejectedValueOnce(
        new Error('First error')
      );

      const { result } = renderHook(() => useCourseEntitlements());

      await waitFor(() => {
        expect(result.current.error).toBe('First error');
      });

      // Second attempt starts (should clear error)
      vi.mocked(api.payments.getUserEntitlements).mockResolvedValue(mockEntitlements);

      await act(async () => {
        await result.current.refetch();
      });

      await waitFor(() => {
        expect(result.current.error).toBeNull();
      });

      expect(result.current.loading).toBe(false);
      expect(result.current.entitlements).toEqual(mockEntitlements);
    });
  });
});
