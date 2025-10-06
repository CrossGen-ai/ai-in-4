import { Link } from 'react-router-dom';

export function ThankYou() {
  return (
    <div className="min-h-screen bg-gradient-to-b from-slate-900 to-slate-800 py-12 px-4">
      <div className="max-w-2xl mx-auto">
        <div className="bg-slate-800 rounded-lg border border-slate-700 p-8">
          <div className="text-center">
            <div className="text-6xl mb-6">✉️</div>
            <h1 className="text-3xl font-bold text-white mb-4">Check Your Email!</h1>
            <p className="text-slate-300 mb-6">
              We've sent you a magic link to log in. Click the link in your email to access your account.
            </p>

            <div className="bg-slate-900 border border-slate-600 rounded-lg p-6 mb-6">
              <h2 className="text-lg font-semibold text-white mb-3">What is a Magic Link?</h2>
              <p className="text-slate-400 text-sm">
                A magic link is a secure, passwordless way to log in. Instead of creating and remembering a password,
                we'll send you a unique link that expires after 15 minutes. Simply click the link in your email
                to access your account.
              </p>
            </div>

            <div className="space-y-3 text-sm text-slate-400">
              <p>
                <strong className="text-slate-300">Didn't receive the email?</strong>
                <br />
                Check your spam folder or try the login page to request another magic link.
              </p>
            </div>

            <div className="mt-8">
              <Link
                to="/login"
                className="inline-block px-6 py-3 bg-blue-600 hover:bg-blue-700 text-white font-semibold rounded-lg transition-colors"
              >
                Go to Login
              </Link>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
