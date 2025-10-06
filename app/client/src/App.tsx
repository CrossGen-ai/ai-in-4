import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider } from './context/AuthContext';
import { ProtectedRoute } from './components/auth/ProtectedRoute';
import { Landing } from './pages/Landing';
import { Register } from './pages/Register';
import { ThankYou } from './pages/ThankYou';
import { Login } from './pages/Login';
import { DevLogin } from './pages/DevLogin';
import { CourseLanding } from './pages/CourseLanding';

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
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </AuthProvider>
    </BrowserRouter>
  );
}

export default App;
