'use client'

import { useState, useEffect } from "react"
import { 
  Paper, 
  Text, 
  Group, 
  Stack, 
  Badge, 
  Progress, 
  Button, 
  ActionIcon,
  Tooltip,
  Alert,
  List,
  ThemeIcon,
  Grid,
  Card,
  Title,
  Divider,
  Loader,
  useMantineColorScheme
} from "@mantine/core"
import { 
  IconBrain, 
  IconShield, 
  IconAlertTriangle, 
  IconCheck, 
  IconX,
  IconEye,
  IconSettings,
  IconTrendingUp,
  IconTrendingDown,
  IconMinus,
  IconInfoCircle,
  IconRefresh
} from "@tabler/icons-react"
import { useApi } from "../../hooks/useApi"
import { ChartSkeleton } from "../LoadingSkeleton"

interface BiasTestResult {
  test_name: string
  bias_score: number
  is_biased: boolean
  confidence: number
  category: string
}

interface ExplainabilityResult {
  method: string
  confidence: number
  insights: string[]
  visualizations: string[]
}

interface ModernBiasDetectionData {
  overall_risk: string
  bias_tests: BiasTestResult[]
  explainability_analysis: ExplainabilityResult[]
  recommendations: string[]
  compliance_status: Record<string, any>
  evaluation_summary: {
    total_tests_run: number
    biased_tests: number
    bias_rate: number
  }
}

export default function ModernBiasDetectionChart() {
  const { data, loading, error, retry } = useApi<ModernBiasDetectionData>(
    "/api/v1/modern-bias/detection-results",
    {
      enableRetry: true,
      cacheKey: 'modern-bias-detection',
      refreshInterval: 60000 // Refresh every minute
    }
  )

  const getRiskColor = (risk: string) => {
    switch (risk) {
      case "low": return "green"
      case "medium": return "yellow"
      case "high": return "orange"
      case "critical": return "red"
      default: return "gray"
    }
  }

  const getRiskIcon = (risk: string) => {
    switch (risk) {
      case "low": return <IconCheck size={16} />
      case "medium": return <IconAlertTriangle size={16} />
      case "high": return <IconX size={16} />
      case "critical": return <IconX size={16} />
      default: return <IconInfoCircle size={16} />
    }
  }

  const getBiasTrendIcon = (score: number) => {
    if (score > 0.15) return <IconTrendingUp size={16} color="red" />
    if (score < 0.05) return <IconTrendingDown size={16} color="green" />
    return <IconMinus size={16} color="orange" />
  }

  const { colorScheme } = useMantineColorScheme();
  const brutalistCardStyle = {
    background: colorScheme === 'dark' ? 'var(--color-black)' : 'var(--color-white)',
    border: '2px solid var(--color-black)',
    borderRadius: 'var(--border-radius-base)',
    boxShadow: 'var(--shadow-brutal)',
    transition: 'all var(--transition-duration-fast) ease',
  };

  if (loading) {
    return <ChartSkeleton />
  }

  if (error) {
    return (
      <Paper p="md" style={{
        ...brutalistCardStyle,
        border: '2px solid rgba(239, 68, 68, 0.8)',
      }}>
        <Stack align="center" gap="md">
          <Alert icon={<IconAlertTriangle size={16} />} color="red" title="Error">
            {error?.message || 'Unknown error'}
          </Alert>
          {retry && (
            <Button 
              onClick={retry} 
              leftSection={<IconRefresh size={16} />} 
              variant="light" 
              color="blue"
              style={{
                border: '2px solid var(--color-black)',
                boxShadow: 'var(--shadow-brutal)',
              }}
            >
              Retry
            </Button>
          )}
        </Stack>
      </Paper>
    )
  }

  if (!data) {
    return (
      <Paper p="md" style={brutalistCardStyle}>
        <Text>No data available</Text>
      </Paper>
    )
  }

  return (
    <Paper p="md" style={brutalistCardStyle}>
      <Stack gap="md">
        {/* Header */}
        <Group justify="space-between" align="center">
          <Group>
            <ThemeIcon size="lg" variant="light" color="blue">
              <IconBrain size={20} />
            </ThemeIcon>
            <div>
              <Text fw={600} size="lg">Modern Bias Detection</Text>
              <Text size="sm" c="dimmed">2025 Analysis Framework</Text>
            </div>
          </Group>
          <Group>
            <Badge 
              color={getRiskColor(data.overall_risk)} 
              variant="light"
              leftSection={getRiskIcon(data.overall_risk)}
            >
              {data.overall_risk.toUpperCase()} RISK
            </Badge>
            <ActionIcon variant="light" color="blue">
              <IconSettings size={16} />
            </ActionIcon>
          </Group>
        </Group>

        <Divider />

        {/* Summary Stats */}
        <Grid>
          <Grid.Col span={4}>
            <Card p="sm" style={brutalistCardStyle}>
              <Text size="xs" c="dimmed" fw={600}>Tests Run</Text>
              <Text fw={700} size="lg">{data.evaluation_summary.total_tests_run}</Text>
            </Card>
          </Grid.Col>
          <Grid.Col span={4}>
            <Card p="sm" style={brutalistCardStyle}>
              <Text size="xs" c="dimmed" fw={600}>Bias Detected</Text>
              <Text fw={700} size="lg" c="red">{data.evaluation_summary.biased_tests}</Text>
            </Card>
          </Grid.Col>
          <Grid.Col span={4}>
            <Card p="sm" style={brutalistCardStyle}>
              <Text size="xs" c="dimmed" fw={600}>Bias Rate</Text>
              <Text fw={700} size="lg">{(data.evaluation_summary.bias_rate * 100).toFixed(0)}%</Text>
            </Card>
          </Grid.Col>
        </Grid>

        {/* Bias Tests */}
        <div>
          <Title order={4} mb="sm">Bias Test Results</Title>
          <Stack gap="xs">
            {data.bias_tests.map((test, index) => (
              <Card key={index} p="sm" style={brutalistCardStyle}>
                <Group justify="space-between" align="center">
                  <Group>
                    <ThemeIcon 
                      size="sm" 
                      variant="light" 
                      color={test.is_biased ? "red" : "green"}
                    >
                      {test.is_biased ? <IconX size={12} /> : <IconCheck size={12} />}
                    </ThemeIcon>
                    <div>
                      <Text fw={500} size="sm">{test.test_name}</Text>
                      <Text size="xs" c="dimmed">{test.category}</Text>
                    </div>
                  </Group>
                  <Group>
                    {getBiasTrendIcon(test.bias_score)}
                    <Text fw={600} size="sm" c={test.is_biased ? "red" : "green"}>
                      {(test.bias_score * 100).toFixed(1)}%
                    </Text>
                    <Badge size="xs" variant="light" color="blue">
                      {(test.confidence * 100).toFixed(0)}% conf
                    </Badge>
                  </Group>
                </Group>
                <Progress 
                  value={test.bias_score * 100} 
                  color={test.is_biased ? "red" : "green"}
                  size="xs"
                  mt="xs"
                />
              </Card>
            ))}
          </Stack>
        </div>

        {/* Explainability Analysis */}
        <div>
          <Title order={4} mb="sm">Explainability Insights</Title>
          <Stack gap="xs">
            {data.explainability_analysis.map((analysis, index) => (
              <Card key={index} p="sm" style={brutalistCardStyle}>
                <Group justify="space-between" align="flex-start">
                  <div style={{ flex: 1 }}>
                    <Text fw={500} size="sm">{analysis.method}</Text>
                    <List size="xs" mt="xs">
                      {analysis.insights.map((insight, i) => (
                        <List.Item key={i}>{insight}</List.Item>
                      ))}
                    </List>
                  </div>
                  <Badge size="xs" variant="light" color="blue">
                    {(analysis.confidence * 100).toFixed(0)}% conf
                  </Badge>
                </Group>
              </Card>
            ))}
          </Stack>
        </div>

        {/* Compliance Status */}
        <div>
          <Title order={4} mb="sm">Compliance Status</Title>
          <Group gap="sm">
            {Object.entries(data.compliance_status).map(([framework, status]) => (
              <Badge 
                key={framework}
                color={status.compliant ? "green" : "red"}
                variant="light"
                leftSection={status.compliant ? <IconCheck size={12} /> : <IconX size={12} />}
              >
                {framework} ({(status.score * 100).toFixed(0)}%)
              </Badge>
            ))}
          </Group>
        </div>

        {/* Recommendations */}
        <div>
          <Title order={4} mb="sm">Recommendations</Title>
          <List size="sm">
            {data.recommendations.map((recommendation, index) => (
              <List.Item key={index} icon={<IconInfoCircle size={14} />}>
                {recommendation}
              </List.Item>
            ))}
          </List>
        </div>

        {/* Actions */}
        <Group justify="center" mt="md">
          <Button variant="light" leftSection={<IconEye size={16} />}>
            View Details
          </Button>
          <Button variant="light" leftSection={<IconSettings size={16} />}>
            Configure Tests
          </Button>
        </Group>
      </Stack>
    </Paper>
  )
}