import React from 'react';
import { useMlops } from '@/lib/api/hooks/useMlops';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { RefreshCw, ExternalLink, CheckCircle, XCircle, AlertCircle } from 'lucide-react';

export function MlopsSettings() {
    const { status, isLoading, error, refetch } = useMlops();

    if (isLoading && !status) {
        return (
            <Card>
                <CardHeader>
                    <CardTitle>MLOps Integration</CardTitle>
                    <CardDescription>Loading configuration status...</CardDescription>
                </CardHeader>
            </Card>
        );
    }

    if (error) {
        return (
            <Card className="border-red-200 bg-red-50 dark:bg-red-900/10">
                <CardHeader>
                    <div className="flex items-center gap-2 text-red-600 dark:text-red-400">
                        <AlertCircle className="h-5 w-5" />
                        <CardTitle>Connection Error</CardTitle>
                    </div>
                    <CardDescription className="text-red-600/80 dark:text-red-400/80">
                        {error}
                    </CardDescription>
                </CardHeader>
                <CardContent>
                    <Button variant="neutral" onClick={() => refetch()} className="mt-2">
                        <RefreshCw className="mr-2 h-4 w-4" />
                        Retry Connection
                    </Button>
                </CardContent>
            </Card>
        );
    }

    return (
        <div className="space-y-6">
            <div className="flex items-center justify-between">
                <div>
                    <h2 className="text-2xl font-bold tracking-tight">MLOps Integration</h2>
                    <p className="text-muted-foreground">
                        Configure external experiment tracking platforms
                    </p>
                </div>
                <Button variant="neutral" size="sm" onClick={() => refetch()} disabled={isLoading}>
                    <RefreshCw className={`mr-2 h-4 w-4 ${isLoading ? 'animate-spin' : ''}`} />
                    Refresh Status
                </Button>
            </div>

            <div className="grid gap-6 md:grid-cols-2">
                {/* Weights & Biases Card */}
                <Card className={status?.wandb.enabled ? 'border-green-200 bg-green-50/30 dark:border-green-900/50 dark:bg-green-900/10' : ''}>
                    <CardHeader className="flex flex-row items-start justify-between space-y-0 pb-2">
                        <div className="space-y-1">
                            <CardTitle className="text-base font-semibold">Weights & Biases</CardTitle>
                            <CardDescription>Cloud experiment tracking</CardDescription>
                        </div>
                        {status?.wandb.enabled ? (
                            <Badge variant="default" className="bg-green-600 hover:bg-green-700">Connected</Badge>
                        ) : (
                            <Badge variant="secondary">Not Configured</Badge>
                        )}
                    </CardHeader>
                    <CardContent className="space-y-4 pt-4">
                        {status?.wandb.enabled ? (
                            <>
                                <div className="grid gap-1 text-sm">
                                    <div className="flex items-center justify-between py-1">
                                        <span className="text-muted-foreground">Project</span>
                                        <span className="font-medium">{status.wandb.project}</span>
                                    </div>
                                    <div className="flex items-center justify-between py-1">
                                        <span className="text-muted-foreground">Entity</span>
                                        <span className="font-medium">{status.wandb.entity || 'Default'}</span>
                                    </div>
                                </div>
                                <div className="flex items-center gap-2 text-sm text-green-600 dark:text-green-400">
                                    <CheckCircle className="h-4 w-4" />
                                    <span>Ready to log experiments</span>
                                </div>
                                <Button variant="neutral" className="w-full" asChild>
                                    <a href="https://wandb.ai" target="_blank" rel="noopener noreferrer">
                                        Open Dashboard <ExternalLink className="ml-2 h-4 w-4" />
                                    </a>
                                </Button>
                            </>
                        ) : (
                            <>
                                <div className="rounded-md bg-muted p-3 text-sm text-muted-foreground">
                                    To enable W&B, add your API key to the backend .env file:
                                    <pre className="mt-2 overflow-x-auto rounded bg-background p-2 font-mono text-xs">
                                        MLOPS_PROVIDER=wandb{'\n'}
                                        WANDB_API_KEY=your_key
                                    </pre>
                                </div>
                                <div className="flex items-center gap-2 text-sm text-muted-foreground">
                                    <XCircle className="h-4 w-4" />
                                    <span>Integration disabled</span>
                                </div>
                            </>
                        )}
                    </CardContent>
                </Card>

                {/* MLflow Card */}
                <Card className={status?.mlflow.enabled ? 'border-blue-200 bg-blue-50/30 dark:border-blue-900/50 dark:bg-blue-900/10' : ''}>
                    <CardHeader className="flex flex-row items-start justify-between space-y-0 pb-2">
                        <div className="space-y-1">
                            <CardTitle className="text-base font-semibold">MLflow</CardTitle>
                            <CardDescription>Self-hosted tracking server</CardDescription>
                        </div>
                        {status?.mlflow.enabled ? (
                            <Badge variant="default" className="bg-blue-600 hover:bg-blue-700">Connected</Badge>
                        ) : (
                            <Badge variant="secondary">Not Configured</Badge>
                        )}
                    </CardHeader>
                    <CardContent className="space-y-4 pt-4">
                        {status?.mlflow.enabled ? (
                            <>
                                <div className="grid gap-1 text-sm">
                                    <div className="flex items-center justify-between py-1">
                                        <span className="text-muted-foreground">Tracking URI</span>
                                        <span className="font-medium truncate max-w-[150px]" title={status.mlflow.tracking_uri}>
                                            {status.mlflow.tracking_uri}
                                        </span>
                                    </div>
                                    <div className="flex items-center justify-between py-1">
                                        <span className="text-muted-foreground">Experiment</span>
                                        <span className="font-medium">{status.mlflow.experiment_name}</span>
                                    </div>
                                </div>
                                <div className="flex items-center gap-2 text-sm text-blue-600 dark:text-blue-400">
                                    <CheckCircle className="h-4 w-4" />
                                    <span>Ready to log experiments</span>
                                </div>
                                <Button variant="neutral" className="w-full" asChild>
                                    <a href={status.mlflow.tracking_uri} target="_blank" rel="noopener noreferrer">
                                        Open Dashboard <ExternalLink className="ml-2 h-4 w-4" />
                                    </a>
                                </Button>
                            </>
                        ) : (
                            <>
                                <div className="rounded-md bg-muted p-3 text-sm text-muted-foreground">
                                    To enable MLflow, configure your tracking server in .env:
                                    <pre className="mt-2 overflow-x-auto rounded bg-background p-2 font-mono text-xs">
                                        MLOPS_PROVIDER=mlflow{'\n'}
                                        MLFLOW_TRACKING_URI=http://...
                                    </pre>
                                </div>
                                <div className="flex items-center gap-2 text-sm text-muted-foreground">
                                    <XCircle className="h-4 w-4" />
                                    <span>Integration disabled</span>
                                </div>
                            </>
                        )}
                    </CardContent>
                </Card>
            </div>
        </div>
    );
}
