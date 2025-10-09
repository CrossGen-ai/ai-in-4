interface CourseCardProps {
  course: {
    id: number;
    title: string;
    description?: string;
    category: string;
    schedule?: string;
    has_access?: boolean;
    // Optional product fields (if coming from products API)
    name?: string;
    price?: number;
    price_id?: string;
    currency?: string;
  };
  hasAccess: boolean;
  onAccessClick?: () => void;
}

export function CourseCard({ course, hasAccess, onAccessClick }: CourseCardProps) {
  const isFree = course.category === 'free';
  const isLocked = !isFree && !hasAccess;
  const courseTitle = course.title || course.name || 'Untitled Course';

  return (
    <div className="relative bg-white rounded-lg shadow-md overflow-hidden hover:shadow-lg transition-shadow">
      <div className="p-6">
        {/* Category badge */}
        <div className="flex items-center justify-between mb-3">
          <span className={`inline-block px-3 py-1 text-xs font-semibold rounded-full ${
            course.category === 'free' ? 'bg-green-100 text-green-800' :
            course.category === 'curriculum' ? 'bg-purple-100 text-purple-800' :
            course.category === 'alacarte' ? 'bg-blue-100 text-blue-800' :
            'bg-gray-100 text-gray-800'
          }`}>
            {course.category.toUpperCase()}
          </span>

          {isFree && (
            <span className="text-green-600 font-semibold">FREE</span>
          )}
          {isLocked && (
            <span className="text-gray-500 flex items-center gap-1">
              <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M5 9V7a5 5 0 0110 0v2a2 2 0 012 2v5a2 2 0 01-2 2H5a2 2 0 01-2-2v-5a2 2 0 012-2zm8-2v2H7V7a3 3 0 016 0z" clipRule="evenodd" />
              </svg>
              Locked
            </span>
          )}
        </div>

        {/* Course info */}
        <h3 className="text-xl font-bold mb-2 text-gray-900">{courseTitle}</h3>
        <p className="text-gray-600 text-sm mb-4 line-clamp-3">
          {course.description || 'No description available'}
        </p>

        {/* Schedule */}
        {course.schedule && (
          <p className="text-sm text-gray-500 mb-4">
            <strong>Schedule:</strong> {course.schedule}
          </p>
        )}

        {/* Action button */}
        <div className="flex items-center justify-between">
          {course.price && (
            <div className="text-lg font-bold text-gray-900">
              {new Intl.NumberFormat('en-US', {
                style: 'currency',
                currency: (course.currency || 'usd').toUpperCase(),
              }).format(course.price / 100)}
            </div>
          )}

          <button
            onClick={onAccessClick}
            className={`px-4 py-2 rounded-lg font-semibold transition-colors ml-auto ${
              hasAccess || isFree
                ? 'bg-blue-600 hover:bg-blue-700 text-white'
                : 'bg-gray-100 hover:bg-gray-200 text-gray-700'
            }`}
          >
            {hasAccess || isFree ? 'Access Materials' :
              course.category === 'curriculum' ? 'Upgrade to Full Curriculum' :
              'Unlock Course'}
          </button>
        </div>
      </div>
    </div>
  );
}
