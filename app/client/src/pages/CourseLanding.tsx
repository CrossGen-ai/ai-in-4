import { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import { api } from '../lib/api/client';
import { Course } from '../lib/api/types';

export function CourseLanding() {
  const { user, logout } = useAuth();
  const [courses, setCourses] = useState<Course[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    loadCourses();
  }, []);

  const loadCourses = async () => {
    try {
      const courseList = await api.courses.listCourses();
      setCourses(courseList);
    } catch (err: any) {
      setError(err.message || 'Failed to load courses');
    } finally {
      setLoading(false);
    }
  };

  const handleLogout = () => {
    logout();
    window.location.href = '/';
  };

  return (
    <div className="min-h-screen bg-gradient-to-b from-slate-900 to-slate-800">
      {/* Header */}
      <header className="bg-slate-800 border-b border-slate-700">
        <div className="container mx-auto px-4 py-4">
          <div className="flex justify-between items-center">
            <h1 className="text-2xl font-bold text-white">AI in 4</h1>
            <div className="flex items-center gap-4">
              <span className="text-slate-400">{user?.email}</span>
              <button
                onClick={handleLogout}
                className="px-4 py-2 bg-slate-700 hover:bg-slate-600 text-white rounded-lg transition-colors"
              >
                Logout
              </button>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <div className="container mx-auto px-4 py-12">
        <div className="mb-8">
          <h2 className="text-3xl font-bold text-white mb-2">Welcome to Your Dashboard</h2>
          <p className="text-slate-400">Here are your available courses and upcoming sessions</p>
        </div>

        {loading ? (
          <div className="text-center text-slate-400">Loading courses...</div>
        ) : error ? (
          <div className="bg-red-900/50 border border-red-700 text-red-200 px-4 py-3 rounded-lg">
            {error}
          </div>
        ) : courses.length === 0 ? (
          <div className="bg-slate-800 border border-slate-700 rounded-lg p-12 text-center">
            <p className="text-slate-400">No courses available yet. Check back soon!</p>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {courses.map((course) => (
              <div key={course.id} className="bg-slate-800 border border-slate-700 rounded-lg p-6">
                <h3 className="text-xl font-semibold text-white mb-3">{course.title}</h3>
                {course.description && (
                  <p className="text-slate-400 mb-4">{course.description}</p>
                )}
                {course.schedule && (
                  <div className="mb-4">
                    <div className="text-sm font-medium text-slate-300 mb-1">Schedule:</div>
                    <div className="text-sm text-slate-400">{course.schedule}</div>
                  </div>
                )}
                {course.materials_url && (
                  <a
                    href={course.materials_url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="inline-block px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition-colors text-sm"
                  >
                    Access Materials
                  </a>
                )}
              </div>
            ))}
          </div>
        )}

        {/* User Info Section */}
        <div className="mt-12 bg-slate-800 border border-slate-700 rounded-lg p-6">
          <h3 className="text-lg font-semibold text-white mb-4">Your Profile</h3>
          <div className="space-y-2 text-sm">
            <div>
              <span className="text-slate-400">Email:</span>{' '}
              <span className="text-white">{user?.email}</span>
            </div>
            <div>
              <span className="text-slate-400">Member since:</span>{' '}
              <span className="text-white">
                {user?.created_at ? new Date(user.created_at).toLocaleDateString() : 'N/A'}
              </span>
            </div>
            {user?.last_login && (
              <div>
                <span className="text-slate-400">Last login:</span>{' '}
                <span className="text-white">
                  {new Date(user.last_login).toLocaleString()}
                </span>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
