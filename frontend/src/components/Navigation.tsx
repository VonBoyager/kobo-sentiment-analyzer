import { Link, useLocation } from 'react-router-dom';
import { BarChart3, LogOut, User, Menu, X } from 'lucide-react';
import { useAuth } from '../contexts/AuthContext';
import { useState } from 'react';

export function Navigation() {
  const location = useLocation();
  const { user, logout } = useAuth();
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  
  const isActive = (path: string) => location.pathname === path;
  const isAdmin = user?.role === 'admin';
  
  return (
    <nav className="fixed top-0 left-0 right-0 bg-gray-800 border-b border-gray-700 z-50 shadow-sm">
      <div className="max-w-[1400px] mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          <Link to="/" className="flex items-center gap-3 group">
            <div className="w-10 h-10 bg-gradient-to-br from-blue-600 to-blue-700 rounded-xl flex items-center justify-center shadow-sm group-hover:shadow-md transition-shadow">
              <BarChart3 className="w-5 h-5 text-white" />
            </div>
            <span className="text-xl font-semibold text-white hidden sm:block">Kobo</span>
          </Link>
          
          {/* Desktop Navigation */}
          <div className="hidden lg:flex items-center gap-2">
            <Link
              to="/"
              className={`px-4 py-2 rounded-xl text-sm font-medium transition-all ${
                isActive('/') 
                  ? 'bg-blue-600 text-white shadow-sm' 
                  : 'text-gray-200 hover:bg-gray-700'
              }`}
            >
              Dashboard
            </Link>
            
            {!isAdmin && (
              <Link
                to="/questionnaire"
                className={`px-4 py-2 rounded-xl text-sm font-medium transition-all ${
                  isActive('/questionnaire') 
                    ? 'bg-blue-600 text-white shadow-sm' 
                    : 'text-gray-200 hover:bg-gray-700'
                }`}
              >
                Questionnaire
              </Link>
            )}
            
            {isAdmin && (
              <>
                <Link
                  to="/upload"
                  className={`px-4 py-2 rounded-xl text-sm font-medium transition-all ${
                    isActive('/upload') 
                      ? 'bg-blue-600 text-white shadow-sm' 
                      : 'text-gray-200 hover:bg-gray-700'
                  }`}
                >
                  Upload Data
                </Link>
                <Link
                  to="/results"
                  className={`px-4 py-2 rounded-xl text-sm font-medium transition-all ${
                    isActive('/results') 
                      ? 'bg-blue-600 text-white shadow-sm' 
                      : 'text-gray-200 hover:bg-gray-700'
                  }`}
                >
                  Results
                </Link>
              </>
            )}
          </div>

          {/* Desktop User Menu */}
          <div className="hidden lg:flex items-center gap-4">
            <div className="flex items-center gap-3 px-4 py-2 bg-gray-700 rounded-xl">
              <div className="w-8 h-8 bg-gradient-to-br from-blue-600 to-blue-700 rounded-lg flex items-center justify-center">
                <User className="w-4 h-4 text-white" />
              </div>
              <div className="flex items-center gap-2">
                <span className="text-sm font-medium text-white">{user?.name}</span>
                {user?.role === 'admin' && (
                  <span className="px-2 py-0.5 bg-blue-900 text-blue-300 text-xs font-medium rounded-md">
                    Admin
                  </span>
                )}
              </div>
            </div>
            <button
              onClick={logout}
              className="flex items-center gap-2 px-4 py-2 text-sm font-medium text-gray-200 hover:bg-gray-700 rounded-xl transition-colors"
              title="Logout"
            >
              <LogOut className="w-4 h-4" />
              <span>Logout</span>
            </button>
          </div>

          {/* Mobile Menu Button */}
          <div className="lg:hidden flex items-center gap-2">
            <button
              onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
              className="p-2 hover:bg-gray-700 rounded-lg transition-colors"
            >
              {mobileMenuOpen ? <X className="w-6 h-6 text-white" /> : <Menu className="w-6 h-6 text-white" />}
            </button>
          </div>
        </div>

        {/* Mobile Menu */}
        {mobileMenuOpen && (
          <div className="lg:hidden border-t border-gray-700 py-4">
            <div className="space-y-1">
              <Link
                to="/"
                onClick={() => setMobileMenuOpen(false)}
                className={`block px-4 py-3 rounded-xl text-sm font-medium transition-colors ${
                  isActive('/') 
                    ? 'bg-blue-600 text-white' 
                    : 'text-gray-200 hover:bg-gray-700'
                }`}
              >
                Dashboard
              </Link>
              
              {!isAdmin && (
                <Link
                  to="/questionnaire"
                  onClick={() => setMobileMenuOpen(false)}
                  className={`block px-4 py-3 rounded-xl text-sm font-medium transition-colors ${
                    isActive('/questionnaire') 
                      ? 'bg-blue-600 text-white' 
                      : 'text-gray-200 hover:bg-gray-700'
                  }`}
                >
                  Questionnaire
                </Link>
              )}
              
              {isAdmin && (
                <>
                  <Link
                    to="/upload"
                    onClick={() => setMobileMenuOpen(false)}
                    className={`block px-4 py-3 rounded-xl text-sm font-medium transition-colors ${
                      isActive('/upload') 
                        ? 'bg-blue-600 text-white' 
                        : 'text-gray-200 hover:bg-gray-700'
                    }`}
                  >
                    Upload Data
                  </Link>
                  <Link
                    to="/results"
                    onClick={() => setMobileMenuOpen(false)}
                    className={`block px-4 py-3 rounded-xl text-sm font-medium transition-colors ${
                      isActive('/results') 
                        ? 'bg-blue-600 text-white' 
                        : 'text-gray-200 hover:bg-gray-700'
                    }`}
                  >
                    Results
                  </Link>
                </>
              )}
            </div>

            {/* Mobile User Info */}
            <div className="mt-4 pt-4 border-t border-gray-700">
              <div className="flex items-center gap-3 px-4 py-2 mb-2">
                <div className="w-10 h-10 bg-gradient-to-br from-blue-600 to-blue-700 rounded-lg flex items-center justify-center">
                  <User className="w-5 h-5 text-white" />
                </div>
                <div>
                  <div className="text-sm font-medium text-white">{user?.name}</div>
                  {user?.role === 'admin' && (
                    <span className="inline-block mt-1 px-2 py-0.5 bg-blue-900 text-blue-300 text-xs font-medium rounded-md">
                      Admin
                    </span>
                  )}
                </div>
              </div>
              <button
                onClick={() => {
                  logout();
                  setMobileMenuOpen(false);
                }}
                className="w-full flex items-center gap-2 px-4 py-3 text-sm font-medium text-gray-200 hover:bg-gray-700 rounded-xl transition-colors"
              >
                <LogOut className="w-4 h-4" />
                <span>Logout</span>
              </button>
            </div>
          </div>
        )}
      </div>
    </nav>
  );
}

