'use client'
import { Container, Box, Title, Text, Paper, Grid, Card, Group, ActionIcon } from '@mantine/core'
import { IconChartBar, IconTrendingUp, IconUsers, IconActivity } from '@tabler/icons-react'

export default function AnalyticsPage() {
  return (
    <Container size="xl" p="md">
        <Box>
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
              <Box>
                <Title order={1} fw={700} style={{
                  background: 'linear-gradient(45deg, #3b82f6, #8b5cf6)',
                  WebkitBackgroundClip: 'text',
                  WebkitTextFillColor: 'transparent',
                }}>
                  AI Analytics Dashboard
                </Title>
                <Text c="gray.6" size="lg" fw={500}>
                  Comprehensive analytics for AI model performance
                </Text>
              </Box>
            </Group>
          </Paper>

          {/* Analytics Cards */}
          <Grid mt="xl">
            <Grid.Col span={{ base: 12, md: 6, lg: 3 }}>
              <Card shadow="sm" padding="lg" radius="md" withBorder>
                <Group justify="space-between" mb="xs">
                  <Text fw={500}>Model Usage</Text>
                  <ActionIcon variant="light" color="blue">
                    <IconChartBar size={20} />
                  </ActionIcon>
                </Group>
                <Text size="xl" fw={700}>1,234</Text>
                <Text size="sm" c="dimmed">
                  Total API calls today
                </Text>
              </Card>
            </Grid.Col>

            <Grid.Col span={{ base: 12, md: 6, lg: 3 }}>
              <Card shadow="sm" padding="lg" radius="md" withBorder>
                <Group justify="space-between" mb="xs">
                  <Text fw={500}>Performance</Text>
                  <ActionIcon variant="light" color="green">
                    <IconTrendingUp size={20} />
                  </ActionIcon>
                </Group>
                <Text size="xl" fw={700}>98.5%</Text>
                <Text size="sm" c="dimmed">
                  Uptime this month
                </Text>
              </Card>
            </Grid.Col>

            <Grid.Col span={{ base: 12, md: 6, lg: 3 }}>
              <Card shadow="sm" padding="lg" radius="md" withBorder>
                <Group justify="space-between" mb="xs">
                  <Text fw={500}>Active Users</Text>
                  <ActionIcon variant="light" color="orange">
                    <IconUsers size={20} />
                  </ActionIcon>
                </Group>
                <Text size="xl" fw={700}>456</Text>
                <Text size="sm" c="dimmed">
                  Users this week
                </Text>
              </Card>
            </Grid.Col>

            <Grid.Col span={{ base: 12, md: 6, lg: 3 }}>
              <Card shadow="sm" padding="lg" radius="md" withBorder>
                <Group justify="space-between" mb="xs">
                  <Text fw={500}>Response Time</Text>
                  <ActionIcon variant="light" color="purple">
                    <IconActivity size={20} />
                  </ActionIcon>
                </Group>
                <Text size="xl" fw={700}>1.2s</Text>
                <Text size="sm" c="dimmed">
                  Average response time
                </Text>
              </Card>
            </Grid.Col>
          </Grid>
        </Box>
      </Container>
  )
}



