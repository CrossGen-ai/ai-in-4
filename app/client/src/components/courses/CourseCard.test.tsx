import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { CourseCard } from './CourseCard';

describe('CourseCard Component', () => {
  describe('Free Course Rendering', () => {
    it('renders free course card with correct styling and labels', () => {
      const freeCourse = {
        id: 1,
        title: 'Introduction to Python',
        description: 'Learn Python basics',
        category: 'free',
        schedule: 'Self-paced',
      };

      render(<CourseCard course={freeCourse} hasAccess={false} />);

      // Check category badge - there are two "FREE" labels
      const freeLabels = screen.getAllByText('FREE');
      expect(freeLabels).toHaveLength(2);
      expect(freeLabels[0]).toHaveClass('text-green-800'); // Badge
      expect(freeLabels[1]).toHaveClass('text-green-600'); // Label

      // Check course info
      expect(screen.getByText('Introduction to Python')).toBeInTheDocument();
      expect(screen.getByText('Learn Python basics')).toBeInTheDocument();
      expect(screen.getByText(/Schedule:/)).toBeInTheDocument();
      expect(screen.getByText(/Self-paced/)).toBeInTheDocument();

      // Check button text for free course
      expect(screen.getByRole('button', { name: /access materials/i })).toBeInTheDocument();
    });

    it('renders free course with no description', () => {
      const freeCourse = {
        id: 1,
        title: 'Free Course',
        category: 'free',
      };

      render(<CourseCard course={freeCourse} hasAccess={false} />);

      expect(screen.getByText('No description available')).toBeInTheDocument();
    });

    it('renders free course without schedule field', () => {
      const freeCourse = {
        id: 1,
        title: 'Free Course',
        category: 'free',
      };

      render(<CourseCard course={freeCourse} hasAccess={false} />);

      expect(screen.queryByText(/Schedule:/)).not.toBeInTheDocument();
    });
  });

  describe('Paid Course with Access', () => {
    it('renders paid course with access and correct styling', () => {
      const paidCourse = {
        id: 2,
        title: 'Advanced Machine Learning',
        description: 'Deep dive into ML algorithms',
        category: 'alacarte',
        price: 9900, // $99.00 in cents
        currency: 'usd',
      };

      render(<CourseCard course={paidCourse} hasAccess={true} />);

      // Should show access button
      const button = screen.getByRole('button', { name: /access materials/i });
      expect(button).toBeInTheDocument();
      expect(button).toHaveClass('bg-blue-600');

      // Should show price
      expect(screen.getByText('$99.00')).toBeInTheDocument();

      // Should NOT show locked icon
      expect(screen.queryByText(/locked/i)).not.toBeInTheDocument();
    });

    it('formats different currencies correctly', () => {
      const euroCourse = {
        id: 3,
        title: 'European Course',
        category: 'alacarte',
        price: 5000, // €50.00 in cents
        currency: 'eur',
      };

      render(<CourseCard course={euroCourse} hasAccess={true} />);

      expect(screen.getByText('€50.00')).toBeInTheDocument();
    });

    it('uses USD as default currency when currency is not specified', () => {
      const course = {
        id: 4,
        title: 'Course Without Currency',
        category: 'alacarte',
        price: 2500, // $25.00 in cents
      };

      render(<CourseCard course={course} hasAccess={true} />);

      expect(screen.getByText('$25.00')).toBeInTheDocument();
    });
  });

  describe('Locked Course (No Access)', () => {
    it('renders locked course with lock icon and correct button text', () => {
      const lockedCourse = {
        id: 5,
        title: 'Premium Course',
        description: 'Advanced content',
        category: 'alacarte',
        price: 4900,
        currency: 'usd',
      };

      render(<CourseCard course={lockedCourse} hasAccess={false} />);

      // Should show lock icon and text
      expect(screen.getByText(/locked/i)).toBeInTheDocument();

      // Should show unlock button with gray styling
      const button = screen.getByRole('button', { name: /unlock course/i });
      expect(button).toBeInTheDocument();
      expect(button).toHaveClass('bg-gray-100');

      // Should show price
      expect(screen.getByText('$49.00')).toBeInTheDocument();
    });

    it('shows "Upgrade to Full Curriculum" button for curriculum courses', () => {
      const curriculumCourse = {
        id: 6,
        title: 'Full Curriculum Access',
        category: 'curriculum',
        price: 19900,
        currency: 'usd',
      };

      render(<CourseCard course={curriculumCourse} hasAccess={false} />);

      expect(screen.getByRole('button', { name: /upgrade to full curriculum/i })).toBeInTheDocument();
    });

    it('displays lock icon SVG with correct attributes', () => {
      const lockedCourse = {
        id: 7,
        title: 'Locked Course',
        category: 'alacarte',
      };

      const { container } = render(<CourseCard course={lockedCourse} hasAccess={false} />);

      const lockIcon = container.querySelector('svg');
      expect(lockIcon).toBeInTheDocument();
      expect(lockIcon).toHaveAttribute('viewBox', '0 0 20 20');
    });
  });

  describe('Category Badge Styling', () => {
    it('applies correct styling for free category', () => {
      const course = {
        id: 8,
        title: 'Free Course',
        category: 'free',
      };

      const { container } = render(<CourseCard course={course} hasAccess={false} />);

      const badge = container.querySelector('.bg-green-100');
      expect(badge).toBeInTheDocument();
      expect(badge).toHaveClass('text-green-800');
      expect(badge).toHaveTextContent('FREE');
    });

    it('applies correct styling for curriculum category', () => {
      const course = {
        id: 9,
        title: 'Curriculum Course',
        category: 'curriculum',
      };

      const { container } = render(<CourseCard course={course} hasAccess={false} />);

      const badge = container.querySelector('.bg-purple-100');
      expect(badge).toBeInTheDocument();
      expect(badge).toHaveClass('text-purple-800');
      expect(badge).toHaveTextContent('CURRICULUM');
    });

    it('applies correct styling for alacarte category', () => {
      const course = {
        id: 10,
        title: 'A La Carte Course',
        category: 'alacarte',
      };

      const { container } = render(<CourseCard course={course} hasAccess={false} />);

      const badge = container.querySelector('.bg-blue-100');
      expect(badge).toBeInTheDocument();
      expect(badge).toHaveClass('text-blue-800');
      expect(badge).toHaveTextContent('ALACARTE');
    });

    it('applies default styling for unknown category', () => {
      const course = {
        id: 11,
        title: 'Unknown Category Course',
        category: 'unknown',
      };

      const { container } = render(<CourseCard course={course} hasAccess={false} />);

      const badge = container.querySelector('.bg-gray-100');
      expect(badge).toBeInTheDocument();
      expect(badge).toHaveClass('text-gray-800');
      expect(badge).toHaveTextContent('UNKNOWN');
    });
  });

  describe('Button Click Interaction', () => {
    it('calls onAccessClick when button is clicked', async () => {
      const user = userEvent.setup();
      const onAccessClick = vi.fn();

      const course = {
        id: 12,
        title: 'Clickable Course',
        category: 'free',
      };

      render(<CourseCard course={course} hasAccess={false} onAccessClick={onAccessClick} />);

      const button = screen.getByRole('button', { name: /access materials/i });
      await user.click(button);

      expect(onAccessClick).toHaveBeenCalledTimes(1);
    });

    it('does not throw error when onAccessClick is undefined', async () => {
      const user = userEvent.setup();

      const course = {
        id: 13,
        title: 'Course Without Handler',
        category: 'free',
      };

      render(<CourseCard course={course} hasAccess={false} />);

      const button = screen.getByRole('button', { name: /access materials/i });

      // Should not throw error
      await expect(user.click(button)).resolves.not.toThrow();
    });

    it('calls onAccessClick multiple times when clicked multiple times', async () => {
      const user = userEvent.setup();
      const onAccessClick = vi.fn();

      const course = {
        id: 14,
        title: 'Multi-Click Course',
        category: 'alacarte',
      };

      render(<CourseCard course={course} hasAccess={false} onAccessClick={onAccessClick} />);

      const button = screen.getByRole('button', { name: /unlock course/i });
      await user.click(button);
      await user.click(button);
      await user.click(button);

      expect(onAccessClick).toHaveBeenCalledTimes(3);
    });
  });

  describe('Course Title Edge Cases', () => {
    it('uses course.name when course.title is not provided', () => {
      const course = {
        id: 15,
        title: '',
        name: 'Fallback Name',
        category: 'free',
      };

      render(<CourseCard course={course} hasAccess={false} />);

      expect(screen.getByText('Fallback Name')).toBeInTheDocument();
    });

    it('uses "Untitled Course" when neither title nor name is provided', () => {
      const course = {
        id: 16,
        title: '',
        category: 'free',
      };

      render(<CourseCard course={course} hasAccess={false} />);

      expect(screen.getByText('Untitled Course')).toBeInTheDocument();
    });

    it('prefers title over name when both are provided', () => {
      const course = {
        id: 17,
        title: 'Primary Title',
        name: 'Secondary Name',
        category: 'free',
      };

      render(<CourseCard course={course} hasAccess={false} />);

      expect(screen.getByText('Primary Title')).toBeInTheDocument();
      expect(screen.queryByText('Secondary Name')).not.toBeInTheDocument();
    });
  });

  describe('Price Display Edge Cases', () => {
    it('does not render price when price is 0', () => {
      const course = {
        id: 18,
        title: 'Free Premium Course',
        category: 'alacarte',
        price: 0,
      };

      render(<CourseCard course={course} hasAccess={false} />);

      // Price should not be rendered (0 is falsy)
      expect(screen.queryByText('$0.00')).not.toBeInTheDocument();
    });

    it('does not render price when price is undefined', () => {
      const course = {
        id: 19,
        title: 'Course Without Price',
        category: 'alacarte',
      };

      render(<CourseCard course={course} hasAccess={false} />);

      // No price element should be rendered
      const priceElement = screen.queryByText(/\$/);
      expect(priceElement).not.toBeInTheDocument();
    });

    it('renders very large price correctly', () => {
      const course = {
        id: 20,
        title: 'Expensive Course',
        category: 'curriculum',
        price: 999999, // $9,999.99
        currency: 'usd',
      };

      render(<CourseCard course={course} hasAccess={false} />);

      expect(screen.getByText('$9,999.99')).toBeInTheDocument();
    });

    it('renders price with 1 cent correctly', () => {
      const course = {
        id: 21,
        title: 'Penny Course',
        category: 'alacarte',
        price: 1, // $0.01
        currency: 'usd',
      };

      render(<CourseCard course={course} hasAccess={false} />);

      expect(screen.getByText('$0.01')).toBeInTheDocument();
    });
  });

  describe('Missing or Invalid Stripe Product/Price IDs', () => {
    it('renders course without price_id field', () => {
      const course = {
        id: 22,
        title: 'Course Without Price ID',
        category: 'alacarte',
        price: 5000,
        currency: 'usd',
      };

      render(<CourseCard course={course} hasAccess={false} />);

      expect(screen.getByText('$50.00')).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /unlock course/i })).toBeInTheDocument();
    });

    it('renders course with empty price_id', () => {
      const course = {
        id: 23,
        title: 'Course With Empty Price ID',
        category: 'alacarte',
        price: 3000,
        currency: 'usd',
        price_id: '',
      };

      render(<CourseCard course={course} hasAccess={false} />);

      expect(screen.getByText('$30.00')).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /unlock course/i })).toBeInTheDocument();
    });

    it('renders course with invalid price_id format', () => {
      const course = {
        id: 24,
        title: 'Course With Invalid Price ID',
        category: 'alacarte',
        price: 2000,
        currency: 'usd',
        price_id: 'invalid_price_id_123',
      };

      // Component should still render normally - validation happens elsewhere
      render(<CourseCard course={course} hasAccess={false} />);

      expect(screen.getByText('$20.00')).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /unlock course/i })).toBeInTheDocument();
    });
  });

  describe('Component Structure and Accessibility', () => {
    it('renders with proper semantic HTML structure', () => {
      const course = {
        id: 25,
        title: 'Accessible Course',
        description: 'Testing accessibility',
        category: 'alacarte',
      };

      const { container } = render(<CourseCard course={course} hasAccess={false} />);

      // Check for main container
      expect(container.querySelector('.bg-white.rounded-lg')).toBeInTheDocument();

      // Check for heading
      expect(screen.getByRole('heading', { level: 3 })).toBeInTheDocument();

      // Check for button
      expect(screen.getByRole('button')).toBeInTheDocument();
    });

    it('applies hover transition classes', () => {
      const course = {
        id: 26,
        title: 'Hoverable Course',
        category: 'free',
      };

      const { container } = render(<CourseCard course={course} hasAccess={false} />);

      const card = container.querySelector('.hover\\:shadow-lg');
      expect(card).toBeInTheDocument();
      expect(card).toHaveClass('transition-shadow');
    });

    it('truncates long descriptions with line-clamp', () => {
      const course = {
        id: 27,
        title: 'Long Description Course',
        description: 'This is a very long description that should be truncated. '.repeat(10),
        category: 'alacarte',
      };

      const { container } = render(<CourseCard course={course} hasAccess={false} />);

      const description = container.querySelector('.line-clamp-3');
      expect(description).toBeInTheDocument();
    });
  });

  describe('Integration Scenarios', () => {
    it('renders complete paid course with all fields', () => {
      const fullCourse = {
        id: 28,
        title: 'Complete Course',
        description: 'Full description with all fields',
        category: 'curriculum',
        schedule: 'Mondays and Wednesdays, 6-8 PM EST',
        price: 14900,
        price_id: 'price_1234567890',
        currency: 'usd',
      };

      render(<CourseCard course={fullCourse} hasAccess={false} />);

      // Verify all elements are rendered
      expect(screen.getByText('Complete Course')).toBeInTheDocument();
      expect(screen.getByText('Full description with all fields')).toBeInTheDocument();
      expect(screen.getByText('CURRICULUM')).toBeInTheDocument();
      expect(screen.getByText(/Mondays and Wednesdays/)).toBeInTheDocument();
      expect(screen.getByText('$149.00')).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /upgrade to full curriculum/i })).toBeInTheDocument();
      expect(screen.getByText(/locked/i)).toBeInTheDocument();
    });

    it('renders minimal free course with only required fields', () => {
      const minimalCourse = {
        id: 29,
        title: 'Minimal Course',
        category: 'free',
      };

      render(<CourseCard course={minimalCourse} hasAccess={false} />);

      // Should render with defaults
      expect(screen.getByText('Minimal Course')).toBeInTheDocument();
      expect(screen.getByText('No description available')).toBeInTheDocument();
      const freeLabels = screen.getAllByText('FREE');
      expect(freeLabels).toHaveLength(2);
      expect(screen.getByRole('button', { name: /access materials/i })).toBeInTheDocument();
    });
  });
});
