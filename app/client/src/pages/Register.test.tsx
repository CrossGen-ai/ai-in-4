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

describe('Register Component - Extended Form', () => {
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

  // Helper to fill required fields for valid submission
  const fillRequiredFields = async () => {
    await user.type(screen.getByPlaceholderText('Your full name'), 'John Doe');
    await user.type(screen.getByPlaceholderText('you@example.com'), 'test@example.com');
    await user.selectOptions(screen.getByLabelText(/Employment Status/), 'Student');
    await user.click(screen.getByLabelText('Educational purposes'));
    await user.click(screen.getByLabelText('Yes'));
    await user.selectOptions(screen.getByLabelText(/How often do you currently use AI tools?/), 'Weekly');
    await user.click(screen.getByLabelText(/3 - Somewhat comfortable/));

    // Select exactly 3 goals
    const goalCheckboxes = screen.getAllByRole('checkbox');
    const goalsOptions = goalCheckboxes.filter(cb =>
      ['Writing/content creation', 'Research and information gathering', 'Coding/technical tasks']
        .some(goal => cb.closest('label')?.textContent?.includes(goal))
    );
    for (const checkbox of goalsOptions.slice(0, 3)) {
      await user.click(checkbox);
    }

    await user.click(screen.getByLabelText('Hands-on practice with examples'));
  };

  describe('Initial Render', () => {
    it('renders all section headings', () => {
      renderRegister();

      expect(screen.getByText('Basic Info')).toBeInTheDocument();
      expect(screen.getByText('Primary Use Context')).toBeInTheDocument();
      expect(screen.getByText('Current AI Experience')).toBeInTheDocument();
      expect(screen.getByText('Usage & Comfort Level')).toBeInTheDocument();
      expect(screen.getByText('Goals & Applications')).toBeInTheDocument();
      expect(screen.getByText('Biggest Challenge')).toBeInTheDocument();
      expect(screen.getByText('Learning Preference')).toBeInTheDocument();
      expect(screen.getByText('Additional Comments')).toBeInTheDocument();
    });

    it('renders all required field markers', () => {
      renderRegister();

      const requiredMarkers = screen.getAllByText('*');
      expect(requiredMarkers.length).toBeGreaterThan(5); // Multiple required fields
    });
  });

  describe('Basic Info Section', () => {
    it('renders name field with character counter', async () => {
      renderRegister();

      const nameInput = screen.getByPlaceholderText('Your full name');
      expect(nameInput).toBeRequired();
      expect(screen.getByText('0/100')).toBeInTheDocument();

      await user.type(nameInput, 'John Doe');
      expect(screen.getByText('8/100')).toBeInTheDocument();
    });

    it('renders employment status dropdown with all options', () => {
      renderRegister();

      const select = screen.getByLabelText(/Employment Status/);
      expect(select).toBeRequired();

      const options = Array.from(select.querySelectorAll('option'));
      expect(options.some(opt => opt.textContent?.includes('Employed full-time'))).toBe(true);
      expect(options.some(opt => opt.textContent?.includes('Student'))).toBe(true);
      expect(options.some(opt => opt.textContent?.includes('Other'))).toBe(true);
    });

    it('shows conditional "Other" field when employment status is Other', async () => {
      renderRegister();

      expect(screen.queryByPlaceholderText('Your employment status')).not.toBeInTheDocument();

      await user.selectOptions(screen.getByLabelText(/Employment Status/), 'Other');

      expect(screen.getByPlaceholderText('Your employment status')).toBeInTheDocument();
      expect(screen.getByPlaceholderText('Your employment status')).toBeRequired();
    });

    it('hides conditional "Other" field when changing from Other', async () => {
      renderRegister();

      await user.selectOptions(screen.getByLabelText(/Employment Status/), 'Other');
      expect(screen.getByPlaceholderText('Your employment status')).toBeInTheDocument();

      await user.selectOptions(screen.getByLabelText(/Employment Status/), 'Student');
      expect(screen.queryByPlaceholderText('Your employment status')).not.toBeInTheDocument();
    });
  });

  describe('Primary Use Context Section', () => {
    it('renders all primary use context radio options', () => {
      renderRegister();

      expect(screen.getByLabelText('Work/Professional tasks')).toBeInTheDocument();
      expect(screen.getByLabelText('Home/Personal use')).toBeInTheDocument();
      expect(screen.getByLabelText('Both equally')).toBeInTheDocument();
      expect(screen.getByLabelText('Educational purposes')).toBeInTheDocument();
      expect(screen.getByLabelText('Side business/Hobby projects')).toBeInTheDocument();
    });

    it('allows selecting one primary use context', async () => {
      renderRegister();

      const workOption = screen.getByLabelText('Work/Professional tasks');
      const homeOption = screen.getByLabelText('Home/Personal use');

      await user.click(workOption);
      expect(workOption).toBeChecked();
      expect(homeOption).not.toBeChecked();

      await user.click(homeOption);
      expect(workOption).not.toBeChecked();
      expect(homeOption).toBeChecked();
    });
  });

  describe('AI Experience Section', () => {
    it('renders tried AI before Yes/No options', () => {
      renderRegister();

      expect(screen.getByLabelText('Yes')).toBeInTheDocument();
      expect(screen.getByLabelText('No')).toBeInTheDocument();
    });

    it('shows AI tools checkboxes when Yes is selected', async () => {
      renderRegister();

      expect(screen.queryByText('Which AI tools have you used?')).not.toBeInTheDocument();

      await user.click(screen.getByLabelText('Yes'));

      expect(screen.getByText('Which AI tools have you used? (Select all that apply)')).toBeInTheDocument();
      expect(screen.getByLabelText('ChatGPT')).toBeInTheDocument();
      expect(screen.getByLabelText('Claude')).toBeInTheDocument();
      expect(screen.getByLabelText('Gemini')).toBeInTheDocument();
    });

    it('hides AI tools checkboxes when No is selected', async () => {
      renderRegister();

      await user.click(screen.getByLabelText('Yes'));
      expect(screen.getByText('Which AI tools have you used? (Select all that apply)')).toBeInTheDocument();

      await user.click(screen.getByLabelText('No'));
      expect(screen.queryByText('Which AI tools have you used?')).not.toBeInTheDocument();
    });

    it('shows Other text field when AI tools Other is checked', async () => {
      renderRegister();

      await user.click(screen.getByLabelText('Yes'));

      const otherCheckbox = screen.getAllByRole('checkbox').find(cb =>
        cb.closest('label')?.textContent?.includes('Other') &&
        !cb.closest('label')?.textContent?.includes('Goals')
      );

      await user.click(otherCheckbox!);
      expect(screen.getByPlaceholderText('Please specify other AI tools')).toBeInTheDocument();
    });
  });

  describe('Usage & Comfort Level Section', () => {
    it('renders usage frequency dropdown with all options', () => {
      renderRegister();

      const select = screen.getByLabelText(/How often do you currently use AI tools?/);
      expect(select).toBeRequired();

      const options = Array.from(select.querySelectorAll('option'));
      expect(options.some(opt => opt.textContent?.includes('Never'))).toBe(true);
      expect(options.some(opt => opt.textContent?.includes('Daily'))).toBe(true);
      expect(options.some(opt => opt.textContent?.includes('Multiple times per day'))).toBe(true);
    });

    it('renders all 5 comfort level options', () => {
      renderRegister();

      expect(screen.getByLabelText(/1 - Complete beginner/)).toBeInTheDocument();
      expect(screen.getByLabelText(/2 - Slightly familiar/)).toBeInTheDocument();
      expect(screen.getByLabelText(/3 - Somewhat comfortable/)).toBeInTheDocument();
      expect(screen.getByLabelText(/4 - Confident/)).toBeInTheDocument();
      expect(screen.getByLabelText(/5 - Very confident/)).toBeInTheDocument();
    });

    it('allows selecting one comfort level', async () => {
      renderRegister();

      const level3 = screen.getByLabelText(/3 - Somewhat comfortable/);
      const level5 = screen.getByLabelText(/5 - Very confident/);

      await user.click(level3);
      expect(level3).toBeChecked();

      await user.click(level5);
      expect(level5).toBeChecked();
      expect(level3).not.toBeChecked();
    });
  });

  describe('Goals Section', () => {
    it('displays goals counter (0/3 initially)', () => {
      renderRegister();

      expect(screen.getByText(/0\/3 selected/)).toBeInTheDocument();
    });

    it('updates counter when goals are selected', async () => {
      renderRegister();

      const goalCheckboxes = screen.getAllByRole('checkbox');
      const firstGoal = goalCheckboxes.find(cb =>
        cb.closest('label')?.textContent?.includes('Writing/content creation')
      );

      await user.click(firstGoal!);
      expect(screen.getByText(/1\/3 selected/)).toBeInTheDocument();
    });

    it('disables additional checkboxes when 3 goals are selected', async () => {
      renderRegister();

      const goalCheckboxes = screen.getAllByRole('checkbox');
      const goalsInSection = goalCheckboxes.filter(cb => {
        const label = cb.closest('label')?.textContent || '';
        return ['Writing/content creation', 'Research and information gathering',
                'Coding/technical tasks', 'Data analysis'].some(goal => label.includes(goal));
      });

      // Select 3 goals
      await user.click(goalsInSection[0]);
      await user.click(goalsInSection[1]);
      await user.click(goalsInSection[2]);

      expect(screen.getByText(/3\/3 selected/)).toBeInTheDocument();

      // 4th checkbox should be disabled
      expect(goalsInSection[3]).toBeDisabled();
    });

    it('allows deselecting to select different goals', async () => {
      renderRegister();

      const goalCheckboxes = screen.getAllByRole('checkbox');
      const goalsInSection = goalCheckboxes.filter(cb => {
        const label = cb.closest('label')?.textContent || '';
        return ['Writing/content creation', 'Research and information gathering',
                'Coding/technical tasks', 'Data analysis'].some(goal => label.includes(goal));
      });

      // Select 3 goals
      await user.click(goalsInSection[0]);
      await user.click(goalsInSection[1]);
      await user.click(goalsInSection[2]);

      // Deselect one
      await user.click(goalsInSection[0]);
      expect(screen.getByText(/2\/3 selected/)).toBeInTheDocument();

      // Select a different one
      await user.click(goalsInSection[3]);
      expect(screen.getByText(/3\/3 selected/)).toBeInTheDocument();
    });

    it('shows error when trying to submit with less than 3 goals', async () => {
      renderRegister();

      await user.type(screen.getByPlaceholderText('Your full name'), 'John Doe');
      await user.type(screen.getByPlaceholderText('you@example.com'), 'test@example.com');
      await user.selectOptions(screen.getByLabelText(/Employment Status/), 'Student');
      await user.click(screen.getByLabelText('Educational purposes'));
      await user.click(screen.getByLabelText('Yes'));
      await user.selectOptions(screen.getByLabelText(/How often do you currently use AI tools?/), 'Weekly');
      await user.click(screen.getByLabelText(/3 - Somewhat comfortable/));
      await user.click(screen.getByLabelText('Hands-on practice with examples'));

      // Select only 2 goals
      const goalCheckboxes = screen.getAllByRole('checkbox');
      const goalsInSection = goalCheckboxes.filter(cb =>
        cb.closest('label')?.textContent?.includes('Writing/content creation') ||
        cb.closest('label')?.textContent?.includes('Research and information gathering')
      );
      await user.click(goalsInSection[0]);
      await user.click(goalsInSection[1]);

      await user.click(screen.getByRole('button', { name: 'Create Account' }));

      await waitFor(() => {
        expect(screen.getByText('Please select exactly 3 goals.')).toBeInTheDocument();
      });
    });
  });

  describe('Challenges Section', () => {
    it('allows selecting multiple challenges without limit', async () => {
      renderRegister();

      const challengeCheckboxes = screen.getAllByRole('checkbox');
      const challengesInSection = challengeCheckboxes.filter(cb => {
        const label = cb.closest('label')?.textContent || '';
        return ["Don't know where to start", "Understanding what AI can/can't do",
                'Writing effective prompts', 'Knowing which tool to use when'].some(ch => label.includes(ch));
      });

      // Select 4 challenges - all should work
      for (const checkbox of challengesInSection) {
        await user.click(checkbox);
        expect(checkbox).toBeChecked();
        expect(checkbox).not.toBeDisabled();
      }
    });
  });

  describe('Learning Preference Section', () => {
    it('renders all learning preference options', () => {
      renderRegister();

      expect(screen.getByLabelText('Step-by-step tutorials')).toBeInTheDocument();
      expect(screen.getByLabelText('Watching video demonstrations')).toBeInTheDocument();
      expect(screen.getByLabelText('Hands-on practice with examples')).toBeInTheDocument();
      expect(screen.getByLabelText('Reading documentation')).toBeInTheDocument();
      expect(screen.getByLabelText('Mix of all above')).toBeInTheDocument();
    });
  });

  describe('Additional Comments Section', () => {
    it('renders textarea with character counter', async () => {
      renderRegister();

      const textarea = screen.getByPlaceholderText('Share any additional thoughts or questions...');
      expect(screen.getByText('0/500')).toBeInTheDocument();

      await user.type(textarea, 'I am excited to learn AI!');
      expect(screen.getByText('26/500')).toBeInTheDocument();
    });

    it('enforces 500 character limit', () => {
      renderRegister();

      const textarea = screen.getByPlaceholderText('Share any additional thoughts or questions...') as HTMLTextAreaElement;
      expect(textarea.maxLength).toBe(500);
    });
  });

  describe('Form Submission', () => {
    it('submits form with all required fields', async () => {
      renderRegister();
      vi.mocked(api.auth.register).mockResolvedValueOnce({
        user: { id: 1, email: 'test@example.com', created_at: new Date().toISOString() },
        access_token: 'token123',
      });

      await fillRequiredFields();
      await user.click(screen.getByRole('button', { name: 'Create Account' }));

      await waitFor(() => {
        expect(api.auth.register).toHaveBeenCalled();
        const callArg = vi.mocked(api.auth.register).mock.calls[0][0];
        expect(callArg.name).toBe('John Doe');
        expect(callArg.email).toBe('test@example.com');
        expect(callArg.employment_status).toBe('Student');
        expect(callArg.primary_use_context).toBe('Educational purposes');
        expect(callArg.tried_ai_before).toBe(true);
        expect(callArg.usage_frequency).toBe('Weekly');
        expect(callArg.comfort_level).toBe(3);
        expect(callArg.goals).toHaveLength(3);
        expect(callArg.learning_preference).toBe('Hands-on practice with examples');
      });
    });

    it('submits form with all fields including optional', async () => {
      renderRegister();
      vi.mocked(api.auth.register).mockResolvedValueOnce({
        user: { id: 1, email: 'test@example.com', created_at: new Date().toISOString() },
        access_token: 'token123',
      });

      await fillRequiredFields();

      // Fill optional fields
      await user.type(screen.getByPlaceholderText('e.g., Technology, Healthcare, Education'), 'Technology');
      await user.type(screen.getByPlaceholderText('e.g., Software Engineer, Teacher, Manager'), 'Developer');
      await user.type(screen.getByPlaceholderText('Share any additional thoughts or questions...'), 'Looking forward to learning!');

      await user.click(screen.getByRole('button', { name: 'Create Account' }));

      await waitFor(() => {
        expect(api.auth.register).toHaveBeenCalled();
        const callArg = vi.mocked(api.auth.register).mock.calls[0][0];
        expect(callArg.industry).toBe('Technology');
        expect(callArg.role).toBe('Developer');
        expect(callArg.additional_comments).toBe('Looking forward to learning!');
      });
    });

    it('navigates to thank-you page on successful submission', async () => {
      renderRegister();
      vi.mocked(api.auth.register).mockResolvedValueOnce({
        user: { id: 1, email: 'test@example.com', created_at: new Date().toISOString() },
        access_token: 'token123',
      });

      await fillRequiredFields();
      await user.click(screen.getByRole('button', { name: 'Create Account' }));

      await waitFor(() => {
        expect(mockNavigate).toHaveBeenCalledWith('/thank-you');
      });
    });

    it('shows loading state during submission', async () => {
      renderRegister();
      let resolveRegister: (value: any) => void;
      const registerPromise = new Promise((resolve) => {
        resolveRegister = resolve;
      });
      vi.mocked(api.auth.register).mockReturnValueOnce(registerPromise as any);

      await fillRequiredFields();
      await user.click(screen.getByRole('button', { name: 'Create Account' }));

      expect(screen.getByRole('button', { name: 'Creating Account...' })).toBeInTheDocument();
      expect(screen.getByRole('button', { name: 'Creating Account...' })).toBeDisabled();

      resolveRegister!({
        user: { id: 1, email: 'test@example.com', created_at: new Date().toISOString() },
        access_token: 'token123',
      });
    });

    it('displays error message on registration failure', async () => {
      renderRegister();
      vi.mocked(api.auth.register).mockRejectedValueOnce(
        new Error('Email already registered')
      );

      await fillRequiredFields();
      await user.click(screen.getByRole('button', { name: 'Create Account' }));

      await waitFor(() => {
        expect(screen.getByText('Email already registered')).toBeInTheDocument();
      });
    });
  });

  describe('Character Limits', () => {
    it('enforces name 100 character limit', () => {
      renderRegister();
      const input = screen.getByPlaceholderText('Your full name') as HTMLInputElement;
      expect(input.maxLength).toBe(100);
    });

    it('enforces email 150 character limit', () => {
      renderRegister();
      const input = screen.getByPlaceholderText('you@example.com') as HTMLInputElement;
      expect(input.maxLength).toBe(150);
    });

    it('enforces industry 100 character limit', () => {
      renderRegister();
      const input = screen.getByPlaceholderText('e.g., Technology, Healthcare, Education') as HTMLInputElement;
      expect(input.maxLength).toBe(100);
    });

    it('enforces role 100 character limit', () => {
      renderRegister();
      const input = screen.getByPlaceholderText('e.g., Software Engineer, Teacher, Manager') as HTMLInputElement;
      expect(input.maxLength).toBe(100);
    });

    it('enforces additional comments 500 character limit', () => {
      renderRegister();
      const textarea = screen.getByPlaceholderText('Share any additional thoughts or questions...') as HTMLTextAreaElement;
      expect(textarea.maxLength).toBe(500);
    });
  });
});
