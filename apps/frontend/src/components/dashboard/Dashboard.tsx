import { useState, useEffect } from "react"
import { Flex, Grid, Stack, Text, Paper, Group, Title, Button, ActionIcon } from "@mantine/core"
import { DatePickerInput } from "@mantine/dates"
import { IconCalendar, IconPlus, IconDownload, IconBrain, IconShield, IconUsers, IconChartBar } from "@tabler/icons-react"
import DeviceBreakdownChart from "../charts/DeviceBreakdownChart"
import ReportSnapshot from "../charts/ReportSnapshotChart"
import ReturningUserChart from "../charts/ReturningUserChart"
import StatsSection from "../charts/StatsSection"
import UserChart from "../charts/UserChart"
import ModernBiasDetectionChart from "../charts/ModernBiasDetectionChart"
import ComprehensiveEvaluationChart from "../charts/ComprehensiveEvaluationChart"
import MultimodalBiasDetectionChart from "../charts/MultimodalBiasDetectionChart"
import AdvancedBiasVisualization from "../charts/AdvancedBiasVisualization"
import RealTimeMonitoring from "./RealTimeMonitoring"
import BiasTestingSimulator from "../simulation/BiasTestingSimulator"
import dateStyleClasses from "../../styles/date.module.css"
import { useApi } from "../../hooks/useApi"
import { mockDashboardStats } from "../../lib/mockData"
import { DashboardSkeleton } from "../LoadingSkeleton"
import ErrorBoundary from "../ErrorBoundary"

interface DashboardStats {
  total_users: number
  total_analyses: number
  total_audit_logs: number
  active_users: number
  high_risk_analyses: number
  recent_activity: number
}

export default function Dashboard() {
  const [value, setValue] = useState<[Date | null, Date | null]>([null, null])
  const { data: stats, loading, error, retry } = useApi<DashboardStats>(
    "/api/v1/database/dashboard-stats",
    {
      fallbackData: mockDashboardStats,
      enableRetry: true,
      cacheKey: 'dashboard-stats'
    }
  )

  // Use real data or fallback to mock data
  const dashboardStats = stats || mockDashboardStats

  // Show loading skeleton while data is loading
  if (loading && !stats) {
    return <DashboardSkeleton />;
  }

  // Show error state with retry option
  if (error && !stats) {
    return (
      <Card
        style={{
          background: 'rgba(255, 255, 255, 0.8)',
          backdropFilter: 'blur(20px)',
          border: '1px solid rgba(239, 68, 68, 0.2)',
          borderRadius: '16px',
          boxShadow: '0 8px 32px rgba(239, 68, 68, 0.1)',
        }}
        p="xl"
      >
        <Stack gap="md" align="center">
          <Text c="red" fw={600}>Failed to load dashboard data</Text>
          <Text c="dimmed" size="sm">{error.message}</Text>
          <Button onClick={retry} variant="light" color="blue">
            Retry
          </Button>
        </Stack>
      </Card>
    );
  }

  return (
    <ErrorBoundary context="Dashboard">
      <Flex w="100%" direction="column" align="start" gap="xl">
        {/* Header Section */}
        <Paper
          p="xl"
          style={{
            background: 'rgba(255, 255, 255, 0.95)',
            backdropFilter: 'blur(20px)',
            border: '1px solid rgba(255, 255, 255, 0.1)',
            boxShadow: '0 4px 20px rgba(0, 0, 0, 0.1)',
          }}
        >
          <Group justify="space-between" align="center" mb="md">
          <Stack gap="xs">
            <Title order={1} fw={700} style={{
              background: 'linear-gradient(45deg, #3b82f6, #8b5cf6)',
              WebkitBackgroundClip: 'text',
              WebkitTextFillColor: 'transparent',
            }}>
              Fairmind - Responsible AI
            </Title>
            <Text c="gray.6" size="lg" fw={500}>
              Comprehensive AI governance and responsible AI management platform
            </Text>
          </Stack>
          <Group>
            <Button
              variant="gradient"
              gradient={{ from: 'blue', to: 'cyan', deg: 90 }}
              leftSection={<IconPlus size={18} />}
              radius="md"
            >
              New Assessment
            </Button>
            <ActionIcon
              variant="default"
              size="lg"
              radius="md"
              aria-label="Export Data"
            >
              <IconDownload size={20} />
            </ActionIcon>
          </Group>
          </Group>
        </Paper>

        {/* Date Picker */}
        <Flex w="100%" align="center" justify="space-between">
          <Text fz={{ base: 18, md: 22, lg: 22 }} fw={600}>
            AI Governance Analytics
          </Text>
          <DatePickerInput
            type="range"
            size="xs"
            leftSection={<IconCalendar size={20} />}
            placeholder="Pick a date"
            value={value}
            classNames={{
              input: dateStyleClasses.date_input,
              placeholder: dateStyleClasses.date_input_placeholder,
            }}
            onChange={setValue}
          />
        </Flex>

        {/* Key Metrics Cards */}
        <Grid columns={12} w="100%">
        <Grid.Col span={{ base: 12, sm: 6, md: 3 }}>
          <Paper p="md" style={{ background: 'rgba(255, 255, 255, 0.8)', backdropFilter: 'blur(10px)' }}>
            <Group>
              <ActionIcon size="lg" variant="light" color="blue">
                <IconBrain size={20} />
              </ActionIcon>
              <div>
                <Text size="xs" c="dimmed">AI Models</Text>
                <Text fw={700} size="lg">{dashboardStats.total_users}</Text>
              </div>
            </Group>
          </Paper>
        </Grid.Col>
        <Grid.Col span={{ base: 12, sm: 6, md: 3 }}>
          <Paper p="md" style={{ background: 'rgba(255, 255, 255, 0.8)', backdropFilter: 'blur(10px)' }}>
            <Group>
              <ActionIcon size="lg" variant="light" color="green">
                <IconShield size={20} />
              </ActionIcon>
              <div>
                <Text size="xs" c="dimmed">Compliance Score</Text>
                <Text fw={700} size="lg">{dashboardStats.recent_activity}%</Text>
              </div>
            </Group>
          </Paper>
        </Grid.Col>
        <Grid.Col span={{ base: 12, sm: 6, md: 3 }}>
          <Paper p="md" style={{ background: 'rgba(255, 255, 255, 0.8)', backdropFilter: 'blur(10px)' }}>
            <Group>
              <ActionIcon size="lg" variant="light" color="orange">
                <IconUsers size={20} />
              </ActionIcon>
              <div>
                <Text size="xs" c="dimmed">Active Users</Text>
                <Text fw={700} size="lg">{dashboardStats.active_users}</Text>
              </div>
            </Group>
          </Paper>
        </Grid.Col>
        <Grid.Col span={{ base: 12, sm: 6, md: 3 }}>
          <Paper p="md" style={{ background: 'rgba(255, 255, 255, 0.8)', backdropFilter: 'blur(10px)' }}>
            <Group>
              <ActionIcon size="lg" variant="light" color="purple">
                <IconChartBar size={20} />
              </ActionIcon>
              <div>
                <Text size="xs" c="dimmed">Assessments</Text>
                <Text fw={700} size="lg">{dashboardStats.total_analyses}</Text>
              </div>
            </Group>
          </Paper>
          </Grid.Col>
        </Grid>

        {/* Modern Bias Detection Section */}
        <Stack w="100%" gap="md">
          <Text fz={{ base: 18, md: 22, lg: 22 }} fw={600}>
            Modern Bias Detection & Explainability
          </Text>
          <Grid columns={12} w="100%">
            <Grid.Col span={{ base: 12, md: 6 }}>
              <ModernBiasDetectionChart />
            </Grid.Col>
            <Grid.Col span={{ base: 12, md: 6 }}>
              <ComprehensiveEvaluationChart />
            </Grid.Col>
          </Grid>
        </Stack>

        {/* Multimodal Bias Detection Section */}
        <Stack w="100%" gap="md">
          <Text fz={{ base: 18, md: 22, lg: 22 }} fw={600}>
            Multimodal Bias Detection
          </Text>
          <Grid columns={12} w="100%">
            <Grid.Col span={{ base: 12 }}>
              <MultimodalBiasDetectionChart />
            </Grid.Col>
          </Grid>
        </Stack>

        {/* Advanced Bias Visualization Section */}
        <Stack w="100%" gap="md">
          <Text fz={{ base: 18, md: 22, lg: 22 }} fw={600}>
            Advanced Bias Visualization
          </Text>
          <Grid columns={12} w="100%">
            <Grid.Col span={{ base: 12 }}>
              <AdvancedBiasVisualization />
            </Grid.Col>
          </Grid>
        </Stack>

        {/* Real-time Monitoring Section */}
        <Stack w="100%" gap="md">
          <Text fz={{ base: 18, md: 22, lg: 22 }} fw={600}>
            Real-time Monitoring
          </Text>
          <Grid columns={12} w="100%">
            <Grid.Col span={{ base: 12 }}>
              <RealTimeMonitoring />
            </Grid.Col>
          </Grid>
        </Stack>

        {/* Bias Testing Simulator Section */}
        <Stack w="100%" gap="md">
          <Text fz={{ base: 18, md: 22, lg: 22 }} fw={600}>
            Interactive Bias Testing
          </Text>
          <Grid columns={12} w="100%">
            <Grid.Col span={{ base: 12 }}>
              <BiasTestingSimulator />
            </Grid.Col>
          </Grid>
        </Stack>

        {/* Charts Section */}
        <Stack w="100%" align="stretch" justify="center" gap="md">
          <Text fz={{ base: 18, md: 22, lg: 22 }} fw={600}>
            AI Governance Analytics
          </Text>
          <Grid columns={10} w="100%">
          <Grid.Col h={400} span={{ base: 10, md: 7, lg: 7 }}>
            <ReportSnapshot />
          </Grid.Col>
          <Grid.Col h={400} span={{ base: 10, md: 3, lg: 3 }}>
            <UserChart />
          </Grid.Col>

          <Grid.Col h={350} span={{ base: 10, md: 5, lg: 4 }}>
            <StatsSection />
          </Grid.Col>
          <Grid.Col h={350} span={{ base: 10, md: 5, lg: 3 }}>
            <ReturningUserChart />
          </Grid.Col>

          <Grid.Col h={350} span={{ base: 10, md: 5, lg: 3 }}>
            <DeviceBreakdownChart />
            </Grid.Col>
          </Grid>
        </Stack>
      </Flex>
    </ErrorBoundary>
  )
}