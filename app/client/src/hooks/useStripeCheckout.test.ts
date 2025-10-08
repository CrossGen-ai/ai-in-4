import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { renderHook, waitFor, act } from '@testing-library/react';
import { useStripeCheckout } from './useStripeCheckout';
import { api } from '../lib/api/client';

// Mock the API client
vi.mock('../lib/api/client', () => ({
  api: {
    payments: {
      createCheckoutSession: vi.fn(),
    },
  },
}));

// Mock window.location
const mockWindowLocation = () => {
  const originalLocation = window.location;
  delete (window as any).location;
  window.location = { ...originalLocation, href: '' } as Location;

  return () => {
    window.location = originalLocation;
  };
};

describe('useStripeCheckout', () => {
  let restoreLocation: () => void;

  beforeEach(() => {
    restoreLocation = mockWindowLocation();
    vi.clearAllMocks();
  });

  afterEach(() => {
    restoreLocation();
  });

  describe('Initial State', () => {
    it('initializes with correct default values', () => {
      const { result } = renderHook(() => useStripeCheckout());

      expect(result.current.loading).toBe(false);
      expect(result.current.error).toBeNull();
      expect(typeof result.current.initiateCheckout).toBe('function');
    });
  });

  describe('Loading State Management', () => {
    it('sets loading to true when checkout starts', async () => {
      vi.mocked(api.payments.createCheckoutSession).mockImplementation(
        () =>
          new Promise((resolve) =>
            setTimeout(
              () =>
                resolve({
                  checkout_url: 'https://checkout.stripe.com/session123',
                  session_id: 'sess_123',
                }),
              100
            )
          )
      );

      const { result } = renderHook(() => useStripeCheckout());

      act(() => {
        result.current.initiateCheckout('price_123');
      });

      // Loading should be true immediately after initiating
      expect(result.current.loading).toBe(true);
      expect(result.current.error).toBeNull();

      await waitFor(() => {
        expect(window.location.href).toBe('https://checkout.stripe.com/session123');
      });
    });

    it('keeps loading true after successful redirect', async () => {
      vi.mocked(api.payments.createCheckoutSession).mockResolvedValue({
        checkout_url: 'https://checkout.stripe.com/session123',
        session_id: 'sess_123',
      });

      const { result } = renderHook(() => useStripeCheckout());

      await act(async () => {
        await result.current.initiateCheckout('price_123');
      });

      // Loading should remain true since user is redirected
      expect(result.current.loading).toBe(true);
    });

    it('sets loading to false when checkout fails', async () => {
      const error = new Error('Payment processing failed');
      vi.mocked(api.payments.createCheckoutSession).mockRejectedValue(error);

      const { result } = renderHook(() => useStripeCheckout());

      await act(async () => {
        await result.current.initiateCheckout('price_123');
      });

      expect(result.current.loading).toBe(false);
      expect(result.current.error).toBe('Payment processing failed');
    });
  });

  describe('Error Handling', () => {
    it('handles Error instance from API', async () => {
      const error = new Error('Network timeout');
      vi.mocked(api.payments.createCheckoutSession).mockRejectedValue(error);

      const { result } = renderHook(() => useStripeCheckout());

      await act(async () => {
        await result.current.initiateCheckout('price_123');
      });

      expect(result.current.error).toBe('Network timeout');
      expect(result.current.loading).toBe(false);
    });

    it('handles non-Error exceptions with generic message', async () => {
      vi.mocked(api.payments.createCheckoutSession).mockRejectedValue('String error');

      const { result } = renderHook(() => useStripeCheckout());

      await act(async () => {
        await result.current.initiateCheckout('price_123');
      });

      expect(result.current.error).toBe('Failed to create checkout session');
      expect(result.current.loading).toBe(false);
    });

    it('clears previous error when starting new checkout', async () => {
      // First call fails
      vi.mocked(api.payments.createCheckoutSession).mockRejectedValueOnce(
        new Error('First error')
      );

      const { result } = renderHook(() => useStripeCheckout());

      await act(async () => {
        await result.current.initiateCheckout('price_123');
      });

      expect(result.current.error).toBe('First error');

      // Second call succeeds
      vi.mocked(api.payments.createCheckoutSession).mockResolvedValueOnce({
        checkout_url: 'https://checkout.stripe.com/session456',
        session_id: 'sess_456',
      });

      await act(async () => {
        await result.current.initiateCheckout('price_456');
      });

      expect(result.current.error).toBeNull();
    });

    it('handles API errors with missing error message', async () => {
      const errorWithoutMessage = { statusCode: 500 };
      vi.mocked(api.payments.createCheckoutSession).mockRejectedValue(errorWithoutMessage);

      const { result } = renderHook(() => useStripeCheckout());

      await act(async () => {
        await result.current.initiateCheckout('price_123');
      });

      expect(result.current.error).toBe('Failed to create checkout session');
    });
  });

  describe('Successful Checkout Flow', () => {
    it('redirects to Stripe checkout URL on success', async () => {
      const mockCheckoutUrl = 'https://checkout.stripe.com/c/pay/cs_test_123';
      vi.mocked(api.payments.createCheckoutSession).mockResolvedValue({
        checkout_url: mockCheckoutUrl,
        session_id: 'cs_test_123',
      });

      const { result } = renderHook(() => useStripeCheckout());

      await act(async () => {
        await result.current.initiateCheckout('price_123');
      });

      expect(window.location.href).toBe(mockCheckoutUrl);
      expect(api.payments.createCheckoutSession).toHaveBeenCalledWith('price_123', undefined);
    });

    it('does not redirect when checkout_url is missing', async () => {
      vi.mocked(api.payments.createCheckoutSession).mockResolvedValue({
        checkout_url: '',
        session_id: 'sess_123',
      });

      const { result } = renderHook(() => useStripeCheckout());

      await act(async () => {
        await result.current.initiateCheckout('price_123');
      });

      expect(window.location.href).toBe('');
    });

    it('does not redirect when checkout_url is null', async () => {
      vi.mocked(api.payments.createCheckoutSession).mockResolvedValue({
        checkout_url: null as any,
        session_id: 'sess_123',
      });

      const { result } = renderHook(() => useStripeCheckout());

      await act(async () => {
        await result.current.initiateCheckout('price_123');
      });

      expect(window.location.href).toBe('');
    });
  });

  describe('Referrer Code Handling', () => {
    it('passes referrer code to API when provided', async () => {
      vi.mocked(api.payments.createCheckoutSession).mockResolvedValue({
        checkout_url: 'https://checkout.stripe.com/session123',
        session_id: 'sess_123',
      });

      const { result } = renderHook(() => useStripeCheckout());

      await act(async () => {
        await result.current.initiateCheckout('price_123', 'FRIEND20');
      });

      expect(api.payments.createCheckoutSession).toHaveBeenCalledWith('price_123', 'FRIEND20');
    });

    it('does not pass referrer code when undefined', async () => {
      vi.mocked(api.payments.createCheckoutSession).mockResolvedValue({
        checkout_url: 'https://checkout.stripe.com/session123',
        session_id: 'sess_123',
      });

      const { result } = renderHook(() => useStripeCheckout());

      await act(async () => {
        await result.current.initiateCheckout('price_123');
      });

      expect(api.payments.createCheckoutSession).toHaveBeenCalledWith('price_123', undefined);
    });

    it('handles empty string referrer code', async () => {
      vi.mocked(api.payments.createCheckoutSession).mockResolvedValue({
        checkout_url: 'https://checkout.stripe.com/session123',
        session_id: 'sess_123',
      });

      const { result } = renderHook(() => useStripeCheckout());

      await act(async () => {
        await result.current.initiateCheckout('price_123', '');
      });

      expect(api.payments.createCheckoutSession).toHaveBeenCalledWith('price_123', '');
    });
  });

  describe('Edge Cases', () => {
    it('handles invalid referral code error from API', async () => {
      const error = new Error('Invalid referral code: INVALID');
      vi.mocked(api.payments.createCheckoutSession).mockRejectedValue(error);

      const { result } = renderHook(() => useStripeCheckout());

      await act(async () => {
        await result.current.initiateCheckout('price_123', 'INVALID');
      });

      expect(result.current.error).toBe('Invalid referral code: INVALID');
      expect(result.current.loading).toBe(false);
    });

    it('handles checkout session expiration scenario', async () => {
      const error = new Error('Checkout session has expired');
      vi.mocked(api.payments.createCheckoutSession).mockRejectedValue(error);

      const { result } = renderHook(() => useStripeCheckout());

      await act(async () => {
        await result.current.initiateCheckout('price_123');
      });

      expect(result.current.error).toBe('Checkout session has expired');
      expect(result.current.loading).toBe(false);
    });

    it('handles multiple concurrent checkout attempts', async () => {
      let resolveFirst: any;
      const firstPromise = new Promise<any>((resolve) => {
        resolveFirst = resolve;
      });

      vi.mocked(api.payments.createCheckoutSession)
        .mockReturnValueOnce(firstPromise)
        .mockResolvedValueOnce({
          checkout_url: 'https://checkout.stripe.com/session2',
          session_id: 'sess_2',
        });

      const { result } = renderHook(() => useStripeCheckout());

      // Start first checkout
      act(() => {
        result.current.initiateCheckout('price_1');
      });

      // Start second checkout while first is pending
      await act(async () => {
        await result.current.initiateCheckout('price_2');
      });

      // Second checkout should complete
      expect(window.location.href).toBe('https://checkout.stripe.com/session2');

      // Resolve first (should not affect state)
      resolveFirst({
        checkout_url: 'https://checkout.stripe.com/session1',
        session_id: 'sess_1',
      });
    });

    it('handles network timeout errors', async () => {
      const timeoutError = new Error('Request timeout after 30s');
      vi.mocked(api.payments.createCheckoutSession).mockRejectedValue(timeoutError);

      const { result } = renderHook(() => useStripeCheckout());

      await act(async () => {
        await result.current.initiateCheckout('price_123');
      });

      expect(result.current.error).toBe('Request timeout after 30s');
      expect(result.current.loading).toBe(false);
    });

    it('handles unauthorized errors when auth token is invalid', async () => {
      const authError = new Error('Unauthorized');
      vi.mocked(api.payments.createCheckoutSession).mockRejectedValue(authError);

      const { result } = renderHook(() => useStripeCheckout());

      await act(async () => {
        await result.current.initiateCheckout('price_123');
      });

      expect(result.current.error).toBe('Unauthorized');
      expect(result.current.loading).toBe(false);
    });
  });

  describe('State Consistency', () => {
    it('maintains consistent state across successful checkouts', async () => {
      vi.mocked(api.payments.createCheckoutSession).mockResolvedValue({
        checkout_url: 'https://checkout.stripe.com/session123',
        session_id: 'sess_123',
      });

      const { result } = renderHook(() => useStripeCheckout());

      // Initial state
      expect(result.current.loading).toBe(false);
      expect(result.current.error).toBeNull();

      // After successful checkout
      await act(async () => {
        await result.current.initiateCheckout('price_123');
      });

      expect(result.current.error).toBeNull();
      expect(result.current.loading).toBe(true); // Stays true after redirect
    });

    it('resets error state on new checkout attempt', async () => {
      // First attempt fails
      vi.mocked(api.payments.createCheckoutSession).mockRejectedValueOnce(
        new Error('Payment method declined')
      );

      const { result } = renderHook(() => useStripeCheckout());

      await act(async () => {
        await result.current.initiateCheckout('price_123');
      });

      expect(result.current.error).toBe('Payment method declined');

      // Second attempt starts (should clear error)
      vi.mocked(api.payments.createCheckoutSession).mockImplementation(
        () => new Promise(() => {}) // Never resolves
      );

      act(() => {
        result.current.initiateCheckout('price_456');
      });

      expect(result.current.error).toBeNull();
      expect(result.current.loading).toBe(true);
    });
  });
});
