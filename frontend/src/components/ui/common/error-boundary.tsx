import React from 'react';
import { Alert, AlertDescription } from '@/components/ui/common/alert';
import { AlertTriangle, RefreshCw } from 'lucide-react';
import { Button } from '@/components/ui/common/button';

interface ErrorBoundaryProps {
  error?: string | null;
  onRetry?: () => void;
  fallback?: React.ReactNode;
  children?: React.ReactNode;
}

export function ErrorBoundary({ 
  error, 
  onRetry, 
  fallback,
  children 
}: ErrorBoundaryProps) {
  if (error) {
    if (fallback) {
      return <>{fallback}</>;
    }
    
    return (
      <Alert variant="destructive">
        <AlertTriangle className="h-4 w-4" />
        <AlertDescription className="flex items-center justify-between">
          <span>{error}</span>
          {onRetry && (
            <Button
              variant="outline"
              size="sm"
              onClick={onRetry}
              className="ml-2"
            >
              <RefreshCw className="h-3 w-3 mr-1" />
              Retry
            </Button>
          )}
        </AlertDescription>
      </Alert>
    );
  }

  return <>{children}</>;
}

export function DefaultErrorFallback({ error, onRetry }: { error: string; onRetry?: () => void }) {
  return (
    <div className="flex flex-col items-center justify-center p-8 text-center">
      <AlertTriangle className="h-12 w-12 text-red-500 mb-4" />
      <h3 className="text-lg font-semibold mb-2">Something went wrong</h3>
      <p className="text-muted-foreground mb-4">{error}</p>
      {onRetry && (
        <Button onClick={onRetry} variant="outline">
          <RefreshCw className="h-4 w-4 mr-2" />
          Try Again
        </Button>
      )}
    </div>
  );
}
