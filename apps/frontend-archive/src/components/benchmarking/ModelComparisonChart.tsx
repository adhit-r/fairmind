"use client";

import React from 'react';
import {
  Paper,
  Title,
  Text,
  Group,
  Stack,
  Card,
  Badge,
  Progress,
  Table,
  Alert,
  useMantineColorScheme
} from '@mantine/core';
import {
  IconTrophy,
  IconTrendingUp,
  IconTrendingDown,
  IconMinus,
  IconAlertTriangle
} from '@tabler/icons-react';
import ErrorBoundary from '../ErrorBoundary';

interface ModelMetrics {
  model_id: string;
  model_name: string;
  task_type: string;
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
  cpu_usage_percent?: number;
}

interface BenchmarkRun {
  run_id: string;
  benchmark_name: string;
  dataset_id: string;
  task_type: string;
  models: string[];
  metrics: Record<string, ModelMetrics>;
  comparison_results: {
    metrics?: Record<string, Record<string, number>>;
    rankings?: Record<string, Array<{ model_id: string; value: number; rank: number }>>;
    best_models?: Record<string, string>;
    summary?: Record<string, any>;
  };
  created_at: string;
}

interface ModelComparisonChartProps {
  benchmarkRun: BenchmarkRun;
  loading?: boolean;
}

export default function ModelComparisonChart({ benchmarkRun, loading }: ModelComparisonChartProps) {
  const { colorScheme } = useMantineColorScheme();

  const brutalistCardStyle = {
    background: colorScheme === 'dark' ? 'var(--color-black)' : 'var(--color-white)',
    border: '4px solid var(--color-black)',
    borderRadius: '0',
    boxShadow: 'var(--shadow-brutal)',
    transition: 'all var(--transition-duration-fast) ease',
  };

  const getMetricValue = (modelId: string, metricName: string): number | undefined => {
    const metrics = benchmarkRun.metrics[modelId];
    if (!metrics) return undefined;
    return (metrics as any)[metricName];
  };

  const getBestModel = (metricName: string): string | undefined => {
    return benchmarkRun.comparison_results.best_models?.[metricName];
  };

  const getRanking = (modelId: string, metricName: string): number | undefined => {
    const rankings = benchmarkRun.comparison_results.rankings?.[metricName];
    if (!rankings) return undefined;
    const rank = rankings.find(r => r.model_id === modelId);
    return rank?.rank;
  };

  const getRankIcon = (rank: number | undefined) => {
    if (rank === undefined) return <IconMinus size={16} />;
    if (rank === 1) return <IconTrophy size={16} style={{ color: '#fbbf24' }} />;
    if (rank <= 3) return <IconTrendingUp size={16} style={{ color: '#10b981' }} />;
    return <IconTrendingDown size={16} style={{ color: '#ef4444' }} />;
  };

  // Determine relevant metrics based on task type
  const getRelevantMetrics = (): string[] => {
    if (benchmarkRun.task_type === 'classification') {
      return ['accuracy', 'precision', 'recall', 'f1_score', 'roc_auc'];
    } else if (benchmarkRun.task_type === 'regression') {
      return ['r2_score', 'rmse', 'mae', 'mse'];
    }
    return ['accuracy', 'f1_score'];
  };

  const relevantMetrics = getRelevantMetrics();
  const systemMetrics = ['latency_ms', 'throughput_rps', 'memory_usage_mb'];
  const allMetrics = [...relevantMetrics, ...systemMetrics];

  if (loading) {
    return (
      <ErrorBoundary context="ModelComparisonChart">
        <Card p="xl" style={brutalistCardStyle}>
          <Text c="dimmed">Loading comparison data...</Text>
        </Card>
      </ErrorBoundary>
    );
  }

  return (
    <ErrorBoundary context="ModelComparisonChart">
      <Stack gap="md">
        <Paper p="md" style={brutalistCardStyle}>
          <Title order={4} mb="md">Model Comparison</Title>
          
          {benchmarkRun.comparison_results.best_models && (
            <Group gap="md" mb="lg">
              {Object.entries(benchmarkRun.comparison_results.best_models).slice(0, 3).map(([metric, modelId]) => (
                <Card key={metric} p="sm" style={brutalistCardStyle}>
                  <Group gap="xs">
                    <IconTrophy size={16} style={{ color: '#fbbf24' }} />
                    <Text size="sm" fw={600}>
                      Best {metric.replace('_', ' ')}: {benchmarkRun.metrics[modelId]?.model_name || modelId}
                    </Text>
                  </Group>
                </Card>
              ))}
            </Group>
          )}

          <Table>
            <Table.Thead>
              <Table.Tr>
                <Table.Th>Model</Table.Th>
                {allMetrics.map(metric => (
                  <Table.Th key={metric}>
                    <Group gap="xs">
                      {metric.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase())}
                      {getBestModel(metric) && (
                        <IconTrophy size={12} style={{ color: '#fbbf24' }} />
                      )}
                    </Group>
                  </Table.Th>
                ))}
              </Table.Tr>
            </Table.Thead>
            <Table.Tbody>
              {benchmarkRun.models.map(modelId => {
                const metrics = benchmarkRun.metrics[modelId];
                return (
                  <Table.Tr key={modelId}>
                    <Table.Td>
                      <Text fw={600}>{metrics?.model_name || modelId}</Text>
                    </Table.Td>
                    {allMetrics.map(metric => {
                      const value = getMetricValue(modelId, metric);
                      const rank = getRanking(modelId, metric);
                      const isBest = getBestModel(metric) === modelId;
                      
                      return (
                        <Table.Td key={metric}>
                          {value !== undefined ? (
                            <Group gap="xs">
                              {getRankIcon(rank)}
                              <Text size="sm">
                                {metric.includes('score') || metric === 'accuracy' || metric === 'precision' || metric === 'recall' || metric === 'roc_auc'
                                  ? (value * 100).toFixed(1) + '%'
                                  : metric.includes('ms') || metric.includes('mb')
                                  ? value.toFixed(1)
                                  : value.toFixed(3)}
                              </Text>
                              {isBest && (
                                <Badge size="xs" color="yellow">Best</Badge>
                              )}
                            </Group>
                          ) : (
                            <Text size="sm" c="dimmed">-</Text>
                          )}
                        </Table.Td>
                      );
                    })}
                  </Table.Tr>
                );
              })}
            </Table.Tbody>
          </Table>
        </Paper>

        {/* Performance Bars */}
        <Paper p="md" style={brutalistCardStyle}>
          <Title order={4} mb="md">Performance Comparison</Title>
          <Stack gap="md">
            {relevantMetrics.slice(0, 4).map(metric => {
              const values = benchmarkRun.models.map(modelId => ({
                modelId,
                modelName: benchmarkRun.metrics[modelId]?.model_name || modelId,
                value: getMetricValue(modelId, metric) || 0
              })).filter(v => v.value > 0);

              if (values.length === 0) return null;

              const maxValue = Math.max(...values.map(v => v.value));

              return (
                <Card key={metric} p="sm" style={brutalistCardStyle}>
                  <Text size="sm" fw={600} mb="xs">
                    {metric.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase())}
                  </Text>
                  <Stack gap="xs">
                    {values.map(({ modelId, modelName, value }) => {
                      const percentage = (value / maxValue) * 100;
                      const isBest = getBestModel(metric) === modelId;
                      
                      return (
                        <Group key={modelId} gap="sm">
                          <Text size="xs" style={{ width: '120px' }}>{modelName}</Text>
                          <Progress
                            value={percentage}
                            color={isBest ? 'yellow' : 'blue'}
                            style={{ flex: 1 }}
                            size="md"
                          />
                          <Text size="xs" style={{ width: '60px', textAlign: 'right' }}>
                            {metric.includes('score') || metric === 'accuracy' || metric === 'precision' || metric === 'recall' || metric === 'roc_auc'
                              ? (value * 100).toFixed(1) + '%'
                              : value.toFixed(3)}
                          </Text>
                          {isBest && <IconTrophy size={14} style={{ color: '#fbbf24' }} />}
                        </Group>
                      );
                    })}
                  </Stack>
                </Card>
              );
            })}
          </Stack>
        </Paper>
      </Stack>
    </ErrorBoundary>
  );
}

