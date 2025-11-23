# Local Testing Guide

## Quick Start

### 1. Backend (Port 8000)
The backend should already be running. If not:
```bash
cd apps/backend
uvicorn api.main:app --reload --port 8000
```

### 2. Frontend (Port 1111)
The frontend is configured to run on port 1111:
```bash
cd apps/frontend-new
bun run dev
```

The frontend will be available at: **http://localhost:1111**

## Environment Configuration

The frontend is configured to connect to the backend via `.env.local`:
```
NEXT_PUBLIC_API_URL=http://localhost:8000
```

## Testing Checklist

### Authentication
- [ ] Login page loads at `/login`
- [ ] Can submit login form
- [ ] Error handling works for invalid credentials
- [ ] Successful login redirects to dashboard

### Dashboard
- [ ] Dashboard loads at `/dashboard`
- [ ] Stats cards display data
- [ ] Charts render correctly
- [ ] Recent activity shows

### Pages to Test
- [ ] Models (`/models`) - Data table with models
- [ ] Bias Detection (`/bias`) - Form submission works
- [ ] Security (`/security`) - Scan history displays
- [ ] Monitoring (`/monitoring`) - Real-time metrics
- [ ] Analytics (`/analytics`) - Charts display
- [ ] Settings (`/settings`) - Form updates work
- [ ] AI BOM (`/ai-bom`) - Component tracking
- [ ] Compliance (`/compliance`) - Framework status
- [ ] System Status (`/status`) - Service health
- [ ] Provenance (`/provenance`) - Search functionality
- [ ] Lifecycle (`/lifecycle`) - Stage processing
- [ ] Evidence (`/evidence`) - Collection form
- [ ] Advanced Bias (`/advanced-bias`) - Analysis types
- [ ] Benchmarks (`/benchmarks`) - Benchmark runs
- [ ] Reports (`/reports`) - Report generation
- [ ] Risks (`/risks`) - Risk assessment
- [ ] Policies (`/policies`) - Policy management
- [ ] AI Governance (`/ai-governance`) - Compliance tracking
- [ ] Datasets (`/datasets`) - Dataset management

### Features to Test
- [ ] Form validation (Zod schemas)
- [ ] Error handling and toasts
- [ ] Loading states (skeletons)
- [ ] Data tables (sorting, filtering, pagination)
- [ ] Charts (Line, Bar, Pie, Area, Radar)
- [ ] Navigation (sidebar, header)
- [ ] Responsive design (mobile/tablet/desktop)

## Common Issues

### CORS Errors
- Ensure backend CORS includes `http://localhost:1111`
- Check backend is running on port 8000

### API Connection Issues
- Verify `.env.local` has correct `NEXT_PUBLIC_API_URL`
- Check browser console for API errors
- Verify backend health endpoint: `http://localhost:8000/health`

### Build Errors
- Run `bun install` to ensure dependencies are installed
- Check TypeScript errors: `bun run type-check`
- Check linting: `bun run lint`

## Performance Testing

### Bundle Size
Check bundle sizes:
```bash
bun run build
```

### Lighthouse Audit
Run Lighthouse in Chrome DevTools:
- Performance: Target 90+
- Accessibility: Target 95+
- Best Practices: Target 95+

## Next Steps

1. Test all pages and forms
2. Verify API integrations work
3. Check responsive design
4. Test error scenarios
5. Verify authentication flow

