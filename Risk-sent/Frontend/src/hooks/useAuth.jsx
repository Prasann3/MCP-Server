import { dataTagErrorSymbol } from '@tanstack/react-query';
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

  const signUp = async (email, password, full_name) => {
    // TODO: Replace with your backend API call
    // Example: const response = await fetch('/api/auth/signup', { method: 'POST', body: JSON.stringify({ email, password, full_name }) });
    
      const res = await fetch("http://127.0.0.1:8000/api/v1/users/" , {
        method: "POST",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify({
          email,
          password ,
          full_name
        })
      })

      const data = await res.json()      
      const user = {
         "full_name" : data.full_name ,
         "email" : data.email
      }
    setUser(user)
    return { user , error: null };
  };

  const signIn = async (email, password) => {

    try {
      const res = await fetch("http://127.0.0.1:8000/api/v1/users/login" , {
        method: "POST",
        headers: {
          "Content-Type": "application/json"
        },
        credentials : "include"
        ,
        body: JSON.stringify({
          email,
          password ,
        })
      })
      if (!res.ok) {
        const errorBody = await res.json().catch(() => null);
        throw new Error(errorBody?.detail || `HTTP ${res.status}`);
      }
      
      const data = await res.json()      
      const user = {
        "full_name" : data.full_name ,
        "email" : data.email
      }
      setUser(user)
      return { user , error: null };
    }
    catch(err) {
         return {error : err}
    }

  };

  const signOut = async () => {
    // TODO: Replace with your backend API call
    // Example: await fetch('/api/auth/signout', { method: 'POST' });
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
