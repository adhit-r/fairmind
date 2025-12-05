'use client'

import { useState } from 'react'
import { useTestHistory } from '@/lib/api/hooks/useTestHistory'
import { Card } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import { Badge } from '@/components/ui/badge'
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert'
import { Skeleton } from '@/components/ui/skeleton'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import {
    IconFlask,
    IconAlertTriangle,
    IconCheck,
    IconX,
    IconFilter,
    IconSearch,
    IconChevronRight,
    IconRefresh
} from '@tabler/icons-react'
import Link from 'next/link'
import type { TestResult } from '@/lib/api/hooks/useTestHistory'

export default function TestHistoryPage() {
    const [testTypeFilter, setTestTypeFilter] = useState<string>('')
    const [searchQuery, setSearchQuery] = useState('')
    const { tests, loading, error, total, refetch } = useTestHistory(undefined, testTypeFilter || undefined)

    const formatDate = (dateString: string) => {
        return new Date(dateString).toLocaleDateString('en-US', {
            year: 'numeric',
            month: 'short',
            day: 'numeric',
            hour: '2-digit',
            minute: '2-digit',
        })
    }

    const getRiskBadge = (risk: string) => {
        const variants = {
            low: { color: 'bg-green-500', icon: IconCheck },
            medium: { color: 'bg-yellow-500', icon: IconAlertTriangle },
            high: { color: 'bg-orange-500', icon: IconAlertTriangle },
            critical: { color: 'bg-red-500', icon: IconX },
        }
        const variant = variants[risk as keyof typeof variants] || variants.medium
        const Icon = variant.icon

        return (
            <Badge className={`border-2 border-black ${variant.color} text-white`}>
                <Icon className="h-3 w-3 mr-1" />
                {risk.toUpperCase()}
            </Badge>
        )
    }

    const getTestTypeBadge = (type: string) => {
        return (
            <Badge variant="secondary" className="border-2 border-black">
                {type === 'ml_bias' ? 'ML Bias' : 'LLM Bias'}
            </Badge>
        )
    }

    const filteredTests = tests.filter(test => {
        if (!searchQuery) return true
        const query = searchQuery.toLowerCase()
        return (
            test.model_id.toLowerCase().includes(query) ||
            test.test_id.toLowerCase().includes(query) ||
            test.summary.toLowerCase().includes(query)
        )
    })

    if (loading && tests.length === 0) {
        return (
            <div className="space-y-6">
                <Skeleton className="h-10 w-48" />
                <div className="space-y-4">
                    {[...Array(5)].map((_, i) => (
                        <Skeleton key={i} className="h-20" />
                    ))}
                </div>
            </div>
        )
    }

    return (
        <div className="space-y-6">
            {/* Header */}
            <div className="flex items-center justify-between">
                <div>
                    <h1 className="text-4xl font-bold">Test History</h1>
                    <p className="text-muted-foreground mt-1">
                        View and analyze all bias detection test results
                    </p>
                </div>
                <Button
                    variant="default"
                    onClick={refetch}
                    className="border-2 border-black shadow-brutal"
                >
                    <IconRefresh className="mr-2 h-4 w-4" />
                    Refresh
                </Button>
            </div>

            {/* Filters */}
            <Card className="p-4 border-2 border-black shadow-brutal">
                <div className="flex gap-4 items-end">
                    <div className="flex-1">
                        <label className="text-sm font-medium mb-2 block">Search</label>
                        <div className="relative">
                            <IconSearch className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                            <Input
                                placeholder="Search by model ID, test ID, or summary..."
                                value={searchQuery}
                                onChange={(e) => setSearchQuery(e.target.value)}
                                className="pl-10 border-2 border-black"
                            />
                        </div>
                    </div>
                    <div className="w-48">
                        <label className="text-sm font-medium mb-2 block">Test Type</label>
                        <Select value={testTypeFilter} onValueChange={setTestTypeFilter}>
                            <SelectTrigger className="border-2 border-black">
                                <SelectValue placeholder="All Types" />
                            </SelectTrigger>
                            <SelectContent>
                                <SelectItem value="">All Types</SelectItem>
                                <SelectItem value="ml_bias">ML Bias</SelectItem>
                                <SelectItem value="llm_bias">LLM Bias</SelectItem>
                            </SelectContent>
                        </Select>
                    </div>
                </div>
            </Card>

            {error && (
                <Alert className="border-2 border-red-500 shadow-brutal">
                    <IconAlertTriangle className="h-4 w-4" />
                    <AlertTitle>Error</AlertTitle>
                    <AlertDescription>{error}</AlertDescription>
                </Alert>
            )}

            {/* Stats Summary */}
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                <Card className="p-4 border-2 border-black shadow-brutal">
                    <div className="text-sm text-muted-foreground">Total Tests</div>
                    <div className="text-3xl font-bold mt-1">{total}</div>
                </Card>
                <Card className="p-4 border-2 border-black shadow-brutal">
                    <div className="text-sm text-muted-foreground">Passed</div>
                    <div className="text-3xl font-bold mt-1 text-green-600">
                        {tests.filter(t => t.overall_risk === 'low').length}
                    </div>
                </Card>
                <Card className="p-4 border-2 border-black shadow-brutal">
                    <div className="text-sm text-muted-foreground">Warnings</div>
                    <div className="text-3xl font-bold mt-1 text-yellow-600">
                        {tests.filter(t => t.overall_risk === 'medium' || t.overall_risk === 'high').length}
                    </div>
                </Card>
                <Card className="p-4 border-2 border-black shadow-brutal">
                    <div className="text-sm text-muted-foreground">Critical</div>
                    <div className="text-3xl font-bold mt-1 text-red-600">
                        {tests.filter(t => t.overall_risk === 'critical').length}
                    </div>
                </Card>
            </div>

            {/* Tests Table */}
            {filteredTests.length === 0 ? (
                <Card className="p-12 border-2 border-black shadow-brutal">
                    <div className="text-center">
                        <IconFlask className="h-16 w-16 mx-auto mb-4 text-muted-foreground opacity-50" />
                        <h3 className="text-xl font-bold mb-2">No tests found</h3>
                        <p className="text-muted-foreground mb-4">
                            {searchQuery || testTypeFilter
                                ? 'Try adjusting your filters'
                                : 'Run your first bias detection test to see results here'}
                        </p>
                        <Link href="/dashboard/bias-simple">
                            <Button variant="default" className="border-2 border-black shadow-brutal">
                                <IconFlask className="mr-2 h-4 w-4" />
                                Run Bias Test
                            </Button>
                        </Link>
                    </div>
                </Card>
            ) : (
                <Card className="p-6 border-2 border-black shadow-brutal">
                    <Table>
                        <TableHeader>
                            <TableRow>
                                <TableHead>Test ID</TableHead>
                                <TableHead>Model ID</TableHead>
                                <TableHead>Type</TableHead>
                                <TableHead>Risk Level</TableHead>
                                <TableHead>Metrics</TableHead>
                                <TableHead>Date</TableHead>
                                <TableHead></TableHead>
                            </TableRow>
                        </TableHeader>
                        <TableBody>
                            {filteredTests.map((test: TestResult) => (
                                <TableRow key={test.test_id} className="hover:bg-muted/50">
                                    <TableCell className="font-mono text-sm">
                                        {test.test_id}
                                    </TableCell>
                                    <TableCell className="font-medium">
                                        {test.model_id}
                                    </TableCell>
                                    <TableCell>
                                        {getTestTypeBadge(test.test_type)}
                                    </TableCell>
                                    <TableCell>
                                        {getRiskBadge(test.overall_risk)}
                                    </TableCell>
                                    <TableCell>
                                        <div className="flex gap-2 items-center">
                                            <span className="text-green-600 font-semibold">
                                                {test.metrics_passed} ✓
                                            </span>
                                            <span className="text-muted-foreground">/</span>
                                            <span className="text-red-600 font-semibold">
                                                {test.metrics_failed} ✗
                                            </span>
                                        </div>
                                    </TableCell>
                                    <TableCell className="text-sm text-muted-foreground">
                                        {formatDate(test.timestamp)}
                                    </TableCell>
                                    <TableCell>
                                        <Link href={`/dashboard/tests/${test.test_id}`}>
                                            <Button variant="neutral" size="sm">
                                                View
                                                <IconChevronRight className="ml-1 h-4 w-4" />
                                            </Button>
                                        </Link>
                                    </TableCell>
                                </TableRow>
                            ))}
                        </TableBody>
                    </Table>
                </Card>
            )}

            {/* Pagination Info */}
            {filteredTests.length > 0 && (
                <div className="text-sm text-muted-foreground text-center">
                    Showing {filteredTests.length} of {total} tests
                </div>
            )}
        </div>
    )
}
