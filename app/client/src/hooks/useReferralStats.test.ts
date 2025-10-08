import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { renderHook, waitFor, act } from '@testing-library/react';
import { useReferralStats } from './useReferralStats';
import { api } from '../lib/api/client';

// Mock the API client
vi.mock('../lib/api/client', () => ({
  api: {
    payments: {
      getReferralStats: vi.fn(),
    },
  },
}));

describe('useReferralStats', () => {
  const mockStats = {
    referral_code: 'FRIEND123',
    total_referrals: 5,
    pending_referrals: 2,
    total_credits: 150,
  };

  beforeEach(() => {
    vi.clearAllMocks();
  });

  afterEach(() => {
    vi.clearAllMocks();
  });

  describe('Initial State and Mount Behavior', () => {
    it('fetches referral statistics on mount', async () => {
      vi.mocked(api.payments.getReferralStats).mockResolvedValue(mockStats);

      const { result } = renderHook(() => useReferralStats());

      // Initial state should have loading true
      expect(result.current.loading).toBe(true);
      expect(result.current.stats).toBeNull();
      expect(result.current.error).toBeNull();

      // Wait for API call to complete
      await waitFor(() => {
        expect(result.current.loading).toBe(false);
      });

      expect(api.payments.getReferralStats).toHaveBeenCalledTimes(1);
      expect(result.current.stats).toEqual(mockStats);
      expect(result.current.error).toBeNull();
    });

    it('initializes with null stats', () => {
      vi.mocked(api.payments.getReferralStats).mockImplementation(
        () => new Promise(() => {}) // Never resolves
      );

      const { result } = renderHook(() => useReferralStats());

      expect(result.current.stats).toBeNull();
      expect(result.current.loading).toBe(true);
      expect(result.current.error).toBeNull();
    });
  });

  describe('Loading State Management', () => {
    it('sets loading to true while fetching', async () => {
      vi.mocked(api.payments.getReferralStats).mockImplementation(
        () =>
          new Promise((resolve) =>
            setTimeout(() => resolve(mockStats), 100)
          )
      );

      const { result } = renderHook(() => useReferralStats());

      expect(result.current.loading).toBe(true);

      await waitFor(() => {
        expect(result.current.loading).toBe(false);
      });
    });

    it('sets loading to false after successful fetch', async () => {
      vi.mocked(api.payments.getReferralStats).mockResolvedValue(mockStats);

      const { result } = renderHook(() => useReferralStats());

      await waitFor(() => {
        expect(result.current.loading).toBe(false);
      });

      expect(result.current.stats).toEqual(mockStats);
    });

    it('sets loading to false after failed fetch', async () => {
      const error = new Error('Network error');
      vi.mocked(api.payments.getReferralStats).mockRejectedValue(error);

      const { result } = renderHook(() => useReferralStats());

      await waitFor(() => {
        expect(result.current.loading).toBe(false);
      });

      expect(result.current.error).toBe('Network error');
    });
  });

  describe('Error Handling', () => {
    it('handles Error instance from API', async () => {
      const error = new Error('Unauthorized');
      vi.mocked(api.payments.getReferralStats).mockRejectedValue(error);

      const { result } = renderHook(() => useReferralStats());

      await waitFor(() => {
        expect(result.current.loading).toBe(false);
      });

      expect(result.current.error).toBe('Unauthorized');
      expect(result.current.stats).toBeNull();
    });

    it('handles non-Error exceptions with generic message', async () => {
      vi.mocked(api.payments.getReferralStats).mockRejectedValue('String error');

      const { result } = renderHook(() => useReferralStats());

      await waitFor(() => {
        expect(result.current.loading).toBe(false);
      });

      expect(result.current.error).toBe('Failed to fetch referral stats');
      expect(result.current.stats).toBeNull();
    });

    it('clears error when refetch succeeds', async () => {
      // First call fails
      vi.mocked(api.payments.getReferralStats).mockRejectedValueOnce(
        new Error('First error')
      );

      const { result } = renderHook(() => useReferralStats());

      await waitFor(() => {
        expect(result.current.error).toBe('First error');
      });

      // Second call succeeds
      vi.mocked(api.payments.getReferralStats).mockResolvedValueOnce(mockStats);

      await act(async () => {
        await result.current.refetch();
      });

      await waitFor(() => {
        expect(result.current.error).toBeNull();
      });

      expect(result.current.stats).toEqual(mockStats);
    });

    it('handles network timeout errors', async () => {
      const timeoutError = new Error('Request timeout after 30s');
      vi.mocked(api.payments.getReferralStats).mockRejectedValue(timeoutError);

      const { result } = renderHook(() => useReferralStats());

      await waitFor(() => {
        expect(result.current.error).toBe('Request timeout after 30s');
      });
    });

    it('handles authentication errors gracefully', async () => {
      const authError = new Error('Unauthorized');
      vi.mocked(api.payments.getReferralStats).mockRejectedValue(authError);

      const { result } = renderHook(() => useReferralStats());

      await waitFor(() => {
        expect(result.current.error).toBe('Unauthorized');
      });

      expect(result.current.stats).toBeNull();
      expect(result.current.loading).toBe(false);
    });
  });

  describe('Refetch Function', () => {
    it('refetches stats and updates state', async () => {
      vi.mocked(api.payments.getReferralStats).mockResolvedValue(mockStats);

      const { result } = renderHook(() => useReferralStats());

      await waitFor(() => {
        expect(result.current.loading).toBe(false);
      });

      expect(api.payments.getReferralStats).toHaveBeenCalledTimes(1);

      // Update mock to return different data
      const updatedStats = {
        referral_code: 'FRIEND123',
        total_referrals: 10,
        pending_referrals: 3,
        total_credits: 300,
      };

      vi.mocked(api.payments.getReferralStats).mockResolvedValue(updatedStats);

      await act(async () => {
        await result.current.refetch();
      });

      await waitFor(() => {
        expect(result.current.stats).toEqual(updatedStats);
      });

      expect(api.payments.getReferralStats).toHaveBeenCalledTimes(2);
    });

    it('sets loading to true during refetch', async () => {
      vi.mocked(api.payments.getReferralStats).mockResolvedValue(mockStats);

      const { result } = renderHook(() => useReferralStats());

      await waitFor(() => {
        expect(result.current.loading).toBe(false);
      });

      // Start refetch with delayed response
      vi.mocked(api.payments.getReferralStats).mockImplementation(
        () =>
          new Promise((resolve) =>
            setTimeout(() => resolve(mockStats), 100)
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
      vi.mocked(api.payments.getReferralStats).mockRejectedValue(
        new Error('Network error')
      );

      const { result } = renderHook(() => useReferralStats());

      await waitFor(() => {
        expect(result.current.error).toBe('Network error');
      });

      // Refetch with success
      vi.mocked(api.payments.getReferralStats).mockResolvedValue(mockStats);

      await act(async () => {
        await result.current.refetch();
      });

      await waitFor(() => {
        expect(result.current.error).toBeNull();
      });
    });

    it('handles refetch failure', async () => {
      vi.mocked(api.payments.getReferralStats).mockResolvedValue(mockStats);

      const { result } = renderHook(() => useReferralStats());

      await waitFor(() => {
        expect(result.current.loading).toBe(false);
      });

      // Refetch fails
      vi.mocked(api.payments.getReferralStats).mockRejectedValue(
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
    it('handles user without any referrals', async () => {
      const emptyStats = {
        referral_code: 'NEWUSER123',
        total_referrals: 0,
        pending_referrals: 0,
        total_credits: 0,
      };

      vi.mocked(api.payments.getReferralStats).mockResolvedValue(emptyStats);

      const { result } = renderHook(() => useReferralStats());

      await waitFor(() => {
        expect(result.current.loading).toBe(false);
      });

      expect(result.current.stats).toEqual(emptyStats);
      expect(result.current.error).toBeNull();
    });

    it('handles pending vs confirmed referral states', async () => {
      const pendingStats = {
        referral_code: 'FRIEND456',
        total_referrals: 5,
        pending_referrals: 5, // All pending
        total_credits: 0,
      };

      vi.mocked(api.payments.getReferralStats).mockResolvedValue(pendingStats);

      const { result } = renderHook(() => useReferralStats());

      await waitFor(() => {
        expect(result.current.loading).toBe(false);
      });

      expect(result.current.stats?.total_referrals).toBe(5);
      expect(result.current.stats?.pending_referrals).toBe(5);
      expect(result.current.stats?.total_credits).toBe(0);
    });

    it('handles confirmed referrals with credits', async () => {
      const confirmedStats = {
        referral_code: 'FRIEND789',
        total_referrals: 10,
        pending_referrals: 2,
        total_credits: 240, // 8 confirmed * 30 credits
      };

      vi.mocked(api.payments.getReferralStats).mockResolvedValue(confirmedStats);

      const { result } = renderHook(() => useReferralStats());

      await waitFor(() => {
        expect(result.current.loading).toBe(false);
      });

      expect(result.current.stats?.total_referrals).toBe(10);
      expect(result.current.stats?.pending_referrals).toBe(2);
      expect(result.current.stats?.total_credits).toBe(240);
    });

    it('handles concurrent refetch calls', async () => {
      vi.mocked(api.payments.getReferralStats).mockResolvedValue(mockStats);

      const { result } = renderHook(() => useReferralStats());

      await waitFor(() => {
        expect(result.current.loading).toBe(false);
      });

      // Mock delayed responses
      let resolveFirst: any;
      const firstPromise = new Promise<any>((resolve) => {
        resolveFirst = resolve;
      });

      const updatedStats = {
        referral_code: 'FRIEND123',
        total_referrals: 15,
        pending_referrals: 5,
        total_credits: 300,
      };

      vi.mocked(api.payments.getReferralStats)
        .mockReturnValueOnce(firstPromise)
        .mockResolvedValueOnce(updatedStats);

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
        expect(result.current.stats).toEqual(updatedStats);
      });

      // Resolve first (should not affect state)
      resolveFirst(mockStats);
    });

    it('handles malformed API responses', async () => {
      vi.mocked(api.payments.getReferralStats).mockResolvedValue(null as any);

      const { result } = renderHook(() => useReferralStats());

      await waitFor(() => {
        expect(result.current.loading).toBe(false);
      });

      // Should handle null response
      expect(result.current.stats).toEqual(null);
    });

    it('handles missing referral code in response', async () => {
      const incompleteStats = {
        referral_code: '',
        total_referrals: 0,
        pending_referrals: 0,
        total_credits: 0,
      };

      vi.mocked(api.payments.getReferralStats).mockResolvedValue(incompleteStats);

      const { result } = renderHook(() => useReferralStats());

      await waitFor(() => {
        expect(result.current.loading).toBe(false);
      });

      expect(result.current.stats).toEqual(incompleteStats);
    });

    it('handles large credit values', async () => {
      const highValueStats = {
        referral_code: 'INFLUENCER',
        total_referrals: 1000,
        pending_referrals: 50,
        total_credits: 28500, // 950 confirmed * 30 credits
      };

      vi.mocked(api.payments.getReferralStats).mockResolvedValue(highValueStats);

      const { result } = renderHook(() => useReferralStats());

      await waitFor(() => {
        expect(result.current.loading).toBe(false);
      });

      expect(result.current.stats?.total_credits).toBe(28500);
    });
  });

  describe('State Consistency', () => {
    it('maintains consistent state across successful fetches', async () => {
      vi.mocked(api.payments.getReferralStats).mockResolvedValue(mockStats);

      const { result } = renderHook(() => useReferralStats());

      // Initial state
      expect(result.current.loading).toBe(true);
      expect(result.current.error).toBeNull();
      expect(result.current.stats).toBeNull();

      // After successful fetch
      await waitFor(() => {
        expect(result.current.loading).toBe(false);
      });

      expect(result.current.error).toBeNull();
      expect(result.current.stats).toEqual(mockStats);
    });

    it('resets error state on new fetch attempt', async () => {
      // First attempt fails
      vi.mocked(api.payments.getReferralStats).mockRejectedValueOnce(
        new Error('First error')
      );

      const { result } = renderHook(() => useReferralStats());

      await waitFor(() => {
        expect(result.current.error).toBe('First error');
      });

      // Second attempt starts (should clear error)
      vi.mocked(api.payments.getReferralStats).mockResolvedValue(mockStats);

      await act(async () => {
        await result.current.refetch();
      });

      await waitFor(() => {
        expect(result.current.error).toBeNull();
      });

      expect(result.current.loading).toBe(false);
      expect(result.current.stats).toEqual(mockStats);
    });

    it('preserves previous stats during refetch', async () => {
      vi.mocked(api.payments.getReferralStats).mockResolvedValue(mockStats);

      const { result } = renderHook(() => useReferralStats());

      await waitFor(() => {
        expect(result.current.stats).toEqual(mockStats);
      });

      // Start refetch
      vi.mocked(api.payments.getReferralStats).mockImplementation(
        () => new Promise(() => {}) // Never resolves
      );

      act(() => {
        result.current.refetch();
      });

      // Stats should still be available during loading
      expect(result.current.loading).toBe(true);
      expect(result.current.stats).toEqual(mockStats);
    });
  });

  describe('Refetch Function Availability', () => {
    it('provides refetch function in returned object', () => {
      vi.mocked(api.payments.getReferralStats).mockImplementation(
        () => new Promise(() => {})
      );

      const { result } = renderHook(() => useReferralStats());

      expect(typeof result.current.refetch).toBe('function');
    });

    it('refetch function can be called multiple times', async () => {
      vi.mocked(api.payments.getReferralStats).mockResolvedValue(mockStats);

      const { result } = renderHook(() => useReferralStats());

      await waitFor(() => {
        expect(result.current.loading).toBe(false);
      });

      // Call refetch multiple times
      await act(async () => {
        await result.current.refetch();
      });

      await act(async () => {
        await result.current.refetch();
      });

      expect(api.payments.getReferralStats).toHaveBeenCalledTimes(3); // Initial + 2 refetches
    });
  });
});
