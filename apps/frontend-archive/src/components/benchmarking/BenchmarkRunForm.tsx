"use client";

import React, { useState } from 'react';
import {
  Paper,
  Title,
  Text,
  Group,
  Stack,
  TextInput,
  Select,
  Textarea,
  Button,
  Card,
  Alert,
  NumberInput,
  Divider,
  useMantineColorScheme
} from '@mantine/core';
import {
  IconPlayerPlay,
  IconAlertTriangle,
  IconCheck,
  IconX,
  IconPlus,
  IconTrash
} from '@tabler/icons-react';
import ErrorBoundary from '../ErrorBoundary';
import { useApi } from '../../hooks/useApi';

interface ModelPrediction {
  model_id: string;
  model_name: string;
  predictions: any[];
  metadata?: {
    latency_ms?: number;
    memory_usage_mb?: number;
    throughput_rps?: number;
    cpu_usage_percent?: number;
  };
}

interface BenchmarkRunFormProps {
  onSuccess?: (runId: string) => void;
  onCancel?: () => void;
}

export default function BenchmarkRunForm({ onSuccess, onCancel }: BenchmarkRunFormProps) {
  const { colorScheme } = useMantineColorScheme();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  const [formData, setFormData] = useState({
    benchmark_name: '',
    dataset_id: '',
    task_type: 'classification',
    ground_truth: '',
    models: [] as ModelPrediction[]
  });

  const brutalistCardStyle = {
    background: colorScheme === 'dark' ? 'var(--color-black)' : 'var(--color-white)',
    border: '4px solid var(--color-black)',
    borderRadius: '0',
    boxShadow: 'var(--shadow-brutal)',
    transition: 'all var(--transition-duration-fast) ease',
  };

  const addModel = () => {
    setFormData({
      ...formData,
      models: [
        ...formData.models,
        {
          model_id: `model-${formData.models.length + 1}`,
          model_name: '',
          predictions: [],
          metadata: {}
        }
      ]
    });
  };

  const removeModel = (index: number) => {
    setFormData({
      ...formData,
      models: formData.models.filter((_, i) => i !== index)
    });
  };

  const updateModel = (index: number, field: keyof ModelPrediction, value: any) => {
    const updatedModels = [...formData.models];
    updatedModels[index] = {
      ...updatedModels[index],
      [field]: value
    };
    setFormData({
      ...formData,
      models: updatedModels
    });
  };

  const updateModelMetadata = (index: number, field: string, value: number | undefined) => {
    const updatedModels = [...formData.models];
    updatedModels[index] = {
      ...updatedModels[index],
      metadata: {
        ...updatedModels[index].metadata,
        [field]: value
      }
    };
    setFormData({
      ...formData,
      models: updatedModels
    });
  };

  const parseArray = (value: string): any[] => {
    try {
      // Try parsing as JSON array
      const parsed = JSON.parse(value);
      if (Array.isArray(parsed)) return parsed;
      return [];
    } catch {
      // Try parsing as comma-separated values
      return value.split(',').map(v => v.trim()).filter(v => v);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    setSuccess(null);

    try {
      // Validate form
      if (!formData.benchmark_name.trim()) {
        throw new Error('Benchmark name is required');
      }
      if (!formData.dataset_id.trim()) {
        throw new Error('Dataset ID is required');
      }
      if (formData.models.length === 0) {
        throw new Error('At least one model is required');
      }
      if (!formData.ground_truth.trim()) {
        throw new Error('Ground truth is required');
      }

      // Parse ground truth
      const groundTruth = parseArray(formData.ground_truth);

      // Prepare model predictions
      const modelPredictions: Record<string, any[]> = {};
      const modelMetadata: Record<string, Record<string, any>> = {};

      formData.models.forEach(model => {
        if (!model.model_id || !model.model_name) {
          throw new Error('All models must have an ID and name');
        }
        if (model.predictions.length === 0) {
          throw new Error(`Model ${model.model_name} must have predictions`);
        }
        if (model.predictions.length !== groundTruth.length) {
          throw new Error(`Model ${model.model_name} predictions length (${model.predictions.length}) must match ground truth length (${groundTruth.length})`);
        }

        modelPredictions[model.model_id] = model.predictions;
        modelMetadata[model.model_id] = {
          name: model.model_name,
          ...model.metadata
        };
      });

      // Call API
      const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
      const response = await fetch(`${API_BASE}/api/v1/model-performance/run-benchmark`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          benchmark_name: formData.benchmark_name,
          dataset_id: formData.dataset_id,
          task_type: formData.task_type,
          model_predictions: modelPredictions,
          ground_truth: groundTruth,
          model_metadata: modelMetadata
        })
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
      }

      const result = await response.json();
      setSuccess(`Benchmark run created successfully! Run ID: ${result.run_id}`);
      
      if (onSuccess) {
        onSuccess(result.run_id);
      }

      // Reset form after 2 seconds
      setTimeout(() => {
        setFormData({
          benchmark_name: '',
          dataset_id: '',
          task_type: 'classification',
          ground_truth: '',
          models: []
        });
        setSuccess(null);
      }, 2000);

    } catch (err: any) {
      setError(err.message || 'Failed to create benchmark run');
    } finally {
      setLoading(false);
    }
  };

  return (
    <ErrorBoundary context="BenchmarkRunForm">
      <Paper p="xl" style={brutalistCardStyle}>
        <Title order={3} mb="md">Run New Benchmark</Title>
        <Text c="dimmed" size="sm" mb="lg">
          Create a new benchmark run to compare multiple models on the same dataset.
        </Text>

        <form onSubmit={handleSubmit}>
          <Stack gap="md">
            {error && (
              <Alert icon={<IconAlertTriangle size={16} />} title="Error" color="red">
                {error}
              </Alert>
            )}

            {success && (
              <Alert icon={<IconCheck size={16} />} title="Success" color="green">
                {success}
              </Alert>
            )}

            <TextInput
              label="Benchmark Name"
              placeholder="e.g., Credit Risk Model Comparison"
              required
              value={formData.benchmark_name}
              onChange={(e) => setFormData({ ...formData, benchmark_name: e.target.value })}
              style={{
                border: '4px solid var(--color-black)',
                borderRadius: '0',
                boxShadow: 'var(--shadow-brutal)',
              }}
            />

            <TextInput
              label="Dataset ID"
              placeholder="e.g., credit-risk-dataset-1"
              required
              value={formData.dataset_id}
              onChange={(e) => setFormData({ ...formData, dataset_id: e.target.value })}
              style={{
                border: '4px solid var(--color-black)',
                borderRadius: '0',
                boxShadow: 'var(--shadow-brutal)',
              }}
            />

            <Select
              label="Task Type"
              required
              data={[
                { value: 'classification', label: 'Classification' },
                { value: 'regression', label: 'Regression' },
                { value: 'text_generation', label: 'Text Generation' },
                { value: 'image_classification', label: 'Image Classification' },
                { value: 'multimodal', label: 'Multimodal' }
              ]}
              value={formData.task_type}
              onChange={(value) => value && setFormData({ ...formData, task_type: value })}
              style={{
                border: '4px solid var(--color-black)',
                borderRadius: '0',
                boxShadow: 'var(--shadow-brutal)',
              }}
            />

            <Textarea
              label="Ground Truth"
              placeholder='Enter ground truth values as JSON array or comma-separated: [0, 1, 0, 1, 0] or "0, 1, 0, 1, 0"'
              required
              minRows={3}
              value={formData.ground_truth}
              onChange={(e) => setFormData({ ...formData, ground_truth: e.target.value })}
              style={{
                border: '4px solid var(--color-black)',
                borderRadius: '0',
                boxShadow: 'var(--shadow-brutal)',
              }}
            />

            <Divider my="md" />

            <Group justify="space-between" align="center">
              <Title order={4}>Models</Title>
              <Button
                leftSection={<IconPlus size={16} />}
                onClick={addModel}
                variant="light"
                size="sm"
                style={{
                  border: '2px solid var(--color-black)',
                  boxShadow: 'var(--shadow-brutal)',
                }}
              >
                Add Model
              </Button>
            </Group>

            {formData.models.length === 0 && (
              <Alert icon={<IconAlertTriangle size={16} />} color="yellow">
                Add at least one model to run the benchmark.
              </Alert>
            )}

            {formData.models.map((model, index) => (
              <Card key={index} p="md" style={brutalistCardStyle}>
                <Stack gap="sm">
                  <Group justify="space-between">
                    <Title order={5}>Model {index + 1}</Title>
                    <Button
                      leftSection={<IconTrash size={14} />}
                      onClick={() => removeModel(index)}
                      variant="light"
                      color="red"
                      size="xs"
                      style={{
                        border: '2px solid var(--color-black)',
                        boxShadow: 'var(--shadow-brutal)',
                      }}
                    >
                      Remove
                    </Button>
                  </Group>

                  <TextInput
                    label="Model ID"
                    placeholder="e.g., model-1"
                    required
                    value={model.model_id}
                    onChange={(e) => updateModel(index, 'model_id', e.target.value)}
                    style={{
                      border: '2px solid var(--color-black)',
                      boxShadow: 'var(--shadow-brutal)',
                    }}
                  />

                  <TextInput
                    label="Model Name"
                    placeholder="e.g., Random Forest"
                    required
                    value={model.model_name}
                    onChange={(e) => updateModel(index, 'model_name', e.target.value)}
                    style={{
                      border: '2px solid var(--color-black)',
                      boxShadow: 'var(--shadow-brutal)',
                    }}
                  />

                  <Textarea
                    label="Predictions"
                    placeholder='Enter predictions as JSON array or comma-separated: [0, 1, 0, 1, 0] or "0, 1, 0, 1, 0"'
                    required
                    minRows={3}
                    value={Array.isArray(model.predictions) ? JSON.stringify(model.predictions) : ''}
                    onChange={(e) => {
                      const parsed = parseArray(e.target.value);
                      updateModel(index, 'predictions', parsed);
                    }}
                    style={{
                      border: '2px solid var(--color-black)',
                      boxShadow: 'var(--shadow-brutal)',
                    }}
                  />

                  <Title order={6} mt="sm">System Metrics (Optional)</Title>
                  <Group grow>
                    <NumberInput
                      label="Latency (ms)"
                      placeholder="e.g., 50.5"
                      value={model.metadata?.latency_ms}
                      onChange={(value) => updateModelMetadata(index, 'latency_ms', typeof value === 'number' ? value : undefined)}
                      style={{
                        border: '2px solid var(--color-black)',
                        boxShadow: 'var(--shadow-brutal)',
                      }}
                    />
                    <NumberInput
                      label="Memory (MB)"
                      placeholder="e.g., 256.0"
                      value={model.metadata?.memory_usage_mb}
                      onChange={(value) => updateModelMetadata(index, 'memory_usage_mb', typeof value === 'number' ? value : undefined)}
                      style={{
                        border: '2px solid var(--color-black)',
                        boxShadow: 'var(--shadow-brutal)',
                      }}
                    />
                  </Group>
                  <Group grow>
                    <NumberInput
                      label="Throughput (rps)"
                      placeholder="e.g., 100.0"
                      value={model.metadata?.throughput_rps}
                      onChange={(value) => updateModelMetadata(index, 'throughput_rps', typeof value === 'number' ? value : undefined)}
                      style={{
                        border: '2px solid var(--color-black)',
                        boxShadow: 'var(--shadow-brutal)',
                      }}
                    />
                    <NumberInput
                      label="CPU Usage (%)"
                      placeholder="e.g., 45.0"
                      value={model.metadata?.cpu_usage_percent}
                      onChange={(value) => updateModelMetadata(index, 'cpu_usage_percent', typeof value === 'number' ? value : undefined)}
                      style={{
                        border: '2px solid var(--color-black)',
                        boxShadow: 'var(--shadow-brutal)',
                      }}
                    />
                  </Group>
                </Stack>
              </Card>
            ))}

            <Group justify="flex-end" mt="lg">
              {onCancel && (
                <Button
                  variant="outline"
                  onClick={onCancel}
                  leftSection={<IconX size={16} />}
                  style={{
                    border: '2px solid var(--color-black)',
                    boxShadow: 'var(--shadow-brutal)',
                  }}
                >
                  Cancel
                </Button>
              )}
              <Button
                type="submit"
                loading={loading}
                leftSection={!loading && <IconPlayerPlay size={16} />}
                style={{
                  border: '2px solid var(--color-black)',
                  boxShadow: 'var(--shadow-brutal)',
                  background: 'var(--color-orange)',
                  color: 'var(--color-white)',
                }}
              >
                {loading ? 'Running Benchmark...' : 'Run Benchmark'}
              </Button>
            </Group>
          </Stack>
        </form>
      </Paper>
    </ErrorBoundary>
  );
}

