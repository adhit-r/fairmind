import React from 'react';
import { Skeleton, Card, Stack, Group, Grid, useMantineColorScheme } from '@mantine/core';

interface LoadingSkeletonProps {
  variant?: 'card' | 'table' | 'chart' | 'dashboard' | 'list';
  count?: number;
  height?: number | string;
}

export const LoadingSkeleton: React.FC<LoadingSkeletonProps> = ({
  variant = 'card',
  count = 1,
  height = 200
}) => {
  const { colorScheme } = useMantineColorScheme();
  const brutalistCardStyle = {
    background: colorScheme === 'dark' ? 'var(--color-black)' : 'var(--color-white)',
    border: '2px solid var(--color-black)',
    borderRadius: 'var(--border-radius-base)',
    boxShadow: 'var(--shadow-brutal)',
    transition: 'all var(--transition-duration-fast) ease',
  };

  const renderSkeleton = () => {
    switch (variant) {
      case 'dashboard':
        return (
          <Grid>
            {Array.from({ length: 4 }).map((_, index) => (
              <Grid.Col key={index} span={{ base: 12, sm: 6, lg: 3 }}>
                <Card style={brutalistCardStyle} p="lg">
                  <Stack gap="sm">
                    <Group justify="space-between">
                      <Skeleton height={20} width="60%" />
                      <Skeleton height={24} width={24} circle />
                    </Group>
                    <Skeleton height={32} width="40%" />
                    <Skeleton height={16} width="80%" />
                  </Stack>
                </Card>
              </Grid.Col>
            ))}
          </Grid>
        );

      case 'chart':
        return (
          <Card style={brutalistCardStyle} p="lg">
            <Stack gap="md">
              <Group justify="space-between">
                <Skeleton height={24} width="30%" />
                <Skeleton height={20} width="20%" />
              </Group>
              <Skeleton height={height} />
              <Group justify="space-between">
                <Skeleton height={16} width="25%" />
                <Skeleton height={16} width="25%" />
                <Skeleton height={16} width="25%" />
              </Group>
            </Stack>
          </Card>
        );

      case 'table':
        return (
          <Card style={brutalistCardStyle} p="lg">
            <Stack gap="md">
              <Group justify="space-between">
                <Skeleton height={24} width="30%" />
                <Skeleton height={36} width="120px" />
              </Group>
              {Array.from({ length: 5 }).map((_, index) => (
                <Group key={index} justify="space-between">
                  <Skeleton height={20} width="25%" />
                  <Skeleton height={20} width="20%" />
                  <Skeleton height={20} width="15%" />
                  <Skeleton height={20} width="20%" />
                </Group>
              ))}
            </Stack>
          </Card>
        );

      case 'list':
        return (
          <Stack gap="md">
            {Array.from({ length: count }).map((_, index) => (
              <Card key={index} style={brutalistCardStyle} p="md">
                <Group>
                  <Skeleton height={40} width={40} circle />
                  <Stack gap="xs" style={{ flex: 1 }}>
                    <Skeleton height={16} width="60%" />
                    <Skeleton height={14} width="80%" />
                  </Stack>
                  <Skeleton height={24} width={60} />
                </Group>
              </Card>
            ))}
          </Stack>
        );

      case 'card':
      default:
        return (
          <Stack gap="md">
            {Array.from({ length: count }).map((_, index) => (
              <Card key={index} style={brutalistCardStyle} p="lg">
                <Stack gap="md">
                  <Group justify="space-between">
                    <Skeleton height={24} width="40%" />
                    <Skeleton height={20} width={20} circle />
                  </Group>
                  <Skeleton height={height} />
                  <Group justify="space-between">
                    <Skeleton height={16} width="30%" />
                    <Skeleton height={16} width="20%" />
                  </Group>
                </Stack>
              </Card>
            ))}
          </Stack>
        );
    }
  };

  return <>{renderSkeleton()}</>;
};

// Specific skeleton components for common use cases
export const DashboardSkeleton = () => <LoadingSkeleton variant="dashboard" />;
export const ChartSkeleton = () => <LoadingSkeleton variant="chart" height={300} />;
export const TableSkeleton = () => <LoadingSkeleton variant="table" />;
export const CardSkeleton = ({ count = 3 }: { count?: number }) => (
  <LoadingSkeleton variant="card" count={count} />
);
export const ListSkeleton = ({ count = 5 }: { count?: number }) => (
  <LoadingSkeleton variant="list" count={count} />
);

export default LoadingSkeleton;