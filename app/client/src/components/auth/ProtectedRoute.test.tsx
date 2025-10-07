import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import { ProtectedRoute } from './ProtectedRoute';
import * as AuthContext from '../../context/AuthContext';

// Mock the useAuth hook
const mockUseAuth = vi.fn();

vi.mock('../../context/AuthContext', async () => {
  const actual = await vi.importActual('../../context/AuthContext');
  return {
    ...actual,
    useAuth: () => mockUseAuth(),
  };
});

// Helper to render component with router
const renderWithRouter = (children: React.ReactNode) => {
  return render(
    <BrowserRouter>
      {children}
    </BrowserRouter>
  );
};

describe('ProtectedRoute', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('Loading State', () => {
    it('should display loading indicator when authentication is being checked', () => {
      // Arrange
      mockUseAuth.mockReturnValue({
        isAuthenticated: false,
        loading: true,
        user: null,
      });

      // Act
      renderWithRouter(
        <ProtectedRoute>
          <div>Protected Content</div>
        </ProtectedRoute>
      );

      // Assert
      expect(screen.getByText('Loading...')).toBeInTheDocument();
      expect(screen.queryByText('Protected Content')).not.toBeInTheDocument();
    });

    it('should center loading indicator on screen', () => {
      // Arrange
      mockUseAuth.mockReturnValue({
        isAuthenticated: false,
        loading: true,
        user: null,
      });

      // Act
      const { container } = renderWithRouter(
        <ProtectedRoute>
          <div>Protected Content</div>
        </ProtectedRoute>
      );

      // Assert
      const loadingContainer = container.querySelector('.flex.items-center.justify-center.min-h-screen');
      expect(loadingContainer).toBeInTheDocument();
    });
  });

  describe('Unauthenticated Access', () => {
    it('should redirect to login page when user is not authenticated', () => {
      // Arrange
      mockUseAuth.mockReturnValue({
        isAuthenticated: false,
        loading: false,
        user: null,
      });

      // Act
      renderWithRouter(
        <ProtectedRoute>
          <div>Protected Content</div>
        </ProtectedRoute>
      );

      // Assert
      expect(screen.queryByText('Protected Content')).not.toBeInTheDocument();
      // Note: Navigate component will redirect, but in test environment it won't actually navigate
      // We verify the protected content is not rendered
    });

    it('should not render children when user is not authenticated', () => {
      // Arrange
      mockUseAuth.mockReturnValue({
        isAuthenticated: false,
        loading: false,
        user: null,
      });

      // Act
      renderWithRouter(
        <ProtectedRoute>
          <div data-testid="protected-content">Secret Content</div>
        </ProtectedRoute>
      );

      // Assert
      expect(screen.queryByTestId('protected-content')).not.toBeInTheDocument();
    });
  });

  describe('Authenticated Access', () => {
    it('should render children when user is authenticated', () => {
      // Arrange
      mockUseAuth.mockReturnValue({
        isAuthenticated: true,
        loading: false,
        user: { id: '1', email: 'test@example.com', name: 'Test User' },
      });

      // Act
      renderWithRouter(
        <ProtectedRoute>
          <div data-testid="protected-content">Protected Content</div>
        </ProtectedRoute>
      );

      // Assert
      expect(screen.getByTestId('protected-content')).toBeInTheDocument();
      expect(screen.getByText('Protected Content')).toBeInTheDocument();
    });

    it('should render multiple children when authenticated', () => {
      // Arrange
      mockUseAuth.mockReturnValue({
        isAuthenticated: true,
        loading: false,
        user: { id: '1', email: 'test@example.com', name: 'Test User' },
      });

      // Act
      renderWithRouter(
        <ProtectedRoute>
          <div>First Element</div>
          <div>Second Element</div>
        </ProtectedRoute>
      );

      // Assert
      expect(screen.getByText('First Element')).toBeInTheDocument();
      expect(screen.getByText('Second Element')).toBeInTheDocument();
    });
  });

  describe('Edge Cases', () => {
    it('should handle missing authentication token (unauthenticated state)', () => {
      // Arrange - Simulates localStorage.getItem('auth_token') returning null
      mockUseAuth.mockReturnValue({
        isAuthenticated: false,
        loading: false,
        user: null,
      });

      // Act
      renderWithRouter(
        <ProtectedRoute>
          <div>Protected Content</div>
        </ProtectedRoute>
      );

      // Assert
      expect(screen.queryByText('Protected Content')).not.toBeInTheDocument();
    });

    it('should handle invalid authentication token (after token validation fails)', () => {
      // Arrange - Simulates token being cleared after failed validation
      mockUseAuth.mockReturnValue({
        isAuthenticated: false,
        loading: false,
        user: null,
      });

      // Act
      renderWithRouter(
        <ProtectedRoute>
          <div>Protected Content</div>
        </ProtectedRoute>
      );

      // Assert
      expect(screen.queryByText('Protected Content')).not.toBeInTheDocument();
    });

    it('should handle token expiry during session (user becomes null)', () => {
      // Arrange - Simulates token expiry while on protected route
      mockUseAuth.mockReturnValue({
        isAuthenticated: false,
        loading: false,
        user: null,
      });

      // Act
      renderWithRouter(
        <ProtectedRoute>
          <div>Course Content</div>
        </ProtectedRoute>
      );

      // Assert - Should trigger redirect to login
      expect(screen.queryByText('Course Content')).not.toBeInTheDocument();
    });

    it('should handle browser back button after logout', () => {
      // Arrange - After logout, isAuthenticated becomes false
      mockUseAuth.mockReturnValue({
        isAuthenticated: false,
        loading: false,
        user: null,
      });

      // Act
      renderWithRouter(
        <ProtectedRoute>
          <div>Previous Page Content</div>
        </ProtectedRoute>
      );

      // Assert - Should redirect to login instead of showing cached content
      expect(screen.queryByText('Previous Page Content')).not.toBeInTheDocument();
    });

    it('should not flash content during loading state', () => {
      // Arrange
      mockUseAuth.mockReturnValue({
        isAuthenticated: false,
        loading: true,
        user: null,
      });

      // Act
      renderWithRouter(
        <ProtectedRoute>
          <div data-testid="protected-content">Protected Content</div>
        </ProtectedRoute>
      );

      // Assert - Protected content should not be visible during loading
      expect(screen.queryByTestId('protected-content')).not.toBeInTheDocument();
      expect(screen.getByText('Loading...')).toBeInTheDocument();
    });
  });

  describe('State Transitions', () => {
    it('should transition from loading to authenticated', () => {
      // Arrange - Start with loading state
      mockUseAuth.mockReturnValue({
        isAuthenticated: false,
        loading: true,
        user: null,
      });

      // Act - Initial render
      const { rerender } = renderWithRouter(
        <ProtectedRoute>
          <div data-testid="protected-content">Protected Content</div>
        </ProtectedRoute>
      );

      expect(screen.getByText('Loading...')).toBeInTheDocument();

      // Update to authenticated state
      mockUseAuth.mockReturnValue({
        isAuthenticated: true,
        loading: false,
        user: { id: '1', email: 'test@example.com', name: 'Test User' },
      });

      // Re-render with new state
      rerender(
        <BrowserRouter>
          <ProtectedRoute>
            <div data-testid="protected-content">Protected Content</div>
          </ProtectedRoute>
        </BrowserRouter>
      );

      // Assert - Should now show protected content
      expect(screen.queryByText('Loading...')).not.toBeInTheDocument();
      expect(screen.getByTestId('protected-content')).toBeInTheDocument();
    });

    it('should transition from loading to unauthenticated (redirect)', () => {
      // Arrange - Start with loading state
      mockUseAuth.mockReturnValue({
        isAuthenticated: false,
        loading: true,
        user: null,
      });

      // Act - Initial render
      const { rerender } = renderWithRouter(
        <ProtectedRoute>
          <div data-testid="protected-content">Protected Content</div>
        </ProtectedRoute>
      );

      expect(screen.getByText('Loading...')).toBeInTheDocument();

      // Update to unauthenticated state
      mockUseAuth.mockReturnValue({
        isAuthenticated: false,
        loading: false,
        user: null,
      });

      // Re-render with new state
      rerender(
        <BrowserRouter>
          <ProtectedRoute>
            <div data-testid="protected-content">Protected Content</div>
          </ProtectedRoute>
        </BrowserRouter>
      );

      // Assert - Should redirect (content not visible)
      expect(screen.queryByText('Loading...')).not.toBeInTheDocument();
      expect(screen.queryByTestId('protected-content')).not.toBeInTheDocument();
    });
  });
});
