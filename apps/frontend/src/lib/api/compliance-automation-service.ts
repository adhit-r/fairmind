/**
 * Compliance Automation API Service
 *
 * Handles all API interactions for compliance automation features:
 * - Schedule management
 * - Violation tracking
 * - Report management
 * - Remediation planning
 * - System status monitoring
 */

import { api } from '@/lib/api/api-client'

// Type definitions
export interface ComplianceSchedule {
    id: string
    framework: string
    frequency: 'daily' | 'weekly' | 'monthly'
    recipients: string[]
    filters?: Record<string, any>
    description?: string
    is_active: boolean
    last_run?: string
    next_run?: string
    created_at: string
    updated_at: string
}

export interface ComplianceViolation {
    id: string
    model_id?: string
    framework: string
    violation_type: string
    severity: 'critical' | 'high' | 'medium' | 'low'
    status: 'open' | 'acknowledged' | 'in_remediation' | 'resolved'
    description?: string
    detected_at: string
    acknowledged_at?: string
    resolved: boolean
    resolved_at?: string
    remediation_plan_id?: string
}

export interface ComplianceReport {
    id: string
    framework: string
    schedule_id?: string
    overall_score: number
    status: string
    report_type: 'pdf' | 'docx' | 'html'
    file_path: string
    file_size: number
    generated_at: string
    expires_at?: string
}

export interface RemediationPlan {
    plan_id: string
    framework: string
    gap_id: string
    gap_description: string
    severity: 'critical' | 'high' | 'medium' | 'low'
    remediation_steps: RemediationStep[]
    estimated_effort_hours: number
    legal_citations: string[]
    success_criteria: string[]
    generated_by: 'ai' | 'manual'
    generated_at: string
}

export interface RemediationStep {
    step_number: number
    action: string
    description: string
    effort_hours?: number
    owner?: string
}

export interface AutomationStatus {
    scheduler_running: boolean
    active_schedules: number
    pending_jobs: number
    total_violations: number
    critical_violations: number
    reports_generated_today: number
    last_scheduler_check: string
}

export interface ScheduleCreateRequest {
    framework: string
    frequency: 'daily' | 'weekly' | 'monthly'
    recipients: string[]
    filters?: Record<string, any>
    description?: string
    is_active?: boolean
}

// Schedule Management APIs
export const scheduleAPI = {
    /**
     * Create a new compliance automation schedule
     */
    create: async (data: ScheduleCreateRequest): Promise<ComplianceSchedule> => {
        return api.post('/api/v1/compliance/schedules', data)
    },

    /**
     * Get list of compliance schedules
     */
    list: async (params?: {
        framework?: string
        is_active?: boolean
        offset?: number
        limit?: number
    }): Promise<{ schedules: ComplianceSchedule[]; total: number; offset: number; limit: number }> => {
        const query = new URLSearchParams()
        if (params?.framework) query.append('framework', params.framework)
        if (params?.is_active !== undefined) query.append('is_active', String(params.is_active))
        if (params?.offset) query.append('offset', String(params.offset))
        if (params?.limit) query.append('limit', String(params.limit))

        return api.get(`/api/v1/compliance/schedules?${query}`)
    },

    /**
     * Get a specific schedule by ID
     */
    get: async (id: string): Promise<ComplianceSchedule> => {
        return api.get(`/api/v1/compliance/schedules/${id}`)
    },

    /**
     * Update a compliance schedule
     */
    update: async (
        id: string,
        data: Partial<{
            frequency: 'daily' | 'weekly' | 'monthly'
            recipients: string[]
            filters: Record<string, any>
            description: string
            is_active: boolean
        }>
    ): Promise<ComplianceSchedule> => {
        return api.put(`/api/v1/compliance/schedules/${id}`, data)
    },

    /**
     * Delete a compliance schedule
     */
    delete: async (id: string): Promise<{ message: string }> => {
        return api.delete(`/api/v1/compliance/schedules/${id}`)
    },

    /**
     * Trigger immediate execution of a schedule
     */
    runNow: async (id: string): Promise<{ message: string; schedule_id: string; triggered_at: string }> => {
        return api.post(`/api/v1/compliance/schedules/${id}/run`, {})
    },
}

// Violation Tracking APIs
export const violationAPI = {
    /**
     * Get list of compliance violations
     */
    list: async (params?: {
        framework?: string
        severity?: 'critical' | 'high' | 'medium' | 'low'
        status?: 'open' | 'acknowledged' | 'in_remediation' | 'resolved'
        model_id?: string
        offset?: number
        limit?: number
    }): Promise<{ violations: ComplianceViolation[]; total: number; offset: number; limit: number }> => {
        const query = new URLSearchParams()
        if (params?.framework) query.append('framework', params.framework)
        if (params?.severity) query.append('severity', params.severity)
        if (params?.status) query.append('status', params.status)
        if (params?.model_id) query.append('model_id', params.model_id)
        if (params?.offset) query.append('offset', String(params.offset))
        if (params?.limit) query.append('limit', String(params.limit))

        return api.get(`/api/v1/compliance/violations?${query}`)
    },

    /**
     * Get a specific violation by ID
     */
    get: async (id: string): Promise<ComplianceViolation> => {
        return api.get(`/api/v1/compliance/violations/${id}`)
    },

    /**
     * Acknowledge a compliance violation
     */
    acknowledge: async (id: string, notes?: string): Promise<ComplianceViolation> => {
        return api.patch(`/api/v1/compliance/violations/${id}/acknowledge`, { notes })
    },
}

// Report Management APIs
export const reportAPI = {
    /**
     * Get list of generated compliance reports
     */
    list: async (params?: {
        framework?: string
        offset?: number
        limit?: number
    }): Promise<{ reports: ComplianceReport[]; total: number; offset: number; limit: number }> => {
        const query = new URLSearchParams()
        if (params?.framework) query.append('framework', params.framework)
        if (params?.offset) query.append('offset', String(params.offset))
        if (params?.limit) query.append('limit', String(params.limit))

        return api.get(`/api/v1/compliance/reports?${query}`)
    },

    /**
     * Get a specific report by ID
     */
    get: async (id: string): Promise<ComplianceReport> => {
        return api.get(`/api/v1/compliance/reports/${id}`)
    },

    /**
     * Download a compliance report
     */
    download: async (id: string): Promise<Blob> => {
        const response = await fetch(`/api/v1/compliance/reports/${id}/download`)
        if (!response.ok) throw new Error('Failed to download report')
        return response.blob()
    },
}

// Remediation APIs
export const remediationAPI = {
    /**
     * Get AI-generated remediation plan for a compliance gap
     */
    generatePlan: async (data: {
        framework: string
        gap_id: string
        model_id?: string
    }): Promise<RemediationPlan> => {
        return api.post('/api/v1/compliance/gap-remediation', data)
    },
}

// System Status API
export const statusAPI = {
    /**
     * Get compliance automation system status
     */
    get: async (): Promise<AutomationStatus> => {
        return api.get('/api/v1/compliance/status')
    },
}

// Utility functions
export const complianceUtils = {
    /**
     * Format date for display
     */
    formatDate: (dateString: string): string => {
        const date = new Date(dateString)
        return date.toLocaleDateString('en-US', {
            year: 'numeric',
            month: 'short',
            day: 'numeric',
        })
    },

    /**
     * Format datetime for display
     */
    formatDateTime: (dateString: string): string => {
        const date = new Date(dateString)
        return date.toLocaleString('en-US', {
            year: 'numeric',
            month: 'short',
            day: 'numeric',
            hour: '2-digit',
            minute: '2-digit',
        })
    },

    /**
     * Get severity badge color
     */
    getSeverityColor: (severity: string): string => {
        const colors: Record<string, string> = {
            critical: 'bg-red-100 border-red-600 text-red-800',
            high: 'bg-orange-100 border-orange-600 text-orange-800',
            medium: 'bg-yellow-100 border-yellow-600 text-yellow-800',
            low: 'bg-green-100 border-green-600 text-green-800',
        }
        return colors[severity.toLowerCase()] || 'bg-gray-100 border-gray-600 text-gray-800'
    },

    /**
     * Get status badge color
     */
    getStatusColor: (status: string): string => {
        const colors: Record<string, string> = {
            compliant: 'text-green-600',
            partial: 'text-yellow-600',
            non_compliant: 'text-red-600',
        }
        return colors[status.toLowerCase()] || 'text-gray-600'
    },

    /**
     * Parse frequency display name
     */
    formatFrequency: (frequency: string): string => {
        const names: Record<string, string> = {
            daily: 'Daily',
            weekly: 'Weekly',
            monthly: 'Monthly',
        }
        return names[frequency.toLowerCase()] || frequency
    },
}

// Legacy service for backward compatibility
export const complianceAutomationService = {
    createSchedule: scheduleAPI.create,
    listSchedules: () => scheduleAPI.list().then(r => ({ data: r.schedules })),
    checkCompliance: (modelId: string) => violationAPI.list({ model_id: modelId }),
    listViolations: () => violationAPI.list(),
}
