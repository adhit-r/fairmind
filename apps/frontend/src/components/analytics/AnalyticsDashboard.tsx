'use client';

import { useState, useEffect } from 'react';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Button } from '@/components/ui/button';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { IconDownload, IconRefresh } from '@tabler/icons-react';
import { analyticsService, TrendPoint } from '@/lib/api/analytics-service';

import TrendLineChart from './TrendLineChart';
import ComparisonBarChart from './ComparisonBarChart';
import BiasHeatmap from './BiasHeatmap';
import MetricCard from './MetricCard';

export default function AnalyticsDashboard() {
    const [loading, setLoading] = useState(true);
    const [timeRange, setTimeRange] = useState('30');
    const [trends, setTrends] = useState<TrendPoint[]>([]);
    const [comparison, setComparison] = useState<Record<string, any>>({});

    // Mock data for initial render/fallback
    const mockTrends = [
        { date: '2023-01-01', value: 0.4, details: {} },
        { date: '2023-01-08', value: 0.35, details: {} },
        { date: '2023-01-15', value: 0.32, details: {} },
        { date: '2023-01-22', value: 0.28, details: {} },
        { date: '2023-01-29', value: 0.25, details: {} },
    ];

    const mockComparison = {
        'model_a': { bias_score: 0.25, accuracy: 0.85, fairness: 0.78 },
        'model_b': { bias_score: 0.15, accuracy: 0.82, fairness: 0.88 },
        'model_c': { bias_score: 0.35, accuracy: 0.90, fairness: 0.65 },
    };

    const mockHeatmap = [
        { x: 'Gender', y: 'Occupation', value: 0.4 },
        { x: 'Gender', y: 'Income', value: 0.3 },
        { x: 'Race', y: 'Occupation', value: 0.5 },
        { x: 'Race', y: 'Income', value: 0.45 },
        { x: 'Age', y: 'Occupation', value: 0.2 },
        { x: 'Age', y: 'Income', value: 0.15 },
    ];

    useEffect(() => {
        fetchData();
    }, [timeRange]);

    const fetchData = async () => {
        setLoading(true);
        try {
            // In a real app, we'd fetch actual data
            // const trendRes = await analyticsService.getBiasTrends(undefined, parseInt(timeRange));
            // if (trendRes.success) setTrends(trendRes.data.trends);

            // Using mock data for demonstration as backend might be empty
            setTrends(mockTrends);
            setComparison(mockComparison);
        } catch (error) {
            console.error("Failed to fetch analytics", error);
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="space-y-6">
            <div className="flex justify-between items-center">
                <h2 className="text-3xl font-bold tracking-tight">Analytics Dashboard</h2>
                <div className="flex items-center gap-2">
                    <Select value={timeRange} onValueChange={setTimeRange}>
                        <SelectTrigger className="w-[180px] border-2 border-black">
                            <SelectValue placeholder="Select time range" />
                        </SelectTrigger>
                        <SelectContent>
                            <SelectItem value="7">Last 7 days</SelectItem>
                            <SelectItem value="30">Last 30 days</SelectItem>
                            <SelectItem value="90">Last 90 days</SelectItem>
                        </SelectContent>
                    </Select>
                    <Button variant="neutral" size="icon" onClick={fetchData} className="border-2 border-black">
                        <IconRefresh size={18} />
                    </Button>
                    <Button variant="default" className="border-2 border-black shadow-brutal">
                        <IconDownload size={18} className="mr-2" /> Export
                    </Button>
                </div>
            </div>

            {/* KPI Cards */}
            <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
                <MetricCard
                    title="Avg Bias Score"
                    value="0.28"
                    trend={-12}
                    description="vs last period"
                />
                <MetricCard
                    title="Models Monitored"
                    value="12"
                    trend={2}
                    description="new models"
                />
                <MetricCard
                    title="Compliance Score"
                    value="94%"
                    trend={5}
                    description="all frameworks"
                />
                <MetricCard
                    title="Alerts Triggered"
                    value="3"
                    trend={-50}
                    description="critical issues"
                />
            </div>

            <Tabs defaultValue="overview" className="space-y-4">
                <TabsList className="border-2 border-black p-0 h-auto bg-transparent gap-2">
                    <TabsTrigger
                        value="overview"
                        className="data-[state=active]:bg-black data-[state=active]:text-white border-2 border-transparent data-[state=active]:border-black rounded-none px-4 py-2"
                    >
                        Overview
                    </TabsTrigger>
                    <TabsTrigger
                        value="comparison"
                        className="data-[state=active]:bg-black data-[state=active]:text-white border-2 border-transparent data-[state=active]:border-black rounded-none px-4 py-2"
                    >
                        Model Comparison
                    </TabsTrigger>
                    <TabsTrigger
                        value="heatmap"
                        className="data-[state=active]:bg-black data-[state=active]:text-white border-2 border-transparent data-[state=active]:border-black rounded-none px-4 py-2"
                    >
                        Bias Heatmap
                    </TabsTrigger>
                </TabsList>

                <TabsContent value="overview" className="space-y-4">
                    <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-7">
                        <div className="col-span-4">
                            <TrendLineChart
                                data={trends}
                                title="Bias Score Trend"
                                metricLabel="Avg Bias Score"
                            />
                        </div>
                        <div className="col-span-3">
                            <ComparisonBarChart
                                data={comparison}
                                metrics={['bias_score', 'accuracy']}
                                title="Top Models Performance"
                            />
                        </div>
                    </div>
                </TabsContent>

                <TabsContent value="comparison" className="space-y-4">
                    <ComparisonBarChart
                        data={comparison}
                        metrics={['bias_score', 'accuracy', 'fairness']}
                        title="Detailed Model Comparison"
                    />
                </TabsContent>

                <TabsContent value="heatmap" className="space-y-4">
                    <BiasHeatmap
                        data={mockHeatmap}
                        title="Bias Distribution by Attribute"
                    />
                </TabsContent>
            </Tabs>
        </div>
    );
}
