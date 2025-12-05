/**
 * Model Upload Hook
 * Handles model file upload with progress tracking
 */

import { useState } from 'react';
import { apiClient } from './api-client';

export interface ModelUploadOptions {
    name?: string;
    description?: string;
    modelType?: string;
    version?: string;
}

export interface UploadProgress {
    loaded: number;
    total: number;
    percentage: number;
}

export function useModelUpload() {
    const [uploading, setUploading] = useState(false);
    const [progress, setProgress] = useState<UploadProgress | null>(null);
    const [error, setError] = useState<string | null>(null);

    const uploadModel = async (file: File, options?: ModelUploadOptions) => {
        setUploading(true);
        setError(null);
        setProgress(null);

        try {
            const formData = new FormData();
            formData.append('file', file);

            if (options?.name) formData.append('name', options.name);
            if (options?.description) formData.append('description', options.description);
            if (options?.modelType) formData.append('model_type', options.modelType);
            if (options?.version) formData.append('version', options.version);

            const response = await apiClient.post('/api/v1/models/upload', formData, {
                headers: {
                    'Content-Type': 'multipart/form-data',
                },
                onUploadProgress: (progressEvent) => {
                    if (progressEvent.total) {
                        const percentage = Math.round(
                            (progressEvent.loaded * 100) / progressEvent.total
                        );
                        setProgress({
                            loaded: progressEvent.loaded,
                            total: progressEvent.total,
                            percentage,
                        });
                    }
                },
            });

            setUploading(false);
            return response.data;
        } catch (err: any) {
            const errorMessage = err.response?.data?.detail || 'Upload failed';
            setError(errorMessage);
            setUploading(false);
            throw new Error(errorMessage);
        }
    };

    const reset = () => {
        setUploading(false);
        setProgress(null);
        setError(null);
    };

    return {
        uploadModel,
        uploading,
        progress,
        error,
        reset,
    };
}
