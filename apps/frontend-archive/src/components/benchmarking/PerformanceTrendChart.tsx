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
  useMantineColorScheme
} from '@mantine/core';
import {
  LineChart,
  AreaChart
} from '@mantine/charts';
import {
  IconTrendingUp,
  IconClock
} from '@tabler/icons-react';
import ErrorBoundary from '../ErrorBoundary';

interface ModelPerformanceHistory {
  model_id: string;
  model_name: string;
  timestamp: string;
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

interface PerformanceTrendChartProps {
  modelId: string;
  history: ModelPerformanceHistory[];
  loading?: boolean;
}

export default function PerformanceTrendChart({ modelId, history, loading }: PerformanceTrendChartProps) {
  const { colorScheme } = useMantineColorScheme();
  const [selectedMetric, setSelectedMetric] = useState<string>('accuracy');

  const brutalistCardStyle = {
    background: colorScheme === 'dark' ? 'var(--color-black)' : 'var(--color-white)',
    border: '4px solid var(--color-black)',
    borderRadius: '0',
    boxShadow: 'var(--shadow-brutal)',
    transition: 'all var(--transition-duration-fast) ease',
  };

  // Get available metrics from history
  const getAvailableMetrics = (): string[] => {
    if (history.length === 0) return [];
    const firstRecord = history[0];
    return Object.keys(firstRecord).filter(key => 
      key !== 'model_id' && 
      key !== 'model_name' && 
      key !== 'timestamp' && 
      (firstRecord as any)[key] !== undefined &&
      typeof (firstRecord as any)[key] === 'number'
    );
  };

  const availableMetrics = getAvailableMetrics();

  // Prepare chart data
  const prepareChartData = () => {
    return history
      .map(record => {
        const value = (record as any)[selectedMetric];
        return {
          date: new Date(record.timestamp).toLocaleDateString(),
          timestamp: record.timestamp,
          value: value !== undefined ? (selectedMetric.includes('score') || selectedMetric === 'accuracy' || selectedMetric === 'precision' || selectedMetric === 'recall' || selectedMetric === 'roc_auc' ? value * 100 : value) : null,
        };
      })
      .filter(item => item.value !== null)
      .sort((a, b) => new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime());
  };

  const chartData = prepareChartData();

  if (loading) {
    return (
      <ErrorBoundary context="PerformanceTrendChart">
        <Card p="xl" style={brutalistCardStyle}>
          <Text c="dimmed">Loading trend data...</Text>
        </Card>
      </ErrorBoundary>
    );
  }

  if (history.length === 0) {
    return (
      <ErrorBoundary context="PerformanceTrendChart">
        <Card p="xl" style={brutalistCardStyle}>
          <Text c="dimmed" ta="center">No historical data available</Text>
        </Card>
      </ErrorBoundary>
    );
  }

  return (
    <ErrorBoundary context="PerformanceTrendChart">
      <Paper p="md" style={brutalistCardStyle}>
        <Group justify="space-between" mb="md">
          <Title order={4}>
            <Group gap="xs">
              <IconTrendingUp size={20} />
              Performance Trend: {history[0]?.model_name || modelId}
            </Group>
          </Title>
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
        </Group>

        {chartData.length > 0 ? (
          <AreaChart
            h={300}
            data={chartData}
            dataKey="date"
            series={[{ name: 'value', color: 'var(--color-orange)', label: selectedMetric.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase()) }]}
            curveType="natural"
            withLegend={false}
            withTooltip={true}
            withDots={true}
            withGradient={true}
            gridAxis="xy"
          />
        ) : (
          <Text c="dimmed" ta="center" py="xl">
            No data available for {selectedMetric}
          </Text>
        )}
      </Paper>
    </ErrorBoundary>
  );
}

