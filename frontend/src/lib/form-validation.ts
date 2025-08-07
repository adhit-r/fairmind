import { FormField, ValidationRule, SelectOption } from '@/types'

export interface ValidationError {
  field: string
  message: string
  type: string
}

export interface ValidationResult {
  isValid: boolean
  errors: ValidationError[]
}

export class FormValidator {
  private fields: FormField[]
  private values: Record<string, any>

  constructor(fields: FormField[], values: Record<string, any>) {
    this.fields = fields
    this.values = values
  }

  validate(): ValidationResult {
    const errors: ValidationError[] = []

    for (const field of this.fields) {
      const value = this.values[field.name]
      const fieldErrors = this.validateField(field, value)
      errors.push(...fieldErrors)
    }

    return {
      isValid: errors.length === 0,
      errors
    }
  }

  private validateField(field: FormField, value: any): ValidationError[] {
    const errors: ValidationError[] = []

    if (!field.validation) return errors

    for (const rule of field.validation) {
      const error = this.validateRule(field, value, rule)
      if (error) {
        errors.push(error)
        break // Stop at first error for this field
      }
    }

    return errors
  }

  private validateRule(field: FormField, value: any, rule: ValidationRule): ValidationError | null {
    switch (rule.type) {
      case 'required':
        if (!value || (typeof value === 'string' && value.trim() === '')) {
          return {
            field: field.name,
            message: rule.message || `${field.label} is required`,
            type: 'required'
          }
        }
        break

      case 'email':
        if (value && !this.isValidEmail(value)) {
          return {
            field: field.name,
            message: rule.message || `${field.label} must be a valid email address`,
            type: 'email'
          }
        }
        break

      case 'min':
        if (value && this.getFieldLength(value) < rule.value!) {
          return {
            field: field.name,
            message: rule.message || `${field.label} must be at least ${rule.value} characters`,
            type: 'min'
          }
        }
        break

      case 'max':
        if (value && this.getFieldLength(value) > rule.value!) {
          return {
            field: field.name,
            message: rule.message || `${field.label} must be no more than ${rule.value} characters`,
            type: 'max'
          }
        }
        break

      case 'pattern':
        if (value && rule.value && !new RegExp(rule.value).test(value)) {
          return {
            field: field.name,
            message: rule.message || `${field.label} format is invalid`,
            type: 'pattern'
          }
        }
        break

      case 'custom':
        if (rule.value && typeof rule.value === 'function') {
          const customResult = rule.value(value, this.values)
          if (customResult !== true) {
            return {
              field: field.name,
              message: rule.message || customResult || `${field.label} validation failed`,
              type: 'custom'
            }
          }
        }
        break
    }

    return null
  }

  private isValidEmail(email: string): boolean {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
    return emailRegex.test(email)
  }

  private getFieldLength(value: any): number {
    if (typeof value === 'string') return value.length
    if (Array.isArray(value)) return value.length
    if (typeof value === 'number') return value.toString().length
    return 0
  }
}

// Predefined validation rules
export const validationRules = {
  required: (message?: string): ValidationRule => ({
    type: 'required',
    message: message || 'This field is required'
  }),

  email: (message?: string): ValidationRule => ({
    type: 'email',
    message: message || 'Please enter a valid email address'
  }),

  minLength: (min: number, message?: string): ValidationRule => ({
    type: 'min',
    value: min,
    message: message || `Must be at least ${min} characters`
  }),

  maxLength: (max: number, message?: string): ValidationRule => ({
    type: 'max',
    value: max,
    message: message || `Must be no more than ${max} characters`
  }),

  pattern: (regex: string, message?: string): ValidationRule => ({
    type: 'pattern',
    value: regex,
    message: message || 'Format is invalid'
  }),

  custom: (validator: (value: any, allValues: Record<string, any>) => boolean | string, message?: string): ValidationRule => ({
    type: 'custom',
    value: validator,
    message: message || 'Validation failed'
  }),

  // AI/ML specific validations
  modelName: (message?: string): ValidationRule => ({
    type: 'pattern',
    value: '^[a-zA-Z0-9_-]+$',
    message: message || 'Model name can only contain letters, numbers, hyphens, and underscores'
  }),

  version: (message?: string): ValidationRule => ({
    type: 'pattern',
    value: '^\\d+\\.\\d+\\.\\d+$',
    message: message || 'Version must be in format X.Y.Z (e.g., 1.0.0)'
  }),

  url: (message?: string): ValidationRule => ({
    type: 'pattern',
    value: '^https?://.+',
    message: message || 'Please enter a valid URL starting with http:// or https://'
  }),

  percentage: (message?: string): ValidationRule => ({
    type: 'custom',
    value: (value: any) => {
      const num = parseFloat(value)
      return !isNaN(num) && num >= 0 && num <= 100
    },
    message: message || 'Percentage must be between 0 and 100'
  }),

  positiveNumber: (message?: string): ValidationRule => ({
    type: 'custom',
    value: (value: any) => {
      const num = parseFloat(value)
      return !isNaN(num) && num > 0
    },
    message: message || 'Must be a positive number'
  }),

  dateInFuture: (message?: string): ValidationRule => ({
    type: 'custom',
    value: (value: any) => {
      const date = new Date(value)
      return date > new Date()
    },
    message: message || 'Date must be in the future'
  }),

  // File validation
  fileSize: (maxSizeMB: number, message?: string): ValidationRule => ({
    type: 'custom',
    value: (value: any) => {
      if (!value || !value.size) return true
      return value.size <= maxSizeMB * 1024 * 1024
    },
    message: message || `File size must be less than ${maxSizeMB}MB`
  }),

  fileType: (allowedTypes: string[], message?: string): ValidationRule => ({
    type: 'custom',
    value: (value: any) => {
      if (!value || !value.type) return true
      return allowedTypes.includes(value.type)
    },
    message: message || `File type must be one of: ${allowedTypes.join(', ')}`
  })
}

// Form field builders for common use cases
export const formFields = {
  // Basic fields
  text: (name: string, label: string, options: Partial<FormField> = {}): FormField => ({
    name,
    label,
    type: 'text',
    required: false,
    ...options
  }),

  email: (name: string, label: string, options: Partial<FormField> = {}): FormField => ({
    name,
    label,
    type: 'email',
    required: false,
    validation: [validationRules.email()],
    ...options
  }),

  password: (name: string, label: string, options: Partial<FormField> = {}): FormField => ({
    name,
    label,
    type: 'password',
    required: false,
    validation: [
      validationRules.minLength(8, 'Password must be at least 8 characters'),
      validationRules.pattern('^(?=.*[a-z])(?=.*[A-Z])(?=.*\\d)', 'Password must contain uppercase, lowercase, and number')
    ],
    ...options
  }),

  number: (name: string, label: string, options: Partial<FormField> = {}): FormField => ({
    name,
    label,
    type: 'number',
    required: false,
    ...options
  }),

  textarea: (name: string, label: string, options: Partial<FormField> = {}): FormField => ({
    name,
    label,
    type: 'textarea',
    required: false,
    ...options
  }),

  select: (name: string, label: string, options: SelectOption[], fieldOptions: Partial<FormField> = {}): FormField => ({
    name,
    label,
    type: 'select',
    required: false,
    options,
    ...fieldOptions
  }),

  checkbox: (name: string, label: string, options: Partial<FormField> = {}): FormField => ({
    name,
    label,
    type: 'checkbox',
    required: false,
    ...options
  }),

  // AI/ML specific fields
  modelName: (name: string, label: string, options: Partial<FormField> = {}): FormField => ({
    name,
    label,
    type: 'text',
    required: false,
    validation: [validationRules.modelName()],
    placeholder: 'e.g., loan-prediction-v1',
    ...options
  }),

  version: (name: string, label: string, options: Partial<FormField> = {}): FormField => ({
    name,
    label,
    type: 'text',
    required: false,
    validation: [validationRules.version()],
    placeholder: 'e.g., 1.0.0',
    ...options
  }),

  percentage: (name: string, label: string, options: Partial<FormField> = {}): FormField => ({
    name,
    label,
    type: 'number',
    required: false,
    validation: [validationRules.percentage()],
    placeholder: '0-100',
    ...options
  }),

  date: (name: string, label: string, options: Partial<FormField> = {}): FormField => ({
    name,
    label,
    type: 'text',
    required: false,
    placeholder: 'YYYY-MM-DD',
    ...options
  }),

  url: (name: string, label: string, options: Partial<FormField> = {}): FormField => ({
    name,
    label,
    type: 'text',
    required: false,
    validation: [validationRules.url()],
    placeholder: 'https://example.com',
    ...options
  }),

  file: (name: string, label: string, allowedTypes: string[], maxSizeMB: number, options: Partial<FormField> = {}): FormField => ({
    name,
    label,
    type: 'text', // Will be handled as file input in component
    required: false,
    validation: [
      validationRules.fileType(allowedTypes),
      validationRules.fileSize(maxSizeMB)
    ],
    ...options
  })
}

// Utility functions
export const getFieldError = (errors: ValidationError[], fieldName: string): string | null => {
  const error = errors.find(e => e.field === fieldName)
  return error ? error.message : null
}

export const hasFieldError = (errors: ValidationError[], fieldName: string): boolean => {
  return errors.some(e => e.field === fieldName)
}

export const clearFieldError = (errors: ValidationError[], fieldName: string): ValidationError[] => {
  return errors.filter(e => e.field !== fieldName)
} 