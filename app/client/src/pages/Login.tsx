import { useState, useEffect } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { api } from '../lib/api/client';

export function Login() {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const { validateToken } = useAuth();
  const [email, setEmail] = useState('');
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState('');
  const [error, setError] = useState('');

  useEffect(() => {
    // Check if there's a token in the URL
    const token = searchParams.get('token');
    if (token) {
      validateMagicLink(token);
    }
  }, [searchParams]);

  const validateMagicLink = async (token: string) => {
    setLoading(true);
    setError('');
    try {
      const success = await validateToken(token);
      if (success) {
        navigate('/courses');
      } else {
        setError('Invalid or expired magic link. Please request a new one.');
      }
    } catch (err: any) {
      setError(err.message || 'Failed to validate magic link');
    } finally {
      setLoading(false);
    }
  };

  const handleRequestMagicLink = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    setMessage('');

    try {
      await api.auth.requestMagicLink(email);
      setMessage('Magic link sent! Check your email.');
      setEmail('');
    } catch (err: any) {
      setError(err.message || 'Failed to send magic link');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-b from-slate-900 to-slate-800 py-12 px-4">
      <div className="max-w-md mx-auto">
        <div className="text-center mb-8">
          <h1 className="text-4xl font-bold text-white mb-2">Welcome Back</h1>
          <p className="text-slate-400">Enter your email to receive a magic link</p>
        </div>

        <div className="bg-slate-800 rounded-lg border border-slate-700 p-8">
          <form onSubmit={handleRequestMagicLink} className="space-y-6">
            <div>
              <label className="block text-sm font-medium text-slate-300 mb-2">
                Email Address
              </label>
              <input
                type="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="w-full px-4 py-2 bg-slate-900 border border-slate-600 rounded-lg text-white focus:outline-none focus:border-blue-500"
                placeholder="you@example.com"
              />
            </div>

            {message && (
              <div className="bg-green-900/50 border border-green-700 text-green-200 px-4 py-3 rounded-lg">
                {message}
              </div>
            )}

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
              {loading ? 'Sending...' : 'Send Magic Link'}
            </button>
          </form>

          <div className="mt-6 text-center">
            <p className="text-slate-400">
              Don't have an account?{' '}
              <a href="/register" className="text-blue-400 hover:text-blue-300">
                Create one
              </a>
            </p>
          </div>

          {import.meta.env.DEV && (
            <div className="mt-6 pt-6 border-t border-slate-700">
              <p className="text-slate-400 text-sm text-center mb-3">Development Mode</p>
              <a
                href="/dev-login"
                className="block w-full px-4 py-2 bg-slate-700 hover:bg-slate-600 text-white text-center rounded-lg transition-colors"
              >
                Quick Login (Dev)
              </a>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
