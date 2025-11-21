# FairMind Frontend (New)

Next.js frontend application for FairMind using Neobrutalism.dev design system.

## Technology Stack

- **Framework**: Next.js 14.2.32
- **UI Library**: Shadcn UI + Neobrutalism.dev components
- **Styling**: Tailwind CSS
- **TypeScript**: Yes
- **Package Manager**: Bun

## Getting Started

### Prerequisites

- Node.js 18+ or Bun
- Backend API running on `http://localhost:8000`

### Installation

```bash
# Install dependencies
bun install

# Run development server
bun run dev
```

The application will be available at `http://localhost:3000` (or port 1111 if specified).

### Environment Variables

Create a `.env.local` file:

```env
NEXT_PUBLIC_API_URL=http://localhost:8000
```

## Project Structure

```
src/
├── app/                    # Next.js app router
│   ├── (dashboard)/       # Dashboard layout group
│   │   └── dashboard/     # Dashboard page
│   ├── layout.tsx         # Root layout
│   ├── page.tsx           # Home page (redirects to dashboard)
│   └── globals.css        # Global styles
├── components/
│   ├── ui/                # Shadcn/Neobrutalism components
│   ├── layout/            # Layout components
│   │   ├── Header.tsx     # Top navigation header
│   │   ├── Sidebar.tsx    # Sidebar with categorized navigation
│   │   └── Navigation.tsx # Navigation wrapper
│   └── OrangeLogo.tsx     # FairMind logo component
├── lib/
│   ├── api/               # API client and hooks
│   │   ├── api-client.ts  # Base API client
│   │   ├── endpoints.ts   # Endpoint definitions
│   │   ├── types.ts       # TypeScript types
│   │   └── hooks/         # React hooks for API calls
│   ├── constants/         # Constants and configuration
│   │   └── navigation.ts  # Navigation structure
│   └── utils.ts           # Utility functions
└── hooks/                 # Custom React hooks
```

## Features

### Navigation

The navigation is organized into categories:

1. **Overview** - Dashboard, System Status
2. **AI Models & Governance** - Model Registry, Provenance, AI BOM, Governance, Lifecycle
3. **Bias Detection & Fairness** - Bias Detection, Advanced Bias, Fairness Analysis, Bias Testing
4. **Security & Compliance** - Security Scans, Compliance, Risk Management, Policies
5. **Monitoring & Analytics** - Monitoring, Analytics, Benchmarks, Reports
6. **Data & Evidence** - Datasets, Evidence
7. **Settings** - Application Settings

### API Integration

The frontend uses a centralized API client (`src/lib/api/api-client.ts`) that:
- Handles authentication tokens
- Provides type-safe API calls
- Includes error handling
- Supports all HTTP methods

### Design System

The application uses Neobrutalism design principles:
- Bold borders (4px black)
- Brutal shadows (6px, 8px, 12px offsets)
- Yellow/Black color scheme
- High contrast
- No gradients

## Development

### Adding New Pages

1. Create page in `src/app/(dashboard)/[page-name]/page.tsx`
2. Add route to `src/lib/constants/navigation.ts`
3. Create API hooks if needed in `src/lib/api/hooks/`

### Adding New Components

1. Use Shadcn CLI: `bunx shadcn@latest add [component]`
2. For Neobrutalism components: `bunx shadcn@latest add https://neobrutalism.dev/r/[component].json`
3. Customize styling in component file

### API Hooks Pattern

```typescript
// src/lib/api/hooks/useExample.ts
import { apiClient } from '../api-client'
import { API_ENDPOINTS } from '../endpoints'

export function useExample() {
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    // Fetch data using apiClient
  }, [])

  return { data, loading, error }
}
```

## Building for Production

```bash
bun run build
bun run start
```

## Migration Status

This is the new frontend built with Neobrutalism.dev. The old frontend has been archived in `apps/frontend-archive/`.

**Completed:**
- ✅ Project setup and configuration
- ✅ Shadcn UI and Neobrutalism.dev integration
- ✅ API client library structure
- ✅ Navigation with categorized menu
- ✅ Header and Sidebar components
- ✅ Dashboard page (basic)

**In Progress:**
- 🔄 Installing remaining Neobrutalism components
- 🔄 Migrating pages from old frontend
- 🔄 Implementing all API integrations

**Next Steps:**
- Complete component installation
- Migrate all pages
- Add charts and visualizations
- Implement forms and data tables
- Add authentication flow
- Testing and QA

## Documentation

- [API Endpoints Documentation](../../docs/API_ENDPOINTS.md)
- [Neobrutalism.dev Documentation](https://www.neobrutalism.dev/docs)
- [Shadcn UI Documentation](https://ui.shadcn.com/docs)
