import { useState, useEffect, createContext, useContext } from 'react';

const AuthContext = createContext(null);

// Mock user storage - replace with your backend API calls
const STORAGE_KEY = 'risksense_user';

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Check for existing session on mount
    const storedUser = localStorage.getItem(STORAGE_KEY);
    if (storedUser) {
      setUser(JSON.parse(storedUser));
    }
    setLoading(false);
  }, []);

  const signUp = async (email, password, fullName) => {
    // TODO: Replace with your backend API call
    // Example: const response = await fetch('/api/auth/signup', { method: 'POST', body: JSON.stringify({ email, password, fullName }) });
    
    const mockUser = {
      id: crypto.randomUUID(),
      email,
      fullName,
      createdAt: new Date().toISOString(),
    };
    
    localStorage.setItem(STORAGE_KEY, JSON.stringify(mockUser));
    setUser(mockUser);
    return { user: mockUser, error: null };
  };

  const signIn = async (email, password) => {
    // TODO: Replace with your backend API call
    // Example: const response = await fetch('/api/auth/signin', { method: 'POST', body: JSON.stringify({ email, password }) });
    
    const mockUser = {
      id: crypto.randomUUID(),
      email,
      fullName: email.split('@')[0],
      createdAt: new Date().toISOString(),
    };
    
    localStorage.setItem(STORAGE_KEY, JSON.stringify(mockUser));
    setUser(mockUser);
    return { user: mockUser, error: null };
  };

  const signOut = async () => {
    // TODO: Replace with your backend API call
    // Example: await fetch('/api/auth/signout', { method: 'POST' });
    
    localStorage.removeItem(STORAGE_KEY);
    setUser(null);
  };

  return (
    <AuthContext.Provider value={{ user, loading, signUp, signIn, signOut }}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};
