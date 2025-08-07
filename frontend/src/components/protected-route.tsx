'use client';

import { ReactNode, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/contexts/auth-context';

interface ProtectedRouteProps {
  children: ReactNode;
  requiredRole?: string;
}

export function ProtectedRoute({ children, requiredRole }: ProtectedRouteProps) {
  const { user, loading } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (loading) return;
    
    // Redirect to login if not authenticated
    if (!user) {
      router.push('/login');
      return;
    }

    // If we need to check roles in the future, we can do it here
    // For now, we're just checking if the user is authenticated
    if (requiredRole) {
      // TODO: Implement role-based access control
      console.warn('Role-based access control not yet implemented');
    }
  }, [user, loading, router, requiredRole]);

  if (loading || !user) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-indigo-500"></div>
      </div>
    );
  }

  return <>{children}</>;
}
