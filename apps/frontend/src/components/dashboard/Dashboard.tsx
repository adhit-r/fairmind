import { Grid, Stack, Text, Paper, Group, Title, Button, Card, Alert, rem } from "@mantine/core"
import { IconPlus, IconDownload, IconBrain, IconShield, IconUsers, IconChartBar, IconAlertTriangle, IconRefresh } from "@tabler/icons-react"
import ReportSnapshot from "../charts/ReportSnapshotChart"
import UserChart from "../charts/UserChart"
import ModernBiasDetectionChart from "../charts/ModernBiasDetectionChart"
import ComprehensiveEvaluationChart from "../charts/ComprehensiveEvaluationChart"
import RealTimeMonitoring from "./RealTimeMonitoring"
import { useApi } from "../../hooks/useApi"
import { DashboardSkeleton } from "../LoadingSkeleton"
import ErrorBoundary from "../ErrorBoundary"
import { useGlassmorphicTheme } from "../../providers/glassmorphic-theme-provider"

interface DashboardStats {
  total_users: number
  total_analyses: number
  total_audit_logs: number
  active_users: number
  high_risk_analyses: number
  recent_activity: number
}

export default function Dashboard() {
  const { data: stats, loading, error, retry } = useApi<DashboardStats>(
    "/api/v1/database/dashboard-stats",
    {
      enableRetry: true,
      maxRetries: 5,
      retryDelay: 2000,
      timeout: 30000, // 30 seconds timeout for dashboard stats
      cacheKey: 'dashboard-stats',
      refreshInterval: 60000 // Refresh every minute
    }
  )

  // Use real API data - no fallback to mock data
  const dashboardStats: DashboardStats = stats || {
    total_users: 0,
    total_analyses: 0,
    total_audit_logs: 0,
    active_users: 0,
    high_risk_analyses: 0,
    recent_activity: 0,
  }

  // Show loading skeleton while data is loading
  if (loading && !stats) {
    return <DashboardSkeleton />;
  }

  // Show error state with retry option
  const { colorScheme } = useGlassmorphicTheme();

  // Pure neobrutal styles - thicker borders, zero radius
  const brutalistCardStyle = {
    background: colorScheme === 'dark' ? 'var(--color-black)' : 'var(--color-white)',
    border: '4px solid var(--color-black)',
    borderRadius: '0',
    boxShadow: 'var(--shadow-brutal)',
    transition: 'all var(--transition-duration-fast) ease',
  };

  const brutalistCardHoverStyle = {
    transform: 'translate(-4px, -4px)',
    boxShadow: 'var(--shadow-brutal-lg)',
  };

  if (error && !stats) {
    return (
      <Stack 
        gap="xl" 
        style={{ 
          background: colorScheme === 'dark' ? 'var(--color-gray-900)' : 'var(--color-gray-100)',
          minHeight: 'calc(100vh - 72px)',
          width: '100%',
          maxWidth: '100%',
          padding: rem(24),
          margin: 0,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          boxSizing: 'border-box',
        }}
      >
        <Card
          style={{
            ...brutalistCardStyle,
            border: '4px solid rgba(239, 68, 68, 0.8)',
            maxWidth: rem(600),
            width: '100%',
          }}
          p="xl"
        >
          <Stack gap="md" align="center">
            <Alert 
              icon={<IconAlertTriangle size={20} />} 
              color="red" 
              title="Failed to load dashboard data"
              style={{
                width: '100%',
                border: '2px solid rgba(239, 68, 68, 0.8)',
                borderRadius: '0',
              }}
            >
              {error?.message || 'Unknown error'}
              <br />
              <Text size="sm" mt="xs" c="dimmed">
                Please check that the backend server is running at {process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}
              </Text>
            </Alert>
            <Button 
              onClick={retry} 
              variant="filled" 
              color="orange"
              size="lg"
              leftSection={<IconRefresh size={20} />}
              style={{
                border: '4px solid var(--color-black)',
                borderRadius: '0',
                boxShadow: 'var(--shadow-brutal)',
                fontWeight: 'var(--font-weight-black)',
                fontSize: rem(16),
                letterSpacing: 'var(--letter-spacing-wide)',
                textTransform: 'uppercase',
                fontFamily: 'var(--font-family-display)',
                padding: `${rem(16)} ${rem(32)}`,
              }}
              onMouseEnter={(e) => {
                e.currentTarget.style.transform = 'translate(-4px, -4px)';
                e.currentTarget.style.boxShadow = 'var(--shadow-brutal-lg)';
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.transform = 'translate(0, 0)';
                e.currentTarget.style.boxShadow = 'var(--shadow-brutal)';
              }}
            >
              RETRY
            </Button>
          </Stack>
        </Card>
      </Stack>
    );
  }

  return (
    <ErrorBoundary context="Dashboard">
      <Stack 
        gap="xl" 
        style={{ 
          background: colorScheme === 'dark' ? 'var(--color-gray-900)' : 'var(--color-gray-100)',
          minHeight: 'calc(100vh - 72px)',
          width: '100%',
          maxWidth: '100%',
          margin: 0,
          padding: rem(24),
          boxSizing: 'border-box',
        }}
      >
        {/* Hero Section - Massive Neobrutal Typography */}
        <Paper style={{
          background: colorScheme === 'dark' ? 'var(--color-black)' : 'var(--color-white)',
          border: '6px solid var(--color-black)',
          boxShadow: '8px 8px 0px 0px var(--color-black)',
          padding: rem(48),
          borderRadius: '0',
        }}>
          <Stack gap="lg">
            <Title order={1} style={{
              fontSize: rem(64),
              fontWeight: 900,
              lineHeight: 1,
              letterSpacing: '-0.03em',
              textTransform: 'uppercase',
              fontFamily: 'var(--font-family-display)',
              color: 'var(--color-black)',
              margin: 0,
            }}>
              FAIRMIND
            </Title>
            <Text style={{
              fontSize: rem(18),
              fontWeight: 700,
              lineHeight: 1.3,
              letterSpacing: '0.08em',
              textTransform: 'uppercase',
              fontFamily: 'var(--font-family-display)',
              color: 'var(--color-gray-700)',
            }}>
              RESPONSIBLE AI GOVERNANCE PLATFORM
            </Text>
            <Group gap="md" mt="md">
            <Button
                size="lg"
                style={{
                  background: 'var(--color-orange)',
                  border: '6px solid var(--color-black)',
                  boxShadow: '8px 8px 0px 0px var(--color-black)',
                  padding: `${rem(20)} ${rem(40)}`,
                  fontSize: rem(16),
                  fontWeight: 900,
                  textTransform: 'uppercase',
                  letterSpacing: '0.15em',
                  color: 'var(--color-white)',
                  fontFamily: 'var(--font-family-display)',
                  borderRadius: 0,
                }}
                leftSection={<IconPlus size={24} />}
                onMouseEnter={(e) => {
                  e.currentTarget.style.transform = 'translate(-6px, -6px)';
                  e.currentTarget.style.boxShadow = '14px 14px 0px 0px var(--color-black)';
                }}
                onMouseLeave={(e) => {
                  e.currentTarget.style.transform = 'translate(0, 0)';
                  e.currentTarget.style.boxShadow = '8px 8px 0px 0px var(--color-black)';
                }}
              >
                NEW ASSESSMENT
            </Button>
              <Button
              size="lg"
                variant="filled"
                color="dark"
                style={{
                  background: 'var(--color-black)',
                  border: '6px solid var(--color-black)',
                  boxShadow: '8px 8px 0px 0px var(--color-black)',
                  padding: `${rem(20)} ${rem(40)}`,
                  fontSize: rem(16),
                  fontWeight: 900,
                  textTransform: 'uppercase',
                  letterSpacing: '0.15em',
                  color: 'var(--color-white)',
                  fontFamily: 'var(--font-family-display)',
                  borderRadius: 0,
                }}
                leftSection={<IconDownload size={24} />}
                onMouseEnter={(e) => {
                  e.currentTarget.style.transform = 'translate(-6px, -6px)';
                  e.currentTarget.style.boxShadow = '14px 14px 0px 0px var(--color-black)';
                }}
                onMouseLeave={(e) => {
                  e.currentTarget.style.transform = 'translate(0, 0)';
                  e.currentTarget.style.boxShadow = '8px 8px 0px 0px var(--color-black)';
                }}
              >
                EXPORT
              </Button>
          </Group>
          </Stack>
        </Paper>

        {/* Stats Section - Neobrutal Grid */}
        <Grid columns={12} gutter="xl">
        <Grid.Col span={{ base: 12, sm: 6, md: 3 }}>
            <Paper style={{
              background: colorScheme === 'dark' ? 'var(--color-black)' : 'var(--color-white)',
              border: '4px solid var(--color-black)',
              boxShadow: '6px 6px 0px 0px var(--color-black)',
              padding: rem(24),
              height: '100%',
              borderRadius: 0,
              boxSizing: 'border-box',
            }}>
              <Group gap="md" align="flex-start">
                <div style={{
                  width: rem(64),
                  height: rem(64),
                  background: 'var(--color-orange)',
                  border: '4px solid var(--color-black)',
                  boxShadow: '4px 4px 0px 0px var(--color-black)',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  flexShrink: 0,
                  borderRadius: 0,
                }}>
                  <IconBrain size={32} color="white" />
                </div>
                <Stack gap="xs" style={{ flex: 1 }}>
                  <Text style={{
                    fontSize: rem(48),
                    fontWeight: 900,
                    lineHeight: 1,
                    color: 'var(--color-black)',
                    fontFamily: 'var(--font-family-display)',
                  }}>
                    {dashboardStats.total_users}
                  </Text>
                  <Text style={{
                    fontSize: rem(12),
                    fontWeight: 700,
                    textTransform: 'uppercase',
                    letterSpacing: '0.15em',
                    color: 'var(--color-gray-700)',
                    fontFamily: 'var(--font-family-display)',
                  }}>
                    AI MODELS
                  </Text>
                </Stack>
              </Group>
          </Paper>
        </Grid.Col>
          
          <Grid.Col span={{ base: 12, sm: 6, md: 3 }}>
            <Paper style={{
              background: colorScheme === 'dark' ? 'var(--color-black)' : 'var(--color-white)',
              border: '4px solid var(--color-black)',
              boxShadow: '6px 6px 0px 0px var(--color-black)',
              padding: rem(24),
              height: '100%',
              borderRadius: 0,
              boxSizing: 'border-box',
            }}>
              <Group gap="md" align="flex-start">
                <div style={{
                  width: rem(64),
                  height: rem(64),
                  background: 'var(--color-orange)',
                  border: '4px solid var(--color-black)',
                  boxShadow: '4px 4px 0px 0px var(--color-black)',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  flexShrink: 0,
                  borderRadius: 0,
                }}>
                  <IconShield size={32} color="white" />
                </div>
                <Stack gap="xs" style={{ flex: 1 }}>
                  <Text style={{
                    fontSize: rem(48),
                    fontWeight: 900,
                    lineHeight: 1,
                    color: 'var(--color-black)',
                    fontFamily: 'var(--font-family-display)',
                  }}>
                    {dashboardStats.total_analyses > 0 
                      ? Math.round((dashboardStats.total_analyses - dashboardStats.high_risk_analyses) / dashboardStats.total_analyses * 100)
                      : 0}%
                  </Text>
                  <Text style={{
                    fontSize: rem(12),
                    fontWeight: 700,
                    textTransform: 'uppercase',
                    letterSpacing: '0.15em',
                    color: 'var(--color-gray-700)',
                    fontFamily: 'var(--font-family-display)',
                  }}>
                    COMPLIANCE
                  </Text>
                </Stack>
              </Group>
            </Paper>
          </Grid.Col>
          
          <Grid.Col span={{ base: 12, sm: 6, md: 3 }}>
            <Paper style={{
              background: colorScheme === 'dark' ? 'var(--color-black)' : 'var(--color-white)',
              border: '4px solid var(--color-black)',
              boxShadow: '6px 6px 0px 0px var(--color-black)',
              padding: rem(24),
              height: '100%',
              borderRadius: 0,
              boxSizing: 'border-box',
            }}>
              <Group gap="md" align="flex-start">
                <div style={{
                  width: rem(64),
                  height: rem(64),
                  background: 'var(--color-orange)',
                  border: '4px solid var(--color-black)',
                  boxShadow: '4px 4px 0px 0px var(--color-black)',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  flexShrink: 0,
                  borderRadius: 0,
                }}>
                  <IconUsers size={32} color="white" />
                </div>
                <Stack gap="xs" style={{ flex: 1 }}>
                  <Text style={{
                    fontSize: rem(48),
                    fontWeight: 900,
                    lineHeight: 1,
                    color: 'var(--color-black)',
                    fontFamily: 'var(--font-family-display)',
                  }}>
                    {dashboardStats.active_users}
                  </Text>
                  <Text style={{
                    fontSize: rem(12),
                    fontWeight: 700,
                    textTransform: 'uppercase',
                    letterSpacing: '0.15em',
                    color: 'var(--color-gray-700)',
                    fontFamily: 'var(--font-family-display)',
                  }}>
                    ACTIVE USERS
                  </Text>
                </Stack>
              </Group>
            </Paper>
          </Grid.Col>
          
          <Grid.Col span={{ base: 12, sm: 6, md: 3 }}>
            <Paper style={{
              background: colorScheme === 'dark' ? 'var(--color-black)' : 'var(--color-white)',
              border: '4px solid var(--color-black)',
              boxShadow: '6px 6px 0px 0px var(--color-black)',
              padding: rem(24),
              height: '100%',
              borderRadius: 0,
              boxSizing: 'border-box',
            }}>
              <Group gap="md" align="flex-start">
                <div style={{
                  width: rem(64),
                  height: rem(64),
                  background: 'var(--color-orange)',
                  border: '4px solid var(--color-black)',
                  boxShadow: '4px 4px 0px 0px var(--color-black)',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  flexShrink: 0,
                  borderRadius: 0,
                }}>
                  <IconChartBar size={32} color="white" />
                </div>
                <Stack gap="xs" style={{ flex: 1 }}>
                  <Text style={{
                    fontSize: rem(48),
                    fontWeight: 900,
                    lineHeight: 1,
                    color: 'var(--color-black)',
                    fontFamily: 'var(--font-family-display)',
                  }}>
                    {dashboardStats.total_analyses}
                  </Text>
                  <Text style={{
                    fontSize: rem(12),
                    fontWeight: 700,
                    textTransform: 'uppercase',
                    letterSpacing: '0.15em',
                    color: 'var(--color-gray-700)',
                    fontFamily: 'var(--font-family-display)',
                  }}>
                    ASSESSMENTS
                  </Text>
                </Stack>
              </Group>
          </Paper>
          </Grid.Col>
        </Grid>

        {/* Charts Section - Neobrutal Blocks */}
        <Paper style={{
          background: colorScheme === 'dark' ? 'var(--color-black)' : 'var(--color-white)',
          border: '4px solid var(--color-black)',
          boxShadow: '6px 6px 0px 0px var(--color-black)',
          padding: rem(32),
          borderRadius: 0,
          boxSizing: 'border-box',
        }}>
          <Title order={2} style={{
            fontSize: rem(28),
            fontWeight: 900,
            lineHeight: 1.1,
            letterSpacing: '-0.02em',
            textTransform: 'uppercase',
            fontFamily: 'var(--font-family-display)',
            color: 'var(--color-black)',
            marginBottom: rem(24),
          }}>
            BIAS DETECTION
          </Title>
          <Grid columns={12} gutter="xl">
            <Grid.Col span={{ base: 12, md: 6 }}>
              <ModernBiasDetectionChart />
            </Grid.Col>
            <Grid.Col span={{ base: 12, md: 6 }}>
              <ComprehensiveEvaluationChart />
            </Grid.Col>
          </Grid>
        </Paper>
        
        <Paper style={{
          background: colorScheme === 'dark' ? 'var(--color-black)' : 'var(--color-white)',
          border: '4px solid var(--color-black)',
          boxShadow: '6px 6px 0px 0px var(--color-black)',
          padding: rem(32),
          borderRadius: 0,
          boxSizing: 'border-box',
        }}>
          <Title order={2} style={{
            fontSize: rem(28),
            fontWeight: 900,
            lineHeight: 1.1,
            letterSpacing: '-0.02em',
            textTransform: 'uppercase',
            fontFamily: 'var(--font-family-display)',
            color: 'var(--color-black)',
            marginBottom: rem(24),
          }}>
            MONITORING
          </Title>
          <RealTimeMonitoring />
        </Paper>
        
        <Paper style={{
          background: colorScheme === 'dark' ? 'var(--color-black)' : 'var(--color-white)',
          border: '4px solid var(--color-black)',
          boxShadow: '6px 6px 0px 0px var(--color-black)',
          padding: rem(32),
          borderRadius: 0,
          boxSizing: 'border-box',
        }}>
          <Title order={2} style={{
            fontSize: rem(28),
            fontWeight: 900,
            lineHeight: 1.1,
            letterSpacing: '-0.02em',
            textTransform: 'uppercase',
            fontFamily: 'var(--font-family-display)',
            color: 'var(--color-black)',
            marginBottom: rem(24),
          }}>
            ANALYTICS
          </Title>
          <Grid columns={12} gutter="xl">
            <Grid.Col span={{ base: 12, md: 8 }}>
              <ReportSnapshot />
            </Grid.Col>
            <Grid.Col span={{ base: 12, md: 4 }}>
            <UserChart />
            </Grid.Col>
          </Grid>
        </Paper>
        </Stack>
    </ErrorBoundary>
  )
}