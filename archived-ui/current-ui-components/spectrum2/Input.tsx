import React from 'react';

interface InputProps {
  type?: 'text' | 'email' | 'password' | 'number' | 'file';
  placeholder?: string;
  value?: string;
  onChange?: (e: React.ChangeEvent<HTMLInputElement>) => void;
  disabled?: boolean;
  required?: boolean;
  label?: string;
  error?: string;
  className?: string;
  id?: string;
}

export const Input: React.FC<InputProps> = ({
  type = 'text',
  placeholder,
  value,
  onChange,
  disabled = false,
  required = false,
  label,
  error,
  className = '',
  id,
}) => {
  const inputId = id || `input-${Math.random().toString(36).substr(2, 9)}`;

  return (
    <div className={`spectrum-field ${className}`}>
      {label && (
        <label htmlFor={inputId} className="spectrum-field-label">
          {label}
          {required && <span className="spectrum-required">*</span>}
        </label>
      )}
      <input
        id={inputId}
        type={type}
        placeholder={placeholder}
        value={value}
        onChange={onChange}
        disabled={disabled}
        required={required}
        className={`spectrum-textfield ${error ? 'spectrum-textfield-error' : ''}`}
      />
      {error && (
        <div className="spectrum-field-error">
          {error}
        </div>
      )}
    </div>
  );
};
