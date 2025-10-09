import { useEffect, useState } from 'react';
import { useAuth } from '../context/AuthContext';
import { api } from '../lib/api/client';
import { useCourseEntitlements } from '../hooks/useCourseEntitlements';
import { useReferralStats } from '../hooks/useReferralStats';
import { CourseCard } from '../components/courses/CourseCard';
import { CourseUnlockModal } from '../components/courses/CourseUnlockModal';
import { useNavigate } from 'react-router-dom';

export default function Dashboard() {
  const { user } = useAuth();
  const navigate = useNavigate();
  const { entitlements, hasAccess, loading: entitlementsLoading } = useCourseEntitlements();
  const { stats: referralStats } = useReferralStats();
  const [products, setProducts] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [copiedCode, setCopiedCode] = useState(false);
  const [modalOpen, setModalOpen] = useState(false);
  const [selectedCourse, setSelectedCourse] = useState<any>(null);

  useEffect(() => {
    const fetchCourses = async () => {
      try {
        // Fetch products with pricing from Stripe
        const productsData = await api.courses.listProducts();

        // Fetch user's course access status
        const coursesWithAccess = await api.courses.listCoursesWithAccess();

        // Create a map of course access by matching product names to course titles
        const accessMap = new Map(
          coursesWithAccess.map((c: any) => [c.title || c.name, c.has_access])
        );

        // Merge products with access information
        const mergedData = productsData.map((product: any) => ({
          ...product,
          has_access: accessMap.get(product.name) ?? false,
        }));

        setProducts(mergedData);
      } catch (error) {
        console.error('Failed to fetch courses:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchCourses();
  }, []);

  const handleCopyReferralCode = () => {
    if (referralStats?.referral_code) {
      const referralUrl = `${window.location.origin}/ref/${referralStats.referral_code}`;
      navigator.clipboard.writeText(referralUrl);
      setCopiedCode(true);
      setTimeout(() => setCopiedCode(false), 2000);
    }
  };

  const handleCourseClick = (course: any) => {
    const isFree = course.category === 'free';
    const hasAccessToCourse = course.has_access ?? false;

    if (isFree || hasAccessToCourse) {
      // Navigate to course content
      navigate(`/course/${course.id}`);
    } else {
      // Open unlock modal for locked paid courses
      setSelectedCourse(course);
      setModalOpen(true);
    }
  };

  const groupedProducts = {
    free: products.filter(p => p.category === 'free'),
    curriculum: products.filter(p => p.category === 'curriculum'),
    alacarte: products.filter(p => p.category === 'alacarte'),
  };

  if (loading || entitlementsLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-xl">Loading...</div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-7xl mx-auto px-4 py-8">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">
            Welcome Back{user?.email ? `, ${user.email.split('@')[0]}` : ''}!
          </h1>
          <p className="text-gray-600">
            Explore courses and unlock new learning opportunities
          </p>
        </div>

        {/* Referral Card */}
        {referralStats && (
          <div className="bg-gradient-to-r from-blue-500 to-purple-600 rounded-lg p-6 mb-8 text-white">
            <h2 className="text-xl font-bold mb-4">Refer Friends & Earn Credits</h2>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
              <div>
                <div className="text-2xl font-bold">{referralStats.total_referrals}</div>
                <div className="text-sm opacity-90">Total Referrals</div>
              </div>
              <div>
                <div className="text-2xl font-bold">{referralStats.pending_referrals}</div>
                <div className="text-sm opacity-90">Pending</div>
              </div>
              <div>
                <div className="text-2xl font-bold">
                  ${(referralStats.total_credits / 100).toFixed(2)}
                </div>
                <div className="text-sm opacity-90">Total Credits</div>
              </div>
            </div>
            <div className="flex items-center gap-2">
              <input
                type="text"
                value={`${window.location.origin}/ref/${referralStats.referral_code}`}
                readOnly
                className="flex-1 px-4 py-2 rounded bg-white/20 text-white placeholder-white/60"
              />
              <button
                onClick={handleCopyReferralCode}
                className="px-4 py-2 bg-white text-blue-600 font-semibold rounded hover:bg-gray-100 transition-colors"
              >
                {copiedCode ? 'Copied!' : 'Copy Link'}
              </button>
            </div>
          </div>
        )}

        {/* Free Courses */}
        {groupedProducts.free.length > 0 && (
          <div className="mb-8">
            <h2 className="text-2xl font-bold mb-4">Free Courses</h2>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {groupedProducts.free.map((course) => (
                <CourseCard
                  key={course.id}
                  course={course}
                  hasAccess={course.has_access ?? true}
                  onAccessClick={() => handleCourseClick(course)}
                />
              ))}
            </div>
          </div>
        )}

        {/* Curriculum Courses */}
        {groupedProducts.curriculum.length > 0 && (
          <div className="mb-8">
            <h2 className="text-2xl font-bold mb-4">Full Curriculum</h2>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {groupedProducts.curriculum.map((course) => (
                <CourseCard
                  key={course.id}
                  course={course}
                  hasAccess={course.has_access ?? false}
                  onAccessClick={() => handleCourseClick(course)}
                />
              ))}
            </div>
          </div>
        )}

        {/* A-La-Carte Courses */}
        {groupedProducts.alacarte.length > 0 && (
          <div className="mb-8">
            <h2 className="text-2xl font-bold mb-4">Individual Courses</h2>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {groupedProducts.alacarte.map((course) => (
                <CourseCard
                  key={course.id}
                  course={course}
                  hasAccess={course.has_access ?? false}
                  onAccessClick={() => handleCourseClick(course)}
                />
              ))}
            </div>
          </div>
        )}
      </div>

      {/* Course Unlock Modal */}
      {selectedCourse && (
        <CourseUnlockModal
          isOpen={modalOpen}
          onClose={() => {
            setModalOpen(false);
            setSelectedCourse(null);
          }}
          course={selectedCourse}
        />
      )}
    </div>
  );
}
