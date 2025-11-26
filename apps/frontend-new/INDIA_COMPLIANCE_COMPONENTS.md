# India Compliance Dashboard Components

This document describes the frontend components created for the India AI Compliance Automation feature.

## Overview

A comprehensive set of React components for managing India-specific AI compliance, including dashboard visualization, gap analysis, trend tracking, report export, integration management, and AI-powered assistance.

## Components

### 1. IndiaComplianceDashboard.tsx

**Purpose**: Main dashboard component for displaying compliance status

**Features**:
- Framework selection dropdown (DPDP Act 2023, NITI Aayog Principles, MeitY Guidelines, Digital India Act)
- Overall compliance score with visual indicator
- Compliance status badge
- Requirements met progress bar
- Evidence collection counter
- Requirement-by-requirement status table
- Real-time status indicators (compliant, non-compliant, partial, pending)

**Props**:
- `systemId: string` - System identifier
- `onFrameworkChange?: (framework: string) => void` - Callback when framework changes

**Usage**:
```tsx
import { IndiaComplianceDashboard } from '@/components/india-compliance'

<IndiaComplianceDashboard 
  systemId="system-123"
  onFrameworkChange={(framework) => console.log(framework)}
/>
```

### 2. GapAnalysisPanel.tsx

**Purpose**: Visualize compliance gaps with severity levels and remediation steps

**Features**:
- Gap summary with severity breakdown (critical, high, medium, low)
- Total remediation effort estimation
- Expandable gap details with:
  - Failed checks list
  - Legal citations
  - Step-by-step remediation recommendations
  - Effort level indicators
- Evidence linking
- Color-coded severity indicators

**Props**:
- `gaps: ComplianceGap[]` - Array of compliance gaps
- `onViewEvidence?: (evidenceId: string) => void` - Callback for evidence viewing

**Usage**:
```tsx
import { GapAnalysisPanel } from '@/components/india-compliance'

<GapAnalysisPanel 
  gaps={gapData}
  onViewEvidence={(id) => console.log(id)}
/>
```

### 3. ComplianceTrendChart.tsx

**Purpose**: Display compliance trends over time using Recharts

**Features**:
- Compliance score trend line chart
- Requirements met vs total requirements bar chart
- Trend summary statistics (current, average, highest, lowest scores)
- Improvement/degradation indicator
- Status distribution timeline
- Historical data visualization

**Props**:
- `framework: string` - Framework name
- `trendData: TrendDataPoint[]` - Historical trend data
- `timeframe: string` - Timeframe label (e.g., "30d", "90d")

**Usage**:
```tsx
import { ComplianceTrendChart } from '@/components/india-compliance'

<ComplianceTrendChart 
  framework="dpdp_act_2023"
  trendData={trendData}
  timeframe="90d"
/>
```

### 4. ExportReportButton.tsx

**Purpose**: Export compliance reports in multiple formats

**Features**:
- Dropdown menu with export format options
- PDF export with legal citations
- CSV export for spreadsheet analysis
- JSON export for system integration
- File download functionality
- Loading state during export

**Props**:
- `reportData: ReportData` - Report data to export
- `systemId: string` - System identifier for filename
- `onExportStart?: () => void` - Callback when export starts
- `onExportComplete?: (format: string) => void` - Callback when export completes

**Usage**:
```tsx
import { ExportReportButton } from '@/components/india-compliance'

<ExportReportButton 
  reportData={reportData}
  systemId="system-123"
  onExportComplete={(format) => console.log(`Exported as ${format}`)}
/>
```

### 5. IntegrationManagementPanel.tsx

**Purpose**: Manage external tool integrations for compliance data

**Features**:
- Display connected integrations with status
- Add new integrations via dialog
- Sync data from integrations
- Disconnect integrations with confirmation
- Integration status indicators
- Last sync timestamp tracking
- Support for:
  - OneTrust (consent and privacy data)
  - Securiti.ai (data discovery)
  - Sprinto (security controls)
  - MLflow (model metadata)
  - AWS/Azure/GCP (data residency)

**Props**:
- `integrations: Integration[]` - Array of integrations
- `onConnect?: (integrationName: string, credentials: Record<string, string>) => Promise<void>`
- `onDisconnect?: (integrationId: string) => Promise<void>`
- `onSync?: (integrationId: string) => Promise<void>`

**Usage**:
```tsx
import { IntegrationManagementPanel } from '@/components/india-compliance'

<IntegrationManagementPanel 
  integrations={integrations}
  onConnect={handleConnect}
  onDisconnect={handleDisconnect}
  onSync={handleSync}
/>
```

### 6. AIComplianceAssistant.tsx

**Purpose**: AI-powered compliance assistant with Q&A, gap analysis, and remediation planning

**Features**:
- Chat interface for compliance questions
- Real-time message streaming
- Gap analysis generation
- Remediation plan generation
- Tabbed interface:
  - Chat tab for Q&A
  - Gap Analysis tab for results
  - Remediation Plan tab for action items
- Copy to clipboard functionality
- Clear chat history
- Mock AI responses (ready for API integration)

**Props**:
- `systemId: string` - System identifier
- `framework: string` - Compliance framework
- `onGapAnalysis?: (analysis: GapAnalysisResult[]) => void`
- `onRemediationPlan?: (plan: RemediationPlan) => void`

**Usage**:
```tsx
import { AIComplianceAssistant } from '@/components/india-compliance'

<AIComplianceAssistant 
  systemId="system-123"
  framework="dpdp_act_2023"
  onGapAnalysis={(results) => console.log(results)}
  onRemediationPlan={(plan) => console.log(plan)}
/>
```

## Shared Utilities

### Date Formatting

All components use a consistent date formatting utility:
```tsx
const formatDate = (dateString: string) => {
  const date = new Date(dateString)
  return date.toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'long',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  })
}
```

## Styling

All components use:
- **Tailwind CSS** for styling
- **Radix UI** components for accessibility
- **Lucide React** for icons
- **Recharts** for data visualization
- Consistent color scheme:
  - Green: Compliant/Success
  - Red: Non-compliant/Critical
  - Orange: High priority
  - Yellow: Medium priority
  - Blue: Low priority/Information

## Data Types

### ComplianceData
```typescript
interface ComplianceData {
  framework: string
  overall_score: number
  status: 'compliant' | 'non_compliant' | 'partial' | 'pending'
  requirements_met: number
  total_requirements: number
  evidence_count: number
  requirements: ComplianceRequirement[]
  timestamp: string
}
```

### ComplianceGap
```typescript
interface ComplianceGap {
  control_id: string
  control_name: string
  category: string
  severity: 'critical' | 'high' | 'medium' | 'low'
  failed_checks: string[]
  remediation_steps: RemediationStep[]
  legal_citation: string
  evidence_id?: string
}
```

### Integration
```typescript
interface Integration {
  id: string
  integration_name: string
  status: 'connected' | 'disconnected' | 'error' | 'pending'
  last_sync?: string
  created_at: string
}
```

## Integration with Backend

Components are designed to work with the backend API endpoints:
- `POST /api/v1/compliance/india/check` - Compliance checking
- `GET /api/v1/compliance/india/frameworks` - Framework definitions
- `POST /api/v1/compliance/india/bias-detection` - Bias detection
- `POST /api/v1/compliance/india/report` - Report generation
- `GET /api/v1/compliance/india/trends` - Compliance trends
- `POST /api/v1/compliance/india/integrations` - Integration management
- `POST /api/v1/compliance/india/ai/gap-analysis` - AI gap analysis
- `POST /api/v1/compliance/india/ai/remediation-plan` - Remediation planning
- `POST /api/v1/compliance/india/ai/ask` - AI Q&A

## Future Enhancements

1. **Real API Integration**: Replace mock data with actual API calls
2. **Real-time Updates**: WebSocket integration for live compliance updates
3. **Advanced Filtering**: Filter gaps by severity, category, or framework
4. **Bulk Actions**: Bulk remediation planning and execution
5. **Custom Reports**: User-defined report templates
6. **Audit Trail**: Detailed audit logging of all compliance activities
7. **Notifications**: Real-time alerts for compliance status changes
8. **Mobile Responsive**: Enhanced mobile experience

## Testing

Components are designed to be testable with:
- Mock data for development
- Clear prop interfaces
- Callback functions for user interactions
- Accessibility features (ARIA labels, semantic HTML)

## Accessibility

All components follow accessibility best practices:
- Semantic HTML structure
- ARIA labels and descriptions
- Keyboard navigation support
- Color contrast compliance
- Focus management
- Screen reader friendly

## Performance

- Lazy loading of components
- Memoization of expensive computations
- Efficient re-rendering
- Optimized chart rendering with Recharts
- Pagination support for large datasets

## Export

All components are exported from `index.ts`:
```typescript
export { IndiaComplianceDashboard } from './IndiaComplianceDashboard'
export { GapAnalysisPanel } from './GapAnalysisPanel'
export { ComplianceTrendChart } from './ComplianceTrendChart'
export { ExportReportButton } from './ExportReportButton'
export { IntegrationManagementPanel } from './IntegrationManagementPanel'
export { AIComplianceAssistant } from './AIComplianceAssistant'
```
