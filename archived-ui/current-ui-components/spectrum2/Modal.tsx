import React, { useEffect } from 'react';

interface ModalProps {
  isOpen: boolean;
  onClose: () => void;
  title?: string;
  children: React.ReactNode;
  size?: 'sm' | 'md' | 'lg' | 'xl';
  className?: string;
}

export const Modal: React.FC<ModalProps> = ({
  isOpen,
  onClose,
  title,
  children,
  size = 'md',
  className = '',
}) => {
  useEffect(() => {
    if (isOpen) {
      document.body.style.overflow = 'hidden';
    } else {
      document.body.style.overflow = 'unset';
    }

    return () => {
      document.body.style.overflow = 'unset';
    };
  }, [isOpen]);

  const sizeClasses = {
    sm: 'max-w-md',
    md: 'max-w-lg',
    lg: 'max-w-2xl',
    xl: 'max-w-4xl',
  };

  if (!isOpen) return null;

  return (
    <div className="spectrum-overlay">
      <div className="spectrum-backdrop" onClick={onClose} />
      <div className={`spectrum-modal ${sizeClasses[size]} ${className}`}>
        {title && (
          <div className="spectrum-modal-header">
            <h2 className="spectrum-heading spectrum-heading--size-m">
              {title}
            </h2>
            <button
              className="spectrum-button spectrum-button--ghost spectrum-button--size-s"
              onClick={onClose}
              aria-label="Close modal"
            >
              <svg className="spectrum-icon spectrum-icon--size-s" viewBox="0 0 36 36">
                <path d="M19.41 18l8.29-8.29a1 1 0 0 0-1.41-1.41L18 16.59l-8.29-8.29a1 1 0 0 0-1.41 1.41L16.59 18l-8.29 8.29a1 1 0 1 0 1.41 1.41L18 19.41l8.29 8.29a1 1 0 0 0 1.41-1.41L19.41 18z"/>
              </svg>
            </button>
          </div>
        )}
        <div className="spectrum-modal-body">
          {children}
        </div>
      </div>
    </div>
  );
};
