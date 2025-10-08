import { useEffect, useState } from 'react';
import { useAuth } from '../context/AuthContext';
import { api } from '../lib/api/client';
import { useCourseEntitlements } from '../hooks/useCourseEntitlements';
import { useReferralStats } from '../hooks/useReferralStats';
import { CourseCard } from '../components/courses/CourseCard';
import { useNavigate } from 'react-router-dom';

export default function Dashboard() {
  const { user } = useAuth();
  const navigate = useNavigate();
  const { entitlements, hasAccess, loading: entitlementsLoading } = useCourseEntitlements();
  const { stats: referralStats } = useReferralStats();
  const [products, setProducts] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [copiedCode, setCopiedCode] = useState(false);

  useEffect(() => {
    const fetchProducts = async () => {
      try {
        const data = await api.courses.listProducts();
        setProducts(data);
      } catch (error) {
        console.error('Failed to fetch products:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchProducts();
  }, []);

  const handleCopyReferralCode = () => {
    if (referralStats?.referral_code) {
      const referralUrl = `${window.location.origin}/ref/${referralStats.referral_code}`;
      navigator.clipboard.writeText(referralUrl);
      setCopiedCode(true);
      setTimeout(() => setCopiedCode(false), 2000);
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
              {groupedProducts.free.map((product) => (
                <CourseCard
                  key={product.id}
                  course={product}
                  hasAccess={true}
                  onAccessClick={() => navigate(`/course/${product.id}`)}
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
              {groupedProducts.curriculum.map((product) => (
                <CourseCard
                  key={product.id}
                  course={product}
                  hasAccess={product.price_id ? hasAccess(product.price_id) : false}
                  onAccessClick={() => {
                    if (product.price_id && hasAccess(product.price_id)) {
                      navigate(`/course/${product.id}`);
                    }
                  }}
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
              {groupedProducts.alacarte.map((product) => (
                <CourseCard
                  key={product.id}
                  course={product}
                  hasAccess={product.price_id ? hasAccess(product.price_id) : false}
                  onAccessClick={() => {
                    if (product.price_id && hasAccess(product.price_id)) {
                      navigate(`/course/${product.id}`);
                    }
                  }}
                />
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
