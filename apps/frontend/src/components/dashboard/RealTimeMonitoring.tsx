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
  Select
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

interface RealTimeMonitoringProps {
  modelId?: string;
  onAlert?: (alert: Alert) => void;
  onMetricUpdate?: (metric: MonitoringMetric) => void;
}

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

  // Mock initial metrics
  const initialMetrics: MonitoringMetric[] = [
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

  useEffect(() => {
    setMetrics(initialMetrics);
  }, []);

  useEffect(() => {
    if (isMonitoring && autoRefresh) {
      intervalRef.current = setInterval(() => {
        updateMetrics();
      }, 5000); // Update every 5 seconds
    } else if (intervalRef.current) {
      clearInterval(intervalRef.current);
    }

    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
      }
    };
  }, [isMonitoring, autoRefresh]);

  const updateMetrics = () => {
    setMetrics(prevMetrics => 
      prevMetrics.map(metric => {
        // Simulate metric changes
        const change = (Math.random() - 0.5) * 0.1;
        const newValue = Math.max(0, Math.min(1, metric.value + change));
        
        // Determine status based on threshold
        let status: 'healthy' | 'warning' | 'critical' = 'healthy';
        if (newValue > metric.threshold * 1.2) {
          status = 'critical';
        } else if (newValue > metric.threshold) {
          status = 'warning';
        }

        // Determine trend
        const trend: 'up' | 'down' | 'stable' = 
          newValue > metric.value ? 'up' : 
          newValue < metric.value ? 'down' : 'stable';

        const updatedMetric: MonitoringMetric = {
          ...metric,
          value: newValue,
          status,
          trend,
          timestamp: new Date().toISOString()
        };

        // Check for alerts
        if (status === 'warning' || status === 'critical') {
          generateAlert(updatedMetric);
        }

        if (onMetricUpdate) {
          onMetricUpdate(updatedMetric);
        }

        return updatedMetric;
      })
    );
  };

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

  return (
    <Stack>
      <Paper p="md">
        <Group justify="space-between" mb="md">
          <Title order={3}>
            <Group gap="sm">
              <IconActivity size={24} />
              Real-time Monitoring
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
