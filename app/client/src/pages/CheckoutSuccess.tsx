import { useEffect } from 'react';
import { Link } from 'react-router-dom';

export default function CheckoutSuccess() {
  useEffect(() => {
    // Could poll entitlements here to check when access is granted
    // For now, we'll just show success message
  }, []);

  return (
    <div className="min-h-screen bg-gray-50 flex items-center justify-center px-4">
      <div className="max-w-md w-full bg-white rounded-lg shadow-lg p-8 text-center">
        <div className="mb-6">
          <div className="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-4">
            <svg className="w-8 h-8 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
            </svg>
          </div>
          <h1 className="text-2xl font-bold text-gray-900 mb-2">
            Payment Successful!
          </h1>
          <p className="text-gray-600">
            Your payment has been processed successfully.
          </p>
        </div>

        <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-6">
          <p className="text-sm text-blue-800">
            🎉 Your access is being processed. This usually takes just a few moments.
          </p>
        </div>

        <Link
          to="/dashboard"
          className="block w-full px-6 py-3 bg-blue-600 hover:bg-blue-700 text-white font-semibold rounded-lg transition-colors"
        >
          Go to Dashboard
        </Link>

        <p className="mt-4 text-sm text-gray-500">
          You'll receive a confirmation email shortly
        </p>
      </div>
    </div>
  );
}
