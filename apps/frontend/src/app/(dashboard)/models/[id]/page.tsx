'use client'

import { use, useState } from 'react'
import { useModel } from '@/lib/api/hooks/useModel'
import { useDatasets } from '@/lib/api/hooks/useDatasets'
import { Card } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Skeleton } from '@/components/ui/skeleton'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { Progress } from '@/components/ui/progress'
import { Separator } from '@/components/ui/separator'
import {
    Dialog,
    DialogContent,
    DialogDescription,
    DialogFooter,
    DialogHeader,
    DialogTitle,
    DialogTrigger,
} from "@/components/ui/dialog"
import {
    Select,
    SelectContent,
    SelectItem,
    SelectTrigger,
    SelectValue,
} from "@/components/ui/select"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import {
    IconBrain,
    IconActivity,
    IconScale,
    IconAlertTriangle,
    IconCheck,
    IconX,
    IconArrowLeft,
    IconTestPipe,
    IconDatabase
} from '@tabler/icons-react'
import Link from 'next/link'
import { ModelEnvironmentalPanel } from '@/components/environmental/ModelEnvironmentalPanel'
import {
    BarChart,
    Bar,
    XAxis,
    YAxis,
    CartesianGrid,
    Tooltip,
    ResponsiveContainer,
    Cell
} from 'recharts'

// Next.js 16 delivers route params as a Promise; reading a property off it
// directly yields undefined, so the model was never fetched. Sibling dynamic
// routes already unwrap with use().
export default function ModelDetailsPage({ params }: { params: Promise<{ id: string }> }) {
    const { id } = use(params)
    const { model, loading, error, runTest, testing, testResult, testError } = useModel(id)
    const { datasets, loading: loadingDatasets } = useDatasets()
    const [dialogOpen, setDialogOpen] = useState(false)

    // Test Config State
    const [selectedDatasetId, setSelectedDatasetId] = useState<string>('')
    const [targetColumn, setTargetColumn] = useState('')
    const [sensitiveAttributes, setSensitiveAttributes] = useState('')

    const handleRunTest = async () => {
        if (selectedDatasetId) {
            await runTest({
                dataset_id: selectedDatasetId,
                target_column: targetColumn,
                sensitive_attributes: sensitiveAttributes.split(',').map(s => s.trim()).filter(s => s)
            })
        } else {
            // Run with synthetic data
            await runTest()
        }
        setDialogOpen(false)
    }

    if (loading) {
        return (
            <div className="space-y-6">
                <div className="flex items-center gap-4">
                    <Skeleton className="h-10 w-10 rounded-full" />
                    <div className="space-y-2">
                        <Skeleton className="h-8 w-64" />
                        <Skeleton className="h-4 w-32" />
                    </div>
                </div>
                <div className="grid grid-cols-3 gap-6">
                    <Skeleton className="h-32" />
                    <Skeleton className="h-32" />
                    <Skeleton className="h-32" />
                </div>
                <Skeleton className="h-96" />
            </div>
        )
    }

    if (error || !model) {
        return (
            <div className="space-y-6">
                <Link href="/models">
                    <Button variant="noShadow" className="pl-0">
                        <IconArrowLeft className="mr-2 h-4 w-4" />
                        Back to Models
                    </Button>
                </Link>
                <Alert className="border-2 border-red-500 shadow-brutal">
                    <IconAlertTriangle className="h-4 w-4" />
                    <AlertDescription>{error?.message || 'Model not found'}</AlertDescription>
                </Alert>
            </div>
        )
    }

    const getStatusBadge = (status: string) => {
        const variants: Record<string, { variant: 'default' | 'secondary' | 'destructive', label: string }> = {
            active: { variant: 'default', label: 'Active' },
            inactive: { variant: 'secondary', label: 'Inactive' },
            deprecated: { variant: 'destructive', label: 'Deprecated' },
        }
        const config = variants[status] || variants.inactive
        return <Badge variant={config.variant} className="border-2 border-black">{config.label}</Badge>
    }

    // Prepare chart data if test results exist
    const chartData = testResult ? Object.entries(testResult.metrics).map(([attr, metrics]: [string, any]) => ({
        name: attr,
        demographic_parity: metrics.demographic_parity?.disparity || 0,
        equality_opportunity: metrics.equality_of_opportunity?.disparity || 0,
    })) : []

    return (
        <div className="space-y-8">
            {/* Header */}
            <div className="flex flex-col gap-4">
                <Link href="/models">
                    <Button variant="noShadow" className="pl-0 w-fit">
                        <IconArrowLeft className="mr-2 h-4 w-4" />
                        Back to Models
                    </Button>
                </Link>

                <div className="flex items-start justify-between">
                    <div>
                        <div className="flex items-center gap-3 mb-2">
                            <h1 className="text-4xl font-bold">{model.name}</h1>
                            {getStatusBadge(model.status)}
                        </div>
                        <p className="text-muted-foreground text-lg max-w-2xl">
                            {model.description || 'No description provided'}
                        </p>
                    </div>

                    <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
                        <DialogTrigger asChild>
                            <Button
                                size="lg"
                                disabled={testing}
                                className="border-2 border-black shadow-brutal hover:translate-y-1 hover:shadow-none transition-all"
                            >
                                {testing ? (
                                    <>
                                        <IconActivity className="mr-2 h-5 w-5 animate-spin" />
                                        Running Tests...
                                    </>
                                ) : (
                                    <>
                                        <IconTestPipe className="mr-2 h-5 w-5" />
                                        Run Bias Test
                                    </>
                                )}
                            </Button>
                        </DialogTrigger>
                        <DialogContent className="border-2 border-black shadow-brutal sm:max-w-[500px]">
                            <DialogHeader>
                                <DialogTitle>Configure Bias Test</DialogTitle>
                                <DialogDescription>
                                    Choose a dataset to test against or use synthetic data for demonstration.
                                </DialogDescription>
                            </DialogHeader>

                            <div className="space-y-6 py-4">
                                <div className="space-y-2">
                                    <Label>Test Dataset</Label>
                                    <Select value={selectedDatasetId} onValueChange={setSelectedDatasetId}>
                                        <SelectTrigger className="border-2 border-black">
                                            <SelectValue placeholder="Select a dataset (Optional)" />
                                        </SelectTrigger>
                                        <SelectContent>
                                            <SelectItem value="">Use Synthetic Data (Demo)</SelectItem>
                                            {datasets.map((d) => (
                                                <SelectItem key={d.id} value={d.id}>
                                                    {d.name} ({d.file_type})
                                                </SelectItem>
                                            ))}
                                        </SelectContent>
                                    </Select>
                                    <p className="text-xs text-muted-foreground">
                                        {datasets.length === 0 && !loadingDatasets && "No datasets found. Upload one in the Datasets section."}
                                    </p>
                                </div>

                                {selectedDatasetId && (
                                    <>
                                        <div className="space-y-2">
                                            <Label>Target Column</Label>
                                            <Input
                                                placeholder="e.g., target, label, class"
                                                value={targetColumn}
                                                onChange={(e) => setTargetColumn(e.target.value)}
                                                className="border-2 border-black"
                                            />
                                            <p className="text-xs text-muted-foreground">
                                                The column containing model predictions or ground truth.
                                            </p>
                                        </div>

                                        <div className="space-y-2">
                                            <Label>Sensitive Attributes</Label>
                                            <Input
                                                placeholder="e.g., gender, race, age"
                                                value={sensitiveAttributes}
                                                onChange={(e) => setSensitiveAttributes(e.target.value)}
                                                className="border-2 border-black"
                                            />
                                            <p className="text-xs text-muted-foreground">
                                                Comma-separated list of attributes to test for bias.
                                            </p>
                                        </div>
                                    </>
                                )}
                            </div>

                            <DialogFooter>
                                <Button variant="noShadow" onClick={() => setDialogOpen(false)}>Cancel</Button>
                                <Button onClick={handleRunTest} disabled={testing}>
                                    {testing ? 'Running...' : 'Start Test'}
                                </Button>
                            </DialogFooter>
                        </DialogContent>
                    </Dialog>
                </div>
            </div>

            {/* Stats Grid */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                <Card className="p-6 border-2 border-black shadow-brutal bg-white">
                    <div className="flex items-center gap-4">
                        <div className="p-3 bg-blue-100 rounded-full border-2 border-black">
                            <IconBrain className="h-6 w-6 text-blue-700" />
                        </div>
                        <div>
                            <p className="text-sm font-bold text-muted-foreground uppercase tracking-wider">Model Type</p>
                            <p className="text-2xl font-bold">{model.type}</p>
                        </div>
                    </div>
                </Card>

                <Card className="p-6 border-2 border-black shadow-brutal bg-white">
                    <div className="flex items-center gap-4">
                        <div className="p-3 bg-purple-100 rounded-full border-2 border-black">
                            <IconScale className="h-6 w-6 text-purple-700" />
                        </div>
                        <div>
                            <p className="text-sm font-bold text-muted-foreground uppercase tracking-wider">Fairness Score</p>
                            <div className="flex items-baseline gap-2">
                                <p className="text-2xl font-bold">{(model.fairness_score * 100).toFixed(1)}%</p>
                                <span className={`text-sm font-bold ${model.fairness_score > 0.8 ? 'text-green-600' : 'text-red-600'}`}>
                                    {model.fairness_score > 0.8 ? 'Good' : 'Needs Attention'}
                                </span>
                            </div>
                        </div>
                    </div>
                </Card>

                <Card className="p-6 border-2 border-black shadow-brutal bg-white">
                    <div className="flex items-center gap-4">
                        <div className="p-3 bg-orange-100 rounded-full border-2 border-black">
                            <IconActivity className="h-6 w-6 text-orange-700" />
                        </div>
                        <div>
                            <p className="text-sm font-bold text-muted-foreground uppercase tracking-wider">Bias Score</p>
                            <div className="flex items-baseline gap-2">
                                <p className="text-2xl font-bold">{(model.bias_score * 100).toFixed(1)}%</p>
                                <span className={`text-sm font-bold ${model.bias_score < 0.2 ? 'text-green-600' : 'text-red-600'}`}>
                                    {model.bias_score < 0.2 ? 'Low Risk' : 'High Risk'}
                                </span>
                            </div>
                        </div>
                    </div>
                </Card>
            </div>

            {/* Test Results Section */}
            {(testResult || model.fairness_score > 0) && (
                <div className="space-y-6">
                    <h2 className="text-2xl font-bold border-b-2 border-black pb-2">Bias Analysis Results</h2>

                    {testError && (
                        <Alert variant="destructive" className="border-2 border-black shadow-brutal">
                            <IconAlertTriangle className="h-4 w-4" />
                            <AlertDescription>{testError.message}</AlertDescription>
                        </Alert>
                    )}

                    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                        {/* Metrics Chart */}
                        <Card className="p-6 border-2 border-black shadow-brutal">
                            <h3 className="text-lg font-bold mb-6">Disparity Metrics by Attribute</h3>
                            <div className="h-[300px] w-full">
                                <ResponsiveContainer width="100%" height="100%">
                                    <BarChart data={chartData}>
                                        <CartesianGrid strokeDasharray="3 3" />
                                        <XAxis dataKey="name" />
                                        <YAxis />
                                        <Tooltip
                                            contentStyle={{
                                                border: '2px solid black',
                                                borderRadius: '8px',
                                                boxShadow: '4px 4px 0px 0px rgba(0,0,0,1)'
                                            }}
                                        />
                                        <Bar dataKey="demographic_parity" name="Demographic Parity" fill="#8884d8" radius={[4, 4, 0, 0]} />
                                        <Bar dataKey="equality_opportunity" name="Equality of Opportunity" fill="#82ca9d" radius={[4, 4, 0, 0]} />
                                    </BarChart>
                                </ResponsiveContainer>
                            </div>
                        </Card>

                        {/* Recommendations */}
                        <Card className="p-6 border-2 border-black shadow-brutal">
                            <h3 className="text-lg font-bold mb-6">Recommendations</h3>
                            <div className="space-y-4">
                                {testResult?.recommendations.map((rec, i) => (
                                    <div key={i} className="flex gap-3 items-start p-4 bg-yellow-50 border-2 border-yellow-200 rounded-lg">
                                        <IconAlertTriangle className="h-5 w-5 text-yellow-600 shrink-0 mt-0.5" />
                                        <p className="text-sm font-medium text-yellow-900">{rec}</p>
                                    </div>
                                )) || (
                                        <div className="text-center py-12 text-muted-foreground">
                                            Run a test to generate recommendations
                                        </div>
                                    )}
                            </div>
                        </Card>
                    </div>

                    {/* Detailed Metrics Table */}
                    <Card className="border-2 border-black shadow-brutal overflow-hidden">
                        <div className="p-4 bg-gray-50 border-b-2 border-black">
                            <h3 className="font-bold">Detailed Metrics</h3>
                        </div>
                        <div className="p-6">
                            {testResult ? (
                                <div className="space-y-6">
                                    {Object.entries(testResult.metrics).map(([attr, metrics]: [string, any]) => (
                                        <div key={attr} className="space-y-3">
                                            <h4 className="font-bold text-lg capitalize flex items-center gap-2">
                                                {attr}
                                                {metrics.demographic_parity?.fair ? (
                                                    <Badge variant="default" className="bg-green-500 hover:bg-green-600">Fair</Badge>
                                                ) : (
                                                    <Badge variant="destructive">Bias Detected</Badge>
                                                )}
                                            </h4>
                                            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                                                <div className="p-4 border rounded-lg bg-gray-50">
                                                    <p className="text-xs text-muted-foreground uppercase font-bold mb-1">Demographic Parity</p>
                                                    <p className="text-2xl font-bold">{metrics.demographic_parity?.disparity?.toFixed(3) || 'N/A'}</p>
                                                    <p className="text-xs text-muted-foreground">Disparity</p>
                                                </div>
                                                <div className="p-4 border rounded-lg bg-gray-50">
                                                    <p className="text-xs text-muted-foreground uppercase font-bold mb-1">Equality of Opp.</p>
                                                    <p className="text-2xl font-bold">{metrics.equality_of_opportunity?.disparity?.toFixed(3) || 'N/A'}</p>
                                                    <p className="text-xs text-muted-foreground">Disparity</p>
                                                </div>
                                                <div className="p-4 border rounded-lg bg-gray-50">
                                                    <p className="text-xs text-muted-foreground uppercase font-bold mb-1">Statistical Parity</p>
                                                    <p className="text-2xl font-bold">{metrics.statistical_parity?.statistical_parity_difference?.toFixed(3) || 'N/A'}</p>
                                                    <p className="text-xs text-muted-foreground">Difference</p>
                                                </div>
                                            </div>
                                        </div>
                                    ))}
                                </div>
                            ) : (
                                <div className="text-center py-12 text-muted-foreground">
                                    No detailed metrics available. Run a test to view analysis.
                                </div>
                            )}
                        </div>
                    </Card>
                </div>
            )}

            {/* Environmental governance: assess this model's environmental
                evidence and see the release gate without leaving evaluation. */}
            <div className="pt-4 border-t-4 border-black">
                <ModelEnvironmentalPanel modelId={id} modelName={model.name} />
            </div>
        </div>
    )
}
