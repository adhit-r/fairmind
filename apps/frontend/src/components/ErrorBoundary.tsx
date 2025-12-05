'use client'

import React from 'react'
import { Card } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert'
import { IconAlertTriangle, IconRefresh } from '@tabler/icons-react'

interface ErrorBoundaryState {
  hasError: boolean
  error: Error | null
}

interface ErrorBoundaryProps {
  children: React.ReactNode
  fallback?: React.ReactNode
}

export class ErrorBoundary extends React.Component<ErrorBoundaryProps, ErrorBoundaryState> {
  constructor(props: ErrorBoundaryProps) {
    super(props)
    this.state = { hasError: false, error: null }
  }

  static getDerivedStateFromError(error: Error): ErrorBoundaryState {
    return { hasError: true, error }
  }

  componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
    console.error('ErrorBoundary caught an error:', error, errorInfo)
  }

  handleReset = () => {
    this.setState({ hasError: false, error: null })
    window.location.reload()
  }

  render() {
    if (this.state.hasError) {
      if (this.props.fallback) {
        return this.props.fallback
      }

      // Don't show error boundary for API errors - they're handled gracefully
      const errorMessage = this.state.error?.message || ''
      if (errorMessage.includes('API') || errorMessage.includes('fetch') || errorMessage.includes('network')) {
        // Silently recover - API errors are handled by components
        this.setState({ hasError: false, error: null })
        return this.props.children
      }

      return (
        <div className="min-h-screen flex items-center justify-center p-4 bg-gray-50">
          <Card className="w-full max-w-md p-6 border-2 border-black shadow-brutal">
            <Alert variant="destructive" className="mb-4 border-2 border-red-500 shadow-brutal">
              <IconAlertTriangle className="h-4 w-4" />
              <AlertTitle>Something went wrong</AlertTitle>
              <AlertDescription>
                {errorMessage || 'An unexpected error occurred'}
              </AlertDescription>
            </Alert>
            <div className="space-y-4">
              <p className="text-sm text-muted-foreground">
                The application encountered an error. Please try refreshing the page.
              </p>
              <Button onClick={this.handleReset} className="w-full border-2 border-black shadow-brutal">
                <IconRefresh className="mr-2 h-4 w-4" />
                Reload Page
              </Button>
            </div>
          </Card>
        </div>
      )
    }

    return this.props.children
  }
}

