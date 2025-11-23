"use client";

import React from 'react';
import {
  Card,
  Text,
  Group,
  Stack,
  Badge,
  Button,
  Loader,
  Alert,
  useMantineColorScheme
} from '@mantine/core';
import {
  IconChartBar,
  IconClock,
  IconUsers,
  IconAlertTriangle,
  IconRefresh
} from '@tabler/icons-react';
import ErrorBoundary from '../ErrorBoundary';

interface BenchmarkRun {
  run_id: string;
  benchmark_name: string;
  dataset_id: string;
  task_type: string;
  models: string[];
  created_at: string;
}

interface BenchmarkRunListProps {
  runs: BenchmarkRun[];
  loading?: boolean;
  onRunSelect: (runId: string) => void;
  selectedRunId: string | null;
}

export default function BenchmarkRunList({ runs, loading, onRunSelect, selectedRunId }: BenchmarkRunListProps) {
  const { colorScheme } = useMantineColorScheme();

  const brutalistCardStyle = {
    background: colorScheme === 'dark' ? 'var(--color-black)' : 'var(--color-white)',
    border: '4px solid var(--color-black)',
    borderRadius: '0',
    boxShadow: 'var(--shadow-brutal)',
    transition: 'all var(--transition-duration-fast) ease',
  };

  const selectedCardStyle = {
    ...brutalistCardStyle,
    border: '4px solid var(--color-orange)',
    boxShadow: 'var(--shadow-brutal), 0 0 0 2px var(--color-yellow-500)',
  };

  if (loading) {
    return (
      <ErrorBoundary context="BenchmarkRunList">
        <Card p="xl" style={brutalistCardStyle}>
          <Group justify="center">
            <Loader size="md" />
            <Text c="dimmed">Loading benchmark runs...</Text>
          </Group>
        </Card>
      </ErrorBoundary>
    );
  }

  if (runs.length === 0) {
    return (
      <ErrorBoundary context="BenchmarkRunList">
        <Card p="xl" style={brutalistCardStyle}>
          <Alert icon={<IconAlertTriangle size={16} />} title="No benchmark runs found" color="yellow">
            No benchmark runs have been created yet. Create a benchmark run to compare model performance.
          </Alert>
        </Card>
      </ErrorBoundary>
    );
  }

  return (
    <ErrorBoundary context="BenchmarkRunList">
      <Stack gap="md">
        {runs.map((run) => (
          <Card
            key={run.run_id}
            p="md"
            onClick={() => onRunSelect(run.run_id)}
            style={{
              cursor: 'pointer',
              ...(selectedRunId === run.run_id ? selectedCardStyle : brutalistCardStyle)
            }}
            onMouseEnter={(e) => {
              if (selectedRunId !== run.run_id) {
                e.currentTarget.style.transform = 'translateY(-2px)';
                e.currentTarget.style.boxShadow = 'var(--shadow-brutal), 0 4px 8px rgba(0,0,0,0.1)';
              }
            }}
            onMouseLeave={(e) => {
              if (selectedRunId !== run.run_id) {
                e.currentTarget.style.transform = 'translateY(0)';
                e.currentTarget.style.boxShadow = 'var(--shadow-brutal)';
              }
            }}
          >
            <Group justify="space-between" align="flex-start">
              <Stack gap="xs" style={{ flex: 1 }}>
                <Group gap="sm">
                  <IconChartBar size={20} />
                  <Text fw={600} size="lg">{run.benchmark_name}</Text>
                  <Badge size="sm">{run.task_type}</Badge>
                </Group>
                <Text size="sm" c="dimmed">
                  Dataset: {run.dataset_id}
                </Text>
                <Group gap="md" mt="xs">
                  <Group gap="xs">
                    <IconUsers size={16} />
                    <Text size="xs" c="dimmed">{run.models.length} models</Text>
                  </Group>
                  <Group gap="xs">
                    <IconClock size={16} />
                    <Text size="xs" c="dimmed">
                      {new Date(run.created_at).toLocaleString()}
                    </Text>
                  </Group>
                </Group>
              </Stack>
              <Button
                variant="light"
                size="sm"
                onClick={(e) => {
                  e.stopPropagation();
                  onRunSelect(run.run_id);
                }}
                style={{
                  border: '2px solid var(--color-black)',
                  boxShadow: 'var(--shadow-brutal)',
                }}
              >
                View Details
              </Button>
            </Group>
          </Card>
        ))}
      </Stack>
    </ErrorBoundary>
  );
}

