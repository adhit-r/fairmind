# Contributor Guide: Loading States & Skeleton Screens (Issue #99)

## Overview

This guide will help you implement consistent loading states and skeleton screens throughout the FairMind application. Since we don't have Figma designs, this document provides all the design patterns, examples, and implementation details you need.

## Design System

### Color Palette
- **Primary Colors**: Yellow (`#FF6B35` / `var(--color-orange)`) and Black (`#000000` / `var(--color-black)`)
- **Background**: White (`#FFFFFF` / `var(--color-white)`) in light mode, Black in dark mode
- **No gradients**: Use solid colors only
- **No emojis**: Use SVG icons exclusively

### Design Style
- **Neobrutal/Glassmorphic**: Bold borders, sharp shadows, glassmorphic effects
- **Borders**: 2-4px solid black borders
- **Shadows**: Brutalist shadows (`var(--shadow-brutal)`, `var(--shadow-brutal-lg)`)
- **Border Radius**: Minimal (`var(--border-radius-base)`) or zero for pure neobrutal
- **Typography**: Bold, uppercase for headings

### Key CSS Variables
```css
--color-black: #000000
--color-white: #FFFFFF
--color-orange: #FF6B35
--shadow-brutal: 4px 4px 0px 0px var(--color-black)
--shadow-brutal-lg: 8px 8px 0px 0px var(--color-black)
--border-radius-base: 4px
```

## Existing Components

### LoadingSkeleton Component

Location: `apps/frontend/src/components/LoadingSkeleton.tsx`

This component already exists and provides several variants:

- `DashboardSkeleton` - For dashboard stat cards
- `ChartSkeleton` - For chart components
- `TableSkeleton` - For table layouts
- `CardSkeleton` - For card grids
- `ListSkeleton` - For list views

**Usage Example:**
```typescript
import { DashboardSkeleton, ChartSkeleton, CardSkeleton } from '@/components/LoadingSkeleton';

// In your component
if (loading && !data) {
  return <DashboardSkeleton />;
}
```

### useApi Hook

Location: `apps/frontend/src/hooks/useApi.ts`

The `useApi` hook provides:
- `data` - The fetched data
- `loading` - Boolean indicating loading state
- `error` - Error object if request failed
- `retry` - Function to retry the request
- `refresh` - Function to refresh data

**Usage Pattern:**
```typescript
const { data, loading, error, retry } = useApi<DataType>(
  "/api/v1/endpoint",
  {
    fallbackData: mockData,
    enableRetry: true,
    cacheKey: 'my-cache-key'
  }
);

// Show skeleton while loading
if (loading && !data) {
  return <CardSkeleton count={3} />;
}

// Show error state
if (error && !data) {
  return (
    <Card style={brutalistCardStyle}>
      <Alert color="red" title="Error">
        {error.message}
      </Alert>
      <Button onClick={retry}>Retry</Button>
    </Card>
  );
}
```

## Implementation Patterns

### Pattern 1: Page-Level Loading States

For pages that fetch data on mount:

```typescript
'use client';

import { CardSkeleton } from '@/components/LoadingSkeleton';
import { useApi } from '@/hooks/useApi';
import { Card, Alert, Button, Stack } from '@mantine/core';
import { useMantineColorScheme } from '@mantine/core';

export default function MyPage() {
  const { colorScheme } = useMantineColorScheme();
  const { data, loading, error, retry } = useApi('/api/v1/my-endpoint');

  const brutalistCardStyle = {
    background: colorScheme === 'dark' ? 'var(--color-black)' : 'var(--color-white)',
    border: '2px solid var(--color-black)',
    borderRadius: 'var(--border-radius-base)',
    boxShadow: 'var(--shadow-brutal)',
    transition: 'all var(--transition-duration-fast) ease',
  };

  // Loading state
  if (loading && !data) {
    return <CardSkeleton count={3} />;
  }

  // Error state
  if (error && !data) {
    return (
      <Card style={brutalistCardStyle} p="lg">
        <Stack gap="md">
          <Alert color="red" title="Failed to load data">
            {error.message || 'Unable to fetch data. Please try again.'}
          </Alert>
          <Button 
            onClick={retry}
            style={{
              border: '2px solid var(--color-black)',
              boxShadow: 'var(--shadow-brutal)',
            }}
          >
            Retry
          </Button>
        </Stack>
      </Card>
    );
  }

  // Render content
  return (
    <div>
      {/* Your content here */}
    </div>
  );
}
```

### Pattern 2: Component-Level Loading States

For components that fetch their own data:

```typescript
import { ChartSkeleton } from '@/components/LoadingSkeleton';
import { useApi } from '@/hooks/useApi';

export default function MyChart() {
  const { data, loading, error, retry } = useApi<ChartData>('/api/v1/chart-data');

  if (loading) {
    return <ChartSkeleton />;
  }

  if (error && !data) {
    return (
      <Card style={brutalistCardStyle}>
        <Alert color="red">{error.message}</Alert>
        <Button onClick={retry}>Retry</Button>
      </Card>
    );
  }

  return (
    <Card style={brutalistCardStyle}>
      {/* Chart component */}
    </Card>
  );
}
```

### Pattern 3: Inline Loading States

For components that show loading within existing content:

```typescript
import { Loader, Skeleton } from '@mantine/core';

export default function MyComponent() {
  const { data, loading } = useApi('/api/v1/data');

  return (
    <Card style={brutalistCardStyle}>
      <Stack gap="md">
        <Group justify="space-between">
          <Title order={3}>My Title</Title>
          {loading && <Loader size="sm" />}
        </Group>
        
        {loading ? (
          <Stack gap="sm">
            <Skeleton height={20} width="60%" />
            <Skeleton height={20} width="80%" />
            <Skeleton height={20} width="40%" />
          </Stack>
        ) : (
          <div>{/* Your content */}</div>
        )}
      </Stack>
    </Card>
  );
}
```

### Pattern 4: Progress Indicators for Long Operations

For operations that take time (e.g., file uploads, benchmark runs):

```typescript
import { Progress, Button } from '@mantine/core';
import { useState } from 'react';

export default function LongOperationComponent() {
  const [progress, setProgress] = useState(0);
  const [isRunning, setIsRunning] = useState(false);

  const handleLongOperation = async () => {
    setIsRunning(true);
    setProgress(0);
    
    // Simulate progress
    const interval = setInterval(() => {
      setProgress((prev) => {
        if (prev >= 100) {
          clearInterval(interval);
          setIsRunning(false);
          return 100;
        }
        return prev + 10;
      });
    }, 500);
  };

  return (
    <Card style={brutalistCardStyle}>
      <Stack gap="md">
        {isRunning && (
          <Progress 
            value={progress} 
            style={{
              border: '2px solid var(--color-black)',
            }}
          />
        )}
        <Button 
          onClick={handleLongOperation}
          disabled={isRunning}
          loading={isRunning}
          style={{
            border: '2px solid var(--color-black)',
            boxShadow: 'var(--shadow-brutal)',
          }}
        >
          {isRunning ? 'Running...' : 'Start Operation'}
        </Button>
      </Stack>
    </Card>
  );
}
```

## Components That Need Loading States

### High Priority (Missing Loading States)

1. **Pages** (in `apps/frontend/src/app/`):
   - [ ] `ai-bom/page.tsx` - Has loading state but could use skeleton
   - [ ] `security/page.tsx` - Needs loading state
   - [ ] `monitoring/page.tsx` - Needs loading state
   - [ ] `fairness/page.tsx` - Needs loading state
   - [ ] `bias/page.tsx` - Needs loading state
   - [ ] `ai-governance/page.tsx` - Needs loading state
   - [ ] `status/page.tsx` - Needs loading state
   - [ ] `risks/page.tsx` - Needs loading state
   - [ ] `reports/page.tsx` - Needs loading state
   - [ ] `provenance/page.tsx` - Needs loading state
   - [ ] `policies/page.tsx` - Needs loading state
   - [ ] `compliance/page.tsx` - Needs loading state
   - [ ] `advanced-bias/page.tsx` - Needs loading state

2. **Chart Components** (in `apps/frontend/src/components/charts/`):
   - [ ] `AdvancedBiasVisualization.tsx` - Has loading prop but needs skeleton
   - [ ] `ReportSnapshotChart.tsx` - Check if needs loading state
   - [ ] `UserChart.tsx` - Check if needs loading state

3. **Benchmarking Components** (in `apps/frontend/src/components/benchmarking/`):
   - [x] `ModelPerformanceBenchmark.tsx` - Already has loading states
   - [ ] `BenchmarkRunForm.tsx` - Has loading but could improve UX
   - [ ] `BenchmarkRunList.tsx` - Has loading but needs skeleton

### Medium Priority (Improve Existing)

1. **Components with basic loading**:
   - [ ] `RealTimeMonitoring.tsx` - Has loading but could use skeleton
   - [ ] `BiasTestingSimulator.tsx` - Has loading messages but could use progress indicators

## Error State Patterns

### Standard Error State

```typescript
if (error && !data) {
  return (
    <Card style={brutalistCardStyle} p="lg">
      <Stack gap="md">
        <Alert 
          color="red" 
          title="Failed to load"
          icon={<IconAlertTriangle size={16} />}
          style={{
            border: '2px solid var(--color-black)',
            boxShadow: 'var(--shadow-brutal)',
          }}
        >
          {error.message || 'An error occurred while loading data.'}
        </Alert>
        {retry && (
          <Button 
            onClick={retry}
            leftSection={<IconRefresh size={16} />}
            style={{
              border: '2px solid var(--color-black)',
              boxShadow: 'var(--shadow-brutal)',
            }}
          >
            Retry
          </Button>
        )}
      </Stack>
    </Card>
  );
}
```

## Testing Your Implementation

1. **Test Loading States**:
   - Throttle network in DevTools (Slow 3G)
   - Verify skeleton appears during loading
   - Check that skeleton matches content layout

2. **Test Error States**:
   - Disconnect network
   - Verify error message appears
   - Test retry functionality

3. **Test Progress Indicators**:
   - Trigger long-running operations
   - Verify progress updates smoothly
   - Check completion state

## Code Style Guidelines

1. **Consistency**: Use the same loading pattern across similar components
2. **Accessibility**: Ensure loading states are announced to screen readers
3. **Performance**: Don't show loading states for cached data
4. **User Experience**: Show skeletons immediately, don't wait for API response

## Example: Complete Implementation

Here's a complete example of a page with proper loading states:

```typescript
'use client';

import { useState } from 'react';
import { Card, Stack, Group, Title, Alert, Button, Text } from '@mantine/core';
import { useMantineColorScheme } from '@mantine/core';
import { IconAlertTriangle, IconRefresh } from '@tabler/icons-react';
import { CardSkeleton } from '@/components/LoadingSkeleton';
import { useApi } from '@/hooks/useApi';

interface MyData {
  items: Array<{ id: string; name: string }>;
  stats: { total: number };
}

export default function MyPage() {
  const { colorScheme } = useMantineColorScheme();
  const { data, loading, error, retry } = useApi<MyData>(
    '/api/v1/my-endpoint',
    {
      fallbackData: { items: [], stats: { total: 0 } },
      enableRetry: true,
    }
  );

  const brutalistCardStyle = {
    background: colorScheme === 'dark' ? 'var(--color-black)' : 'var(--color-white)',
    border: '2px solid var(--color-black)',
    borderRadius: 'var(--border-radius-base)',
    boxShadow: 'var(--shadow-brutal)',
    transition: 'all var(--transition-duration-fast) ease',
  };

  // Loading state
  if (loading && !data) {
    return <CardSkeleton count={3} />;
  }

  // Error state
  if (error && !data) {
    return (
      <Card style={brutalistCardStyle} p="lg">
        <Stack gap="md">
          <Alert
            color="red"
            title="Failed to load data"
            icon={<IconAlertTriangle size={16} />}
            style={{
              border: '2px solid var(--color-black)',
              boxShadow: 'var(--shadow-brutal)',
            }}
          >
            {error.message || 'Unable to fetch data. Please try again.'}
          </Alert>
          <Button
            onClick={retry}
            leftSection={<IconRefresh size={16} />}
            style={{
              border: '2px solid var(--color-black)',
              boxShadow: 'var(--shadow-brutal)',
            }}
          >
            Retry
          </Button>
        </Stack>
      </Card>
    );
  }

  // Render content
  return (
    <Stack gap="md">
      <Card style={brutalistCardStyle} p="lg">
        <Title order={2}>My Page</Title>
        <Text mt="md">Total: {data?.stats.total || 0}</Text>
      </Card>

      {data?.items.map((item) => (
        <Card key={item.id} style={brutalistCardStyle} p="md">
          <Text>{item.name}</Text>
        </Card>
      ))}
    </Stack>
  );
}
```

## Resources

- **LoadingSkeleton Component**: `apps/frontend/src/components/LoadingSkeleton.tsx`
- **useApi Hook**: `apps/frontend/src/hooks/useApi.ts`
- **Design System CSS**: `apps/frontend/src/styles/neobrutal.css`
- **Example Implementation**: `apps/frontend/src/components/dashboard/Dashboard.tsx`

## Questions?

If you have questions about:
- Design patterns: Check existing implementations in `Dashboard.tsx` or `MultimodalBiasDetectionChart.tsx`
- API usage: See `useApi.ts` hook documentation
- Styling: Refer to `neobrutal.css` and `globals.css`

## Next Steps

1. Start with one page/component
2. Implement loading state using the patterns above
3. Test thoroughly
4. Move to the next component
5. Ensure consistency across all implementations

Good luck! 🚀

