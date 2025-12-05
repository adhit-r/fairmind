'use client'

import { useState } from 'react'
import { useRemediation } from '@/lib/api/hooks/useRemediation'
import { Card } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Badge } from '@/components/ui/badge'
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert'
import { Skeleton } from '@/components/ui/skeleton'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import {
    IconWand,
    IconAlertTriangle,
    IconCheck,
    IconCopy,
    IconTrendingUp,
    IconCode,
    IconBulb,
    IconRocket
} from '@tabler/icons-react'
import { useToast } from '@/hooks/use-toast'

export default function RemediationPage() {
    const [testId, setTestId] = useState('')
    const { remediation, loading, error, getRemediation } = useRemediation()
    const { toast } = useToast()

    const handleAnalyze = () => {
        if (!testId.trim()) {
            toast({
                title: 'Test ID required',
                description: 'Please enter a test ID to analyze',
                variant: 'destructive',
            })
            return
        }
        getRemediation(testId)
    }

    const copyCode = (code: string) => {
        navigator.clipboard.writeText(code)
        toast({
            title: 'Code copied!',
            description: 'Implementation code copied to clipboard',
        })
    }

    const getImprovementColor = (percentage: number) => {
        if (percentage >= 30) return 'text-green-600'
        if (percentage >= 15) return 'text-yellow-600'
        return 'text-orange-600'
    }

    return (
        <div className="space-y-6">
            {/* Header */}
            <div>
                <h1 className="text-4xl font-bold">🪄 Automated Bias Remediation</h1>
                <p className="text-muted-foreground mt-1">
                    Get actionable strategies to fix bias in your models with ready-to-use code
                </p>
            </div>

            {/* Input Section */}
            <Card className="p-6 border-2 border-black shadow-brutal">
                <div className="flex gap-4 items-end">
                    <div className="flex-1">
                        <label className="text-sm font-medium mb-2 block">Test ID</label>
                        <Input
                            placeholder="Enter test ID (e.g., ml-test-20251123010000)"
                            value={testId}
                            onChange={(e) => setTestId(e.target.value)}
                            className="border-2 border-black"
                            onKeyDown={(e) => e.key === 'Enter' && handleAnalyze()}
                        />
                    </div>
                    <Button
                        onClick={handleAnalyze}
                        disabled={loading}
                        className="border-2 border-black shadow-brutal"
                    >
                        <IconWand className="mr-2 h-4 w-4" />
                        {loading ? 'Analyzing...' : 'Get Remediation'}
                    </Button>
                </div>
            </Card>

            {error && (
                <Alert className="border-2 border-red-500 shadow-brutal">
                    <IconAlertTriangle className="h-4 w-4" />
                    <AlertTitle>Error</AlertTitle>
                    <AlertDescription>{error}</AlertDescription>
                </Alert>
            )}

            {loading && (
                <div className="space-y-4">
                    <Skeleton className="h-32" />
                    <Skeleton className="h-64" />
                </div>
            )}

            {remediation && !loading && (
                <>
                    {/* Summary */}
                    <Card className="p-6 border-2 border-black shadow-brutal bg-gradient-to-r from-purple-50 to-blue-50">
                        <div className="flex items-start gap-3">
                            <IconRocket className="h-6 w-6 text-purple-600 mt-1" />
                            <div className="flex-1">
                                <h2 className="text-xl font-bold mb-2">Best Strategy Recommended</h2>
                                <p className="text-muted-foreground mb-4">{remediation.summary}</p>
                                <div className="flex gap-4">
                                    <div>
                                        <div className="text-sm text-muted-foreground">Strategy</div>
                                        <Badge className="mt-1 border-2 border-black bg-purple-500 text-white">
                                            {remediation.best_strategy.strategy.replace(/_/g, ' ').toUpperCase()}
                                        </Badge>
                                    </div>
                                    <div>
                                        <div className="text-sm text-muted-foreground">Expected Improvement</div>
                                        <div className={`text-2xl font-bold mt-1 ${getImprovementColor(remediation.best_strategy.improvement_percentage)}`}>
                                            +{remediation.best_strategy.improvement_percentage.toFixed(1)}%
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </Card>

                    {/* Strategies Tabs */}
                    <Card className="p-6 border-2 border-black shadow-brutal">
                        <Tabs defaultValue="0" className="w-full">
                            <TabsList className="grid w-full grid-cols-3 mb-6">
                                {remediation.strategies.map((strategy, idx) => (
                                    <TabsTrigger key={idx} value={idx.toString()} className="border-2 border-black">
                                        {strategy.strategy.replace(/_/g, ' ')}
                                    </TabsTrigger>
                                ))}
                            </TabsList>

                            {remediation.strategies.map((strategy, idx) => (
                                <TabsContent key={idx} value={idx.toString()} className="space-y-6">
                                    {/* Strategy Header */}
                                    <div className="flex items-center justify-between">
                                        <div>
                                            <h3 className="text-2xl font-bold capitalize">
                                                {strategy.strategy.replace(/_/g, ' ')} Strategy
                                            </h3>
                                            <div className="flex gap-2 mt-2">
                                                <Badge className="border-2 border-black bg-green-500 text-white">
                                                    <IconCheck className="h-3 w-3 mr-1" />
                                                    {strategy.improvement_percentage.toFixed(1)}% Improvement
                                                </Badge>
                                                {strategy.success && (
                                                    <Badge className="border-2 border-black bg-blue-500 text-white">
                                                        Ready to Deploy
                                                    </Badge>
                                                )}
                                            </div>
                                        </div>
                                    </div>

                                    {/* Warnings */}
                                    {strategy.warnings && strategy.warnings.length > 0 && (
                                        <Alert className="border-2 border-yellow-500 shadow-brutal bg-yellow-50">
                                            <IconAlertTriangle className="h-4 w-4" />
                                            <AlertTitle>Important Considerations</AlertTitle>
                                            <AlertDescription>
                                                <ul className="list-disc list-inside space-y-1 mt-2">
                                                    {strategy.warnings.map((warning, i) => (
                                                        <li key={i}>{warning}</li>
                                                    ))}
                                                </ul>
                                            </AlertDescription>
                                        </Alert>
                                    )}

                                    {/* Explanation */}
                                    <Card className="p-4 border-2 border-black bg-blue-50">
                                        <div className="flex items-start gap-3">
                                            <IconBulb className="w-5 h-5 text-yellow-600 mt-0.5 flex-shrink-0" />
                                            <div className="flex-1">
                                                <h4 className="font-bold mb-2">How It Works</h4>
                                                <div className="prose prose-sm max-w-none text-muted-foreground whitespace-pre-line">
                                                    {strategy.explanation}
                                                </div>
                                            </div>
                                        </div>
                                    </Card>

                                    {/* Metrics Comparison */}
                                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                                        <Card className="p-4 border-2 border-black">
                                            <h4 className="font-bold mb-3 flex items-center gap-2">
                                                <IconTrendingUp className="h-4 w-4" />
                                                Original Metrics
                                            </h4>
                                            <div className="space-y-2">
                                                {Object.entries(strategy.original_metrics).map(([metric, value]) => (
                                                    <div key={metric} className="flex justify-between">
                                                        <span className="text-sm capitalize">{metric.replace(/_/g, ' ')}</span>
                                                        <span className="font-semibold">{(value * 100).toFixed(1)}%</span>
                                                    </div>
                                                ))}
                                            </div>
                                        </Card>

                                        <Card className="p-4 border-2 border-black bg-green-50">
                                            <h4 className="font-bold mb-3 flex items-center gap-2 text-green-700">
                                                <IconCheck className="h-4 w-4" />
                                                Improved Metrics
                                            </h4>
                                            <div className="space-y-2">
                                                {Object.entries(strategy.improved_metrics).map(([metric, value]) => (
                                                    <div key={metric} className="flex justify-between">
                                                        <span className="text-sm capitalize">{metric.replace(/_/g, ' ')}</span>
                                                        <span className="font-semibold text-green-700">
                                                            {(value * 100).toFixed(1)}%
                                                            <span className="text-xs ml-1">
                                                                (+{((value - (strategy.original_metrics[metric] || 0)) * 100).toFixed(1)}%)
                                                            </span>
                                                        </span>
                                                    </div>
                                                ))}
                                            </div>
                                        </Card>
                                    </div>

                                    {/* Threshold Adjustments */}
                                    {strategy.threshold_adjustments && (
                                        <Card className="p-4 border-2 border-black bg-purple-50">
                                            <h4 className="font-bold mb-3">Optimal Thresholds</h4>
                                            <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                                                {Object.entries(strategy.threshold_adjustments).map(([group, threshold]) => (
                                                    <div key={group} className="border-2 border-black p-3 rounded-lg bg-white">
                                                        <div className="text-xs text-muted-foreground">Group {group}</div>
                                                        <div className="text-xl font-bold text-purple-600">{threshold.toFixed(2)}</div>
                                                    </div>
                                                ))}
                                            </div>
                                        </Card>
                                    )}

                                    {/* Implementation Code */}
                                    <Card className="p-4 border-2 border-black bg-gray-50">
                                        <div className="flex items-center justify-between mb-3">
                                            <h4 className="font-bold flex items-center gap-2">
                                                <IconCode className="h-4 w-4" />
                                                Implementation Code
                                            </h4>
                                            <Button
                                                variant="neutral"
                                                size="sm"
                                                onClick={() => copyCode(strategy.implementation_code)}
                                            >
                                                <IconCopy className="h-4 w-4 mr-2" />
                                                Copy Code
                                            </Button>
                                        </div>
                                        <pre className="bg-black text-green-400 p-4 rounded-lg overflow-x-auto text-sm border-2 border-gray-700">
                                            <code>{strategy.implementation_code}</code>
                                        </pre>
                                    </Card>
                                </TabsContent>
                            ))}
                        </Tabs>
                    </Card>
                </>
            )}

            {/* Empty State */}
            {!remediation && !loading && !error && (
                <Card className="p-12 border-2 border-black shadow-brutal">
                    <div className="text-center">
                        <IconWand className="h-16 w-16 mx-auto mb-4 text-muted-foreground opacity-50" />
                        <h3 className="text-xl font-bold mb-2">Ready to Fix Bias?</h3>
                        <p className="text-muted-foreground mb-4">
                            Enter a test ID above to get automated remediation strategies with ready-to-use code
                        </p>
                        <div className="flex gap-2 justify-center text-sm text-muted-foreground">
                            <div className="flex items-center gap-1">
                                <IconCheck className="h-4 w-4 text-green-600" />
                                <span>Multiple strategies</span>
                            </div>
                            <div className="flex items-center gap-1">
                                <IconCheck className="h-4 w-4 text-green-600" />
                                <span>Copy-paste code</span>
                            </div>
                            <div className="flex items-center gap-1">
                                <IconCheck className="h-4 w-4 text-green-600" />
                                <span>Expected improvements</span>
                            </div>
                        </div>
                    </div>
                </Card>
            )}
        </div>
    )
}
