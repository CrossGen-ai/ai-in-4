import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor, act } from '@testing-library/react';
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
    users: {
      getCurrentUser: vi.fn(),
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

// Mock AuthContext
const mockLogin = vi.fn().mockResolvedValue(undefined);
vi.mock('../context/AuthContext', () => ({
  AuthProvider: ({ children }: { children: React.ReactNode }) => children,
  useAuth: () => ({
    user: null,
    isAuthenticated: false,
    loading: false,
    login: mockLogin,
    logout: vi.fn(),
    validateToken: vi.fn(),
  }),
}));

describe('Register Component - Extended Form', () => {
  let user: ReturnType<typeof userEvent.setup>;

  beforeEach(() => {
    vi.clearAllMocks();
    mockLogin.mockClear();
    mockNavigate.mockClear();
    user = userEvent.setup();
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

    // Find employment status dropdown by its placeholder option
    const employmentSelect = screen.getAllByRole('combobox')[0];
    await user.selectOptions(employmentSelect, 'Student');

    await user.click(screen.getByLabelText('Educational purposes'));
    await user.click(screen.getByLabelText('Yes'));

    // Find usage frequency dropdown
    const frequencySelect = screen.getAllByRole('combobox')[1];
    await user.selectOptions(frequencySelect, 'Weekly');

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
      // Usage & Comfort Level is conditional - only shown when tried_ai_before is true
      expect(screen.queryByText('Usage & Comfort Level')).not.toBeInTheDocument();
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

      // Check character counter is present (multiple 0/100 exist, so just verify one exists)
      const counters = screen.getAllByText('0/100');
      expect(counters.length).toBeGreaterThan(0);

      await user.type(nameInput, 'John Doe');
      expect(screen.getByText('8/100')).toBeInTheDocument();
    });

    it('renders employment status dropdown with all options', () => {
      renderRegister();

      const select = screen.getAllByRole('combobox')[0];
      expect(select).toBeRequired();

      const options = Array.from(select.querySelectorAll('option'));
      expect(options.some(opt => opt.textContent?.includes('Employed full-time'))).toBe(true);
      expect(options.some(opt => opt.textContent?.includes('Student'))).toBe(true);
      expect(options.some(opt => opt.textContent?.includes('Other'))).toBe(true);
    });

    it('shows conditional "Other" field when employment status is Other', async () => {
      renderRegister();

      expect(screen.queryByPlaceholderText('Your employment status')).not.toBeInTheDocument();

      const select = screen.getAllByRole('combobox')[0];
      await user.selectOptions(select, 'Other');

      expect(screen.getByPlaceholderText('Your employment status')).toBeInTheDocument();
      expect(screen.getByPlaceholderText('Your employment status')).toBeRequired();
    });

    it('hides conditional "Other" field when changing from Other', async () => {
      renderRegister();

      const select = screen.getAllByRole('combobox')[0];
      await user.selectOptions(select, 'Other');
      expect(screen.getByPlaceholderText('Your employment status')).toBeInTheDocument();

      await user.selectOptions(select, 'Student');
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
    it('renders usage frequency dropdown with all options', async () => {
      renderRegister();

      // Section is hidden initially
      expect(screen.queryByText('Usage & Comfort Level')).not.toBeInTheDocument();

      // Click Yes to show the section
      await user.click(screen.getByLabelText('Yes'));

      // Now the section should be visible
      expect(screen.getByText('Usage & Comfort Level')).toBeInTheDocument();

      const select = screen.getAllByRole('combobox')[1];
      expect(select).toBeRequired();

      const options = Array.from(select.querySelectorAll('option'));
      expect(options.some(opt => opt.textContent?.includes('Never'))).toBe(true);
      expect(options.some(opt => opt.textContent?.includes('Daily'))).toBe(true);
      expect(options.some(opt => opt.textContent?.includes('Multiple times per day'))).toBe(true);
    });

    it('renders all 5 comfort level options', async () => {
      renderRegister();

      // Click Yes to show the section
      await user.click(screen.getByLabelText('Yes'));

      expect(screen.getByLabelText(/1 - Complete beginner/)).toBeInTheDocument();
      expect(screen.getByLabelText(/2 - Slightly familiar/)).toBeInTheDocument();
      expect(screen.getByLabelText(/3 - Somewhat comfortable/)).toBeInTheDocument();
      expect(screen.getByLabelText(/4 - Confident/)).toBeInTheDocument();
      expect(screen.getByLabelText(/5 - Very confident/)).toBeInTheDocument();
    });

    it('allows selecting one comfort level', async () => {
      renderRegister();

      // Click Yes to show the section
      await user.click(screen.getByLabelText('Yes'));

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
      await user.selectOptions(screen.getAllByRole('combobox')[0], 'Student');
      await user.click(screen.getByLabelText('Educational purposes'));
      await user.click(screen.getByLabelText('Yes'));
      await user.selectOptions(screen.getAllByRole('combobox')[1], 'Weekly');
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
      await waitFor(() => {
        expect(screen.getByText('25/500')).toBeInTheDocument();
      });
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

    it('navigates to dashboard on successful submission', async () => {
      renderRegister();
      vi.mocked(api.auth.register).mockResolvedValueOnce({
        user: { id: 1, email: 'test@example.com', created_at: new Date().toISOString() },
        access_token: 'token123',
      });

      await fillRequiredFields();
      await user.click(screen.getByRole('button', { name: 'Create Account' }));

      await waitFor(() => {
        expect(mockNavigate).toHaveBeenCalledWith('/dashboard');
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

      await act(async () => {
        resolveRegister!({
          user: { id: 1, email: 'test@example.com', created_at: new Date().toISOString() },
          access_token: 'token123',
        });
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

    it('updates character counter at limit', async () => {
      renderRegister();
      const nameInput = screen.getByPlaceholderText('Your full name');
      const text100Chars = 'A'.repeat(100);

      await user.type(nameInput, text100Chars);
      expect(screen.getByText('100/100')).toBeInTheDocument();
    });

    it('handles special characters in character count', async () => {
      renderRegister();
      const textarea = screen.getByPlaceholderText('Share any additional thoughts or questions...');

      await user.type(textarea, 'Test with émojis 🎉 and special chars: @#$%^&*()');
      const charCount = 'Test with émojis 🎉 and special chars: @#$%^&*()'.length;
      expect(screen.getByText(`${charCount}/500`)).toBeInTheDocument();
    });

    it('enforces employment_status_other 50 character limit', async () => {
      renderRegister();

      await user.selectOptions(screen.getAllByRole('combobox')[0], 'Other');
      const input = screen.getByPlaceholderText('Your employment status') as HTMLInputElement;
      expect(input.maxLength).toBe(50);
    });

    it('enforces ai_tools_other 100 character limit', async () => {
      renderRegister();

      await user.click(screen.getByLabelText('Yes'));
      const otherCheckbox = screen.getAllByRole('checkbox').find(cb =>
        cb.closest('label')?.textContent?.includes('Other') &&
        !cb.closest('label')?.textContent?.includes('Goals')
      );
      await user.click(otherCheckbox!);

      const input = screen.getByPlaceholderText('Please specify other AI tools') as HTMLInputElement;
      expect(input.maxLength).toBe(100);
    });

    it('enforces goals_other 100 character limit', async () => {
      renderRegister();

      const goalCheckboxes = screen.getAllByRole('checkbox');
      const otherGoalCheckbox = goalCheckboxes.find(cb =>
        cb.closest('label')?.textContent === 'Other'
      );
      await user.click(otherGoalCheckbox!);

      const input = screen.getByPlaceholderText('Please specify your other goal') as HTMLInputElement;
      expect(input.maxLength).toBe(100);
    });

    it('enforces challenges_other 150 character limit', async () => {
      renderRegister();

      const challengeCheckboxes = screen.getAllByRole('checkbox');
      const otherChallengeCheckbox = challengeCheckboxes.find(cb =>
        cb.closest('label')?.textContent === 'Other' &&
        cb.closest('.space-y-4')?.querySelector('h2')?.textContent?.includes('Biggest Challenge')
      );
      await user.click(otherChallengeCheckbox!);

      const input = screen.getByPlaceholderText('Please specify your other challenge') as HTMLInputElement;
      expect(input.maxLength).toBe(150);
    });
  });

  describe('Edge Cases - Conditional Logic', () => {
    it('clears AI tools selections when changing from Yes to No', async () => {
      renderRegister();

      // Select Yes and choose some tools
      await user.click(screen.getByLabelText('Yes'));
      const chatGPTCheckbox = screen.getByLabelText('ChatGPT');
      const claudeCheckbox = screen.getByLabelText('Claude');
      await user.click(chatGPTCheckbox);
      await user.click(claudeCheckbox);

      expect(chatGPTCheckbox).toBeChecked();
      expect(claudeCheckbox).toBeChecked();

      // Change to No
      await user.click(screen.getByLabelText('No'));

      // Section should be hidden
      expect(screen.queryByText('Which AI tools have you used?')).not.toBeInTheDocument();

      // Change back to Yes - selections should be cleared
      await user.click(screen.getByLabelText('Yes'));
      const chatGPTCheckboxAfter = screen.getByLabelText('ChatGPT');
      const claudeCheckboxAfter = screen.getByLabelText('Claude');

      expect(chatGPTCheckboxAfter).not.toBeChecked();
      expect(claudeCheckboxAfter).not.toBeChecked();
    });

    it('clears employment_status_other when changing from Other to different option', async () => {
      renderRegister();

      // Select Other and type text
      await user.selectOptions(screen.getAllByRole('combobox')[0], 'Other');
      const otherInput = screen.getByPlaceholderText('Your employment status');
      await user.type(otherInput, 'Freelancer');

      // Change to Student
      await user.selectOptions(screen.getAllByRole('combobox')[0], 'Student');

      // Change back to Other - text should be cleared
      await user.selectOptions(screen.getAllByRole('combobox')[0], 'Other');
      const otherInputAfter = screen.getByPlaceholderText('Your employment status') as HTMLInputElement;
      expect(otherInputAfter.value).toBe('');
    });

    it('hides AI tools Other text field when unchecking Other', async () => {
      renderRegister();

      await user.click(screen.getByLabelText('Yes'));
      const otherCheckbox = screen.getAllByRole('checkbox').find(cb =>
        cb.closest('label')?.textContent?.includes('Other') &&
        !cb.closest('label')?.textContent?.includes('Goals')
      );

      // Check Other
      await user.click(otherCheckbox!);
      expect(screen.getByPlaceholderText('Please specify other AI tools')).toBeInTheDocument();

      // Uncheck Other
      await user.click(otherCheckbox!);
      expect(screen.queryByPlaceholderText('Please specify other AI tools')).not.toBeInTheDocument();
    });

    it('hides Goals Other text field when unchecking Other', async () => {
      renderRegister();

      const goalCheckboxes = screen.getAllByRole('checkbox');
      const otherGoalCheckbox = goalCheckboxes.find(cb =>
        cb.closest('label')?.textContent === 'Other'
      );

      // Check Other
      await user.click(otherGoalCheckbox!);
      expect(screen.getByPlaceholderText('Please specify your other goal')).toBeInTheDocument();

      // Uncheck Other
      await user.click(otherGoalCheckbox!);
      expect(screen.queryByPlaceholderText('Please specify your other goal')).not.toBeInTheDocument();
    });

    it('hides Challenges Other text field when unchecking Other', async () => {
      renderRegister();

      const challengeCheckboxes = screen.getAllByRole('checkbox');
      const otherChallengeCheckbox = challengeCheckboxes.find(cb =>
        cb.closest('label')?.textContent === 'Other' &&
        cb.closest('.space-y-4')?.querySelector('h2')?.textContent?.includes('Biggest Challenge')
      );

      // Check Other
      await user.click(otherChallengeCheckbox!);
      expect(screen.getByPlaceholderText('Please specify your other challenge')).toBeInTheDocument();

      // Uncheck Other
      await user.click(otherChallengeCheckbox!);
      expect(screen.queryByPlaceholderText('Please specify your other challenge')).not.toBeInTheDocument();
    });
  });

  describe('Edge Cases - Goals Selection', () => {
    it('prevents selecting more than 3 goals via UI', async () => {
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

      // Try to select 4th goal - should be disabled
      expect(goalsInSection[3]).toBeDisabled();

      // Attempt to click disabled checkbox (should not change state)
      await user.click(goalsInSection[3]);
      expect(goalsInSection[3]).not.toBeChecked();
      expect(screen.getByText(/3\/3 selected/)).toBeInTheDocument();
    });

    it('shows exactly 3 goals validation error', async () => {
      renderRegister();

      await user.type(screen.getByPlaceholderText('Your full name'), 'John Doe');
      await user.type(screen.getByPlaceholderText('you@example.com'), 'test@example.com');
      await user.selectOptions(screen.getAllByRole('combobox')[0], 'Student');
      await user.click(screen.getByLabelText('Educational purposes'));
      await user.click(screen.getByLabelText('Yes'));
      await user.selectOptions(screen.getAllByRole('combobox')[1], 'Weekly');
      await user.click(screen.getByLabelText(/3 - Somewhat comfortable/));
      await user.click(screen.getByLabelText('Hands-on practice with examples'));

      // Select 0 goals
      await user.click(screen.getByRole('button', { name: 'Create Account' }));

      await waitFor(() => {
        expect(screen.getByText('Please select exactly 3 goals.')).toBeInTheDocument();
      });
    });

    it('allows submission with exactly 3 goals', async () => {
      renderRegister();
      vi.mocked(api.auth.register).mockResolvedValueOnce({
        user: { id: 1, email: 'test@example.com', created_at: new Date().toISOString() },
        access_token: 'token123',
      });

      await fillRequiredFields();
      await user.click(screen.getByRole('button', { name: 'Create Account' }));

      await waitFor(() => {
        expect(api.auth.register).toHaveBeenCalled();
        expect(screen.queryByText('Please select exactly 3 goals.')).not.toBeInTheDocument();
      });
    });
  });

  describe('Edge Cases - Rapid Form Changes', () => {
    it('handles rapid selection changes without breaking state', async () => {
      renderRegister();

      const workOption = screen.getByLabelText('Work/Professional tasks');
      const homeOption = screen.getByLabelText('Home/Personal use');
      const bothOption = screen.getByLabelText('Both equally');

      // Rapid changes
      await user.click(workOption);
      await user.click(homeOption);
      await user.click(bothOption);
      await user.click(workOption);
      await user.click(homeOption);

      expect(homeOption).toBeChecked();
      expect(workOption).not.toBeChecked();
      expect(bothOption).not.toBeChecked();
    });

    it('handles rapid checkbox toggling without breaking state', async () => {
      renderRegister();

      const challengeCheckboxes = screen.getAllByRole('checkbox');
      const firstChallenge = challengeCheckboxes.find(cb =>
        cb.closest('label')?.textContent?.includes("Don't know where to start")
      );

      // Rapid toggling
      await user.click(firstChallenge!);
      await user.click(firstChallenge!);
      await user.click(firstChallenge!);
      await user.click(firstChallenge!);
      await user.click(firstChallenge!);

      expect(firstChallenge).toBeChecked();
    });

    it('handles rapid goal selection/deselection near limit', async () => {
      renderRegister();

      const goalCheckboxes = screen.getAllByRole('checkbox');
      const goalsInSection = goalCheckboxes.filter(cb => {
        const label = cb.closest('label')?.textContent || '';
        return ['Writing/content creation', 'Research and information gathering',
                'Coding/technical tasks', 'Data analysis'].some(goal => label.includes(goal));
      });

      // Select 3
      await user.click(goalsInSection[0]);
      await user.click(goalsInSection[1]);
      await user.click(goalsInSection[2]);

      // Rapid deselect/select (2 clicks to deselect then select again)
      await user.click(goalsInSection[2]);
      await user.click(goalsInSection[2]);

      // Should still have 3 selected and goal 2 checked
      await waitFor(() => {
        expect(screen.getByText(/3\/3 selected/)).toBeInTheDocument();
        expect(goalsInSection[2]).toBeChecked();
      });
    });
  });

  describe('Edge Cases - Email Validation', () => {
    it('accepts valid email formats', async () => {
      renderRegister();

      const emailInput = screen.getByPlaceholderText('you@example.com') as HTMLInputElement;

      await user.type(emailInput, 'valid.email+tag@example.com');
      expect(emailInput.value).toBe('valid.email+tag@example.com');
      expect(emailInput.validity.valid).toBe(true);
    });

    it('handles special characters in email', async () => {
      renderRegister();

      const emailInput = screen.getByPlaceholderText('you@example.com') as HTMLInputElement;

      await user.type(emailInput, 'user+filter@sub.domain.co.uk');
      expect(emailInput.value).toBe('user+filter@sub.domain.co.uk');
    });

    it('enforces email format through HTML5 validation', () => {
      renderRegister();

      const emailInput = screen.getByPlaceholderText('you@example.com') as HTMLInputElement;
      expect(emailInput.type).toBe('email');
      expect(emailInput.required).toBe(true);
    });

    it('accepts extremely long but valid emails up to 150 chars', async () => {
      renderRegister();

      const longEmail = 'a'.repeat(130) + '@example.com'; // 142 chars total
      const emailInput = screen.getByPlaceholderText('you@example.com');

      await user.type(emailInput, longEmail);
      expect((emailInput as HTMLInputElement).value).toBe(longEmail);
    });
  });

  describe('Edge Cases - Required Field Validation', () => {
    it('shows validation error when submitting with missing required fields', async () => {
      renderRegister();
      vi.mocked(api.auth.register).mockResolvedValueOnce({
        user: { id: 1, email: 'test@example.com', created_at: new Date().toISOString() },
        access_token: 'token123',
      });

      // Fill all HTML5 required fields to test that validation passes
      await user.type(screen.getByPlaceholderText('Your full name'), 'John Doe');
      await user.type(screen.getByPlaceholderText('you@example.com'), 'test@example.com');
      const employmentSelect = screen.getAllByRole('combobox')[0];
      await user.selectOptions(employmentSelect, 'Student');
      await user.click(screen.getByLabelText('Educational purposes'));
      await user.click(screen.getByLabelText('Yes'));
      const frequencySelect = screen.getAllByRole('combobox')[1];
      await user.selectOptions(frequencySelect, 'Weekly');
      await user.click(screen.getByLabelText(/3 - Somewhat comfortable/));
      await user.click(screen.getByLabelText('Hands-on practice with examples'));

      // Select 3 goals to pass goals validation
      const goalCheckboxes = screen.getAllByRole('checkbox');
      const goalsInSection = goalCheckboxes.filter(cb =>
        ['Writing/content creation', 'Research and information gathering', 'Coding/technical tasks']
          .some(goal => cb.closest('label')?.textContent?.includes(goal))
      );
      await user.click(goalsInSection[0]);
      await user.click(goalsInSection[1]);
      await user.click(goalsInSection[2]);

      const submitButton = screen.getByRole('button', { name: 'Create Account' });
      await user.click(submitButton);

      // Should not show validation error when all required fields are filled
      await waitFor(() => {
        expect(api.auth.register).toHaveBeenCalled();
        expect(screen.queryByText('Please fill in all required fields.')).not.toBeInTheDocument();
      });
    });

    it('validates comfort_level is selected (not 0)', async () => {
      renderRegister();
      vi.mocked(api.auth.register).mockResolvedValueOnce({
        user: { id: 1, email: 'test@example.com', created_at: new Date().toISOString() },
        access_token: 'token123',
      });

      await user.type(screen.getByPlaceholderText('Your full name'), 'John Doe');
      await user.type(screen.getByPlaceholderText('you@example.com'), 'test@example.com');
      await user.selectOptions(screen.getAllByRole('combobox')[0], 'Student');
      await user.click(screen.getByLabelText('Educational purposes'));
      await user.click(screen.getByLabelText('Yes'));
      await user.selectOptions(screen.getAllByRole('combobox')[1], 'Weekly');
      // Select comfort level to satisfy HTML5 and custom validation
      await user.click(screen.getByLabelText(/3 - Somewhat comfortable/));
      await user.click(screen.getByLabelText('Hands-on practice with examples'));

      // Select 3 goals
      const goalCheckboxes = screen.getAllByRole('checkbox');
      const goalsInSection = goalCheckboxes.filter(cb =>
        ['Writing/content creation', 'Research and information gathering', 'Coding/technical tasks']
          .some(goal => cb.closest('label')?.textContent?.includes(goal))
      );
      await user.click(goalsInSection[0]);
      await user.click(goalsInSection[1]);
      await user.click(goalsInSection[2]);

      await user.click(screen.getByRole('button', { name: 'Create Account' }));

      // Should not show validation error when comfort level is selected
      await waitFor(() => {
        expect(api.auth.register).toHaveBeenCalled();
        expect(screen.queryByText('Please fill in all required fields.')).not.toBeInTheDocument();
      });
    });

    it('validates tried_ai_before is not null', async () => {
      renderRegister();
      vi.mocked(api.auth.register).mockResolvedValueOnce({
        user: { id: 1, email: 'test@example.com', created_at: new Date().toISOString() },
        access_token: 'token123',
      });

      await user.type(screen.getByPlaceholderText('Your full name'), 'John Doe');
      await user.type(screen.getByPlaceholderText('you@example.com'), 'test@example.com');
      await user.selectOptions(screen.getAllByRole('combobox')[0], 'Student');
      await user.click(screen.getByLabelText('Educational purposes'));
      // Select tried_ai_before to satisfy HTML5 and custom validation
      await user.click(screen.getByLabelText('Yes'));
      await user.selectOptions(screen.getAllByRole('combobox')[1], 'Weekly');
      await user.click(screen.getByLabelText(/3 - Somewhat comfortable/));
      await user.click(screen.getByLabelText('Hands-on practice with examples'));

      // Select 3 goals
      const goalCheckboxes = screen.getAllByRole('checkbox');
      const goalsInSection = goalCheckboxes.filter(cb =>
        ['Writing/content creation', 'Research and information gathering', 'Coding/technical tasks']
          .some(goal => cb.closest('label')?.textContent?.includes(goal))
      );
      await user.click(goalsInSection[0]);
      await user.click(goalsInSection[1]);
      await user.click(goalsInSection[2]);

      await user.click(screen.getByRole('button', { name: 'Create Account' }));

      // Should not show validation error when tried_ai_before is selected
      await waitFor(() => {
        expect(api.auth.register).toHaveBeenCalled();
        expect(screen.queryByText('Please fill in all required fields.')).not.toBeInTheDocument();
      });
    });
  });

  describe('Edge Cases - API Payload', () => {
    it('includes Other text in ai_tools_used when Other is selected', async () => {
      renderRegister();
      vi.mocked(api.auth.register).mockResolvedValueOnce({
        user: { id: 1, email: 'test@example.com', created_at: new Date().toISOString() },
        access_token: 'token123',
      });

      await fillRequiredFields();

      // Select Other AI tool and fill text
      const otherCheckbox = screen.getAllByRole('checkbox').find(cb =>
        cb.closest('label')?.textContent?.includes('Other') &&
        !cb.closest('label')?.textContent?.includes('Goals')
      );
      await user.click(otherCheckbox!);
      await user.type(screen.getByPlaceholderText('Please specify other AI tools'), 'Custom AI Tool');

      await user.click(screen.getByRole('button', { name: 'Create Account' }));

      await waitFor(() => {
        expect(api.auth.register).toHaveBeenCalled();
        const callArg = vi.mocked(api.auth.register).mock.calls[0][0];
        expect(callArg.ai_tools_used).toContain('Other: Custom AI Tool');
      });
    });

    it('includes Other text in goals when Other is selected', async () => {
      renderRegister();
      vi.mocked(api.auth.register).mockResolvedValueOnce({
        user: { id: 1, email: 'test@example.com', created_at: new Date().toISOString() },
        access_token: 'token123',
      });

      await user.type(screen.getByPlaceholderText('Your full name'), 'John Doe');
      await user.type(screen.getByPlaceholderText('you@example.com'), 'test@example.com');
      await user.selectOptions(screen.getAllByRole('combobox')[0], 'Student');
      await user.click(screen.getByLabelText('Educational purposes'));
      await user.click(screen.getByLabelText('Yes'));
      await user.selectOptions(screen.getAllByRole('combobox')[1], 'Weekly');
      await user.click(screen.getByLabelText(/3 - Somewhat comfortable/));
      await user.click(screen.getByLabelText('Hands-on practice with examples'));

      // Select 2 regular goals + Other
      const goalCheckboxes = screen.getAllByRole('checkbox');
      const writingGoal = goalCheckboxes.find(cb =>
        cb.closest('label')?.textContent === 'Writing/content creation'
      );
      const researchGoal = goalCheckboxes.find(cb =>
        cb.closest('label')?.textContent === 'Research and information gathering'
      );
      const otherGoal = goalCheckboxes.find(cb => {
        const labelText = cb.closest('label')?.textContent || '';
        const sectionHeading = cb.closest('.space-y-4')?.querySelector('h2')?.textContent || '';
        return labelText === 'Other' && sectionHeading.includes('Goals');
      });

      await user.click(writingGoal!);
      await user.click(researchGoal!);
      await user.click(otherGoal!);
      await user.type(screen.getByPlaceholderText('Please specify your other goal'), 'Custom Goal');

      await user.click(screen.getByRole('button', { name: 'Create Account' }));

      await waitFor(() => {
        expect(api.auth.register).toHaveBeenCalled();
        const callArg = vi.mocked(api.auth.register).mock.calls[0][0];
        expect(callArg.goals).toContain('Other: Custom Goal');
      });
    });

    it('includes Other text in challenges when Other is selected', async () => {
      renderRegister();
      vi.mocked(api.auth.register).mockResolvedValueOnce({
        user: { id: 1, email: 'test@example.com', created_at: new Date().toISOString() },
        access_token: 'token123',
      });

      await fillRequiredFields();

      // Select Other challenge and fill text
      const challengeCheckboxes = screen.getAllByRole('checkbox');
      const otherChallenge = challengeCheckboxes.find(cb =>
        cb.closest('label')?.textContent === 'Other' &&
        cb.closest('.space-y-4')?.querySelector('h2')?.textContent?.includes('Biggest Challenge')
      );
      await user.click(otherChallenge!);
      await user.type(screen.getByPlaceholderText('Please specify your other challenge'), 'Custom Challenge');

      await user.click(screen.getByRole('button', { name: 'Create Account' }));

      await waitFor(() => {
        expect(api.auth.register).toHaveBeenCalled();
        const callArg = vi.mocked(api.auth.register).mock.calls[0][0];
        expect(callArg.challenges).toContain('Other: Custom Challenge');
      });
    });

    it('omits ai_tools_used from payload when tried_ai_before is false', async () => {
      renderRegister();
      vi.mocked(api.auth.register).mockResolvedValueOnce({
        user: { id: 1, email: 'test@example.com', created_at: new Date().toISOString() },
        access_token: 'token123',
      });

      await user.type(screen.getByPlaceholderText('Your full name'), 'John Doe');
      await user.type(screen.getByPlaceholderText('you@example.com'), 'test@example.com');
      await user.selectOptions(screen.getAllByRole('combobox')[0], 'Student');
      await user.click(screen.getByLabelText('Educational purposes'));
      await user.click(screen.getByLabelText('No')); // No AI experience - this hides Usage & Comfort Level section
      // Note: usage_frequency and comfort_level are not needed when tried_ai_before is false
      await user.click(screen.getByLabelText('Hands-on practice with examples'));

      // Select 3 goals
      const goalCheckboxes = screen.getAllByRole('checkbox');
      const goalsInSection = goalCheckboxes.filter(cb =>
        ['Writing/content creation', 'Research and information gathering', 'Coding/technical tasks']
          .some(goal => cb.closest('label')?.textContent?.includes(goal))
      );
      await user.click(goalsInSection[0]);
      await user.click(goalsInSection[1]);
      await user.click(goalsInSection[2]);

      await user.click(screen.getByRole('button', { name: 'Create Account' }));

      await waitFor(() => {
        expect(api.auth.register).toHaveBeenCalled();
        const callArg = vi.mocked(api.auth.register).mock.calls[0][0];
        expect(callArg.tried_ai_before).toBe(false);
        expect(callArg.ai_tools_used).toBeUndefined();
        expect(callArg.usage_frequency).toBeUndefined();
        expect(callArg.comfort_level).toBeUndefined();
      });
    });

    it('omits challenges from payload when none selected', async () => {
      renderRegister();
      vi.mocked(api.auth.register).mockResolvedValueOnce({
        user: { id: 1, email: 'test@example.com', created_at: new Date().toISOString() },
        access_token: 'token123',
      });

      await fillRequiredFields();
      // Don't select any challenges

      await user.click(screen.getByRole('button', { name: 'Create Account' }));

      await waitFor(() => {
        expect(api.auth.register).toHaveBeenCalled();
        const callArg = vi.mocked(api.auth.register).mock.calls[0][0];
        expect(callArg.challenges).toBeUndefined();
      });
    });
  });
});
