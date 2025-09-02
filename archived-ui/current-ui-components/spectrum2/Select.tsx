import React from 'react';

interface SelectOption {
  value: string;
  label: string;
  disabled?: boolean;
}

interface SelectProps {
  options: SelectOption[];
  value?: string;
  onChange?: (e: React.ChangeEvent<HTMLSelectElement>) => void;
  disabled?: boolean;
  required?: boolean;
  label?: string;
  placeholder?: string;
  error?: string;
  className?: string;
  id?: string;
}

export const Select: React.FC<SelectProps> = ({
  options,
  value,
  onChange,
  disabled = false,
  required = false,
  label,
  placeholder,
  error,
  className = '',
  id,
}) => {
  const selectId = id || `select-${Math.random().toString(36).substr(2, 9)}`;

  return (
    <div className={`spectrum-field ${className}`}>
      {label && (
        <label htmlFor={selectId} className="spectrum-field-label">
          {label}
          {required && <span className="spectrum-required">*</span>}
        </label>
      )}
      <select
        id={selectId}
        value={value}
        onChange={onChange}
        disabled={disabled}
        required={required}
        className={`spectrum-picker ${error ? 'spectrum-picker-error' : ''}`}
      >
        {placeholder && (
          <option value="" disabled>
            {placeholder}
          </option>
        )}
        {options.map((option) => (
          <option
            key={option.value}
            value={option.value}
            disabled={option.disabled}
          >
            {option.label}
          </option>
        ))}
      </select>
      {error && (
        <div className="spectrum-field-error">
          {error}
        </div>
      )}
    </div>
  );
};
