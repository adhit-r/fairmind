import React from 'react';

interface CardProps {
  children: React.ReactNode;
  variant?: 'default' | 'quiet' | 'selected' | 'interactive' | 'elevated';
  size?: 'xs' | 's' | 'm' | 'l' | 'xl';
  header?: React.ReactNode;
  footer?: React.ReactNode;
  onClick?: () => void;
  disabled?: boolean;
  className?: string;
}

export const Card: React.FC<CardProps> = ({
  children,
  variant = 'default',
  size = 'm',
  header,
  footer,
  onClick,
  disabled = false,
  className = '',
}) => {
  const getCardStyles = (): React.CSSProperties => {
    const baseStyles: React.CSSProperties = {
      backgroundColor: 'var(--spectrum-semantic-background-color-default)',
      borderRadius: 'var(--spectrum-border-radius-200)',
      border: '1px solid var(--spectrum-semantic-border-color-default)',
      fontFamily: 'var(--spectrum-font-family-base)',
      color: 'var(--spectrum-semantic-text-color-primary)',
      transition: 'all var(--spectrum-transition-duration-200) var(--spectrum-transition-ease)',
      position: 'relative',
      overflow: 'hidden',
      cursor: disabled ? 'not-allowed' : onClick ? 'pointer' : 'default',
    };

    // Size styles
    const sizeStyles = {
      xs: {
        padding: 'var(--spectrum-space-100)',
      },
      s: {
        padding: 'var(--spectrum-space-150)',
      },
      m: {
        padding: 'var(--spectrum-space-200)',
      },
      l: {
        padding: 'var(--spectrum-space-300)',
      },
      xl: {
        padding: 'var(--spectrum-space-400)',
      },
    };

    // Variant styles
    const variantStyles = {
      default: {
        backgroundColor: 'var(--spectrum-semantic-background-color-default)',
        borderColor: 'var(--spectrum-semantic-border-color-default)',
        boxShadow: 'var(--spectrum-shadow-100)',
      },
      quiet: {
        backgroundColor: 'var(--spectrum-semantic-background-color-secondary)',
        borderColor: 'var(--spectrum-semantic-border-color-default)',
        boxShadow: 'var(--spectrum-shadow-0)',
      },
      selected: {
        backgroundColor: 'var(--spectrum-semantic-background-color-secondary)',
        borderColor: 'var(--spectrum-semantic-informative-color)',
        boxShadow: 'var(--spectrum-shadow-200)',
      },
      interactive: {
        backgroundColor: 'var(--spectrum-semantic-background-color-default)',
        borderColor: 'var(--spectrum-semantic-border-color-default)',
        boxShadow: 'var(--spectrum-shadow-100)',
        '&:hover': {
          backgroundColor: 'var(--spectrum-semantic-background-color-secondary)',
          boxShadow: 'var(--spectrum-shadow-200)',
          transform: 'translateY(-1px)',
        },
        '&:active': {
          backgroundColor: 'var(--spectrum-semantic-background-color-tertiary)',
          transform: 'translateY(0)',
        },
      },
      elevated: {
        backgroundColor: 'var(--spectrum-semantic-background-color-default)',
        borderColor: 'var(--spectrum-semantic-border-color-default)',
        boxShadow: 'var(--spectrum-shadow-300)',
        '&:hover': {
          boxShadow: 'var(--spectrum-shadow-400)',
          transform: 'translateY(-2px)',
        },
      },
    };

    return {
      ...baseStyles,
      ...sizeStyles[size],
      ...variantStyles[variant],
    };
  };

  const getHeaderStyles = (): React.CSSProperties => ({
    padding: 'var(--spectrum-space-200) var(--spectrum-space-200) var(--spectrum-space-100) var(--spectrum-space-200)',
    borderBottom: header ? '1px solid var(--spectrum-semantic-border-color-default)' : 'none',
    marginBottom: header ? 'var(--spectrum-space-100)' : '0',
  });

  const getContentStyles = (): React.CSSProperties => ({
    padding: header || footer ? 'var(--spectrum-space-100) var(--spectrum-space-200)' : '0',
  });

  const getFooterStyles = (): React.CSSProperties => ({
    padding: 'var(--spectrum-space-100) var(--spectrum-space-200) var(--spectrum-space-200) var(--spectrum-space-200)',
    borderTop: footer ? '1px solid var(--spectrum-semantic-border-color-default)' : 'none',
    marginTop: footer ? 'var(--spectrum-space-100)' : '0',
    backgroundColor: 'var(--spectrum-semantic-background-color-secondary)',
  });

  const handleClick = (e: React.MouseEvent) => {
    if (!disabled && onClick) {
      onClick();
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' || e.key === ' ') {
      e.preventDefault();
      if (!disabled && onClick) {
        onClick();
      }
    }
  };

  const CardWrapper = onClick ? 'button' : 'div';

  return (
    <CardWrapper
      className={className}
      style={getCardStyles()}
      onClick={handleClick}
      onKeyDown={handleKeyDown}
      disabled={disabled}
      aria-disabled={disabled}
      tabIndex={onClick && !disabled ? 0 : undefined}
      type={onClick ? 'button' : undefined}
    >
      {header && (
        <div style={getHeaderStyles()}>
          {header}
        </div>
      )}
      
      <div style={getContentStyles()}>
        {children}
      </div>
      
      {footer && (
        <div style={getFooterStyles()}>
          {footer}
        </div>
      )}
    </CardWrapper>
  );
};
