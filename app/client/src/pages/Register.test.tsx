import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { BrowserRouter } from 'react-router-dom';
import { Register } from './Register';
import { api } from '../lib/api/client';

// Mock the API client
vi.mock('../lib/api/client', () => ({
  api: {
    auth: {
      register: vi.fn(),
    },
  },
}));

// Mock useNavigate
const mockNavigate = vi.fn();
vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom');
  return {
    ...actual,
    useNavigate: () => mockNavigate,
  };
});

describe('Register Component', () => {
  const user = userEvent.setup();

  beforeEach(() => {
    vi.clearAllMocks();
  });

  const renderRegister = () => {
    return render(
      <BrowserRouter>
        <Register />
      </BrowserRouter>
    );
  };

  describe('Initial Render', () => {
    it('renders the registration form with all fields', () => {
      renderRegister();

      expect(screen.getByText('Create Your Account')).toBeInTheDocument();
      expect(screen.getByText('Join the AI in 4 learning community')).toBeInTheDocument();
      expect(screen.getByText('Email Address')).toBeInTheDocument();
      expect(screen.getByPlaceholderText('you@example.com')).toBeInTheDocument();
      expect(screen.getByText('AI Experience Level')).toBeInTheDocument();
      expect(screen.getByText('Your Background (Optional)')).toBeInTheDocument();
      expect(screen.getByPlaceholderText('Tell us about your professional background...')).toBeInTheDocument();
      expect(screen.getByText('Learning Goals (Optional)')).toBeInTheDocument();
      expect(screen.getByPlaceholderText('What do you hope to achieve with AI?')).toBeInTheDocument();
      expect(screen.getByRole('button', { name: 'Create Account' })).toBeInTheDocument();
    });

    it('has default experience level set to Beginner', () => {
      renderRegister();

      const selectElement = screen.getByDisplayValue('Beginner - New to AI') as HTMLSelectElement;
      expect(selectElement.value).toBe('Beginner');
    });

    it('renders link to login page', () => {
      renderRegister();

      const loginLink = screen.getByRole('link', { name: 'Sign in' });
      expect(loginLink).toBeInTheDocument();
      expect(loginLink).toHaveAttribute('href', '/login');
    });
  });

  describe('Form Validation - Email', () => {
    it('requires email field to be filled', async () => {
      renderRegister();

      const submitButton = screen.getByRole('button', { name: 'Create Account' });
      await user.click(submitButton);

      // HTML5 validation prevents form submission
      expect(api.auth.register).not.toHaveBeenCalled();
    });

    it('accepts valid email format', async () => {
      renderRegister();
      vi.mocked(api.auth.register).mockResolvedValueOnce({
        user: { id: 1, email: 'test@example.com', created_at: new Date().toISOString() },
        access_token: 'token123',
      });

      const emailInput = screen.getByPlaceholderText('you@example.com');
      await user.type(emailInput, 'test@example.com');
      await user.click(screen.getByRole('button', { name: 'Create Account' }));

      await waitFor(() => {
        expect(api.auth.register).toHaveBeenCalledWith({
          email: 'test@example.com',
          experience_level: 'Beginner',
          background: '',
          goals: '',
        });
      });
    });
  });

  describe('Form Input Handling', () => {
    it('updates email field on user input', async () => {
      renderRegister();

      const emailInput = screen.getByPlaceholderText('you@example.com') as HTMLInputElement;
      await user.type(emailInput, 'user@test.com');

      expect(emailInput.value).toBe('user@test.com');
    });

    it('updates experience level on selection', async () => {
      renderRegister();

      const selectElement = screen.getByDisplayValue('Beginner - New to AI') as HTMLSelectElement;
      await user.selectOptions(selectElement, 'Advanced');

      expect(selectElement.value).toBe('Advanced');
    });

    it('updates background field on user input', async () => {
      renderRegister();

      const backgroundInput = screen.getByPlaceholderText('Tell us about your professional background...') as HTMLTextAreaElement;
      await user.type(backgroundInput, 'Software developer with 5 years experience');

      expect(backgroundInput.value).toBe('Software developer with 5 years experience');
    });

    it('updates goals field on user input', async () => {
      renderRegister();

      const goalsInput = screen.getByPlaceholderText('What do you hope to achieve with AI?') as HTMLTextAreaElement;
      await user.type(goalsInput, 'Learn to build AI applications');

      expect(goalsInput.value).toBe('Learn to build AI applications');
    });

    it('handles very long text in background field', async () => {
      renderRegister();

      const longText = 'A'.repeat(1000);
      const backgroundInput = screen.getByPlaceholderText('Tell us about your professional background...') as HTMLTextAreaElement;
      await user.type(backgroundInput, longText);

      expect(backgroundInput.value).toBe(longText);
    });

    it('handles very long text in goals field', async () => {
      renderRegister();

      const longText = 'B'.repeat(1000);
      const goalsInput = screen.getByPlaceholderText('What do you hope to achieve with AI?') as HTMLTextAreaElement;
      await user.type(goalsInput, longText);

      expect(goalsInput.value).toBe(longText);
    });
  });

  describe('Successful Registration', () => {
    it('submits form with all fields filled', async () => {
      renderRegister();
      vi.mocked(api.auth.register).mockResolvedValueOnce({
        user: { id: 1, email: 'test@example.com', created_at: new Date().toISOString() },
        access_token: 'token123',
      });

      await user.type(screen.getByPlaceholderText('you@example.com'), 'test@example.com');
      await user.selectOptions(screen.getByDisplayValue('Beginner - New to AI'), 'Intermediate');
      await user.type(screen.getByPlaceholderText('Tell us about your professional background...'), 'Software Engineer');
      await user.type(screen.getByPlaceholderText('What do you hope to achieve with AI?'), 'Master AI development');

      await user.click(screen.getByRole('button', { name: 'Create Account' }));

      await waitFor(() => {
        expect(api.auth.register).toHaveBeenCalledWith({
          email: 'test@example.com',
          experience_level: 'Intermediate',
          background: 'Software Engineer',
          goals: 'Master AI development',
        });
      });
    });

    it('shows loading state during submission', async () => {
      renderRegister();
      let resolveRegister: (value: any) => void;
      const registerPromise = new Promise((resolve) => {
        resolveRegister = resolve;
      });
      vi.mocked(api.auth.register).mockReturnValueOnce(registerPromise as any);

      await user.type(screen.getByPlaceholderText('you@example.com'), 'test@example.com');
      await user.click(screen.getByRole('button', { name: 'Create Account' }));

      expect(screen.getByRole('button', { name: 'Creating Account...' })).toBeInTheDocument();
      expect(screen.getByRole('button')).toBeDisabled();

      resolveRegister!({
        user: { id: 1, email: 'test@example.com', created_at: new Date().toISOString() },
        access_token: 'token123',
      });
    });

    it('navigates to thank-you page on success', async () => {
      renderRegister();
      vi.mocked(api.auth.register).mockResolvedValueOnce({
        user: { id: 1, email: 'test@example.com', created_at: new Date().toISOString() },
        access_token: 'token123',
      });

      await user.type(screen.getByPlaceholderText('you@example.com'), 'test@example.com');
      await user.click(screen.getByRole('button', { name: 'Create Account' }));

      await waitFor(() => {
        expect(mockNavigate).toHaveBeenCalledWith('/thank-you');
      });
    });

    it('submits form with only required fields', async () => {
      renderRegister();
      vi.mocked(api.auth.register).mockResolvedValueOnce({
        user: { id: 1, email: 'minimal@example.com', created_at: new Date().toISOString() },
        access_token: 'token123',
      });

      await user.type(screen.getByPlaceholderText('you@example.com'), 'minimal@example.com');
      await user.click(screen.getByRole('button', { name: 'Create Account' }));

      await waitFor(() => {
        expect(api.auth.register).toHaveBeenCalledWith({
          email: 'minimal@example.com',
          experience_level: 'Beginner',
          background: '',
          goals: '',
        });
      });
    });
  });

  describe('Error Handling', () => {
    it('displays error message on registration failure', async () => {
      renderRegister();
      vi.mocked(api.auth.register).mockRejectedValueOnce(
        new Error('Email already registered')
      );

      await user.type(screen.getByPlaceholderText('you@example.com'), 'duplicate@example.com');
      await user.click(screen.getByRole('button', { name: 'Create Account' }));

      await waitFor(() => {
        expect(screen.getByText('Email already registered')).toBeInTheDocument();
      });
    });

    it('displays generic error message when error has no message', async () => {
      renderRegister();
      vi.mocked(api.auth.register).mockRejectedValueOnce(new Error());

      await user.type(screen.getByPlaceholderText('you@example.com'), 'test@example.com');
      await user.click(screen.getByRole('button', { name: 'Create Account' }));

      await waitFor(() => {
        expect(screen.getByText('Registration failed. Please try again.')).toBeInTheDocument();
      });
    });

    it('handles network errors gracefully', async () => {
      renderRegister();
      vi.mocked(api.auth.register).mockRejectedValueOnce(
        new Error('Network request failed')
      );

      await user.type(screen.getByPlaceholderText('you@example.com'), 'test@example.com');
      await user.click(screen.getByRole('button', { name: 'Create Account' }));

      await waitFor(() => {
        expect(screen.getByText('Network request failed')).toBeInTheDocument();
      });
    });

    it('clears previous error on new submission', async () => {
      renderRegister();
      vi.mocked(api.auth.register)
        .mockRejectedValueOnce(new Error('First error'))
        .mockResolvedValueOnce({
          user: { id: 1, email: 'test@example.com', created_at: new Date().toISOString() },
          access_token: 'token123',
        });

      await user.type(screen.getByPlaceholderText('you@example.com'), 'test@example.com');
      await user.click(screen.getByRole('button', { name: 'Create Account' }));

      await waitFor(() => {
        expect(screen.getByText('First error')).toBeInTheDocument();
      });

      await user.click(screen.getByRole('button', { name: 'Create Account' }));

      await waitFor(() => {
        expect(screen.queryByText('First error')).not.toBeInTheDocument();
      });
    });

    it('re-enables button after error', async () => {
      renderRegister();
      vi.mocked(api.auth.register).mockRejectedValueOnce(
        new Error('Registration failed')
      );

      await user.type(screen.getByPlaceholderText('you@example.com'), 'test@example.com');
      await user.click(screen.getByRole('button', { name: 'Create Account' }));

      await waitFor(() => {
        expect(screen.getByText('Registration failed')).toBeInTheDocument();
      });

      const submitButton = screen.getByRole('button', { name: 'Create Account' });
      expect(submitButton).not.toBeDisabled();
    });
  });

  describe('Experience Level Options', () => {
    it('displays all experience level options', () => {
      renderRegister();

      const selectElement = screen.getByDisplayValue('Beginner - New to AI');
      const options = Array.from(selectElement.querySelectorAll('option'));

      expect(options).toHaveLength(3);
      expect(options[0]).toHaveTextContent('Beginner - New to AI');
      expect(options[1]).toHaveTextContent('Intermediate - Some experience');
      expect(options[2]).toHaveTextContent('Advanced - Experienced with AI');
    });

    it('submits correct experience level value', async () => {
      renderRegister();
      vi.mocked(api.auth.register).mockResolvedValueOnce({
        user: { id: 1, email: 'test@example.com', created_at: new Date().toISOString() },
        access_token: 'token123',
      });

      await user.type(screen.getByPlaceholderText('you@example.com'), 'test@example.com');
      await user.selectOptions(screen.getByDisplayValue('Beginner - New to AI'), 'Advanced');
      await user.click(screen.getByRole('button', { name: 'Create Account' }));

      await waitFor(() => {
        expect(api.auth.register).toHaveBeenCalledWith(
          expect.objectContaining({
            experience_level: 'Advanced',
          })
        );
      });
    });
  });

  describe('Accessibility', () => {
    it('has proper labels for all form fields', () => {
      renderRegister();

      expect(screen.getByText('Email Address')).toBeInTheDocument();
      expect(screen.getByText('AI Experience Level')).toBeInTheDocument();
      expect(screen.getByText('Your Background (Optional)')).toBeInTheDocument();
      expect(screen.getByText('Learning Goals (Optional)')).toBeInTheDocument();
    });

    it('has proper input types', () => {
      renderRegister();

      const emailInput = screen.getByPlaceholderText('you@example.com');
      expect(emailInput).toHaveAttribute('type', 'email');
    });

    it('shows required attribute on email field', () => {
      renderRegister();

      const emailInput = screen.getByPlaceholderText('you@example.com');
      expect(emailInput).toBeRequired();
    });
  });
});
