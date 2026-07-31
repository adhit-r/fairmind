'use client'

import { use, useState } from 'react'
import { apiClient } from '@/lib/api/api-client'
import { API_ENDPOINTS } from '@/lib/api/endpoints'
import { Card } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert'
import { Skeleton } from '@/components/ui/skeleton'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import {
    IconArrowLeft,
    IconAlertTriangle,
    IconDatabase,
    IconDownload,
    IconTrash,
    IconTable,
    IconFileText
} from '@tabler/icons-react'
import Link from 'next/link'
import { useRouter } from 'next/navigation'
import { useToast } from '@/hooks/use-toast'
import { useEffect } from 'react'

interface PageProps {
    params: Promise<{ datasetId: string }>
}

interface DatasetMetadata {
    dataset_id: string
    filename: string
    user_id: string
    rows: number
    columns: string[]
    column_types: Record<string, string>
    file_size_bytes: number
    uploaded_at: string
    metadata: Record<string, any>
    preview: Record<string, any>[]
}

export default function DatasetDetailPage({ params }: PageProps) {
    const { datasetId } = use(params)
    const router = useRouter()
    const { toast } = useToast()
    const [dataset, setDataset] = useState<DatasetMetadata | null>(null)
    const [loading, setLoading] = useState(true)
    const [error, setError] = useState<string | null>(null)
    const [deleting, setDeleting] = useState(false)

    useEffect(() => {
        fetchDataset()
    }, [datasetId])

    const fetchDataset = async () => {
        setLoading(true)
        setError(null)
        try {
            const response = await apiClient.get<DatasetMetadata>(
                API_ENDPOINTS.biasV2.getDataset(datasetId),
                { maxRetries: 2, timeout: 10000 }
            )
            if (response) {
                setDataset(response as any)
            } else {
                setError('Dataset not found')
            }
        } catch (err) {
            setError(err instanceof Error ? err.message : 'Failed to fetch dataset')
        } finally {
            setLoading(false)
        }
    }

    const handleDelete = async () => {
        if (!confirm('Are you sure you want to delete this dataset? This action cannot be undone.')) {
            return
        }

        setDeleting(true)
        try {
            await apiClient.delete(API_ENDPOINTS.biasV2.deleteDataset(datasetId))
            toast({
                title: 'Dataset deleted',
                description: 'Dataset has been deleted successfully',
            })
            router.push('/dashboard/datasets')
        } catch (err) {
            toast({
                title: 'Delete failed',
                description: err instanceof Error ? err.message : 'Failed to delete dataset',
                variant: 'destructive',
            })
        } finally {
            setDeleting(false)
        }
    }

    const formatDate = (dateString: string) => {
        return new Date(dateString).toLocaleDateString('en-US', {
            year: 'numeric',
            month: 'long',
            day: 'numeric',
            hour: '2-digit',
            minute: '2-digit',
        })
    }

    const formatFileSize = (bytes: number) => {
        if (bytes < 1024) return `${bytes} B`
        if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(2)} KB`
        return `${(bytes / (1024 * 1024)).toFixed(2)} MB`
    }

    if (loading) {
        return (
            <div className="space-y-6">
                <Skeleton className="h-10 w-64" />
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                    {[...Array(3)].map((_, i) => (
                        <Skeleton key={i} className="h-32" />
                    ))}
                </div>
                <Skeleton className="h-96" />
            </div>
        )
    }

    if (error || !dataset) {
        return (
            <div className="space-y-6">
                <Link href="/dashboard/datasets">
                    <Button variant="neutral">
                        <IconArrowLeft className="mr-2 h-4 w-4" />
                        Back to Datasets
                    </Button>
                </Link>
                <Alert className="border-2 border-red-500 shadow-brutal">
                    <IconAlertTriangle className="h-4 w-4" />
                    <AlertTitle>Error</AlertTitle>
                    <AlertDescription>{error || 'Dataset not found'}</AlertDescription>
                </Alert>
            </div>
        )
    }

    return (
        <div className="space-y-6">
            {/* Header */}
            <div className="flex items-center justify-between">
                <div className="flex items-center gap-4">
                    <Link href="/dashboard/datasets">
                        <Button variant="neutral" size="sm">
                            <IconArrowLeft className="mr-2 h-4 w-4" />
                            Back
                        </Button>
                    </Link>
                    <div>
                        <h1 className="text-4xl font-bold">{dataset.filename}</h1>
                        <p className="text-muted-foreground mt-1 font-mono text-sm">
                            {datasetId}
                        </p>
                    </div>
                </div>
                <div className="flex gap-2">
                    <Button
                        variant="reverse"
                        onClick={handleDelete}
                        disabled={deleting}
                        className="border-2 border-black shadow-brutal bg-red-500 text-white hover:bg-red-600"
                    >
                        <IconTrash className="mr-2 h-4 w-4" />
                        {deleting ? 'Deleting...' : 'Delete'}
                    </Button>
                </div>
            </div>

            {/* Summary Cards */}
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                <Card className="p-6 border-2 border-black shadow-brutal">
                    <div className="flex items-center gap-3">
                        <IconTable className="h-8 w-8 text-primary" />
                        <div>
                            <div className="text-sm text-muted-foreground">Rows</div>
                            <div className="text-2xl font-bold">{dataset.rows.toLocaleString()}</div>
                        </div>
                    </div>
                </Card>
                <Card className="p-6 border-2 border-black shadow-brutal">
                    <div className="flex items-center gap-3">
                        <IconFileText className="h-8 w-8 text-primary" />
                        <div>
                            <div className="text-sm text-muted-foreground">Columns</div>
                            <div className="text-2xl font-bold">{dataset.columns.length}</div>
                        </div>
                    </div>
                </Card>
                <Card className="p-6 border-2 border-black shadow-brutal">
                    <div className="flex items-center gap-3">
                        <IconDatabase className="h-8 w-8 text-primary" />
                        <div>
                            <div className="text-sm text-muted-foreground">File Size</div>
                            <div className="text-2xl font-bold">{formatFileSize(dataset.file_size_bytes)}</div>
                        </div>
                    </div>
                </Card>
                <Card className="p-6 border-2 border-black shadow-brutal">
                    <div>
                        <div className="text-sm text-muted-foreground mb-2">Uploaded</div>
                        <div className="text-sm font-medium">{formatDate(dataset.uploaded_at)}</div>
                    </div>
                </Card>
            </div>

            {/* Schema */}
            <Card className="p-6 border-2 border-black shadow-brutal">
                <h2 className="text-xl font-bold mb-4">Schema</h2>
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
                    {dataset.columns.map((column) => (
                        <div key={column} className="border-2 border-black p-3 rounded-lg bg-muted">
                            <div className="font-semibold">{column}</div>
                            <Badge variant="secondary" className="mt-1 border border-black text-xs">
                                {dataset.column_types[column] || 'unknown'}
                            </Badge>
                        </div>
                    ))}
                </div>
            </Card>

            {/* Data Preview */}
            <Card className="p-6 border-2 border-black shadow-brutal">
                <h2 className="text-xl font-bold mb-4">Data Preview</h2>
                <div className="overflow-x-auto">
                    <Table>
                        <TableHeader>
                            <TableRow>
                                {dataset.columns.map((column) => (
                                    <TableHead key={column} className="font-bold">
                                        {column}
                                    </TableHead>
                                ))}
                            </TableRow>
                        </TableHeader>
                        <TableBody>
                            {dataset.preview.map((row, idx) => (
                                <TableRow key={idx}>
                                    {dataset.columns.map((column) => (
                                        <TableCell key={column} className="font-mono text-sm">
                                            {String(row[column] ?? 'N/A')}
                                        </TableCell>
                                    ))}
                                </TableRow>
                            ))}
                        </TableBody>
                    </Table>
                </div>
                <p className="text-sm text-muted-foreground mt-4">
                    Showing first {dataset.preview.length} rows of {dataset.rows.toLocaleString()} total rows
                </p>
            </Card>

            {/* Metadata */}
            {dataset.metadata && Object.keys(dataset.metadata).length > 0 && (
                <Card className="p-6 border-2 border-black shadow-brutal">
                    <h2 className="text-xl font-bold mb-4">Metadata</h2>
                    <div className="space-y-2">
                        {Object.entries(dataset.metadata).map(([key, value]) => (
                            <div key={key} className="flex items-start gap-3">
                                <span className="font-semibold min-w-32">{key}:</span>
                                <span className="text-muted-foreground">{String(value)}</span>
                            </div>
                        ))}
                    </div>
                </Card>
            )}

            {/* Actions */}
            <Card className="p-6 border-2 border-black shadow-brutal">
                <h2 className="text-xl font-bold mb-4">Actions</h2>
                <div className="flex gap-3">
                    <Link href={`/dashboard/bias-simple?dataset=${datasetId}`}>
                        <Button variant="default" className="border-2 border-black shadow-brutal">
                            Run Bias Test
                        </Button>
                    </Link>
                </div>
            </Card>
        </div>
    )
}
