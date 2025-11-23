"use client";

import React from 'react';
import {
  Card,
  Text,
  Group,
  Stack,
  Badge,
  useMantineColorScheme
} from '@mantine/core';
import {
  IconClock,
  IconCpu,
  IconDatabase,
  IconTrendingUp,
  IconTrendingDown
} from '@tabler/icons-react';

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
}

interface PerformanceMetricsCardProps {
  modelId: string;
  metrics: ModelMetrics;
  taskType: string;
}

export default function PerformanceMetricsCard({ modelId, metrics, taskType }: PerformanceMetricsCardProps) {
  const { colorScheme } = useMantineColorScheme();

  const brutalistCardStyle = {
    background: colorScheme === 'dark' ? 'var(--color-black)' : 'var(--color-white)',
    border: '4px solid var(--color-black)',
    borderRadius: '0',
    boxShadow: 'var(--shadow-brutal)',
    transition: 'all var(--transition-duration-fast) ease',
  };

  const getPrimaryMetric = (): { label: string; value: number | undefined; format: 'percent' | 'decimal' | 'number' } => {
    if (taskType === 'classification') {
      return { label: 'Accuracy', value: metrics.accuracy, format: 'percent' as const };
    } else if (taskType === 'regression') {
      return { label: 'R² Score', value: metrics.r2_score, format: 'decimal' as const };
    }
    return { label: 'Accuracy', value: metrics.accuracy, format: 'percent' as const };
  };

  const formatValue = (value: number | undefined, format: 'percent' | 'decimal' | 'number'): string => {
    if (value === undefined) return '-';
    if (format === 'percent') return (value * 100).toFixed(1) + '%';
    if (format === 'decimal') return value.toFixed(3);
    if (format === 'number') return value.toFixed(1);
    return value.toFixed(1);
  };

  const primaryMetric = getPrimaryMetric();

  return (
    <Card p="md" style={brutalistCardStyle}>
      <Stack gap="sm">
        <Group justify="space-between">
          <Text fw={600} size="sm">{metrics.model_name || modelId}</Text>
          <Badge size="sm">{taskType}</Badge>
        </Group>

        <Group gap="xs">
          <Text size="xs" c="dimmed">{primaryMetric.label}:</Text>
          <Text fw={700} size="lg">
            {formatValue(primaryMetric.value, primaryMetric.format)}
          </Text>
        </Group>

        {taskType === 'classification' && (
          <Stack gap="xs">
            {metrics.f1_score !== undefined && (
              <Group justify="space-between">
                <Text size="xs" c="dimmed">F1 Score:</Text>
                <Text size="sm" fw={500}>{formatValue(metrics.f1_score, 'percent')}</Text>
              </Group>
            )}
            {metrics.precision !== undefined && (
              <Group justify="space-between">
                <Text size="xs" c="dimmed">Precision:</Text>
                <Text size="sm" fw={500}>{formatValue(metrics.precision, 'percent')}</Text>
              </Group>
            )}
            {metrics.recall !== undefined && (
              <Group justify="space-between">
                <Text size="xs" c="dimmed">Recall:</Text>
                <Text size="sm" fw={500}>{formatValue(metrics.recall, 'percent')}</Text>
              </Group>
            )}
            {metrics.roc_auc !== undefined && (
              <Group justify="space-between">
                <Text size="xs" c="dimmed">ROC AUC:</Text>
                <Text size="sm" fw={500}>{formatValue(metrics.roc_auc, 'percent')}</Text>
              </Group>
            )}
          </Stack>
        )}

        {taskType === 'regression' && (
          <Stack gap="xs">
            {metrics.rmse !== undefined && (
              <Group justify="space-between">
                <Text size="xs" c="dimmed">RMSE:</Text>
                <Text size="sm" fw={500}>{formatValue(metrics.rmse, 'decimal')}</Text>
              </Group>
            )}
            {metrics.mae !== undefined && (
              <Group justify="space-between">
                <Text size="xs" c="dimmed">MAE:</Text>
                <Text size="sm" fw={500}>{formatValue(metrics.mae, 'decimal')}</Text>
              </Group>
            )}
            {metrics.mse !== undefined && (
              <Group justify="space-between">
                <Text size="xs" c="dimmed">MSE:</Text>
                <Text size="sm" fw={500}>{formatValue(metrics.mse, 'decimal')}</Text>
              </Group>
            )}
          </Stack>
        )}

        {(metrics.latency_ms !== undefined || metrics.memory_usage_mb !== undefined || metrics.throughput_rps !== undefined) && (
          <Stack gap="xs" mt="xs" pt="xs" style={{ borderTop: '1px solid var(--color-gray-300)' }}>
            {metrics.latency_ms !== undefined && (
              <Group gap="xs" justify="space-between">
                <Group gap="xs">
                  <IconClock size={14} />
                  <Text size="xs" c="dimmed">Latency:</Text>
                </Group>
                <Text size="sm" fw={500}>{formatValue(metrics.latency_ms, 'number')} ms</Text>
              </Group>
            )}
            {metrics.throughput_rps !== undefined && (
              <Group gap="xs" justify="space-between">
                <Group gap="xs">
                  <IconTrendingUp size={14} />
                  <Text size="xs" c="dimmed">Throughput:</Text>
                </Group>
                <Text size="sm" fw={500}>{formatValue(metrics.throughput_rps, 'number')} rps</Text>
              </Group>
            )}
            {metrics.memory_usage_mb !== undefined && (
              <Group gap="xs" justify="space-between">
                <Group gap="xs">
                  <IconDatabase size={14} />
                  <Text size="xs" c="dimmed">Memory:</Text>
                </Group>
                <Text size="sm" fw={500}>{formatValue(metrics.memory_usage_mb, 'number')} MB</Text>
              </Group>
            )}
            {metrics.cpu_usage_percent !== undefined && (
              <Group gap="xs" justify="space-between">
                <Group gap="xs">
                  <IconCpu size={14} />
                  <Text size="xs" c="dimmed">CPU:</Text>
                </Group>
                <Text size="sm" fw={500}>{formatValue(metrics.cpu_usage_percent, 'number')}%</Text>
              </Group>
            )}
          </Stack>
        )}
      </Stack>
    </Card>
  );
}

