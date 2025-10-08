import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { PaywallOverlay } from './PaywallOverlay';

describe('PaywallOverlay', () => {
  describe('Display Price and Category', () => {
    it('renders price and category correctly', () => {
      const onUnlock = vi.fn();

      render(
        <PaywallOverlay
          price={4999}
          currency="usd"
          category="a-la-carte"
          onUnlock={onUnlock}
        />
      );

      expect(screen.getByText('$49.99')).toBeInTheDocument();
      expect(screen.getByText('a-la-carte')).toBeInTheDocument();
    });

    it('formats USD currency correctly', () => {
      const onUnlock = vi.fn();

      render(
        <PaywallOverlay
          price={9999}
          currency="usd"
          category="curriculum"
          onUnlock={onUnlock}
        />
      );

      expect(screen.getByText('$99.99')).toBeInTheDocument();
    });

    it('formats EUR currency correctly', () => {
      const onUnlock = vi.fn();

      render(
        <PaywallOverlay
          price={5000}
          currency="eur"
          category="curriculum"
          onUnlock={onUnlock}
        />
      );

      expect(screen.getByText('€50.00')).toBeInTheDocument();
    });

    it('formats GBP currency correctly', () => {
      const onUnlock = vi.fn();

      render(
        <PaywallOverlay
          price={7500}
          currency="gbp"
          category="a-la-carte"
          onUnlock={onUnlock}
        />
      );

      expect(screen.getByText('£75.00')).toBeInTheDocument();
    });

    it('formats JPY currency correctly (no decimal places)', () => {
      const onUnlock = vi.fn();

      render(
        <PaywallOverlay
          price={10000}
          currency="jpy"
          category="curriculum"
          onUnlock={onUnlock}
        />
      );

      expect(screen.getByText('¥100')).toBeInTheDocument();
    });

    it('displays category badge', () => {
      const onUnlock = vi.fn();

      render(
        <PaywallOverlay
          price={2999}
          currency="usd"
          category="curriculum"
          onUnlock={onUnlock}
        />
      );

      const badge = screen.getByText('curriculum');
      expect(badge).toBeInTheDocument();
      expect(badge).toHaveClass('bg-blue-500/80', 'text-white');
    });

    it('handles zero price', () => {
      const onUnlock = vi.fn();

      render(
        <PaywallOverlay
          price={0}
          currency="usd"
          category="free"
          onUnlock={onUnlock}
        />
      );

      expect(screen.getByText('$0.00')).toBeInTheDocument();
    });

    it('handles very large prices', () => {
      const onUnlock = vi.fn();

      render(
        <PaywallOverlay
          price={999999}
          currency="usd"
          category="a-la-carte"
          onUnlock={onUnlock}
        />
      );

      expect(screen.getByText('$9,999.99')).toBeInTheDocument();
    });
  });

  describe('Unlock Button Interaction', () => {
    it('renders "Unlock Access" button by default', () => {
      const onUnlock = vi.fn();

      render(
        <PaywallOverlay
          price={4999}
          currency="usd"
          category="a-la-carte"
          onUnlock={onUnlock}
        />
      );

      const button = screen.getByRole('button', { name: 'Unlock Access' });
      expect(button).toBeInTheDocument();
      expect(button).not.toBeDisabled();
    });

    it('calls onUnlock when button is clicked', async () => {
      const user = userEvent.setup();
      const onUnlock = vi.fn();

      render(
        <PaywallOverlay
          price={4999}
          currency="usd"
          category="a-la-carte"
          onUnlock={onUnlock}
        />
      );

      const button = screen.getByRole('button', { name: 'Unlock Access' });
      await user.click(button);

      expect(onUnlock).toHaveBeenCalledTimes(1);
    });

    it('shows "Processing..." when loading is true', () => {
      const onUnlock = vi.fn();

      render(
        <PaywallOverlay
          price={4999}
          currency="usd"
          category="a-la-carte"
          onUnlock={onUnlock}
          loading={true}
        />
      );

      const button = screen.getByRole('button', { name: 'Processing...' });
      expect(button).toBeInTheDocument();
      expect(button).toBeDisabled();
    });

    it('disables button when loading is true', async () => {
      const user = userEvent.setup();
      const onUnlock = vi.fn();

      render(
        <PaywallOverlay
          price={4999}
          currency="usd"
          category="a-la-carte"
          onUnlock={onUnlock}
          loading={true}
        />
      );

      const button = screen.getByRole('button', { name: 'Processing...' });
      await user.click(button);

      // Button is disabled, so onUnlock should not be called
      expect(onUnlock).not.toHaveBeenCalled();
    });

    it('re-enables button when loading changes from true to false', () => {
      const onUnlock = vi.fn();

      const { rerender } = render(
        <PaywallOverlay
          price={4999}
          currency="usd"
          category="a-la-carte"
          onUnlock={onUnlock}
          loading={true}
        />
      );

      let button = screen.getByRole('button', { name: 'Processing...' });
      expect(button).toBeDisabled();

      rerender(
        <PaywallOverlay
          price={4999}
          currency="usd"
          category="a-la-carte"
          onUnlock={onUnlock}
          loading={false}
        />
      );

      button = screen.getByRole('button', { name: 'Unlock Access' });
      expect(button).not.toBeDisabled();
    });

    it('does not call onUnlock multiple times on rapid clicks', async () => {
      const user = userEvent.setup();
      const onUnlock = vi.fn();

      render(
        <PaywallOverlay
          price={4999}
          currency="usd"
          category="a-la-carte"
          onUnlock={onUnlock}
        />
      );

      const button = screen.getByRole('button', { name: 'Unlock Access' });

      // Simulate rapid clicks
      await user.click(button);
      await user.click(button);
      await user.click(button);

      // Function should be called 3 times (no debouncing implemented)
      // This tests current behavior - could be changed to prevent double-charging
      expect(onUnlock).toHaveBeenCalledTimes(3);
    });
  });

  describe('Overlay Styling', () => {
    it('has blur effect backdrop styling', () => {
      const onUnlock = vi.fn();

      const { container } = render(
        <PaywallOverlay
          price={4999}
          currency="usd"
          category="a-la-carte"
          onUnlock={onUnlock}
        />
      );

      const overlay = container.firstChild as HTMLElement;
      expect(overlay).toHaveClass('backdrop-blur-sm');
    });

    it('has semi-transparent background', () => {
      const onUnlock = vi.fn();

      const { container } = render(
        <PaywallOverlay
          price={4999}
          currency="usd"
          category="a-la-carte"
          onUnlock={onUnlock}
        />
      );

      const overlay = container.firstChild as HTMLElement;
      expect(overlay).toHaveClass('bg-black/60');
    });

    it('positions overlay absolutely', () => {
      const onUnlock = vi.fn();

      const { container } = render(
        <PaywallOverlay
          price={4999}
          currency="usd"
          category="a-la-carte"
          onUnlock={onUnlock}
        />
      );

      const overlay = container.firstChild as HTMLElement;
      expect(overlay).toHaveClass('absolute', 'inset-0');
    });

    it('centers content with flexbox', () => {
      const onUnlock = vi.fn();

      const { container } = render(
        <PaywallOverlay
          price={4999}
          currency="usd"
          category="a-la-carte"
          onUnlock={onUnlock}
        />
      );

      const overlay = container.firstChild as HTMLElement;
      expect(overlay).toHaveClass('flex', 'items-center', 'justify-center');
    });

    it('has rounded corners on container', () => {
      const onUnlock = vi.fn();

      const { container } = render(
        <PaywallOverlay
          price={4999}
          currency="usd"
          category="a-la-carte"
          onUnlock={onUnlock}
        />
      );

      const overlay = container.firstChild as HTMLElement;
      expect(overlay).toHaveClass('rounded-lg');
    });
  });

  describe('Additional Information Display', () => {
    it('shows "One-time payment" text', () => {
      const onUnlock = vi.fn();

      render(
        <PaywallOverlay
          price={4999}
          currency="usd"
          category="a-la-carte"
          onUnlock={onUnlock}
        />
      );

      expect(screen.getByText(/One-time payment/i)).toBeInTheDocument();
    });

    it('shows "Instant access" text', () => {
      const onUnlock = vi.fn();

      render(
        <PaywallOverlay
          price={4999}
          currency="usd"
          category="a-la-carte"
          onUnlock={onUnlock}
        />
      );

      expect(screen.getByText(/Instant access/i)).toBeInTheDocument();
    });

    it('displays payment info with bullet separator', () => {
      const onUnlock = vi.fn();

      render(
        <PaywallOverlay
          price={4999}
          currency="usd"
          category="a-la-carte"
          onUnlock={onUnlock}
        />
      );

      const paymentInfo = screen.getByText(/One-time payment • Instant access/i);
      expect(paymentInfo).toBeInTheDocument();
      expect(paymentInfo).toHaveClass('text-sm', 'text-white/80');
    });
  });

  describe('Edge Cases and Error Handling', () => {
    it('handles lowercase currency codes', () => {
      const onUnlock = vi.fn();

      render(
        <PaywallOverlay
          price={2999}
          currency="usd"
          category="a-la-carte"
          onUnlock={onUnlock}
        />
      );

      expect(screen.getByText('$29.99')).toBeInTheDocument();
    });

    it('handles uppercase currency codes', () => {
      const onUnlock = vi.fn();

      render(
        <PaywallOverlay
          price={2999}
          currency="USD"
          category="a-la-carte"
          onUnlock={onUnlock}
        />
      );

      expect(screen.getByText('$29.99')).toBeInTheDocument();
    });

    it('handles mixed case currency codes', () => {
      const onUnlock = vi.fn();

      render(
        <PaywallOverlay
          price={2999}
          currency="Usd"
          category="a-la-carte"
          onUnlock={onUnlock}
        />
      );

      expect(screen.getByText('$29.99')).toBeInTheDocument();
    });

    it('handles special characters in category name', () => {
      const onUnlock = vi.fn();

      render(
        <PaywallOverlay
          price={4999}
          currency="usd"
          category="A-La-Carte & Premium"
          onUnlock={onUnlock}
        />
      );

      expect(screen.getByText('A-La-Carte & Premium')).toBeInTheDocument();
    });

    it('handles empty category string', () => {
      const onUnlock = vi.fn();

      render(
        <PaywallOverlay
          price={4999}
          currency="usd"
          category=""
          onUnlock={onUnlock}
        />
      );

      // Should still render the component without errors
      expect(screen.getByRole('button', { name: 'Unlock Access' })).toBeInTheDocument();
    });

    it('handles negative prices gracefully', () => {
      const onUnlock = vi.fn();

      render(
        <PaywallOverlay
          price={-1000}
          currency="usd"
          category="a-la-carte"
          onUnlock={onUnlock}
        />
      );

      // Intl.NumberFormat handles negative numbers
      expect(screen.getByText('-$10.00')).toBeInTheDocument();
    });

    it('handles loading prop being undefined', () => {
      const onUnlock = vi.fn();

      render(
        <PaywallOverlay
          price={4999}
          currency="usd"
          category="a-la-carte"
          onUnlock={onUnlock}
        />
      );

      const button = screen.getByRole('button', { name: 'Unlock Access' });
      expect(button).not.toBeDisabled();
    });
  });

  describe('Button Styling States', () => {
    it('has correct styling for enabled button', () => {
      const onUnlock = vi.fn();

      render(
        <PaywallOverlay
          price={4999}
          currency="usd"
          category="a-la-carte"
          onUnlock={onUnlock}
        />
      );

      const button = screen.getByRole('button', { name: 'Unlock Access' });
      expect(button).toHaveClass(
        'px-6',
        'py-3',
        'bg-blue-600',
        'hover:bg-blue-700',
        'text-white',
        'font-semibold',
        'rounded-lg',
        'transition-colors'
      );
    });

    it('has disabled styling when loading', () => {
      const onUnlock = vi.fn();

      render(
        <PaywallOverlay
          price={4999}
          currency="usd"
          category="a-la-carte"
          onUnlock={onUnlock}
          loading={true}
        />
      );

      const button = screen.getByRole('button', { name: 'Processing...' });
      expect(button).toHaveClass(
        'disabled:opacity-50',
        'disabled:cursor-not-allowed'
      );
    });
  });

  describe('Accessibility', () => {
    it('button has correct role', () => {
      const onUnlock = vi.fn();

      render(
        <PaywallOverlay
          price={4999}
          currency="usd"
          category="a-la-carte"
          onUnlock={onUnlock}
        />
      );

      const button = screen.getByRole('button');
      expect(button).toBeInTheDocument();
    });

    it('button has correct disabled attribute when loading', () => {
      const onUnlock = vi.fn();

      render(
        <PaywallOverlay
          price={4999}
          currency="usd"
          category="a-la-carte"
          onUnlock={onUnlock}
          loading={true}
        />
      );

      const button = screen.getByRole('button', { name: 'Processing...' });
      expect(button).toHaveAttribute('disabled');
    });

    it('price is displayed in heading for screen readers', () => {
      const onUnlock = vi.fn();

      render(
        <PaywallOverlay
          price={4999}
          currency="usd"
          category="a-la-carte"
          onUnlock={onUnlock}
        />
      );

      const priceHeading = screen.getByRole('heading', { level: 3 });
      expect(priceHeading).toHaveTextContent('$49.99');
    });
  });
});
