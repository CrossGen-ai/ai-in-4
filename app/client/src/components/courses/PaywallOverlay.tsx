interface PaywallOverlayProps {
  price: number;
  currency: string;
  category: string;
  onUnlock: () => void;
  loading?: boolean;
}

export function PaywallOverlay({ price, currency, category, onUnlock, loading }: PaywallOverlayProps) {
  const formatPrice = (amount: number, curr: string) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: curr.toUpperCase(),
    }).format(amount / 100);
  };

  return (
    <div className="absolute inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center rounded-lg">
      <div className="text-center px-6 py-8 bg-white/10 rounded-lg border border-white/20">
        <div className="mb-4">
          <div className="inline-block px-3 py-1 bg-blue-500/80 text-white text-sm font-medium rounded-full mb-2">
            {category}
          </div>
          <h3 className="text-2xl font-bold text-white mb-2">
            {formatPrice(price, currency)}
          </h3>
        </div>

        <button
          onClick={onUnlock}
          disabled={loading}
          className="px-6 py-3 bg-blue-600 hover:bg-blue-700 text-white font-semibold rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {loading ? 'Processing...' : 'Unlock Access'}
        </button>

        <p className="mt-4 text-sm text-white/80">
          One-time payment • Instant access
        </p>
      </div>
    </div>
  );
}
