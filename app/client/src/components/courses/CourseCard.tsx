import { PaywallOverlay } from './PaywallOverlay';
import { useStripeCheckout } from '../../hooks/useStripeCheckout';

interface CourseCardProps {
  course: {
    id: string;
    name: string;
    description?: string;
    category: string;
    price?: number;
    price_id?: string;
    currency: string;
  };
  hasAccess: boolean;
  onAccessClick?: () => void;
}

export function CourseCard({ course, hasAccess, onAccessClick }: CourseCardProps) {
  const { initiateCheckout, loading } = useStripeCheckout();

  const handleUnlock = () => {
    if (course.price_id) {
      initiateCheckout(course.price_id);
    }
  };

  const isFree = course.category === 'free' || !course.price;
  const isLocked = !isFree && !hasAccess;

  return (
    <div className="relative bg-white rounded-lg shadow-md overflow-hidden hover:shadow-lg transition-shadow">
      <div className="p-6">
        {/* Category badge */}
        <div className="flex items-center justify-between mb-3">
          <span className={`inline-block px-3 py-1 text-xs font-semibold rounded-full ${
            course.category === 'free' ? 'bg-green-100 text-green-800' :
            course.category === 'curriculum' ? 'bg-purple-100 text-purple-800' :
            'bg-blue-100 text-blue-800'
          }`}>
            {course.category.toUpperCase()}
          </span>

          {isFree && (
            <span className="text-green-600 font-semibold">FREE</span>
          )}
        </div>

        {/* Course info */}
        <h3 className="text-xl font-bold mb-2 text-gray-900">{course.name}</h3>
        <p className="text-gray-600 text-sm mb-4 line-clamp-3">
          {course.description || 'No description available'}
        </p>

        {/* Price or action button */}
        <div className="flex items-center justify-between">
          {course.price && (
            <div className="text-lg font-bold text-gray-900">
              {new Intl.NumberFormat('en-US', {
                style: 'currency',
                currency: course.currency.toUpperCase(),
              }).format(course.price / 100)}
            </div>
          )}

          <button
            onClick={onAccessClick}
            className={`px-4 py-2 rounded-lg font-semibold transition-colors ${
              hasAccess || isFree
                ? 'bg-green-600 hover:bg-green-700 text-white'
                : 'bg-gray-200 text-gray-500 cursor-not-allowed'
            }`}
            disabled={isLocked}
          >
            {hasAccess || isFree ? 'Access Now' : 'Locked'}
          </button>
        </div>
      </div>

      {/* Paywall overlay */}
      {isLocked && course.price && (
        <PaywallOverlay
          price={course.price}
          currency={course.currency}
          category={course.category}
          onUnlock={handleUnlock}
          loading={loading}
        />
      )}
    </div>
  );
}
