'use client';

import { createContext, useContext, ReactNode, useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { createClient } from '@supabase/supabase-js';

type UserProfile = {
  id: string;
  email: string;
  full_name?: string;
  avatar_url?: string;
  role?: string;
  username?: string;
  organization_id?: string | null;
  organization_name?: string;
  onboarding_completed?: boolean;
};

type LoginResponse = {
  success: boolean;
  error?: string;
};

type AuthContextType = {
  user: UserProfile | null;
  login: (email: string, password: string) => Promise<LoginResponse>;
  signUp: (email: string, password: string, fullName: string, organizationName: string) => Promise<{ error: Error | null }>;
  logout: () => Promise<void>;
  updateProfile: (updates: Partial<UserProfile>) => Promise<void>;
  loading: boolean;
};

const AuthContext = createContext<AuthContextType | undefined>(undefined);

// Initialize Supabase client
const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL || 'https://swapkvhzyhcruoyjpkyr.supabase.co';
const supabaseAnonKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY || 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InN3YXBrdmh6eWhjcnVveWpwa3lyIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTM0Njg4NTQsImV4cCI6MjA2OTA0NDg1NH0.ckdz6Kv63Tp4F6iuMhzuTQr8sfMhxpeZVmGzGaf40k8';

const supabase = createClient(supabaseUrl, supabaseAnonKey);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<UserProfile | null>(null);
  const [loading, setLoading] = useState(true);
  const [mounted, setMounted] = useState(false);
  const router = useRouter();

  useEffect(() => {
    setMounted(true);
  }, []);

  useEffect(() => {
    // Check for existing session
    const checkSession = async () => {
      try {
        const { data: { session }, error } = await supabase.auth.getSession();
        
        if (error) {
          console.error('Error getting session:', error);
          setLoading(false);
          return;
        }

        if (session?.user) {
          await loadUserProfile(session.user.id);
        }
      } catch (error) {
        console.error('Error checking session:', error);
      } finally {
        setLoading(false);
      }
    };

    checkSession();

    // Listen for auth changes
    const { data: { subscription } } = supabase.auth.onAuthStateChange(
      async (event, session) => {
        if (event === 'SIGNED_IN' && session?.user) {
          await loadUserProfile(session.user.id);
        } else if (event === 'SIGNED_OUT') {
          setUser(null);
        }
      }
    );

    return () => subscription.unsubscribe();
  }, []);

  const loadUserProfile = async (userId: string) => {
    try {
      const { data: profile, error } = await supabase
        .from('profiles')
        .select('*')
        .eq('id', userId)
        .single();

      if (error) {
        console.error('Error loading user profile:', error);
        return;
      }

      if (profile) {
        const userProfile: UserProfile = {
          id: profile.id,
          email: profile.email || '',
          full_name: profile.full_name,
          avatar_url: profile.avatar_url,
          role: profile.role || 'user',
          username: profile.username,
          organization_id: profile.default_org_id,
          organization_name: profile.organization_name,
          onboarding_completed: profile.is_onboarded || false
        };
        setUser(userProfile);
      }
    } catch (error) {
      console.error('Error loading user profile:', error);
    }
  };

  const login = async (email: string, password: string): Promise<LoginResponse> => {
    try {
      const { data, error } = await supabase.auth.signInWithPassword({
        email,
        password,
      });

      if (error) {
        return { 
          success: false, 
          error: error.message 
        };
      }

      if (data.user) {
        await loadUserProfile(data.user.id);
        return { success: true };
      }

      return { 
        success: false, 
        error: 'Login failed. Please try again.' 
      };
    } catch (error) {
      console.error('Login failed:', error);
      return { 
        success: false, 
        error: error instanceof Error ? error.message : 'Login failed. Please try again.' 
      };
    }
  };

  const signUp = async (email: string, password: string, fullName: string, organizationName: string): Promise<{ error: Error | null }> => {
    try {
      const { data, error } = await supabase.auth.signUp({
        email,
        password,
        options: {
          data: {
            full_name: fullName,
            organization_name: organizationName,
          }
        }
      });

      if (error) {
        return { error: new Error(error.message) };
      }

      if (data.user) {
        // Create profile in profiles table
        const { error: profileError } = await supabase
          .from('profiles')
          .insert([
            {
              id: data.user.id,
              username: email.split('@')[0] + '_' + Math.random().toString(36).substr(2, 8),
              full_name: fullName,
              role: 'user',
              is_onboarded: false
            }
          ]);

        if (profileError) {
          console.error('Error creating profile:', profileError);
        }

        await loadUserProfile(data.user.id);
        return { error: null };
      }

      return { error: new Error('Signup failed') };
    } catch (error) {
      console.error('Signup failed:', error);
      return { 
        error: error instanceof Error ? error : new Error('Signup failed') 
      };
    }
  };

  const logout = async () => {
    try {
      const { error } = await supabase.auth.signOut();
      if (error) {
        console.error('Logout error:', error);
      }
      setUser(null);
      router.push('/login');
    } catch (error) {
      console.error('Logout failed:', error);
    }
  };

  const updateProfile = async (updates: Partial<UserProfile>) => {
    if (!user) return;
    
    try {
      const { error } = await supabase
        .from('profiles')
        .update({
          full_name: updates.full_name,
          avatar_url: updates.avatar_url,
          username: updates.username,
        })
        .eq('id', user.id);

      if (error) {
        console.error('Error updating profile:', error);
        return;
      }

      const updatedUser = { ...user, ...updates };
      setUser(updatedUser);
    } catch (error) {
      console.error('Error updating profile:', error);
    }
  };

  const value = {
    user,
    login,
    signUp,
    logout,
    updateProfile,
    loading,
  };

  return <AuthContext.Provider value={value}>{mounted && !loading && children}</AuthContext.Provider>;
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}
