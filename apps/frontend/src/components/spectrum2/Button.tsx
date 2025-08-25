import React from 'react';

interface ButtonProps {
  children: React.ReactNode;
  variant?: 'primary' | 'secondary' | 'cta' | 'negative' | 'quiet';
  size?: 'xs' | 's' | 'm' | 'l' | 'xl';
  icon?: React.ReactNode;
  iconPosition?: 'start' | 'end';
  fullWidth?: boolean;
  disabled?: boolean;
  onClick?: () => void;
  type?: 'button' | 'submit' | 'reset';
  className?: string;
}

export const Button: React.FC<ButtonProps> = ({
  children,
  variant = 'primary',
  size = 'm',
  icon,
  iconPosition = 'start',
  fullWidth = false,
  disabled = false,
  onClick,
  type = 'button',
  className = '',
}) => {
  const getButtonStyles = (): React.CSSProperties => {
    const baseStyles: React.CSSProperties = {
      display: 'inline-flex',
      alignItems: 'center',
      justifyContent: 'center',
      gap: icon ? 'var(--spectrum-space-100)' : '0',
      border: 'none',
      borderRadius: 'var(--spectrum-border-radius-100)',
      fontFamily: 'var(--spectrum-font-family-base)',
      fontWeight: 'var(--spectrum-font-weight-medium)',
      textDecoration: 'none',
      cursor: disabled ? 'not-allowed' : 'pointer',
      transition: 'all var(--spectrum-transition-duration-200) var(--spectrum-transition-ease)',
      position: 'relative',
      overflow: 'hidden',
      width: fullWidth ? '100%' : 'auto',
      minWidth: 'fit-content',
      userSelect: 'none',
      WebkitUserSelect: 'none',
      MozUserSelect: 'none',
      msUserSelect: 'none',
    };

    // Size styles
    const sizeStyles = {
      xs: {
        padding: 'var(--spectrum-space-50) var(--spectrum-space-100)',
        fontSize: 'var(--spectrum-font-size-75)',
        lineHeight: 'var(--spectrum-line-height-tight)',
        minHeight: 'var(--spectrum-space-300)',
      },
      s: {
        padding: 'var(--spectrum-space-75) var(--spectrum-space-150)',
        fontSize: 'var(--spectrum-font-size-100)',
        lineHeight: 'var(--spectrum-line-height-tight)',
        minHeight: 'var(--spectrum-space-400)',
      },
      m: {
        padding: 'var(--spectrum-space-100) var(--spectrum-space-200)',
        fontSize: 'var(--spectrum-font-size-200)',
        lineHeight: 'var(--spectrum-line-height-tight)',
        minHeight: 'var(--spectrum-space-500)',
      },
      l: {
        padding: 'var(--spectrum-space-150) var(--spectrum-space-300)',
        fontSize: 'var(--spectrum-font-size-300)',
        lineHeight: 'var(--spectrum-line-height-tight)',
        minHeight: 'var(--spectrum-space-600)',
      },
      xl: {
        padding: 'var(--spectrum-space-200) var(--spectrum-space-400)',
        fontSize: 'var(--spectrum-font-size-400)',
        lineHeight: 'var(--spectrum-line-height-tight)',
        minHeight: 'var(--spectrum-space-700)',
      },
    };

    // Variant styles
    const variantStyles = {
      primary: {
        backgroundColor: disabled 
          ? 'var(--spectrum-neutral-200)' 
          : 'var(--spectrum-semantic-informative-color)',
        color: disabled 
          ? 'var(--spectrum-semantic-text-color-disabled)' 
          : 'var(--spectrum-neutral-0)',
        boxShadow: disabled 
          ? 'var(--spectrum-shadow-0)' 
          : 'var(--spectrum-shadow-100)',
        '&:hover': {
          backgroundColor: disabled 
            ? 'var(--spectrum-neutral-200)' 
            : 'var(--spectrum-semantic-informative-color-hover)',
          boxShadow: disabled 
            ? 'var(--spectrum-shadow-0)' 
            : 'var(--spectrum-shadow-200)',
          transform: disabled ? 'none' : 'translateY(-1px)',
        },
        '&:active': {
          backgroundColor: disabled 
            ? 'var(--spectrum-neutral-200)' 
            : 'var(--spectrum-semantic-informative-color-down)',
          transform: disabled ? 'none' : 'translateY(0)',
        },
      },
      secondary: {
        backgroundColor: disabled 
          ? 'var(--spectrum-neutral-200)' 
          : 'var(--spectrum-semantic-background-color-default)',
        color: disabled 
          ? 'var(--spectrum-semantic-text-color-disabled)' 
          : 'var(--spectrum-semantic-informative-color)',
        border: `1px solid ${disabled 
          ? 'var(--spectrum-neutral-300)' 
          : 'var(--spectrum-semantic-informative-color)'}`,
        boxShadow: disabled 
          ? 'var(--spectrum-shadow-0)' 
          : 'var(--spectrum-shadow-100)',
        '&:hover': {
          backgroundColor: disabled 
            ? 'var(--spectrum-neutral-200)' 
            : 'var(--spectrum-semantic-background-color-secondary)',
          borderColor: disabled 
            ? 'var(--spectrum-neutral-300)' 
            : 'var(--spectrum-semantic-informative-color-hover)',
          color: disabled 
            ? 'var(--spectrum-semantic-text-color-disabled)' 
            : 'var(--spectrum-semantic-informative-color-hover)',
          boxShadow: disabled 
            ? 'var(--spectrum-shadow-0)' 
            : 'var(--spectrum-shadow-200)',
          transform: disabled ? 'none' : 'translateY(-1px)',
        },
        '&:active': {
          backgroundColor: disabled 
            ? 'var(--spectrum-neutral-200)' 
            : 'var(--spectrum-semantic-background-color-tertiary)',
          transform: disabled ? 'none' : 'translateY(0)',
        },
      },
      cta: {
        backgroundColor: disabled 
          ? 'var(--spectrum-neutral-200)' 
          : 'var(--spectrum-semantic-positive-color)',
        color: disabled 
          ? 'var(--spectrum-semantic-text-color-disabled)' 
          : 'var(--spectrum-neutral-0)',
        boxShadow: disabled 
          ? 'var(--spectrum-shadow-0)' 
          : 'var(--spectrum-shadow-200)',
        '&:hover': {
          backgroundColor: disabled 
            ? 'var(--spectrum-neutral-200)' 
            : 'var(--spectrum-semantic-positive-color-hover)',
          boxShadow: disabled 
            ? 'var(--spectrum-shadow-0)' 
            : 'var(--spectrum-shadow-300)',
          transform: disabled ? 'none' : 'translateY(-1px)',
        },
        '&:active': {
          backgroundColor: disabled 
            ? 'var(--spectrum-neutral-200)' 
            : 'var(--spectrum-semantic-positive-color-down)',
          transform: disabled ? 'none' : 'translateY(0)',
        },
      },
      negative: {
        backgroundColor: disabled 
          ? 'var(--spectrum-neutral-200)' 
          : 'var(--spectrum-semantic-notice-color)',
        color: disabled 
          ? 'var(--spectrum-semantic-text-color-disabled)' 
          : 'var(--spectrum-neutral-0)',
        boxShadow: disabled 
          ? 'var(--spectrum-shadow-0)' 
          : 'var(--spectrum-shadow-100)',
        '&:hover': {
          backgroundColor: disabled 
            ? 'var(--spectrum-neutral-200)' 
            : 'var(--spectrum-semantic-notice-color-hover)',
          boxShadow: disabled 
            ? 'var(--spectrum-shadow-0)' 
            : 'var(--spectrum-shadow-200)',
          transform: disabled ? 'none' : 'translateY(-1px)',
        },
        '&:active': {
          backgroundColor: disabled 
            ? 'var(--spectrum-neutral-200)' 
            : 'var(--spectrum-semantic-notice-color-down)',
          transform: disabled ? 'none' : 'translateY(0)',
        },
      },
      quiet: {
        backgroundColor: 'transparent',
        color: disabled 
          ? 'var(--spectrum-semantic-text-color-disabled)' 
          : 'var(--spectrum-semantic-informative-color)',
        boxShadow: 'var(--spectrum-shadow-0)',
        '&:hover': {
          backgroundColor: disabled 
            ? 'transparent' 
            : 'var(--spectrum-semantic-background-color-secondary)',
          color: disabled 
            ? 'var(--spectrum-semantic-text-color-disabled)' 
            : 'var(--spectrum-semantic-informative-color-hover)',
        },
        '&:active': {
          backgroundColor: disabled 
            ? 'transparent' 
            : 'var(--spectrum-semantic-background-color-tertiary)',
        },
      },
    };

    return {
      ...baseStyles,
      ...sizeStyles[size],
      ...variantStyles[variant],
    };
  };

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

  return (
    <button
      type={type}
      className={className}
      style={getButtonStyles()}
      onClick={handleClick}
      onKeyDown={handleKeyDown}
      disabled={disabled}
      aria-disabled={disabled}
      tabIndex={disabled ? -1 : 0}
    >
      {icon && iconPosition === 'start' && (
        <span style={{ display: 'flex', alignItems: 'center' }}>
          {icon}
        </span>
      )}
      <span>{children}</span>
      {icon && iconPosition === 'end' && (
        <span style={{ display: 'flex', alignItems: 'center' }}>
          {icon}
        </span>
      )}
    </button>
  );
};
