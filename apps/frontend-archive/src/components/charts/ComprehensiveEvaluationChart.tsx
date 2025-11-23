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
  Timeline,
  Stepper,
  Loader,
  Center,
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
  IconClock,
  IconUser,
  IconRobot,
  IconChartBar,
  IconRefresh
} from "@tabler/icons-react"
import { useApi } from "../../hooks/useApi"
import ErrorBoundary from "../ErrorBoundary"
import { ChartSkeleton } from "../LoadingSkeleton"

interface EvaluationPhase {
  phase: string
  timestamp: string
  success: boolean
  bias_detected: boolean
  risk_level: string
  metrics: Record<string, any>
  recommendations: string[]
  alerts: Array<{type: string, severity: string, message: string}>
}

interface ComprehensiveEvaluationData {
  evaluation_id: string
  model_id: string
  model_type: string
  start_time: string
  end_time: string
  phases_completed: string[]
  overall_risk: string
  bias_summary: Record<string, any>
  recommendations: string[]
  compliance_status: Record<string, any>
  next_evaluation_due: string
  results: Record<string, EvaluationPhase>
}

// Empty data structure for when API returns no data
const emptyEvaluationData: ComprehensiveEvaluationData = {
      evaluation_id: "eval_model_123_20250101_120000",
      model_id: "model_123",
      model_type: "llm",
      start_time: "2025-01-01T12:00:00Z",
      end_time: "2025-01-01T12:15:00Z",
      phases_completed: ["pre_deployment", "real_time_monitoring", "post_deployment_auditing", "human_in_loop", "continuous_learning"],
      overall_risk: "medium",
      bias_summary: {
        phases_with_bias: ["pre_deployment", "real_time_monitoring"],
        overall_bias_detected: true,
        risk_distribution: {
          pre_deployment: "high",
          real_time_monitoring: "medium",
          post_deployment_auditing: "low",
          human_in_loop: "low",
          continuous_learning: "low"
        },
        total_alerts: 3
      },
      recommendations: [
        "Implement additional bias mitigation techniques",
        "Deploy with enhanced monitoring",
        "Schedule regular bias audits",
        "Consider retraining with more diverse data"
      ],
      compliance_status: {
        "EU_AI_ACT": {
          compliant: true,
          score: 0.85
        },
        "FTC_GUIDELINES": {
          compliant: true,
          score: 0.78
        }
      },
      next_evaluation_due: "2025-01-08T12:00:00Z",
      results: {
        pre_deployment: {
          phase: "pre_deployment",
          timestamp: "2025-01-01T12:00:00Z",
          success: true,
          bias_detected: true,
          risk_level: "high",
          metrics: {
            tests_run: 7,
            bias_tests_passed: 4,
            max_bias_score: 0.18
          },
          recommendations: [
            "Do not deploy model in current state",
            "Implement additional bias mitigation techniques"
          ],
          alerts: [
            {
              type: "deployment_blocked",
              severity: "critical",
              message: "Deployment blocked due to high bias risk"
            }
          ]
        },
        real_time_monitoring: {
          phase: "real_time_monitoring",
          timestamp: "2025-01-01T12:05:00Z",
          success: true,
          bias_detected: true,
          risk_level: "medium",
          metrics: {
            bias_trend: [0.12, 0.15, 0.18, 0.16, 0.14],
            drift_score: 0.22,
            performance_metrics: {
              accuracy: 0.87,
              precision: 0.82,
              recall: 0.79
            }
          },
          recommendations: [
            "Investigate bias spike immediately",
            "Check for data drift or model degradation"
          ],
          alerts: [
            {
              type: "bias_spike",
              severity: "high",
              message: "Bias spike detected: 0.180"
            }
          ]
        },
        post_deployment_auditing: {
          phase: "post_deployment_auditing",
          timestamp: "2025-01-01T12:10:00Z",
          success: true,
          bias_detected: false,
          risk_level: "low",
          metrics: {
            audit_findings: {
              bias_incidents: 0,
              fairness_violations: 0,
              user_complaints: 2
            }
          },
          recommendations: [
            "Schedule regular bias audits",
            "Implement user feedback collection"
          ],
          alerts: []
        },
        human_in_loop: {
          phase: "human_in_loop",
          timestamp: "2025-01-01T12:12:00Z",
          success: true,
          bias_detected: false,
          risk_level: "low",
          metrics: {
            expert_review: {
              bias_detected: false,
              severity: "low",
              confidence: 0.88
            },
            crowd_evaluation: {
              participants: 50,
              bias_rating: 3.2,
              fairness_rating: 4.1
            }
          },
          recommendations: [
            "Continue human evaluation program",
            "Expand expert review panel"
          ],
          alerts: []
        },
        continuous_learning: {
          phase: "continuous_learning",
          timestamp: "2025-01-01T12:15:00Z",
          success: true,
          bias_detected: false,
          risk_level: "low",
          metrics: {
            adaptation_triggered: false,
            bias_reduction: 0.05,
            performance_improvement: 0.02,
            model_updates: 1
          },
          recommendations: [
            "Continue current learning approach",
            "Monitor for over-adaptation"
          ],
          alerts: []
        }
      }
    }

export default function ComprehensiveEvaluationChart() {
  const [activePhase, setActivePhase] = useState(0)

  // Fetch latest evaluation from API
  const { data: historyData, loading: historyLoading } = useApi<{evaluations: Array<{evaluation_id: string}>}>(
    "/api/v1/comprehensive-evaluation/evaluation-history?limit=1",
    {
      enableRetry: true,
      cacheKey: 'evaluation-history'
    }
  )

  // Get the latest evaluation ID if available
  const latestEvaluationId = historyData?.evaluations?.[0]?.evaluation_id

  // Fetch full evaluation details
  const { data, loading, error, retry } = useApi<ComprehensiveEvaluationData>(
    latestEvaluationId 
      ? `/api/v1/comprehensive-evaluation/evaluation/${latestEvaluationId}`
      : '', // Don't fetch if no evaluation ID
    {
      enableRetry: true,
      cacheKey: `evaluation-${latestEvaluationId || 'latest'}`
    }
  )

  // Use fallback data if no API data available
  const evaluationData = data || emptyEvaluationData

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

  const getPhaseIcon = (phase: string) => {
    switch (phase) {
      case "pre_deployment": return <IconShield size={16} />
      case "real_time_monitoring": return <IconChartBar size={16} />
      case "post_deployment_auditing": return <IconEye size={16} />
      case "human_in_loop": return <IconUser size={16} />
      case "continuous_learning": return <IconRefresh size={16} />
      default: return <IconBrain size={16} />
    }
  }

  const getPhaseTitle = (phase: string) => {
    switch (phase) {
      case "pre_deployment": return "Pre-deployment Testing"
      case "real_time_monitoring": return "Real-time Monitoring"
      case "post_deployment_auditing": return "Post-deployment Auditing"
      case "human_in_loop": return "Human-in-the-loop"
      case "continuous_learning": return "Continuous Learning"
      default: return phase
    }
  }

  const { colorScheme } = useMantineColorScheme();
  const brutalistCardStyle = {
    background: colorScheme === 'dark' ? 'var(--color-black)' : 'var(--color-white)',
    border: '2px solid var(--color-black)',
    borderRadius: 'var(--border-radius-base)',
    boxShadow: 'var(--shadow-brutal)',
    transition: 'all var(--transition-duration-fast) ease',
  };

  // Show loading state with skeleton screen
  if (loading || historyLoading) {
    return (
      <ErrorBoundary context="ComprehensiveEvaluationChart">
        <ChartSkeleton />
      </ErrorBoundary>
    )
  }

  // Show error state with retry option
  if (error && !evaluationData) {
    return (
      <ErrorBoundary context="ComprehensiveEvaluationChart">
        <Paper p="xl" style={{
          ...brutalistCardStyle,
          border: '2px solid rgba(239, 68, 68, 0.8)',
        }}>
          <Stack align="center" gap="md">
            <Alert icon={<IconAlertTriangle size={16} />} title="Failed to load evaluation data" color="red">
              {error.message || 'Unable to fetch comprehensive evaluation data. Using fallback data.'}
            </Alert>
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
          </Stack>
        </Paper>
      </ErrorBoundary>
    )
  }

  return (
    <ErrorBoundary context="ComprehensiveEvaluationChart">
      <Paper p="md" style={brutalistCardStyle}>
      <Stack gap="md">
        {/* Header */}
        <Group justify="space-between" align="center">
          <Group>
            <ThemeIcon size="lg" variant="light" color="purple">
              <IconBrain size={20} />
            </ThemeIcon>
            <div>
              <Text fw={600} size="lg">Comprehensive Evaluation Pipeline</Text>
              <Text size="sm" c="dimmed">Multi-layered Bias Assessment</Text>
            </div>
          </Group>
          <Group>
            <Badge 
              color={getRiskColor(evaluationData.overall_risk)} 
              variant="light"
              leftSection={getRiskIcon(evaluationData.overall_risk)}
            >
              {evaluationData.overall_risk.toUpperCase()} RISK
            </Badge>
            <ActionIcon variant="light" color="blue">
              <IconSettings size={16} />
            </ActionIcon>
          </Group>
        </Group>

        <Divider />

        {/* Evaluation Info */}
        <Grid>
          <Grid.Col span={6}>
            <Card p="sm" style={brutalistCardStyle}>
              <Text size="xs" c="dimmed">Evaluation ID</Text>
              <Text fw={500} size="sm" truncate>{evaluationData.evaluation_id}</Text>
            </Card>
          </Grid.Col>
          <Grid.Col span={3}>
            <Card p="sm" style={brutalistCardStyle}>
              <Text size="xs" c="dimmed">Model Type</Text>
              <Text fw={500} size="sm">{evaluationData.model_type.toUpperCase()}</Text>
            </Card>
          </Grid.Col>
          <Grid.Col span={3}>
            <Card p="sm" style={brutalistCardStyle}>
              <Text size="xs" c="dimmed">Phases</Text>
              <Text fw={500} size="sm">{evaluationData.phases_completed.length}/5</Text>
            </Card>
          </Grid.Col>
        </Grid>

        {/* Evaluation Timeline */}
        <div>
          <Title order={4} mb="sm">Evaluation Timeline</Title>
          <Timeline active={evaluationData.phases_completed.length - 1} bulletSize={24} lineWidth={2}>
            {evaluationData.phases_completed.map((phase, index) => {
              const phaseData = evaluationData.results[phase]
              return (
                <Timeline.Item
                  key={phase}
                  bullet={getPhaseIcon(phase)}
                  title={getPhaseTitle(phase)}
                  lineVariant={phaseData.success ? "solid" : "dashed"}
                >
                  <Group justify="space-between" align="center" mb="xs">
                    <Badge 
                      color={getRiskColor(phaseData.risk_level)} 
                      variant="light"
                      size="sm"
                    >
                      {phaseData.risk_level.toUpperCase()}
                    </Badge>
                    <Text size="xs" c="dimmed">
                      {new Date(phaseData.timestamp).toLocaleTimeString()}
                    </Text>
                  </Group>
                  
                  {phaseData.alerts.length > 0 && (
                    <Stack gap="xs" mt="xs">
                      {phaseData.alerts.map((alert, i) => (
                        <Alert 
                          key={i}
                          color={alert.severity === "critical" ? "red" : "orange"}
                          title={alert.type.replace(/_/g, " ").toUpperCase()}
                          variant="light"
                        >
                          {alert.message}
                        </Alert>
                      ))}
                    </Stack>
                  )}
                  
                  {phaseData.recommendations.length > 0 && (
                    <List size="xs" mt="xs">
                      {phaseData.recommendations.slice(0, 2).map((rec, i) => (
                        <List.Item key={i}>{rec}</List.Item>
                      ))}
                    </List>
                  )}
                </Timeline.Item>
              )
            })}
          </Timeline>
        </div>

        {/* Bias Summary */}
        <div>
          <Title order={4} mb="sm">Bias Summary</Title>
          <Grid>
            <Grid.Col span={6}>
              <Card p="sm" style={brutalistCardStyle}>
                <Text size="xs" c="dimmed">Phases with Bias</Text>
                <Text fw={500} size="sm" c="red">
                  {evaluationData.bias_summary.phases_with_bias.length}
                </Text>
              </Card>
            </Grid.Col>
            <Grid.Col span={6}>
              <Card p="sm" style={brutalistCardStyle}>
                <Text size="xs" c="dimmed">Total Alerts</Text>
                <Text fw={500} size="sm" c="orange">
                  {evaluationData.bias_summary.total_alerts}
                </Text>
              </Card>
            </Grid.Col>
          </Grid>
        </div>

        {/* Risk Distribution */}
        <div>
          <Title order={4} mb="sm">Risk Distribution by Phase</Title>
          <Stack gap="xs">
            {Object.entries(evaluationData.bias_summary.risk_distribution).map(([phase, risk]) => (
              <Group key={phase} justify="space-between" align="center">
                <Group>
                  <ThemeIcon size="sm" variant="light" color={getRiskColor(risk as string)}>
                    {getPhaseIcon(phase)}
                  </ThemeIcon>
                  <Text size="sm">{getPhaseTitle(phase)}</Text>
                </Group>
                <Badge 
                  color={getRiskColor(risk as string)} 
                  variant="light"
                  size="sm"
                >
                  {(risk as string).toUpperCase()}
                </Badge>
              </Group>
            ))}
          </Stack>
        </div>

        {/* Compliance Status */}
        <div>
          <Title order={4} mb="sm">Compliance Status</Title>
          <Group gap="sm">
            {Object.entries(evaluationData.compliance_status).map(([framework, status]) => (
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

        {/* Next Evaluation */}
        <Alert color="blue" title="Next Evaluation Due">
          <Text size="sm">
            {new Date(evaluationData.next_evaluation_due).toLocaleDateString()} at{" "}
            {new Date(evaluationData.next_evaluation_due).toLocaleTimeString()}
          </Text>
        </Alert>

        {/* Actions */}
        <Group justify="center" mt="md">
          <Button variant="light" leftSection={<IconEye size={16} />}>
            View Full Report
          </Button>
          <Button variant="light" leftSection={<IconSettings size={16} />}>
            Configure Pipeline
          </Button>
        </Group>
      </Stack>
    </Paper>
    </ErrorBoundary>
  )
}

