'use client'

/**
 * Simplified Bias Detection Page - Neo-Brutalist Design
 * Single workflow: Upload CSV → Run Analysis → View Results
 */

import { useState } from 'react'
import { IconUpload, IconAlertTriangle, IconCheck, IconX, IconLoader, IconArrowRight, IconChartBar } from '@tabler/icons-react'
import { apiClient } from '@/lib/api/api-client'

interface BiasResult {
    score: number
    passed: boolean
    disparity: number
    group_scores: Record<string, number>
    interpretation: string
    recommendations: string[]
}

interface BiasTestResponse {
    test_id: string
    model_id: string
    timestamp: string
    overall_risk: 'low' | 'medium' | 'high' | 'critical'
    metrics_passed: number
    metrics_failed: number
    results: Record<string, BiasResult>
    summary: string
    recommendations: string[]
}

export default function BiasDetectionPage() {
    // Mode Selection
    const [mode, setMode] = useState<'tabular' | 'llm'>('tabular')

    // Step 1: Upload
    const [file, setFile] = useState<File | null>(null)
    const [uploading, setUploading] = useState(false)
    const [datasetId, setDatasetId] = useState<string | null>(null)
    const [columns, setColumns] = useState<string[]>([])

    // Step 2: Configure
    const [modelId, setModelId] = useState('')
    const [protectedAttr, setProtectedAttr] = useState<string>('')
    const [predictionCol, setPredictionCol] = useState<string>('')
    const [groundTruthCol, setGroundTruthCol] = useState<string>('')

    // LLM Config
    const [promptCol, setPromptCol] = useState<string>('')
    const [responseCol, setResponseCol] = useState<string>('')

    const [threshold, setThreshold] = useState(0.8)
    const [selectedMetrics, setSelectedMetrics] = useState<string[]>([
        'demographic_parity',
        'equalized_odds',
        'equal_opportunity'
    ])

    // Step 3: Results
    const [analyzing, setAnalyzing] = useState(false)
    const [results, setResults] = useState<BiasTestResponse | null>(null)
    const [error, setError] = useState<string | null>(null)

    // Reset state when switching modes
    const toggleMode = (newMode: 'tabular' | 'llm') => {
        setMode(newMode)
        setResults(null)
        setError(null)
        if (newMode === 'llm') {
            setSelectedMetrics(['sentiment_disparity', 'stereotyping', 'counterfactual_fairness'])
        } else {
            setSelectedMetrics(['demographic_parity', 'equalized_odds', 'equal_opportunity'])
        }
    }

    const handleUpload = async () => {
        if (!file) return

        setUploading(true)
        setError(null)

        try {
            const formData = new FormData()
            formData.append('file', file)
            const response = await apiClient.post<any>('/api/v1/bias-v2/upload-dataset', formData)
            if (!response.success || !response.data) {
                throw new Error(response.error || 'Upload failed')
            }

            const data = response.data
            setDatasetId(data.dataset_id)
            setColumns(data.columns)

            // Auto-detect common column names
            if (mode === 'tabular') {
                if (data.columns.includes('prediction')) setPredictionCol('prediction')
                if (data.columns.includes('gender')) setProtectedAttr('gender')
                if (data.columns.includes('ground_truth')) setGroundTruthCol('ground_truth')
            } else {
                if (data.columns.includes('prompt')) setPromptCol('prompt')
                if (data.columns.includes('response')) setResponseCol('response')
            }

        } catch (err) {
            setError(err instanceof Error ? err.message : 'Upload failed')
        } finally {
            setUploading(false)
        }
    }

    const handleAnalyze = async () => {
        if (!datasetId) return

        setAnalyzing(true)
        setError(null)

        try {
            const endpoint = mode === 'tabular' ? '/api/v1/bias-v2/detect' : '/api/v1/bias-v2/detect-llm'

            const body = mode === 'tabular' ? {
                model_id: modelId || 'test-model',
                dataset_id: datasetId,
                protected_attribute: protectedAttr,
                prediction_column: predictionCol,
                ground_truth_column: groundTruthCol || null,
                fairness_threshold: threshold,
                metrics: selectedMetrics
            } : {
                model_id: modelId || 'llm-model',
                dataset_id: datasetId,
                prompt_column: promptCol,
                response_column: responseCol,
                metrics: selectedMetrics
            }

            const response = await apiClient.post<BiasTestResponse>(endpoint, body)

            if (!response.success || !response.data) {
                throw new Error(response.error || 'Analysis failed')
            }

            setResults(response.data)

        } catch (err) {
            setError(err instanceof Error ? err.message : 'Analysis failed')
        } finally {
            setAnalyzing(false)
        }
    }

    const getRiskColor = (risk: string) => {
        switch (risk) {
            case 'low': return 'bg-[#a3e635] text-black' // Lime
            case 'medium': return 'bg-[#fde047] text-black' // Yellow
            case 'high': return 'bg-[#fb923c] text-black' // Orange
            case 'critical': return 'bg-[#f87171] text-black' // Red
            default: return 'bg-white text-black'
        }
    }

    const toggleMetric = (metric: string) => {
        if (selectedMetrics.includes(metric)) {
            setSelectedMetrics(selectedMetrics.filter(m => m !== metric))
        } else {
            setSelectedMetrics([...selectedMetrics, metric])
        }
    }

    return (
        <div className="p-8 max-w-6xl mx-auto space-y-8 font-sans">
            <div className="p-8 flex justify-between items-center fm-card">
                <div>
                    <h1 className="text-4xl font-semibold text-black tracking-tight">Bias Detection</h1>
                    <p className="text-lg font-medium text-gray-600 mt-2">Production-Ready Fairness Analysis</p>
                </div>

                {/* Mode Toggle */}
                <div className="flex bg-gray-100 p-1 rounded-[14px] shadow-[var(--fm-shadow)]">
                    <button
                        onClick={() => toggleMode('tabular')}
                        className={`px-6 py-2 font-semibold transition-all ${mode === 'tabular' ? 'bg-black text-white ' : 'text-gray-500 hover:text-black'}`}
                    >
                        Tabular (ML)
                    </button>
                    <button
                        onClick={() => toggleMode('llm')}
                        className={`px-6 py-2 font-semibold transition-all ${mode === 'llm' ? 'bg-black text-white ' : 'text-gray-500 hover:text-black'}`}
                    >
                        Text (LLM)
                    </button>
                </div>
            </div>

            {error && (
                <div className="bg-[#f87171] text-black px-4 py-3 font-bold flex items-center gap-2 rounded-[14px] shadow-[var(--fm-shadow)]">
                    <IconAlertTriangle size={24} stroke={2} />
                    <span>{error}</span>
                </div>
            )}

            {/* Step 1: Upload Dataset */}
            <div className="p-6 transition-all fm-card">
                <div className="flex items-center gap-3 mb-6">
                    <div className="bg-black text-white w-10 h-10 flex items-center justify-center font-semibold text-xl border border-[var(--fm-line)]">1</div>
                    <h3 className="text-2xl font-bold">Upload Dataset</h3>
                </div>

                <p className="text-base font-medium text-gray-600 mb-6">
                    {mode === 'tabular'
                        ? 'Upload a CSV file with model predictions and protected attributes (gender, race, age, etc.)'
                        : 'Upload a CSV file with prompts and model responses for text analysis.'}
                </p>

                <div className="flex flex-col md:flex-row items-start md:items-center gap-4">
                    <input
                        type="file"
                        accept=".csv"
                        onChange={(e) => setFile(e.target.files?.[0] || null)}
                        disabled={!!datasetId}
                        className="block w-full text-[13.5px] text-[var(--fm-ink2)] file:mr-4 file:h-9 file:cursor-pointer file:rounded-full file:border-0 file:bg-[var(--fm-ink)] file:px-4 file:text-[12.5px] file:font-semibold file:text-white hover:file:bg-black"
                    />

                    <button
                        onClick={handleUpload}
                        disabled={!file || !!datasetId || uploading}
                        className={`flex items-center gap-2 px-6 py-3 border border-[var(--fm-line)] font-bold transition-all
              ${!file || !!datasetId || uploading
                                ? 'bg-gray-200 text-gray-400 cursor-not-allowed'
                                : 'bg-[#fb7185] text-black hover:bg-[#f43f5e]'}`}
                    >
                        {uploading ? <IconLoader className="animate-spin" size={20} stroke={2} /> : <IconUpload size={20} stroke={2} />}
                        UPLOAD CSV
                    </button>
                </div>

                {datasetId && (
                    <div className="mt-6 bg-[#86efac] text-black px-4 py-3 font-bold flex items-center gap-2 rounded-[14px] shadow-[var(--fm-shadow)]">
                        <IconCheck size={24} stroke={2} />
                        <span>Dataset uploaded! ID: {datasetId} • {columns.length} columns detected</span>
                    </div>
                )}
            </div>

            {/* Step 2: Configure Analysis */}
            {datasetId && (
                <div className="p-6 transition-all fm-card">
                    <div className="flex items-center gap-3 mb-6">
                        <div className="bg-black text-white w-10 h-10 flex items-center justify-center font-semibold text-xl border border-[var(--fm-line)]">2</div>
                        <h3 className="text-2xl font-bold">Configure Analysis</h3>
                    </div>

                    {mode === 'tabular' ? (
                        // Tabular Configuration
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                            <div>
                                <label className="block text-sm font-semibold text-black mb-2 tracking-wide">Protected Attribute</label>
                                <select
                                    className="w-full p-3 font-medium focus:outline-none focus:ring-0 focus:bg-blue-50 fm-card"
                                    value={protectedAttr}
                                    onChange={(e) => setProtectedAttr(e.target.value)}
                                >
                                    <option value="">SELECT COLUMN...</option>
                                    {columns.map(col => <option key={col} value={col}>{col}</option>)}
                                </select>
                            </div>

                            <div>
                                <label className="block text-sm font-semibold text-black mb-2 tracking-wide">Prediction Column</label>
                                <select
                                    className="w-full p-3 font-medium focus:outline-none focus:ring-0 focus:bg-blue-50 fm-card"
                                    value={predictionCol}
                                    onChange={(e) => setPredictionCol(e.target.value)}
                                >
                                    <option value="">SELECT COLUMN...</option>
                                    {columns.map(col => <option key={col} value={col}>{col}</option>)}
                                </select>
                            </div>

                            <div>
                                <label className="block text-sm font-semibold text-black mb-2 tracking-wide">Ground Truth (Optional)</label>
                                <select
                                    className="w-full p-3 font-medium focus:outline-none focus:ring-0 focus:bg-blue-50 fm-card"
                                    value={groundTruthCol}
                                    onChange={(e) => setGroundTruthCol(e.target.value)}
                                >
                                    <option value="">NONE</option>
                                    {columns.map(col => <option key={col} value={col}>{col}</option>)}
                                </select>
                            </div>

                            <div>
                                <label className="block text-sm font-semibold text-black mb-2 tracking-wide">Fairness Threshold (0.8 = 80%)</label>
                                <input
                                    type="number"
                                    min="0.5"
                                    max="1.0"
                                    step="0.05"
                                    className="w-full p-3 font-medium focus:outline-none focus:ring-0 focus:bg-blue-50 fm-card"
                                    value={threshold}
                                    onChange={(e) => setThreshold(parseFloat(e.target.value))}
                                />
                            </div>
                        </div>
                    ) : (
                        // LLM Configuration
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                            <div>
                                <label className="block text-sm font-semibold text-black mb-2 tracking-wide">Prompt Column</label>
                                <select
                                    className="w-full p-3 font-medium focus:outline-none focus:ring-0 focus:bg-blue-50 fm-card"
                                    value={promptCol}
                                    onChange={(e) => setPromptCol(e.target.value)}
                                >
                                    <option value="">SELECT COLUMN...</option>
                                    {columns.map(col => <option key={col} value={col}>{col}</option>)}
                                </select>
                            </div>

                            <div>
                                <label className="block text-sm font-semibold text-black mb-2 tracking-wide">Response Column</label>
                                <select
                                    className="w-full p-3 font-medium focus:outline-none focus:ring-0 focus:bg-blue-50 fm-card"
                                    value={responseCol}
                                    onChange={(e) => setResponseCol(e.target.value)}
                                >
                                    <option value="">SELECT COLUMN...</option>
                                    {columns.map(col => <option key={col} value={col}>{col}</option>)}
                                </select>
                            </div>
                        </div>
                    )}

                    <div className="mt-8">
                        <label className="block text-sm font-semibold text-black mb-3 tracking-wide">Metrics</label>
                        <div className="flex flex-wrap gap-4">
                            {(mode === 'tabular' ? [
                                { id: 'demographic_parity', label: 'Demographic Parity' },
                                { id: 'equalized_odds', label: 'Equalized Odds' },
                                { id: 'equal_opportunity', label: 'Equal Opportunity' },
                                { id: 'predictive_parity', label: 'Predictive Parity' }
                            ] : [
                                { id: 'sentiment_disparity', label: 'Sentiment Disparity' },
                                { id: 'stereotyping', label: 'Stereotype Analysis' },
                                { id: 'counterfactual_fairness', label: 'Counterfactual Fairness (SOTA)' }
                            ]).map(metric => (
                                <button
                                    key={metric.id}
                                    onClick={() => toggleMetric(metric.id)}
                                    className={`px-4 py-2 font-bold border border-[var(--fm-line)] transition-all
                    ${selectedMetrics.includes(metric.id)
                                            ? 'bg-[#67e8f9] text-black'
                                            : 'bg-white text-gray-500 hover:bg-gray-50'}`}
                                >
                                    {metric.label}
                                </button>
                            ))}
                        </div>
                    </div>

                    <button
                        onClick={handleAnalyze}
                        disabled={analyzing || (mode === 'tabular' ? (!protectedAttr || !predictionCol) : (!promptCol || !responseCol))}
                        className={`mt-10 w-full flex justify-center items-center gap-3 py-4 px-6 border border-[var(--fm-line)] font-semibold text-lg uppercase tracking-wider transition-all
              ${analyzing || (mode === 'tabular' ? (!protectedAttr || !predictionCol) : (!promptCol || !responseCol))
                                ? 'bg-gray-200 text-gray-400 cursor-not-allowed'
                                : 'bg-[#c084fc] text-black hover:bg-[#a855f7]'}`}
                    >
                        {analyzing ? (
                            <>
                                <IconLoader className="animate-spin" size={24} stroke={3} /> PROCESSING...
                            </>
                        ) : (
                            <>
                                RUN {mode === 'tabular' ? 'BIAS' : 'LLM'} ANALYSIS <IconArrowRight size={24} stroke={3} />
                            </>
                        )}
                    </button>
                </div>
            )}

            {/* Step 3: Results */}
            {results && (
                <div className="p-6 fm-card">
                    <div className="flex flex-col md:flex-row justify-between items-start md:items-center mb-8 gap-4">
                        <div className="flex items-center gap-3">
                            <div className="bg-black text-white w-10 h-10 flex items-center justify-center font-semibold text-xl border border-[var(--fm-line)]">3</div>
                            <div>
                                <h3 className="text-2xl font-bold">Analysis Results</h3>
                                <p className="text-sm font-bold text-gray-500">ID: {results.test_id}</p>
                            </div>
                        </div>
                        <span className={`px-6 py-2 font-semibold text-xl ${getRiskColor(results.overall_risk)} rounded-[14px] shadow-[var(--fm-shadow)]`}>
                            {results.overall_risk} RISK
                        </span>
                    </div>

                    <div className={`p-6 mb-8 ${getRiskColor(results.overall_risk)} rounded-[14px] shadow-[var(--fm-shadow)]`}>
                        <div className="flex gap-4 items-start">
                            {results.overall_risk === 'low' ? <IconCheck size={32} stroke={3} /> : <IconAlertTriangle size={32} stroke={3} />}
                            <p className="font-bold text-lg leading-tight">{results.summary}</p>
                        </div>
                    </div>

                    <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-10">
                        <div className="p-6 text-center fm-card">
                            <p className="text-sm font-semibold text-gray-500 mb-2">Metrics Passed</p>
                            <p className="text-5xl font-semibold text-[#16a34a]">{results.metrics_passed}</p>
                        </div>
                        <div className="p-6 text-center fm-card">
                            <p className="text-sm font-semibold text-gray-500 mb-2">Metrics Failed</p>
                            <p className="text-5xl font-semibold text-[#dc2626]">{results.metrics_failed}</p>
                        </div>
                    </div>

                    {/* Detailed Results */}
                    <h4 className="text-xl font-semibold mb-6 flex items-center gap-2">
                        <IconChartBar size={24} stroke={3} /> Detailed Metrics
                    </h4>
                    <div className="space-y-8">
                        {Object.entries(results.results).map(([metric, result]) => (
                            <div key={metric} className="p-6 fm-card">
                                <div className="flex justify-between items-center mb-4">
                                    <h5 className="font-bold text-lg capitalize">{metric.replace(/_/g, ' ')}</h5>
                                    {result.passed ? (
                                        <span className="px-3 py-1 bg-[#86efac] text-black border border-[var(--fm-line)] text-xs font-semibold uppercase flex items-center gap-1">
                                            <IconCheck size={14} stroke={3} /> PASS
                                        </span>
                                    ) : (
                                        <span className="px-3 py-1 bg-[#fca5a5] text-black border border-[var(--fm-line)] text-xs font-semibold uppercase flex items-center gap-1">
                                            <IconX size={14} stroke={3} /> FAIL
                                        </span>
                                    )}
                                </div>

                                <div className="w-full bg-gray-200 h-4 border border-[var(--fm-line)] mb-2">
                                    <div
                                        className={`h-full ${result.passed ? 'bg-[#22c55e]' : 'bg-[#ef4444]'}`}
                                        style={{ width: `${Math.min(result.score * 100, 100)}%` }}
                                    ></div>
                                </div>
                                <p className="text-sm font-bold text-gray-600 mb-4">
                                    Score: {(result.score * 100).toFixed(1)}% {mode === 'tabular' && `(Threshold: ${(threshold * 100).toFixed(0)}%)`}
                                </p>

                                <p className="text-base font-medium text-black mb-6 leading-relaxed">{result.interpretation}</p>

                                {/* Group Scores */}
                                <div className="overflow-x-auto border border-[var(--fm-line)]">
                                    <table className="min-w-full divide-y-2 divide-black">
                                        <thead className="bg-gray-100">
                                            <tr>
                                                <th className="px-4 py-3 text-left text-xs font-semibold text-black uppercase tracking-wider">Group</th>
                                                <th className="px-4 py-3 text-left text-xs font-semibold text-black uppercase tracking-wider">Rate</th>
                                            </tr>
                                        </thead>
                                        <tbody className="bg-white divide-y-2 divide-black">
                                            {Object.entries(result.group_scores).map(([group, score]) => (
                                                <tr key={group}>
                                                    <td className="px-4 py-3 whitespace-nowrap text-sm font-bold text-black">{group}</td>
                                                    <td className="px-4 py-3 whitespace-nowrap text-sm font-medium text-gray-700">{(score * 100).toFixed(1)}%</td>
                                                </tr>
                                            ))}
                                        </tbody>
                                    </table>
                                </div>
                            </div>
                        ))}
                    </div>

                    {/* Recommendations */}
                    <h4 className="text-xl font-semibold mt-10 mb-6">Recommendations</h4>
                    <div className="space-y-4">
                        {results.recommendations.map((rec, idx) => (
                            <div key={idx} className="bg-[#bfdbfe] p-4 rounded-[14px] shadow-[var(--fm-shadow)]">
                                <p className="font-bold text-black">{rec}</p>
                            </div>
                        ))}
                    </div>
                </div>
            )}
        </div>
    )
}
