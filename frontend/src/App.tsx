import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { Toaster } from 'sonner';
import { AuthProvider } from './contexts/AuthContext';
import { Login } from './components/Login';
import { Navigation } from './components/Navigation';
import { Dashboard } from './components/Dashboard';
import { EmployeeDashboard } from './components/EmployeeDashboard';
import { Questionnaire } from './components/Questionnaire';
import { Consent } from './components/Consent';
import { Upload } from './components/Upload';
import { Results } from './components/Results';
import { AdminQuestionnaires } from './components/AdminQuestionnaires';
import { RoleGuard } from './components/RoleGuard';
import { useAuth } from './contexts/AuthContext';
import './styles/main.css';

function AppRoutes() {
  const { user } = useAuth();

  // Public routes (accessible without login)
  const publicRoutes = (
    <>
      <Route path="/login" element={!user ? <Login /> : <Navigate to="/" replace />} />
      <Route path="/questionnaire" element={<Consent />} />
      <Route path="/questionnaire/start" element={<Questionnaire />} />
    </>
  );

  if (!user) {
    return (
      <Routes>
        {publicRoutes}
        <Route path="*" element={<Navigate to="/login" replace />} />
      </Routes>
    );
  }

  return (
    <div className="min-h-screen bg-gray-900 transition-colors duration-200">
      <Navigation />
      <main className="pt-16">
        <Routes>
          {publicRoutes}
          <Route
            path="/"
            element={
              user.is_staff ? <Dashboard /> : <EmployeeDashboard />
            }
          />
          <Route
            path="/upload"
            element={
              <RoleGuard allowedRoles={['admin']}>
                <Upload />
              </RoleGuard>
            }
          />
          <Route
            path="/results"
            element={
              <RoleGuard allowedRoles={['admin']}>
                <Results />
              </RoleGuard>
            }
          />
          <Route
            path="/admin/questionnaires"
            element={
              <RoleGuard allowedRoles={['admin']}>
                <AdminQuestionnaires />
              </RoleGuard>
            }
          />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </main>
    </div>
  );
}

export default function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <AppRoutes />
        <Toaster position="top-right" richColors />
      </AuthProvider>
    </BrowserRouter>
  );
}

