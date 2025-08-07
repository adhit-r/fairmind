'use client';

import { createContext, useContext, ReactNode, useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { createClient } from '@/lib/supabase/client';
import type { User, Session } from '@supabase/supabase-js';

type UserProfile = {
  id: string;
  email: string;
  full_name?: string;
  avatar_url?: string;
  role?: string;
};

type LoginResponse = {
  success: boolean;
  error?: string;
};

type AuthContextType = {
  user: User | null;
  profile: UserProfile | null;
  login: (email: string, password: string) => Promise<LoginResponse>;
  signUp: (email: string, password: string, fullName: string) => Promise<{ error: Error | null }>;
  logout: () => Promise<void>;
  hasPermission: (resourceType: string, resourceId: string, permission: string) => Promise<boolean>;
  loading: boolean;
};

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [profile, setProfile] = useState<UserProfile | null>(null);
  const [loading, setLoading] = useState(true);
  const router = useRouter();
  const supabase = createClient();

  useEffect(() => {
    const { data: { subscription } } = supabase.auth.onAuthStateChange(
      async (event: string, session: Session | null) => {
        const currentUser = session?.user || null;
        setUser(currentUser);

        if (currentUser) {
          // For demo purposes, use mock data
          if (currentUser.email === 'admin@fairmind.ai') {
            setProfile({
              id: currentUser.id,
              email: currentUser.email!,
              full_name: 'Admin User',
              role: 'admin'
            });
          } else if (currentUser.email === 'user@fairmind.ai') {
            setProfile({
              id: currentUser.id,
              email: currentUser.email!,
              full_name: 'Regular User',
              role: 'user'
            });
          }
        } else {
          setProfile(null);
        }
        
        setLoading(false);
      }
    );

    return () => {
      subscription.unsubscribe();
    };
  }, [supabase.auth]);

  const login = async (email: string, password: string): Promise<LoginResponse> => {
    try {
      // For demo purposes, use hardcoded credentials
      if (email === 'admin@fairmind.ai' && password === 'password') {
        const { data, error } = await supabase.auth.signInWithPassword({
          email,
          password: 'password', // In a real app, this would be the actual password
        });

        if (error) throw error;
        return { success: true };
      } else if (email === 'user@fairmind.ai' && password === 'password') {
        const { data, error } = await supabase.auth.signInWithPassword({
          email,
          password: 'password', // In a real app, this would be the actual password
        });

        if (error) throw error;
        return { success: true };
      }
      
      return { success: false, error: 'Invalid credentials' };
    } catch (error) {
      console.error('Login failed:', error);
      return { 
        success: false, 
        error: error instanceof Error ? error.message : 'Login failed. Please try again.' 
      };
    }
  };

  const signUp = async (email: string, password: string, fullName: string) => {
    try {
      const { data, error } = await supabase.auth.signUp({
        email,
        password,
        options: {
          data: {
            full_name: fullName,
          },
        },
      });

      if (error) throw error;
      return { error: null };
    } catch (error) {
      console.error('Signup failed:', error);
      return { 
        error: error instanceof Error ? error : new Error('Signup failed') 
      };
    }
  };

  const logout = async () => {
    try {
      await supabase.auth.signOut();
      setUser(null);
      setProfile(null);
      router.push('/login');
    } catch (error) {
      console.error('Logout failed:', error);
    }
  };

  const hasPermission = async (resourceType: string, resourceId: string, permission: string) => {
    if (!user || !profile) return false;
    
    // Admin has all permissions
    if (profile.role === 'admin') return true;
    
    // For demo purposes, allow view permission to all authenticated users
    if (permission === 'view') return true;
    
    // In a real app, you would check the permission using AuthZed
    // return await checkPermission(resourceType, resourceId, permission, user.id);
    return false;
  };

  const value = {
    user,
    profile,
    login,
    signUp,
    logout,
    hasPermission,
    loading,
  };

  return <AuthContext.Provider value={value}>{!loading && children}</AuthContext.Provider>;
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}
