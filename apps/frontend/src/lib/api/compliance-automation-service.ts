import { apiClient, type ApiResponse } from './api-client'

export interface ComplianceSchedule {
    id: string
    framework: string
    frequency: string
    recipients: string[]
    last_run: string | null
    next_run: string | null
    is_active: boolean
}

export interface ComplianceViolation {
    id: string
    model_id: string
    framework: string
    violation_type: string
    severity: 'low' | 'medium' | 'high' | 'critical'
    description: string
    detected_at: string
}

export interface ScheduleCreateRequest {
    framework: string
    frequency: string
    recipients: string[]
    filters?: Record<string, any>
}

export interface ComplianceAutomationService {
    createSchedule(data: ScheduleCreateRequest): Promise<ApiResponse<ComplianceSchedule>>
    listSchedules(): Promise<ApiResponse<ComplianceSchedule[]>>
    checkCompliance(modelId: string): Promise<ApiResponse<ComplianceViolation[]>>
    listViolations(): Promise<ApiResponse<ComplianceViolation[]>>
}

class ComplianceAutomationServiceImpl implements ComplianceAutomationService {
    async createSchedule(data: ScheduleCreateRequest): Promise<ApiResponse<ComplianceSchedule>> {
        return apiClient.post<ComplianceSchedule>('/api/v1/compliance/schedules', data)
    }

    async listSchedules(): Promise<ApiResponse<ComplianceSchedule[]>> {
        return apiClient.get<ComplianceSchedule[]>('/api/v1/compliance/schedules')
    }

    async checkCompliance(modelId: string): Promise<ApiResponse<ComplianceViolation[]>> {
        return apiClient.post<ComplianceViolation[]>('/api/v1/compliance/check', { model_id: modelId })
    }

    async listViolations(): Promise<ApiResponse<ComplianceViolation[]>> {
        return apiClient.get<ComplianceViolation[]>('/api/v1/compliance/violations')
    }
}

export const complianceAutomationService = new ComplianceAutomationServiceImpl()
