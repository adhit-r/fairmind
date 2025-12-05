'use client'

import { useState, useEffect } from 'react'
import { useRealtimeModels, type ModelConfig, type BiasTestResult, type ComprehensiveAnalysisResult } from '@/lib/api/hooks/useRealtimeModels'
import { Card, CardContent, CardDescription, CardHeader, CardTitle, CardFooter } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Textarea } from '@/components/ui/textarea'
import { Badge } from '@/components/ui/badge'
import { Progress } from '@/components/ui/progress'
import { Slider } from '@/components/ui/slider'
import { useToast } from '@/hooks/use-toast'
import {
    IconPlugConnected,
    IconPlayerPlay,
    IconActivity,
    IconLoader,
    IconSettings,
    IconChartBar,
    IconBrain
} from '@tabler/icons-react'

export default function RealtimeIntegrationPage() {
    const {
        loading,
        getProviders,
        getBiasTestTypes,
        testConnection,
        performBiasTest,
        performComprehensiveAnalysis
    } = useRealtimeModels()

    const { toast } = useToast()

    // State
    const [providers, setProviders] = useState<any[]>([])
    const [testTypes, setTestTypes] = useState<any[]>([])
    const [activeTab, setActiveTab] = useState('config')
    const [isConnected, setIsConnected] = useState(false)

    // Configuration State
    const [config, setConfig] = useState<ModelConfig>({
        provider: 'openai',
        model_name: 'gpt-3.5-turbo',
        model_type: 'chat_completion',
        api_key: '',
        temperature: 0.7,
        max_tokens: 1000,
        top_p: 1.0,
        frequency_penalty: 0.0,
        presence_penalty: 0.0
    })

    // Interactive Test State
    const [selectedTestType, setSelectedTestType] = useState('gender_bias')
    const [customPrompt, setCustomPrompt] = useState('')
    const [testResult, setTestResult] = useState<BiasTestResult | null>(null)

    // Analysis State
    const [analysisResult, setAnalysisResult] = useState<ComprehensiveAnalysisResult | null>(null)

    // Load initial data
    useEffect(() => {
        const loadData = async () => {
            const providersData = await getProviders()
            if (providersData && providersData.success) {
                setProviders(providersData.providers.providers)
            }

            const testTypesData = await getBiasTestTypes()
            if (testTypesData && testTypesData.success) {
                setTestTypes(testTypesData.test_types.test_types)
            }
        }
        loadData()
    }, [getProviders, getBiasTestTypes])

    // Handlers
    const handleTestConnection = async () => {
        try {
            if (!config.api_key && config.provider !== 'local') {
                toast({
                    title: "API Key Required",
                    description: "Please enter an API key for this provider",
                    variant: "destructive"
                })
                return
            }

            const result = await testConnection(config)
            if (result && result.success) {
                setIsConnected(true)
                toast({
                    title: "Connected Successfully",
                    description: `Response time: ${result.response_time.toFixed(2)}s`,
                })
                setActiveTab('interactive')
            }
        } catch (err) {
            setIsConnected(false)
            toast({
                title: "Connection Failed",
                description: err instanceof Error ? err.message : "Could not connect to model",
                variant: "destructive"
            })
        }
    }

    const handleRunTest = async () => {
        try {
            setTestResult(null)
            const result = await performBiasTest(
                config,
                selectedTestType,
                ['male', 'female', 'non-binary'], // Default groups, could be made dynamic
                customPrompt || undefined
            )
            if (result) {
                setTestResult(result)
            }
        } catch (err) {
            toast({
                title: "Test Failed",
                description: err instanceof Error ? err.message : "Analysis failed",
                variant: "destructive"
            })
        }
    }

    const handleRunAnalysis = async () => {
        try {
            setAnalysisResult(null)
            const result = await performComprehensiveAnalysis(
                config,
                ['male', 'female', 'non-binary', 'white', 'black', 'asian', 'hispanic']
            )
            if (result) {
                setAnalysisResult(result)
            }
        } catch (err) {
            toast({
                title: "Analysis Failed",
                description: err instanceof Error ? err.message : "Full analysis failed",
                variant: "destructive"
            })
        }
    }

    const getBiasScoreColor = (score: number) => {
        if (score < 0.1) return 'text-green-600'
        if (score < 0.3) return 'text-yellow-600'
        return 'text-red-600'
    }

    return (
        <div className="space-y-6">
            {/* Header */}
            <div className="flex items-center justify-between">
                <div>
                    <h1 className="text-4xl font-bold">Real-time Integration</h1>
                    <p className="text-muted-foreground mt-1">
                        Connect live models for instant bias detection and monitoring
                    </p>
                </div>
                {isConnected && (
                    <Badge variant="default" className="bg-green-500 hover:bg-green-600 text-white px-4 py-2 text-sm border-2 border-black">
                        <IconPlugConnected className="mr-2 h-4 w-4" />
                        Connected: {config.provider}/{config.model_name}
                    </Badge>
                )}
            </div>

            <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-4">
                <TabsList className="border-2 border-black p-1 bg-muted">
                    <TabsTrigger value="config" className="data-[state=active]:bg-white data-[state=active]:border-2 data-[state=active]:border-black">
                        <IconSettings className="mr-2 h-4 w-4" />
                        Configuration
                    </TabsTrigger>
                    <TabsTrigger value="interactive" disabled={!isConnected} className="data-[state=active]:bg-white data-[state=active]:border-2 data-[state=active]:border-black">
                        <IconPlayerPlay className="mr-2 h-4 w-4" />
                        Interactive Test
                    </TabsTrigger>
                    <TabsTrigger value="analysis" disabled={!isConnected} className="data-[state=active]:bg-white data-[state=active]:border-2 data-[state=active]:border-black">
                        <IconChartBar className="mr-2 h-4 w-4" />
                        Comprehensive Analysis
                    </TabsTrigger>
                </TabsList>

                {/* Configuration Tab */}
                <TabsContent value="config">
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                        <Card className="border-2 border-black shadow-brutal">
                            <CardHeader>
                                <CardTitle>Model Settings</CardTitle>
                                <CardDescription>Configure your model provider and parameters</CardDescription>
                            </CardHeader>
                            <CardContent className="space-y-4">
                                <div className="space-y-2">
                                    <Label>Provider</Label>
                                    <Select
                                        value={config.provider}
                                        onValueChange={(val) => setConfig({ ...config, provider: val })}
                                    >
                                        <SelectTrigger className="border-2 border-black">
                                            <SelectValue placeholder="Select provider" />
                                        </SelectTrigger>
                                        <SelectContent>
                                            {providers.map(p => (
                                                <SelectItem key={p.id} value={p.id} disabled={!p.available}>
                                                    {p.name} {!p.available && '(Unavailable)'}
                                                </SelectItem>
                                            ))}
                                        </SelectContent>
                                    </Select>
                                </div>

                                <div className="space-y-2">
                                    <Label>Model Name</Label>
                                    <Input
                                        value={config.model_name}
                                        onChange={(e) => setConfig({ ...config, model_name: e.target.value })}
                                        placeholder="e.g., gpt-4, claude-3-opus"
                                        className="border-2 border-black"
                                    />
                                </div>

                                <div className="space-y-2">
                                    <Label>API Key</Label>
                                    <Input
                                        type="password"
                                        value={config.api_key}
                                        onChange={(e) => setConfig({ ...config, api_key: e.target.value })}
                                        placeholder="sk-..."
                                        className="border-2 border-black"
                                    />
                                    <p className="text-xs text-muted-foreground">Keys are never stored permanently in the browser.</p>
                                </div>

                                <div className="space-y-2">
                                    <Label>Base URL (Optional)</Label>
                                    <Input
                                        value={config.base_url || ''}
                                        onChange={(e) => setConfig({ ...config, base_url: e.target.value })}
                                        placeholder="https://api.openai.com/v1"
                                        className="border-2 border-black"
                                    />
                                </div>
                            </CardContent>
                            <CardFooter>
                                <Button
                                    onClick={handleTestConnection}
                                    disabled={loading}
                                    className="w-full border-2 border-black shadow-brutal hover:translate-y-1 hover:shadow-none transition-all"
                                >
                                    {loading ? <IconLoader className="animate-spin mr-2" /> : <IconPlugConnected className="mr-2 h-4 w-4" />}
                                    Test Connection
                                </Button>
                            </CardFooter>
                        </Card>

                        <Card className="border-2 border-black shadow-brutal">
                            <CardHeader>
                                <CardTitle>Parameters</CardTitle>
                                <CardDescription>Fine-tune generation settings</CardDescription>
                            </CardHeader>
                            <CardContent className="space-y-6">
                                <div className="space-y-2">
                                    <div className="flex justify-between">
                                        <Label>Temperature</Label>
                                        <span className="text-sm font-mono">{config.temperature}</span>
                                    </div>
                                    <Slider
                                        value={[config.temperature || 0.7]}
                                        max={2}
                                        step={0.1}
                                        onValueChange={([val]) => setConfig({ ...config, temperature: val })}
                                        className="py-2"
                                    />
                                </div>

                                <div className="space-y-2">
                                    <div className="flex justify-between">
                                        <Label>Max Tokens</Label>
                                        <span className="text-sm font-mono">{config.max_tokens}</span>
                                    </div>
                                    <Slider
                                        value={[config.max_tokens || 1000]}
                                        max={4096}
                                        step={100}
                                        onValueChange={([val]) => setConfig({ ...config, max_tokens: val })}
                                        className="py-2"
                                    />
                                </div>

                                <div className="space-y-2">
                                    <div className="flex justify-between">
                                        <Label>Top P</Label>
                                        <span className="text-sm font-mono">{config.top_p}</span>
                                    </div>
                                    <Slider
                                        value={[config.top_p || 1.0]}
                                        max={1}
                                        step={0.05}
                                        onValueChange={([val]) => setConfig({ ...config, top_p: val })}
                                        className="py-2"
                                    />
                                </div>
                            </CardContent>
                        </Card>
                    </div>
                </TabsContent>

                {/* Interactive Test Tab */}
                <TabsContent value="interactive">
                    <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                        <div className="lg:col-span-1 space-y-6">
                            <Card className="border-2 border-black shadow-brutal">
                                <CardHeader>
                                    <CardTitle>Test Configuration</CardTitle>
                                </CardHeader>
                                <CardContent className="space-y-4">
                                    <div className="space-y-2">
                                        <Label>Test Type</Label>
                                        <Select
                                            value={selectedTestType}
                                            onValueChange={setSelectedTestType}
                                        >
                                            <SelectTrigger className="border-2 border-black">
                                                <SelectValue />
                                            </SelectTrigger>
                                            <SelectContent>
                                                {testTypes.map(t => (
                                                    <SelectItem key={t.id} value={t.id}>
                                                        {t.name}
                                                    </SelectItem>
                                                ))}
                                            </SelectContent>
                                        </Select>
                                    </div>

                                    <div className="space-y-2">
                                        <Label>Custom Prompt (Optional)</Label>
                                        <Textarea
                                            value={customPrompt}
                                            onChange={(e) => setCustomPrompt(e.target.value)}
                                            placeholder="Enter a specific prompt to test..."
                                            className="border-2 border-black min-h-[100px]"
                                        />
                                    </div>

                                    <Button
                                        onClick={handleRunTest}
                                        disabled={loading}
                                        className="w-full border-2 border-black shadow-brutal"
                                    >
                                        {loading ? 'Running...' : 'Run Bias Test'}
                                    </Button>
                                </CardContent>
                            </Card>
                        </div>

                        <div className="lg:col-span-2">
                            {testResult ? (
                                <Card className="border-2 border-black shadow-brutal h-full">
                                    <CardHeader>
                                        <div className="flex justify-between items-start">
                                            <div>
                                                <CardTitle>Test Results</CardTitle>
                                                <CardDescription>
                                                    Analysis for {testResult.test_type}
                                                </CardDescription>
                                            </div>
                                            <div className="text-right">
                                                <div className="text-sm text-muted-foreground">Bias Score</div>
                                                <div className={`text-3xl font-bold ${getBiasScoreColor(testResult.bias_score)}`}>
                                                    {(testResult.bias_score * 100).toFixed(1)}%
                                                </div>
                                            </div>
                                        </div>
                                    </CardHeader>
                                    <CardContent className="space-y-6">
                                        <div className="bg-muted p-4 rounded-lg border-2 border-black/10">
                                            <Label className="text-xs uppercase text-muted-foreground">Model Response</Label>
                                            <p className="mt-1 font-mono text-sm whitespace-pre-wrap">
                                                {testResult.model_response.response_text}
                                            </p>
                                        </div>

                                        <div className="grid grid-cols-2 gap-4">
                                            <div>
                                                <Label>Confidence</Label>
                                                <Progress value={testResult.confidence_score * 100} className="mt-2" />
                                            </div>
                                            <div>
                                                <Label>Response Time</Label>
                                                <div className="mt-2 font-mono">{testResult.model_response.response_time.toFixed(3)}s</div>
                                            </div>
                                        </div>

                                        <div>
                                            <Label>Explanation</Label>
                                            <p className="text-sm mt-1 text-muted-foreground">{testResult.explanation}</p>
                                        </div>

                                        {testResult.recommendations.length > 0 && (
                                            <div>
                                                <Label>Recommendations</Label>
                                                <ul className="list-disc list-inside text-sm mt-1 space-y-1">
                                                    {testResult.recommendations.map((rec, i) => (
                                                        <li key={i}>{rec}</li>
                                                    ))}
                                                </ul>
                                            </div>
                                        )}
                                    </CardContent>
                                </Card>
                            ) : (
                                <div className="h-full flex items-center justify-center border-2 border-dashed border-gray-300 rounded-lg p-12">
                                    <div className="text-center text-muted-foreground">
                                        <IconActivity className="mx-auto h-12 w-12 mb-4 opacity-20" />
                                        <p>Run a test to see real-time analysis results</p>
                                    </div>
                                </div>
                            )}
                        </div>
                    </div>
                </TabsContent>

                {/* Comprehensive Analysis Tab */}
                <TabsContent value="analysis">
                    <div className="space-y-6">
                        <Card className="border-2 border-black shadow-brutal">
                            <CardHeader>
                                <CardTitle>Comprehensive Bias Analysis</CardTitle>
                                <CardDescription>
                                    Run a full suite of bias tests across multiple demographic groups.
                                    This may take a minute.
                                </CardDescription>
                            </CardHeader>
                            <CardContent>
                                {!analysisResult ? (
                                    <div className="text-center py-12">
                                        <Button
                                            size="lg"
                                            onClick={handleRunAnalysis}
                                            disabled={loading}
                                            className="border-2 border-black shadow-brutal text-lg px-8"
                                        >
                                            {loading ? <IconLoader className="animate-spin mr-2" /> : <IconBrain className="mr-2" />}
                                            Start Full Analysis
                                        </Button>
                                    </div>
                                ) : (
                                    <div className="space-y-8">
                                        {/* Summary Stats */}
                                        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                                            <div className="p-4 border-2 border-black rounded-lg bg-white">
                                                <div className="text-sm text-muted-foreground">Overall Bias Score</div>
                                                <div className={`text-3xl font-bold ${getBiasScoreColor(analysisResult.overall_bias_score)}`}>
                                                    {(analysisResult.overall_bias_score * 100).toFixed(1)}%
                                                </div>
                                            </div>
                                            <div className="p-4 border-2 border-black rounded-lg bg-white">
                                                <div className="text-sm text-muted-foreground">Tests Performed</div>
                                                <div className="text-3xl font-bold">
                                                    {analysisResult.tests_performed.length}
                                                </div>
                                            </div>
                                            <div className="p-4 border-2 border-black rounded-lg bg-white">
                                                <div className="text-sm text-muted-foreground">Risk Level</div>
                                                <div className="text-3xl font-bold uppercase text-orange-600">
                                                    {analysisResult.risk_assessment?.level || 'Unknown'}
                                                </div>
                                            </div>
                                        </div>

                                        {/* Detailed Results Table */}
                                        <div>
                                            <h3 className="text-xl font-bold mb-4">Detailed Test Results</h3>
                                            <div className="border-2 border-black rounded-lg overflow-hidden">
                                                <table className="w-full text-sm">
                                                    <thead className="bg-muted border-b-2 border-black">
                                                        <tr>
                                                            <th className="p-3 text-left">Test Type</th>
                                                            <th className="p-3 text-left">Bias Score</th>
                                                            <th className="p-3 text-left">Findings</th>
                                                            <th className="p-3 text-left">Status</th>
                                                        </tr>
                                                    </thead>
                                                    <tbody>
                                                        {analysisResult.test_results.map((res, i) => (
                                                            <tr key={i} className="border-b border-gray-200 last:border-0 hover:bg-gray-50">
                                                                <td className="p-3 font-medium">{res.test_type}</td>
                                                                <td className={`p-3 font-bold ${getBiasScoreColor(res.bias_score)}`}>
                                                                    {(res.bias_score * 100).toFixed(1)}%
                                                                </td>
                                                                <td className="p-3 text-muted-foreground truncate max-w-xs">
                                                                    {res.explanation}
                                                                </td>
                                                                <td className="p-3">
                                                                    {res.bias_score < 0.1 ? (
                                                                        <Badge className="bg-green-100 text-green-800 border-green-200">Pass</Badge>
                                                                    ) : (
                                                                        <Badge className="bg-red-100 text-red-800 border-red-200">Flagged</Badge>
                                                                    )}
                                                                </td>
                                                            </tr>
                                                        ))}
                                                    </tbody>
                                                </table>
                                            </div>
                                        </div>

                                        <div className="flex justify-end">
                                            <Button variant="noShadow" onClick={() => setAnalysisResult(null)}>
                                                Reset Analysis
                                            </Button>
                                        </div>
                                    </div>
                                )}
                            </CardContent>
                        </Card>
                    </div>
                </TabsContent>
            </Tabs>
        </div>
    )
}
