# Issue #99: Loading States & Skeleton Screens - Implementation Checklist

Use this checklist to track your progress implementing loading states throughout the application.

## Pages That Need Loading States

### High Priority

- [ ] `apps/frontend/src/app/ai-bom/page.tsx`
  - [ ] Add skeleton screen for initial load
  - [ ] Add loading state for data fetching
  - [ ] Add error state with retry

- [ ] `apps/frontend/src/app/security/page.tsx`
  - [ ] Add skeleton screen
  - [ ] Add loading state
  - [ ] Add error state

- [ ] `apps/frontend/src/app/monitoring/page.tsx`
  - [ ] Add skeleton screen
  - [ ] Add loading state
  - [ ] Add error state

- [ ] `apps/frontend/src/app/fairness/page.tsx`
  - [ ] Add skeleton screen
  - [ ] Add loading state
  - [ ] Add error state

- [ ] `apps/frontend/src/app/bias/page.tsx`
  - [ ] Add skeleton screen
  - [ ] Add loading state
  - [ ] Add error state

- [ ] `apps/frontend/src/app/ai-governance/page.tsx`
  - [ ] Add skeleton screen
  - [ ] Add loading state
  - [ ] Add error state

- [ ] `apps/frontend/src/app/status/page.tsx`
  - [ ] Add skeleton screen
  - [ ] Add loading state
  - [ ] Add error state

- [ ] `apps/frontend/src/app/risks/page.tsx`
  - [ ] Add skeleton screen
  - [ ] Add loading state
  - [ ] Add error state

- [ ] `apps/frontend/src/app/reports/page.tsx`
  - [ ] Add skeleton screen
  - [ ] Add loading state
  - [ ] Add error state

- [ ] `apps/frontend/src/app/provenance/page.tsx`
  - [ ] Add skeleton screen
  - [ ] Add loading state
  - [ ] Add error state

- [ ] `apps/frontend/src/app/policies/page.tsx`
  - [ ] Add skeleton screen
  - [ ] Add loading state
  - [ ] Add error state

- [ ] `apps/frontend/src/app/compliance/page.tsx`
  - [ ] Add skeleton screen
  - [ ] Add loading state
  - [ ] Add error state

- [ ] `apps/frontend/src/app/advanced-bias/page.tsx`
  - [ ] Add skeleton screen
  - [ ] Add loading state
  - [ ] Add error state

## Components That Need Loading States

### Chart Components

- [ ] `apps/frontend/src/components/charts/AdvancedBiasVisualization.tsx`
  - [ ] Improve loading state (currently has `loading` prop)
  - [ ] Add skeleton screen
  - [ ] Add error state

- [ ] `apps/frontend/src/components/charts/ReportSnapshotChart.tsx`
  - [ ] Check if needs loading state
  - [ ] Add if needed

- [ ] `apps/frontend/src/components/charts/UserChart.tsx`
  - [ ] Check if needs loading state
  - [ ] Add if needed

### Benchmarking Components

- [ ] `apps/frontend/src/components/benchmarking/BenchmarkRunForm.tsx`
  - [ ] Improve loading UX (currently has basic loading)
  - [ ] Add progress indicator for long operations
  - [ ] Add better loading messages

- [ ] `apps/frontend/src/components/benchmarking/BenchmarkRunList.tsx`
  - [ ] Replace text loading with skeleton
  - [ ] Add error state

### Other Components

- [ ] `apps/frontend/src/components/dashboard/RealTimeMonitoring.tsx`
  - [ ] Replace text loading with skeleton
  - [ ] Improve loading UX

- [ ] `apps/frontend/src/components/simulation/BiasTestingSimulator.tsx`
  - [ ] Add progress indicators for long operations
  - [ ] Improve loading messages

## Pages That Already Have Loading States (Verify Consistency)

- [x] `apps/frontend/src/components/dashboard/Dashboard.tsx` - ✅ Has `DashboardSkeleton`
- [x] `apps/frontend/src/app/evidence/page.tsx` - ✅ Has `CardSkeleton`
- [x] `apps/frontend/src/app/lifecycle/page.tsx` - ✅ Has `CardSkeleton`
- [x] `apps/frontend/src/app/security/scans/page.tsx` - ✅ Has `CardSkeleton`
- [x] `apps/frontend/src/components/charts/ModernBiasDetectionChart.tsx` - ✅ Has `ChartSkeleton`
- [x] `apps/frontend/src/components/charts/MultimodalBiasDetectionChart.tsx` - ✅ Has `ChartSkeleton`
- [x] `apps/frontend/src/components/charts/ComprehensiveEvaluationChart.tsx` - ✅ Has `ChartSkeleton`
- [x] `apps/frontend/src/components/benchmarking/ModelPerformanceBenchmark.tsx` - ✅ Has `ChartSkeleton`

## Implementation Notes

### For Each Component:

1. **Import necessary components:**
   ```typescript
   import { CardSkeleton, ChartSkeleton, DashboardSkeleton } from '@/components/LoadingSkeleton';
   import { useApi } from '@/hooks/useApi';
   import { Card, Alert, Button, Stack } from '@mantine/core';
   ```

2. **Add loading state check:**
   ```typescript
   if (loading && !data) {
     return <CardSkeleton count={3} />;
   }
   ```

3. **Add error state:**
   ```typescript
   if (error && !data) {
     return (
       <Card style={brutalistCardStyle}>
         <Alert color="red">{error.message}</Alert>
         <Button onClick={retry}>Retry</Button>
       </Card>
     );
   }
   ```

4. **Use brutalist styling:**
   ```typescript
   const brutalistCardStyle = {
     background: colorScheme === 'dark' ? 'var(--color-black)' : 'var(--color-white)',
     border: '2px solid var(--color-black)',
     borderRadius: 'var(--border-radius-base)',
     boxShadow: 'var(--shadow-brutal)',
   };
   ```

## Testing Checklist

For each component you implement:

- [ ] Test loading state appears during data fetch
- [ ] Test skeleton matches content layout
- [ ] Test error state appears on failure
- [ ] Test retry functionality works
- [ ] Test with slow network (throttle in DevTools)
- [ ] Test with network disconnected
- [ ] Verify styling matches design system (yellow/black, neobrutal)
- [ ] Verify no gradients or emojis used
- [ ] Verify accessibility (screen reader announcements)

## Progress Tracking

**Total Components**: ~20
**Completed**: 0
**In Progress**: 0
**Remaining**: ~20

---

**Last Updated**: [Date]
**Contributor**: [Your Name]

