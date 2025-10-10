import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { api } from '../lib/api/client';
import type { User } from '../lib/api/types';

export function DevLogin() {
  const navigate = useNavigate();
  const { login } = useAuth();
  const [users, setUsers] = useState<User[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    loadUsers();
  }, []);

  const loadUsers = async () => {
    try {
      const userList = await api.auth.getDevUsers();
      setUsers(userList);
    } catch (err: any) {
      setError(err.message || 'Failed to load users');
    } finally {
      setLoading(false);
    }
  };

  const handleSelectUser = async (user: User) => {
    try {
      // Use dev login endpoint for instant authentication
      const response = await api.auth.devLogin(user.email);

      // Login with the token (login function handles storing and fetching user)
      await login(response.access_token);

      // Redirect to dashboard
      navigate('/dashboard');
    } catch (err: any) {
      setError(err.message || 'Failed to login');
    }
  };

  if (!import.meta.env.DEV) {
    navigate('/');
    return null;
  }

  return (
    <div className="min-h-screen bg-gradient-to-b from-slate-900 to-slate-800 py-12 px-4">
      <div className="max-w-2xl mx-auto">
        <div className="text-center mb-8">
          <h1 className="text-4xl font-bold text-white mb-2">Dev Quick Login</h1>
          <p className="text-slate-400">Select a user to login as (Development Only)</p>
        </div>

        <div className="bg-slate-800 rounded-lg border border-slate-700 p-8">
          {loading ? (
            <div className="text-center text-slate-400">Loading users...</div>
          ) : error ? (
            <div className="bg-red-900/50 border border-red-700 text-red-200 px-4 py-3 rounded-lg">
              {error}
            </div>
          ) : users.length === 0 ? (
            <div className="text-center text-slate-400">
              No users found. Run the seed script first.
            </div>
          ) : (
            <div className="space-y-3">
              {users.map((user) => (
                <button
                  key={user.id}
                  onClick={() => handleSelectUser(user)}
                  className="w-full px-4 py-3 bg-slate-700 hover:bg-slate-600 text-white rounded-lg transition-colors text-left"
                >
                  <div className="font-medium">{user.email}</div>
                  <div className="text-sm text-slate-400">
                    User ID: {user.id} | Created: {new Date(user.created_at).toLocaleDateString()}
                  </div>
                </button>
              ))}
            </div>
          )}

          <div className="mt-6 text-center">
            <a href="/login" className="text-blue-400 hover:text-blue-300">
              Back to Login
            </a>
          </div>
        </div>
      </div>
    </div>
  );
}
