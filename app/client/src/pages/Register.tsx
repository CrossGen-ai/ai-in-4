import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { api } from '../lib/api/client';
import { useAuth } from '../context/AuthContext';

// Employment status options
const EMPLOYMENT_OPTIONS = [
  'Employed full-time',
  'Employed part-time',
  'Self-employed/Freelancer',
  'Between jobs',
  'Homemaker',
  'Retired',
  'Student',
  'Other'
];

// Primary use context options
const PRIMARY_USE_OPTIONS = [
  'Work/Professional tasks',
  'Home/Personal use',
  'Both equally',
  'Educational purposes',
  'Side business/Hobby projects'
];

// AI tools options
const AI_TOOLS_OPTIONS = [
  'ChatGPT',
  'Claude',
  'Grok',
  'Gemini',
  'Perplexity',
  'Copilot (Microsoft)',
  'Midjourney/DALL-E (image generation)',
  'Other'
];

// Usage frequency options
const USAGE_FREQUENCY_OPTIONS = [
  'Never',
  'Once a month or less',
  'Weekly',
  'Daily',
  'Multiple times per day'
];

// Goals options
const GOALS_OPTIONS = [
  'Writing/content creation',
  'Research and information gathering',
  'Data analysis',
  'Coding/technical tasks',
  'Creative work (images, design)',
  'Customer service/communication',
  'Process automation',
  'Learning new skills',
  'Personal productivity/organization',
  'Meal planning/household management',
  'Career transition support',
  'Other'
];

// Challenges options
const CHALLENGES_OPTIONS = [
  "Don't know where to start",
  "Understanding what AI can/can't do",
  'Writing effective prompts',
  'Knowing which tool to use when',
  'Integrating AI into my workflow',
  'Concerns about accuracy/reliability',
  'Privacy/security concerns',
  'Cost of AI tools',
  'Other'
];

// Learning preference options
const LEARNING_PREFERENCE_OPTIONS = [
  'Step-by-step tutorials',
  'Watching video demonstrations',
  'Hands-on practice with examples',
  'Reading documentation',
  'Mix of all above'
];

export function Register() {
  const navigate = useNavigate();
  const { login } = useAuth();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [formData, setFormData] = useState({
    email: '',
    name: '',
    employment_status: '',
    employment_status_other: '',
    industry: '',
    role: '',
    primary_use_context: '',
    tried_ai_before: null as boolean | null,
    ai_tools_used: [] as string[],
    ai_tools_other: '',
    usage_frequency: '',
    comfort_level: 0,
    goals: [] as string[],
    goals_other: '',
    challenges: [] as string[],
    challenges_other: '',
    learning_preference: '',
    additional_comments: '',
    experience_level: 'Intermediate',
    background: ''
  });

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    // Validate exactly 3 goals selected
    if (formData.goals.length !== 3) {
      setError('Please select exactly 3 goals.');
      setLoading(false);
      return;
    }

    // Validate all required fields
    // Note: usage_frequency and comfort_level are only required if tried_ai_before is true
    const requiredFieldsMissing = !formData.name || !formData.employment_status ||
      !formData.primary_use_context || formData.tried_ai_before === null ||
      !formData.learning_preference ||
      (formData.tried_ai_before && (!formData.usage_frequency || !formData.comfort_level));

    if (requiredFieldsMissing) {
      setError('Please fill in all required fields.');
      setLoading(false);
      return;
    }

    try {
      // Prepare API payload with proper field handling
      const payload = {
        email: formData.email,
        name: formData.name,
        employment_status: formData.employment_status,
        employment_status_other: formData.employment_status === 'Other' ? formData.employment_status_other : undefined,
        industry: formData.industry || undefined,
        role: formData.role || undefined,
        primary_use_context: formData.primary_use_context,
        tried_ai_before: formData.tried_ai_before,
        ai_tools_used: formData.tried_ai_before ? formData.ai_tools_used.map(tool =>
          tool === 'Other' && formData.ai_tools_other ? `Other: ${formData.ai_tools_other}` : tool
        ) : undefined,
        usage_frequency: formData.tried_ai_before ? formData.usage_frequency : undefined,
        comfort_level: formData.tried_ai_before ? formData.comfort_level : undefined,
        goals: formData.goals.map(goal =>
          goal === 'Other' && formData.goals_other ? `Other: ${formData.goals_other}` : goal
        ),
        challenges: formData.challenges.length > 0 ? formData.challenges.map(challenge =>
          challenge === 'Other' && formData.challenges_other ? `Other: ${formData.challenges_other}` : challenge
        ) : undefined,
        learning_preference: formData.learning_preference,
        additional_comments: formData.additional_comments || undefined,
        experience_level: formData.experience_level,
        background: formData.background || undefined
      };

      const response = await api.auth.register(payload);

      // Login with the returned token
      await login(response.access_token);

      // Redirect to dashboard
      navigate('/dashboard');
    } catch (err: any) {
      setError(err.message || 'Registration failed. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const toggleArrayField = (field: 'ai_tools_used' | 'goals' | 'challenges', value: string) => {
    setFormData(prev => {
      const currentArray = prev[field];
      const isSelected = currentArray.includes(value);

      if (isSelected) {
        return { ...prev, [field]: currentArray.filter(item => item !== value) };
      } else {
        // For goals, enforce 3-item limit
        if (field === 'goals' && currentArray.length >= 3) {
          return prev;
        }
        return { ...prev, [field]: [...currentArray, value] };
      }
    });
  };

  const getCharCount = (text: string, limit: number) => {
    return `${text.length}/${limit}`;
  };

  return (
    <div className="min-h-screen bg-gradient-to-b from-slate-900 to-slate-800 py-12 px-4">
      <div className="max-w-3xl mx-auto">
        <div className="text-center mb-8">
          <h1 className="text-4xl font-bold text-white mb-2">Create Your Account</h1>
          <p className="text-slate-400">Help us personalize your AI learning journey</p>
        </div>

        <div className="bg-slate-800 rounded-lg border border-slate-700 p-8">
          <form onSubmit={handleSubmit} className="space-y-8">
            {/* BASIC INFO SECTION */}
            <div className="space-y-4">
              <h2 className="text-2xl font-bold text-white border-b border-slate-600 pb-2">Basic Info</h2>

              {/* Name */}
              <div>
                <label className="block text-sm font-medium text-slate-300 mb-2">
                  Name <span className="text-red-400">*</span>
                </label>
                <input
                  type="text"
                  required
                  maxLength={100}
                  value={formData.name}
                  onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                  className="w-full px-4 py-2 bg-slate-900 border border-slate-600 rounded-lg text-white focus:outline-none focus:border-blue-500"
                  placeholder="Your full name"
                />
                <div className="text-xs text-slate-500 mt-1">{getCharCount(formData.name, 100)}</div>
              </div>

              {/* Email */}
              <div>
                <label className="block text-sm font-medium text-slate-300 mb-2">
                  Email Address <span className="text-red-400">*</span>
                </label>
                <input
                  type="email"
                  required
                  maxLength={150}
                  value={formData.email}
                  onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                  className="w-full px-4 py-2 bg-slate-900 border border-slate-600 rounded-lg text-white focus:outline-none focus:border-blue-500"
                  placeholder="you@example.com"
                />
                <div className="text-xs text-slate-500 mt-1">{getCharCount(formData.email, 150)}</div>
              </div>

              {/* Employment Status */}
              <div>
                <label className="block text-sm font-medium text-slate-300 mb-2">
                  Employment Status <span className="text-red-400">*</span>
                </label>
                <select
                  required
                  value={formData.employment_status}
                  onChange={(e) => setFormData({ ...formData, employment_status: e.target.value, employment_status_other: '' })}
                  className="w-full px-4 py-2 bg-slate-900 border border-slate-600 rounded-lg text-white focus:outline-none focus:border-blue-500"
                >
                  <option value="">Select employment status</option>
                  {EMPLOYMENT_OPTIONS.map(option => (
                    <option key={option} value={option}>{option}</option>
                  ))}
                </select>
              </div>

              {/* Employment Status Other (conditional) */}
              {formData.employment_status === 'Other' && (
                <div>
                  <label className="block text-sm font-medium text-slate-300 mb-2">
                    Please specify <span className="text-red-400">*</span>
                  </label>
                  <input
                    type="text"
                    required
                    maxLength={50}
                    value={formData.employment_status_other}
                    onChange={(e) => setFormData({ ...formData, employment_status_other: e.target.value })}
                    className="w-full px-4 py-2 bg-slate-900 border border-slate-600 rounded-lg text-white focus:outline-none focus:border-blue-500"
                    placeholder="Your employment status"
                  />
                  <div className="text-xs text-slate-500 mt-1">{getCharCount(formData.employment_status_other, 50)}</div>
                </div>
              )}

              {/* Industry */}
              <div>
                <label className="block text-sm font-medium text-slate-300 mb-2">
                  Industry/Field (Optional)
                </label>
                <input
                  type="text"
                  maxLength={100}
                  value={formData.industry}
                  onChange={(e) => setFormData({ ...formData, industry: e.target.value })}
                  className="w-full px-4 py-2 bg-slate-900 border border-slate-600 rounded-lg text-white focus:outline-none focus:border-blue-500"
                  placeholder="e.g., Technology, Healthcare, Education"
                />
                <div className="text-xs text-slate-500 mt-1">{getCharCount(formData.industry, 100)}</div>
              </div>

              {/* Role */}
              <div>
                <label className="block text-sm font-medium text-slate-300 mb-2">
                  Role/Job Title (Optional)
                </label>
                <input
                  type="text"
                  maxLength={100}
                  value={formData.role}
                  onChange={(e) => setFormData({ ...formData, role: e.target.value })}
                  className="w-full px-4 py-2 bg-slate-900 border border-slate-600 rounded-lg text-white focus:outline-none focus:border-blue-500"
                  placeholder="e.g., Software Engineer, Teacher, Manager"
                />
                <div className="text-xs text-slate-500 mt-1">{getCharCount(formData.role, 100)}</div>
              </div>
            </div>

            {/* PRIMARY USE CONTEXT SECTION */}
            <div className="space-y-4">
              <h2 className="text-2xl font-bold text-white border-b border-slate-600 pb-2">Primary Use Context</h2>

              <div>
                <label className="block text-sm font-medium text-slate-300 mb-3">
                  Where do you plan to use AI most? <span className="text-red-400">*</span>
                </label>
                <div className="space-y-2">
                  {PRIMARY_USE_OPTIONS.map(option => (
                    <label key={option} className="flex items-center space-x-3 text-slate-300 cursor-pointer hover:text-white">
                      <input
                        type="radio"
                        name="primary_use_context"
                        required
                        value={option}
                        checked={formData.primary_use_context === option}
                        onChange={(e) => setFormData({ ...formData, primary_use_context: e.target.value })}
                        className="w-4 h-4 text-blue-600 focus:ring-blue-500"
                      />
                      <span>{option}</span>
                    </label>
                  ))}
                </div>
              </div>
            </div>

            {/* CURRENT AI EXPERIENCE SECTION */}
            <div className="space-y-4">
              <h2 className="text-2xl font-bold text-white border-b border-slate-600 pb-2">Current AI Experience</h2>

              {/* Tried AI Before */}
              <div>
                <label className="block text-sm font-medium text-slate-300 mb-3">
                  Have you tried AI tools before? <span className="text-red-400">*</span>
                </label>
                <div className="flex space-x-6">
                  <label className="flex items-center space-x-3 text-slate-300 cursor-pointer hover:text-white">
                    <input
                      type="radio"
                      name="tried_ai_before"
                      required
                      value="true"
                      checked={formData.tried_ai_before === true}
                      onChange={() => setFormData({ ...formData, tried_ai_before: true })}
                      className="w-4 h-4 text-blue-600 focus:ring-blue-500"
                    />
                    <span>Yes</span>
                  </label>
                  <label className="flex items-center space-x-3 text-slate-300 cursor-pointer hover:text-white">
                    <input
                      type="radio"
                      name="tried_ai_before"
                      required
                      value="false"
                      checked={formData.tried_ai_before === false}
                      onChange={() => setFormData({
                        ...formData,
                        tried_ai_before: false,
                        ai_tools_used: [],
                        ai_tools_other: '',
                        usage_frequency: '',
                        comfort_level: 0
                      })}
                      className="w-4 h-4 text-blue-600 focus:ring-blue-500"
                    />
                    <span>No</span>
                  </label>
                </div>
              </div>

              {/* AI Tools Used (conditional) */}
              {formData.tried_ai_before === true && (
                <div>
                  <label className="block text-sm font-medium text-slate-300 mb-3">
                    Which AI tools have you used? (Select all that apply)
                  </label>
                  <div className="space-y-2">
                    {AI_TOOLS_OPTIONS.map(option => (
                      <label key={option} className="flex items-center space-x-3 text-slate-300 cursor-pointer hover:text-white">
                        <input
                          type="checkbox"
                          value={option}
                          checked={formData.ai_tools_used.includes(option)}
                          onChange={() => toggleArrayField('ai_tools_used', option)}
                          className="w-4 h-4 text-blue-600 focus:ring-blue-500 rounded"
                        />
                        <span>{option}</span>
                      </label>
                    ))}
                  </div>

                  {/* AI Tools Other (conditional) */}
                  {formData.ai_tools_used.includes('Other') && (
                    <div className="mt-3">
                      <input
                        type="text"
                        maxLength={100}
                        value={formData.ai_tools_other}
                        onChange={(e) => setFormData({ ...formData, ai_tools_other: e.target.value })}
                        className="w-full px-4 py-2 bg-slate-900 border border-slate-600 rounded-lg text-white focus:outline-none focus:border-blue-500"
                        placeholder="Please specify other AI tools"
                      />
                      <div className="text-xs text-slate-500 mt-1">{getCharCount(formData.ai_tools_other, 100)}</div>
                    </div>
                  )}
                </div>
              )}
            </div>

            {/* USAGE & COMFORT LEVEL SECTION (conditional) */}
            {formData.tried_ai_before === true && (
              <div className="space-y-4">
                <h2 className="text-2xl font-bold text-white border-b border-slate-600 pb-2">Usage & Comfort Level</h2>

                {/* Usage Frequency */}
                <div>
                  <label className="block text-sm font-medium text-slate-300 mb-2">
                    How often do you currently use AI tools? <span className="text-red-400">*</span>
                  </label>
                  <select
                    required={formData.tried_ai_before === true}
                    value={formData.usage_frequency}
                    onChange={(e) => setFormData({ ...formData, usage_frequency: e.target.value })}
                    className="w-full px-4 py-2 bg-slate-900 border border-slate-600 rounded-lg text-white focus:outline-none focus:border-blue-500"
                  >
                    <option value="">Select frequency</option>
                    {USAGE_FREQUENCY_OPTIONS.map(option => (
                      <option key={option} value={option}>{option}</option>
                    ))}
                  </select>
                </div>

                {/* Comfort Level */}
                <div>
                  <label className="block text-sm font-medium text-slate-300 mb-3">
                    Rate your comfort level with AI (1-5) <span className="text-red-400">*</span>
                  </label>
                  <div className="space-y-2">
                    {[1, 2, 3, 4, 5].map(level => (
                      <label key={level} className="flex items-center space-x-3 text-slate-300 cursor-pointer hover:text-white">
                        <input
                          type="radio"
                          name="comfort_level"
                          required={formData.tried_ai_before === true}
                          value={level}
                          checked={formData.comfort_level === level}
                          onChange={() => setFormData({ ...formData, comfort_level: level })}
                          className="w-4 h-4 text-blue-600 focus:ring-blue-500"
                        />
                        <span>
                          {level} - {
                            level === 1 ? 'Complete beginner' :
                            level === 2 ? 'Slightly familiar' :
                            level === 3 ? 'Somewhat comfortable' :
                            level === 4 ? 'Confident' :
                            'Very confident'
                          }
                        </span>
                      </label>
                    ))}
                  </div>
                </div>
              </div>
            )}

            {/* GOALS & APPLICATIONS SECTION */}
            <div className="space-y-4">
              <h2 className="text-2xl font-bold text-white border-b border-slate-600 pb-2">Goals & Applications</h2>

              <div>
                <label className="block text-sm font-medium text-slate-300 mb-2">
                  What do you want to use AI for? <span className="text-red-400">*</span>
                </label>
                <p className="text-sm text-slate-400 mb-3">
                  Select exactly 3 goals ({formData.goals.length}/3 selected)
                </p>
                <div className="space-y-2">
                  {GOALS_OPTIONS.map(option => {
                    const isSelected = formData.goals.includes(option);
                    const isDisabled = !isSelected && formData.goals.length >= 3;

                    return (
                      <label
                        key={option}
                        className={`flex items-center space-x-3 cursor-pointer ${
                          isDisabled ? 'text-slate-600' : 'text-slate-300 hover:text-white'
                        }`}
                      >
                        <input
                          type="checkbox"
                          value={option}
                          checked={isSelected}
                          disabled={isDisabled}
                          onChange={() => toggleArrayField('goals', option)}
                          className="w-4 h-4 text-blue-600 focus:ring-blue-500 rounded disabled:opacity-50"
                        />
                        <span>{option}</span>
                      </label>
                    );
                  })}
                </div>

                {/* Goals Other (conditional) */}
                {formData.goals.includes('Other') && (
                  <div className="mt-3">
                    <input
                      type="text"
                      maxLength={100}
                      value={formData.goals_other}
                      onChange={(e) => setFormData({ ...formData, goals_other: e.target.value })}
                      className="w-full px-4 py-2 bg-slate-900 border border-slate-600 rounded-lg text-white focus:outline-none focus:border-blue-500"
                      placeholder="Please specify your other goal"
                    />
                    <div className="text-xs text-slate-500 mt-1">{getCharCount(formData.goals_other, 100)}</div>
                  </div>
                )}
              </div>
            </div>

            {/* BIGGEST CHALLENGE SECTION */}
            <div className="space-y-4">
              <h2 className="text-2xl font-bold text-white border-b border-slate-600 pb-2">Biggest Challenge</h2>

              <div>
                <label className="block text-sm font-medium text-slate-300 mb-3">
                  What's your biggest obstacle with AI right now? (Select all that apply)
                </label>
                <div className="space-y-2">
                  {CHALLENGES_OPTIONS.map(option => (
                    <label key={option} className="flex items-center space-x-3 text-slate-300 cursor-pointer hover:text-white">
                      <input
                        type="checkbox"
                        value={option}
                        checked={formData.challenges.includes(option)}
                        onChange={() => toggleArrayField('challenges', option)}
                        className="w-4 h-4 text-blue-600 focus:ring-blue-500 rounded"
                      />
                      <span>{option}</span>
                    </label>
                  ))}
                </div>

                {/* Challenges Other (conditional) */}
                {formData.challenges.includes('Other') && (
                  <div className="mt-3">
                    <input
                      type="text"
                      maxLength={150}
                      value={formData.challenges_other}
                      onChange={(e) => setFormData({ ...formData, challenges_other: e.target.value })}
                      className="w-full px-4 py-2 bg-slate-900 border border-slate-600 rounded-lg text-white focus:outline-none focus:border-blue-500"
                      placeholder="Please specify your other challenge"
                    />
                    <div className="text-xs text-slate-500 mt-1">{getCharCount(formData.challenges_other, 150)}</div>
                  </div>
                )}
              </div>
            </div>

            {/* LEARNING PREFERENCE SECTION */}
            <div className="space-y-4">
              <h2 className="text-2xl font-bold text-white border-b border-slate-600 pb-2">Learning Preference</h2>

              <div>
                <label className="block text-sm font-medium text-slate-300 mb-3">
                  How do you learn best? <span className="text-red-400">*</span>
                </label>
                <div className="space-y-2">
                  {LEARNING_PREFERENCE_OPTIONS.map(option => (
                    <label key={option} className="flex items-center space-x-3 text-slate-300 cursor-pointer hover:text-white">
                      <input
                        type="radio"
                        name="learning_preference"
                        required
                        value={option}
                        checked={formData.learning_preference === option}
                        onChange={(e) => setFormData({ ...formData, learning_preference: e.target.value })}
                        className="w-4 h-4 text-blue-600 focus:ring-blue-500"
                      />
                      <span>{option}</span>
                    </label>
                  ))}
                </div>
              </div>
            </div>

            {/* ADDITIONAL COMMENTS SECTION */}
            <div className="space-y-4">
              <h2 className="text-2xl font-bold text-white border-b border-slate-600 pb-2">Additional Comments</h2>

              <div>
                <label className="block text-sm font-medium text-slate-300 mb-2">
                  Is there anything else you'd like us to know about your AI learning goals? (Optional)
                </label>
                <textarea
                  rows={4}
                  maxLength={500}
                  value={formData.additional_comments}
                  onChange={(e) => setFormData({ ...formData, additional_comments: e.target.value })}
                  className="w-full px-4 py-2 bg-slate-900 border border-slate-600 rounded-lg text-white focus:outline-none focus:border-blue-500"
                  placeholder="Share any additional thoughts or questions..."
                />
                <div className="text-xs text-slate-500 mt-1">{getCharCount(formData.additional_comments, 500)}</div>
              </div>
            </div>

            {error && (
              <div className="bg-red-900/50 border border-red-700 text-red-200 px-4 py-3 rounded-lg">
                {error}
              </div>
            )}

            <button
              type="submit"
              disabled={loading}
              className="w-full px-6 py-3 bg-blue-600 hover:bg-blue-700 disabled:bg-blue-800 text-white font-semibold rounded-lg transition-colors"
            >
              {loading ? 'Creating Account...' : 'Create Account'}
            </button>
          </form>

          <div className="mt-6 text-center">
            <p className="text-slate-400">
              Already have an account?{' '}
              <a href="/login" className="text-blue-400 hover:text-blue-300">
                Sign in
              </a>
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
