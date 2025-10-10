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
  Tabs,
  RingProgress,
  Center
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
  IconPhoto,
  IconMicrophone,
  IconVideo,
  IconArrowsMaximize
} from "@tabler/icons-react"

interface MultimodalBiasResult {
  modality: string
  bias_type: string
  bias_score: number
  confidence: number
  is_biased: boolean
  details: Record<string, any>
  recommendations: string[]
  timestamp: string
}

interface MultimodalBiasData {
  timestamp: string
  modalities: string[]
  individual_modality_results: Record<string, MultimodalBiasResult[]>
  cross_modal_results: MultimodalBiasResult[]
  overall_assessment: {
    overall_bias_score: number
    biased_modalities: string[]
    cross_modal_bias_detected: boolean
    risk_level: string
  }
  recommendations: string[]
}

export default function MultimodalBiasDetectionChart() {
  const [data, setData] = useState<MultimodalBiasData | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [activeTab, setActiveTab] = useState<string | null>("overview")

  // Mock data for demonstration
  useEffect(() => {
    const mockData: MultimodalBiasData = {
      timestamp: "2025-01-01T12:00:00Z",
      modalities: ["text", "image", "audio", "video"],
      individual_modality_results: {
        image: [
          {
            modality: "image",
            bias_type: "demographic_representation",
            bias_score: 0.18,
            confidence: 0.85,
            is_biased: true,
            details: {
              demographic_breakdown: {
                gender: { male: 0.6, female: 0.4 },
                race: { white: 0.7, black: 0.15, asian: 0.1, other: 0.05 }
              }
            },
            recommendations: ["Increase diversity in training data", "Implement demographic balancing"],
            timestamp: "2025-01-01T12:00:00Z"
          },
          {
            modality: "image",
            bias_type: "object_detection_bias",
            bias_score: 0.12,
            confidence: 0.82,
            is_biased: true,
            details: {
              object_associations: {
                kitchen: { gender: { female: 0.8, male: 0.2 } },
                office: { gender: { male: 0.7, female: 0.3 } }
              }
            },
            recommendations: ["Balance object-person associations", "Use CLIP-based analysis"],
            timestamp: "2025-01-01T12:00:00Z"
          }
        ],
        audio: [
          {
            modality: "audio",
            bias_type: "voice_characteristics",
            bias_score: 0.15,
            confidence: 0.88,
            is_biased: true,
            details: {
              voice_characteristics: {
                gender: { male: 0.6, female: 0.4 },
                pitch: { low: 0.6, medium: 0.3, high: 0.1 }
              }
            },
            recommendations: ["Balance voice characteristics", "Implement demographic classifier probing"],
            timestamp: "2025-01-01T12:00:00Z"
          }
        ],
        video: [
          {
            modality: "video",
            bias_type: "motion_bias",
            bias_score: 0.20,
            confidence: 0.83,
            is_biased: true,
            details: {
              activity_distribution: {
                professional: { male: 0.7, female: 0.3 },
                domestic: { male: 0.2, female: 0.8 }
              }
            },
            recommendations: ["Balance activities across demographic groups", "Use pose estimation"],
            timestamp: "2025-01-01T12:00:00Z"
          }
        ]
      },
      cross_modal_results: [
        {
          modality: "text",
          bias_type: "cross_modal_stereotypes",
          bias_score: 0.16,
          confidence: 0.77,
          is_biased: true,
          details: {
            cross_modal_analysis: {
              modality_a: "text",
              modality_b: "image",
              interaction_strength: 0.16,
              stereotype_amplification: 0.2
            }
          },
          recommendations: ["Monitor cross-modal bias interactions", "Implement consistency testing"],
          timestamp: "2025-01-01T12:00:00Z"
        }
      ],
      overall_assessment: {
        overall_bias_score: 0.16,
        biased_modalities: ["image", "audio", "video"],
        cross_modal_bias_detected: true,
        risk_level: "medium"
      },
      recommendations: [
        "Implement immediate bias mitigation measures",
        "Focus bias mitigation on: image, audio, video",
        "Implement cross-modal consistency monitoring",
        "Use interaction effect analysis"
      ]
    }

    setTimeout(() => {
      setData(mockData)
      setLoading(false)
    }, 1000)
  }, [])

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

  const getModalityIcon = (modality: string) => {
    switch (modality) {
      case "image": return <IconPhoto size={16} />
      case "audio": return <IconMicrophone size={16} />
      case "video": return <IconVideo size={16} />
      case "text": return <IconBrain size={16} />
      default: return <IconInfoCircle size={16} />
    }
  }

  const getBiasTrendIcon = (score: number) => {
    if (score > 0.15) return <IconTrendingUp size={16} color="red" />
    if (score < 0.05) return <IconTrendingDown size={16} color="green" />
    return <IconMinus size={16} color="orange" />
  }

  if (loading) {
    return (
      <Paper p="md" style={{ background: 'rgba(255, 255, 255, 0.8)', backdropFilter: 'blur(10px)' }}>
        <Text>Loading multimodal bias detection analysis...</Text>
      </Paper>
    )
  }

  if (error) {
    return (
      <Paper p="md" style={{ background: 'rgba(255, 255, 255, 0.8)', backdropFilter: 'blur(10px)' }}>
        <Alert color="red" title="Error">
          {error}
        </Alert>
      </Paper>
    )
  }

  if (!data) return null

  return (
    <Paper p="md" style={{ background: 'rgba(255, 255, 255, 0.8)', backdropFilter: 'blur(10px)' }}>
      <Stack gap="md">
        {/* Header */}
        <Group justify="space-between" align="center">
          <Group>
            <ThemeIcon size="lg" variant="light" color="cyan">
              <IconArrowsMaximize size={20} />
            </ThemeIcon>
            <div>
              <Text fw={600} size="lg">Multimodal Bias Detection</Text>
              <Text size="sm" c="dimmed">Cross-Modal Analysis Framework</Text>
            </div>
          </Group>
          <Group>
            <Badge 
              color={getRiskColor(data.overall_assessment.risk_level)} 
              variant="light"
              leftSection={getRiskIcon(data.overall_assessment.risk_level)}
            >
              {data.overall_assessment.risk_level.toUpperCase()} RISK
            </Badge>
            <ActionIcon variant="light" color="blue">
              <IconSettings size={16} />
            </ActionIcon>
          </Group>
        </Group>

        <Divider />

        {/* Overview Stats */}
        <Grid>
          <Grid.Col span={3}>
            <Card p="sm" style={{ background: 'rgba(255, 255, 255, 0.5)' }}>
              <Text size="xs" c="dimmed">Modalities</Text>
              <Text fw={700} size="lg">{data.modalities.length}</Text>
            </Card>
          </Grid.Col>
          <Grid.Col span={3}>
            <Card p="sm" style={{ background: 'rgba(255, 255, 255, 0.5)' }}>
              <Text size="xs" c="dimmed">Biased Modalities</Text>
              <Text fw={700} size="lg" c="red">{data.overall_assessment.biased_modalities.length}</Text>
            </Card>
          </Grid.Col>
          <Grid.Col span={3}>
            <Card p="sm" style={{ background: 'rgba(255, 255, 255, 0.5)' }}>
              <Text size="xs" c="dimmed">Overall Bias</Text>
              <Text fw={700} size="lg">{(data.overall_assessment.overall_bias_score * 100).toFixed(1)}%</Text>
            </Card>
          </Grid.Col>
          <Grid.Col span={3}>
            <Card p="sm" style={{ background: 'rgba(255, 255, 255, 0.5)' }}>
              <Text size="xs" c="dimmed">Cross-Modal</Text>
              <Text fw={700} size="lg" c={data.overall_assessment.cross_modal_bias_detected ? "red" : "green"}>
                {data.overall_assessment.cross_modal_bias_detected ? "Yes" : "No"}
              </Text>
            </Card>
          </Grid.Col>
        </Grid>

        {/* Tabs for different views */}
        <Tabs value={activeTab} onChange={setActiveTab}>
          <Tabs.List>
            <Tabs.Tab value="overview">Overview</Tabs.Tab>
            <Tabs.Tab value="modalities">Modalities</Tabs.Tab>
            <Tabs.Tab value="cross-modal">Cross-Modal</Tabs.Tab>
            <Tabs.Tab value="recommendations">Recommendations</Tabs.Tab>
          </Tabs.List>

          <Tabs.Panel value="overview" pt="md">
            <Grid>
              <Grid.Col span={6}>
                <Card p="md" style={{ background: 'rgba(255, 255, 255, 0.5)' }}>
                  <Text fw={500} mb="sm">Overall Bias Score</Text>
                  <Center>
                    <RingProgress
                      size={120}
                      thickness={12}
                      sections={[
                        { value: data.overall_assessment.overall_bias_score * 100, color: getRiskColor(data.overall_assessment.risk_level) }
                      ]}
                      label={
                        <Text ta="center" fw={700} size="lg">
                          {(data.overall_assessment.overall_bias_score * 100).toFixed(1)}%
                        </Text>
                      }
                    />
                  </Center>
                </Card>
              </Grid.Col>
              <Grid.Col span={6}>
                <Card p="md" style={{ background: 'rgba(255, 255, 255, 0.5)' }}>
                  <Text fw={500} mb="sm">Modality Risk Distribution</Text>
                  <Stack gap="xs">
                    {data.modalities.map((modality) => {
                      const isBiased = data.overall_assessment.biased_modalities.includes(modality)
                      return (
                        <Group key={modality} justify="space-between">
                          <Group>
                            <ThemeIcon size="sm" variant="light" color={isBiased ? "red" : "green"}>
                              {getModalityIcon(modality)}
                            </ThemeIcon>
                            <Text size="sm" tt="capitalize">{modality}</Text>
                          </Group>
                          <Badge 
                            color={isBiased ? "red" : "green"} 
                            variant="light"
                            size="sm"
                          >
                            {isBiased ? "Biased" : "Clean"}
                          </Badge>
                        </Group>
                      )
                    })}
                  </Stack>
                </Card>
              </Grid.Col>
            </Grid>
          </Tabs.Panel>

          <Tabs.Panel value="modalities" pt="md">
            <Stack gap="md">
              {Object.entries(data.individual_modality_results).map(([modality, results]) => (
                <Card key={modality} p="md" style={{ background: 'rgba(255, 255, 255, 0.5)' }}>
                  <Group mb="sm">
                    <ThemeIcon size="md" variant="light" color="blue">
                      {getModalityIcon(modality)}
                    </ThemeIcon>
                    <Text fw={600} size="lg" tt="capitalize">{modality} Analysis</Text>
                  </Group>
                  
                  <Stack gap="xs">
                    {results.map((result, index) => (
                      <Card key={index} p="sm" style={{ background: 'rgba(255, 255, 255, 0.3)' }}>
                        <Group justify="space-between" align="center">
                          <Group>
                            <ThemeIcon 
                              size="sm" 
                              variant="light" 
                              color={result.is_biased ? "red" : "green"}
                            >
                              {result.is_biased ? <IconX size={12} /> : <IconCheck size={12} />}
                            </ThemeIcon>
                            <div>
                              <Text fw={500} size="sm">{result.bias_type.replace(/_/g, " ")}</Text>
                              <Text size="xs" c="dimmed">{result.modality}</Text>
                            </div>
                          </Group>
                          <Group>
                            {getBiasTrendIcon(result.bias_score)}
                            <Text fw={600} size="sm" c={result.is_biased ? "red" : "green"}>
                              {(result.bias_score * 100).toFixed(1)}%
                            </Text>
                            <Badge size="xs" variant="light" color="blue">
                              {(result.confidence * 100).toFixed(0)}% conf
                            </Badge>
                          </Group>
                        </Group>
                        <Progress 
                          value={result.bias_score * 100} 
                          color={result.is_biased ? "red" : "green"}
                          size="xs"
                          mt="xs"
                        />
                      </Card>
                    ))}
                  </Stack>
                </Card>
              ))}
            </Stack>
          </Tabs.Panel>

          <Tabs.Panel value="cross-modal" pt="md">
            <Stack gap="md">
              {data.cross_modal_results.map((result, index) => (
                <Card key={index} p="md" style={{ background: 'rgba(255, 255, 255, 0.5)' }}>
                  <Group mb="sm">
                    <ThemeIcon size="md" variant="light" color="purple">
                      <IconArrowsMaximize size={16} />
                    </ThemeIcon>
                    <Text fw={600} size="lg">Cross-Modal Interaction</Text>
                  </Group>
                  
                  <Group justify="space-between" align="center" mb="sm">
                    <Group>
                      <ThemeIcon 
                        size="sm" 
                        variant="light" 
                        color={result.is_biased ? "red" : "green"}
                      >
                        {result.is_biased ? <IconX size={12} /> : <IconCheck size={12} />}
                      </ThemeIcon>
                      <Text fw={500} size="sm">{result.bias_type.replace(/_/g, " ")}</Text>
                    </Group>
                    <Group>
                      {getBiasTrendIcon(result.bias_score)}
                      <Text fw={600} size="sm" c={result.is_biased ? "red" : "green"}>
                        {(result.bias_score * 100).toFixed(1)}%
                      </Text>
                      <Badge size="xs" variant="light" color="blue">
                        {(result.confidence * 100).toFixed(0)}% conf
                      </Badge>
                    </Group>
                  </Group>
                  
                  <Progress 
                    value={result.bias_score * 100} 
                    color={result.is_biased ? "red" : "green"}
                    size="sm"
                    mb="sm"
                  />
                  
                  {result.details.cross_modal_analysis && (
                    <Text size="xs" c="dimmed">
                      Interaction between {result.details.cross_modal_analysis.modality_a} and {result.details.cross_modal_analysis.modality_b}
                    </Text>
                  )}
                </Card>
              ))}
            </Stack>
          </Tabs.Panel>

          <Tabs.Panel value="recommendations" pt="md">
            <Card p="md" style={{ background: 'rgba(255, 255, 255, 0.5)' }}>
              <Text fw={600} size="lg" mb="md">Recommendations</Text>
              <List size="sm">
                {data.recommendations.map((recommendation, index) => (
                  <List.Item key={index} icon={<IconInfoCircle size={14} />}>
                    {recommendation}
                  </List.Item>
                ))}
              </List>
            </Card>
          </Tabs.Panel>
        </Tabs>

        {/* Actions */}
        <Group justify="center" mt="md">
          <Button variant="light" leftSection={<IconEye size={16} />}>
            View Details
          </Button>
          <Button variant="light" leftSection={<IconSettings size={16} />}>
            Configure Analysis
          </Button>
        </Group>
      </Stack>
    </Paper>
  )
}
