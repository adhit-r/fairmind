import { useState, useEffect, useCallback } from 'react';
import { apiClient } from '../api-client';
import { API_ENDPOINTS } from '../endpoints';

export interface MlopsStatus {
    provider: string;
    wandb: {
        enabled: boolean;
        project?: string;
        entity?: string;
    };
    mlflow: {
        enabled: boolean;
        tracking_uri?: string;
        experiment_name?: string;
    };
}

export interface MlopsStatusResponse {
    success: boolean;
    status: MlopsStatus;
    enabled: boolean;
}

export interface RunUrlResponse {
    success: boolean;
    provider: string;
    run_id: string;
    url: string;
}

export function useMlops() {
    const [status, setStatus] = useState<MlopsStatus | null>(null);
    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);

    const fetchStatus = useCallback(async () => {
        setIsLoading(true);
        setError(null);
        try {
            const response = await apiClient.get<MlopsStatusResponse>(API_ENDPOINTS.mlops.status);
            if (response.success && response.data) {
                setStatus(response.data.status);
            } else {
                setError(response.error || 'Failed to fetch MLOps status');
            }
        } catch (err) {
            setError(err instanceof Error ? err.message : 'An unknown error occurred');
        } finally {
            setIsLoading(false);
        }
    }, []);

    const getRunUrl = useCallback(async (provider: string, runId: string): Promise<string | null> => {
        try {
            const response = await apiClient.get<RunUrlResponse>(API_ENDPOINTS.mlops.runUrl(provider, runId));
            if (response.success && response.data) {
                return response.data.url;
            }
            return null;
        } catch (err) {
            console.error('Error fetching run URL:', err);
            return null;
        }
    }, []);

    // Initial fetch
    useEffect(() => {
        fetchStatus();
    }, [fetchStatus]);

    return {
        status,
        isLoading,
        error,
        refetch: fetchStatus,
        getRunUrl
    };
}
