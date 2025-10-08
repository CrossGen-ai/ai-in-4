import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { CourseCard } from './CourseCard';
import * as useStripeCheckoutHook from '../../hooks/useStripeCheckout';

// Mock the hooks
vi.mock('../../hooks/useStripeCheckout');

// Mock PaywallOverlay component
vi.mock('./PaywallOverlay', () => ({
  PaywallOverlay: ({ onUnlock, loading }: any) => (
    <div data-testid="paywall-overlay">
      <button onClick={onUnlock} disabled={loading} data-testid="unlock-button">
        {loading ? 'Processing...' : 'Unlock Access'}
      </button>
    </div>
  ),
}));

describe('CourseCard', () => {
  const mockInitiateCheckout = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
    vi.mocked(useStripeCheckoutHook.useStripeCheckout).mockReturnValue({
      initiateCheckout: mockInitiateCheckout,
      loading: false,
      error: null,
    });
  });

  describe('Course Information Rendering', () => {
    it('renders course title, description, and price', () => {
      const course = {
        id: 'course-1',
        name: 'Introduction to AI',
        description: 'Learn the fundamentals of artificial intelligence',
        category: 'a-la-carte',
        price: 4999, // $49.99 in cents
        price_id: 'price_123',
        currency: 'usd',
      };

      render(<CourseCard course={course} hasAccess={false} />);

      expect(screen.getByText('Introduction to AI')).toBeInTheDocument();
      expect(screen.getByText('Learn the fundamentals of artificial intelligence')).toBeInTheDocument();
      expect(screen.getByText('$49.99')).toBeInTheDocument();
      expect(screen.getByText('A-LA-CARTE')).toBeInTheDocument();
    });

    it('renders default description when description is missing', () => {
      const course = {
        id: 'course-1',
        name: 'Test Course',
        category: 'free',
        currency: 'usd',
      };

      render(<CourseCard course={course} hasAccess={true} />);

      expect(screen.getByText('No description available')).toBeInTheDocument();
    });

    it('formats price correctly for different currencies', () => {
      const courseUSD = {
        id: 'course-1',
        name: 'USD Course',
        category: 'a-la-carte',
        price: 9999,
        price_id: 'price_usd',
        currency: 'usd',
      };

      const { rerender } = render(<CourseCard course={courseUSD} hasAccess={false} />);
      expect(screen.getByText('$99.99')).toBeInTheDocument();

      const courseEUR = {
        id: 'course-2',
        name: 'EUR Course',
        category: 'a-la-carte',
        price: 5000,
        price_id: 'price_eur',
        currency: 'eur',
      };

      rerender(<CourseCard course={courseEUR} hasAccess={false} />);
      expect(screen.getByText('€50.00')).toBeInTheDocument();
    });

    it('handles very long course descriptions', () => {
      const longDescription = 'A'.repeat(500);
      const course = {
        id: 'course-1',
        name: 'Test Course',
        description: longDescription,
        category: 'free',
        currency: 'usd',
      };

      render(<CourseCard course={course} hasAccess={true} />);

      // Description should be clamped with CSS (line-clamp-3)
      expect(screen.getByText(longDescription)).toBeInTheDocument();
    });
  });

  describe('Category Badge Rendering', () => {
    it('renders free category badge with correct styling', () => {
      const course = {
        id: 'course-1',
        name: 'Free Course',
        category: 'free',
        currency: 'usd',
      };

      render(<CourseCard course={course} hasAccess={true} />);

      const badge = screen.getByText('FREE', { selector: 'span.inline-block' });
      expect(badge).toBeInTheDocument();
      expect(badge).toHaveClass('bg-green-100', 'text-green-800');
    });

    it('renders curriculum category badge with correct styling', () => {
      const course = {
        id: 'course-1',
        name: 'Curriculum Course',
        category: 'curriculum',
        price: 2999,
        price_id: 'price_123',
        currency: 'usd',
      };

      render(<CourseCard course={course} hasAccess={false} />);

      const badge = screen.getByText('CURRICULUM');
      expect(badge).toHaveClass('bg-purple-100', 'text-purple-800');
    });

    it('renders a-la-carte category badge with correct styling', () => {
      const course = {
        id: 'course-1',
        name: 'A La Carte Course',
        category: 'a-la-carte',
        price: 1999,
        price_id: 'price_123',
        currency: 'usd',
      };

      render(<CourseCard course={course} hasAccess={false} />);

      const badge = screen.getByText('A-LA-CARTE');
      expect(badge).toHaveClass('bg-blue-100', 'text-blue-800');
    });

    it('shows FREE label for free courses', () => {
      const course = {
        id: 'course-1',
        name: 'Free Course',
        category: 'free',
        currency: 'usd',
      };

      render(<CourseCard course={course} hasAccess={false} />);

      expect(screen.getByText('FREE', { selector: 'span.text-green-600' })).toBeInTheDocument();
    });

    it('does not show FREE label for paid courses', () => {
      const course = {
        id: 'course-1',
        name: 'Paid Course',
        category: 'a-la-carte',
        price: 2999,
        price_id: 'price_123',
        currency: 'usd',
      };

      render(<CourseCard course={course} hasAccess={false} />);

      expect(screen.queryByText('FREE', { selector: 'span.text-green-600' })).not.toBeInTheDocument();
    });
  });

  describe('Access Button States', () => {
    it('shows "Access Now" button for free courses', () => {
      const course = {
        id: 'course-1',
        name: 'Free Course',
        category: 'free',
        currency: 'usd',
      };

      render(<CourseCard course={course} hasAccess={false} />);

      const button = screen.getByRole('button', { name: 'Access Now' });
      expect(button).toBeInTheDocument();
      expect(button).not.toBeDisabled();
      expect(button).toHaveClass('bg-green-600');
    });

    it('shows "Access Now" button for purchased courses', () => {
      const course = {
        id: 'course-1',
        name: 'Purchased Course',
        category: 'a-la-carte',
        price: 2999,
        price_id: 'price_123',
        currency: 'usd',
      };

      render(<CourseCard course={course} hasAccess={true} />);

      const button = screen.getByRole('button', { name: 'Access Now' });
      expect(button).toBeInTheDocument();
      expect(button).not.toBeDisabled();
      expect(button).toHaveClass('bg-green-600');
    });

    it('shows disabled "Locked" button for locked paid courses', () => {
      const course = {
        id: 'course-1',
        name: 'Locked Course',
        category: 'a-la-carte',
        price: 2999,
        price_id: 'price_123',
        currency: 'usd',
      };

      render(<CourseCard course={course} hasAccess={false} />);

      const button = screen.getByRole('button', { name: 'Locked' });
      expect(button).toBeInTheDocument();
      expect(button).toBeDisabled();
      expect(button).toHaveClass('bg-gray-200', 'text-gray-500');
    });

    it('treats course without price as free', () => {
      const course = {
        id: 'course-1',
        name: 'Course Without Price',
        category: 'curriculum',
        currency: 'usd',
      };

      render(<CourseCard course={course} hasAccess={false} />);

      const button = screen.getByRole('button', { name: 'Access Now' });
      expect(button).toBeInTheDocument();
      expect(button).not.toBeDisabled();
    });

    it('calls onAccessClick when Access Now button is clicked', async () => {
      const user = userEvent.setup();
      const onAccessClick = vi.fn();
      const course = {
        id: 'course-1',
        name: 'Free Course',
        category: 'free',
        currency: 'usd',
      };

      render(<CourseCard course={course} hasAccess={true} onAccessClick={onAccessClick} />);

      const button = screen.getByRole('button', { name: 'Access Now' });
      await user.click(button);

      expect(onAccessClick).toHaveBeenCalledTimes(1);
    });

    it('does not trigger onAccessClick when locked button is clicked', async () => {
      const user = userEvent.setup();
      const onAccessClick = vi.fn();
      const course = {
        id: 'course-1',
        name: 'Locked Course',
        category: 'a-la-carte',
        price: 2999,
        price_id: 'price_123',
        currency: 'usd',
      };

      render(<CourseCard course={course} hasAccess={false} onAccessClick={onAccessClick} />);

      const button = screen.getByRole('button', { name: 'Locked' });
      await user.click(button);

      // Button is disabled, so click should not trigger callback
      expect(onAccessClick).not.toHaveBeenCalled();
    });
  });

  describe('Paywall Overlay', () => {
    it('shows paywall overlay for locked paid courses', () => {
      const course = {
        id: 'course-1',
        name: 'Locked Course',
        category: 'a-la-carte',
        price: 2999,
        price_id: 'price_123',
        currency: 'usd',
      };

      render(<CourseCard course={course} hasAccess={false} />);

      expect(screen.getByTestId('paywall-overlay')).toBeInTheDocument();
    });

    it('does not show paywall overlay for free courses', () => {
      const course = {
        id: 'course-1',
        name: 'Free Course',
        category: 'free',
        currency: 'usd',
      };

      render(<CourseCard course={course} hasAccess={false} />);

      expect(screen.queryByTestId('paywall-overlay')).not.toBeInTheDocument();
    });

    it('does not show paywall overlay for purchased courses', () => {
      const course = {
        id: 'course-1',
        name: 'Purchased Course',
        category: 'a-la-carte',
        price: 2999,
        price_id: 'price_123',
        currency: 'usd',
      };

      render(<CourseCard course={course} hasAccess={true} />);

      expect(screen.queryByTestId('paywall-overlay')).not.toBeInTheDocument();
    });

    it('does not show paywall for courses without price', () => {
      const course = {
        id: 'course-1',
        name: 'No Price Course',
        category: 'curriculum',
        currency: 'usd',
      };

      render(<CourseCard course={course} hasAccess={false} />);

      expect(screen.queryByTestId('paywall-overlay')).not.toBeInTheDocument();
    });
  });

  describe('Stripe Checkout Integration', () => {
    it('initiates checkout when unlock button is clicked', async () => {
      const user = userEvent.setup();
      const course = {
        id: 'course-1',
        name: 'Locked Course',
        category: 'a-la-carte',
        price: 2999,
        price_id: 'price_123',
        currency: 'usd',
      };

      render(<CourseCard course={course} hasAccess={false} />);

      const unlockButton = screen.getByTestId('unlock-button');
      await user.click(unlockButton);

      expect(mockInitiateCheckout).toHaveBeenCalledWith('price_123');
    });

    it('does not initiate checkout when price_id is missing', async () => {
      const user = userEvent.setup();
      const course = {
        id: 'course-1',
        name: 'Course Without Price ID',
        category: 'a-la-carte',
        price: 2999,
        currency: 'usd',
      };

      render(<CourseCard course={course} hasAccess={false} />);

      const unlockButton = screen.getByTestId('unlock-button');
      await user.click(unlockButton);

      expect(mockInitiateCheckout).not.toHaveBeenCalled();
    });

    it('shows loading state in paywall overlay during checkout', () => {
      vi.mocked(useStripeCheckoutHook.useStripeCheckout).mockReturnValue({
        initiateCheckout: mockInitiateCheckout,
        loading: true,
        error: null,
      });

      const course = {
        id: 'course-1',
        name: 'Locked Course',
        category: 'a-la-carte',
        price: 2999,
        price_id: 'price_123',
        currency: 'usd',
      };

      render(<CourseCard course={course} hasAccess={false} />);

      const unlockButton = screen.getByTestId('unlock-button');
      expect(unlockButton).toBeDisabled();
      expect(unlockButton).toHaveTextContent('Processing...');
    });

    it('passes loading state to PaywallOverlay', () => {
      vi.mocked(useStripeCheckoutHook.useStripeCheckout).mockReturnValue({
        initiateCheckout: mockInitiateCheckout,
        loading: true,
        error: null,
      });

      const course = {
        id: 'course-1',
        name: 'Locked Course',
        category: 'a-la-carte',
        price: 2999,
        price_id: 'price_123',
        currency: 'usd',
      };

      render(<CourseCard course={course} hasAccess={false} />);

      expect(screen.getByTestId('paywall-overlay')).toBeInTheDocument();
      expect(screen.getByTestId('unlock-button')).toBeDisabled();
    });
  });

  describe('Edge Cases', () => {
    it('handles zero price as free course', () => {
      const course = {
        id: 'course-1',
        name: 'Zero Price Course',
        category: 'a-la-carte',
        price: 0,
        currency: 'usd',
      };

      render(<CourseCard course={course} hasAccess={false} />);

      expect(screen.getByRole('button', { name: 'Access Now' })).toBeInTheDocument();
      expect(screen.queryByTestId('paywall-overlay')).not.toBeInTheDocument();
    });

    it('handles null price correctly', () => {
      const course = {
        id: 'course-1',
        name: 'Null Price Course',
        category: 'curriculum',
        price: null as any,
        currency: 'usd',
      };

      render(<CourseCard course={course} hasAccess={false} />);

      expect(screen.getByRole('button', { name: 'Access Now' })).toBeInTheDocument();
      expect(screen.queryByTestId('paywall-overlay')).not.toBeInTheDocument();
    });

    it('handles undefined price correctly', () => {
      const course = {
        id: 'course-1',
        name: 'Undefined Price Course',
        category: 'a-la-carte',
        price: undefined,
        currency: 'usd',
      };

      render(<CourseCard course={course} hasAccess={false} />);

      expect(screen.getByRole('button', { name: 'Access Now' })).toBeInTheDocument();
      expect(screen.queryByTestId('paywall-overlay')).not.toBeInTheDocument();
    });

    it('handles empty price_id gracefully', async () => {
      const user = userEvent.setup();
      const course = {
        id: 'course-1',
        name: 'Empty Price ID',
        category: 'a-la-carte',
        price: 2999,
        price_id: '',
        currency: 'usd',
      };

      render(<CourseCard course={course} hasAccess={false} />);

      const unlockButton = screen.getByTestId('unlock-button');
      await user.click(unlockButton);

      // Should not call initiateCheckout with empty string
      expect(mockInitiateCheckout).not.toHaveBeenCalled();
    });

    it('handles very large price values', () => {
      const course = {
        id: 'course-1',
        name: 'Expensive Course',
        category: 'a-la-carte',
        price: 999999, // $9,999.99
        price_id: 'price_123',
        currency: 'usd',
      };

      render(<CourseCard course={course} hasAccess={false} />);

      expect(screen.getByText('$9,999.99')).toBeInTheDocument();
    });

    it('handles missing onAccessClick prop', async () => {
      const user = userEvent.setup();
      const course = {
        id: 'course-1',
        name: 'Free Course',
        category: 'free',
        currency: 'usd',
      };

      render(<CourseCard course={course} hasAccess={true} />);

      const button = screen.getByRole('button', { name: 'Access Now' });

      // Should not throw error when clicked without callback
      await expect(user.click(button)).resolves.not.toThrow();
    });

    it('handles special characters in course name', () => {
      const course = {
        id: 'course-1',
        name: 'AI & ML: Advanced "Techniques" (2024)',
        category: 'free',
        currency: 'usd',
      };

      render(<CourseCard course={course} hasAccess={true} />);

      expect(screen.getByText('AI & ML: Advanced "Techniques" (2024)')).toBeInTheDocument();
    });

    it('handles special characters in description', () => {
      const course = {
        id: 'course-1',
        name: 'Test Course',
        description: 'Learn <html>, "JavaScript" & React.js!',
        category: 'free',
        currency: 'usd',
      };

      render(<CourseCard course={course} hasAccess={true} />);

      expect(screen.getByText('Learn <html>, "JavaScript" & React.js!')).toBeInTheDocument();
    });
  });

  describe('Lock State Logic', () => {
    it('course is locked when paid and no access', () => {
      const course = {
        id: 'course-1',
        name: 'Locked Course',
        category: 'a-la-carte',
        price: 2999,
        price_id: 'price_123',
        currency: 'usd',
      };

      render(<CourseCard course={course} hasAccess={false} />);

      expect(screen.getByRole('button', { name: 'Locked' })).toBeDisabled();
      expect(screen.getByTestId('paywall-overlay')).toBeInTheDocument();
    });

    it('course is unlocked when paid and has access', () => {
      const course = {
        id: 'course-1',
        name: 'Unlocked Course',
        category: 'a-la-carte',
        price: 2999,
        price_id: 'price_123',
        currency: 'usd',
      };

      render(<CourseCard course={course} hasAccess={true} />);

      expect(screen.getByRole('button', { name: 'Access Now' })).not.toBeDisabled();
      expect(screen.queryByTestId('paywall-overlay')).not.toBeInTheDocument();
    });

    it('free course is always unlocked regardless of hasAccess', () => {
      const course = {
        id: 'course-1',
        name: 'Free Course',
        category: 'free',
        currency: 'usd',
      };

      const { rerender } = render(<CourseCard course={course} hasAccess={false} />);

      expect(screen.getByRole('button', { name: 'Access Now' })).not.toBeDisabled();
      expect(screen.queryByTestId('paywall-overlay')).not.toBeInTheDocument();

      rerender(<CourseCard course={course} hasAccess={true} />);

      expect(screen.getByRole('button', { name: 'Access Now' })).not.toBeDisabled();
      expect(screen.queryByTestId('paywall-overlay')).not.toBeInTheDocument();
    });

    it('curriculum category with no price is treated as free', () => {
      const course = {
        id: 'course-1',
        name: 'Curriculum Course',
        category: 'curriculum',
        currency: 'usd',
      };

      render(<CourseCard course={course} hasAccess={false} />);

      expect(screen.getByRole('button', { name: 'Access Now' })).not.toBeDisabled();
      expect(screen.queryByTestId('paywall-overlay')).not.toBeInTheDocument();
    });
  });

  describe('Accessibility', () => {
    it('button has correct disabled state for screen readers', () => {
      const course = {
        id: 'course-1',
        name: 'Locked Course',
        category: 'a-la-carte',
        price: 2999,
        price_id: 'price_123',
        currency: 'usd',
      };

      render(<CourseCard course={course} hasAccess={false} />);

      const button = screen.getByRole('button', { name: 'Locked' });
      expect(button).toHaveAttribute('disabled');
    });

    it('accessible course information structure', () => {
      const course = {
        id: 'course-1',
        name: 'Test Course',
        description: 'Test Description',
        category: 'a-la-carte',
        price: 2999,
        price_id: 'price_123',
        currency: 'usd',
      };

      render(<CourseCard course={course} hasAccess={false} />);

      // Title should be in h3
      const title = screen.getByRole('heading', { level: 3, name: 'Test Course' });
      expect(title).toBeInTheDocument();
    });
  });
});
