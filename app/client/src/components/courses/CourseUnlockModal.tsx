import { useStripeCheckout } from '../../hooks/useStripeCheckout';

interface CourseUnlockModalProps {
  isOpen: boolean;
  onClose: () => void;
  course: {
    id: string | number;
    name?: string;
    title?: string;
    description?: string;
    price?: number;
    price_id?: string;
    currency?: string;
    category?: string;
  };
}

export function CourseUnlockModal({ isOpen, onClose, course }: CourseUnlockModalProps) {
  const { initiateCheckout, loading } = useStripeCheckout();

  if (!isOpen) return null;

  const courseName = course.name || course.title || 'Course';
  const formattedPrice = course.price
    ? new Intl.NumberFormat('en-US', {
        style: 'currency',
        currency: (course.currency || 'usd').toUpperCase(),
      }).format(course.price / 100)
    : 'Price not available';

  const handleUnlockAccess = () => {
    if (course.price_id) {
      initiateCheckout(course.price_id);
    } else {
      alert('Unable to initiate checkout. Price information not available.');
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-50">
      <div className="bg-white rounded-lg shadow-xl max-w-md w-full mx-4 overflow-hidden">
        {/* Modal Header */}
        <div className="bg-gradient-to-r from-blue-500 to-purple-600 px-6 py-4 text-white">
          <div className="flex items-center justify-between">
            <h2 className="text-xl font-bold">Unlock Course</h2>
            <button
              onClick={onClose}
              className="text-white hover:text-gray-200 transition-colors"
              aria-label="Close modal"
            >
              <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>
        </div>

        {/* Modal Body */}
        <div className="p-6">
          <h3 className="text-lg font-bold text-gray-900 mb-2">{courseName}</h3>

          {course.description && (
            <p className="text-gray-600 text-sm mb-4">{course.description}</p>
          )}

          {/* Pricing Section */}
          <div className="bg-gray-50 rounded-lg p-4 mb-6">
            <div className="flex items-center justify-between">
              <span className="text-gray-700 font-medium">Course Price:</span>
              <span className="text-2xl font-bold text-gray-900">{formattedPrice}</span>
            </div>

            {course.category && (
              <div className="mt-2 text-sm text-gray-500">
                Category: <span className="font-semibold uppercase">{course.category}</span>
              </div>
            )}
          </div>

          {/* Benefits */}
          <div className="mb-6">
            <h4 className="font-semibold text-gray-900 mb-2">What you'll get:</h4>
            <ul className="space-y-2 text-sm text-gray-600">
              <li className="flex items-start">
                <svg className="w-5 h-5 text-green-500 mr-2 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                </svg>
                Full access to all course materials
              </li>
              <li className="flex items-start">
                <svg className="w-5 h-5 text-green-500 mr-2 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                </svg>
                Lifetime access to course content
              </li>
              <li className="flex items-start">
                <svg className="w-5 h-5 text-green-500 mr-2 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                </svg>
                Certificate of completion
              </li>
            </ul>
          </div>

          {/* Action Buttons */}
          <div className="flex gap-3">
            <button
              onClick={onClose}
              className="flex-1 px-4 py-2 border border-gray-300 rounded-lg font-semibold text-gray-700 hover:bg-gray-50 transition-colors"
            >
              Cancel
            </button>
            <button
              onClick={handleUnlockAccess}
              disabled={loading || !course.price_id}
              className={`flex-1 px-4 py-2 rounded-lg font-semibold transition-colors ${
                loading || !course.price_id
                  ? 'bg-gray-300 text-gray-500 cursor-not-allowed'
                  : 'bg-gradient-to-r from-blue-500 to-purple-600 text-white hover:from-blue-600 hover:to-purple-700'
              }`}
            >
              {loading ? 'Processing...' : 'Unlock Access'}
            </button>
          </div>

          {!course.price_id && (
            <p className="mt-3 text-sm text-red-600 text-center">
              Pricing information unavailable. Please contact support.
            </p>
          )}
        </div>
      </div>
    </div>
  );
}
