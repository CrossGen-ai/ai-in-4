import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider } from './context/AuthContext';
import { ProtectedRoute } from './components/auth/ProtectedRoute';
import { Landing } from './pages/Landing';
import { Register } from './pages/Register';
import { ThankYou } from './pages/ThankYou';
import { Login } from './pages/Login';
import { DevLogin } from './pages/DevLogin';
import { CourseLanding } from './pages/CourseLanding';
import Dashboard from './pages/Dashboard';
import CheckoutSuccess from './pages/CheckoutSuccess';
import CheckoutCancel from './pages/CheckoutCancel';

function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <Routes>
          <Route path="/" element={<Landing />} />
          <Route path="/register" element={<Register />} />
          <Route path="/thank-you" element={<ThankYou />} />
          <Route path="/login" element={<Login />} />
          <Route path="/dev-login" element={<DevLogin />} />
          <Route
            path="/courses"
            element={
              <ProtectedRoute>
                <CourseLanding />
              </ProtectedRoute>
            }
          />
          <Route
            path="/dashboard"
            element={
              <ProtectedRoute>
                <Dashboard />
              </ProtectedRoute>
            }
          />
          <Route path="/purchase/success" element={<CheckoutSuccess />} />
          <Route path="/purchase/cancelled" element={<CheckoutCancel />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </AuthProvider>
    </BrowserRouter>
  );
}

export default App;
