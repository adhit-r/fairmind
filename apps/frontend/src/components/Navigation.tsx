'use client';

import {
  AppShell,
  NavLink,
  Group,
  Text,
  ActionIcon,
  Burger,
  ScrollArea,
  Divider,
  Badge,
  Stack,
  rem,
  Box,
  Button,
} from '@mantine/core';
import { useDisclosure } from '@mantine/hooks';
import {
  IconDashboard,
  IconBrain,
  IconShield,
  IconTarget,
  IconFileAnalytics,
  IconLock,
  IconActivity,
  IconDatabase,
  IconTrendingUp,
  IconCpu,
  IconSearch,
  IconBell,
  IconSettings,
  IconPalette,
  IconChevronRight,
  IconPlus,
} from '@tabler/icons-react';
import { useState } from 'react';
import { useGlassmorphicTheme } from '@/providers/glassmorphic-theme-provider';

const navigationData = [
  {
    label: 'Overview',
    icon: IconDashboard,
    links: [
      { label: 'Dashboard', href: '/' },
      { label: 'System Status', href: '/status' },
    ],
  },
  {
    label: 'AI Models',
    icon: IconBrain,
    links: [
      { label: 'Model Registry', href: '/models' },
      { label: 'Model Provenance', href: '/provenance' },
      { label: 'Real-time Integration', href: '/realtime-models' },
    ],
  },
  {
    label: 'Bias Detection',
    icon: IconTarget,
    links: [
      { label: 'Bias Analysis', href: '/bias' },
      { label: 'Advanced Detection', href: '/advanced-bias' },
      { label: 'Modern Detection', href: '/modern-bias' },
    ],
  },
  {
    label: 'Fairness Governance',
    icon: IconShield,
    links: [
      { label: 'Fairness Metrics', href: '/fairness' },
      { label: 'Policy Management', href: '/policies' },
      { label: 'Compliance Frameworks', href: '/compliance' },
    ],
  },
  {
    label: 'AI Governance',
    icon: IconFileAnalytics,
    links: [
      { label: 'Governance Hub', href: '/ai-governance' },
      { label: 'AI Bill of Materials', href: '/ai-bom' },
      { label: 'Risk Management', href: '/risks' },
    ],
  },
  {
    label: 'Security',
    icon: IconLock,
    links: [
      { label: 'Security Testing', href: '/security' },
      { label: 'Vulnerability Scans', href: '/security/scans' },
    ],
  },
  {
    label: 'Monitoring',
    icon: IconActivity,
    links: [
      { label: 'Real-time Monitoring', href: '/monitoring' },
      { label: 'Alert Management', href: '/monitoring/alerts' },
    ],
  },
  {
    label: 'Data & Datasets',
    icon: IconDatabase,
    links: [
      { label: 'Dataset Management', href: '/datasets' },
      { label: 'Database Health', href: '/database/health' },
    ],
  },
  {
    label: 'Benchmarking',
    icon: IconTrendingUp,
    links: [
      { label: 'Benchmark Suite', href: '/benchmarks' },
      { label: 'Performance Tests', href: '/benchmarks/performance' },
    ],
  },
  {
    label: 'Tools & Integration',
    icon: IconCpu,
    links: [
      { label: 'Modern Tools', href: '/modern-tools' },
      { label: 'Simulations', href: '/simulations' },
    ],
  },
  {
    label: 'Design System',
    icon: IconPalette,
    links: [
      { label: 'Design System', href: '/design-system' },
      { label: 'Test Page', href: '/test-design-system' },
      { label: 'Brutalism Test', href: '/test-brutalism' },
      { label: 'Navigation Test', href: '/test-navigation' },
      { label: 'UI Test', href: '/test-ui' },
      { label: 'Verify Design System', href: '/verify-design-system' },
      { label: 'Test New Nav', href: '/test-new-nav' },
      { label: 'Test Assessment Button', href: '/test-assessment-button' },
      { label: 'Test Orange Logo', href: '/test-orange-logo' },
      { label: 'Design System JSON', href: '/design-system-json' },
    ],
  },
];

interface NavigationProps {
  children: React.ReactNode;
}

export function Navigation({ children }: NavigationProps) {
  const [opened, { toggle }] = useDisclosure();
  const [activeSection, setActiveSection] = useState<string | null>(null);
  const { colorScheme } = useGlassmorphicTheme();

  // Brutalist styles for navbar
  const navbarBrutalistStyle = {
    background: colorScheme === 'dark' ? 'var(--color-black)' : 'var(--color-white)',
    border: '2px solid var(--color-black)',
    borderRadius: 'var(--border-radius-none)',
    boxShadow: 'var(--shadow-brutal)',
  };

  // Brutalist styles for header
  const headerBrutalistStyle = {
    background: colorScheme === 'dark' ? 'var(--color-black)' : 'var(--color-white)',
    border: '2px solid var(--color-black)',
    borderBottom: '2px solid var(--color-black)',
    boxShadow: 'var(--shadow-brutal)',
  };

  // Styles for the "New Assessment" button
  const newAssessmentButtonStyle = {
    background: 'var(--color-orange)',
    color: 'var(--color-white)',
    border: '2px solid var(--color-black)',
    borderRadius: 'var(--border-radius-none)',
    padding: `${rem(8)} ${rem(12)}`,
    margin: `0 0 ${rem(8)} 0`,
    fontWeight: 'var(--font-weight-bold)',
    boxShadow: 'var(--shadow-brutal)',
    width: '100%',
    justifyContent: 'flex-start',
    fontFamily: 'var(--font-family-display)',
  };

  const newAssessmentButtonHoverStyle = {
    background: 'var(--color-orange-dark)',
    color: 'var(--color-white)',
    transform: 'translate(-2px, -2px)',
    boxShadow: 'var(--shadow-brutal-lg)',
  };

  // Styles for navigation items - brutalist design with orange accent
  const navItemStyle = {
    background: 'transparent',
    border: '2px solid var(--color-black)',
    borderRadius: 'var(--border-radius-none)',
    padding: `${rem(8)} ${rem(12)}`,
    marginBottom: rem(2),
    transition: 'all var(--transition-duration-fast) ease',
    fontWeight: 'var(--font-weight-bold)',
    color: colorScheme === 'dark' ? 'var(--color-white)' : 'var(--color-black)',
    boxShadow: 'var(--shadow-brutal)',
    width: '100%',
    justifyContent: 'flex-start',
  };

  const navItemHoverStyle = {
    background: 'var(--color-orange)', // Orange accent on hover
    color: 'var(--color-white)',
    transform: 'translate(-2px, -2px)',
    boxShadow: 'var(--shadow-brutal-lg)',
  };

  const activeNavItemStyle = {
    background: 'var(--color-orange)', // Orange accent for active items
    color: 'var(--color-white)',
    border: '2px solid var(--color-black)',
    borderRadius: 'var(--border-radius-none)',
    padding: `${rem(8)} ${rem(12)}`,
    marginBottom: rem(2),
    fontWeight: 'var(--font-weight-bold)',
    boxShadow: 'var(--shadow-brutal-lg)',
    transform: 'translate(-2px, -2px)',
  };

  const subNavItemStyle = {
    background: 'transparent',
    border: '2px solid var(--color-black)',
    borderRadius: 'var(--border-radius-none)',
    padding: `${rem(6)} ${rem(16)}`,
    margin: `${rem(2)} 0`,
    transition: 'all var(--transition-duration-fast) ease',
    color: colorScheme === 'dark' ? 'var(--color-gray-300)' : 'var(--color-gray-700)',
    boxShadow: 'var(--shadow-brutal-sm)',
    width: '100%',
    justifyContent: 'flex-start',
  };

  const subNavItemHoverStyle = {
    background: 'var(--color-orange-light)', // Light orange on hover
    color: 'var(--color-white)',
    transform: 'translate(-2px, -2px)',
    boxShadow: 'var(--shadow-brutal)',
  };

  return (
    <AppShell
      navbar={{
        width: 260,
        breakpoint: 'sm',
        collapsed: { mobile: !opened },
      }}
      header={{ height: 60 }}
      padding="md"
    >
      <AppShell.Header style={headerBrutalistStyle}>
        <Group h="100%" px="md" justify="space-between">
          <Group gap="xs">
            <Burger opened={opened} onClick={toggle} hiddenFrom="sm" size="sm" />
            <OrangeLogo size="sm" />
          </Group>

          <Group gap="xs">
            <ActionIcon
              variant="filled"
              size="lg"
              radius="xs"
              color="orange"
              style={{
                border: '2px solid var(--color-black)',
                boxShadow: 'var(--shadow-brutal)',
                background: 'var(--color-orange)',
                transform: 'translate(0, 0)',
                transition: 'transform var(--transition-duration-fast) ease, box-shadow var(--transition-duration-fast) ease',
              }}
            >
              <IconSearch size={18} />
            </ActionIcon>
            <ActionIcon
              variant="filled"
              size="lg"
              radius="xs"
              color="orange"
              style={{
                border: '2px solid var(--color-black)',
                boxShadow: 'var(--shadow-brutal)',
                background: 'var(--color-orange)',
                transform: 'translate(0, 0)',
                transition: 'transform var(--transition-duration-fast) ease, box-shadow var(--transition-duration-fast) ease',
              }}
            >
              <IconBell size={18} />
            </ActionIcon>
            <ActionIcon
              variant="filled"
              size="lg"
              radius="xs"
              color="orange"
              style={{
                border: '2px solid var(--color-black)',
                boxShadow: 'var(--shadow-brutal)',
                background: 'var(--color-orange)',
                transform: 'translate(0, 0)',
                transition: 'transform var(--transition-duration-fast) ease, box-shadow var(--transition-duration-fast) ease',
              }}
            >
              <IconSettings size={18} />
            </ActionIcon>
          </Group>
        </Group>
      </AppShell.Header>

      <AppShell.Navbar p="md" style={navbarBrutalistStyle}>
        <AppShell.Section grow component={ScrollArea}>
          {/* New Assessment Button */}
          <Button
            variant="filled"
            color="orange"
            style={newAssessmentButtonStyle}
            onMouseEnter={(e) => {
              Object.assign(e.currentTarget.style, newAssessmentButtonHoverStyle);
            }}
            onMouseLeave={(e) => {
              Object.assign(e.currentTarget.style, newAssessmentButtonStyle);
            }}
          >
            <Group gap="sm" wrap="nowrap">
              <IconPlus size={18} color="var(--color-white)" stroke={2} />
              <Text 
                size="sm" 
                fw={700}
                c="white"
                style={{ 
                  fontFamily: 'var(--font-family-display)',
                }}
              >
                New Assessment
              </Text>
            </Group>
          </Button>
          
          <Stack gap={2}>
            {navigationData.map((section) => (
              <div key={section.label}>
                <Button
                  variant="default"
                  onClick={() =>
                    setActiveSection(activeSection === section.label ? null : section.label)
                  }
                  style={activeSection === section.label ? activeNavItemStyle : navItemStyle}
                  onMouseEnter={(e) => {
                    if (activeSection !== section.label) {
                      Object.assign(e.currentTarget.style, navItemHoverStyle);
                    }
                  }}
                  onMouseLeave={(e) => {
                    if (activeSection !== section.label) {
                      Object.assign(e.currentTarget.style, navItemStyle);
                    }
                  }}
                >
                  <Group gap="sm" wrap="nowrap" justify="space-between" w="100%">
                    <Group gap="sm" wrap="nowrap">
                      <section.icon 
                        size={18} 
                        color={activeSection === section.label ? 'var(--color-white)' : (colorScheme === 'dark' ? 'var(--color-white)' : 'var(--color-black)')} 
                        stroke={2}
                      />
                      <Text 
                        size="sm" 
                        fw={700}
                        c={activeSection === section.label ? 'var(--color-white)' : (colorScheme === 'dark' ? 'var(--color-white)' : 'var(--color-black)')}
                        style={{ 
                          overflow: 'hidden', 
                          textOverflow: 'ellipsis', 
                          whiteSpace: 'nowrap',
                          fontFamily: 'var(--font-family-display)',
                        }}
                      >
                        {section.label}
                      </Text>
                    </Group>
                    <IconChevronRight 
                      size={16} 
                      style={{ 
                        transform: activeSection === section.label ? 'rotate(90deg)' : 'rotate(0deg)',
                        transition: 'transform 200ms ease',
                      }} 
                    />
                  </Group>
                </Button>
                
                {activeSection === section.label && (
                  <Stack gap={1} mt="xs" ml="md">
                    {section.links.map((link) => (
                      <Button
                        key={link.href}
                        component="a"
                        href={link.href}
                        variant="default"
                        style={subNavItemStyle}
                        onMouseEnter={(e) => {
                          Object.assign(e.currentTarget.style, subNavItemHoverStyle);
                        }}
                        onMouseLeave={(e) => {
                          Object.assign(e.currentTarget.style, subNavItemStyle);
                        }}
                      >
                        <Text 
                          size="sm" 
                          fw={500}
                          c={colorScheme === 'dark' ? 'var(--color-gray-300)' : 'var(--color-gray-700)'}
                          style={{ 
                            overflow: 'hidden', 
                            textOverflow: 'ellipsis', 
                            whiteSpace: 'nowrap' 
                          }}
                        >
                          {link.label}
                        </Text>
                      </Button>
                    ))}
                  </Stack>
                )}
              </div>
            ))}
          </Stack>
        </AppShell.Section>

        <AppShell.Section>
          <Divider my="sm" color="var(--color-black)" />
          <Group justify="center" p="md">
            <Text 
              size="xs" 
              fw={700}
              c={colorScheme === 'dark' ? 'var(--color-white)' : 'var(--color-black)'}
              style={{ 
                fontFamily: 'var(--font-family-display)',
              }}
            >
              FairMind AI Platform
            </Text>
          </Group>
        </AppShell.Section>
      </AppShell.Navbar>

      <AppShell.Main>{children}</AppShell.Main>
    </AppShell>
  );
}