import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { BarChart3, Mail, Lock, AlertCircle, Sparkles } from 'lucide-react';

export function Login() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const { login } = useAuth();
  const navigate = useNavigate();

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setError('');

    const success = login(email, password);
    if (success) {
      navigate('/');
    } else {
      setError('Invalid credentials. Please try again.');
    }
  };

  const handleDemoLogin = (role: 'admin' | 'employee') => {
    const demoEmail = role === 'admin' ? 'admin@kobo.com' : 'employee@kobo.com';
    const demoPassword = 'demo1234';
    
    setEmail(demoEmail);
    setPassword(demoPassword);
    
    login(demoEmail, demoPassword);
    navigate('/');
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-900 via-slate-900 to-gray-900 flex items-center justify-center p-4 sm:p-6">
      <div className="relative w-full max-w-md">
        {/* Logo & Title */}
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center w-16 h-16 bg-gradient-to-br from-blue-600 to-blue-700 rounded-2xl mb-4 shadow-xl">
            <BarChart3 className="w-8 h-8 text-white" />
          </div>
          <h1 className="text-3xl sm:text-4xl mb-2 text-white">Welcome to Kobo</h1>
          <div className="flex items-center justify-center gap-2 text-gray-400">
            <Sparkles className="w-4 h-4 text-blue-400" />
            <p className="text-sm sm:text-base">Employee Satisfaction Analytics Platform</p>
          </div>
        </div>

        {/* Login Card */}
        <div className="bg-gray-800 rounded-3xl p-8 shadow-xl border border-gray-700">
          <form onSubmit={handleSubmit} className="space-y-5">
            {error && (
              <div className="p-4 bg-red-900/20 border border-red-800 rounded-xl flex items-start gap-3">
                <AlertCircle className="w-5 h-5 text-red-400 flex-shrink-0 mt-0.5" />
                <div className="flex-1">
                  <p className="text-sm text-red-300 font-medium">Error</p>
                  <p className="text-sm text-red-400 mt-0.5">{error}</p>
                </div>
              </div>
            )}

            <div>
              <label htmlFor="email" className="block text-sm font-medium text-gray-300 mb-2">
                Email Address
              </label>
              <div className="relative">
                <Mail className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-500" />
                <input
                  id="email"
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="you@company.com"
                  className="w-full pl-12 pr-4 py-3.5 bg-gray-700 border border-gray-600 text-white placeholder-gray-500 rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-400 focus:border-transparent transition-all"
                  required
                />
              </div>
            </div>

            <div>
              <label htmlFor="password" className="block text-sm font-medium text-gray-300 mb-2">
                Password
              </label>
              <div className="relative">
                <Lock className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-500" />
                <input
                  id="password"
                  type="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="••••••••"
                  className="w-full pl-12 pr-4 py-3.5 bg-gray-700 border border-gray-600 text-white placeholder-gray-500 rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-400 focus:border-transparent transition-all"
                  required
                />
              </div>
            </div>

            <button
              type="submit"
              className="w-full py-3.5 bg-gradient-to-r from-blue-600 to-blue-700 text-white rounded-xl font-medium hover:from-blue-700 hover:to-blue-800 transition-all shadow-lg shadow-blue-500/30 hover:shadow-xl hover:shadow-blue-500/40"
            >
              Sign In
            </button>
          </form>

          {/* Demo Accounts */}
          <div className="mt-6 pt-6 border-t border-gray-700">
            <p className="text-sm text-gray-400 text-center mb-3">
              Try demo accounts
            </p>
            <div className="grid grid-cols-2 gap-3">
              <button
                onClick={() => handleDemoLogin('admin')}
                className="px-4 py-3 bg-gray-700 hover:bg-gray-600 text-gray-200 rounded-xl transition-colors text-sm font-medium border border-gray-600"
              >
                Admin Demo
              </button>
              <button
                onClick={() => handleDemoLogin('employee')}
                className="px-4 py-3 bg-gray-700 hover:bg-gray-600 text-gray-200 rounded-xl transition-colors text-sm font-medium border border-gray-600"
              >
                Employee Demo
              </button>
            </div>
          </div>
        </div>

        {/* Footer */}
        <p className="text-center text-gray-400 text-sm mt-6">
          Powered by Machine Learning Analytics
        </p>
      </div>
    </div>
  );
}

