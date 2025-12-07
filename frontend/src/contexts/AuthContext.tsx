import { createContext, useContext, useState, ReactNode } from 'react';

import { api } from '../api/client';

interface User {
  username: string;
  email: string;
  is_staff: boolean;
  token?: string;
}

interface AuthContextType {
  user: User | null;
  login: (username: string, password: string) => Promise<boolean>;
  logout: () => void;
  isAuthenticated: boolean;
  isLoading: boolean;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(() => {
    // Check local storage on initial load
    const savedUser = localStorage.getItem('user');
    const token = localStorage.getItem('api_token');
    if (savedUser && token) {
      return JSON.parse(savedUser);
    }
    return null;
  });
  const [isLoading, setIsLoading] = useState(false);

  const login = async (username: string, password: string): Promise<boolean> => {
    setIsLoading(true);
    try {
      const response = await api.auth.login({ username, password });
      
      if (response.data.token) {
        const userData: User = {
          username: response.data.user?.username || username,
          email: response.data.user?.email || '',
          is_staff: response.data.user?.is_staff || false,
          token: response.data.token
        };
        
        // Save to state and local storage
        setUser(userData);
        localStorage.setItem('user', JSON.stringify(userData));
        localStorage.setItem('api_token', response.data.token);
        
        return true;
      }
      return false;
    } catch (error) {
      console.error('Login failed:', error);
      return false;
    } finally {
      setIsLoading(false);
    }
  };

  const logout = () => {
    setUser(null);
    localStorage.removeItem('user');
    localStorage.removeItem('api_token');
    api.auth.logout().catch(console.error); // Call backend logout
  };

  return (
    <AuthContext.Provider value={{ user, login, logout, isAuthenticated: !!user, isLoading }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}

