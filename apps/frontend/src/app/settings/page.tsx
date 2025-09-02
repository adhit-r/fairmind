'use client';

import {
  Container,
  Title,
  Text,
  Card,
  SimpleGrid,
  Stack,
  Group,
  Button,
  Switch,
  Select,
  TextInput,
  NumberInput,
  Textarea,
  Divider,
  Tabs,
  Alert,
  Badge,
  ThemeIcon,
  Box,
  PasswordInput,
  ColorInput,
  FileInput,
  Checkbox,
  ActionIcon,
  Modal,
  Accordion,
  List,
} from '@mantine/core';
import {
  IconSettings,
  IconUser,
  IconShield,
  IconDatabase,
  IconBell,
  IconPalette,
  IconDownload,
  IconUpload,
  IconEye,
  IconEdit,
  IconTrash,
  IconPlus,
  IconCheck,
  IconX,
  IconAlertTriangle,
  IconBrain,
  IconTarget,
  IconShieldCheck,
  IconGlobe,
  IconBuilding,
  IconLock,
  IconKey,
  IconLink,
} from '@tabler/icons-react';
import { useState } from 'react';

// Mock data - replace with real data from your backend
const mockSettingsData = {
  user: {
    name: 'John Doe',
    email: 'john.doe@company.com',
    role: 'Admin',
    department: 'AI Governance',
    avatar: null,
  },
  preferences: {
    theme: 'light',
    language: 'en',
    timezone: 'UTC',
    notifications: {
      email: true,
      push: true,
      sms: false,
      criticalAlerts: true,
      weeklyReports: true,
      monthlyReports: false,
    },
    dashboard: {
      defaultView: 'overview',
      refreshInterval: 30,
      showCharts: true,
      showAlerts: true,
    },
  },
  integrations: [
    {
      name: 'Supabase',
      type: 'Database',
      status: 'Connected',
      lastSync: '2024-01-15 10:30:00',
      config: {
        url: 'https://company.supabase.co',
        database: 'fairmind_prod',
        schema: 'public',
      },
    },
    {
      name: 'FastAPI Backend',
      type: 'API',
      status: 'Connected',
      lastSync: '2024-01-15 10:25:00',
      config: {
        url: 'https://api.fairmind.com',
        version: 'v1.0.0',
        endpoints: 15,
      },
    },
    {
      name: 'Slack',
      type: 'Notifications',
      status: 'Disconnected',
      lastSync: 'Never',
      config: {
        channel: '#ai-governance',
        webhook: 'https://hooks.slack.com/...',
      },
    },
  ],
  security: {
    twoFactorEnabled: true,
    sessionTimeout: 480,
    passwordPolicy: 'Strong',
    lastPasswordChange: '2024-01-01',
    failedLoginAttempts: 0,
    ipWhitelist: ['192.168.1.0/24', '10.0.0.0/8'],
  },
  system: {
    version: '1.2.0',
    lastUpdate: '2024-01-10',
    databaseSize: '2.4 GB',
    logRetention: 90,
    backupFrequency: 'Daily',
    monitoring: {
      enabled: true,
      interval: 5,
      alertThreshold: 80,
    },
  },
};

export default function SettingsPage() {
  const [activeTab, setActiveTab] = useState('profile');
  const [showIntegrationModal, setShowIntegrationModal] = useState(false);
  const [editingIntegration, setEditingIntegration] = useState<any>(null);
  const [newIntegration, setNewIntegration] = useState({
    name: '',
    type: '',
    config: {},
  });

  const handleSaveSettings = () => {
    // TODO: Implement settings save logic
    console.log('Saving settings...');
  };

  const handleTestConnection = (integration: any) => {
    // TODO: Implement connection test logic
    console.log('Testing connection for:', integration.name);
  };

  const handleDisconnectIntegration = (integration: any) => {
    // TODO: Implement disconnect logic
    console.log('Disconnecting:', integration.name);
  };

  return (
    <Container size="xl" py="xl">
      <Stack spacing="xl">
        {/* Header */}
        <Group position="apart">
          <Box>
            <Title order={1}>Settings & Configuration</Title>
            <Text color="dimmed" size="sm">
              Manage your account preferences, system settings, and integrations
            </Text>
          </Box>
          <Group>
            <Button leftIcon={<IconDownload size={16} />} variant="outline">
              Export Settings
            </Button>
            <Button leftIcon={<IconUpload size={16} />} variant="outline">
              Import Settings
            </Button>
            <Button onClick={handleSaveSettings}>
              Save Changes
            </Button>
          </Group>
        </Group>

        {/* Settings Tabs */}
        <Tabs value={activeTab} onTabChange={(value) => setActiveTab(value as string)}>
          <Tabs.List>
            <Tabs.Tab value="profile" icon={<IconUser size={16} />}>
              Profile
            </Tabs.Tab>
            <Tabs.Tab value="preferences" icon={<IconSettings size={16} />}>
              Preferences
            </Tabs.Tab>
            <Tabs.Tab value="integrations" icon={<IconLink size={16} />}>
              Integrations
            </Tabs.Tab>
            <Tabs.Tab value="security" icon={<IconShield size={16} />}>
              Security
            </Tabs.Tab>
            <Tabs.Tab value="system" icon={<IconDatabase size={16} />}>
              System
            </Tabs.Tab>
          </Tabs.List>

          {/* Profile Tab */}
          <Tabs.Panel value="profile" pt="md">
            <Card withBorder>
              <Title order={3} mb="md">User Profile</Title>
              <SimpleGrid cols={2} spacing="lg">
                <TextInput
                  label="Full Name"
                  value={mockSettingsData.user.name}
                  placeholder="Enter your full name"
                />
                <TextInput
                  label="Email Address"
                  value={mockSettingsData.user.email}
                  placeholder="Enter your email"
                  type="email"
                />
                <Select
                  label="Role"
                  value={mockSettingsData.user.role}
                  data={['Admin', 'Manager', 'Analyst', 'Viewer']}
                />
                <TextInput
                  label="Department"
                  value={mockSettingsData.user.department}
                  placeholder="Enter your department"
                />
                <FileInput
                  label="Profile Picture"
                  placeholder="Upload profile picture"
                  accept="image/*"
                />
                <Box>
                  <Text size="sm" weight={500} mb="xs">
                    Account Status
                  </Text>
                  <Badge color="green" size="lg">
                    Active
                  </Badge>
                </Box>
              </SimpleGrid>
            </Card>
          </Tabs.Panel>

          {/* Preferences Tab */}
          <Tabs.Panel value="preferences" pt="md">
            <Stack spacing="lg">
              {/* Theme & Display */}
              <Card withBorder>
                <Title order={3} mb="md">Theme & Display</Title>
                <SimpleGrid cols={2} spacing="lg">
                  <Select
                    label="Theme"
                    value={mockSettingsData.preferences.theme}
                    data={[
                      { value: 'light', label: 'Light' },
                      { value: 'dark', label: 'Dark' },
                      { value: 'auto', label: 'Auto (System)' },
                    ]}
                  />
                  <Select
                    label="Language"
                    value={mockSettingsData.preferences.language}
                    data={[
                      { value: 'en', label: 'English' },
                      { value: 'es', label: 'Spanish' },
                      { value: 'fr', label: 'French' },
                      { value: 'de', label: 'German' },
                    ]}
                  />
                  <Select
                    label="Timezone"
                    value={mockSettingsData.preferences.timezone}
                    data={[
                      { value: 'UTC', label: 'UTC' },
                      { value: 'EST', label: 'Eastern Time' },
                      { value: 'PST', label: 'Pacific Time' },
                      { value: 'GMT', label: 'Greenwich Mean Time' },
                    ]}
                  />
                  <ColorInput
                    label="Accent Color"
                    placeholder="Choose accent color"
                    defaultValue="#228BE6"
                  />
                </SimpleGrid>
              </Card>

              {/* Notifications */}
              <Card withBorder>
                <Title order={3} mb="md">Notification Preferences</Title>
                <Stack spacing="md">
                  <Group position="apart">
                    <Box>
                      <Text weight={500}>Email Notifications</Text>
                      <Text size="sm" color="dimmed">Receive notifications via email</Text>
                    </Box>
                    <Switch
                      checked={mockSettingsData.preferences.notifications.email}
                      onChange={() => {}}
                    />
                  </Group>
                  <Group position="apart">
                    <Box>
                      <Text weight={500}>Push Notifications</Text>
                      <Text size="sm" color="dimmed">Receive push notifications in browser</Text>
                    </Box>
                    <Switch
                      checked={mockSettingsData.preferences.notifications.push}
                      onChange={() => {}}
                    />
                  </Group>
                  <Group position="apart">
                    <Box>
                      <Text weight={500}>Critical Alerts</Text>
                      <Text size="sm" color="dimmed">Always notify for critical issues</Text>
                    </Box>
                    <Switch
                      checked={mockSettingsData.preferences.notifications.criticalAlerts}
                      onChange={() => {}}
                    />
                  </Group>
                  <Group position="apart">
                    <Box>
                      <Text weight={500}>Weekly Reports</Text>
                      <Text size="sm" color="dimmed">Receive weekly summary reports</Text>
                    </Box>
                    <Switch
                      checked={mockSettingsData.preferences.notifications.weeklyReports}
                      onChange={() => {}}
                    />
                  </Group>
                </Stack>
              </Card>

              {/* Dashboard Settings */}
              <Card withBorder>
                <Title order={3} mb="md">Dashboard Settings</Title>
                <SimpleGrid cols={2} spacing="lg">
                  <Select
                    label="Default View"
                    value={mockSettingsData.preferences.dashboard.defaultView}
                    data={[
                      { value: 'overview', label: 'Overview' },
                      { value: 'models', label: 'Models' },
                      { value: 'analytics', label: 'Analytics' },
                      { value: 'compliance', label: 'Compliance' },
                    ]}
                  />
                  <NumberInput
                    label="Refresh Interval (seconds)"
                    value={mockSettingsData.preferences.dashboard.refreshInterval}
                    min={10}
                    max={300}
                    step={10}
                  />
                  <Group position="apart">
                    <Box>
                      <Text weight={500}>Show Charts</Text>
                      <Text size="sm" color="dimmed">Display interactive charts and graphs</Text>
                    </Box>
                    <Switch
                      checked={mockSettingsData.preferences.dashboard.showCharts}
                      onChange={() => {}}
                    />
                  </Group>
                  <Group position="apart">
                    <Box>
                      <Text weight={500}>Show Alerts</Text>
                      <Text size="sm" color="dimmed">Display real-time alerts and notifications</Text>
                    </Box>
                    <Switch
                      checked={mockSettingsData.preferences.dashboard.showAlerts}
                      onChange={() => {}}
                    />
                  </Group>
                </SimpleGrid>
              </Card>
            </Stack>
          </Tabs.Panel>

          {/* Integrations Tab */}
          <Tabs.Panel value="integrations" pt="md">
            <Card withBorder>
              <Group position="apart" mb="md">
                <Title order={3}>System Integrations</Title>
                <Button
                  leftIcon={<IconPlus size={16} />}
                  onClick={() => setShowIntegrationModal(true)}
                >
                  Add Integration
                </Button>
              </Group>

              <Stack spacing="md">
                {mockSettingsData.integrations.map((integration, index) => (
                  <Card key={index} withBorder p="md">
                    <Group position="apart">
                      <Box>
                        <Group spacing="sm" mb="xs">
                          <Text weight={500} size="lg">{integration.name}</Text>
                          <Badge
                            color={integration.status === 'Connected' ? 'green' : 'red'}
                          >
                            {integration.status}
                          </Badge>
                          <Badge variant="outline">{integration.type}</Badge>
                        </Group>
                        <Text size="sm" color="dimmed">
                          Last sync: {integration.lastSync}
                        </Text>
                        {integration.config.url && (
                          <Text size="xs" color="dimmed" mt="xs">
                            {integration.config.url}
                          </Text>
                        )}
                      </Box>
                      <Group spacing="xs">
                        <ActionIcon
                          size="sm"
                          variant="subtle"
                          onClick={() => handleTestConnection(integration)}
                        >
                          <IconEye size={16} />
                        </ActionIcon>
                        <ActionIcon
                          size="sm"
                          variant="subtle"
                          onClick={() => setEditingIntegration(integration)}
                        >
                          <IconEdit size={16} />
                        </ActionIcon>
                        <ActionIcon
                          size="sm"
                          variant="subtle"
                          color="red"
                          onClick={() => handleDisconnectIntegration(integration)}
                        >
                          <IconTrash size={16} />
                        </ActionIcon>
                      </Group>
                    </Group>
                  </Card>
                ))}
              </Stack>
            </Card>
          </Tabs.Panel>

          {/* Security Tab */}
          <Tabs.Panel value="security" pt="md">
            <Stack spacing="lg">
              <Card withBorder>
                <Title order={3} mb="md">Security Settings</Title>
                <SimpleGrid cols={2} spacing="lg">
                  <Group position="apart">
                    <Box>
                      <Text weight={500}>Two-Factor Authentication</Text>
                      <Text size="sm" color="dimmed">Add an extra layer of security</Text>
                    </Box>
                    <Switch
                      checked={mockSettingsData.security.twoFactorEnabled}
                      onChange={() => {}}
                    />
                  </Group>
                  <NumberInput
                    label="Session Timeout (minutes)"
                    value={mockSettingsData.security.sessionTimeout}
                    min={15}
                    max={1440}
                    step={15}
                  />
                  <Select
                    label="Password Policy"
                    value={mockSettingsData.security.passwordPolicy}
                    data={['Weak', 'Medium', 'Strong', 'Very Strong']}
                  />
                  <TextInput
                    label="Last Password Change"
                    value={mockSettingsData.security.lastPasswordChange}
                    readOnly
                  />
                </SimpleGrid>
              </Card>

              <Card withBorder>
                <Title order={3} mb="md">Access Control</Title>
                <Stack spacing="md">
                  <TextInput
                    label="Failed Login Attempts"
                    value={mockSettingsData.security.failedLoginAttempts.toString()}
                    readOnly
                  />
                  <Textarea
                    label="IP Whitelist"
                    value={mockSettingsData.security.ipWhitelist.join('\n')}
                    placeholder="Enter IP addresses or ranges (one per line)"
                    minRows={3}
                  />
                  <Button variant="outline" leftIcon={<IconPlus size={16} />}>
                    Add IP Address
                  </Button>
                </Stack>
              </Card>
            </Stack>
          </Tabs.Panel>

          {/* System Tab */}
          <Tabs.Panel value="system" pt="md">
            <Stack spacing="lg">
              <Card withBorder>
                <Title order={3} mb="md">System Information</Title>
                <SimpleGrid cols={2} spacing="lg">
                  <TextInput
                    label="Version"
                    value={mockSettingsData.system.version}
                    readOnly
                  />
                  <TextInput
                    label="Last Update"
                    value={mockSettingsData.system.lastUpdate}
                    readOnly
                  />
                  <TextInput
                    label="Database Size"
                    value={mockSettingsData.system.databaseSize}
                    readOnly
                  />
                  <NumberInput
                    label="Log Retention (days)"
                    value={mockSettingsData.system.logRetention}
                    min={7}
                    max={365}
                    step={7}
                  />
                  <Select
                    label="Backup Frequency"
                    value={mockSettingsData.system.backupFrequency}
                    data={['Daily', 'Weekly', 'Monthly']}
                  />
                  <Box>
                    <Text size="sm" weight={500} mb="xs">
                      System Status
                    </Text>
                    <Badge color="green" size="lg">
                      Healthy
                    </Badge>
                  </Box>
                </SimpleGrid>
              </Card>

              <Card withBorder>
                <Title order={3} mb="md">Monitoring & Alerts</Title>
                <Stack spacing="md">
                  <Group position="apart">
                    <Box>
                      <Text weight={500}>System Monitoring</Text>
                      <Text size="sm" color="dimmed">Enable automated system monitoring</Text>
                    </Box>
                    <Switch
                      checked={mockSettingsData.system.monitoring.enabled}
                      onChange={() => {}}
                    />
                  </Group>
                  <NumberInput
                    label="Monitoring Interval (minutes)"
                    value={mockSettingsData.system.monitoring.interval}
                    min={1}
                    max={60}
                    step={1}
                  />
                  <NumberInput
                    label="Alert Threshold (%)"
                    value={mockSettingsData.system.monitoring.alertThreshold}
                    min={50}
                    max={100}
                    step={5}
                  />
                </Stack>
              </Card>

              <Card withBorder>
                <Title order={3} mb="md">Maintenance</Title>
                <Group>
                  <Button variant="outline" leftIcon={<IconDownload size={16} />}>
                    Download Logs
                  </Button>
                  <Button variant="outline" leftIcon={<IconDatabase size={16} />}>
                    Database Backup
                  </Button>
                  <Button variant="outline" leftIcon={<IconSettings size={16} />}>
                    System Diagnostics
                  </Button>
                </Group>
              </Card>
            </Stack>
          </Tabs.Panel>
        </Tabs>
      </Stack>

      {/* Integration Modal */}
      <Modal
        opened={showIntegrationModal || !!editingIntegration}
        onClose={() => {
          setShowIntegrationModal(false);
          setEditingIntegration(null);
        }}
        title={editingIntegration ? 'Edit Integration' : 'Add New Integration'}
        size="lg"
      >
        <Stack spacing="md">
          <TextInput
            label="Integration Name"
            value={editingIntegration?.name || newIntegration.name}
            placeholder="Enter integration name"
            onChange={(e) => {
              if (editingIntegration) {
                setEditingIntegration({ ...editingIntegration, name: e.target.value });
              } else {
                setNewIntegration({ ...newIntegration, name: e.target.value });
              }
            }}
          />
          <Select
            label="Integration Type"
            value={editingIntegration?.type || newIntegration.type}
            data={[
              { value: 'Database', label: 'Database' },
              { value: 'API', label: 'API' },
              { value: 'Notifications', label: 'Notifications' },
              { value: 'Storage', label: 'Storage' },
              { value: 'Analytics', label: 'Analytics' },
            ]}
            onChange={(value) => {
              if (editingIntegration) {
                setEditingIntegration({ ...editingIntegration, type: value || '' });
              } else {
                setNewIntegration({ ...newIntegration, type: value || '' });
              }
            }}
          />
          <TextInput
            label="Connection URL"
            placeholder="Enter connection URL"
          />
          <TextInput
            label="API Key (if required)"
            placeholder="Enter API key"
            type="password"
          />
          <Group position="apart">
            <Button variant="outline" onClick={() => {
              setShowIntegrationModal(false);
              setEditingIntegration(null);
            }}>
              Cancel
            </Button>
            <Button>
              {editingIntegration ? 'Update Integration' : 'Add Integration'}
            </Button>
          </Group>
        </Stack>
      </Modal>
    </Container>
  );
}
