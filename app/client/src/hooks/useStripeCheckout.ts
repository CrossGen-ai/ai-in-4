import { useState } from 'react';
import { api } from '../lib/api/client';

export function useStripeCheckout() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const initiateCheckout = async (priceId: string, referrerCode?: string) => {
    setLoading(true);
    setError(null);

    try {
      const response = await api.payments.createCheckoutSession(priceId, referrerCode);

      // Redirect to Stripe checkout
      if (response.checkout_url) {
        window.location.href = response.checkout_url;
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to create checkout session');
      setLoading(false);
    }
  };

  return {
    initiateCheckout,
    loading,
    error,
  };
}
