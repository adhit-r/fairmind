'use client';

import { MantineProvider } from '@mantine/core';
import { ModalsProvider } from '@mantine/modals';
import { Notifications } from '@mantine/notifications';
import { Spotlight, spotlight } from '@mantine/spotlight';
import { NProgress, NavigationProgress } from '@mantine/nprogress';
import { theme } from '@/lib/mantine';
import { IconSearch, IconDashboard, IconUsers, IconShield, IconBrain, IconChartBar, IconSettings } from '@tabler/icons-react';

const actions = [
  {
    id: 'dashboard',
    label: 'Dashboard',
    description: 'Go to main dashboard',
    onClick: () => window.location.href = '/dashboard',
    leftSection: <IconDashboard size="1.2rem" />,
  },
  {
    id: 'models',
    label: 'AI Models',
    description: 'Manage and analyze AI models',
    onClick: () => window.location.href = '/models',
    leftSection: <IconBrain size="1.2rem" />,
  },
  {
    id: 'bias-detection',
    label: 'Bias Detection',
    description: 'Analyze model fairness and bias',
    onClick: () => window.location.href = '/bias-detection',
    leftSection: <IconShield size="1.2rem" />,
  },
  {
    id: 'analytics',
    label: 'Analytics',
    description: 'View performance metrics and reports',
    onClick: () => window.location.href = '/analytics',
    leftSection: <IconChartBar size="1.2rem" />,
  },
  {
    id: 'users',
    label: 'Users',
    description: 'Manage user accounts and permissions',
    onClick: () => window.location.href = '/users',
    leftSection: <IconUsers size="1.2rem" />,
  },
  {
    id: 'settings',
    label: 'Settings',
    description: 'Configure system settings',
    onClick: () => window.location.href = '/settings',
    leftSection: <IconSettings size="1.2rem" />,
  },
];

export function MantineAppProvider({ children }: { children: React.ReactNode }) {
  return (
    <MantineProvider theme={theme} defaultColorScheme="light">
      <ModalsProvider>
        <Notifications position="top-right" />
        <NavigationProgress />
        <Spotlight
          actions={actions}
          nothingFound="Nothing found..."
          highlightQuery
          searchProps={{
            leftSection: <IconSearch size="1.2rem" />,
            placeholder: 'Search...',
          }}
          shortcut={['mod + K']}
        />
        {children}
      </ModalsProvider>
    </MantineProvider>
  );
}
