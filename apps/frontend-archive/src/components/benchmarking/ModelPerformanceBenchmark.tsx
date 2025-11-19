"use client";

import React, { useState } from 'react';
import {
  Paper,
  Title,
  Text,
  Group,
  Stack,
  Grid,
  Button,
  Select,
  Card,
  Badge,
  Alert,
  Tabs,
  Divider,
  useMantineColorScheme
} from '@mantine/core';
import {
  IconChartBar,
  IconRefresh,
  IconDownload,
  IconAlertTriangle,
  IconCheck,
  IconTrophy,
  IconClock,
  IconCpu,
  IconDatabase,
  IconPlus
} from '@tabler/icons-react';
import ErrorBoundary from '../ErrorBoundary';
import { ChartSkeleton } from '../LoadingSkeleton';
import ModelComparisonChart from './ModelComparisonChart';
import BenchmarkComparisonChart from './BenchmarkComparisonChart';
import PerformanceTrendChart from './PerformanceTrendChart';
import PerformanceMetricsCard from './PerformanceMetricsCard';
import BenchmarkRunList from './BenchmarkRunList';
import BenchmarkRunForm from './BenchmarkRunForm';
import { useApi } from '../../hooks/useApi';

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
  demographic_parity?: number;
  equalized_odds?: number;
  equal_opportunity?: number;
  timestamp?: string;
  metadata?: Record<string, any>;
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
  metadata?: Record<string, any>;
}

interface BenchmarkRunsResponse {
  success: boolean;
  runs: Array<{
    run_id: string;
    benchmark_name: string;
    dataset_id: string;
    task_type: string;
    models: string[];
    created_at: string;
  }>;
  total: number;
}

export default function ModelPerformanceBenchmark() {
  const { colorScheme } = useMantineColorScheme();
  const [selectedRunId, setSelectedRunId] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<string>('runs');
  const [showForm, setShowForm] = useState<boolean>(false);

  const brutalistCardStyle = {
    background: colorScheme === 'dark' ? 'var(--color-black)' : 'var(--color-white)',
    border: '4px solid var(--color-black)',
    borderRadius: '0',
    boxShadow: 'var(--shadow-brutal)',
    transition: 'all var(--transition-duration-fast) ease',
  };

  // Fetch benchmark runs
  const { data: runsData, loading: runsLoading, error: runsError, retry: retryRuns } = useApi<BenchmarkRunsResponse>(
    '/api/v1/model-performance/benchmark-runs?limit=10',
    {
      fallbackData: { success: true, runs: [], total: 0 },
      enableRetry: true,
      cacheKey: 'benchmark-runs'
    }
  );

  // Fetch selected benchmark run details
  const { data: runData, loading: runLoading, error: runError, retry: retryRun } = useApi<{ success: boolean; run: BenchmarkRun }>(
    selectedRunId ? `/api/v1/model-performance/benchmark-runs/${selectedRunId}` : '',
    {
      fallbackData: null,
      enableRetry: true,
      cacheKey: selectedRunId ? `benchmark-run-${selectedRunId}` : undefined
    }
  );

  const handleRunSelect = (runId: string) => {
    setSelectedRunId(runId);
    setActiveTab('details');
  };

  const handleExport = () => {
    if (runData?.run) {
      const dataStr = JSON.stringify(runData.run, null, 2);
      const dataBlob = new Blob([dataStr], { type: 'application/json' });
      const url = URL.createObjectURL(dataBlob);
      const link = document.createElement('a');
      link.href = url;
      link.download = `benchmark-${runData.run.run_id}.json`;
      link.click();
      URL.revokeObjectURL(url);
    }
  };

  if (runsLoading && !runsData) {
    return (
      <ErrorBoundary context="ModelPerformanceBenchmark">
        <ChartSkeleton />
      </ErrorBoundary>
    );
  }

  if (runsError && !runsData) {
    return (
      <ErrorBoundary context="ModelPerformanceBenchmark">
        <Card p="xl" style={{
          ...brutalistCardStyle,
          border: '2px solid rgba(239, 68, 68, 0.8)',
        }}>
          <Stack align="center" gap="md">
            <Alert icon={<IconAlertTriangle size={16} />} title="Failed to load benchmark data" color="red">
              {runsError?.message || 'Unable to fetch benchmark runs.'}
            </Alert>
            <Button onClick={retryRuns} leftSection={<IconRefresh size={16} />} variant="light" color="blue">
              Retry
            </Button>
          </Stack>
        </Card>
      </ErrorBoundary>
    );
  }

  const handleFormSuccess = (runId: string) => {
    setShowForm(false);
    setSelectedRunId(runId);
    setActiveTab('details');
    // Refresh runs list
    retryRuns();
  };

  return (
    <ErrorBoundary context="ModelPerformanceBenchmark">
      <Stack gap="lg">
        {showForm && (
          <BenchmarkRunForm
            onSuccess={handleFormSuccess}
            onCancel={() => setShowForm(false)}
          />
        )}

        <Paper p="xl" style={brutalistCardStyle}>
          <Group justify="space-between" mb="md">
            <Title order={2}>
              <Group gap="sm">
                <IconChartBar size={28} />
                Model Performance Benchmarking
              </Group>
            </Title>
            <Group>
              <Button
                leftSection={<IconPlus size={16} />}
                onClick={() => setShowForm(!showForm)}
                variant="light"
                style={{
                  border: '4px solid var(--color-black)',
                  borderRadius: '0',
                  boxShadow: 'var(--shadow-brutal)',
                }}
              >
                {showForm ? 'Hide Form' : 'New Benchmark'}
              </Button>
              {runData?.run && (
                <Button
                  leftSection={<IconDownload size={16} />}
                  onClick={handleExport}
                  variant="light"
                  style={{
                    border: '2px solid var(--color-black)',
                    boxShadow: 'var(--shadow-brutal)',
                  }}
                >
                  Export Report
                </Button>
              )}
            </Group>
          </Group>

          <Text c="dimmed" size="sm" mb="lg">
            Compare model performance across multiple metrics including accuracy, latency, and fairness.
          </Text>

          <Tabs value={activeTab} onChange={(value) => setActiveTab(value || 'runs')}>
            <Tabs.List>
              <Tabs.Tab value="runs" leftSection={<IconChartBar size={16} />}>
                Benchmark Runs
              </Tabs.Tab>
              {selectedRunId && (
                <>
                  <Tabs.Tab value="details" leftSection={<IconCheck size={16} />}>
                    Run Details
                  </Tabs.Tab>
                  <Tabs.Tab value="comparison" leftSection={<IconTrophy size={16} />}>
                    Model Comparison
                  </Tabs.Tab>
                </>
              )}
            </Tabs.List>

            <Tabs.Panel value="runs" pt="md">
              <BenchmarkRunList
                runs={runsData?.runs || []}
                loading={runsLoading}
                onRunSelect={handleRunSelect}
                selectedRunId={selectedRunId}
              />
            </Tabs.Panel>

            {selectedRunId && (
              <>
                <Tabs.Panel value="details" pt="md">
                  {runLoading ? (
                    <ChartSkeleton />
                  ) : runError ? (
                    <Alert icon={<IconAlertTriangle size={16} />} title="Failed to load benchmark run" color="red">
                      {runError?.message || 'Unable to fetch benchmark run details.'}
                      <Button onClick={retryRun} leftSection={<IconRefresh size={16} />} variant="light" color="blue" mt="md">
                        Retry
                      </Button>
                    </Alert>
                  ) : runData?.run ? (
                    <Stack gap="md">
                      <Card p="md" style={brutalistCardStyle}>
                        <Group justify="space-between" mb="sm">
                          <Title order={4}>{runData.run.benchmark_name}</Title>
                          <Badge>{runData.run.task_type}</Badge>
                        </Group>
                        <Text size="sm" c="dimmed" mb="md">
                          Dataset: {runData.run.dataset_id} • {runData.run.models.length} models • {new Date(runData.run.created_at).toLocaleString()}
                        </Text>
                        <Divider mb="md" />
                        <Grid>
                          {Object.entries(runData.run.metrics).map(([modelId, metrics]) => (
                            <Grid.Col key={modelId} span={{ base: 12, sm: 6, lg: 4 }}>
                              <PerformanceMetricsCard
                                modelId={modelId}
                                metrics={metrics}
                                taskType={runData.run.task_type}
                              />
                            </Grid.Col>
                          ))}
                        </Grid>
                      </Card>
                    </Stack>
                  ) : null}
                </Tabs.Panel>

                <Tabs.Panel value="comparison" pt="md">
                  {runData?.run ? (
                    <Stack gap="md">
                      <ModelComparisonChart
                        benchmarkRun={runData.run}
                        loading={runLoading}
                      />
                      <BenchmarkComparisonChart
                        benchmarkRun={runData.run}
                        loading={runLoading}
                      />
                    </Stack>
                  ) : (
                    <Alert icon={<IconAlertTriangle size={16} />} title="No benchmark run selected" color="yellow">
                      Please select a benchmark run to view comparisons.
                    </Alert>
                  )}
                </Tabs.Panel>
              </>
            )}
          </Tabs>
        </Paper>
      </Stack>
    </ErrorBoundary>
  );
}

