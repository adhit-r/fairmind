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
  username?: string;
  default_org_id?: string | null;
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

  // Fetch user profile from Supabase
  const fetchUserProfile = async (userId: string) => {
    try {
      const { data, error } = await supabase
        .from('profiles')
        .select('*')
        .eq('id', userId)
        .single();

      if (error) {
        console.error('Error fetching user profile:', error);
        return null;
      }

      return data;
    } catch (error) {
      console.error('Error fetching user profile:', error);
      return null;
    }
  };

  useEffect(() => {
    let isMounted = true;

    // Initial session check so we don't render a blank screen
    (async () => {
      try {
        const { data: { session } } = await supabase.auth.getSession();
        const currentUser = session?.user || null;
        if (!isMounted) return;
        setUser(currentUser);

        if (currentUser) {
          const userProfile = await fetchUserProfile(currentUser.id);
          if (!isMounted) return;
          if (userProfile) {
            setProfile({
              id: String(userProfile.id),
              email: String(currentUser.email!),
              full_name: userProfile.full_name ? String(userProfile.full_name) : undefined,
              avatar_url: userProfile.avatar_url ? String(userProfile.avatar_url) : undefined,
              role: userProfile.role ? String(userProfile.role) : undefined,
              username: userProfile.username ? String(userProfile.username) : undefined,
              default_org_id: userProfile.default_org_id ? String(userProfile.default_org_id) : null,
            });
          } else {
            setProfile({
              id: currentUser.id,
              email: currentUser.email!,
              full_name: currentUser.user_metadata?.full_name,
              role: 'user',
              default_org_id: null,
            });
          }
        } else {
          setProfile(null);
        }
      } finally {
        if (isMounted) setLoading(false);
      }
    })();

    // Subscribe to auth changes
    const { data: { subscription } } = supabase.auth.onAuthStateChange(
      async (_event: string, session: Session | null) => {
        const currentUser = session?.user || null;
        setUser(currentUser);
        if (currentUser) {
          const userProfile = await fetchUserProfile(currentUser.id);
          if (userProfile) {
            setProfile({
              id: String(userProfile.id),
              email: String(currentUser.email!),
              full_name: userProfile.full_name ? String(userProfile.full_name) : undefined,
              avatar_url: userProfile.avatar_url ? String(userProfile.avatar_url) : undefined,
              role: userProfile.role ? String(userProfile.role) : undefined,
              username: userProfile.username ? String(userProfile.username) : undefined,
              default_org_id: userProfile.default_org_id ? String(userProfile.default_org_id) : null,
            });
          } else {
            setProfile({
              id: currentUser.id,
              email: currentUser.email!,
              full_name: currentUser.user_metadata?.full_name,
              role: 'user',
              default_org_id: null,
            });
          }
        } else {
          setProfile(null);
        }
      }
    );

    return () => {
      isMounted = false;
      subscription.unsubscribe();
    };
  }, [supabase]);

  const login = async (email: string, password: string): Promise<LoginResponse> => {
    try {
      const { data, error } = await supabase.auth.signInWithPassword({
        email,
        password,
      });

      if (error) {
        console.error('Login error:', error);
        return { 
          success: false, 
          error: error.message 
        };
      }

      return { success: true };
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
