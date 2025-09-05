'use client';

import {
  AppShell as MantineAppShell,
  Text,
  Group,
  ActionIcon,
  ThemeIcon,
  Stack,
  Divider,
  Box,
  Container,
  Button,
  ScrollArea,
  NavLink,
  Switch,
  useMantineColorScheme,
  Burger,
} from '@mantine/core';
import { useDisclosure } from '@mantine/hooks';
import {
  IconBrain,
  IconDashboard,
  IconTarget,
  IconShield,
  IconChartBar,
  IconSettings,
  IconUser,
  IconBell,
  IconUpload,
  IconFileText,
  IconAlertTriangle,
  IconDatabase,
  IconSearch,
  IconMoon,
  IconSun,
  IconRobot,
  IconReport,
  IconGitBranch,
  IconTestPipe,
  IconActivity,
} from '@tabler/icons-react';
import { useRouter, usePathname } from 'next/navigation';
import { useState } from 'react';
import OnboardingWizard from '../OnboardingWizard';

const navigationItems = [
  {
    label: 'Dashboard',
    icon: <IconDashboard size={16} />,
    href: '/dashboard',
  },
  {
    label: 'Model Assessment',
    icon: <IconTarget size={16} />,
    href: '/model-assessment',
    children: [
      { label: 'Upload Model', icon: <IconUpload size={16} />, href: '/model-assessment/upload' },
      { label: 'Active Assessments', icon: <IconTarget size={16} />, href: '/model-assessment/active' },
      { label: 'Assessment History', icon: <IconFileText size={16} />, href: '/model-assessment/history' },
    ],
  },
  {
    label: 'Compliance Management',
    icon: <IconShield size={16} />,
    href: '/compliance',
    children: [
      { label: 'Overview', icon: <IconDashboard size={16} />, href: '/compliance/overview' },
      { label: 'Frameworks', icon: <IconFileText size={16} />, href: '/compliance/frameworks' },
      { label: 'Audits', icon: <IconSearch size={16} />, href: '/compliance/audits' },
      { label: 'Policies', icon: <IconFileText size={16} />, href: '/compliance/policies' },
    ],
  },
  {
    label: 'Security Center',
    icon: <IconShield size={16} />,
    href: '/security',
    children: [
      { label: 'Security Scans', icon: <IconShield size={16} />, href: '/security' },
      { label: 'Container Security', icon: <IconDatabase size={16} />, href: '/security/container' },
      { label: 'LLM Security', icon: <IconBrain size={16} />, href: '/security/llm' },
      { label: 'Model Security', icon: <IconRobot size={16} />, href: '/security/model' },
    ],
  },
  {
    label: 'Risk & Security',
    icon: <IconAlertTriangle size={16} />,
    href: '/risk-security',
    children: [
      { label: 'Risk Matrix', icon: <IconChartBar size={16} />, href: '/risk-security/matrix' },
      { label: 'Security Monitoring', icon: <IconShield size={16} />, href: '/risk-security/monitoring' },
      { label: 'Threat Detection', icon: <IconAlertTriangle size={16} />, href: '/risk-security/threats' },
    ],
  },
  {
    label: 'Reporting & Analytics',
    icon: <IconChartBar size={16} />,
    href: '/reporting',
    children: [
      { label: 'Executive Dashboard', icon: <IconDashboard size={16} />, href: '/reporting/executive' },
      { label: 'Technical Reports', icon: <IconFileText size={16} />, href: '/reporting/technical' },
      { label: 'Custom Analytics', icon: <IconChartBar size={16} />, href: '/reporting/analytics' },
    ],
  },
  {
    label: 'Settings',
    icon: <IconSettings size={16} />,
    href: '/settings',
    children: [
      { label: 'User Management', icon: <IconUser size={16} />, href: '/settings/users' },
      { label: 'System Configuration', icon: <IconSettings size={16} />, href: '/settings/system' },
      { label: 'Data Management', icon: <IconDatabase size={16} />, href: '/settings/data' },
    ],
  },
];

interface AppShellProps {
  children: React.ReactNode;
}

export function AppShell({ children }: AppShellProps) {
  const router = useRouter();
  const pathname = usePathname();
  const { colorScheme, toggleColorScheme } = useMantineColorScheme();
  const [opened, { toggle }] = useDisclosure(false);
  const [onboardingOpened, setOnboardingOpened] = useState(false);

  const renderNavItems = (items: typeof navigationItems, level: number = 0) => {
    return items.map((item) => (
      <Box key={item.href}>
        <NavLink
          label={item.label}
          leftSection={item.icon}
          active={pathname === item.href}
          onClick={() => router.push(item.href)}
          variant="filled"
          style={{ marginLeft: level * 16 }}
        />
        {item.children && (
          <Box ml="md">
            {renderNavItems(item.children, level + 1)}
          </Box>
        )}
      </Box>
    ));
  };

  return (
    <>
      <MantineAppShell
        header={{ height: 60 }}
        navbar={{ width: 280, breakpoint: 'sm', collapsed: { mobile: !opened } }}
        padding="md"
        bg={colorScheme === 'dark' ? 'dark.8' : 'gray.0'}
      >
        <MantineAppShell.Header>
          <Group h="100%" px="md" justify="space-between">
            <Group>
              <Burger opened={opened} onClick={toggle} hiddenFrom="sm" size="sm" />
              <Group gap="xs">
                <ThemeIcon size="lg" radius="md" color="blue" variant="light">
                  <IconBrain size="1.5rem" />
                </ThemeIcon>
                <Text fw={600} size="lg" c={colorScheme === 'dark' ? 'white' : 'dark'}>
                  FairMind AI Governance
                </Text>
              </Group>
            </Group>
            <Group>
              <Switch
                checked={colorScheme === 'dark'}
                onChange={toggleColorScheme}
                size="md"
                onLabel={<IconSun size="1rem" stroke={2.5} />}
                offLabel={<IconMoon size="1rem" stroke={2.5} />}
              />
              <ActionIcon variant="light" size="lg">
                <IconBell size="1.2rem" />
              </ActionIcon>
              <Button
                variant="light"
                size="sm"
                onClick={() => setOnboardingOpened(true)}
                leftSection={<IconRobot size="1rem" />}
              >
                AI Setup
              </Button>
            </Group>
          </Group>
        </MantineAppShell.Header>

        <MantineAppShell.Navbar p="md" bg={colorScheme === 'dark' ? 'dark.7' : 'white'}>
          <ScrollArea h="100%">
            <Stack gap="md">
              {/* AI Governance Core */}
              <Text size="xs" tt="uppercase" fw={700} c="dimmed">
                AI Governance
              </Text>
              
              <Button
                variant={pathname === '/dashboard' ? 'light' : 'subtle'}
                leftSection={<IconDashboard size="1rem" />}
                justify="flex-start"
                fullWidth
                onClick={() => router.push('/dashboard')}
              >
                Governance Dashboard
              </Button>
              
              <Button
                variant={pathname === '/models' ? 'light' : 'subtle'}
                leftSection={<IconRobot size="1rem" />}
                justify="flex-start"
                fullWidth
                onClick={() => router.push('/models')}
              >
                Model Registry
              </Button>
              
              <Button
                variant={pathname === '/datasets' ? 'light' : 'subtle'}
                leftSection={<IconDatabase size="1rem" />}
                justify="flex-start"
                fullWidth
                onClick={() => router.push('/datasets')}
              >
                Dataset Management
              </Button>
              
              <Button
                variant={pathname === '/ai-bom' ? 'light' : 'subtle'}
                leftSection={<IconFileText size="1rem" />}
                justify="flex-start"
                fullWidth
                onClick={() => router.push('/ai-bom')}
              >
                AI/ML BOM
              </Button>

              <Divider />

              {/* Bias & Fairness */}
              <Text size="xs" tt="uppercase" fw={700} c="dimmed">
                Bias & Fairness
              </Text>
              
              <Button
                variant={pathname === '/bias-analysis' ? 'light' : 'subtle'}
                leftSection={<IconTarget size="1rem" />}
                justify="flex-start"
                fullWidth
                onClick={() => router.push('/bias-analysis')}
              >
                Bias Detection
              </Button>
              
              <Button
                variant={pathname === '/fairness-metrics' ? 'light' : 'subtle'}
                leftSection={<IconChartBar size="1rem" />}
                justify="flex-start"
                fullWidth
                onClick={() => router.push('/fairness-metrics')}
              >
                Fairness Metrics
              </Button>
              
              <Button
                variant={pathname === '/bias-reports' ? 'light' : 'subtle'}
                leftSection={<IconReport size="1rem" />}
                justify="flex-start"
                fullWidth
                onClick={() => router.push('/bias-reports')}
              >
                Bias Reports
              </Button>

              <Divider />

              {/* Security & Compliance */}
              <Text size="xs" tt="uppercase" fw={700} c="dimmed">
                Security & Compliance
              </Text>
              
              <Button
                variant={pathname === '/security-analysis' ? 'light' : 'subtle'}
                leftSection={<IconShield size="1rem" />}
                justify="flex-start"
                fullWidth
                onClick={() => router.push('/security-analysis')}
              >
                Security Scanning
              </Button>
              
              <Button
                variant={pathname === '/compliance' ? 'light' : 'subtle'}
                leftSection={<IconFileText size="1rem" />}
                justify="flex-start"
                fullWidth
                onClick={() => router.push('/compliance')}
              >
                Compliance Tracking
              </Button>
              
              <Button
                variant={pathname === '/audit-trail' ? 'light' : 'subtle'}
                leftSection={<IconActivity size="1rem" />}
                justify="flex-start"
                fullWidth
                onClick={() => router.push('/audit-trail')}
              >
                Audit Trail
              </Button>

              <Divider />

              {/* Model Operations */}
              <Text size="xs" tt="uppercase" fw={700} c="dimmed">
                Model Operations
              </Text>
              
              <Button
                variant={pathname === '/simulation' ? 'light' : 'subtle'}
                leftSection={<IconTestPipe size="1rem" />}
                justify="flex-start"
                fullWidth
                onClick={() => router.push('/simulation')}
              >
                Model Testing
              </Button>
              
              <Button
                variant={pathname === '/monitoring' ? 'light' : 'subtle'}
                leftSection={<IconChartBar size="1rem" />}
                justify="flex-start"
                fullWidth
                onClick={() => router.push('/monitoring')}
              >
                Performance Monitoring
              </Button>
              
              <Button
                variant={pathname === '/model-lineage' ? 'light' : 'subtle'}
                leftSection={<IconGitBranch size="1rem" />}
                justify="flex-start"
                fullWidth
                onClick={() => router.push('/model-lineage')}
              >
                Model Lineage
              </Button>

              <Divider />

              {/* System */}
              <Text size="xs" tt="uppercase" fw={700} c="dimmed">
                System
              </Text>
              
              <Button
                variant={pathname === '/settings' ? 'light' : 'subtle'}
                leftSection={<IconSettings size="1rem" />}
                justify="flex-start"
                fullWidth
                onClick={() => router.push('/settings')}
              >
                Settings
              </Button>
              
              <Button
                variant={pathname === '/api-docs' ? 'light' : 'subtle'}
                leftSection={<IconFileText size="1rem" />}
                justify="flex-start"
                fullWidth
                onClick={() => window.open('http://localhost:8000/docs', '_blank')}
              >
                API Documentation
              </Button>
            </Stack>
          </ScrollArea>
        </MantineAppShell.Navbar>

        <MantineAppShell.Main>
          {children}
        </MantineAppShell.Main>
      </MantineAppShell>

      <OnboardingWizard
        opened={onboardingOpened}
        onClose={() => setOnboardingOpened(false)}
      />
    </>
  );
}
