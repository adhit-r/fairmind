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
} from '@mantine/core';
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
} from '@tabler/icons-react';
import { useRouter, usePathname } from 'next/navigation';

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
    <MantineAppShell
      header={{ height: 60 }}
      navbar={{ width: 280, breakpoint: 'md' }}
      padding="md"
    >
      <MantineAppShell.Header bg="white" withBorder>
        <Container size="lg" h="100%">
          <Group justify="space-between" h="100%">
            <Group>
              <ThemeIcon size="lg" radius="md" color="blue">
                <IconBrain size="1.5rem" />
              </ThemeIcon>
              <Text fw={600} size="lg" c="dark.8">
                FairMind
              </Text>
            </Group>

            <Group gap="sm">
              <ActionIcon variant="subtle" size="lg">
                <IconBell size="1.2rem" />
              </ActionIcon>
              <ActionIcon variant="subtle" size="lg">
                <IconUser size="1.2rem" />
              </ActionIcon>
              <ActionIcon variant="subtle" size="lg">
                <IconSettings size="1.2rem" />
              </ActionIcon>
            </Group>
          </Group>
        </Container>
      </MantineAppShell.Header>

      <MantineAppShell.Navbar bg="white" withBorder>
        <MantineAppShell.Section>
          <Text p="md" fw={500} size="sm" c="dimmed">
            Navigation
          </Text>
        </MantineAppShell.Section>

        <Divider />

        <MantineAppShell.Section grow component={ScrollArea}>
          <Stack gap={4} p="md">
            {renderNavItems(navigationItems)}
          </Stack>
        </MantineAppShell.Section>

        <MantineAppShell.Section p="md">
          <Divider mb="md" />
          <Stack gap="xs">
            <Text size="xs" c="dimmed" ta="center">
              FairMind v1.0.0
            </Text>
            <Text size="xs" c="dimmed" ta="center">
              AI Governance Platform
            </Text>
          </Stack>
        </MantineAppShell.Section>
      </MantineAppShell.Navbar>

      <MantineAppShell.Main>
        <Container size="lg">
          {children}
        </Container>
      </MantineAppShell.Main>
    </MantineAppShell>
  );
}
