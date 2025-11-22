'use client'

import { use } from 'react'
import { useTestDetail } from '@/lib/api/hooks/useTestHistory'
import { Card } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert'
import { Skeleton } from '@/components/ui/skeleton'
import { Progress } from '@/components/ui/progress'
import {
    IconArrowLeft,
    IconAlertTriangle,
    IconCheck,
    IconX,
    IconDownload,
    IconChartBar,
    IconListDetails,
    IconBulb
} from '@tabler/icons-react'
import Link from 'next/link'

interface PageProps {
    params: Promise<{ testId: string }>
}

export default function TestDetailPage({ params }: PageProps) {
    const { testId } = use(params)
    const { testDetail, loading, error } = useTestDetail(testId)

    const formatDate = (dateString: string) => {
        return new Date(dateString).toLocaleDateString('en-US', {
            year: 'numeric',
            month: 'long',
            day: 'numeric',
            hour: '2-digit',
            minute: '2-digit',
        })
    }

    const getRiskColor = (risk: string) => {
        const colors = {
            low: 'bg-green-500',
            medium: 'bg-yellow-500',
            high: 'bg-orange-500',
            critical: 'bg-red-500',
        }
        return colors[risk as keyof typeof colors] || colors.medium
    }

    const exportResults = () => {
        if (!testDetail) return

        const dataStr = JSON.stringify(testDetail, null, 2)
        const dataBlob = new Blob([dataStr], { type: 'application/json' })
        const url = URL.createObjectURL(dataBlob)
        const link = document.createElement('a')
        link.href = url
        link.download = `${testId}-results.json`
        link.click()
        URL.revokeObjectURL(url)
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

    if (error || !testDetail) {
        return (
            <div className="space-y-6">
                <Link href="/dashboard/tests">
                    <Button variant="neutral">
                        <IconArrowLeft className="mr-2 h-4 w-4" />
                        Back to Tests
                    </Button>
                </Link>
                <Alert className="border-2 border-red-500 shadow-brutal">
                    <IconAlertTriangle className="h-4 w-4" />
                    <AlertTitle>Error</AlertTitle>
                    <AlertDescription>{error || 'Test not found'}</AlertDescription>
                </Alert>
            </div>
        )
    }

    const metricsData = Object.entries(testDetail.results || {}).map(([name, data]: [string, any]) => ({
        metric: name.replace(/_/g, ' ').replace(/\b\w/g, (l: string) => l.toUpperCase()),
        score: data.score * 100,
        passed: data.passed,
    }))

    const riskDistribution = [
        { name: 'Passed', value: testDetail.metrics_passed, color: '#22c55e' },
        { name: 'Failed', value: testDetail.metrics_failed, color: '#ef4444' },
    ]

    return (
        <div className="space-y-6">
            {/* Header */}
            <div className="flex items-center justify-between">
                <div className="flex items-center gap-4">
                    <Link href="/dashboard/tests">
                        <Button variant="neutral" size="sm">
                            <IconArrowLeft className="mr-2 h-4 w-4" />
                            Back
                        </Button>
                    </Link>
                    <div>
                        <h1 className="text-4xl font-bold">Test Results</h1>
                        <p className="text-muted-foreground mt-1 font-mono text-sm">
                            {testId}
                        </p>
                    </div>
                </div>
                <Button
                    variant="default"
                    onClick={exportResults}
                    className="border-2 border-black shadow-brutal"
                >
                    <IconDownload className="mr-2 h-4 w-4" />
                    Export JSON
                </Button>
            </div>

            {/* Summary Cards */}
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                <Card className="p-6 border-2 border-black shadow-brutal">
                    <div className="text-sm text-muted-foreground mb-2">Overall Risk</div>
                    <Badge className={`${getRiskColor(testDetail.overall_risk)} border-2 border-black text-white text-lg px-4 py-2`}>
                        {testDetail.overall_risk.toUpperCase()}
                    </Badge>
                </Card>
                <Card className="p-6 border-2 border-black shadow-brutal">
                    <div className="text-sm text-muted-foreground mb-2">Model ID</div>
                    <div className="text-xl font-bold">{testDetail.model_id}</div>
                </Card>
                <Card className="p-6 border-2 border-black shadow-brutal">
                    <div className="text-sm text-muted-foreground mb-2">Test Type</div>
                    <Badge variant="secondary" className="border-2 border-black text-lg px-4 py-2">
                        {testDetail.test_id.startsWith('ml-') ? 'ML Bias' : 'LLM Bias'}
                    </Badge>
                </Card>
                <Card className="p-6 border-2 border-black shadow-brutal">
                    <div className="text-sm text-muted-foreground mb-2">Date</div>
                    <div className="text-sm font-medium">{formatDate(testDetail.timestamp)}</div>
                </Card>
            </div>

            {/* Summary */}
            <Card className="p-6 border-2 border-black shadow-brutal">
                <div className="flex items-start gap-3">
                    <IconListDetails className="h-6 w-6 text-primary mt-1" />
                    <div className="flex-1">
                        <h2 className="text-xl font-bold mb-2">Summary</h2>
                        <p className="text-muted-foreground leading-relaxed">{testDetail.summary}</p>
                    </div>
                </div>
            </Card>

            {/* Metrics Overview */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                {/* Metrics Breakdown */}
                <Card className="p-6 border-2 border-black shadow-brutal">
                    <div className="flex items-center gap-2 mb-4">
                        <IconChartBar className="h-5 w-5 text-primary" />
                        <h2 className="text-xl font-bold">Metrics Breakdown</h2>
                    </div>
                    <div className="space-y-4">
                        {metricsData.map((metric) => (
                            <div key={metric.metric} className="space-y-2">
                                <div className="flex items-center justify-between">
                                    <span className="font-medium">{metric.metric}</span>
                                    <div className="flex items-center gap-2">
                                        <span className="text-sm font-semibold">
                                            {metric.score.toFixed(1)}%
                                        </span>
                                        {metric.passed ? (
                                            <IconCheck className="h-4 w-4 text-green-600" />
                                        ) : (
                                            <IconX className="h-4 w-4 text-red-600" />
                                        )}
                                    </div>
                                </div>
                                <Progress
                                    value={metric.score}
                                    className={`h-2 ${metric.passed ? 'bg-green-100' : 'bg-red-100'}`}
                                />
                            </div>
                        ))}
                    </div>
                </Card>

                {/* Pass/Fail Distribution */}
                <Card className="p-6 border-2 border-black shadow-brutal">
                    <h2 className="text-xl font-bold mb-4">Pass/Fail Distribution</h2>
                    <div className="space-y-4">
                        <div>
                            <div className="flex items-center justify-between mb-2">
                                <span className="text-sm font-medium">Passed Metrics</span>
                                <span className="text-sm font-semibold text-green-600">
                                    {testDetail.metrics_passed}
                                </span>
                            </div>
                            <Progress
                                value={(testDetail.metrics_passed / (testDetail.metrics_passed + testDetail.metrics_failed)) * 100}
                                className="h-4 bg-gray-200"
                            />
                        </div>
                        <div>
                            <div className="flex items-center justify-between mb-2">
                                <span className="text-sm font-medium">Failed Metrics</span>
                                <span className="text-sm font-semibold text-red-600">
                                    {testDetail.metrics_failed}
                                </span>
                            </div>
                            <Progress
                                value={(testDetail.metrics_failed / (testDetail.metrics_passed + testDetail.metrics_failed)) * 100}
                                className="h-4 bg-gray-200"
                            />
                        </div>
                    </div>
                    <div className="mt-6 grid grid-cols-2 gap-4 text-center">
                        <div className="border-2 border-black p-4 rounded-lg bg-green-50">
                            <div className="text-3xl font-bold text-green-600">
                                {testDetail.metrics_passed}
                            </div>
                            <div className="text-sm text-muted-foreground">Passed</div>
                        </div>
                        <div className="border-2 border-black p-4 rounded-lg bg-red-50">
                            <div className="text-3xl font-bold text-red-600">
                                {testDetail.metrics_failed}
                            </div>
                            <div className="text-sm text-muted-foreground">Failed</div>
                        </div>
                    </div>
                </Card>            </div>

            {/* Detailed Metrics */}
            <Card className="p-6 border-2 border-black shadow-brutal">
                <h2 className="text-xl font-bold mb-4">Detailed Metrics</h2>
                <div className="space-y-6">
                    {Object.entries(testDetail.results || {}).map(([metricName, metricData]: [string, any]) => (
                        <div key={metricName} className="border-2 border-black p-4 rounded-lg">
                            <div className="flex items-center justify-between mb-3">
                                <h3 className="text-lg font-bold capitalize">
                                    {metricName.replace(/_/g, ' ')}
                                </h3>
                                <Badge className={metricData.passed ? 'bg-green-500 border-2 border-black' : 'bg-red-500 border-2 border-black'}>
                                    {metricData.passed ? 'PASSED' : 'FAILED'}
                                </Badge>
                            </div>
                            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-3">
                                <div>
                                    <span className="text-sm text-muted-foreground">Score:</span>
                                    <span className="ml-2 font-semibold">{(metricData.score * 100).toFixed(2)}%</span>
                                </div>
                                <div>
                                    <span className="text-sm text-muted-foreground">Disparity:</span>
                                    <span className="ml-2 font-semibold">{(metricData.disparity * 100).toFixed(2)}%</span>
                                </div>
                            </div>
                            <div className="mb-3">
                                <div className="text-sm font-medium mb-2">Group Scores:</div>
                                <div className="grid grid-cols-2 md:grid-cols-4 gap-2">
                                    {Object.entries(metricData.group_scores || {}).map(([group, score]: [string, any]) => (
                                        <div key={group} className="bg-muted p-2 rounded border border-black">
                                            <div className="text-xs text-muted-foreground">{group}</div>
                                            <div className="font-semibold">{(score * 100).toFixed(1)}%</div>
                                        </div>
                                    ))}
                                </div>
                            </div>
                            <div className="text-sm text-muted-foreground italic">
                                {metricData.interpretation}
                            </div>
                        </div>
                    ))}
                </div>
            </Card>

            {/* Recommendations */}
            {testDetail.recommendations && testDetail.recommendations.length > 0 && (
                <Card className="p-6 border-2 border-black shadow-brutal">
                    <div className="flex items-start gap-3">
                        <IconBulb className="h-6 w-6 text-yellow-500 mt-1" />
                        <div className="flex-1">
                            <h2 className="text-xl font-bold mb-4">Recommendations</h2>
                            <ul className="space-y-3">
                                {testDetail.recommendations.map((rec: string, idx: number) => (
                                    <li key={idx} className="flex items-start gap-3">
                                        <span className="text-primary font-bold">{idx + 1}.</span>
                                        <span className="text-muted-foreground">{rec}</span>
                                    </li>
                                ))}
                            </ul>
                        </div>
                    </div>
                </Card>
            )}
        </div>
    )
}
