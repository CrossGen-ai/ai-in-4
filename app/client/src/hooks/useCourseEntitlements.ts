import { useState, useEffect } from 'react';
import { api } from '../lib/api/client';

interface Entitlement {
  price_id: string;
  product_id: string;
  product_name: string;
  status: string;
  created_at: string;
}

export function useCourseEntitlements() {
  const [entitlements, setEntitlements] = useState<Entitlement[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchEntitlements = async () => {
    setLoading(true);
    setError(null);

    try {
      const data = await api.payments.getUserEntitlements();
      setEntitlements(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch entitlements');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchEntitlements();
  }, []);

  const hasAccess = (priceId: string): boolean => {
    return entitlements.some(
      (ent) => ent.price_id === priceId && ent.status === 'active'
    );
  };

  return {
    entitlements,
    loading,
    error,
    refetch: fetchEntitlements,
    hasAccess,
  };
}
