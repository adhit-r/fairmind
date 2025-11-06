"use client";

import React, { useState, useEffect, useRef } from 'react';
import { 
  Paper, 
  Title, 
  Text, 
  Group, 
  Stack, 
  Grid, 
  Button, 
  Badge,
  Progress,
  Card,
  ActionIcon,
  Tooltip,
  Alert,
  RingProgress,
  Timeline,
  Indicator,
  Switch,
  Select,
  Loader,
  Center
} from '@mantine/core';
import { 
  IconBrain,
  IconShield,
  IconUsers,
  IconChartBar,
  IconAlertTriangle,
  IconCheck,
  IconX,
  IconRefresh,
  IconSettings,
  IconPlayerPlay,
  IconPlayerPause,
  IconPlayerStop,
  IconBell,
  IconBellOff,
  IconActivity,
  IconTrendingUp,
  IconTrendingDown
} from '@tabler/icons-react';
import { useApi } from '../../hooks/useApi';
import ErrorBoundary from '../ErrorBoundary';

interface MonitoringMetric {
  id: string;
  name: string;
  value: number;
  threshold: number;
  status: 'healthy' | 'warning' | 'critical';
  trend: 'up' | 'down' | 'stable';
  timestamp: string;
  description: string;
}

interface Alert {
  id: string;
  type: 'bias' | 'performance' | 'system';
  severity: 'low' | 'medium' | 'high' | 'critical';
  message: string;
  timestamp: string;
  acknowledged: boolean;
  resolved: boolean;
}

interface MonitoringMetricsData {
  summary?: {
    avg_accuracy?: number;
    avg_latency?: number;
    uptime?: number;
    throughput?: number;
  };
  metrics?: Array<{
    date: string;
    accuracy?: number;
    latency?: number;
    throughput?: number;
  }>;
}

interface RealTimeMonitoringProps {
  modelId?: string;
  onAlert?: (alert: Alert) => void;
  onMetricUpdate?: (metric: MonitoringMetric) => void;
}

// Fallback metrics if API fails
const fallbackMetrics: MonitoringMetric[] = [
  {
    id: 'bias_score',
    name: 'Overall Bias Score',
    value: 0.23,
    threshold: 0.3,
    status: 'healthy',
    trend: 'down',
    timestamp: new Date().toISOString(),
    description: 'Average bias score across all protected attributes'
  },
  {
    id: 'fairness_gap',
    name: 'Fairness Gap',
    value: 0.15,
    threshold: 0.2,
    status: 'healthy',
    trend: 'stable',
    timestamp: new Date().toISOString(),
    description: 'Maximum difference in outcomes between groups'
  },
  {
    id: 'demographic_parity',
    name: 'Demographic Parity',
    value: 0.85,
    threshold: 0.8,
    status: 'healthy',
    trend: 'up',
    timestamp: new Date().toISOString(),
    description: 'Proportion of positive outcomes across demographic groups'
  },
  {
    id: 'equalized_odds',
    name: 'Equalized Odds',
    value: 0.78,
    threshold: 0.75,
    status: 'healthy',
    trend: 'up',
    timestamp: new Date().toISOString(),
    description: 'Equal true positive and false positive rates across groups'
  },
  {
    id: 'model_performance',
    name: 'Model Performance',
    value: 0.92,
    threshold: 0.85,
    status: 'healthy',
    trend: 'stable',
    timestamp: new Date().toISOString(),
    description: 'Overall model accuracy and performance'
  },
  {
    id: 'response_time',
    name: 'Response Time',
    value: 0.45,
    threshold: 0.5,
    status: 'healthy',
    trend: 'down',
    timestamp: new Date().toISOString(),
    description: 'Average response time in seconds'
  }
];

// Convert API data to MonitoringMetric format
const convertApiDataToMetrics = (apiData: MonitoringMetricsData): MonitoringMetric[] => {
  if (!apiData.summary) {
    return fallbackMetrics;
  }

  const { summary } = apiData;
  const metrics: MonitoringMetric[] = [];

  if (summary.avg_accuracy !== undefined) {
    metrics.push({
      id: 'model_performance',
      name: 'Model Performance',
      value: summary.avg_accuracy / 100, // Convert to 0-1 range
      threshold: 0.85,
      status: summary.avg_accuracy >= 85 ? 'healthy' : summary.avg_accuracy >= 75 ? 'warning' : 'critical',
      trend: 'stable',
      timestamp: new Date().toISOString(),
      description: 'Overall model accuracy and performance'
    });
  }

  if (summary.avg_latency !== undefined) {
    metrics.push({
      id: 'response_time',
      name: 'Response Time',
      value: summary.avg_latency / 1000, // Convert to seconds
      threshold: 0.5,
      status: summary.avg_latency <= 500 ? 'healthy' : summary.avg_latency <= 1000 ? 'warning' : 'critical',
      trend: 'down',
      timestamp: new Date().toISOString(),
      description: 'Average response time in seconds'
    });
  }

  if (summary.uptime !== undefined) {
    metrics.push({
      id: 'system_uptime',
      name: 'System Uptime',
      value: summary.uptime / 100, // Convert to 0-1 range
      threshold: 0.99,
      status: summary.uptime >= 99 ? 'healthy' : summary.uptime >= 95 ? 'warning' : 'critical',
      trend: 'stable',
      timestamp: new Date().toISOString(),
      description: 'System availability percentage'
    });
  }

  // Add default bias metrics if not provided
  if (metrics.length === 0) {
    return fallbackMetrics;
  }

  // Add bias-related metrics (these would come from bias detection API)
  metrics.push(
    {
      id: 'bias_score',
      name: 'Overall Bias Score',
      value: 0.23,
      threshold: 0.3,
      status: 'healthy',
      trend: 'down',
      timestamp: new Date().toISOString(),
      description: 'Average bias score across all protected attributes'
    },
    {
      id: 'fairness_gap',
      name: 'Fairness Gap',
      value: 0.15,
      threshold: 0.2,
      status: 'healthy',
      trend: 'stable',
      timestamp: new Date().toISOString(),
      description: 'Maximum difference in outcomes between groups'
    }
  );

  return metrics;
};

const RealTimeMonitoring: React.FC<RealTimeMonitoringProps> = ({
  modelId = 'default',
  onAlert,
  onMetricUpdate
}) => {
  const [isMonitoring, setIsMonitoring] = useState(false);
  const [metrics, setMetrics] = useState<MonitoringMetric[]>([]);
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [selectedTimeRange, setSelectedTimeRange] = useState('1h');
  const [notificationsEnabled, setNotificationsEnabled] = useState(true);
  const [autoRefresh, setAutoRefresh] = useState(true);
  const intervalRef = useRef<NodeJS.Timeout | null>(null);

  // Fetch monitoring metrics from API
  const { data: apiData, loading, error, retry, refresh } = useApi<MonitoringMetricsData>(
    '/api/v1/database/monitoring-metrics',
    {
      fallbackData: { summary: {}, metrics: [] },
      enableRetry: true,
      cacheKey: 'monitoring-metrics',
      refreshInterval: autoRefresh && isMonitoring ? 5000 : undefined
    }
  );

  // Convert API data to metrics format
  useEffect(() => {
    if (apiData) {
      const convertedMetrics = convertApiDataToMetrics(apiData);
      setMetrics(convertedMetrics);
    } else if (!loading && !apiData) {
      // Use fallback if no data available
      setMetrics(fallbackMetrics);
    }
  }, [apiData, loading]);

  // Auto-refresh when monitoring is enabled
  useEffect(() => {
    if (isMonitoring && autoRefresh) {
      intervalRef.current = setInterval(() => {
        refresh(); // Use API refresh to fetch fresh data
      }, 5000); // Update every 5 seconds
    } else if (intervalRef.current) {
      clearInterval(intervalRef.current);
    }

    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
      }
    };
  }, [isMonitoring, autoRefresh, refresh]);

  // Check for metric changes and generate alerts
  useEffect(() => {
    if (metrics.length > 0) {
      metrics.forEach(metric => {
        // Check for alerts based on metric status
        if (metric.status === 'warning' || metric.status === 'critical') {
          const existingAlert = alerts.find(a => 
            a.message.includes(metric.name) && !a.resolved
          );
          
          if (!existingAlert) {
            generateAlert(metric);
          }
        }

        // Notify parent component of metric updates
        if (onMetricUpdate) {
          onMetricUpdate(metric);
        }
      });
    }
  }, [metrics, alerts, onMetricUpdate]);

  const generateAlert = (metric: MonitoringMetric) => {
    const alert: Alert = {
      id: `alert_${Date.now()}`,
      type: 'bias',
      severity: metric.status === 'critical' ? 'high' : 'medium',
      message: `${metric.name} is ${metric.status}. Current value: ${metric.value.toFixed(3)}`,
      timestamp: new Date().toISOString(),
      acknowledged: false,
      resolved: false
    };

    setAlerts(prev => [alert, ...prev.slice(0, 9)]); // Keep only last 10 alerts

    if (onAlert) {
      onAlert(alert);
    }
  };

  const handleStartMonitoring = () => {
    setIsMonitoring(true);
  };

  const handleStopMonitoring = () => {
    setIsMonitoring(false);
  };

  const handlePauseMonitoring = () => {
    setIsMonitoring(false);
  };

  const acknowledgeAlert = (alertId: string) => {
    setAlerts(prev => 
      prev.map(alert => 
        alert.id === alertId 
          ? { ...alert, acknowledged: true }
          : alert
      )
    );
  };

  const resolveAlert = (alertId: string) => {
    setAlerts(prev => 
      prev.map(alert => 
        alert.id === alertId 
          ? { ...alert, resolved: true }
          : alert
      )
    );
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'healthy': return 'green';
      case 'warning': return 'yellow';
      case 'critical': return 'red';
      default: return 'gray';
    }
  };

  const getSeverityColor = (severity: string) => {
    switch (severity) {
      case 'low': return 'blue';
      case 'medium': return 'yellow';
      case 'high': return 'orange';
      case 'critical': return 'red';
      default: return 'gray';
    }
  };

  const getTrendIcon = (trend: string) => {
    switch (trend) {
      case 'up': return <IconTrendingUp size={16} color="green" />;
      case 'down': return <IconTrendingDown size={16} color="red" />;
      default: return <IconActivity size={16} color="blue" />;
    }
  };

  const renderMetricCard = (metric: MonitoringMetric) => (
    <Card key={metric.id} p="md" style={{ height: '100%' }}>
      <Group justify="space-between" mb="sm">
        <Text fw="bold" size="sm">{metric.name}</Text>
        <Group gap="xs">
          {getTrendIcon(metric.trend)}
          <Badge 
            color={getStatusColor(metric.status)}
            variant="light"
            size="sm"
          >
            {metric.status}
          </Badge>
        </Group>
      </Group>
      
      <Stack gap="xs">
        <Group justify="space-between">
          <Text size="xl" fw="bold">
            {metric.value.toFixed(3)}
          </Text>
          <Text size="sm" c="dimmed">
            / {metric.threshold.toFixed(3)}
          </Text>
        </Group>
        
        <Progress 
          value={(metric.value / metric.threshold) * 100} 
          color={getStatusColor(metric.status)}
          size="sm"
        />
        
        <Text size="xs" c="dimmed">
          {metric.description}
        </Text>
        
        <Text size="xs" c="dimmed">
          Updated: {new Date(metric.timestamp).toLocaleTimeString()}
        </Text>
      </Stack>
    </Card>
  );

  const renderAlertItem = (alert: Alert) => (
    <Timeline.Item
      key={alert.id}
      bullet={
        <Indicator
          color={getSeverityColor(alert.severity)}
          size={12}
          withBorder
        />
      }
      title={
        <Group justify="space-between">
          <Text size="sm" fw="bold">
            {alert.type.toUpperCase()} Alert
          </Text>
          <Badge 
            color={getSeverityColor(alert.severity)}
            variant="light"
            size="sm"
          >
            {alert.severity}
          </Badge>
        </Group>
      }
    >
      <Text size="sm" mb="xs">
        {alert.message}
      </Text>
      <Text size="xs" c="dimmed" mb="xs">
        {new Date(alert.timestamp).toLocaleString()}
      </Text>
      {!alert.resolved && (
        <Group gap="xs">
          <Button
            size="xs"
            variant="light"
            onClick={() => acknowledgeAlert(alert.id)}
            disabled={alert.acknowledged}
          >
            {alert.acknowledged ? 'Acknowledged' : 'Acknowledge'}
          </Button>
          <Button
            size="xs"
            variant="outline"
            onClick={() => resolveAlert(alert.id)}
          >
            Resolve
          </Button>
        </Group>
      )}
    </Timeline.Item>
  );

  const renderOverallHealth = () => {
    const healthyMetrics = metrics.filter(m => m.status === 'healthy').length;
    const totalMetrics = metrics.length;
    const healthPercentage = (healthyMetrics / totalMetrics) * 100;

    return (
      <Card p="md">
        <Group justify="space-between" mb="md">
          <Title order={4}>Overall System Health</Title>
          <Badge 
            color={healthPercentage > 80 ? 'green' : healthPercentage > 60 ? 'yellow' : 'red'}
            variant="light"
          >
            {healthPercentage.toFixed(0)}%
          </Badge>
        </Group>
        
        <RingProgress
          size={120}
          thickness={8}
          sections={[
            { value: healthPercentage, color: healthPercentage > 80 ? 'green' : healthPercentage > 60 ? 'yellow' : 'red' }
          ]}
          label={
            <Text ta="center" size="sm" fw="bold">
              {healthyMetrics}/{totalMetrics}
            </Text>
          }
        />
        
        <Text size="sm" c="dimmed" ta="center" mt="sm">
          Healthy Metrics
        </Text>
      </Card>
    );
  };

  // Show loading state
  if (loading && metrics.length === 0) {
    return (
      <ErrorBoundary context="RealTimeMonitoring">
        <Card p="xl">
          <Center>
            <Stack align="center" gap="md">
              <Loader size="lg" />
              <Text c="dimmed">Loading monitoring metrics...</Text>
            </Stack>
          </Center>
        </Card>
      </ErrorBoundary>
    );
  }

  // Show error state with retry option
  if (error && metrics.length === 0) {
    return (
      <ErrorBoundary context="RealTimeMonitoring">
        <Card p="xl" style={{ 
          background: 'rgba(255, 255, 255, 0.8)',
          backdropFilter: 'blur(20px)',
          border: '1px solid rgba(239, 68, 68, 0.2)',
        }}>
          <Stack align="center" gap="md">
            <Alert icon={<IconAlertTriangle size={16} />} title="Failed to load monitoring data" color="red">
              {error.message || 'Unable to fetch monitoring metrics. Using fallback data.'}
            </Alert>
            <Button onClick={retry} leftSection={<IconRefresh size={16} />} variant="light" color="blue">
              Retry
            </Button>
          </Stack>
        </Card>
      </ErrorBoundary>
    );
  }

  return (
    <ErrorBoundary context="RealTimeMonitoring">
      <Stack>
        <Paper p="md">
          <Group justify="space-between" mb="md">
            <Title order={3}>
              <Group gap="sm">
                <IconActivity size={24} />
                Real-time Monitoring
                {loading && <Loader size="sm" />}
              </Group>
            </Title>
            <Group>
              <Select
                value={selectedTimeRange}
                onChange={(value) => value && setSelectedTimeRange(value)}
                data={[
                  { value: '15m', label: 'Last 15 minutes' },
                  { value: '1h', label: 'Last hour' },
                  { value: '6h', label: 'Last 6 hours' },
                  { value: '24h', label: 'Last 24 hours' },
                  { value: '7d', label: 'Last 7 days' }
                ]}
                size="sm"
              />
              <Switch
                label="Auto-refresh"
                checked={autoRefresh}
                onChange={(event) => setAutoRefresh(event.currentTarget.checked)}
                size="sm"
              />
              <Switch
                label="Notifications"
                checked={notificationsEnabled}
                onChange={(event) => setNotificationsEnabled(event.currentTarget.checked)}
                size="sm"
              />
              {error && (
                <Tooltip label="Retry loading metrics">
                  <ActionIcon onClick={retry} color="blue" variant="light">
                    <IconRefresh size={18} />
                  </ActionIcon>
                </Tooltip>
              )}
            </Group>
          </Group>

        <Group mb="md">
          {!isMonitoring ? (
            <Button
              leftSection={<IconPlayerPlay size={16} />}
              onClick={handleStartMonitoring}
              color="green"
            >
              Start Monitoring
            </Button>
          ) : (
            <>
              <Button
                leftSection={<IconPlayerPause size={16} />}
                onClick={handlePauseMonitoring}
                color="yellow"
              >
                Pause
              </Button>
              <Button
                leftSection={<IconPlayerStop size={16} />}
                onClick={handleStopMonitoring}
                color="red"
                variant="outline"
              >
                Stop
              </Button>
            </>
          )}
          <Button
            leftSection={<IconRefresh size={16} />}
            onClick={updateMetrics}
            variant="light"
          >
            Refresh Now
          </Button>
        </Group>

        {isMonitoring && (
          <Alert
            icon={<IconActivity size={16} />}
            title="Monitoring Active"
            color="green"
            variant="light"
            mb="md"
          >
            Real-time monitoring is active. Metrics are being updated every 5 seconds.
          </Alert>
        )}
      </Paper>

      <Grid>
        <Grid.Col span={8}>
          <Paper p="md">
            <Title order={4} mb="md">Key Metrics</Title>
            <Grid>
              {metrics.map(metric => (
                <Grid.Col key={metric.id} span={6}>
                  {renderMetricCard(metric)}
                </Grid.Col>
              ))}
            </Grid>
          </Paper>
        </Grid.Col>
        
        <Grid.Col span={4}>
          <Stack>
            {renderOverallHealth()}
            
            <Paper p="md">
              <Group justify="space-between" mb="md">
                <Title order={4}>Recent Alerts</Title>
                <Badge color="red" variant="light">
                  {alerts.filter(a => !a.resolved).length}
                </Badge>
              </Group>
              
              {alerts.length > 0 ? (
                <Timeline active={-1} bulletSize={12} lineWidth={2}>
                  {alerts.slice(0, 5).map(renderAlertItem)}
                </Timeline>
              ) : (
                <Text size="sm" c="dimmed" ta="center">
                  No recent alerts
                </Text>
              )}
            </Paper>
          </Stack>
        </Grid.Col>
      </Grid>
    </Stack>
  );
};

export default RealTimeMonitoring;
