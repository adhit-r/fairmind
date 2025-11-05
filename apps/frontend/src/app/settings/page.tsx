'use client'

import App from '../../components/layouts/App'
import { Container, Box, Title, Text, Paper, Grid, Card, Group, ActionIcon, Switch, Button } from '@mantine/core'
import { IconSettings, IconBell, IconShield, IconPalette, IconDatabase } from '@tabler/icons-react'

export default function SettingsPage() {
  return (
    <App>
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
                  Settings
                </Title>
                <Text c="gray.6" size="lg" fw={500}>
                  Configure your AI governance platform
                </Text>
              </Box>
            </Group>
          </Paper>

          {/* Settings Cards */}
          <Grid mt="xl">
            <Grid.Col span={{ base: 12, md: 6 }}>
              <Card shadow="sm" padding="lg" radius="md" withBorder>
                <Group justify="space-between" mb="md">
                  <Text fw={500} size="lg">Notifications</Text>
                  <ActionIcon variant="light" color="blue">
                    <IconBell size={20} />
                  </ActionIcon>
                </Group>
                <Box mb="md">
                  <Group justify="space-between" mb="sm">
                    <Text>Email Notifications</Text>
                    <Switch defaultChecked />
                  </Group>
                  <Group justify="space-between" mb="sm">
                    <Text>Push Notifications</Text>
                    <Switch />
                  </Group>
                  <Group justify="space-between">
                    <Text>Weekly Reports</Text>
                    <Switch defaultChecked />
                  </Group>
                </Box>
              </Card>
            </Grid.Col>

            <Grid.Col span={{ base: 12, md: 6 }}>
              <Card shadow="sm" padding="lg" radius="md" withBorder>
                <Group justify="space-between" mb="md">
                  <Text fw={500} size="lg">Security</Text>
                  <ActionIcon variant="light" color="red">
                    <IconShield size={20} />
                  </ActionIcon>
                </Group>
                <Box mb="md">
                  <Group justify="space-between" mb="sm">
                    <Text>Two-Factor Authentication</Text>
                    <Switch defaultChecked />
                  </Group>
                  <Group justify="space-between" mb="sm">
                    <Text>Session Timeout</Text>
                    <Switch defaultChecked />
                  </Group>
                  <Group justify="space-between">
                    <Text>Audit Logging</Text>
                    <Switch defaultChecked />
                  </Group>
                </Box>
              </Card>
            </Grid.Col>

            <Grid.Col span={{ base: 12, md: 6 }}>
              <Card shadow="sm" padding="lg" radius="md" withBorder>
                <Group justify="space-between" mb="md">
                  <Text fw={500} size="lg">Appearance</Text>
                  <ActionIcon variant="light" color="purple">
                    <IconPalette size={20} />
                  </ActionIcon>
                </Group>
                <Box mb="md">
                  <Group justify="space-between" mb="sm">
                    <Text>Dark Mode</Text>
                    <Switch />
                  </Group>
                  <Group justify="space-between" mb="sm">
                    <Text>Compact Layout</Text>
                    <Switch />
                  </Group>
                  <Group justify="space-between">
                    <Text>High Contrast</Text>
                    <Switch />
                  </Group>
                </Box>
              </Card>
            </Grid.Col>

            <Grid.Col span={{ base: 12, md: 6 }}>
              <Card shadow="sm" padding="lg" radius="md" withBorder>
                <Group justify="space-between" mb="md">
                  <Text fw={500} size="lg">Data Management</Text>
                  <ActionIcon variant="light" color="green">
                    <IconDatabase size={20} />
                  </ActionIcon>
                </Group>
                <Box mb="md">
                  <Group justify="space-between" mb="sm">
                    <Text>Auto Backup</Text>
                    <Switch defaultChecked />
                  </Group>
                  <Group justify="space-between" mb="sm">
                    <Text>Data Retention</Text>
                    <Switch defaultChecked />
                  </Group>
                  <Group justify="space-between">
                    <Text>Export Data</Text>
                    <Button size="xs" variant="light">Export</Button>
                  </Group>
                </Box>
              </Card>
            </Grid.Col>
          </Grid>
        </Box>
      </Container>
    </App>
  )
}



