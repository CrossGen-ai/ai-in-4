import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter } from 'react-router-dom';
import { Login } from './Login';
import { AuthProvider } from '../context/AuthContext';
import * as apiClient from '../lib/api/client';

// Mock the API client
vi.mock('../lib/api/client', () => ({
  api: {
    auth: {
      requestMagicLink: vi.fn(),
      validateMagicLink: vi.fn(),
      logout: vi.fn(),
    },
    users: {
      getCurrentUser: vi.fn(),
    },
  },
}));

// Mock react-router-dom navigation
const mockNavigate = vi.fn();
vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom');
  return {
    ...actual,
    useNavigate: () => mockNavigate,
  };
});

// Helper to render component with providers
const renderWithProviders = (ui: React.ReactElement, { route = '/' } = {}) => {
  return render(
    <MemoryRouter initialEntries={[route]}>
      <AuthProvider>{ui}</AuthProvider>
    </MemoryRouter>
  );
};

describe('Login Component', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    localStorage.clear();
    mockNavigate.mockClear();
  });

  describe('Magic Link Request Form', () => {
    it('renders login form with email input and submit button', () => {
      renderWithProviders(<Login />);

      expect(screen.getByText('Welcome Back')).toBeInTheDocument();
      expect(screen.getByText('Enter your email to receive a magic link')).toBeInTheDocument();
      expect(screen.getByPlaceholderText('you@example.com')).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /send magic link/i })).toBeInTheDocument();
    });

    it('displays success message when magic link is sent successfully', async () => {
      const user = userEvent.setup();
      vi.mocked(apiClient.api.auth.requestMagicLink).mockResolvedValueOnce({
        message: 'Magic link sent',
      });

      renderWithProviders(<Login />);

      const emailInput = screen.getByPlaceholderText('you@example.com');
      const submitButton = screen.getByRole('button', { name: /send magic link/i });

      await user.type(emailInput, 'test@example.com');
      await user.click(submitButton);

      await waitFor(() => {
        expect(screen.getByText('Magic link sent! Check your email.')).toBeInTheDocument();
      });

      expect(apiClient.api.auth.requestMagicLink).toHaveBeenCalledWith('test@example.com');
      expect(emailInput).toHaveValue(''); // Email should be cleared after success
    });

    it('displays loading state while sending magic link', async () => {
      const user = userEvent.setup();
      vi.mocked(apiClient.api.auth.requestMagicLink).mockImplementation(
        () => new Promise(resolve => setTimeout(resolve, 100))
      );

      renderWithProviders(<Login />);

      const emailInput = screen.getByPlaceholderText('you@example.com');
      const submitButton = screen.getByRole('button', { name: /send magic link/i });

      await user.type(emailInput, 'test@example.com');
      await user.click(submitButton);

      expect(screen.getByRole('button', { name: /sending.../i })).toBeDisabled();
    });

    it('displays error message when magic link request fails', async () => {
      const user = userEvent.setup();
      vi.mocked(apiClient.api.auth.requestMagicLink).mockRejectedValueOnce(
        new Error('Failed to send email')
      );

      renderWithProviders(<Login />);

      const emailInput = screen.getByPlaceholderText('you@example.com');
      const submitButton = screen.getByRole('button', { name: /send magic link/i });

      await user.type(emailInput, 'test@example.com');
      await user.click(submitButton);

      await waitFor(() => {
        expect(screen.getByText('Failed to send email')).toBeInTheDocument();
      });
    });

    it('displays generic error message when error has no message', async () => {
      const user = userEvent.setup();
      vi.mocked(apiClient.api.auth.requestMagicLink).mockRejectedValueOnce({});

      renderWithProviders(<Login />);

      const emailInput = screen.getByPlaceholderText('you@example.com');
      const submitButton = screen.getByRole('button', { name: /send magic link/i });

      await user.type(emailInput, 'test@example.com');
      await user.click(submitButton);

      await waitFor(() => {
        expect(screen.getByText('Failed to send magic link')).toBeInTheDocument();
      });
    });

    it('requires email input to be filled', async () => {
      const user = userEvent.setup();

      renderWithProviders(<Login />);

      const submitButton = screen.getByRole('button', { name: /send magic link/i });
      await user.click(submitButton);

      // Form should not submit with empty email (HTML5 validation)
      expect(apiClient.api.auth.requestMagicLink).not.toHaveBeenCalled();
    });

    it('handles empty email edge case gracefully', async () => {
      const user = userEvent.setup();
      vi.mocked(apiClient.api.auth.requestMagicLink).mockResolvedValueOnce({
        message: 'Success',
      });

      renderWithProviders(<Login />);

      const emailInput = screen.getByPlaceholderText('you@example.com') as HTMLInputElement;

      // Try to bypass HTML5 validation by setting value programmatically
      emailInput.value = '';
      emailInput.removeAttribute('required');

      const submitButton = screen.getByRole('button', { name: /send magic link/i });
      await user.click(submitButton);

      // Form will submit with empty string since we removed validation
      await waitFor(() => {
        expect(apiClient.api.auth.requestMagicLink).toHaveBeenCalledWith('');
      });
    });
  });

  describe('Magic Link Validation', () => {
    it('validates magic link token from URL on mount', async () => {
      vi.mocked(apiClient.api.auth.validateMagicLink).mockResolvedValueOnce({
        access_token: 'valid-token',
        user: {
          id: 1,
          email: 'test@example.com',
          full_name: 'Test User',
          user_type: 'student',
          is_active: true,
          created_at: new Date().toISOString(),
        },
      });

      renderWithProviders(<Login />, { route: '/?token=magic-link-token' });

      await waitFor(() => {
        expect(apiClient.api.auth.validateMagicLink).toHaveBeenCalledWith('magic-link-token');
        expect(mockNavigate).toHaveBeenCalledWith('/dashboard');
      });
    });

    it('displays error when magic link token is invalid', async () => {
      vi.mocked(apiClient.api.auth.validateMagicLink).mockRejectedValueOnce(
        new Error('Invalid token')
      );

      renderWithProviders(<Login />, { route: '/?token=invalid-token' });

      await waitFor(() => {
        expect(screen.getByText('Invalid or expired magic link. Please request a new one.')).toBeInTheDocument();
      });

      expect(mockNavigate).not.toHaveBeenCalled();
    });

    it('displays error when magic link token is expired', async () => {
      vi.mocked(apiClient.api.auth.validateMagicLink).mockRejectedValueOnce(
        new Error('Token expired')
      );

      renderWithProviders(<Login />, { route: '/?token=expired-token' });

      await waitFor(() => {
        expect(screen.getByText('Invalid or expired magic link. Please request a new one.')).toBeInTheDocument();
      });
    });

    it('handles validateToken returning false', async () => {
      // Mock the AuthContext validateToken to return false
      vi.mocked(apiClient.api.auth.validateMagicLink).mockRejectedValueOnce(
        new Error('Validation failed')
      );

      renderWithProviders(<Login />, { route: '/?token=bad-token' });

      await waitFor(() => {
        expect(screen.getByText('Invalid or expired magic link. Please request a new one.')).toBeInTheDocument();
      });

      expect(mockNavigate).not.toHaveBeenCalled();
    });

    it('displays generic error message when validateToken fails without message', async () => {
      vi.mocked(apiClient.api.auth.validateMagicLink).mockRejectedValueOnce({});

      renderWithProviders(<Login />, { route: '/?token=error-token' });

      await waitFor(() => {
        expect(screen.getByText('Invalid or expired magic link. Please request a new one.')).toBeInTheDocument();
      });
    });

    it('shows loading state during token validation', async () => {
      vi.mocked(apiClient.api.auth.validateMagicLink).mockImplementation(
        () => new Promise((_, reject) => setTimeout(() => reject(new Error('timeout')), 100))
      );

      renderWithProviders(<Login />, { route: '/?token=validating-token' });

      // During validation, the button should show loading state (button text changes to "Sending...")
      const button = screen.getByRole('button', { name: /sending/i });
      expect(button).toBeDisabled();

      // Wait for validation to complete
      await waitFor(() => {
        expect(screen.getByText('Invalid or expired magic link. Please request a new one.')).toBeInTheDocument();
      });
    });
  });

  describe('Network Error Handling', () => {
    it('handles network errors during magic link request', async () => {
      const user = userEvent.setup();
      vi.mocked(apiClient.api.auth.requestMagicLink).mockRejectedValueOnce(
        new Error('Network error')
      );

      renderWithProviders(<Login />);

      const emailInput = screen.getByPlaceholderText('you@example.com');
      const submitButton = screen.getByRole('button', { name: /send magic link/i });

      await user.type(emailInput, 'test@example.com');
      await user.click(submitButton);

      await waitFor(() => {
        expect(screen.getByText('Network error')).toBeInTheDocument();
      });
    });

    it('handles network errors during token validation', async () => {
      vi.mocked(apiClient.api.auth.validateMagicLink).mockRejectedValueOnce(
        new Error('Network connection failed')
      );

      renderWithProviders(<Login />, { route: '/?token=network-error-token' });

      await waitFor(() => {
        expect(screen.getByText('Invalid or expired magic link. Please request a new one.')).toBeInTheDocument();
      });
    });
  });

  describe('UI Elements', () => {
    it('renders link to registration page', () => {
      renderWithProviders(<Login />);

      const registerLink = screen.getByRole('link', { name: /create one/i });
      expect(registerLink).toBeInTheDocument();
      expect(registerLink).toHaveAttribute('href', '/register');
    });

    it('shows dev login link in development mode', () => {
      // Mock DEV environment
      vi.stubEnv('DEV', true);

      renderWithProviders(<Login />);

      const devLoginLink = screen.getByRole('link', { name: /quick login \(dev\)/i });
      expect(devLoginLink).toBeInTheDocument();
      expect(devLoginLink).toHaveAttribute('href', '/dev-login');
      expect(screen.getByText('Development Mode')).toBeInTheDocument();

      vi.unstubAllEnvs();
    });

    it('hides dev login link in production mode', () => {
      // Mock production environment
      vi.stubEnv('DEV', false);

      renderWithProviders(<Login />);

      expect(screen.queryByText('Development Mode')).not.toBeInTheDocument();
      expect(screen.queryByRole('link', { name: /quick login \(dev\)/i })).not.toBeInTheDocument();

      vi.unstubAllEnvs();
    });
  });

  describe('Form State Management', () => {
    it('clears error message when starting new magic link request', async () => {
      const user = userEvent.setup();

      // First request fails
      vi.mocked(apiClient.api.auth.requestMagicLink).mockRejectedValueOnce(
        new Error('First error')
      );

      renderWithProviders(<Login />);

      const emailInput = screen.getByPlaceholderText('you@example.com');
      const submitButton = screen.getByRole('button', { name: /send magic link/i });

      await user.type(emailInput, 'test@example.com');
      await user.click(submitButton);

      await waitFor(() => {
        expect(screen.getByText('First error')).toBeInTheDocument();
      });

      // Second request succeeds
      vi.mocked(apiClient.api.auth.requestMagicLink).mockResolvedValueOnce({
        message: 'Success',
      });

      await user.clear(emailInput);
      await user.type(emailInput, 'test2@example.com');
      await user.click(submitButton);

      await waitFor(() => {
        expect(screen.queryByText('First error')).not.toBeInTheDocument();
        expect(screen.getByText('Magic link sent! Check your email.')).toBeInTheDocument();
      });
    });

    it('clears success message when starting new magic link request', async () => {
      const user = userEvent.setup();

      // First request succeeds
      vi.mocked(apiClient.api.auth.requestMagicLink).mockResolvedValueOnce({
        message: 'Success',
      });

      renderWithProviders(<Login />);

      const emailInput = screen.getByPlaceholderText('you@example.com');
      const submitButton = screen.getByRole('button', { name: /send magic link/i });

      await user.type(emailInput, 'test@example.com');
      await user.click(submitButton);

      await waitFor(() => {
        expect(screen.getByText('Magic link sent! Check your email.')).toBeInTheDocument();
      });

      // Second request
      vi.mocked(apiClient.api.auth.requestMagicLink).mockResolvedValueOnce({
        message: 'Success again',
      });

      await user.type(emailInput, 'test2@example.com');
      await user.click(submitButton);

      await waitFor(() => {
        // Success message should be cleared and shown again
        const successMessages = screen.getAllByText('Magic link sent! Check your email.');
        expect(successMessages).toHaveLength(1);
      });
    });
  });

  describe('Email Input Validation Edge Cases', () => {
    it('accepts valid email formats', async () => {
      const user = userEvent.setup();
      vi.mocked(apiClient.api.auth.requestMagicLink).mockResolvedValue({
        message: 'Success',
      });

      renderWithProviders(<Login />);

      const emailInput = screen.getByPlaceholderText('you@example.com');
      const submitButton = screen.getByRole('button', { name: /send magic link/i });

      const validEmails = [
        'test@example.com',
        'user.name@example.co.uk',
        'test+tag@example.com',
        'test_user@example.com',
      ];

      for (const email of validEmails) {
        await user.clear(emailInput);
        await user.type(emailInput, email);
        await user.click(submitButton);

        await waitFor(() => {
          expect(apiClient.api.auth.requestMagicLink).toHaveBeenCalledWith(email);
        });

        vi.clearAllMocks();
      }
    });
  });
});
