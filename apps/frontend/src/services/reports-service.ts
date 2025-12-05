import { apiClient } from '@/lib/api/api-client';
import { API_ENDPOINTS } from '@/lib/api/endpoints';

export interface ReportGenerationResponse {
    success: boolean;
    filepath: string;
    filename: string;
}

export interface ReportRequest {
    report_type: 'bias_audit' | 'compliance_cert' | 'model_card';
    model_data: Record<string, any>;
    report_data: Record<string, any>;
}

export const reportsService = {
    async generateReport(request: ReportRequest): Promise<ReportGenerationResponse> {
        // Using the correct endpoint from API_ENDPOINTS or hardcoded if not present yet
        // The backend route is /api/v1/reports/generate (assuming prefixed) or just /reports/generate
        // Based on endpoints.ts, it seems we should add it there, but for now let's use the path directly
        // Backend router prefix is /reports, and main.py likely mounts it under /api/v1
        const response = await apiClient.post<ReportGenerationResponse>('/api/v1/reports/generate', request);

        if (response.success && response.data) {
            return response.data;
        }
        throw new Error(response.error || 'Failed to generate report');
    },

    getDownloadUrl(filename: string): string {
        // Construct the download URL
        // Assuming the backend is on the same host/port proxy or we use the base URL
        // For local dev it's http://localhost:8000/api/v1/reports/download/{filename}
        // But we should use the apiClient's base URL logic if possible, or just relative path
        return `/api/v1/reports/download/${filename}`;
    }
};
