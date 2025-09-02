import React from 'react';

interface StatusBadgeProps {
  status: 'success' | 'warning' | 'error' | 'info' | 'processing' | 'neutral';
  size?: 'xs' | 's' | 'm' | 'l' | 'xl';
  children: React.ReactNode;
  className?: string;
}

export const StatusBadge: React.FC<StatusBadgeProps> = ({
  status,
  size = 'm',
  children,
  className = '',
}) => {
  const getStatusStyles = (): React.CSSProperties => {
    const baseStyles: React.CSSProperties = {
      display: 'inline-flex',
      alignItems: 'center',
      justifyContent: 'center',
      borderRadius: 'var(--spectrum-border-radius-1000)',
      fontFamily: 'var(--spectrum-font-family-base)',
      fontWeight: 'var(--spectrum-font-weight-medium)',
      textAlign: 'center',
      whiteSpace: 'nowrap',
      userSelect: 'none',
      WebkitUserSelect: 'none',
      MozUserSelect: 'none',
      msUserSelect: 'none',
    };

    // Size styles
    const sizeStyles = {
      xs: {
        padding: 'var(--spectrum-space-25) var(--spectrum-space-50)',
        fontSize: 'var(--spectrum-font-size-50)',
        lineHeight: 'var(--spectrum-line-height-tight)',
        minHeight: 'var(--spectrum-space-200)',
      },
      s: {
        padding: 'var(--spectrum-space-50) var(--spectrum-space-75)',
        fontSize: 'var(--spectrum-font-size-75)',
        lineHeight: 'var(--spectrum-line-height-tight)',
        minHeight: 'var(--spectrum-space-250)',
      },
      m: {
        padding: 'var(--spectrum-space-75) var(--spectrum-space-100)',
        fontSize: 'var(--spectrum-font-size-100)',
        lineHeight: 'var(--spectrum-line-height-tight)',
        minHeight: 'var(--spectrum-space-300)',
      },
      l: {
        padding: 'var(--spectrum-space-100) var(--spectrum-space-150)',
        fontSize: 'var(--spectrum-font-size-200)',
        lineHeight: 'var(--spectrum-line-height-tight)',
        minHeight: 'var(--spectrum-space-350)',
      },
      xl: {
        padding: 'var(--spectrum-space-150) var(--spectrum-space-200)',
        fontSize: 'var(--spectrum-font-size-300)',
        lineHeight: 'var(--spectrum-line-height-tight)',
        minHeight: 'var(--spectrum-space-400)',
      },
    };

    // Status styles
    const statusStyles = {
      success: {
        backgroundColor: 'var(--spectrum-semantic-positive-color)',
        color: 'var(--spectrum-neutral-0)',
        boxShadow: 'var(--spectrum-shadow-100)',
      },
      warning: {
        backgroundColor: 'var(--spectrum-semantic-warning-color)',
        color: 'var(--spectrum-neutral-900)',
        boxShadow: 'var(--spectrum-shadow-100)',
      },
      error: {
        backgroundColor: 'var(--spectrum-semantic-notice-color)',
        color: 'var(--spectrum-neutral-0)',
        boxShadow: 'var(--spectrum-shadow-100)',
      },
      info: {
        backgroundColor: 'var(--spectrum-semantic-informative-color)',
        color: 'var(--spectrum-neutral-0)',
        boxShadow: 'var(--spectrum-shadow-100)',
      },
      processing: {
        backgroundColor: 'var(--spectrum-semantic-background-color-secondary)',
        color: 'var(--spectrum-semantic-informative-color)',
        border: '1px solid var(--spectrum-semantic-informative-color)',
        boxShadow: 'var(--spectrum-shadow-0)',
        position: 'relative' as const,
        overflow: 'hidden',
      },
      neutral: {
        backgroundColor: 'var(--spectrum-semantic-background-color-secondary)',
        color: 'var(--spectrum-semantic-text-color-secondary)',
        border: '1px solid var(--spectrum-semantic-border-color-default)',
        boxShadow: 'var(--spectrum-shadow-0)',
      },
    };

    return {
      ...baseStyles,
      ...sizeStyles[size],
      ...statusStyles[status],
    };
  };

  return (
    <span
      className={className}
      style={getStatusStyles()}
      role="status"
      aria-label={`Status: ${status}`}
    >
      {children}
    </span>
  );
};
