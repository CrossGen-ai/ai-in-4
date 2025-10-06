import { Link } from 'react-router-dom';

export function Landing() {
  return (
    <div className="min-h-screen bg-gradient-to-b from-slate-900 to-slate-800">
      {/* Hero Section */}
      <div className="container mx-auto px-4 py-20">
        <div className="text-center">
          <h1 className="text-5xl md:text-6xl font-bold text-white mb-6">
            AI in 4
          </h1>
          <p className="text-xl md:text-2xl text-slate-300 mb-4">
            Humanizing the Machine
          </p>
          <p className="text-lg text-slate-400 mb-12 max-w-2xl mx-auto">
            Learn artificial intelligence through interactive, hands-on sessions.
            Join our community of learners and master AI fundamentals in just 4 weeks.
          </p>
          <div className="flex gap-4 justify-center">
            <Link
              to="/register"
              className="px-8 py-4 bg-blue-600 hover:bg-blue-700 text-white font-semibold rounded-lg transition-colors text-lg"
            >
              Get Started
            </Link>
            <Link
              to="/login"
              className="px-8 py-4 bg-slate-700 hover:bg-slate-600 text-white font-semibold rounded-lg transition-colors text-lg"
            >
              Sign In
            </Link>
          </div>
        </div>

        {/* Course Highlights */}
        <div className="mt-24 grid grid-cols-1 md:grid-cols-3 gap-8">
          <div className="bg-slate-800 p-8 rounded-lg border border-slate-700">
            <div className="text-3xl mb-4">🎓</div>
            <h3 className="text-xl font-semibold text-white mb-3">Expert-Led Sessions</h3>
            <p className="text-slate-400">
              Learn from experienced AI practitioners through interactive live sessions
            </p>
          </div>
          <div className="bg-slate-800 p-8 rounded-lg border border-slate-700">
            <div className="text-3xl mb-4">💡</div>
            <h3 className="text-xl font-semibold text-white mb-3">Practical Projects</h3>
            <p className="text-slate-400">
              Build real AI applications and gain hands-on experience
            </p>
          </div>
          <div className="bg-slate-800 p-8 rounded-lg border border-slate-700">
            <div className="text-3xl mb-4">🤝</div>
            <h3 className="text-xl font-semibold text-white mb-3">Community Support</h3>
            <p className="text-slate-400">
              Connect with fellow learners and grow together
            </p>
          </div>
        </div>

        {/* What You'll Learn */}
        <div className="mt-24">
          <h2 className="text-3xl font-bold text-white text-center mb-12">
            What You'll Learn
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6 max-w-4xl mx-auto">
            <div className="flex items-start gap-4">
              <div className="text-blue-500 text-xl">✓</div>
              <div className="text-slate-300">
                Fundamentals of AI and Machine Learning
              </div>
            </div>
            <div className="flex items-start gap-4">
              <div className="text-blue-500 text-xl">✓</div>
              <div className="text-slate-300">
                Working with Large Language Models
              </div>
            </div>
            <div className="flex items-start gap-4">
              <div className="text-blue-500 text-xl">✓</div>
              <div className="text-slate-300">
                Building AI-Powered Applications
              </div>
            </div>
            <div className="flex items-start gap-4">
              <div className="text-blue-500 text-xl">✓</div>
              <div className="text-slate-300">
                Ethical AI and Best Practices
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Footer */}
      <footer className="border-t border-slate-700 mt-24 py-8">
        <div className="container mx-auto px-4 text-center text-slate-500">
          <p>&copy; 2024 CrossGen AI. All rights reserved.</p>
        </div>
      </footer>
    </div>
  );
}
