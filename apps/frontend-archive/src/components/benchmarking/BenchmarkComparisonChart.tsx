"use client";

import React, { useState } from 'react';
import {
  Paper,
  Title,
  Text,
  Group,
  Stack,
  Card,
  Select,
  Tabs,
  useMantineColorScheme
} from '@mantine/core';
import {
  BarChart,
  LineChart,
  AreaChart
} from '@mantine/charts';
import {
  IconChartBar,
  IconTrendingUp,
  IconChartLine
} from '@tabler/icons-react';
import ErrorBoundary from '../ErrorBoundary';

interface ModelMetrics {
  model_id: string;
  model_name: string;
  accuracy?: number;
  precision?: number;
  recall?: number;
  f1_score?: number;
  roc_auc?: number;
  mse?: number;
  rmse?: number;
  mae?: number;
  r2_score?: number;
  latency_ms?: number;
  throughput_rps?: number;
  memory_usage_mb?: number;
}

interface BenchmarkRun {
  run_id: string;
  benchmark_name: string;
  task_type: string;
  models: string[];
  metrics: Record<string, ModelMetrics>;
  comparison_results: {
    rankings?: Record<string, Array<{ model_id: string; value: number; rank: number }>>;
    best_models?: Record<string, string>;
  };
}

interface BenchmarkComparisonChartProps {
  benchmarkRun: BenchmarkRun;
  loading?: boolean;
}

export default function BenchmarkComparisonChart({ benchmarkRun, loading }: BenchmarkComparisonChartProps) {
  const { colorScheme } = useMantineColorScheme();
  const [selectedMetric, setSelectedMetric] = useState<string>('accuracy');
  const [chartType, setChartType] = useState<'bar' | 'line' | 'area'>('bar');

  const brutalistCardStyle = {
    background: colorScheme === 'dark' ? 'var(--color-black)' : 'var(--color-white)',
    border: '4px solid var(--color-black)',
    borderRadius: '0',
    boxShadow: 'var(--shadow-brutal)',
    transition: 'all var(--transition-duration-fast) ease',
  };

  // Get available metrics based on task type
  const getAvailableMetrics = (): string[] => {
    if (benchmarkRun.task_type === 'classification') {
      return ['accuracy', 'precision', 'recall', 'f1_score', 'roc_auc'];
    } else if (benchmarkRun.task_type === 'regression') {
      return ['r2_score', 'rmse', 'mae', 'mse'];
    }
    return ['accuracy', 'f1_score'];
  };

  const availableMetrics = getAvailableMetrics();

  // Prepare chart data
  const prepareChartData = () => {
    return benchmarkRun.models.map(modelId => {
      const metrics = benchmarkRun.metrics[modelId];
      const value = (metrics as any)[selectedMetric];
      return {
        model: metrics?.model_name || modelId,
        value: value !== undefined ? (selectedMetric.includes('score') || selectedMetric === 'accuracy' || selectedMetric === 'precision' || selectedMetric === 'recall' || selectedMetric === 'roc_auc' ? value * 100 : value) : 0,
        modelId
      };
    }).filter(item => item.value > 0);
  };

  const chartData = prepareChartData();

  // Get best model for selected metric
  const bestModel = benchmarkRun.comparison_results.best_models?.[selectedMetric];

  if (loading) {
    return (
      <ErrorBoundary context="BenchmarkComparisonChart">
        <Card p="xl" style={brutalistCardStyle}>
          <Text c="dimmed">Loading chart data...</Text>
        </Card>
      </ErrorBoundary>
    );
  }

  const renderChart = () => {
    const commonProps = {
      data: chartData,
      dataKey: 'model',
      series: [{ name: 'value', color: 'var(--color-orange)', label: selectedMetric.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase()) }],
      h: 300,
      withLegend: false,
      withTooltip: true,
      withDots: true,
      withGradient: false,
      gridAxis: 'xy' as const,
    };

    switch (chartType) {
      case 'bar':
        return <BarChart {...commonProps} />;
      case 'line':
        return <LineChart {...commonProps} curveType="natural" />;
      case 'area':
        return <AreaChart {...commonProps} curveType="natural" />;
      default:
        return <BarChart {...commonProps} />;
    }
  };

  return (
    <ErrorBoundary context="BenchmarkComparisonChart">
      <Stack gap="md">
        <Paper p="md" style={brutalistCardStyle}>
          <Group justify="space-between" mb="md">
            <Title order={4}>Performance Comparison</Title>
            <Group gap="sm">
              <Select
                value={selectedMetric}
                onChange={(value) => value && setSelectedMetric(value)}
                data={availableMetrics.map(metric => ({
                  value: metric,
                  label: metric.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase())
                }))}
                size="sm"
                style={{ width: '150px' }}
              />
              <Tabs value={chartType} onChange={(value) => setChartType(value as 'bar' | 'line' | 'area')}>
                <Tabs.List>
                  <Tabs.Tab value="bar" leftSection={<IconChartBar size={14} />}>
                    Bar
                  </Tabs.Tab>
                  <Tabs.Tab value="line" leftSection={<IconTrendingUp size={14} />}>
                    Line
                  </Tabs.Tab>
                  <Tabs.Tab value="area" leftSection={<IconChartLine size={14} />}>
                    Area
                  </Tabs.Tab>
                </Tabs.List>
              </Tabs>
            </Group>
          </Group>

          {chartData.length > 0 ? (
            <>
              {bestModel && (
                <Text size="sm" c="dimmed" mb="md">
                  Best {selectedMetric.replace('_', ' ')}: {benchmarkRun.metrics[bestModel]?.model_name || bestModel}
                </Text>
              )}
              {renderChart()}
            </>
          ) : (
            <Text c="dimmed" ta="center" py="xl">
              No data available for {selectedMetric}
            </Text>
          )}
        </Paper>
      </Stack>
    </ErrorBoundary>
  );
}

