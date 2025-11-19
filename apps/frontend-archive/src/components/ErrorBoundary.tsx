import React, { Component, ErrorInfo, ReactNode } from 'react';
import { Card, Text, Button, Stack, Alert, Group } from '@mantine/core';
import { IconAlertTriangle, IconRefresh } from '@tabler/icons-react';

interface Props {
  children: ReactNode;
  fallback?: ReactNode;
  context?: string;
}

interface State {
  hasError: boolean;
  error?: Error;
  errorInfo?: ErrorInfo;
}

class ErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = { hasError: false };
  }

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    this.setState({
      error,
      errorInfo,
    });

    // Log error to console in development
    if (process.env.NODE_ENV === 'development') {
      console.error('ErrorBoundary caught an error:', error, errorInfo);
    }

    // In production, you would send this to an error reporting service
    // Example: Sentry.captureException(error, { contexts: { errorInfo } });
  }

  handleReset = () => {
    this.setState({ hasError: false, error: undefined, errorInfo: undefined });
  };

  render() {
    if (this.state.hasError) {
      // Custom fallback UI
      if (this.props.fallback) {
        return this.props.fallback;
      }

      // Default error UI with brutalist styling
      const brutalistErrorStyle = {
        background: 'var(--color-white)',
        border: '2px solid var(--color-black)',
        borderRadius: 'var(--border-radius-base)',
        boxShadow: 'var(--shadow-brutal)',
        borderColor: 'rgba(239, 68, 68, 0.8)',
      };

      return (
        <Card
          style={brutalistErrorStyle}
          p="xl"
        >
          <Stack gap="md">
            <Alert
              icon={<IconAlertTriangle size={16} />}
              title="Something went wrong"
              color="red"
              variant="light"
            >
              {this.props.context 
                ? `An error occurred in the ${this.props.context} component.`
                : 'An unexpected error occurred.'
              }
            </Alert>

            {process.env.NODE_ENV === 'development' && this.state.error && (
              <Card withBorder p="sm" style={{ fontSize: '12px', fontFamily: 'monospace' }}>
                <Text size="xs" c="red" fw={600}>Error Details:</Text>
                <Text size="xs" c="dimmed">{this.state.error.message}</Text>
                {this.state.errorInfo && (
                  <>
                    <Text size="xs" c="red" fw={600} mt="xs">Stack Trace:</Text>
                    <Text size="xs" c="dimmed" style={{ whiteSpace: 'pre-wrap' }}>
                      {this.state.errorInfo.componentStack}
                    </Text>
                  </>
                )}
              </Card>
            )}

            <Group justify="center">
              <Button
                leftSection={<IconRefresh size={16} />}
                onClick={this.handleReset}
                variant="light"
                color="blue"
              >
                Try Again
              </Button>
              <Button
                variant="outline"
                onClick={() => window.location.reload()}
              >
                Reload Page
              </Button>
            </Group>
          </Stack>
        </Card>
      );
    }

    return this.props.children;
  }
}

export default ErrorBoundary;

// Hook version for functional components
export const useErrorHandler = () => {
  const handleError = (error: Error, errorInfo?: any) => {
    console.error('Error caught by useErrorHandler:', error, errorInfo);
    
    // In production, send to error reporting service
    // Example: Sentry.captureException(error, { extra: errorInfo });
  };

  return { handleError };
};

// Higher-order component for wrapping components with error boundary
export const withErrorBoundary = <P extends object>(
  Component: React.ComponentType<P>,
  context?: string
) => {
  const WrappedComponent = (props: P) => (
    <ErrorBoundary context={context}>
      <Component {...props} />
    </ErrorBoundary>
  );

  WrappedComponent.displayName = `withErrorBoundary(${Component.displayName || Component.name})`;
  
  return WrappedComponent;
};